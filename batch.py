import os
import time
import logging
import threading
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from urllib.parse import urlparse

from audio_utils import download_audio, convert_to_wav, cleanup_temp_files
from transcribe import transcribe
from translate import translate
from srt_export import export_srt
from cache import CacheManager, CacheType

# Setup logger
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status of a single task in a batch"""
    PENDING = auto()
    DOWNLOADING = auto()
    CONVERTING = auto()
    TRANSCRIBING = auto()
    TRANSLATING = auto()
    EXPORTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    SKIPPED = auto()

class BatchStatus(Enum):
    """Status of the entire batch operation"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()

@dataclass
class TaskProgress:
    """Progress information for a single task"""
    url: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    download_progress: float = 0.0
    conversion_progress: float = 0.0
    transcription_progress: float = 0.0
    translation_progress: float = 0.0
    export_progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    temp_files: List[str] = field(default_factory=list)
    
    def update_progress(self):
        """Update overall progress based on stage-specific progress"""
        if self.status == TaskStatus.DOWNLOADING:
            self.progress = self.download_progress * 0.2
        elif self.status == TaskStatus.CONVERTING:
            self.progress = 0.2 + (self.conversion_progress * 0.1)
        elif self.status == TaskStatus.TRANSCRIBING:
            self.progress = 0.3 + (self.transcription_progress * 0.4)
        elif self.status == TaskStatus.TRANSLATING:
            self.progress = 0.7 + (self.translation_progress * 0.2)
        elif self.status == TaskStatus.EXPORTING:
            self.progress = 0.9 + (self.export_progress * 0.1)
        elif self.status == TaskStatus.COMPLETED:
            self.progress = 1.0
        elif self.status == TaskStatus.FAILED or self.status == TaskStatus.CANCELLED:
            # Keep progress as is
            pass
            
    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return None
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "url": self.url,
            "status": self.status.name,
            "progress": self.progress,
            "error": self.error,
            "elapsed_time": self.get_elapsed_time(),
            "stage_progress": {
                "download": self.download_progress,
                "conversion": self.conversion_progress,
                "transcription": self.transcription_progress,
                "translation": self.translation_progress,
                "export": self.export_progress
            }
        }
    
    def cleanup(self):
        """Clean up any temporary files"""
        if self.temp_files:
            cleanup_temp_files(*self.temp_files)
            self.temp_files = []


class BatchProcessor:
    """
    Manages batch processing of multiple YouTube URLs with progress tracking,
    caching, error handling, and cancellation support.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None, concurrency: int = 2):
        """
        Initialize the batch processor.
        
        Args:
            cache_manager: Optional cache manager for storing/retrieving results
            concurrency: Maximum number of parallel tasks
        """
        self.cache_manager = cache_manager
        self.concurrency = max(1, min(10, concurrency))  # Limit between 1-10
        self.tasks: Dict[str, TaskProgress] = {}
        self.futures: Dict[str, Future] = {}
        self.status = BatchStatus.IDLE
        self.lock = threading.RLock()
        self.cancel_event = threading.Event()
        self._executor = None
        self.on_progress_callback = None
        self.on_completion_callback = None
        
    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for progress updates"""
        self.on_progress_callback = callback
        
    def set_completion_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for batch completion"""
        self.on_completion_callback = callback
        
    def validate_url(self, url: str) -> bool:
        """Validate if a URL appears to be a valid YouTube URL"""
        if not url:
            return False
            
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and \
                   ('youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc)
        except Exception:
            return False
            
    def _report_progress(self, task_id: Optional[str] = None):
        """Report progress to callback if set"""
        if self.on_progress_callback is None:
            return
            
        with self.lock:
            if task_id:
                # Report single task progress
                task = self.tasks.get(task_id)
                if task:
                    self.on_progress_callback({
                        "type": "task_progress",
                        "task": task.to_dict(),
                        "batch_status": self.status.name,
                        "batch_progress": self._calculate_overall_progress()
                    })
            else:
                # Report overall batch progress
                self.on_progress_callback({
                    "type": "batch_progress",
                    "tasks": {url: task.to_dict() for url, task in self.tasks.items()},
                    "batch_status": self.status.name,
                    "batch_progress": self._calculate_overall_progress(),
                    "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                    "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                    "total": len(self.tasks)
                })
                
    def _calculate_overall_progress(self) -> float:
        """Calculate overall batch progress"""
        if not self.tasks:
            return 0.0
            
        total_progress = sum(task.progress for task in self.tasks.values())
        return total_progress / len(self.tasks)
        
    def _process_url(self, url: str, model: str = 'small', target_lang: Optional[str] = None, 
                   output_dir: Optional[str] = None, formats: List[str] = None) -> Dict[str, Any]:
        """
        Process a single URL through the entire pipeline.
        
        Args:
            url: YouTube URL to process
            model: Whisper model to use
            target_lang: Target language for translation (None for no translation)
            output_dir: Directory to save output files
            formats: List of export formats (default: ['srt'])
            
        Returns:
            Dictionary with processing results
        """
        task = self.tasks[url]
        task.start_time = time.time()
        
        # Check if cancelled before starting
        if self.cancel_event.is_set():
            with self.lock:
                task.status = TaskStatus.CANCELLED
                task.update_progress()
                self._report_progress(url)
            return {"status": "cancelled", "url": url}
            
        # Check cache first if available
        cache_hit = False
        if self.cache_manager:
            cache_params = {"model": model}
            if target_lang:
                cache_params["target_lang"] = target_lang
                
            cached_result = self.cache_manager.get(CacheType.TRANSCRIPTION, url, cache_params)
            if cached_result:
                with self.lock:
                    task.status = TaskStatus.COMPLETED
                    task.progress = 1.0
                    task.result = cached_result
                    task.end_time = time.time()
                    self._report_progress(url)
                    
                logger.info(f"Cache hit for {url}")
                cache_hit = True
                
                # Still do export if needed
                if formats and output_dir:
                    self._export_results(url, cached_result, output_dir, formats)
                    
                return {
                    "status": "completed", 
                    "url": url, 
                    "result": cached_result,
                    "cached": True
                }
                
        if cache_hit:
            return {"status": "completed", "url": url, "cached": True}
            
        audio_path = None
        wav_path = None
        result = None
        
        try:
            # DOWNLOADING
            with self.lock:
                task.status = TaskStatus.DOWNLOADING
                self._report_progress(url)
                
            def download_progress_callback(progress, filename):
                with self.lock:
                    task.download_progress = progress
                    task.update_progress()
                    self._report_progress(url)
            
            if self.cancel_event.is_set():
                raise Exception("Task cancelled")
                
            audio_path = download_audio(url, download_progress_callback)
            task.temp_files.append(audio_path)
            
            # CONVERTING
            with self.lock:
                task.status = TaskStatus.CONVERTING
                self._report_progress(url)
                
            def conversion_progress_callback(progress, filename):
                with self.lock:
                    task.conversion_progress = progress
                    task.update_progress()
                    self._report_progress(url)
            
            if self.cancel_event.is_set():
                raise Exception("Task cancelled")
                
            wav_path = convert_to_wav(audio_path, progress_callback=conversion_progress_callback)
            task.temp_files.append(wav_path)
            
            # TRANSCRIBING
            with self.lock:
                task.status = TaskStatus.TRANSCRIBING
                task.transcription_progress = 0.0
                task.update_progress()
                self._report_progress(url)
                
            # Transcription doesn't support progress callbacks yet
            # In a future version, we could modify the transcribe function to support it
            
            if self.cancel_event.is_set():
                raise Exception("Task cancelled")
                
            result = transcribe(wav_path, model)
            
            # TRANSLATING (if needed)
            if target_lang:
                with self.lock:
                    task.status = TaskStatus.TRANSLATING
                    task.translation_progress = 0.0
                    task.update_progress()
                    self._report_progress(url)
                    
                if self.cancel_event.is_set():
                    raise Exception("Task cancelled")
                    
                translated_text = translate(result.get('text', ''), target_lang)
                result['translated_text'] = translated_text
                
                with self.lock:
                    task.translation_progress = 1.0
                    task.update_progress()
                    self._report_progress(url)
            
            # EXPORTING 
            if formats and output_dir:
                with self.lock:
                    task.status = TaskStatus.EXPORTING
                    task.export_progress = 0.0
                    task.update_progress()
                    self._report_progress(url)
                    
                if self.cancel_event.is_set():
                    raise Exception("Task cancelled")
                    
                export_paths = self._export_results(url, result, output_dir, formats)
                
                with self.lock:
                    task.export_progress = 1.0
                    task.update_progress()
                    self._report_progress(url)
            
            # Store in cache if available
            if self.cache_manager and result:
                self.cache_manager.store(CacheType.TRANSCRIPTION, url, result, 
                                        params={"model": model, "target_lang": target_lang})
            
            # COMPLETED
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.progress = 1.0
                task.result = result
                task.end_time = time.time()
                self._report_progress(url)
                
            return {
                "status": "completed", 
                "url": url, 
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            if self.cancel_event.is_set():
                status = TaskStatus.CANCELLED
            else:
                status = TaskStatus.FAILED
                
            with self.lock:
                task.status = status
                task.error = str(e)
                task.end_time = time.time()
                self._report_progress(url)
                
            return {
                "status": "failed" if status == TaskStatus.FAILED else "cancelled", 
                "url": url, 
                "error": str(e)
            }
        finally:
            # Cleanup temporary files
            task.cleanup()
            
    def _export_results(self, url: str, result: Dict[str, Any], output_dir: str, 
                      formats: List[str]) -> Dict[str, str]:
        """
        Export transcription results in specified formats.
        
        Args:
            url: YouTube URL (used for filename generation)
            result: Transcription results
            output_dir: Directory to save output files
            formats: List of export formats (e.g. 'srt', 'txt', 'json')
            
        Returns:
            Dictionary mapping format to output filepath
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Generate a safe filename from the URL
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
        base_filename = os.path.join(output_dir, f"yt_{video_id}")
        
        # Get output paths for each format
        export_paths = {}
        
        # Handle each format
        for fmt in formats:
            fmt = fmt.lower()
            
            if fmt == 'srt':
                output_path = f"{base_filename}.srt"
                export_srt(result.get('segments', []), output_path)
                export_paths['srt'] = output_path
                
            elif fmt == 'txt':
                output_path = f"{base_filename}.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.get('text', ''))
                export_paths['txt'] = output_path
                
            elif fmt == 'json':
                output_path = f"{base_filename}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(result, f, ensure_ascii=False, indent=2)
                export_paths['json'] = output_path
                
            elif fmt == 'vtt':
                output_path = f"{base_filename}.vtt"
                self._export_vtt(result.get('segments', []), output_path)
                export_paths['vtt'] = output_path
                
        return export_paths
        
    def _export_vtt(self, segments, output_path):
        """Export transcription segments as WebVTT format"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for i, segment in enumerate(segments):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                
                # Format timestamps as HH:MM:SS.mmm
                start_time = time.strftime('%H:%M:%S', time.gmtime(start)) + f".{int((start % 1) * 1000):03d}"
                end_time = time.strftime('%H:%M:%S', time.gmtime(end)) + f".{int((end % 1) * 1000):03d}"
                
                f.write(f"{i+1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                
    def process_batch(self, urls: List[str], model: str = 'small', target_lang: Optional[str] = None,
                     output_dir: Optional[str] = None, formats: List[str] = None) -> Dict[str, Any]:
        """
        Process a batch of YouTube URLs.
        
        Args:
            urls: List of YouTube URLs to process
            model: Whisper model to use
            target_lang: Target language for translation (None for no translation)
            output_dir: Directory to save output files
            formats: List of export formats (default: ['srt'])
            
        Returns:
            Batch processing results
        """
        if not urls:
            return {"status": "error", "message": "No URLs provided"}
            
        if not formats:
            formats = ['srt']
            
        with self.lock:
            # Reset state for new batch
            self.cancel_event.clear()
            self.tasks = {}
            self.futures = {}
            self.status = BatchStatus.RUNNING
            
            # Initialize tasks
            for url in urls:
                if self.validate_url(url):
                    self.tasks[url] = TaskProgress(url=url)
                    
            if not self.tasks:
                return {"status": "error", "message": "No valid YouTube URLs provided"}
                
            self._executor = ThreadPoolExecutor(max_workers=self.concurrency)
            
            # Submit tasks to executor
            for url in self.tasks:
                future = self._executor.submit(
                    self._process_url, 
                    url, 
                    model=model,
                    target_lang=target_lang,
                    output_dir=output_dir,
                    formats=formats
                )
                self.futures[url] = future
                
            # Report initial progress
            self._report_progress()
            
        # Create a separate thread to monitor progress and completion
        def monitor_progress():
            try:
                # Wait for all tasks to complete
                for url, future in self.futures.items():
                    try:
                        result = future.result()  # This blocks until the future completes
                    except Exception as e:
                        logger.error(f"Task for {url} failed: {str(e)}")
                
                # Determine final batch status
                with self.lock:
                    if self.cancel_event.is_set():
                        self.status = BatchStatus.CANCELLED
                    elif any(task.status == TaskStatus.FAILED for task in self.tasks.values()):
                        self.status = BatchStatus.FAILED
                    else:
                        self.status = BatchStatus.COMPLETED
                    
                    # Final progress report
                    self._report_progress()
                    
                    # Call completion callback if set
                    if self.on_completion_callback:
                        self.on_completion_callback({
                            "status": self.status.name,
                            "tasks": {url: task.to_dict() for url, task in self.tasks.items()},
                            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                            "total": len(self.tasks)
                        })
                    
            except Exception as e:
                logger.error(f"Error in progress monitor: {str(e)}")
                logger.debug(traceback.format_exc())
            finally:
                # Ensure executor is shut down
                if self._executor:
                    self._executor.shutdown(wait=False)
                    
        # Start the monitor thread
        monitor_thread = threading.Thread(target=monitor_progress)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return {
            "status": "started",
            "tasks": list(self.tasks.keys()),
            "total": len(self.tasks)
        }
        
    def cancel(self) -> bool:
        """
        Cancel the current batch operation.
        
        Returns:
            True if cancellation was initiated, False if no batch is running
        """
        with self.lock:
            if self.status != BatchStatus.RUNNING:
                return False
                
            # Set the cancel event to signal tasks
            self.cancel_event.set()
            self.status = BatchStatus.CANCELLED
            
            # Report progress update
            self._report_progress()
            
            return True
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the batch operation.
        
        Returns:
            Status information for the batch and all tasks
        """
        with self.lock:
            return {
                "batch_status": self.status.name,
                "batch_progress": self._calculate_overall_progress(),
                "tasks": {url: task.to_dict() for url, task in self.tasks.items()},
                "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                "total": len(self.tasks)
            }
            
    def pause(self) -> bool:
        """
        Pause the current batch operation (not fully implemented).
        
        Note: This is a placeholder. True pausing would require additional
        coordination within each processing step.
        
        Returns:
            True if pause was initiated, False if no batch is running
        """
        with self.lock:
            if self.status != BatchStatus.RUNNING:
                return False
                
            # Note: Full pause functionality would require more complex coordination
            self.status = BatchStatus.PAUSED
            
            # Report progress update
            self._report_progress()
            
            return True
            
    def resume(self) -> bool:
        """
        Resume a paused batch operation (not fully implemented).
        
        Note: This is a placeholder. True resuming would require additional
        coordination within each processing step.
        
        Returns:
            True if resume was initiated, False if no batch is paused
        """
        with self.lock:
            if self.status != BatchStatus.PAUSED:
                return False
                
            # Note: Full resume functionality would require more complex coordination
            self.status = BatchStatus.RUNNING
            
            # Report progress update
            self._report_progress()
            
            return True


# For backward compatibility
def batch_process(urls, model='small', target_lang=None, concurrency=2, output_dir=None, formats=None):
    """Legacy function for backward compatibility"""
    processor = BatchProcessor(concurrency=concurrency)
    return processor.process_batch(urls, model, target_lang, output_dir, formats)
