"""
Advanced features for YouTube Transcriber Pro.
Provides professional-level enhancements like recent files management,
auto-updates, system tray integration, keyboard shortcuts, session management,
and error reporting.
"""

import os
import sys
import json
import time
import logging
import platform
import traceback
import tempfile
import shutil
import socket
import threading
import subprocess
import webbrowser
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

from PyQt6.QtCore import (
    Qt, QObject, QSettings, QTimer, QSize, QPoint, QRect, QUrl, QEvent,
    QStandardPaths, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal,
    pyqtSlot, QByteArray, QBuffer, QModelIndex, QSortFilterProxyModel
)
from PyQt6.QtGui import (
    QIcon, QAction, QKeySequence, QShortcut, QPixmap, QDesktopServices, QFont,
    QColor, QCloseEvent, QImage, QFontMetrics, QMovie, QStandardItemModel,
    QStandardItem
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QMenu, QSystemTrayIcon, QLabel,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QListWidget, 
    QListWidgetItem, QPushButton, QToolButton, QProgressBar, QMessageBox,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QGroupBox, QTabWidget,
    QFileDialog, QScrollArea, QFrame, QSplitter, QSpacerItem, QSizePolicy
)

from styles import style_manager, IconSet, AnimationPresets, Typography, FontWeight


# Set up logger
logger = logging.getLogger(__name__)


# ==============================================================================
# RECENT FILES MANAGER
# ==============================================================================

class RecentFile:
    """Class representing a recently processed file or URL"""
    
    def __init__(self, 
                path: str, 
                file_type: str = "url", 
                title: str = "", 
                timestamp: Optional[datetime] = None,
                metadata: Dict[str, Any] = None):
        """
        Initialize a recent file entry
        
        Args:
            path: File path or URL
            file_type: Type of file ('url', 'audio', 'video', 'transcript')
            title: Display title for the file
            timestamp: When the file was processed
            metadata: Additional metadata
        """
        self.path = path
        self.file_type = file_type
        self.title = title or os.path.basename(path) or path
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "path": self.path,
            "file_type": self.file_type,
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecentFile':
        """Create from dictionary"""
        try:
            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
        except ValueError:
            timestamp = datetime.now()
            
        return cls(
            path=data.get("path", ""),
            file_type=data.get("file_type", "url"),
            title=data.get("title", ""),
            timestamp=timestamp,
            metadata=data.get("metadata", {})
        )


class RecentFilesManager(QObject):
    """Manages recently processed files"""
    
    # Signal emitted when the recent files list changes
    recent_files_changed = pyqtSignal(list)
    
    def __init__(self, 
                max_files: int = 20,
                settings_key: str = "recent_files",
                parent: Optional[QObject] = None):
        """
        Initialize the recent files manager
        
        Args:
            max_files: Maximum number of recent files to track
            settings_key: Key for storing recent files in QSettings
            parent: Parent QObject
        """
        super().__init__(parent)
        self.max_files = max_files
        self.settings_key = settings_key
        self.files: List[RecentFile] = []
        
        # Load recent files from settings
        self.load()
        
    def add_file(self, 
                path: str, 
                file_type: str = "url", 
                title: str = "", 
                metadata: Dict[str, Any] = None) -> None:
        """
        Add a file to the recent files list
        
        Args:
            path: File path or URL
            file_type: Type of file ('url', 'audio', 'video', 'transcript')
            title: Display title for the file
            metadata: Additional metadata
        """
        # Create RecentFile object
        recent_file = RecentFile(
            path=path,
            file_type=file_type,
            title=title,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Remove existing entry with same path
        self.files = [f for f in self.files if f.path != path]
        
        # Add new entry at the beginning
        self.files.insert(0, recent_file)
        
        # Limit list size
        if len(self.files) > self.max_files:
            self.files = self.files[:self.max_files]
            
        # Save changes
        self.save()
        
        # Emit signal
        self.recent_files_changed.emit(self.files)
        
    def remove_file(self, path: str) -> None:
        """Remove a file from the recent files list"""
        self.files = [f for f in self.files if f.path != path]
        self.save()
        self.recent_files_changed.emit(self.files)
        
    def clear(self) -> None:
        """Clear all recent files"""
        self.files = []
        self.save()
        self.recent_files_changed.emit(self.files)
        
    def get_files(self, file_type: Optional[str] = None) -> List[RecentFile]:
        """
        Get recent files, optionally filtered by type
        
        Args:
            file_type: Optional file type filter
            
        Returns:
            List of RecentFile objects
        """
        if file_type:
            return [f for f in self.files if f.file_type == file_type]
        return self.files
        
    def save(self) -> None:
        """Save recent files to QSettings"""
        settings = QSettings()
        
        # Convert to serializable format
        serialized = [f.to_dict() for f in self.files]
        
        # Save as JSON
        settings.setValue(self.settings_key, json.dumps(serialized))
        
    def load(self) -> None:
        """Load recent files from QSettings"""
        settings = QSettings()
        
        # Get JSON data
        json_data = settings.value(self.settings_key, "[]")
        
        try:
            # Parse JSON
            serialized = json.loads(json_data)
            
            # Convert to RecentFile objects
            self.files = [RecentFile.from_dict(data) for data in serialized]
            
        except Exception as e:
            logger.error(f"Error loading recent files: {str(e)}")
            self.files = []


class RecentFilesMenu(QMenu):
    """Menu for displaying and managing recent files"""
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, 
                recent_files_manager: RecentFilesManager,
                parent=None):
        """
        Initialize the recent files menu
        
        Args:
            recent_files_manager: RecentFilesManager instance
            parent: Parent widget
        """
        super().__init__("Recent Files", parent)
        self.recent_files_manager = recent_files_manager
        
        # Connect to recent files change signal
        self.recent_files_manager.recent_files_changed.connect(self.update_menu)
        
        # Initialize menu
        self.update_menu(self.recent_files_manager.get_files())
        
    def update_menu(self, files: List[RecentFile]) -> None:
        """Update menu with current recent files"""
        # Clear existing items
        self.clear()
        
        if not files:
            # Show empty message if no recent files
            empty_action = QAction("No Recent Files", self)
            empty_action.setEnabled(False)
            self.addAction(empty_action)
        else:
            # Add recent files
            for i, file in enumerate(files):
                # Truncate long paths
                display_path = file.path
                if len(display_path) > 60:
                    display_path = display_path[:30] + "..." + display_path[-27:]
                    
                # Create action for file
                action = QAction(f"{file.title} ({display_path})", self)
                action.setData(file.path)
                
                # Set icon based on file type
                icon_name = IconSet.ICON_FILE
                if file.file_type == "url":
                    icon_name = IconSet.ICON_VIDEO
                elif file.file_type == "audio":
                    icon_name = IconSet.ICON_AUDIO
                elif file.file_type == "transcript":
                    icon_name = IconSet.ICON_TEXT
                    
                action.setIcon(IconSet.get_icon(icon_name))
                
                # Connect action
                action.triggered.connect(lambda checked=False, path=file.path: self.file_selected.emit(path))
                
                self.addAction(action)
                
                # Add separator after first 10 items
                if i == 9 and len(files) > 10:
                    self.addSeparator()
        
        # Add separator and management actions
        if files:
            self.addSeparator()
            
        # Clear action
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self.recent_files_manager.clear)
        self.addAction(clear_action)


# ==============================================================================
# AUTO UPDATER
# ==============================================================================

class UpdateStatus(Enum):
    """Status of an update check"""
    CHECKING = auto()
    UP_TO_DATE = auto()
    UPDATE_AVAILABLE = auto()
    DOWNLOADING = auto()
    READY_TO_INSTALL = auto()
    INSTALLING = auto()
    ERROR = auto()


class UpdateInfo:
    """Information about an available update"""
    
    def __init__(self, 
                version: str, 
                download_url: str, 
                release_notes: str = "",
                release_date: Optional[datetime] = None,
                file_size: int = 0):
        """
        Initialize update information
        
        Args:
            version: Version string
            download_url: URL to download the update
            release_notes: Release notes or changelog
            release_date: When the update was released
            file_size: Size of the update file in bytes
        """
        self.version = version
        self.download_url = download_url
        self.release_notes = release_notes
        self.release_date = release_date
        self.file_size = file_size
        self.downloaded_file: Optional[str] = None


class AutoUpdater(QObject):
    """Checks for and handles application updates"""
    
    # Signals
    update_status_changed = pyqtSignal(UpdateStatus, str)
    download_progress = pyqtSignal(float)  # 0.0-1.0
    
    def __init__(self, 
                current_version: str,
                update_url: str,
                update_check_interval: int = 24,  # hours
                parent=None):
        """
        Initialize the auto updater
        
        Args:
            current_version: Current application version
            update_url: URL to check for updates
            update_check_interval: Hours between update checks
            parent: Parent QObject
        """
        super().__init__(parent)
        self.current_version = current_version
        self.update_url = update_url
        self.update_check_interval = update_check_interval
        self.status = UpdateStatus.UP_TO_DATE
        self.update_info: Optional[UpdateInfo] = None
        self.last_check: Optional[datetime] = None
        self.check_in_progress = False
        self.download_thread: Optional[QThread] = None
        
        # Timer for automatic update checks
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_for_updates)
        
        # Load last check time
        settings = QSettings()
        last_check_str = settings.value("updates/last_check", "")
        if last_check_str:
            try:
                self.last_check = datetime.fromisoformat(last_check_str)
            except ValueError:
                self.last_check = None
                
        # Start timer if needed
        self._schedule_next_check()
        
    def _schedule_next_check(self) -> None:
        """Schedule the next automatic update check"""
        if not self.last_check:
            # First run - check soon
            self.check_timer.start(60 * 1000)  # 1 minute
        else:
            # Calculate time until next check
            elapsed = datetime.now() - self.last_check
            check_interval = timedelta(hours=self.update_check_interval)
            
            if elapsed >= check_interval:
                # Past due - check soon
                self.check_timer.start(60 * 1000)  # 1 minute
            else:
                # Schedule at the appropriate time
                remaining = check_interval - elapsed
                # Convert to milliseconds, with 1 minute minimum
                ms = max(60 * 1000, int(remaining.total_seconds() * 1000))
                self.check_timer.start(ms)
    
    def check_for_updates(self, silent: bool = False) -> None:
        """
        Check for available updates
        
        Args:
            silent: Whether to suppress status notifications for up-to-date
        """
        if self.check_in_progress:
            return
            
        self.check_in_progress = True
        self._set_status(UpdateStatus.CHECKING, "Checking for updates...")
        
        # Create worker thread for network operation
        class UpdateCheckerThread(QThread):
            result_signal = pyqtSignal(dict)
            error_signal = pyqtSignal(str)
            
            def __init__(self, update_url: str, current_version: str):
                super().__init__()
                self.update_url = update_url
                self.current_version = current_version
                
            def run(self):
                try:
                    # Add user agent and timeout
                    headers = {
                        'User-Agent': f'YouTubeTranscriberPro/{self.current_version}'
                    }
                    
                    # Make request to update URL
                    req = Request(self.update_url, headers=headers)
                    with urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        
                    # Emit result
                    self.result_signal.emit(data)
                    
                except Exception as e:
                    self.error_signal.emit(str(e))
        
        # Create thread
        self.thread = UpdateCheckerThread(self.update_url, self.current_version)
        
        # Connect signals
        self.thread.result_signal.connect(self._on_update_check_result)
        self.thread.error_signal.connect(self._on_update_check_error)
        self.thread.finished.connect(lambda: setattr(self, 'check_in_progress', False))
        
        # Start thread
        self.thread.start()
        
    def _on_update_check_result(self, data: Dict[str, Any]) -> None:
        """Handle update check result"""
        # Update last check time
        self.last_check = datetime.now()
        settings = QSettings()
        settings.setValue("updates/last_check", self.last_check.isoformat())
        
        # Check if update is available
        latest_version = data.get("version", "0.0.0")
        
        # Simple version comparison (could be more sophisticated)
        if self._compare_versions(latest_version, self.current_version) <= 0:
            # Up to date
            self._set_status(UpdateStatus.UP_TO_DATE, "Your application is up to date.")
            return
            
        # Update available
        self.update_info = UpdateInfo(
            version=latest_version,
            download_url=data.get("download_url", ""),
            release_notes=data.get("release_notes", ""),
            file_size=data.get("file_size", 0)
        )
        
        try:
            if data.get("release_date"):
                self.update_info.release_date = datetime.fromisoformat(data["release_date"])
        except ValueError:
            pass  # Ignore invalid date format
            
        self._set_status(
            UpdateStatus.UPDATE_AVAILABLE,
            f"Version {latest_version} is available"
        )
    
    def _on_update_check_error(self, error: str) -> None:
        """Handle update check error"""
        self._set_status(UpdateStatus.ERROR, f"Update check failed: {error}")
    
    def _set_status(self, status: UpdateStatus, message: str) -> None:
        """Set current update status and emit signal"""
        self.status = status
        self.update_status_changed.emit(status, message)
        
    def _compare_versions(self, version_a: str, version_b: str) -> int:
        """
        Compare version strings
        
        Returns:
            1 if version_a > version_b
            0 if version_a == version_b
            -1 if version_a < version_b
        """
        # Split into components
        a_parts = version_a.split('.')
        b_parts = version_b.split('.')
        
        # Pad with zeros to make lengths equal
        while len(a_parts) < len(b_parts):
            a_parts.append('0')
        while len(b_parts) < len(a_parts):
            b_parts.append('0')
            
        # Compare each component
        for a, b in zip(a_parts, b_parts):
            try:
                a_val = int(a)
                b_val = int(b)
                if a_val > b_val:
                    return 1
                if a_val < b_val:
                    return -1
            except ValueError:
                # Non-numeric components - fallback to string comparison
                if a > b:
                    return 1
                if a < b:
                    return -1
                    
        # Versions are equal
        return 0
        
    def download_update(self) -> None:
        """Download the available update"""
        if not self.update_info or not self.update_info.download_url:
            self._set_status(UpdateStatus.ERROR, "No update available to download")
            return
            
        if self.download_thread and self.download_thread.isRunning():
            # Download already in progress
            return
            
        self._set_status(UpdateStatus.DOWNLOADING, f"Downloading version {self.update_info.version}...")
        
        # Create worker thread for download
        class UpdateDownloaderThread(QThread):
            progress_signal = pyqtSignal(float)
            success_signal = pyqtSignal(str)
            error_signal = pyqtSignal(str)
            
            def __init__(self, download_url: str, version: str):
                super().__init__()
                self.download_url = download_url
                self.version = version
                
            def run(self):
                try:
                    # Create temp file
                    fd, temp_path = tempfile.mkstemp(suffix='.zip')
                    os.close(fd)
                    
                    # Download with progress reporting
                    headers = {
                        'User-Agent': 'YouTubeTranscriberPro'
                    }
                    
                    req = Request(self.download_url, headers=headers)
                    with urlopen(req) as response:
                        # Get content length
                        content_length = int(response.headers.get('Content-Length', 0))
                        
                        # Download with progress updates
                        downloaded = 0
                        with open(temp_path, 'wb') as f:
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break
                                    
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if content_length:
                                    progress = min(1.0, downloaded / content_length)
                                    self.progress_signal.emit(progress)
                    
                    # Signal success with the path to the downloaded file
                    self.success_signal.emit(temp_path)
                    
                except Exception as e:
                    self.error_signal.emit(str(e))
                    # Clean up failed download
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except:
                        pass
        
        # Create thread
        self.download_thread = UpdateDownloaderThread(
            self.update_info.download_url,
            self.update_info.version
        )
        
        # Connect signals
        self.download_thread.progress_signal.connect(self.download_progress)
        self.download_thread.success_signal.connect(self._on_download_success)
        self.download_thread.error_signal.connect(self._on_download_error)
        
        # Start thread
        self.download_thread.start()
        
    def _on_download_success(self, file_path: str) -> None:
        """Handle successful download"""
        if self.update_info:
            self.update_info.downloaded_file = file_path
            self._set_status(
                UpdateStatus.READY_TO_INSTALL,
                f"Version {self.update_info.version} ready to install"
            )
        
    def _on_download_error(self, error: str) -> None:
        """Handle download error"""
        self._set_status(UpdateStatus.ERROR, f"Download failed: {error}")
        
    def install_update(self) -> bool:
        """
        Install the downloaded update
        
        Returns:
            True if installation process started successfully
        """
        if not self.update_info or not self.update_info.downloaded_file:
            self._set_status(UpdateStatus.ERROR, "No downloaded update to install")
            return False
            
        if not os.path.exists(self.update_info.downloaded_file):
            self._set_status(UpdateStatus.ERROR, "Update file not found")
            return False
            
        self._set_status(UpdateStatus.INSTALLING, "Installing update...")
        
        try:
            # The installation process depends on your application's packaging
            # This is a simplified example
            
            if platform.system() == "Windows":
                # For Windows, start the installer and exit this application
                subprocess.Popen(["explorer", self.update_info.downloaded_file])
                QTimer.singleShot(1000, lambda: QApplication.instance().quit())
                return True
                
            elif platform.system() == "Darwin":  # macOS
                # For macOS, open the DMG file
                subprocess.Popen(["open", self.update_info.downloaded_file])
                QTimer.singleShot(1000, lambda: QApplication.instance().quit())
                return True
                
            else:  # Linux
                # For Linux, this depends on packaging method
                subprocess.Popen(["xdg-open", self.update_info.downloaded_file])
                QTimer.singleShot(1000, lambda: QApplication.instance().quit())
                return True
                
        except Exception as e:
            self._set_status(UpdateStatus.ERROR, f"Installation failed: {str(e)}")
            return False
            
        return False
        

class UpdateDialog(QDialog):
    """Dialog for displaying and handling updates"""
    
    def __init__(self, updater: AutoUpdater, parent=None):
        super().__init__(parent)
        self.updater = updater
        
        self.setWindowTitle("Software Update")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Status icon and title
        header_layout = QHBoxLayout()
        
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(48, 48)
        header_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setFont(Typography.get_font(
            Typography.FONT_SIZE_L, FontWeight.BOLD
        ))
        header_layout.addWidget(self.status_label, 1)
        
        layout.addLayout(header_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Release notes
        self.notes_label = QLabel("Release Notes:")
        layout.addWidget(self.notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setMinimumHeight(100)
        layout.addWidget(self.notes_edit)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        
        # Remind later button
        self.remind_button = QPushButton("Remind Me Later")
        self.remind_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.remind_button)
        
        self.button_layout.addStretch()
        
        # Check button
        self.check_button = QPushButton("Check Now")
        self.check_button.clicked.connect(lambda: self.updater.check_for_updates(False))
        style_manager.apply_card_style(self.check_button)
        self.button_layout.addWidget(self.check_button)
        
        # Download button
        self.download_button = QPushButton("Download Update")
        self.download_button.clicked.connect(self.updater.download_update)
        style_manager.apply_card_style(self.download_button)
        self.button_layout.addWidget(self.download_button)
        
        # Install button
        self.install_button = QPushButton("Install Update")
        self.install_button.clicked.connect(self._on_install_clicked)
        style_manager.apply_card_style(self.install_button)
        self.button_layout.addWidget(self.install_button)
        
        layout.addLayout(self.button_layout)
        
        # Connect to updater signals
        self.updater.update_status_changed.connect(self._on_status_changed)
        self.updater.download_progress.connect(self._on_download_progress)
        
        # Initial UI state
        self._update_ui(self.updater.status)
        
    def _on_status_changed(self, status: UpdateStatus, message: str) -> None:
        """Handle update status changes"""
        self.status_label.setText(message)
        self._update_ui(status)
        
    def _on_download_progress(self, progress: float) -> None:
        """Handle download progress"""
        self.progress_bar.setValue(int(progress * 100))
        
    def _update_ui(self, status: UpdateStatus) -> None:
        """Update UI based on status"""
        # Set icon
        icon_file = IconSet.ICON_INFO
        if status == UpdateStatus.UPDATE_AVAILABLE:
            icon_file = IconSet.ICON_DOWNLOAD
        elif status == UpdateStatus.DOWNLOADING:
            icon_file = IconSet.ICON_DOWNLOAD
        elif status == UpdateStatus.READY_TO_INSTALL:
            icon_file = IconSet.ICON_SUCCESS
        elif status == UpdateStatus.ERROR:
            icon_file = IconSet.ICON_ERROR
            
        self.status_icon.setPixmap(IconSet.get_pixmap(icon_file, QSize(48, 48)))
        
        # Update release notes
        if self.updater.update_info:
            self.notes_edit.setText(self.updater.update_info.release_notes)
            self.notes_label.setVisible(True)
            self.notes_edit.setVisible(True)
        else:
            self.notes_label.setVisible(False)
            self.notes_edit.setVisible(False)
            
        # Show/hide progress bar
        self.progress_bar.setVisible(status == UpdateStatus.DOWNLOADING)
        
        # Update buttons
        self.check_button.setVisible(status in [UpdateStatus.UP_TO_DATE, UpdateStatus.ERROR])
        self.download_button.setVisible(status == UpdateStatus.UPDATE_AVAILABLE)
        self.install_button.setVisible(status == UpdateStatus.READY_TO_INSTALL)
        
    def _on_install_clicked(self) -> None:
        """Handle install button click"""
        if self.updater.update_info:
            # Show confirmation dialog
            result = QMessageBox.question(
                self,
                "Install Update",
                f"Are you sure you want to install version {self.updater.update_info.version}?\n\n"
                "The application will restart after installation.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # Install update
                if self.updater.install_update():
                    # Close dialog - application will be restarted by the installer
                    self.accept()


# ==============================================================================
# SYSTEM TRAY MANAGER
# ==============================================================================

class NotificationType(Enum):
    """Types of system tray notifications"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    SUCCESS = auto()


class SystemTrayManager(QObject):
    """Manages system tray icon and notifications"""
    
    # Signal emitted when the application should be shown
    show_app_requested = pyqtSignal()
    
    # Signal emitted when the application should be hidden
    hide_app_requested = pyqtSignal()
    
    # Signal emitted when the application should exit
    exit_app_requested = pyqtSignal()
    
    def __init__(self, 
                app_name: str, 
                icon_name: str = IconSet.APP_ICON,
                parent=None):
        """
        Initialize the system tray manager
        
        Args:
            app_name: Application name for menus and notifications
            icon_name: Icon file name from IconSet
            parent: Parent QObject
        """
        super().__init__(parent)
        self.app_name = app_name
        self.icon_name = icon_name
        self.tray_icon = None
        self.menu = None
        self.notification_enabled = True
        
        # Load notification preference from settings
        settings = QSettings()
        self.notification_enabled = settings.value("system_tray/notifications", True, type=bool)
        
        # Create system tray icon if supported
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._setup_tray_icon()
        else:
            logger.warning("System tray is not available on this platform")
    
    def _setup_tray_icon(self) -> None:
        """Set up the system tray icon and menu"""
        # Create menu
        self.menu = QMenu()
        
        # Create actions
        show_action = QAction("Show Application", self.menu)
        show_action.triggered.connect(self.show_app_requested)
        self.menu.addAction(show_action)
        
        hide_action = QAction("Hide to Tray", self.menu)
        hide_action.triggered.connect(self.hide_app_requested)
        self.menu.addAction(hide_action)
        
        self.menu.addSeparator()
        
        # Notification toggle
        notification_action = QAction("Enable Notifications", self.menu)
        notification_action.setCheckable(True)
        notification_action.setChecked(self.notification_enabled)
        notification_action.triggered.connect(self._on_notification_toggled)
        self.menu.addAction(notification_action)
        
        self.menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.exit_app_requested)
        self.menu.addAction(exit_action)
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(IconSet.get_icon(self.icon_name))
        self.tray_icon.setToolTip(self.app_name)
        self.tray_icon.setContextMenu(self.menu)
        
        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger or \
           reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Single or double click - show the app
            self.show_app_requested.emit()
            
    def _on_notification_toggled(self, enabled: bool) -> None:
        """Handle notification toggle"""
        self.notification_enabled = enabled
        
        # Save to settings
        settings = QSettings()
        settings.setValue("system_tray/notifications", enabled)
        
    def show_notification(self, 
                        title: str, 
                        message: str, 
                        notification_type: NotificationType = NotificationType.INFO,
                        duration_ms: int = 5000) -> None:
        """
        Show a system tray notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            duration_ms: Display duration in milliseconds
        """
        if not self.tray_icon or not self.notification_enabled:
            return
            
        # Map notification type to icon
        icon_map = {
            NotificationType.INFO: QSystemTrayIcon.MessageIcon.Information,
            NotificationType.WARNING: QSystemTrayIcon.MessageIcon.Warning,
            NotificationType.ERROR: QSystemTrayIcon.MessageIcon.Critical,
            NotificationType.SUCCESS: QSystemTrayIcon.MessageIcon.Information
        }
        
        icon = icon_map.get(notification_type, QSystemTrayIcon.MessageIcon.Information)
        
        # Show notification
        self.tray_icon.showMessage(title, message, icon, duration_ms)
        
    def update_icon(self, icon_name: str) -> None:
        """Update the tray icon"""
        if self.tray_icon:
            self.icon_name = icon_name
            self.tray_icon.setIcon(IconSet.get_icon(icon_name))
            
    def update_tooltip(self, tooltip: str) -> None:
        """Update the tray icon tooltip"""
        if self.tray_icon:
            self.tray_icon.setToolTip(tooltip)


# ==============================================================================
# KEYBOARD MANAGER
# ==============================================================================

class ShortcutAction(Enum):
    """Actions that can be triggered by shortcuts"""
    START_PROCESSING = auto()
    STOP_PROCESSING = auto()
    OPEN_FILE = auto()
    SAVE_FILE = auto()
    SETTINGS = auto()
    NEW_TASK = auto()
    SHOW_LOGS = auto()
    CLEAR_QUEUE = auto()
    TOGGLE_FULLSCREEN = auto()
    EXIT = auto()


class ShortcutConfig:
    """Configuration for a keyboard shortcut"""
    
    def __init__(self, 
                action: ShortcutAction, 
                key_sequence: str,
                description: str = "",
                is_global: bool = False,
                enabled: bool = True):
        """
        Initialize a shortcut configuration
        
        Args:
            action: The action to trigger
            key_sequence: QKeySequence string (e.g., "Ctrl+S")
            description: Human-readable description
            is_global: Whether this is a global (system-wide) shortcut
            enabled: Whether the shortcut is enabled
        """
        self.action = action
        self.key_sequence = key_sequence
        self.description = description
        self.is_global = is_global
        self.enabled = enabled
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action": self.action.name,
            "key_sequence": self.key_sequence,
            "description": self.description,
            "is_global": self.is_global,
            "enabled": self.enabled
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShortcutConfig':
        """Create from dictionary"""
        try:
            action = ShortcutAction[data.get("action", "")]
        except (KeyError, ValueError):
            # Default to a safe action if invalid
            action = ShortcutAction.SETTINGS
            
        return cls(
            action=action,
            key_sequence=data.get("key_sequence", ""),
            description=data.get("description", ""),
            is_global=data.get("is_global", False),
            enabled=data.get("enabled", True)
        )


class KeyboardManager(QObject):
    """Manages keyboard shortcuts for the application"""
    
    # Signal emitted when a shortcut is triggered
    shortcut_triggered = pyqtSignal(ShortcutAction)
    
    def __init__(self, parent=None):
        """
        Initialize the keyboard manager
        
        Args:
            parent: Parent QObject (typically the main window)
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.shortcuts: Dict[ShortcutAction, QShortcut] = {}
        self.configs: Dict[ShortcutAction, ShortcutConfig] = {}
        
        # Initialize with default shortcuts
        self._init_default_shortcuts()
        
        # Load custom shortcuts from settings
        self.load_shortcuts()
        
    def _init_default_shortcuts(self) -> None:
        """Initialize default shortcut configurations"""
        defaults = [
            ShortcutConfig(
                ShortcutAction.START_PROCESSING,
                "Ctrl+Return",
                "Start Processing",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.STOP_PROCESSING,
                "Ctrl+Escape",
                "Stop Processing",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.OPEN_FILE,
                "Ctrl+O",
                "Open File",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.SAVE_FILE,
                "Ctrl+S",
                "Save File",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.SETTINGS,
                "Ctrl+,",
                "Open Settings",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.NEW_TASK,
                "Ctrl+N",
                "New Task",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.SHOW_LOGS,
                "Ctrl+L",
                "Show Logs",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.CLEAR_QUEUE,
                "Ctrl+Shift+C",
                "Clear Queue",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.TOGGLE_FULLSCREEN,
                "F11",
                "Toggle Fullscreen",
                False,
                True
            ),
            ShortcutConfig(
                ShortcutAction.EXIT,
                "Ctrl+Q",
                "Exit Application",
                False,
                True
            )
        ]
        
        # Add to configs dictionary
        for config in defaults:
            self.configs[config.action] = config
            
    def load_shortcuts(self) -> None:
        """Load shortcut configurations from settings"""
        settings = QSettings()
        
        # Get serialized shortcuts
        shortcut_data = settings.value("keyboard/shortcuts", "{}")
        
        try:
            # Parse JSON
            shortcut_dict = json.loads(shortcut_data)
            
            # Update configs with custom settings
            for action_name, config_data in shortcut_dict.items():
                try:
                    action = ShortcutAction[action_name]
                    if action in self.configs:
                        # Update existing config
                        self.configs[action] = ShortcutConfig.from_dict(config_data)
                except (KeyError, ValueError):
                    # Skip invalid action names
                    continue
                    
        except Exception as e:
            logger.error(f"Error loading shortcuts: {str(e)}")
            
        # Create shortcut objects
        self._create_shortcuts()
        
    def save_shortcuts(self) -> None:
        """Save shortcut configurations to settings"""
        settings = QSettings()
        
        # Convert configs to serializable format
        shortcut_dict = {action.name: config.to_dict() 
                       for action, config in self.configs.items()}
        
        # Save as JSON
        settings.setValue("keyboard/shortcuts", json.dumps(shortcut_dict))
        
    def _create_shortcuts(self) -> None:
        """Create QShortcut objects from configurations"""
        # Remove existing shortcuts
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
            shortcut.setParent(None)
            
        self.shortcuts.clear()
        
        # Create new shortcuts
        for action, config in self.configs.items():
            if not config.enabled or not config.key_sequence:
                continue
                
            # Create QShortcut
            key_seq = QKeySequence(config.key_sequence)
            if not key_seq.isEmpty():
                shortcut = QShortcut(key_seq, self.parent_widget)
                
                # Connect to handler
                shortcut.activated.connect(
                    lambda act=action: self.shortcut_triggered.emit(act)
                )
                
                # Add to dictionary
                self.shortcuts[action] = shortcut
                
    def update_shortcut(self, 
                      action: ShortcutAction, 
                      key_sequence: str,
                      enabled: bool = True) -> bool:
        """
        Update a shortcut configuration
        
        Args:
            action: The action to update
            key_sequence: New key sequence
            enabled: Whether the shortcut should be enabled
            
        Returns:
            True if the update was successful
        """
        if action not in self.configs:
            return False
            
        # Update config
        config = self.configs[action]
        config.key_sequence = key_sequence
        config.enabled = enabled
        
        # Recreate shortcuts
        self._create_shortcuts()
        
        # Save changes
        self.save_shortcuts()
        
        return True


class ShortcutConfigDialog(QDialog):
    """Dialog for configuring keyboard shortcuts"""
    
    def __init__(self, keyboard_manager: KeyboardManager, parent=None):
        super().__init__(parent)
        self.keyboard_manager = keyboard_manager
        
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumWidth(500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create shortcut table
        self.shortcuts_table = QTableWidget(self)
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut", "Enabled"])
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.shortcuts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.shortcuts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.shortcuts_table.setAlternatingRowColors(True)
        self.shortcuts_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.shortcuts_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Reset to defaults button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # Edit button
        self.edit_button = QPushButton("Edit Shortcut")
        self.edit_button.clicked.connect(self._edit_shortcut)
        self.edit_button.setEnabled(False)
        style_manager.apply_card_style(self.edit_button)
        button_layout.addWidget(self.edit_button)
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        style_manager.apply_card_style(self.ok_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.shortcuts_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Fill table with shortcuts
        self._populate_table()
        
    def _populate_table(self) -> None:
        """Fill table with current shortcuts"""
        # Clear table
        self.shortcuts_table.setRowCount(0)
        
        # Add shortcuts
        for row, (action, config) in enumerate(sorted(
            self.keyboard_manager.configs.items(), 
            key=lambda x: x[1].description
        )):
            self.shortcuts_table.insertRow(row)
            
            # Action name
            action_item = QTableWidgetItem(config.description)
            action_item.setData(Qt.ItemDataRole.UserRole, action)
            self.shortcuts_table.setItem(row, 0, action_item)
            
            # Shortcut key
            shortcut_item = QTableWidgetItem(config.key_sequence)
            self.shortcuts_table.setItem(row, 1, shortcut_item)
            
            # Enabled checkbox
            enabled_item = QTableWidgetItem()
            enabled_item.setCheckState(
                Qt.CheckState.Checked if config.enabled else Qt.CheckState.Unchecked
            )
            self.shortcuts_table.setItem(row, 2, enabled_item)
            
        # Resize columns
        self.shortcuts_table.resizeColumnsToContents()
        
    def _on_selection_changed(self) -> None:
        """Handle selection change"""
        selected_items = self.shortcuts_table.selectedItems()
        self.edit_button.setEnabled(len(selected_items) > 0)
        
    def _edit_shortcut(self) -> None:
        """Edit the selected shortcut"""
        selected_rows = set(index.row() for index in self.shortcuts_table.selectedIndexes())
        if not selected_rows:
            return
            
        row = list(selected_rows)[0]
        action_item = self.shortcuts_table.item(row, 0)
        action = action_item.data(Qt.ItemDataRole.UserRole)
        
        # Get current config
        config = self.keyboard_manager.configs.get(action)
        if not config:
            return
            
        # Show shortcut editor dialog
        dialog = ShortcutEditorDialog(config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update shortcut
            self.keyboard_manager.update_shortcut(
                action, 
                dialog.key_sequence, 
                dialog.is_enabled
            )
            
            # Update table
            self._populate_table()
            
    def _reset_to_defaults(self) -> None:
        """Reset shortcuts to defaults"""
        # Confirm reset
        result = QMessageBox.question(
            self,
            "Reset Shortcuts",
            "Are you sure you want to reset all shortcuts to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reinitialize defaults
            self.keyboard_manager._init_default_shortcuts()
            self.keyboard_manager._create_shortcuts()
            self.keyboard_manager.save_shortcuts()
            
            # Update table
            self._populate_table()


class ShortcutEditorDialog(QDialog):
    """Dialog for editing a keyboard shortcut"""
    
    def __init__(self, config: ShortcutConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.key_sequence = config.key_sequence
        self.is_enabled = config.enabled
        
        self.setWindowTitle("Edit Shortcut")
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Action name
        layout.addWidget(QLabel(f"Action: {config.description}"))
        
        # Shortcut edit
        shortcut_layout = QHBoxLayout()
        
        shortcut_layout.addWidget(QLabel("Shortcut:"))
        
        self.shortcut_edit = QKeySequenceEdit()
        if self.key_sequence:
            self.shortcut_edit.setKeySequence(QKeySequence(self.key_sequence))
        shortcut_layout.addWidget(self.shortcut_edit)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.shortcut_edit.clear)
        shortcut_layout.addWidget(clear_button)
        
        layout.addLayout(shortcut_layout)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(self.is_enabled)
        layout.addWidget(self.enabled_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._accept)
        style_manager.apply_card_style(ok_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
    def _accept(self) -> None:
        """Accept the dialog and save changes"""
        self.key_sequence = self.shortcut_edit.keySequence().toString()
        self.is_enabled = self.enabled_check.isChecked()
        self.accept()


# ==============================================================================
# SESSION MANAGER
# ==============================================================================

class WindowState:
    """Represents the state of a window"""
    
    def __init__(self, 
                geometry: QRect,
                is_maximized: bool = False,
                is_fullscreen: bool = False):
        """
        Initialize a window state
        
        Args:
            geometry: Window geometry
            is_maximized: Whether the window is maximized
            is_fullscreen: Whether the window is in fullscreen mode
        """
        self.geometry = geometry
        self.is_maximized = is_maximized
        self.is_fullscreen = is_fullscreen
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "x": self.geometry.x(),
            "y": self.geometry.y(),
            "width": self.geometry.width(),
            "height": self.geometry.height(),
            "is_maximized": self.is_maximized,
            "is_fullscreen": self.is_fullscreen
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowState':
        """Create from dictionary"""
        geometry = QRect(
            data.get("x", 100),
            data.get("y", 100),
            data.get("width", 800),
            data.get("height", 600)
        )
        
        return cls(
            geometry=geometry,
            is_maximized=data.get("is_maximized", False),
            is_fullscreen=data.get("is_fullscreen", False)
        )


class SessionManager:
    """Manages application session state"""
    
    def __init__(self, app_name: str):
        """
        Initialize the session manager
        
        Args:
            app_name: Application name for settings
        """
        self.app_name = app_name
        self.recent_files_manager = None
        
    def save_window_state(self, window: QMainWindow) -> None:
        """
        Save window state to settings
        
        Args:
            window: Main window to save state for
        """
        settings = QSettings()
        
        # Create window state
        state = WindowState(
            geometry=window.geometry(),
            is_maximized=window.isMaximized(),
            is_fullscreen=window.isFullScreen()
        )
        
        # Save to settings
        settings.setValue("window/state", json.dumps(state.to_dict()))
        
    def restore_window_state(self, window: QMainWindow) -> bool:
        """
        Restore window state from settings
        
        Args:
            window: Main window to restore state for
            
        Returns:
            True if state was restored successfully
        """
        settings = QSettings()
        
        # Get window state
        state_data = settings.value("window/state", "{}")
        
        try:
            # Parse JSON
            state_dict = json.loads(state_data)
            
            # Create window state
            state = WindowState.from_dict(state_dict)
            
            # Restore state
            window.setGeometry(state.geometry)
            
            if state.is_maximized:
                window.showMaximized()
            elif state.is_fullscreen:
                window.showFullScreen()
                
            return True
            
        except Exception as e:
            logger.error(f"Error restoring window state: {str(e)}")
            return False
            
    def save_session(self, window: QMainWindow, data: Dict[str, Any]) -> None:
        """
        Save session data to settings
        
        Args:
            window: Main window
            data: Session data to save
        """
        # Save window state
        self.save_window_state(window)
        
        # Save session data
        settings = QSettings()
        settings.setValue("session/data", json.dumps(data))
        settings.setValue("session/timestamp", datetime.now().isoformat())
        
    def restore_session(self, window: QMainWindow) -> Dict[str, Any]:
        """
        Restore session data from settings
        
        Args:
            window: Main window
            
        Returns:
            Session data, or empty dict if no session was found
        """
        # Restore window state
        self.restore_window_state(window)
        
        # Restore session data
        settings = QSettings()
        session_data = settings.value("session/data", "{}")
        
        try:
            # Parse JSON
            data = json.loads(session_data)
            return data
            
        except Exception as e:
            logger.error(f"Error restoring session data: {str(e)}")
            return {}
            
    def clear_session(self) -> None:
        """Clear saved session data"""
        settings = QSettings()
        settings.remove("session/data")
        settings.remove("session/timestamp")
        
    def has_session(self) -> bool:
        """Check if a saved session exists"""
        settings = QSettings()
        return settings.contains("session/data")
        
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the saved session
        
        Returns:
            Dictionary with session info, or empty dict if no session exists
        """
        settings = QSettings()
        
        if not settings.contains("session/data"):
            return {}
            
        timestamp_str = settings.value("session/timestamp", "")
        timestamp = None
        
        try:
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            pass
            
        return {
            "timestamp": timestamp,
            "has_session": True
        }
        
    def set_recent_files_manager(self, manager: RecentFilesManager) -> None:
        """Set the recent files manager"""
        self.recent_files_manager = manager


# ==============================================================================
# ERROR REPORTER
# ==============================================================================

class ErrorSeverity(Enum):
    """Severity of an error"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorReport:
    """Information about an error"""
    
    def __init__(self, 
                message: str,
                details: str = "",
                severity: ErrorSeverity = ErrorSeverity.ERROR,
                timestamp: Optional[datetime] = None,
                context: Dict[str, Any] = None):
        """
        Initialize an error report
        
        Args:
            message: Error message
            details: Detailed error information
            severity: Error severity
            timestamp: When the error occurred
            context: Additional context information
        """
        self.message = message
        self.details = details
        self.severity = severity
        self.timestamp = timestamp or datetime.now()
        self.context = context or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message": self.message,
            "details": self.details,
            "severity": self.severity.name,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorReport':
        """Create from dictionary"""
        try:
            severity = ErrorSeverity[data.get("severity", "ERROR")]
        except (KeyError, ValueError):
            severity = ErrorSeverity.ERROR
            
        try:
            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
        except ValueError:
            timestamp = datetime.now()
            
        return cls(
            message=data.get("message", ""),
            details=data.get("details", ""),
            severity=severity,
            timestamp=timestamp,
            context=data.get("context", {})
        )


class ErrorReporter(QObject):
    """Manages error reporting and logging"""
    
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(ErrorReport)
    
    def __init__(self, app_name: str, parent=None):
        """
        Initialize the error reporter
        
        Args:
            app_name: Application name for error reports
            parent: Parent QObject
        """
        super().__init__(parent)
        self.app_name = app_name
        self.system_info = self._collect_system_info()
        self.error_reports: List[ErrorReport] = []
        self.max_reports = 100
        
        # Load saved reports
        self._load_reports()
        
    def _collect_system_info(self) -> Dict[str, str]:
        """Collect system information for error reports"""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname()
        }
        
        # Add Qt version if available
        try:
            from PyQt6.QtCore import QT_VERSION_STR
            info["qt_version"] = QT_VERSION_STR
        except:
            pass
            
        return info
        
    def report_error(self, 
                   message: str, 
                   details: str = "", 
                   severity: ErrorSeverity = ErrorSeverity.ERROR,
                   context: Dict[str, Any] = None,
                   show_dialog: bool = True) -> None:
        """
        Report an error
        
        Args:
            message: Error message
            details: Detailed error information
            severity: Error severity
            context: Additional context information
            show_dialog: Whether to show an error dialog
        """
        # Create error report
        report = ErrorReport(
            message=message,
            details=details,
            severity=severity,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        # Add system info to context
        report.context["system_info"] = self.system_info
        
        # Log error
        log_func = logger.error
        if severity == ErrorSeverity.CRITICAL:
            log_func = logger.critical
        elif severity == ErrorSeverity.WARNING:
            log_func = logger.warning
        elif severity == ErrorSeverity.INFO:
            log_func = logger.info
            
        log_func(f"{message}: {details}")
        
        # Add report to list
        self.error_reports.append(report)
        
        # Limit list size
        if len(self.error_reports) > self.max_reports:
            self.error_reports = self.error_reports[-self.max_reports:]
            
        # Save reports
        self._save_reports()
        
        # Emit signal
        self.error_occurred.emit(report)
        
        # Show dialog if requested
        if show_dialog:
            dialog = ErrorDialog(report, self.app_name, self.parent())
            dialog.exec()
            
    def report_exception(self, 
                       exc_type: type, 
                       exc_value: Exception, 
                       exc_traceback: traceback,
                       context: Dict[str, Any] = None,
                       show_dialog: bool = True) -> None:
        """
        Report an exception
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
            context: Additional context information
            show_dialog: Whether to show an error dialog
        """
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = "".join(tb_lines)
        
        # Create context if needed
        if not context:
            context = {}
            
        # Add exception info to context
        context["exception_type"] = exc_type.__name__
        
        # Report error
        self.report_error(
            message=str(exc_value) or exc_type.__name__,
            details=tb_str,
            severity=ErrorSeverity.ERROR,
            context=context,
            show_dialog=show_dialog
        )
        
    def clear_reports(self) -> None:
        """Clear all error reports"""
        self.error_reports = []
        self._save_reports()
        
    def get_reports(self, max_count: Optional[int] = None) -> List[ErrorReport]:
        """
        Get error reports
        
        Args:
            max_count: Maximum number of reports to retrieve
            
        Returns:
            List of error reports, most recent first
        """
        if max_count is None:
            return list(reversed(self.error_reports))
        else:
            return list(reversed(self.error_reports))[:max_count]
            
    def _save_reports(self) -> None:
        """Save error reports to settings"""
        settings = QSettings()
        
        # Convert to serializable format
        serialized = [report.to_dict() for report in self.error_reports]
        
        # Save as JSON
        settings.setValue("error_reports", json.dumps(serialized))
        
    def _load_reports(self) -> None:
        """Load error reports from settings"""
        settings = QSettings()
        
        # Get JSON data
        json_data = settings.value("error_reports", "[]")
        
        try:
            # Parse JSON
            serialized = json.loads(json_data)
            
            # Convert to ErrorReport objects
            self.error_reports = [ErrorReport.from_dict(data) for data in serialized]
            
        except Exception as e:
            logger.error(f"Error loading error reports: {str(e)}")
            self.error_reports = []


class ErrorDialog(QDialog):
    """Dialog for displaying error details"""
    
    def __init__(self, 
               report: ErrorReport, 
               app_name: str,
               parent=None):
        """
        Initialize the error dialog
        
        Args:
            report: Error report to display
            app_name: Application name
            parent: Parent widget
        """
        super().__init__(parent)
        self.report = report
        self.app_name = app_name
        
        self.setWindowTitle(f"{app_name} - Error")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Error icon and message
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_name = IconSet.ICON_ERROR
        if self.report.severity == ErrorSeverity.WARNING:
            icon_name = IconSet.ICON_WARNING
        elif self.report.severity == ErrorSeverity.INFO:
            icon_name = IconSet.ICON_INFO
            
        icon_label.setPixmap(IconSet.get_pixmap(icon_name, QSize(48, 48)))
        header_layout.addWidget(icon_label)
        
        message_label = QLabel(self.report.message)
        message_label.setWordWrap(True)
        message_label.setFont(Typography.get_font(
            Typography.FONT_SIZE_L, FontWeight.BOLD
        ))
        header_layout.addWidget(message_label, 1)
        
        layout.addLayout(header_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Error details
        details_group = QGroupBox("Error Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_edit = QTextEdit()
        self.details_edit.setReadOnly(True)
        self.details_edit.setFont(Typography.get_font(
            Typography.FONT_SIZE_M, FontWeight.NORMAL, monospace=True
        ))
        self.details_edit.setText(self.report.details)
        details_layout.addWidget(self.details_edit)
        
        layout.addWidget(details_group)
        
        # User feedback
        feedback_group = QGroupBox("Feedback (Optional)")
        feedback_layout = QVBoxLayout(feedback_group)
        
        feedback_label = QLabel("Please describe what you were doing when the error occurred:")
        feedback_layout.addWidget(feedback_label)
        
        self.feedback_edit = QTextEdit()
        self.feedback_edit.setPlaceholderText("Enter your feedback here...")
        feedback_layout.addWidget(self.feedback_edit)
        
        layout.addWidget(feedback_group)
        
        # Recovery options
        recovery_group = QGroupBox("Recovery Options")
        recovery_layout = QVBoxLayout(recovery_group)
        
        # Restart application option
        self.restart_check = QCheckBox("Restart application")
        self.restart_check.setChecked(self.report.severity == ErrorSeverity.CRITICAL)
        recovery_layout.addWidget(self.restart_check)
        
        # Reset settings option
        self.reset_settings_check = QCheckBox("Reset application settings")
        recovery_layout.addWidget(self.reset_settings_check)
        
        layout.addWidget(recovery_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Copy button
        self.copy_button = QPushButton("Copy Debug Info")
        self.copy_button.clicked.connect(self._copy_debug_info)
        button_layout.addWidget(self.copy_button)
        
        button_layout.addStretch()
        
        # Send report button
        self.send_button = QPushButton("Send Error Report")
        self.send_button.clicked.connect(self._send_report)
        button_layout.addWidget(self.send_button)
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        style_manager.apply_card_style(self.ok_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def _copy_debug_info(self) -> None:
        """Copy debug information to clipboard"""
        # Create report text
        lines = [
            f"=== {self.app_name} Error Report ===",
            f"Time: {self.report.timestamp.isoformat()}",
            f"Severity: {self.report.severity.name}",
            f"Error: {self.report.message}",
            "",
            "=== Details ===",
            self.report.details,
            "",
            "=== System Info ===",
        ]
        
        # Add system info
        system_info = self.report.context.get("system_info", {})
        for key, value in system_info.items():
            lines.append(f"{key}: {value}")
            
        # Add user feedback
        if self.feedback_edit.toPlainText():
            lines.append("")
            lines.append("=== User Feedback ===")
            lines.append(self.feedback_edit.toPlainText())
            
        # Join lines
        report_text = "\n".join(lines)
        
        # Copy to clipboard
        QApplication.clipboard().setText(report_text)
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Debug Info Copied",
            "Debug information has been copied to the clipboard."
        )
        
    def _send_report(self) -> None:
        """Send error report"""
        # In a real application, this would send the report to a server
        # For this example, we'll just show a confirmation message
        
        # Add user feedback to report
        self.report.context["user_feedback"] = self.feedback_edit.toPlainText()
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Error Report Sent",
            "Thank you for your feedback. The error report has been sent."
        )
        
        # Close dialog
        self.accept()


class CrashHandler:
    """Handles application crashes and recovery"""
    
    def __init__(self, 
               app_name: str,
               error_reporter: ErrorReporter,
               session_manager: Optional[SessionManager] = None):
        """
        Initialize the crash handler
        
        Args:
            app_name: Application name
            error_reporter: ErrorReporter instance
            session_manager: Optional SessionManager instance
        """
        self.app_name = app_name
        self.error_reporter = error_reporter
        self.session_manager = session_manager
        self.crash_count = 0
        self.last_crash_time = None
        
        # Load crash history
        settings = QSettings()
        self.crash_count = settings.value("crash_handler/crash_count", 0, type=int)
        crash_time_str = settings.value("crash_handler/last_crash_time", "")
        
        try:
            if crash_time_str:
                self.last_crash_time = datetime.fromisoformat(crash_time_str)
        except ValueError:
            self.last_crash_time = None
            
    def install_handler(self) -> None:
        """Install global exception handler"""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._handle_exception
        
    def uninstall_handler(self) -> None:
        """Uninstall global exception handler"""
        if hasattr(self, '_original_excepthook'):
            sys.excepthook = self._original_excepthook
            
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exception"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let Python handle keyboard interrupts
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return
            
        # Update crash statistics
        self.crash_count += 1
        self.last_crash_time = datetime.now()
        
        # Save crash history
        settings = QSettings()
        settings.setValue("crash_handler/crash_count", self.crash_count)
        settings.setValue("crash_handler/last_crash_time", self.last_crash_time.isoformat())
        
        # Save crash report
        self.error_reporter.report_exception(
            exc_type, exc_value, exc_traceback,
            context={"is_crash": True},
            show_dialog=False  # Don't show dialog during crash
        )
        
        # Create crash file
        self._create_crash_file(exc_type, exc_value, exc_traceback)
        
        # Let the original handler run
        self._original_excepthook(exc_type, exc_value, exc_traceback)
        
    def _create_crash_file(self, exc_type, exc_value, exc_traceback):
        """Create a crash file with diagnostic information"""
        try:
            # Create crash directory if it doesn't exist
            crash_dir = os.path.join(os.path.expanduser("~"), ".ytpro", "crashes")
            os.makedirs(crash_dir, exist_ok=True)
            
            # Create crash file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = os.path.join(crash_dir, f"crash_{timestamp}.txt")
            
            # Format traceback
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Collect system info
            system_info = self.error_reporter.system_info
            
            # Write crash file
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write(f"=== {self.app_name} Crash Report ===\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Crash count: {self.crash_count}\n")
                f.write(f"Exception type: {exc_type.__name__}\n")
                f.write(f"Exception value: {str(exc_value)}\n")
                f.write("\n=== Traceback ===\n")
                f.write(tb_str)
                f.write("\n=== System Information ===\n")
                
                for key, value in system_info.items():
                    f.write(f"{key}: {value}\n")
                    
                # Write application state if available
                if self.session_manager:
                    f.write("\n=== Session Information ===\n")
                    session_info = self.session_manager.get_session_info()
                    for key, value in session_info.items():
                        f.write(f"{key}: {value}\n")
                
            # Also create a marker file to indicate a crash occurred
            # This will be checked on next startup for recovery
            marker_file = os.path.join(crash_dir, "needs_recovery")
            with open(marker_file, "w") as f:
                f.write(crash_file)
                
            logger.info(f"Crash report saved to {crash_file}")
            return crash_file
            
        except Exception as e:
            # Don't let crash handler exceptions propagate
            logger.error(f"Failed to create crash file: {str(e)}")
            return None
            
    def check_for_safe_mode(self) -> bool:
        """Check if the application should start in safe mode due to recent crashes"""
        # Check for multiple recent crashes
        if self.crash_count >= 3:
            # If we've had 3 or more crashes and the most recent was within the last hour
            if self.last_crash_time and (datetime.now() - self.last_crash_time) < timedelta(hours=1):
                return True
                
        return False
        
    def needs_recovery(self) -> bool:
        """Check if the application needs to recover from a crash"""
        recovery_marker = os.path.join(
            os.path.expanduser("~"), ".ytpro", "crashes", "needs_recovery"
        )
        return os.path.exists(recovery_marker)
        
    def get_last_crash_file(self) -> Optional[str]:
        """Get the path to the last crash file, if any"""
        recovery_marker = os.path.join(
            os.path.expanduser("~"), ".ytpro", "crashes", "needs_recovery"
        )
        
        if os.path.exists(recovery_marker):
            try:
                with open(recovery_marker, "r") as f:
                    crash_file = f.read().strip()
                    if os.path.exists(crash_file):
                        return crash_file
            except:
                pass
                
        return None
        
    def perform_recovery(self, window: QMainWindow) -> bool:
        """
        Perform recovery after a crash
        
        Args:
            window: Main window to restore
            
        Returns:
            True if recovery was successful
        """
        if not self.needs_recovery():
            return False
            
        try:
            # Clear recovery marker
            recovery_marker = os.path.join(
                os.path.expanduser("~"), ".ytpro", "crashes", "needs_recovery"
            )
            os.remove(recovery_marker)
            
            # Restore session if available
            if self.session_manager:
                session_data = self.session_manager.restore_session(window)
                
                # Show recovery message
                QMessageBox.information(
                    window,
                    "Application Recovery",
                    "The application has been recovered after a crash. "
                    "Your session has been restored."
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Recovery failed: {str(e)}")
            
        return False
        
    def reset_crash_count(self) -> None:
        """Reset the crash counter after successful startup"""
        if self.crash_count > 0:
            self.crash_count = 0
            settings = QSettings()
            settings.setValue("crash_handler/crash_count", 0)
