import os, tempfile, subprocess
from tenacity import retry, stop_after_attempt, wait_fixed
import yt_dlp
import socket
import logging
from typing import Optional, Callable, Dict, Any

# Setup logger
logger = logging.getLogger(__name__)

class DownloadProgressHook:
    def __init__(self, callback: Optional[Callable[[float, str], None]] = None):
        self.callback = callback
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.filename = ""
        
    def __call__(self, d: Dict[str, Any]) -> None:
        if d['status'] == 'downloading':
            self.downloaded_bytes = d.get('downloaded_bytes', 0)
            self.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            self.filename = d.get('filename', '')
            
            if self.callback and self.total_bytes:
                progress = self.downloaded_bytes / self.total_bytes
                self.callback(progress, self.filename)
        elif d['status'] == 'finished':
            if self.callback:
                self.callback(1.0, self.filename)
            logger.info(f"Download complete: {self.filename}")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def download_audio(video_url: str, progress_callback: Optional[Callable[[float, str], None]] = None) -> str:
    """
    Download audio from a YouTube video URL.
    
    Args:
        video_url: The YouTube video URL
        progress_callback: Optional callback function that receives progress updates (float 0-1, filename)
        
    Returns:
        Path to the downloaded audio file
        
    Raises:
        ValueError: If the URL is invalid
        yt_dlp.utils.DownloadError: If download fails after retries
        socket.error: If network connectivity issues occur
    """
    if not video_url or not video_url.strip():
        raise ValueError("Empty or invalid YouTube URL provided")
    
    # Create a unique temporary directory for this download
    temp_dir = tempfile.mkdtemp(prefix="ytpro_")
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [DownloadProgressHook(progress_callback)],
    }
    
    try:
        logger.info(f"Downloading audio from: {video_url}")
        
        # Perform the download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            # Get the actual filename used (including any processing by yt-dlp)
            if 'entries' in info:  # Can handle playlists too, but get first entry
                info = info['entries'][0]
            
            # This is the file after postprocessing to m4a
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.m4a'
            
            if not os.path.exists(filename):
                # Check for similar files in the directory (handling any filename changes by yt-dlp)
                potential_files = [f for f in os.listdir(temp_dir) if f.endswith('.m4a')]
                if potential_files:
                    filename = os.path.join(temp_dir, potential_files[0])
                else:
                    raise FileNotFoundError(f"Downloaded file not found in {temp_dir}")
            
            logger.info(f"Audio successfully downloaded to: {filename}")
            return filename
            
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download failed: {str(e)}")
        # Clean up the temp directory on failure
        try:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        except Exception as cleanup_err:
            logger.warning(f"Failed to clean up temp directory: {str(cleanup_err)}")
        raise
    except socket.error as e:
        logger.error(f"Network error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        # Clean up the temp directory on failure
        try:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        except Exception as cleanup_err:
            logger.warning(f"Failed to clean up temp directory: {str(cleanup_err)}")
        raise RuntimeError(f"Failed to download audio: {str(e)}")

def convert_to_wav(input_path: str, rate: int = 16000, progress_callback: Optional[Callable[[float, str], None]] = None) -> str:
    """
    Convert an audio file to WAV format with specified sample rate.
    
    Args:
        input_path: Path to the input audio file
        rate: Sample rate for the output WAV file (default: 16000)
        progress_callback: Optional callback function that receives progress updates (float 0-1, filename)
        
    Returns:
        Path to the converted WAV file
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        RuntimeError: If FFmpeg conversion fails
    """
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create a temporary output file
    fd, out_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Get file info to validate input format and for progress calculation
    try:
        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 
                     'default=noprint_wrappers=1:nokey=1', input_path]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if probe_result.returncode != 0:
            logger.warning(f"Unable to probe input file duration: {input_path}")
            duration = None
        else:
            try:
                duration = float(probe_result.stdout.strip())
                logger.info(f"Input file duration: {duration} seconds")
            except (ValueError, TypeError):
                logger.warning(f"Invalid duration value from FFprobe: {probe_result.stdout}")
                duration = None
    except Exception as e:
        logger.warning(f"Error during file probing: {str(e)}")
        duration = None
    
    # Build FFmpeg command with appropriate options for better quality and compatibility
    cmd = [
        'ffmpeg', 
        '-i', input_path,
        '-ar', str(rate),  # Sample rate
        '-ac', '1',        # Mono audio
        '-c:a', 'pcm_s16le',  # Uncompressed 16-bit PCM
        '-y',              # Overwrite output file
        '-v', 'error',     # Only show errors
        '-stats',          # Show stats for progress tracking
        out_path
    ]
    
    logger.info(f"Converting {input_path} to WAV format (rate: {rate}Hz)")
    
    try:
        # Start FFmpeg process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True, 
            bufsize=1
        )
        
        # Track progress by parsing FFmpeg output
        last_progress = 0
        for line in process.stderr:
            # Try to parse ffmpeg progress information
            if "time=" in line and duration:
                # Extract time information (format: time=HH:MM:SS.MS)
                try:
                    time_str = line.split("time=")[1].split(" ")[0].strip()
                    h, m, s = time_str.split(':')
                    current_time = float(h) * 3600 + float(m) * 60 + float(s)
                    progress = min(current_time / duration, 1.0)
                    
                    # Only report progress when it changes significantly (avoid excessive callbacks)
                    if progress - last_progress >= 0.05 or progress >= 0.99:
                        if progress_callback:
                            progress_callback(progress, out_path)
                        last_progress = progress
                except Exception as e:
                    logger.debug(f"Error parsing FFmpeg progress: {str(e)}")
        
        # Wait for process to complete
        process.wait()
        
        # Check for successful completion
        if process.returncode != 0:
            err = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
            logger.error(f"FFmpeg conversion failed: {err}")
            
            # Clean up the output file if conversion failed
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up output file: {str(cleanup_err)}")
                
            raise RuntimeError(f"Audio conversion failed: {err}")
        
        # Signal completion
        if progress_callback:
            progress_callback(1.0, out_path)
            
        logger.info(f"Successfully converted to WAV: {out_path}")
        return out_path
        
    except Exception as e:
        logger.error(f"Error during audio conversion: {str(e)}")
        
        # Clean up the output file in case of any exception
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception as cleanup_err:
            logger.warning(f"Failed to clean up output file: {str(cleanup_err)}")
            
        raise RuntimeError(f"Failed to convert audio: {str(e)}")

def cleanup_temp_files(*file_paths):
    """
    Clean up temporary files safely.
    
    Args:
        *file_paths: Paths to files that should be deleted
    """
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.debug(f"Removed temporary file: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {path}: {str(e)}")
