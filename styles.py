"""
Modern styling and theming system for the YouTube Transcriber Pro application.
Provides color schemes, widget styles, icon definitions, animations, and layout constants.
"""

import os
import sys
import platform
from enum import Enum, auto
from typing import Dict, Any, Tuple, List, Optional, NamedTuple

from PyQt6.QtCore import (
    Qt, QSize, QEasingCurve, QPoint, QRect, QPropertyAnimation, QMargins
)
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QIcon, QPalette, QPixmap, QLinearGradient, QGradient
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QLabel, QLineEdit, QComboBox,
    QScrollArea, QScrollBar, QToolTip, QCheckBox, QRadioButton, QProgressBar,
    QSlider, QTabWidget, QTabBar, QToolBar, QMenuBar, QMenu, QListWidget,
    QGraphicsDropShadowEffect, QStyleFactory
)


# ==============================================================================
# COLOR SCHEMES
# ==============================================================================

class ColorRole(Enum):
    """Color roles for application theming"""
    PRIMARY = auto()            # Main brand color 
    SECONDARY = auto()          # Secondary brand color
    SUCCESS = auto()            # Success/Positive color
    WARNING = auto()            # Warning color
    ERROR = auto()              # Error/Danger color
    INFO = auto()               # Information color
    
    BACKGROUND = auto()         # Main background
    BACKGROUND_ALT = auto()     # Alternative background (cards, etc.)
    BACKGROUND_HOVER = auto()   # Hover state background 
    
    FOREGROUND = auto()         # Main text color
    FOREGROUND_DIM = auto()     # Secondary/dimmed text
    FOREGROUND_DISABLED = auto() # Disabled text
    
    BORDER = auto()             # Border color
    BORDER_LIGHT = auto()       # Lighter border color
    
    SHADOW = auto()             # Shadow color


class ColorPalette:
    """Color palette definition with light/dark variants"""
    
    def __init__(self, name: str, colors: Dict[ColorRole, QColor]):
        self.name = name
        self.colors = colors
        
    def get(self, role: ColorRole) -> QColor:
        """Get color for specific role"""
        return self.colors.get(role, QColor(0, 0, 0))
        
    def to_dict(self) -> Dict[str, str]:
        """Convert palette to dictionary of hex colors"""
        return {role.name.lower(): color.name() for role, color in self.colors.items()}


# Default Dark Theme Palette
DARK_PALETTE = ColorPalette("Dark", {
    ColorRole.PRIMARY: QColor(42, 130, 218),       # Blue
    ColorRole.SECONDARY: QColor(94, 92, 230),      # Purple
    ColorRole.SUCCESS: QColor(46, 204, 113),       # Green
    ColorRole.WARNING: QColor(241, 196, 15),       # Yellow
    ColorRole.ERROR: QColor(231, 76, 60),          # Red
    ColorRole.INFO: QColor(52, 152, 219),          # Light Blue
    
    ColorRole.BACKGROUND: QColor(30, 30, 30),      # Dark gray
    ColorRole.BACKGROUND_ALT: QColor(45, 45, 45),  # Medium gray
    ColorRole.BACKGROUND_HOVER: QColor(55, 55, 55), # Lighter gray
    
    ColorRole.FOREGROUND: QColor(240, 240, 240),   # Almost white
    ColorRole.FOREGROUND_DIM: QColor(180, 180, 180), # Light gray
    ColorRole.FOREGROUND_DISABLED: QColor(120, 120, 120), # Medium gray
    
    ColorRole.BORDER: QColor(70, 70, 70),          # Medium gray
    ColorRole.BORDER_LIGHT: QColor(90, 90, 90),    # Lighter gray
    
    ColorRole.SHADOW: QColor(0, 0, 0, 80)          # Semi-transparent black
})

# Default Light Theme Palette
LIGHT_PALETTE = ColorPalette("Light", {
    ColorRole.PRIMARY: QColor(42, 130, 218),       # Blue
    ColorRole.SECONDARY: QColor(94, 92, 230),      # Purple
    ColorRole.SUCCESS: QColor(46, 204, 113),       # Green
    ColorRole.WARNING: QColor(241, 196, 15),       # Yellow
    ColorRole.ERROR: QColor(231, 76, 60),          # Red
    ColorRole.INFO: QColor(52, 152, 219),          # Light Blue
    
    ColorRole.BACKGROUND: QColor(245, 245, 245),   # Light gray
    ColorRole.BACKGROUND_ALT: QColor(255, 255, 255), # White
    ColorRole.BACKGROUND_HOVER: QColor(235, 235, 235), # Slightly darker gray
    
    ColorRole.FOREGROUND: QColor(30, 30, 30),      # Almost black
    ColorRole.FOREGROUND_DIM: QColor(100, 100, 100), # Dark gray
    ColorRole.FOREGROUND_DISABLED: QColor(170, 170, 170), # Medium gray
    
    ColorRole.BORDER: QColor(220, 220, 220),       # Light gray
    ColorRole.BORDER_LIGHT: QColor(240, 240, 240), # Very light gray
    
    ColorRole.SHADOW: QColor(0, 0, 0, 30)          # Semi-transparent black
})


# ==============================================================================
# FONTS AND TYPOGRAPHY
# ==============================================================================

class FontWeight(Enum):
    """Font weight definitions"""
    THIN = QFont.Weight.Thin
    LIGHT = QFont.Weight.Light
    NORMAL = QFont.Weight.Normal
    MEDIUM = QFont.Weight.Medium
    BOLD = QFont.Weight.Bold
    BLACK = QFont.Weight.Black


class Typography:
    """Typography definitions for the application"""
    
    DEFAULT_FONT_FAMILY = "Segoe UI" if platform.system() == "Windows" else \
                         "SF Pro Text" if platform.system() == "Darwin" else \
                         "Roboto"
    
    MONOSPACE_FONT_FAMILY = "Consolas" if platform.system() == "Windows" else \
                          "SF Mono" if platform.system() == "Darwin" else \
                          "Ubuntu Mono"
    
    # Font size scale
    FONT_SIZE_XS = 10
    FONT_SIZE_S = 12 
    FONT_SIZE_M = 14
    FONT_SIZE_L = 16
    FONT_SIZE_XL = 20
    FONT_SIZE_XXL = 24
    
    @staticmethod
    def get_font(
        size: int = 14, 
        weight: FontWeight = FontWeight.NORMAL, 
        monospace: bool = False
    ) -> QFont:
        """Get a font with specified parameters"""
        family = Typography.MONOSPACE_FONT_FAMILY if monospace else Typography.DEFAULT_FONT_FAMILY
        font = QFont(family, size)
        font.setWeight(weight.value)
        return font


# ==============================================================================
# ICONS AND RESOURCES
# ==============================================================================

class IconSet:
    """Icon definitions for the application"""
    
    # Base path for icons
    ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icons")
    
    # Create icons directory if it doesn't exist
    os.makedirs(ICON_PATH, exist_ok=True)
    
    # Application icons
    APP_ICON = "app.png"
    SPLASH_ICON = "splash.png"
    
    # Action icons
    ICON_ADD = "add.png"
    ICON_REMOVE = "remove.png"
    ICON_EDIT = "edit.png"
    ICON_SAVE = "save.png"
    ICON_OPEN = "open.png"
    ICON_SETTINGS = "settings.png"
    ICON_SEARCH = "search.png"
    ICON_DOWNLOAD = "download.png"
    ICON_UPLOAD = "upload.png"
    ICON_PLAY = "play.png"
    ICON_PAUSE = "pause.png"
    ICON_STOP = "stop.png"
    ICON_REFRESH = "refresh.png"
    ICON_INFO = "info.png"
    ICON_WARNING = "warning.png"
    ICON_ERROR = "error.png"
    ICON_SUCCESS = "success.png"
    
    # File type icons
    ICON_FILE = "file.png"
    ICON_FOLDER = "folder.png"
    ICON_AUDIO = "audio.png"
    ICON_VIDEO = "video.png"
    ICON_TEXT = "text.png"
    ICON_SRT = "srt.png"
    
    @staticmethod
    def get_icon(name: str) -> QIcon:
        """Get an icon by name"""
        path = os.path.join(IconSet.ICON_PATH, name)
        if os.path.exists(path):
            return QIcon(path)
        else:
            # Return empty icon if file doesn't exist
            return QIcon()
            
    @staticmethod
    def get_pixmap(name: str, size: QSize = QSize(32, 32)) -> QPixmap:
        """Get a pixmap by name and size"""
        icon = IconSet.get_icon(name)
        return icon.pixmap(size)


# ==============================================================================
# ANIMATIONS
# ==============================================================================

class AnimationPresets:
    """Animation presets for the application"""
    
    # Duration presets (in milliseconds)
    DURATION_FAST = 150
    DURATION_NORMAL = 300
    DURATION_SLOW = 500
    
    # Easing curves
    EASE_IN_OUT = QEasingCurve.Type.InOutCubic
    EASE_OUT = QEasingCurve.Type.OutCubic
    EASE_IN = QEasingCurve.Type.InCubic
    EASE_BOUNCE = QEasingCurve.Type.OutBounce
    EASE_ELASTIC = QEasingCurve.Type.OutElastic
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = DURATION_NORMAL) -> QPropertyAnimation:
        """Create a fade-in animation for a widget"""
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect:
            return None
            
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(AnimationPresets.EASE_OUT)
        return animation
        
    @staticmethod
    def fade_out(widget: QWidget, duration: int = DURATION_NORMAL) -> QPropertyAnimation:
        """Create a fade-out animation for a widget"""
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect:
            return None
            
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(AnimationPresets.EASE_IN)
        return animation


# ==============================================================================
# LAYOUT AND SPACING
# ==============================================================================

class Spacing:
    """Spacing constants for layouts"""
    
    XXS = 2
    XS = 4
    S = 8
    M = 12
    L = 16
    XL = 24
    XXL = 32
    
    # Margins
    WINDOW_MARGINS = QMargins(L, L, L, L)
    CARD_MARGINS = QMargins(M, M, M, M)
    DIALOG_MARGINS = QMargins(L, L, L, L)
    

class Dimensions:
    """Common dimension constants"""
    
    # Widget sizes
    BUTTON_HEIGHT = 32
    INPUT_HEIGHT = 32
    ICON_SIZE_SMALL = QSize(16, 16)
    ICON_SIZE_MEDIUM = QSize(24, 24)
    ICON_SIZE_LARGE = QSize(32, 32)
    
    # Window sizes
    DIALOG_MIN_WIDTH = 400
    DIALOG_MIN_HEIGHT = 300
    MAIN_WINDOW_MIN_WIDTH = 800
    MAIN_WINDOW_MIN_HEIGHT = 600
    
    # Border radius
    BORDER_RADIUS_S = 4
    BORDER_RADIUS_M = 8
    BORDER_RADIUS_L = 12


# ==============================================================================
# STYLE SHEETS AND WIDGET STYLING
# ==============================================================================

class StyleManager:
    """Manages application styling and provides style sheets for widgets"""
    
    def __init__(self, is_dark_theme: bool = True):
        """Initialize the style manager"""
        self.palette = DARK_PALETTE if is_dark_theme else LIGHT_PALETTE
        self.is_dark_theme = is_dark_theme
        
    def set_theme(self, is_dark_theme: bool):
        """Change the current theme"""
        self.palette = DARK_PALETTE if is_dark_theme else LIGHT_PALETTE
        self.is_dark_theme = is_dark_theme
        
    def get_color(self, role: ColorRole) -> QColor:
        """Get a color for the current theme"""
        return self.palette.get(role)
        
    def get_app_stylesheet(self) -> str:
        """Get the global application stylesheet"""
        colors = self.palette.colors
        
        # Extract colors for stylesheet
        primary = colors[ColorRole.PRIMARY].name()
        secondary = colors[ColorRole.SECONDARY].name()
        success = colors[ColorRole.SUCCESS].name()
        warning = colors[ColorRole.WARNING].name()
        error = colors[ColorRole.ERROR].name()
        info = colors[ColorRole.INFO].name()
        
        bg = colors[ColorRole.BACKGROUND].name()
        bg_alt = colors[ColorRole.BACKGROUND_ALT].name()
        bg_hover = colors[ColorRole.BACKGROUND_HOVER].name()
        
        fg = colors[ColorRole.FOREGROUND].name()
        fg_dim = colors[ColorRole.FOREGROUND_DIM].name()
        fg_disabled = colors[ColorRole.FOREGROUND_DISABLED].name()
        
        border = colors[ColorRole.BORDER].name()
        border_light = colors[ColorRole.BORDER_LIGHT].name()
        
        # Build stylesheet
        return f"""
            /* Global styles */
            QWidget {{
                background-color: {bg};
                color: {fg};
                font-family: "{Typography.DEFAULT_FONT_FAMILY}";
                font-size: {Typography.FONT_SIZE_M}px;
            }}
            
            /* QLabel styles */
            QLabel {{
                background-color: transparent;
                padding: 2px;
            }}
            
            QLabel[heading="true"] {{
                font-size: {Typography.FONT_SIZE_XL}px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            
            QLabel[subheading="true"] {{
                font-size: {Typography.FONT_SIZE_L}px;
                color: {fg_dim};
            }}
            
            QLabel[error="true"] {{
                color: {error};
            }}
            
            QLabel[success="true"] {{
                color: {success};
            }}
            
            /* QPushButton styles */
            QPushButton {{
                background-color: {bg_alt};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 6px 16px;
                min-height: {Dimensions.BUTTON_HEIGHT}px;
            }}
            
            QPushButton:hover {{
                background-color: {bg_hover};
                border: 1px solid {primary};
            }}
            
            QPushButton:pressed {{
                background-color: {bg_hover};
                border: 1px solid {primary};
            }}
            
            QPushButton:disabled {{
                background-color: {bg};
                color: {fg_disabled};
                border: 1px solid {border};
            }}
            
            QPushButton[primary="true"] {{
                background-color: {primary};
                color: white;
                border: none;
            }}
            
            QPushButton[primary="true"]:hover {{
                background-color: {QColor(colors[ColorRole.PRIMARY]).lighter(110).name()};
            }}
            
            QPushButton[primary="true"]:pressed {{
                background-color: {QColor(colors[ColorRole.PRIMARY]).darker(110).name()};
            }}
            
            QPushButton[primary="true"]:disabled {{
                background-color: {QColor(colors[ColorRole.PRIMARY]).lighter(150).name()};
                color: rgba(255, 255, 255, 150);
            }}
            
            QPushButton[danger="true"] {{
                background-color: {error};
                color: white;
                border: none;
            }}
            
            QPushButton[danger="true"]:hover {{
                background-color: {QColor(colors[ColorRole.ERROR]).lighter(110).name()};
            }}
            
            QPushButton[danger="true"]:pressed {{
                background-color: {QColor(colors[ColorRole.ERROR]).darker(110).name()};
            }}
            
            QPushButton[flat="true"] {{
                background-color: transparent;
                border: none;
            }}
            
            QPushButton[flat="true"]:hover {{
                background-color: rgba(200, 200, 200, 20);
            }}
            
            QPushButton[flat="true"]:pressed {{
                background-color: rgba(200, 200, 200, 40);
            }}
            
            /* QLineEdit styles */
            QLineEdit {{
                background-color: {bg_alt};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 5px 8px;
                min-height: {Dimensions.INPUT_HEIGHT - 10}px;
                selection-background-color: {primary};
            }}
            
            QLineEdit:focus {{
                border: 1px solid {primary};
            }}
            
            QLineEdit:disabled {{
                background-color: {bg};
                color: {fg_disabled};
                border: 1px solid {border};
            }}
            
            /* QTextEdit styles */
            QTextEdit {{
                background-color: {bg_alt};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 5px;
                selection-background-color: {primary};
            }}
            
            QTextEdit:focus {{
                border: 1px solid {primary};
            }}
            
            /* QComboBox styles */
            QComboBox {{
                background-color: {bg_alt};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 5px 8px;
                min-height: {Dimensions.INPUT_HEIGHT - 10}px;
                selection-background-color: {primary};
            }}
            
            QComboBox:focus {{
                border: 1px solid {primary};
            }}
            
            QComboBox:disabled {{
                background-color: {bg};
                color: {fg_disabled};
                border: 1px solid {border};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {bg_alt};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                selection-background-color: {primary};
            }}
            
            /* QProgressBar styles */
            QProgressBar {{
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                background-color: {bg_alt};
                text-align: center;
                color: {fg};
                height: 8px;
            }}
            
            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: {Dimensions.BORDER_RADIUS_S - 1}px;
            }}
            
            /* QCheckBox styles */
            QCheckBox {{
                spacing: 8px;
                background-color: transparent;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {border};
                border-radius: 3px;
                background-color: {bg_alt};
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {primary};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {primary};
                border: 1px solid {primary};
                image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'><polyline points='20 6 9 17 4 12'></polyline></svg>");
            }}
            
            /* QRadioButton styles */
            QRadioButton {{
                spacing: 8px;
                background-color: transparent;
            }}
            
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {border};
                border-radius: 9px;
                background-color: {bg_alt};
            }}
            
            QRadioButton::indicator:unchecked:hover {{
                border: 1px solid {primary};
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {bg_alt};
                border: 1px solid {primary};
            }}
            
            QRadioButton::indicator:checked:hover {{
                border: 1px solid {primary};
            }}
            
            QRadioButton::indicator::checked:pressed {{
                background-color: {bg_alt};
            }}
                        
            /* QScrollBar styles */
            QScrollBar:vertical {{
                background-color: {bg};
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {border};
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {border_light};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {bg};
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {border};
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {border_light};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            /* QTabWidget and QTabBar styles */
            QTabWidget::pane {{
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: {bg};
                border: 1px solid {border};
                border-bottom: none;
                border-top-left-radius: {Dimensions.BORDER_RADIUS_S}px;
                border-top-right-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 8px 12px;
                min-width: 80px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {bg_alt};
                border-bottom: none;
            }}
            
            QTabBar::tab:hover {{
                background-color: {bg_hover};
            }}
            
            /* QToolTip styles */
            QToolTip {{
                background-color: {QColor(colors[ColorRole.BACKGROUND_ALT]).darker(110).name()};
                color: {fg};
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 5px;
            }}
            
            /* QGroupBox styles */
            QGroupBox {{
                border: 1px solid {border};
                border-radius: {Dimensions.BORDER_RADIUS_M}px;
                margin-top: 20px;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }}
            
            /* QFrame styles */
            QFrame[frameShape="4"] {{ /* QFrame::HLine */
                background-color: {border};
                border: none;
                height: 1px;
            }}
            
            QFrame[frameShape="5"] {{ /* QFrame::VLine */
                background-color: {border};
                border: none;
                width: 1px;
            }}
            
            /* Card style container */
            .CardContainer {{
                background-color: {bg_alt};
                border-radius: {Dimensions.BORDER_RADIUS_M}px;
                padding: 16px;
            }}
            
            /* Modern custom scrollable area */
            .ScrollableArea QScrollBar:vertical {{
                width: 8px;
                background-color: transparent;
            }}
            
            .ScrollableArea QScrollBar::handle:vertical {{
                background-color: {border};
                border-radius: 4px;
            }}
            
            /* Task list item */
            .TaskItem {{
                background-color: {bg_alt};
                border-radius: {Dimensions.BORDER_RADIUS_S}px;
                padding: 8px;
                margin: 2px 0;
            }}
            
            .TaskItem:hover {{
                background-color: {bg_hover};
            }}
            
            /* Status indicators */
            .StatusIndicator {{
                border-radius: 4px;
                min-width: 8px;
                min-height: 8px;
            }}
            
            .StatusIndicator[status="success"] {{
                background-color: {success};
            }}
            
            .StatusIndicator[status="error"] {{
                background-color: {error};
            }}
            
            .StatusIndicator[status="warning"] {{
                background-color: {warning};
            }}
            
            .StatusIndicator[status="info"] {{
                background-color: {info};
            }}
        """
    
    def get_button_style(self, is_primary: bool = False, is_danger: bool = False, is_flat: bool = False) -> str:
        """Get style for specific button type"""
        primary_attr = 'primary="true"' if is_primary else ''
        danger_attr = 'danger="true"' if is_danger else ''
        flat_attr = 'flat="true"' if is_flat else ''
        
        return f'{primary_attr} {danger_attr} {flat_attr}'.strip()
        
    def get_label_style(self, is_heading: bool = False, is_subheading: bool = False, 
                       is_error: bool = False, is_success: bool = False) -> str:
        """Get style for specific label type"""
        heading_attr = 'heading="true"' if is_heading else ''
        subheading_attr = 'subheading="true"' if is_subheading else ''
        error_attr = 'error="true"' if is_error else ''
        success_attr = 'success="true"' if is_success else ''
        
        return f'{heading_attr} {subheading_attr} {error_attr} {success_attr}'.strip()
    
    def apply_card_style(self, widget: QWidget):
        """Apply card container style to widget"""
        widget.setObjectName("CardContainer")
        widget.setProperty("class", "CardContainer")
        
    def apply_scrollable_style(self, scroll_area: QScrollArea):
        """Apply modern scrollable area style"""
        scroll_area.setObjectName("ScrollableArea")
        scroll_area.setProperty("class", "ScrollableArea")
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
    def apply_task_item_style(self, widget: QWidget):
        """Apply task item style to widget"""
        widget.setObjectName("TaskItem")
        widget.setProperty("class", "TaskItem")
        
    def create_shadow_effect(self, widget: QWidget, blur_radius: int = 20, 
                           x_offset: int = 0, y_offset: int = 4, 
                           color: Optional[QColor] = None) -> QGraphicsDropShadowEffect:
        """
        Create and apply a drop shadow effect to a widget
        
        Args:
            widget: Widget to apply shadow to
            blur_radius: Shadow blur radius
            x_offset: Horizontal offset
            y_offset: Vertical offset
            color: Shadow color (uses theme shadow color if None)
            
        Returns:
            The created shadow effect
        """
        shadow = QGraphicsDropShadowEffect(widget)
        
        # Use theme shadow color if none provided
        if color is None:
            color = self.palette.get(ColorRole.SHADOW)
            
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(x_offset, y_offset)
        shadow.setColor(color)
        
        widget.setGraphicsEffect(shadow)
        return shadow
        
    def create_modern_button(self, text: str, parent=None, 
                           is_primary: bool = False, 
                           is_danger: bool = False, 
                           is_flat: bool = False) -> QPushButton:
        """
        Create a styled button
        
        Args:
            text: Button text
            parent: Parent widget
            is_primary: Whether this is a primary action button
            is_danger: Whether this is a danger/warning button
            is_flat: Whether this is a flat button
            
        Returns:
            Styled QPushButton
        """
        button = QPushButton(text, parent)
        
        # Apply appropriate style
        style = self.get_button_style(is_primary, is_danger, is_flat)
        if style:
            button.setProperty("class", style)
            
        # Set size policy
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.setMinimumHeight(Dimensions.BUTTON_HEIGHT)
        
        return button
        
    def create_modern_heading(self, text: str, parent=None, 
                            is_subheading: bool = False) -> QLabel:
        """
        Create a styled heading
        
        Args:
            text: Heading text
            parent: Parent widget
            is_subheading: Whether this is a subheading
            
        Returns:
            Styled QLabel
        """
        label = QLabel(text, parent)
        
        # Apply appropriate style
        style = self.get_label_style(is_heading=not is_subheading, 
                                    is_subheading=is_subheading)
        if style:
            label.setProperty("class", style)
            
        # Set font
        size = Typography.FONT_SIZE_L if is_subheading else Typography.FONT_SIZE_XL
        weight = FontWeight.MEDIUM if is_subheading else FontWeight.BOLD
        label.setFont(Typography.get_font(size, weight))
        
        return label
        
    def create_status_indicator(self, status_type: str, parent=None) -> QLabel:
        """
        Create a small colored status indicator
        
        Args:
            status_type: Status type ('success', 'error', 'warning', 'info')
            parent: Parent widget
            
        Returns:
            QLabel configured as status indicator
        """
        indicator = QLabel(parent)
        indicator.setProperty("class", "StatusIndicator")
        indicator.setProperty("status", status_type)
        
        # Set fixed size
        indicator.setFixedSize(10, 10)
        
        return indicator
        
    def create_card_widget(self, parent=None) -> QWidget:
        """
        Create a card-style container widget
        
        Args:
            parent: Parent widget
            
        Returns:
            QWidget with card styling
        """
        widget = QWidget(parent)
        self.apply_card_style(widget)
        
        # Add shadow effect
        self.create_shadow_effect(widget, blur_radius=15, y_offset=3)
        
        return widget
        
    def create_fade_animation(self, widget: QWidget, 
                            start_value: float = 0.0, 
                            end_value: float = 1.0, 
                            duration: int = AnimationPresets.DURATION_NORMAL) -> QPropertyAnimation:
        """
        Create a fade animation for a widget
        
        Args:
            widget: Widget to animate
            start_value: Starting opacity (0.0-1.0)
            end_value: Ending opacity (0.0-1.0)
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation object
        """
        # Create opacity effect if it doesn't exist
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect or not isinstance(opacity_effect, QGraphicsOpacityEffect):
            opacity_effect = QGraphicsOpacityEffect(widget)
            opacity_effect.setOpacity(start_value)
            widget.setGraphicsEffect(opacity_effect)
            
        # Create animation
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(AnimationPresets.EASE_OUT if start_value < end_value else AnimationPresets.EASE_IN)
        
        return animation
    
    def apply_global_style(self, app: QApplication):
        """
        Apply global styling to the entire application
        
        Args:
            app: QApplication instance
        """
        # Set stylesheet
        app.setStyleSheet(self.get_app_stylesheet())
        
        # Set fusion style for consistent look
        app.setStyle(QStyleFactory.create("Fusion"))


# Initialize global style manager
style_manager = StyleManager(is_dark_theme=True)
