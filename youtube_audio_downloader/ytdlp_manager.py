import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp

from .config import DownloaderConfig
from .exceptions import DownloadFailedError, VideoUnavailableError, NetworkError, LowQualityError


logger = logging.getLogger(__name__)


class YtDlpManager:
    """
    Manages yt-dlp operations with proper error handling and retry logic.
    """
    
    def __init__(self, config: DownloaderConfig):
        """Initialize with configuration."""
        
        self.config = config
    

    def download_video(self, video_url: str, base_output_path: Path) -> Dict[str, Any]:
        """
        Downloads a video using yt-dlp with retry logic.
        """

        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for {video_url}")
                    time.sleep(self.config.retry_delay_seconds * attempt)
                
                return self._execute_download(video_url, base_output_path)
                
            except VideoUnavailableError:
                raise

            except Exception as e:
                last_error = e
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries:
                    continue
                else:
                    break
        
        self._handle_final_error(last_error, video_url)
    

    def _execute_download(self, video_url: str, base_output_path: Path) -> Dict[str, Any]:
        """
        Executes a single download attempt with a pre-download quality check.
        """
        ydl_opts = self._build_ydl_options(base_output_path)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                metadata = self._extract_metadata(info_dict)
                logger.debug(f"Extracted metadata for video: {metadata.get('title', 'Unknown')}")

                if self.config.min_audio_quality > 0:
                    abr = info_dict.get('abr', 0)
                    if abr < self.config.min_audio_quality:
                        raise LowQualityError(f"Audio quality ({abr}k) is below the minimum of {self.config.min_audio_quality}k")

                ydl.download([video_url])
                
                final_audio_path = info_dict.get('requested_downloads')[0]['filepath']

                if not final_audio_path or not Path(final_audio_path).exists():
                    raise DownloadFailedError("Download finished, but the final audio file could not be found.")

                return {
                    'success': True,
                    'metadata': metadata,
                    'audio_file': final_audio_path,
                    'error': None
                }
                
        except LowQualityError:
            raise

        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            
            if any(keyword in error_msg for keyword in ['private', 'unavailable', 'deleted', 'removed']):
                raise VideoUnavailableError(f"Video unavailable: {e}")
            
            elif any(keyword in error_msg for keyword in ['network', 'connection', 'timeout']):
                raise NetworkError(f"Network error: {e}")
            
            else:
                raise DownloadFailedError(f"Download failed: {e}")
        
        except Exception as e:
            raise DownloadFailedError(f"Unexpected error during download: {e}")
        

    def _build_ydl_options(self, base_output_path: Path) -> Dict[str, Any]:
        """
        Builds the options dictionary for yt-dlp.
        """

        output_template = f"{str(base_output_path)}.%(ext)s"
        
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.config.audio_format,
                'preferredquality': str(self.config.audio_quality),
            }],
            'overwrites': self.config.overwrite_existing,
            'quiet': True,
            'noprogress': True,
            'extract_flat': False,
        }
        
        if self.config.download_subtitles:
            opts.update({
                'writesubtitles': True,
                'writeautomaticsub': self.config.download_auto_generated_subtitles,
                'subtitleslangs': self.config.subtitle_languages,
                'subtitlesformat': 'vtt',
            })
        
        return opts
    
    def _extract_metadata(self, info_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts useful metadata from yt-dlp info dictionary.
        """

        return {
            'title': info_dict.get('title'),
            'duration': info_dict.get('duration'),
            'upload_date': info_dict.get('upload_date'),
            'uploader': info_dict.get('uploader'),
            'view_count': info_dict.get('view_count'),
            'like_count': info_dict.get('like_count'),
            'description': info_dict.get('description'),
            'tags': info_dict.get('tags', []),
            'resolution': info_dict.get('resolution'),
            'fps': info_dict.get('fps'),
        }
    

    def _handle_final_error(self, error: Exception, video_url: str):
        """
        Handles the final error after all retries are exhausted.
        """

        if isinstance(error, (VideoUnavailableError, NetworkError, DownloadFailedError)):
            raise error
        
        else:
            raise DownloadFailedError(f"Download failed after {self.config.max_retries} retries: {error}")
    

    def extract_info_only(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts video information without downloading.
        """
        
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return self._extract_metadata(info)
                
        except Exception as e:
            logger.warning(f"Could not extract info for {video_url}: {e}")
            return None