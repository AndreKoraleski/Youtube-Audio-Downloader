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
        
        logger.info("Downloader initialized with config: %s", self.config)
    

    def download(self, video_url: str) -> DownloadResult:
        """
        Downloads a single YouTube video's audio and optionally subtitles.
        """
        video_id = None
        
        try:
            logger.info("Starting download for URL: %s", video_url)
            video_id = self.url_manager.extract_video_id(video_url)
            normalized_url = self.url_manager.normalize_url(video_url)
            
            metadata = self.ytdlp_manager.extract_info_only(normalized_url)
            title = metadata.get('title') if metadata else None
            
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
            download_result = self.ytdlp_manager.download_video(normalized_url, base_output_path)
            
            verification = self.filesystem_manager.verify_download_results(base_output_path)
            if not verification['success']:
                raise DownloadFailedError("Download verification failed - expected files not found")
            
            logger.info("Download completed successfully for video ID: %s", video_id)
            return DownloadResult.success_result(
                video_id=video_id,
                video_url=normalized_url,
                audio_path=verification['audio_file'],
                subtitle_files=verification['subtitle_files'],
                metadata=download_result.get('metadata', {})
            )
            
        except InvalidURLError as e:
            logger.error("Invalid URL provided: %s", e)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )
            
        except VideoUnavailableError as e:
            logger.error("Video unavailable: %s", e)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )

        except LowQualityError as e:
            logger.warning("Video skipped due to low quality: %s", e)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )
            
        except FileSystemError as e:
            logger.error("Filesystem error: %s", e)
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )
            
        except (NetworkError, DownloadFailedError) as e:
            logger.error("Download failed: %s", e)

            if video_id:
                try:
                    output_dir, base_output_path = self.filesystem_manager.prepare_download_paths(video_id)
                    self.filesystem_manager.cleanup_failed_download(base_output_path)
                    
                except Exception:
                    pass
            
            return DownloadResult.error_result(
                video_id or "unknown", video_url, str(e)
            )
            
        except Exception as e:
            logger.exception("Unexpected error during download")
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