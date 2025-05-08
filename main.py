import os
import sys
import logging
import argparse
import traceback
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt6.QtCore import QTimer, QSettings, QCoreApplication
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QPixmap, QIcon

# Import our modules
from ui import MainWindow, ThemeManager, Theme, APP_NAME, APP_VERSION, ORGANIZATION_NAME
from batch import BatchProcessor
from settings import load_settings, save_settings, DEFAULT_SETTINGS


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration for the application"""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Set root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(console_handler)
    
    # Set up file logging if requested
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            # Add file handler
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)
            
            logging.info(f"Logging to file: {log_file}")
        except Exception as e:
            logging.error(f"Failed to set up file logging: {str(e)}")
            
    # Reduce verbosity of some noisy libraries
    logging.getLogger("PyQt6").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized at level {log_level}")


# Exception handling
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Let the default handler handle KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    # Log the exception
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # If we're in development mode, also print to stderr
    if os.environ.get("YTPRO_DEBUG") == "1":
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default="INFO", help="Set logging level")
    parser.add_argument("--log-file", help="Log to specified file")
    parser.add_argument("--theme", choices=["light", "dark"], help="Set UI theme")
    parser.add_argument("--output-dir", help="Set output directory")
    parser.add_argument("--model", help="Set whisper model")
    parser.add_argument("urls", nargs="*", help="YouTube URLs to process")
    
    return parser.parse_args()


def create_settings_dir_if_missing():
    """Create settings directory if it doesn't exist"""
    settings_dir = os.path.join(os.path.expanduser("~"), ".ytpro")
    if not os.path.exists(settings_dir):
        try:
            os.makedirs(settings_dir, exist_ok=True)
        except Exception as e:
            logging.warning(f"Failed to create settings directory: {str(e)}")
    return settings_dir


def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up environment variables
    if args.debug:
        os.environ["YTPRO_DEBUG"] = "1"
        
    # Set up logging
    log_level = "DEBUG" if args.debug else args.log_level
    if not args.log_file and args.debug:
        # Default debug log location
        args.log_file = os.path.join(os.path.expanduser("~"), ".ytpro", "debug.log")
        
    setup_logging(log_level, args.log_file)
    
    # Set up uncaught exception handler
    sys.excepthook = handle_exception
    
    # Initialize QApplication
    QCoreApplication.setApplicationName(ORGANIZATION_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Create settings directory if missing
    create_settings_dir_if_missing()
    
    # Create settings.py if it doesn't exist (defined in ui.py)
    from ui import create_settings_file_if_missing
    create_settings_file_if_missing()
    
    # Load settings
    settings = load_settings()
    
    # Override settings with command line arguments
    if args.theme:
        settings["theme"] = args.theme
    if args.output_dir:
        settings["output_dir"] = args.output_dir
    if args.model and args.model in ["tiny", "base", "small", "medium", "large"]:
        settings["default_model"] = args.model
        
    # Apply theme
    theme = Theme.from_string(settings.get("theme", "dark"))
    ThemeManager.apply_theme(app, theme)
    
    # Create main window
    main_window = MainWindow()
    
    # Add initial URLs if provided
    for url in args.urls:
        if main_window.batch_processor.validate_url(url):
            main_window._add_url_to_list(url)
    
    # Show the main window
    main_window.show()
    
    # Start processing automatically if URLs were provided and no errors
    if args.urls and len(main_window.task_widgets) > 0:
        # Use QTimer to ensure the UI is fully loaded before starting
        QTimer.singleShot(500, main_window._on_start_processing)
    
    # Run the application
    exit_code = app.exec()
    
    # Cleanup before exit
    logging.info("Application exiting")
    
    # Return exit code to system
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
