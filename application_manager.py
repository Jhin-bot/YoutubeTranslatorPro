"""
Application manager for YouTube Transcriber Pro.
Coordinates all advanced features and provides a centralized interface for the main application.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple

from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

from advanced_features import (
    RecentFilesManager, RecentFilesMenu,
    AutoUpdater, UpdateStatus, UpdateDialog,
    SystemTrayManager, NotificationType,
    KeyboardManager, ShortcutAction, ShortcutConfigDialog,
    SessionManager,
    ErrorReporter, ErrorSeverity, ErrorDialog, CrashHandler
)
from ui import APP_NAME, APP_VERSION, MainWindow


# Set up logger
logger = logging.getLogger(__name__)


class ApplicationManager(QObject):
    """
    Central manager for all advanced application features.
    
    Coordinates the initialization, configuration, and interaction of various
    advanced features like recent files management, auto-updating, error handling,
    and system tray integration.
    """
    
    # Signals
    startup_complete = pyqtSignal()
    shutdown_initiated = pyqtSignal()
    feature_status_changed = pyqtSignal(str, bool)  # Feature name, enabled
    error_occurred = pyqtSignal(str, str)  # Message, details
    
    def __init__(self, app: QApplication, main_window: Optional[QMainWindow] = None):
        """
        Initialize the application manager.
        
        Args:
            app: The QApplication instance
            main_window: Optional main window to manage. If None, a new MainWindow will be created.
        """
        super().__init__()
        self.app = app
        
        # Create main window if not provided
        self.main_window = main_window or MainWindow()
        
        # Initialize feature managers with default settings
        self._init_feature_managers()
        
        # Connect signals and slots
        self._connect_signals()
        
        # Initialize main window advanced features
        self._init_main_window_features()
        
        # Log initialization
        logger.info(f"{APP_NAME} v{APP_VERSION} application manager initialized")
        
    def _init_feature_managers(self):
        """Initialize all feature managers"""
        # Recent files management
        self.recent_files_manager = RecentFilesManager(
            max_files=20,
            settings_key="recent_files"
        )
        
        # Session management
        self.session_manager = SessionManager(APP_NAME)
        self.session_manager.set_recent_files_manager(self.recent_files_manager)
        
        # Error reporting
        self.error_reporter = ErrorReporter(APP_NAME, parent=self)
        
        # Crash handling
        self.crash_handler = CrashHandler(
            app_name=APP_NAME,
            error_reporter=self.error_reporter,
            session_manager=self.session_manager
        )
        
        # Install exception handler
        self.crash_handler.install_handler()
        
        # System tray integration
        self.system_tray_manager = SystemTrayManager(
            app_name=APP_NAME,
            parent=self
        )
        
        # Keyboard shortcuts
        self.keyboard_manager = KeyboardManager(parent=self.main_window)
        
        # Auto-updater
        update_url = "https://api.example.com/youtube-transcriber-pro/updates"
        self.auto_updater = AutoUpdater(
            current_version=APP_VERSION,
            update_url=update_url,
            update_check_interval=24,  # Check daily
            parent=self
        )
        
    def _connect_signals(self):
        """Connect signals between components"""
        # System tray signals
        self.system_tray_manager.show_app_requested.connect(self._show_main_window)
        self.system_tray_manager.hide_app_requested.connect(self._hide_main_window)
        self.system_tray_manager.exit_app_requested.connect(self.shutdown)
        
        # Keyboard shortcut signals
        self.keyboard_manager.shortcut_triggered.connect(self._handle_shortcut)
        
        # Auto-updater signals
        self.auto_updater.update_status_changed.connect(self._handle_update_status)
        
        # Error reporter signals
        self.error_reporter.error_occurred.connect(self._handle_error)
        
    def _init_main_window_features(self):
        """Initialize features that integrate with the main window"""
        # Set window title with version
        self.main_window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        
        # Create recent files menu
        self.recent_files_menu = RecentFilesMenu(self.recent_files_manager)
        self.recent_files_menu.file_selected.connect(self._open_recent_file)
        
        # Check for recovery needs
        if self.crash_handler.needs_recovery():
            # Perform recovery if needed
            QTimer.singleShot(500, lambda: self.crash_handler.perform_recovery(self.main_window))
        
        # Check for safe mode
        if self.crash_handler.check_for_safe_mode():
            QMessageBox.warning(
                self.main_window,
                "Safe Mode",
                "The application has detected multiple crashes and is running in safe mode. "
                "Some features may be disabled to improve stability."
            )
            
        # Once application runs successfully for a while, reset crash count
        QTimer.singleShot(30000, self.crash_handler.reset_crash_count)
        
    def startup(self):
        """Start the application"""
        # Show the main window
        self.main_window.show()
        
        # Check for updates (silent)
        QTimer.singleShot(5000, lambda: self.auto_updater.check_for_updates(silent=True))
        
        # Emit startup complete signal
        self.startup_complete.emit()
        logger.info("Application startup complete")
        
    def shutdown(self):
        """Shutdown the application"""
        # Emit shutdown signal
        self.shutdown_initiated.emit()
        logger.info("Application shutdown initiated")
        
        # Save session state
        self.session_manager.save_session(self.main_window, {
            "timestamp": str(self.app.startingUp())
        })
        
        # Uninstall crash handler
        self.crash_handler.uninstall_handler()
        
        # Quit application
        self.app.quit()
        
    def _show_main_window(self):
        """Show the main window"""
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()
        
    def _hide_main_window(self):
        """Hide the main window"""
        self.main_window.hide()
        
        # Show notification if enabled
        self.system_tray_manager.show_notification(
            APP_NAME,
            "Application minimized to system tray",
            NotificationType.INFO,
            3000
        )
        
    def _handle_shortcut(self, action: ShortcutAction):
        """Handle triggered shortcuts"""
        logger.debug(f"Shortcut triggered: {action.name}")
        
        if action == ShortcutAction.EXIT:
            self.shutdown()
            
        elif action == ShortcutAction.SETTINGS:
            # Show settings dialog
            pass  # Will be implemented in MainWindow
            
        elif action == ShortcutAction.TOGGLE_FULLSCREEN:
            if self.main_window.isFullScreen():
                self.main_window.showNormal()
            else:
                self.main_window.showFullScreen()
                
    def _handle_update_status(self, status: UpdateStatus, message: str):
        """Handle update status changes"""
        logger.info(f"Update status: {status.name} - {message}")
        
        # Show notification for available updates
        if status == UpdateStatus.UPDATE_AVAILABLE:
            self.system_tray_manager.show_notification(
                "Update Available",
                message,
                NotificationType.INFO,
                5000
            )
            
            # Show update dialog
            update_dialog = UpdateDialog(self.auto_updater, self.main_window)
            update_dialog.show()
            
    def _handle_error(self, report):
        """Handle errors reported by the error reporter"""
        # Log errors
        logger.error(f"Error reported: {report.message}")
        
        # Emit signal with simplified info
        self.error_occurred.emit(report.message, report.details)
        
    def _open_recent_file(self, file_path: str):
        """Handle opening a recent file"""
        logger.info(f"Opening recent file: {file_path}")
        
        # Delegate to main window handler if it exists
        if hasattr(self.main_window, "open_file"):
            self.main_window.open_file(file_path)
            
    def configure_shortcut(self, action: ShortcutAction, key_sequence: str, enabled: bool = True) -> bool:
        """
        Configure a keyboard shortcut
        
        Args:
            action: The shortcut action

