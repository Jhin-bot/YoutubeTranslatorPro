# YouTube Transcriber Pro

A powerful desktop application for transcribing, translating, and processing YouTube videos using OpenAI's Whisper speech recognition model. Quickly convert spoken content into accurate text transcripts with support for multiple languages and export formats.

![YouTube Transcriber Pro Screenshot](screenshot.png)

## Features

- **Transcribe YouTube Videos**: Convert speech to text using state-of-the-art Whisper models
- **Batch Processing**: Process multiple YouTube URLs at once with parallel execution
- **Multiple Export Formats**: Export transcripts as SRT, TXT, JSON, and WebVTT
- **Translation Support**: Translate transcripts to multiple languages 
- **Smart Caching**: Avoid reprocessing the same content with efficient caching
- **Modern UI**: User-friendly interface with drag-and-drop URL support and progress tracking
- **Multi-platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.8 or higher
- FFmpeg (for audio conversion)
- Internet connection (for downloading YouTube videos)
- At least 2GB of free RAM
- Sufficient disk space for downloaded audio and cached transcriptions

## Installation

### Prerequisites

1. Install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. Install FFmpeg:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` or equivalent for your distribution

### Method 1: Install from PyPI (Recommended)

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install youtube-transcriber-pro
```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/username/YouTubeTranscriberPro.git
cd YouTubeTranscriberPro

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### GUI Application

Launch the application with:

```bash
# If installed from PyPI
yttrans

# If installed manually
python -m YouTubeTranscriberPro
```

### Command Line Usage

The application can be used from the command line:

```bash
# Basic usage with GUI
yttrans

# Process specific URLs directly
yttrans https://www.youtube.com/watch?v=EXAMPLE_ID1 https://www.youtube.com/watch?v=EXAMPLE_ID2

# Specify output directory and model
yttrans --output-dir ~/transcripts --model medium https://www.youtube.com/watch?v=EXAMPLE_ID
```

### Command Line Options

```
yttrans --help

usage: yttrans [-h] [--debug] [--log-level LOG_LEVEL] [--log-file LOG_FILE] [--theme {light,dark}] [--output-dir OUTPUT_DIR] [--model MODEL] [urls ...]

YouTube Transcriber Pro v1.0.0

positional arguments:
  urls                  YouTube URLs to process

options:
  -h, --help            show this help message and exit
  --debug               Enable debug mode
  --log-level LOG_LEVEL
                        Set logging level
  --log-file LOG_FILE   Log to specified file
  --theme {light,dark}  Set UI theme
  --output-dir OUTPUT_DIR
                        Set output directory
  --model MODEL         Set whisper model
```

## Whisper Models

The application supports the following Whisper models:

| Model | Size | Memory Required | Accuracy | Speed |
|-------|------|----------------|----------|-------|
| tiny  | 75MB | ~1GB RAM       | Lowest   | Fastest |
| base  | 142MB| ~1GB RAM       | Low      | Fast |
| small | 466MB| ~2GB RAM       | Medium   | Medium |
| medium| 1.5GB| ~4GB RAM       | High     | Slow |
| large | 3GB  | ~8GB RAM       | Highest  | Slowest |

The default model is `small`, which offers a good balance between accuracy and speed.

## Configuration

The application's settings can be configured through the GUI or by editing the settings file located at:

- **Windows**: `%USERPROFILE%\.ytpro\settings.json`
- **macOS/Linux**: `~/.ytpro/settings.json`

### Available Settings

| Setting | Description | Default Value |
|---------|-------------|---------------|
| theme | UI theme (light/dark) | dark |
| output_dir | Default output directory | ~/Downloads/YouTubeTranscriber |
| default_model | Default Whisper model | small |
| concurrency | Number of parallel tasks | 2 |
| default_language | Default translation language | None |
| cache_enabled | Enable result caching | true |
| cache_dir | Cache directory | ~/.ytpro_cache |
| cache_size_mb | Maximum cache size (MB) | 1000 |
| cache_ttl | Cache time-to-live (days) | 30 |

## Development Setup

For developers who want to contribute to the project:

1. Clone the repository:
   ```bash
   git clone https://github.com/username/YouTubeTranscriberPro.git
   cd YouTubeTranscriberPro
   ```

2. Create a development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. Run the application in development mode:
   ```bash
   python -m main --debug
   ```

### Project Structure

```
YouTubeTranscriberPro/
├── audio_utils.py       # Audio downloading and conversion
├── batch.py             # Batch processing implementation
├── cache.py             # Caching system
├── main.py              # Application entry point
├── README.md            # This file
├── requirements.txt     # Dependencies
├── settings.py          # Settings management
├── srt_export.py        # SRT export functionality
├── transcribe.py        # Whisper transcription
├── translate.py         # Translation functionality
└── ui.py                # PyQt6 UI implementation
```

## Troubleshooting

### Common Issues

#### FFmpeg Not Found

Error: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

Solution: Make sure FFmpeg is installed and available in your system PATH. You can verify by running `ffmpeg -version` in your terminal.

#### Audio Download Failures

Error: `Failed to download audio: HTTP Error 429: Too Many Requests`

Solution: YouTube may be rate-limiting your requests. Try again later or use a VPN.

#### Out of Memory Errors

Error: `RuntimeError: CUDA out of memory` or similar memory errors

Solution: Try using a smaller Whisper model (e.g., "small" instead of "medium" or "large").

#### UI Not Displaying Correctly

Issue: UI elements misaligned or text unreadable

Solution: Try changing the theme in settings or restart the application.

### Logs Location

Application logs can be found at:

- **Debug mode**: `~/.ytpro/debug.log`
- **Custom log**: Location specified with `--log-file` option

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading capabilities
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the UI framework
- [FFmpeg](https://ffmpeg.org/) for audio processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request
