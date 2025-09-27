from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union, Callable

@dataclass(frozen=True)
class AudioFormat:
    MP3: str = "mp3"
    WAV: str = "wav"
    M4A: str = "m4a"
    FLAC: str = "flac"

@dataclass(frozen=True)
class AudioQuality:
    SUPER_HIGH: int = 320
    VERY_HIGH: int = 256
    HIGH: int = 192
    MEDIUM: int = 128
    LOW: int = 64
    BEST_AVAILABLE: int = 0

@dataclass
class DownloaderConfig:
    """
    Configuration settings for the YouTube audio downloader.
    """
    # --- Core Settings ---
    output_directory: str
    
    audio_format: str = AudioFormat.MP3
    min_audio_quality: int = 0
    audio_quality: int = AudioQuality.BEST_AVAILABLE
    overwrite_existing: bool = False

    # --- Audio Processing Settings ---
    sample_rate: Optional[int] = None
    force_mono: bool = False

    # --- Advanced Processing & Efficiency ---
    download_time_range: Optional[Tuple[str, str]] = None # e.g., ("01:00", "05:30")
    extract_chapters: bool = True
    create_metadata_file: bool = True

    # --- Audio Format and Quality Constants ---
    MP3: str = AudioFormat.MP3
    WAV: str = AudioFormat.WAV
    M4A: str = AudioFormat.M4A
    FLAC: str = AudioFormat.FLAC

    SUPER_HIGH: int = AudioQuality.SUPER_HIGH
    VERY_HIGH: int = AudioQuality.VERY_HIGH
    HIGH: int = AudioQuality.HIGH
    MEDIUM: int = AudioQuality.MEDIUM
    LOW: int = AudioQuality.LOW
    BEST_AVAILABLE: int = AudioQuality.BEST_AVAILABLE

    # --- Subtitle Settings ---
    download_subtitles: bool = False
    download_auto_generated_subtitles: bool = False
    subtitle_languages: Optional[List[str]] = None

    # --- Processing Settings ---
    create_video_subdirectory: bool = True
    clean_filename: bool = True
    max_filename_length: int = 100

    # --- Status Reporting ---
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"

    # --- Error Handling ---
    max_retries: int = 3
    retry_delay_seconds: float = 2.0

    # --- Logging ---
    success_log: Union[Optional[str], Callable] = None
    error_log: Union[Optional[str], Callable] = None

    def __post_init__(self):
        """Validate configuration after initialization."""

        if self.download_subtitles and not self.subtitle_languages:
            raise ValueError("Subtitle languages must be provided when downloading subtitles.")
        
        if not Path(self.output_directory).is_absolute():
            object.__setattr__(self, 'output_directory', str(Path(self.output_directory).resolve()))
