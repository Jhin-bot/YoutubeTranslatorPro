import os
import sys
import time
from typing import List, Optional, Callable

from PyQt6.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QRect, QSequentialAnimationGroup, QParallelAnimationGroup,
    pyqtSignal, pyqtSlot
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QBrush, QPen, QFont, 
    QLinearGradient, QRadialGradient, QPainterPath, QFontMetrics
)
from PyQt6.QtWidgets import (
    QApplication, QSplashScreen, QWidget, QLabel, QProgressBar,
    QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
)

from ui import APP_NAME, APP_VERSION, Theme, ThemeManager


class LoadingStep:
    """Represents a loading step in the application initialization process"""
    
    def __init__(self, name: str, weight: float = 1.0, callback: Optional[Callable] = None):
        """
        Initialize a loading step
        
        Args:
            name: Name of the loading step
            weight: Relative weight for progress calculation
            callback: Optional callback to execute during this step
        """
        self.name = name
        self.weight = weight
        self.callback = callback
        self.completed = False
        
    def execute(self) -> bool:
        """Execute the loading step"""
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                print(f"Error in loading step '{self.name}': {str(e)}")
                return False
        
        self.completed = True
        return True


class AnimatedLabel(QLabel):
    """Label with animation capabilities"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        
    def fade_in(self, duration: int = 500):
        """Fade in the label"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
    def fade_out(self, duration: int = 500):
        """Fade out the label"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.start()


class LogoWidget(QWidget):
    """Custom widget for displaying the application logo with animations"""
    
    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.highlight_pos = 0
        self.highlight_direction = 1
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(50)  # 20 fps animation
        
        # Set fixed size
        self.setFixedSize(size, size)
        
        # Dark theme flag
        self.is_dark_theme = True
        
    def _update_animation(self):
        """Update animation state"""
        # Rotate effect
        self.angle = (self.angle + 2) % 360
        
        # Highlight effect
        self.highlight_pos += 0.02 * self.highlight_direction
        if self.highlight_pos > 1.0:
            self.highlight_pos = 1.0
            self.highlight_direction = -1
        elif self.highlight_pos < 0.0:
            self.highlight_pos = 0.0
            self.highlight_direction = 1
            
        self.update()
        
    def set_theme(self, is_dark: bool):
        """Set theme for the logo"""
        self.is_dark_theme = is_dark
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event for the logo"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Center of the widget
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 10
        
        # Save painter state
        painter.save()
        
        # Translate to center for rotation
        painter.translate(center_x, center_y)
        
        # Define colors based on theme
        if self.is_dark_theme:
            bg_color = QColor(53, 53, 53)
            outer_ring_color = QColor(80, 80, 80)
            inner_ring_color = QColor(30, 30, 30)
            highlight_color = QColor(42, 130, 218)
        else:
            bg_color = QColor(240, 240, 240)
            outer_ring_color = QColor(180, 180, 180)
            inner_ring_color = QColor(220, 220, 220)
            highlight_color = QColor(42, 130, 218)
            
        # Draw outer circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(outer_ring_color))
        painter.drawEllipse(QPoint(0, 0), int(radius), int(radius))
        
        # Draw inner circle
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(QPoint(0, 0), int(radius * 0.85), int(radius * 0.85))
        
        # Draw waveform bars
        painter.setPen(QPen(highlight_color, 3))
        painter.rotate(self.angle)  # Rotate for animation
        
        # Draw 6 audio bars
        for i in range(6):
            bar_height = radius * 0.5
            
            # Make the bars have different heights in a wave pattern
            if i % 2 == 0:
                mod_height = bar_height * (0.7 + 0.3 * abs(self.highlight_pos - 0.5) * 2)
            else:
                mod_height = bar_height * (0.5 + 0.5 * self.highlight_pos)
                
            # Calculate bar position with angle
            angle = i * 60  # 6 bars, 360/6 = 60 degrees
            painter.save()
            painter.rotate(angle)
            painter.drawLine(0, 0, 0, -mod_height)
            painter.restore()
            
        # Add a small circle in the center
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(highlight_color))
        painter.drawEllipse(QPoint(0, 0), int(radius * 0.15), int(radius * 0.15))
        
        # Restore painter state
        painter.restore()
        
        # Draw text for YT
        painter.setFont(QFont("Arial", int(radius * 0.4), QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255) if self.is_dark_theme else QColor(40, 40, 40))
        text_rect = QRect(0, 0, self.width(), self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "YT")


class ModernSplashScreen(QSplashScreen):
    """Modern splash screen with animations and progress tracking"""
    
    def __init__(self, app_name: str, app_version: str, is_dark_theme: bool = True):
        """
        Initialize the splash screen
        
        Args:
            app_name: Application name
            app_version: Application version
            is_dark_theme: Whether to use dark theme
        """
        # Create a pixmap for the base splash screen
        pixmap = QPixmap(500, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        # Store properties
        self.app_name = app_name
        self.app_version = app_version
        self.is_dark_theme = is_dark_theme
        self.loading_steps: List[LoadingStep] = []
        self.current_step = 0
        self.progress = 0.0
        self.status_text = "Initializing..."
        
        # Setup UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI elements"""
        # Main widget with a layout
        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        
        # Size the main widget to match the splash screen
        self.main_widget.setFixedSize(500, 400)
        
        # Set background color based on theme
        if self.is_dark_theme:
            bg_color = QColor(30, 30, 30)
            text_color = QColor(255, 255, 255)
            accent_color = QColor(42, 130, 218)
        else:
            bg_color = QColor(245, 245, 245)
            text_color = QColor(20, 20, 20)
            accent_color = QColor(42, 130, 218)
            
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 240);
                color: rgb({text_color.red()}, {text_color.green()}, {text_color.blue()});
                border-radius: 10px;
            }}
            QProgressBar {{
                border: 1px solid rgba({accent_color.red()}, {accent_color.green()}, {accent_color.blue()}, 150);
                border-radius: 5px;
                text-align: center;
                color: transparent;
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 100);
            }}
            QProgressBar::chunk {{
                background-color: rgba({accent_color.red()}, {accent_color.green()}, {accent_color.blue()}, 200);
                border-radius: 4px;
            }}
        """)
        
        # Add logo
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo = LogoWidget(size=120)
        self.logo.set_theme(self.is_dark_theme)
        logo_layout.addWidget(self.logo)
        
        self.main_layout.addLayout(logo_layout)
        self.main_layout.addSpacing(10)
        
        # Add application name
        self.app_name_label = AnimatedLabel(self.app_name)
        self.app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_name_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.main_layout.addWidget(self.app_name_label)
        
        # Add version
        self.version_label = AnimatedLabel(f"Version {self.app_version}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setFont(QFont("Arial", 10))
        self.main_layout.addWidget(self.version_label)
        
        self.main_layout.addSpacing(20)
        
        # Add status text
        self.status_label = AnimatedLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setText(self.status_text)
        self.main_layout.addWidget(self.status_label)
        
        self.main_layout.addSpacing(5)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        # Add space at the bottom
        self.main_layout.addStretch()
        
        # Start animations
        QTimer.singleShot(100, self._start_animations)
        
    def _start_animations(self):
        """Start the initial animations"""
        self.app_name_label.fade_in(800)
        QTimer.singleShot(200, lambda: self.version_label.fade_in(800))
        QTimer.singleShot(400, lambda: self.status_label.fade_in(800))
        
    def add_loading_step(self, name: str, weight: float = 1.0, callback: Optional[Callable] = None):
        """Add a loading step to be executed during startup"""
        self.loading_steps.append(LoadingStep(name, weight, callback))
        
    def set_status(self, text: str):
        """Set the current status text"""
        self.status_text = text
        self.status_label.setText(text)
        QApplication.processEvents()
        
    def update_progress(self, value: float):
        """Update the progress value (0-1)"""
        self.progress = max(0.0, min(1.0, value))
        self.progress_bar.setValue(int(self.progress * 100))
        QApplication.processEvents()
        
    def execute_loading_steps(self):
        """Execute all loading steps in sequence"""
        if not self.loading_steps:
            self.update_progress(1.0)
            return
            
        # Calculate total weight
        total_weight = sum(step.weight for step in self.loading_steps)
        current_progress = 0.0
        
        # Execute each step
        for i, step in enumerate(self.loading_steps):
            self.set_status(f"Loading: {step.name}...")
            self.current_step = i
            
            # Execute the step
            success = step.execute()
            
            # Update progress based on step weight
            current_progress += step.weight / total_weight
            self.update_progress(current_progress)
            
            # Sleep a bit for visual effect
            time.sleep(0.1)
            
            # Handle step failure
            if not success:
                self.set_status(f"Error in loading step: {step.name}")
                return False
        
        # All steps completed
        self.set_status("Startup completed!")
        self.update_progress(1.0)
        return True
    
    def finish(self, main_window=None, fade_duration: int = 500):
        """
        Finish the splash screen with fade-out transition
        
        Args:
            main_window: Main window to show after splash
            fade_duration: Duration of fade out animation in ms
        """
        # Create opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self.main_widget)
        self.opacity_effect.setOpacity(1.0)
        self.main_widget.setGraphicsEffect(self.opacity_effect)
        
        # Create fade out animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(fade_duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # When animation finishes, close splash and show main window
        def finish_splash():
            self.close()
            if main_window:
                main_window.show()
                
        self.fade_animation.finished.connect(finish_splash)
        self.fade_animation.start()
    
    def display_error(self, error_message: str):
        """
        Display an error message on the splash screen
        
        Args:
            error_message: Error message to display
        """
        self.set_status(f"Error: {error_message}")
        
        # Change progress bar color to red
        if self.is_dark_theme:
            error_color = QColor(200, 50, 50)
        else:
            error_color = QColor(220, 60, 60)
        
        # Update progress bar style for error state
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid rgba({error_color.red()}, {error_color.green()}, {error_color.blue()}, 150);
                border-radius: 5px;
                text-align: center;
                background-color: rgba(0, 0, 0, 30);
            }}
            QProgressBar::chunk {{
                background-color: rgba({error_color.red()}, {error_color.green()}, {error_color.blue()}, 200);
                border-radius: 4px;
            }}
        """)


def create_splash_screen(app) -> ModernSplashScreen:
    """
    Create and configure a splash screen
    
    Args:
        app: QApplication instance
        
    Returns:
        Configured splash screen instance
    """
    # Get theme from app settings
    is_dark_theme = True
    try:
        from ui import Theme, ThemeManager
        # Detect current theme from application settings
        # This is a placeholder and should use your actual theme detection logic
        is_dark_theme = True  # Default to dark theme
    except:
        # Fallback to dark theme if there's any issue
        is_dark_theme = True
    
    # Create splash screen
    splash = ModernSplashScreen(APP_NAME, APP_VERSION, is_dark_theme)
    
    # Add loading steps
    splash.add_loading_step("Initializing Components", 1.0)
    splash.add_loading_step("Loading Configuration", 1.5)
    splash.add_loading_step("Preparing Resources", 1.0)
    splash.add_loading_step("Checking Dependencies", 2.0)
    splash.add_loading_step("Setting Up UI", 2.5)
    
    # Show splash
    splash.show()
    app.processEvents()
    
    return splash

