import logging
from typing import Union

from .config import DownloaderConfig
from .result import DownloadResult
from .url_manager import URLManager
from .filesystem_manager import FilesystemManager
from .ytdlp_manager import YtDlpManager
from .exceptions import (
    InvalidURLError, 
    DownloadFailedError, 
    FileSystemError, 
    VideoUnavailableError, 
    NetworkError,
    LowQualityError
)


logger = logging.getLogger(__name__)


class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


class Downloader:
    """
    Main downloader class that coordinates all components.
    Similar architecture to the Coordinator class.
    """
    
    def __init__(self, config: DownloaderConfig):
        """
        Initialize the downloader with all necessary managers.
        """
        self.config = config
        self.url_manager = URLManager()
        self.filesystem_manager = FilesystemManager(config)
        self.ytdlp_manager = YtDlpManager(config)
        
        self._setup_logging()
        
        logger.info("Downloader initialized with config: %s", self.config)
    
    def _setup_logging(self):
        """
        Configures file logging based on the provided config.
        """
        lib_logger = logging.getLogger('youtube_audio_downloader')
        lib_logger.setLevel(logging.DEBUG)

        if isinstance(self.config.error_log, str):
            error_handler = logging.FileHandler(self.config.error_log)
            error_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            error_handler.setFormatter(formatter)
            lib_logger.addHandler(error_handler)
            logger.debug(f"Attached error log handler to: {self.config.error_log}")

        if isinstance(self.config.success_log, str):
            success_handler = logging.FileHandler(self.config.success_log)
            success_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            success_handler.setFormatter(formatter)
            success_handler.addFilter(InfoFilter())
            lib_logger.addHandler(success_handler)
            logger.debug(f"Attached success log handler to: {self.config.success_log}")


    def download(self, video_url: str) -> DownloadResult:
        """
        Downloads a single YouTube video's audio and optionally subtitles.
        """
        video_id = None
        output_dir = None
        base_output_path = None
        
        try:
            logger.info("Starting download for URL: %s", video_url)
            video_id = self.url_manager.extract_video_id(video_url)
            normalized_url = self.url_manager.normalize_url(video_url)
            
            metadata = self.ytdlp_manager.extract_info_only(normalized_url)
            if not metadata:
                raise VideoUnavailableError("Could not retrieve video metadata.")

            title = metadata.get('title')
            
            output_dir, base_output_path = self.filesystem_manager.prepare_download_paths(
                video_id, title
            )
            
            existing_files = self.filesystem_manager.check_existing_files(base_output_path)
            if existing_files['should_skip']:
                logger.info("Skipping download - files already exist: %s", existing_files['audio'])
                return DownloadResult.skipped_result(
                    video_id, normalized_url, 
                    "Files already exist and overwrite is disabled"
                )
            
            logger.info("Downloading video ID: %s", video_id)
            download_result = self.ytdlp_manager.download_video(video_url, base_output_path)
            
            verification = self.filesystem_manager.verify_download_results(base_output_path)
            if not verification['success']:
                raise DownloadFailedError("Download verification failed - expected files not found")
            
            final_metadata = download_result.get('metadata', metadata)
            self.filesystem_manager.save_metadata_file(base_output_path, final_metadata)
            
            logger.info("Download completed successfully for video ID: %s", video_id)
            return DownloadResult.success_result(
                video_id=video_id,
                video_url=normalized_url,
                audio_path=verification['audio_file'],
                subtitle_files=verification['subtitle_files'],
                metadata=final_metadata
            )
            
        except (
            InvalidURLError, VideoUnavailableError, LowQualityError, 
            FileSystemError, NetworkError, DownloadFailedError
        ) as e:
            logger.error("Download failed due to a known error: %s", e)
            if base_output_path:
                self.filesystem_manager.cleanup_failed_download(base_output_path)
            if output_dir:
                self.filesystem_manager.remove_video_subdirectory(output_dir)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )
            
        except Exception as e:
            logger.exception("An unexpected error occurred during download")
            if base_output_path:
                self.filesystem_manager.cleanup_failed_download(base_output_path)
            if output_dir:
                self.filesystem_manager.remove_video_subdirectory(output_dir)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, f"Unexpected error: {str(e)}"
            )
        

    def validate_url(self, video_url: str) -> bool:
        """
        Validates if a URL is a valid YouTube URL.
        """
        return self.url_manager.validate_url(video_url)
    

    def get_video_info(self, video_url: str) -> Union[dict, None]:
        """
        Gets video information without downloading.
        """

        try:
            normalized_url = self.url_manager.normalize_url(video_url)
            return self.ytdlp_manager.extract_info_only(normalized_url)
        
        except Exception as e:
            logger.error("Could not get video info: %s", e)
            return None
