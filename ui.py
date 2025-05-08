import os
import sys
import json
import logging
import platform
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QSize, QUrl, QTimer, QThread, QObject, QSettings, QStandardPaths,
    pyqtSignal, pyqtSlot, QMimeData, QEvent, QPoint, QRect, QPropertyAnimation
)
from PyQt6.QtGui import (
    QIcon, QAction, QFont, QColor, QPalette, QDragEnterEvent, QDropEvent,
    QPixmap, QPainter, QBrush, QPen, QMovie, QLinearGradient, QGradient,
    QFontMetrics, QCloseEvent, QStandardItemModel, QStandardItem
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QSplitter, QComboBox, QCheckBox, QGroupBox, QTabWidget,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QSizePolicy, QToolBar, QStatusBar, QToolButton,
    QGridLayout, QSlider, QSpacerItem, QStackedWidget, QToolTip
)

from batch import BatchProcessor, TaskStatus, BatchStatus
from cache import CacheManager, CacheType
from settings import load_settings, save_settings, DEFAULT_SETTINGS  # We'll create this

# Setup logger
logger = logging.getLogger(__name__)

# Define application-wide constants
APP_NAME = "YouTube Transcriber Pro"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "YouTubeTranscriberPro"

# Available whisper models
WHISPER_MODELS = [
    "tiny", "base", "small", "medium", "large"
]

# Available languages for translation
LANGUAGES = {
    "None": "No Translation",
    "en": "English",
    "es": "Spanish",
    "fr": "French", 
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi"
}

# Export formats
EXPORT_FORMATS = {
    "srt": "SubRip (.srt)",
    "txt": "Plain Text (.txt)",
    "json": "JSON (.json)",
    "vtt": "WebVTT (.vtt)"
}

# Theme constants
class Theme(Enum):
    """Application theme enum"""
    LIGHT = auto()
    DARK = auto()

    @staticmethod
    def from_string(theme_str: str) -> "Theme":
        """Convert string to Theme enum"""
        if theme_str.lower() == "dark":
            return Theme.DARK
        return Theme.LIGHT


class ThemeManager:
    """Manages application-wide theming"""
    
    @staticmethod
    def apply_theme(app: QApplication, theme: Theme) -> None:
        """Apply theme to application"""
        if theme == Theme.DARK:
            ThemeManager._apply_dark_theme(app)
        else:
            ThemeManager._apply_light_theme(app)
    
    @staticmethod
    def _apply_dark_theme(app: QApplication) -> None:
        """Apply dark theme to application"""
        palette = QPalette()
        
        # Basic colors
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        
        app.setPalette(palette)
        app.setStyleSheet("""
            QToolTip { 
                color: #ffffff; 
                background-color: #2a82da; 
                border: 1px solid white; 
            }
            QMenu {
                background-color: #353535;
                border: 1px solid #5c5c5c;
            }
            QMenu::item {
                background-color: transparent;
            }
            QMenu::item:selected { 
                background-color: #2a82da;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #555;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                width: 20px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #353535;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: 1px solid #555;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #353535;
            }
            QScrollBar:vertical {
                border: none;
                background: #2a2a2a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #5c5c5c;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
    
    @staticmethod
    def _apply_light_theme(app: QApplication) -> None:
        """Apply light theme to application"""
        palette = QPalette()
        
        # Reset to default light palette
        app.setStyle("Fusion")
        
        # Some custom overrides for light theme
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        app.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                width: 20px;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #bbb;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QPushButton {
                border: 1px solid #bbb;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d9d9d9;
            }
            QTabWidget::pane {
                border: 1px solid #bbb;
            }
            QTabBar::tab {
                border: 1px solid #bbb;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #f2f2f2;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #bbb;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)


class TaskItemWidget(QWidget):
    """Widget representing a single task in the batch list"""
    
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        
        # Initialize UI
        self._init_ui()
        self.update_status(TaskStatus.PENDING, 0)
        
    def _init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # URL and status layout
        top_layout = QHBoxLayout()
        
        # URL label with ellipsis for long URLs
        self.url_label = QLabel()
        self.url_label.setTextFormat(Qt.TextFormat.RichText)
        self.url_label.setOpenExternalLinks(True)
        url_text = self.url
        if len(url_text) > 60:
            display_url = f"{url_text[:30]}...{url_text[-30:]}"
        else:
            display_url = url_text
        self.url_label.setText(f'<a href="{self.url}" style="text-decoration:none;">{display_url}</a>')
        self.url_label.setMaximumWidth(500)
        self.url_label.setToolTip(self.url)
        top_layout.addWidget(self.url_label)
        
        top_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Pending")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.status_label)
        
        layout.addLayout(top_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Stage progress layout (hidden by default)
        self.stage_layout = QHBoxLayout()
        self.stage_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add stage labels
        self.stage_labels = {}
        stages = [
            ("download", "Download"), 
            ("conversion", "Convert"), 
            ("transcription", "Transcribe"),
            ("translation", "Translate"), 
            ("export", "Export")
        ]
        
        for stage_id, stage_text in stages:
            label = QLabel(stage_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumWidth(80)
            label.setStyleSheet("color: #888;")
            self.stage_labels[stage_id] = label
            self.stage_layout.addWidget(label)
            
        layout.addLayout(self.stage_layout)
        self.setMaximumHeight(80)
        
        # Initially hide stage labels
        self._set_stage_visibility(False)
        
        # Set stylesheet
        self.setStyleSheet("""
            TaskItemWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        
    def _set_stage_visibility(self, visible: bool):
        """Show or hide stage progress labels"""
        for label in self.stage_labels.values():
            label.setVisible(visible)
            
    def _highlight_active_stage(self, active_stage: str):
        """Highlight the currently active processing stage"""
        for stage_id, label in self.stage_labels.items():
            if stage_id == active_stage:
                label.setStyleSheet("color: #2a82da; font-weight: bold;")
            elif self._is_completed_stage(stage_id, active_stage):
                label.setStyleSheet("color: #2a82da;")
            else:
                label.setStyleSheet("color: #888;")
                
    def _is_completed_stage(self, stage: str, current_stage: str) -> bool:
        """Check if a stage is completed based on the current active stage"""
        stage_order = ["download", "conversion", "transcription", "translation", "export"]
        try:
            stage_idx = stage_order.index(stage)
            current_idx = stage_order.index(current_stage)
            return stage_idx < current_idx
        except ValueError:
            return False
            
    def update_status(self, status: TaskStatus, progress: float, stage_progress: Dict[str, float] = None):
        """Update task status and progress"""
        # Update progress bar
        self.progress_bar.setValue(int(progress * 100))
        
        # Map status to user-friendly text and styling
        status_map = {
            TaskStatus.PENDING: {"text": "Pending", "style": "color: #888;"},
            TaskStatus.DOWNLOADING: {"text": "Downloading", "style": "color: #2a82da;"},
            TaskStatus.CONVERTING: {"text": "Converting", "style": "color: #2a82da;"},
            TaskStatus.TRANSCRIBING: {"text": "Transcribing", "style": "color: #2a82da;"},
            TaskStatus.TRANSLATING: {"text": "Translating", "style": "color: #2a82da;"},
            TaskStatus.EXPORTING: {"text": "Exporting", "style": "color: #2a82da;"},
            TaskStatus.COMPLETED: {"text": "Completed", "style": "color: #28a745;"},
            TaskStatus.FAILED: {"text": "Failed", "style": "color: #dc3545;"},
            TaskStatus.CANCELLED: {"text": "Cancelled", "style": "color: #ffc107;"},
            TaskStatus.SKIPPED: {"text": "Skipped", "style": "color: #6c757d;"}
        }
        
        # Update status label
        status_info = status_map.get(status, {"text": "Unknown", "style": "color: #888;"})
        self.status_label.setText(status_info["text"])
        self.status_label.setStyleSheet(status_info["style"])
        
        # Handle stage progress
        if status in [TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, 
                      TaskStatus.TRANSLATING, TaskStatus.EXPORTING]:
            # Show stage progress indicators
            self._set_stage_visibility(True)
            
            # Map status to active stage
            status_to_stage = {
                TaskStatus.DOWNLOADING: "download",
                TaskStatus.CONVERTING: "conversion",
                TaskStatus.TRANSCRIBING: "transcription",
                TaskStatus.TRANSLATING: "translation",
                TaskStatus.EXPORTING: "export"
            }
            active_stage = status_to_stage.get(status)
            self._highlight_active_stage(active_stage)
            
        elif status == TaskStatus.COMPLETED:
            # All stages complete
            self._set_stage_visibility(True)
            for label in self.stage_labels.values():
                label.setStyleSheet("color: #28a745;")
                
        elif status == TaskStatus.FAILED or status == TaskStatus.CANCELLED:
            # Show stage progress but highlight failure
            self._set_stage_visibility(True)
            
        else:
            # Hide stage progress for pending tasks
            self._set_stage_visibility(False)
            
    def show_error(self, error_message: str):
        """Display error status and message"""
        self.update_status(TaskStatus.FAILED, 0)
        self.status_label.setToolTip(error_message)
        
        # Add a small indicator to show there's an error tooltip
        self.status_label.setText("Failed ⓘ")


class UrlDropBox(QLineEdit):
    """Custom URL input with drag and drop support"""
    
    urls_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter YouTube URL or drag and drop video links here")
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for URLs"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for URLs"""
        mime_data = event.mimeData()
        urls = []
        
        if mime_data.hasUrls():
            # Extract URLs from QUrls
            for url in mime_data.urls():
                urls.append(url.toString())
        elif mime_data.hasText():
            # Extract URLs from text, assuming one URL per line
            text = mime_data.text()
            for line in text.strip().split('\n'):
                line = line.strip()
                if line:
                    urls.append(line)
                    
        if urls:
            # If only one URL, set it in the text field
            if len(urls) == 1:
                self.setText(urls[0])
            # Emit signal with all URLs
            self.urls_dropped.emit(urls)
            
        event.acceptProposedAction()


class SettingsDialog(QDialog):
    """Application settings dialog"""
    
    def __init__(self, settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.settings = settings.copy()  # Work with a copy of settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        self._init_ui()
        
    def _init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tabs for different setting categories
        tab_widget = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        current_theme = "Dark" if self.settings.get("theme") == "dark" else "Light"
        self.theme_combo.setCurrentText(current_theme)
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings.get("output_dir", ""))
        output_dir_layout.addWidget(self.output_dir_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_output_dir)
        output_dir_layout.addWidget(browse_button)
        
        general_layout.addRow("Output Directory:", output_dir_layout)
        
        # Default model
        self.model_combo = QComboBox()
        self.model_combo.addItems(WHISPER_MODELS)
        current_model = self.settings.get("default_model", "small")
        if current_model in WHISPER_MODELS:
            self.model_combo.setCurrentText(current_model)
        general_layout.addRow("Default Model:", self.model_combo)
        
        # Concurrency
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 10)
        self.concurrency_spin.setValue(self.settings.get("concurrency", 2))
        general_layout.addRow("Concurrent Tasks:", self.concurrency_spin)
        
        # Default language
        self.language_combo = QComboBox()
        for lang_code, lang_name in LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)
        
        current_lang = self.settings.get("default_language", "None")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
                
        general_layout.addRow("Default Target Language:", self.language_combo)
        
        # Cache settings tab
        cache_tab = QWidget()
        cache_layout = QFormLayout(cache_tab)
        
        # Enable cache
        self.cache_enabled_check = QCheckBox()
        self.cache_enabled_check.setChecked(self.settings.get("cache_enabled", True))
        cache_layout.addRow("Enable Caching:", self.cache_enabled_check)
        
        # Cache directory
        cache_dir_layout = QHBoxLayout()
        self.cache_dir_edit = QLineEdit(self.settings.get("cache_dir", ""))
        cache_dir_layout.addWidget(self.cache_dir_edit)
        
        cache_browse_button = QPushButton("Browse...")
        cache_browse_button.clicked.connect(self._browse_cache_dir)
        cache_dir_layout.addWidget(cache_browse_button)
        
        cache_layout.addRow("Cache Directory:", cache_dir_layout)
        
        # Cache size limit
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 10000)  # 100MB to 10GB
        self.cache_size_spin.setValue(int(self.settings.get("cache_size_mb", 1000)))
        self.cache_size_spin.setSuffix(" MB")
        cache_layout.addRow("Cache Size Limit:", self.cache_size_spin)
        
        # TTL
        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(1, 365)  # 1 to 365 days
        # Convert seconds to days
        ttl_days = int(self.settings.get("cache_ttl", 60 * 60 * 24 * 30) / (60 * 60 * 24))
        self.cache_ttl_spin.setValue(ttl_days)
        self.cache_ttl_spin.setSuffix(" days")
        cache_layout.addRow("Cache Item TTL:", self.cache_ttl_spin)
        
        # Add cache cleanup button
        self.clean_cache_button = QPushButton("Clean Cache Now")
        cache_layout.addRow("", self.clean_cache_button)
        
        # Add tabs to tab widget
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(cache_tab, "Cache")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _browse_output_dir(self):
        """Browse for output directory"""
        current_dir = self.output_dir_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", current_dir
        )
        if directory:
            self.output_dir_edit.setText(directory)
            
    def _browse_cache_dir(self):
        """Browse for cache directory"""
        current_dir = self.cache_dir_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory", current_dir
        )
        if directory:
            self.cache_dir_edit.setText(directory)
            
    def get_settings(self) -> Dict[str, Any]:
        """Get the updated settings"""
        # Update settings with new values
        self.settings["theme"] = self.theme_combo.currentText().lower()
        self.settings["output_dir"] = self.output_dir_edit.text()
        self.settings["default_model"] = self.model_combo.currentText()
        self.settings["concurrency"] = self.concurrency_spin.value()
        self.settings["default_language"] = self.language_combo.currentData()
        
        # Cache settings
        self.settings["cache_enabled"] = self.cache_enabled_check.isChecked()
        self.settings["cache_dir"] = self.cache_dir_edit.text()
        self.settings["cache_size_mb"] = self.cache_size_spin.value()
        # Convert days to seconds
        self.settings["cache_ttl"] = self.cache_ttl_spin.value() * 24 * 60 * 60
        
        return self.settings


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.settings = self._load_settings()
        self.cache_manager = self._init_cache_manager()
        self.batch_processor = BatchProcessor(
            cache_manager=self.cache_manager,
            concurrency=self.settings.get("concurrency", 2)
        )
        
        # Set up UI
        self._init_ui()
        
        # Set window properties
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(800, 600)
        
        # Connect batch processor signals
        self.batch_processor.set_progress_callback(self._on_progress_update)
        self.batch_processor.set_completion_callback(self._on_batch_completed)
        
        # Apply settings
        self._apply_settings()
        
    def _init_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # URL Input section
        url_group = QGroupBox("YouTube URL")
        url_layout = QVBoxLayout(url_group)
        
        # URL input with drag & drop support
        self.url_input = UrlDropBox()
        self.url_input.urls_dropped.connect(self._on_urls_dropped)
        url_layout.addWidget(self.url_input)
        
        # URL input buttons
        url_buttons_layout = QHBoxLayout()
        
        self.add_url_button = QPushButton("Add URL")
        self.add_url_button.clicked.connect(self._on_add_url)
        url_buttons_layout.addWidget(self.add_url_button)
        
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self._on_paste_from_clipboard)
        url_buttons_layout.addWidget(self.paste_button)
        
        self.clear_urls_button = QPushButton("Clear All")
        self.clear_urls_button.clicked.connect(self._on_clear_urls)
        url_buttons_layout.addWidget(self.clear_urls_button)
        
        url_layout.addLayout(url_buttons_layout)
        main_layout.addWidget(url_group)
        
        # Options & settings section
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)
        
        # Whisper model selection
        model_label = QLabel("Model:")
        options_layout.addWidget(model_label, 0, 0)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(WHISPER_MODELS)
        default_model = self.settings.get("default_model", "small")
        if default_model in WHISPER_MODELS:
            self.model_combo.setCurrentText(default_model)
        options_layout.addWidget(self.model_combo, 0, 1)
        
        # Target language for translation
        language_label = QLabel("Target Language:")
        options_layout.addWidget(language_label, 0, 2)
        
        self.language_combo = QComboBox()
        for lang_code, lang_name in LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)
            
        default_lang = self.settings.get("default_language", "None")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == default_lang:
                self.language_combo.setCurrentIndex(i)
                break
        options_layout.addWidget(self.language_combo, 0, 3)
        
        # Output directory
        output_label = QLabel("Output Folder:")
        options_layout.addWidget(output_label, 1, 0)
        
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings.get("output_dir", ""))
        self.output_dir_edit.setPlaceholderText("Default output directory")
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_button = QPushButton("Browse...")
        self.browse_output_button.clicked.connect(self._on_browse_output)
        output_dir_layout.addWidget(self.browse_output_button)
        
        options_layout.addLayout(output_dir_layout, 1, 1, 1, 3)
        
        # Export formats
        formats_label = QLabel("Export Formats:")
        options_layout.addWidget(formats_label, 2, 0)
        
        formats_layout = QHBoxLayout()
        self.format_checkboxes = {}
        
        for fmt_code, fmt_name in EXPORT_FORMATS.items():
            checkbox = QCheckBox(fmt_name)
            if fmt_code == "srt":  # Default to SRT always checked
                checkbox.setChecked(True)
            self.format_checkboxes[fmt_code] = checkbox
            formats_layout.addWidget(checkbox)
            
        options_layout.addLayout(formats_layout, 2, 1, 1, 3)
        
        # Add settings button
        self.settings_button = QPushButton("Settings...")
        self.settings_button.clicked.connect(self._on_show_settings)
        options_layout.addWidget(self.settings_button, 3, 3, Qt.AlignmentFlag.AlignRight)
        
        main_layout.addWidget(options_group)
        
        # Task list
        tasks_group = QGroupBox("Tasks")
        tasks_layout = QVBoxLayout(tasks_group)
        
        # Task list container (scrollable)
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setMinimumHeight(200)
        
        self.tasks_container = QWidget()
        self.tasks_container_layout = QVBoxLayout(self.tasks_container)
        self.tasks_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_container_layout.setSpacing(5)
        
        self.tasks_scroll.setWidget(self.tasks_container)
        tasks_layout.addWidget(self.tasks_scroll)
        
        # Task widgets dictionary
        self.task_widgets = {}
        
        # Overall progress
        progress_layout = QHBoxLayout()
        
        progress_label = QLabel("Overall Progress:")
        progress_layout.addWidget(progress_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        progress_layout.addWidget(self.overall_progress)
        
        tasks_layout.addLayout(progress_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self._on_start_processing)
        self.start_button.setEnabled(False)  # Disabled until URLs are added
        controls_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_processing)
        self.cancel_button.setEnabled(False)  # Disabled until processing starts
        controls_layout.addWidget(self.cancel_button)
        
        self.open_output_button = QPushButton("Open Output Folder")
        self.open_output_button.clicked.connect(self._on_open_output_folder)
        controls_layout.addWidget(self.open_output_button)
        
        tasks_layout.addLayout(controls_layout)
        
        main_layout.addWidget(tasks_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                return settings
            else:
                # Default settings
                return {
                    "theme": "dark",
                    "output_dir": os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeTranscriber"),
                    "default_model": "small",
                    "concurrency": 2,
                    "default_language": "None",
                    "cache_enabled": True,
                    "cache_dir": os.path.join(os.path.expanduser("~"), ".ytpro_cache"),
                    "cache_size_mb": 1000,
                    "cache_ttl": 60 * 60 * 24 * 30  # 30 days
                }
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return {
                "theme": "dark",
                "output_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
                "default_model": "small",
                "concurrency": 2,
                "default_language": "None"
            }
            
    def _save_settings(self):
        """Save application settings"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            self.status_bar.showMessage(f"Error saving settings: {str(e)}", 5000)
            
    def _init_cache_manager(self) -> Optional[CacheManager]:
        """Initialize the cache manager"""
        if not self.settings.get("cache_enabled", True):
            return None
            
        try:
            cache_dir = self.settings.get("cache_dir", "")
            if not cache_dir:
                cache_dir = os.path.join(os.path.expanduser("~"), ".ytpro_cache")
                
            cache_size_mb = self.settings.get("cache_size_mb", 1000)
            cache_size_bytes = cache_size_mb * 1024 * 1024
            
            cache_ttl = self.settings.get("cache_ttl", 60 * 60 * 24 * 30)  # 30 days default
            
            return CacheManager(
                base_dir=cache_dir,
                ttl=cache_ttl,
                size_limit=cache_size_bytes
            )
        except Exception as e:
            logger.error(f"Error initializing cache: {str(e)}")
            self.status_bar.showMessage(f"Error initializing cache: {str(e)}", 5000)
            return None
            
    def _apply_settings(self):
        """Apply settings to the UI and components"""
        # Apply theme when theme changes
        pass  # Theme is applied at the application level
        
        # Update batch processor with new concurrency
        if hasattr(self, 'batch_processor'):
            self.batch_processor.concurrency = self.settings.get("concurrency", 2)
            
        # Update cache manager if cache settings changed
        # This would typically be done on app restart, but we could reinitialize it here
            
    def _on_add_url(self):
        """Add URL from input field to task list"""
        url = self.url_input.text().strip()
        if not url:
            self.status_bar.showMessage("Please enter a YouTube URL", 3000)
            return
            
        if not self.batch_processor.validate_url(url):
            self.status_bar.showMessage("Invalid YouTube URL", 3000)
            return
            
        self._add_url_to_list(url)
        self.url_input.clear()
        
    def _on_urls_dropped(self, urls: List[str]):
        """Handle dropped URLs"""
        valid_urls = []
        for url in urls:
            if self.batch_processor.validate_url(url):
                valid_urls.append(url)
                self._add_url_to_list(url)
                
        if valid_urls:
            self.status_bar.showMessage(f"Added {len(valid_urls)} valid URLs", 3000)
        else:
            self.status_bar.showMessage("No valid YouTube URLs found", 3000)
            
    def _on_paste_from_clipboard(self):
        """Paste URLs from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            self.status_bar.showMessage("Clipboard is empty", 3000)
            return
            
        # Parse URLs from clipboard (one per line)
        urls = []
        for line in text.strip().split('\n'):
            url = line.strip()
            if url and self.batch_processor.validate_url(url):
                urls.append(url)
                self._add_url_to_list(url)
                
        if urls:
            self.status_bar.showMessage(f"Added {len(urls)} valid URLs from clipboard", 3000)
        else:
            self.status_bar.showMessage("No valid YouTube URLs found in clipboard", 3000)
            
    def _on_clear_urls(self):
        """Clear all URLs from the task list"""
        if not self.task_widgets:
            return
            
        # Ask for confirmation if there are tasks
        if len(self.task_widgets) > 0:
            confirm = QMessageBox.question(
                self, 
                "Clear All Tasks", 
                "Are you sure you want to clear all tasks?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.No:
                return
                
        # Clear tasks
        for widget in self.task_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
            
        self.task_widgets.clear()
        self.start_button.setEnabled(False)
        self.status_bar.showMessage("All tasks cleared", 3000)
        
    def _on_browse_output(self):
        """Browse for output directory"""
        current_dir = self.output_dir_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", current_dir
        )
        if directory:
            self.output_dir_edit.setText(directory)
            self.settings["output_dir"] = directory
            self._save_settings()
            
    def _on_show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated settings
            new_settings = dialog.get_settings()
            
            # Check if theme changed
            theme_changed = new_settings.get("theme") != self.settings.get("theme")
            
            # Check if cache settings changed
            cache_settings_changed = (
                new_settings.get("cache_enabled") != self.settings.get("cache_enabled") or
                new_settings.get("cache_dir") != self.settings.get("cache_dir") or
                new_settings.get("cache_size_mb") != self.settings.get("cache_size_mb") or
                new_settings.get("cache_ttl") != self.settings.get("cache_ttl")
            )
            
            # Update settings
            self.settings = new_settings
            self._save_settings()
            
            # Apply settings
            self._apply_settings()
            
            # Update UI with new default values
            if self.settings.get("default_model") in WHISPER_MODELS:
                self.model_combo.setCurrentText(self.settings.get("default_model"))
                
            default_lang = self.settings.get("default_language", "None")
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == default_lang:
                    self.language_combo.setCurrentIndex(i)
                    break
                    
            self.output_dir_edit.setText(self.settings.get("output_dir", ""))
            
            # Notify user if theme change requires restart
            if theme_changed:
                QMessageBox.information(
                    self,
                    "Theme Changed",
                    "The theme will be applied when you restart the application."
                )
                
    def _add_url_to_list(self, url: str):
        """Add a URL to the task list"""
        # Skip if URL already in list
        if url in self.task_widgets:
            self.status_bar.showMessage(f"URL already in list: {url}", 3000)
            return
            
        # Create task widget and add to layout
        task_widget = TaskItemWidget(url)
        self.tasks_container_layout.addWidget(task_widget)
        self.task_widgets[url] = task_widget
        
        # Enable start button if there are tasks
        self.start_button.setEnabled(True)
        
    def _on_start_processing(self):
        """Start batch processing"""
        # Validate settings
        if not self._validate_settings():
            return
            
        # Get selected URLs
        urls = list(self.task_widgets.keys())
        if not urls:
            self.status_bar.showMessage("No URLs to process", 3000)
            return
            
        # Get output directory
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = self.settings.get("output_dir", "")
            
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                msg = f"Error creating output directory: {str(e)}"
                logger.error(msg)
                QMessageBox.critical(self, "Error", msg)
                return
                
        # Get selected model
        model = self.model_combo.currentText()
        
        # Get target language (None if no translation)
        target_lang = self.language_combo.currentData()
        if target_lang == "None":
            target_lang = None
            
        # Get selected export formats
        formats = self._get_selected_formats()
        if not formats:
            QMessageBox.warning(self, "Warning", "No export formats selected. Please select at least one format.")
            return
            
        # Update UI state
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.settings_button.setEnabled(False)
        
        # Reset progress
        self.overall_progress.setValue(0)
        
        # Reset task status
        for task_widget in self.task_widgets.values():
            task_widget.update_status(TaskStatus.PENDING, 0)
            
        # Start batch processing
        result = self.batch_processor.process_batch(
            urls=urls,
            model=model,
            target_lang=target_lang,
            output_dir=output_dir,
            formats=formats
        )
        
        if result.get("status") == "started":
            self.status_bar.showMessage(f"Processing {len(urls)} URLs...")
        else:
            error_msg = result.get("message", "Unknown error")
            self.status_bar.showMessage(f"Error starting batch: {error_msg}", 5000)
            
            # Restore UI state
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.settings_button.setEnabled(True)
            
    def _on_cancel_processing(self):
        """Cancel batch processing"""
        if self.batch_processor.status == BatchStatus.RUNNING:
            cancel_result = self.batch_processor.cancel()
            if cancel_result:
                self.status_bar.showMessage("Cancelling batch processing...")
                
                # UI will be updated when batch completion callback is triggered
            else:
                self.status_bar.showMessage("Failed to cancel batch processing", 3000)
                
    def _on_progress_update(self, data: Dict[str, Any]):
        """Handle progress updates from batch processor"""
        # Update individual task progress
        if data.get("type") == "task_progress":
            task = data.get("task", {})
            url = task.get("url")
            if url in self.task_widgets:
                status_str = task.get("status", "PENDING")
                try:
                    status = TaskStatus[status_str]
                except KeyError:
                    status = TaskStatus.PENDING
                    
                progress = task.get("progress", 0)
                stage_progress = task.get("stage_progress", {})
                
                self.task_widgets[url].update_status(status, progress, stage_progress)
                
                # Show error if present
                if status == TaskStatus.FAILED and task.get("error"):
                    self.task_widgets[url].show_error(task.get("error"))
                    
        # Update overall batch progress
        batch_progress = data.get("batch_progress", 0)
        self._update_overall_progress(batch_progress)
        
        # Update status message
        batch_status = data.get("batch_status", "IDLE")
        batch_status_map = {
            "RUNNING": "Processing...",
            "PAUSED": "Paused",
            "COMPLETED": "Completed",
            "CANCELLED": "Cancelled",
            "FAILED": "Failed"
        }
        
        if batch_status in batch_status_map:
            completed = data.get("completed", 0)
            total = data.get("total", 0)
            if total > 0:
                self.status_bar.showMessage(
                    f"{batch_status_map[batch_status]} {completed}/{total} tasks"
                )
                
        # Update UI state for non-running states
        if batch_status != "RUNNING":
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.settings_button.setEnabled(True)
            
    def _on_batch_completed(self, data: Dict[str, Any]):
        """Handle batch completion"""
        batch_status = data.get("status", "IDLE")
        completed = data.get("completed", 0)
        failed = data.get("failed", 0)
        total = data.get("total", 0)
        
        # Update status bar
        if batch_status == "COMPLETED":
            if failed == 0:
                self.status_bar.showMessage(f"All {total} tasks completed successfully", 5000)
            else:
                self.status_bar.showMessage(
                    f"Batch completed with {completed} successes and {failed} failures", 5000
                )
        elif batch_status == "CANCELLED":
            self.status_bar.showMessage(f"Batch cancelled. {completed} tasks completed.", 5000)
        elif batch_status == "FAILED":
            self.status_bar.showMessage(f"Batch failed. {completed} tasks completed, {failed} failed.", 5000)
            
        # Update UI state
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.settings_button.setEnabled(True)
        
        # Update progress bar to match reality (in case of cancellation)
        if batch_status == "CANCELLED":
            if total > 0:
                progress = completed / total
                self._update_overall_progress(progress)
                
        # Show notification if completely successful
        if batch_status == "COMPLETED" and failed == 0 and total > 0:
            QMessageBox.information(
                self,
                "Processing Complete",
                f"All {total} tasks have been processed successfully!"
            )
            
    def _on_open_output_folder(self):
        """Open the output folder in the default file explorer"""
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = self.settings.get("output_dir", "")
            
        if not output_dir or not os.path.exists(output_dir):
            self.status_bar.showMessage("Output directory does not exist", 3000)
            return
            
        # Open folder using the appropriate platform-specific method
        try:
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux and other Unix-like
                os.system(f'xdg-open "{output_dir}"')
                
            self.status_bar.showMessage(f"Opened output folder: {output_dir}", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Error opening output folder: {str(e)}", 3000)
            
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        # Save settings and window state
        self._save_settings()
        self._save_window_state()
        
        # Check if processing is in progress
        if self.batch_processor.status == BatchStatus.RUNNING:
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Processing is still in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Cancel processing and accept close event
                self.batch_processor.cancel()
                event.accept()
            else:
                # Reject close event
                event.ignore()
        else:
            # Accept close event
            event.accept()
            
    def _save_window_state(self):
        """Save window state to settings"""
        self.settings["window_geometry"] = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height(),
            "maximized": self.isMaximized()
        }
        
    def _restore_window_state(self):
        """Restore window state from settings"""
        geom = self.settings.get("window_geometry", {})
        if geom:
            # Set position and size
            x = geom.get("x", 100)
            y = geom.get("y", 100)
            width = geom.get("width", 800)
            height = geom.get("height", 600)
            
            self.setGeometry(x, y, width, height)
            
            # Set maximized state
            if geom.get("maximized", False):
                self.showMaximized()
                
    def _get_selected_formats(self) -> List[str]:
        """Get the selected export formats"""
        formats = []
        for fmt, checkbox in self.format_checkboxes.items():
            if checkbox.isChecked():
                formats.append(fmt)
        return formats
        
    def _update_overall_progress(self, progress: float):
        """Update the overall progress bar"""
        self.overall_progress.setValue(int(progress * 100))
        
    def _validate_settings(self) -> bool:
        """Validate settings before starting processing"""
        # Check output directory
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = self.settings.get("output_dir", "")
            
        if not output_dir:
            QMessageBox.warning(
                self,
                "Missing Output Directory",
                "Please specify an output directory for the transcripts."
            )
            return False
            
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not create output directory: {str(e)}"
                )
                return False
                
        # Check if at least one format is selected
        if not self._get_selected_formats():
            QMessageBox.warning(
                self,
                "No Export Formats",
                "Please select at least one export format."
            )
            return False
            
        return True


def create_settings_file_if_missing():
    """Create settings.py file if it doesn't exist"""
    settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.py")
    
    if not os.path.exists(settings_file):
        with open(settings_file, 'w') as f:
            f.write("""import os
import json
import logging
from typing import Dict, Any

# Setup logger
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    "theme": "dark",
    "output_dir": os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeTranscriber"),
    "default_model": "small",
    "concurrency": 2,
    "default_language": "None",
    "cache_enabled": True,
    "cache_dir": os.path.join(os.path.expanduser("~"), ".ytpro_cache"),
    "cache_size_mb": 1000,
    "cache_ttl": 60 * 60 * 24 * 30  # 30 days
}

def load_settings() -> Dict[str, Any]:
    """Load application settings from file"""
    try:
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            return settings
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save application settings to file"""
    try:
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return False
""")
