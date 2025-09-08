import logging
import os
import re
from pathlib import Path
from typing import Tuple

from .config import DownloaderConfig
from .exceptions import FileSystemError


logger = logging.getLogger(__name__)


class FilesystemManager:
    """
    Handles filesystem operations for the downloader.
    """
    
    def __init__(self, config: DownloaderConfig):
        """Initialize with configuration."""

        self.config = config
    
    def prepare_download_paths(self, video_id: str, title: str = None) -> Tuple[Path, Path]:
        """
        Prepares the filesystem paths for downloading.
        """

        try:
            if self.config.create_video_subdirectory:
                output_dir = Path(self.config.output_directory) / video_id

            else:
                output_dir = Path(self.config.output_directory)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created/verified output directory: {output_dir}")
            
            if title and self.config.clean_filename:
                filename = self._clean_filename(title, video_id)

            else:
                filename = video_id
            
            base_output_path = output_dir / filename
            
            return output_dir, base_output_path
            
        except OSError as e:
            raise FileSystemError(f"Failed to create output directory: {e}")
        
        except Exception as e:
            raise FileSystemError(f"Filesystem preparation failed: {e}")
    

    def _clean_filename(self, title: str, video_id: str) -> str:
        """
        Cleans a video title to make it filesystem-safe.
        """

        if not title:
            return video_id
        
        cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())
        
        if len(cleaned) > self.config.max_filename_length:
            cleaned = cleaned[:self.config.max_filename_length - 15] + f"_{video_id}"
        
        if not cleaned or cleaned.isspace():
            return video_id
        
        return cleaned
    

    def check_existing_files(self, base_path: Path) -> dict:
        """
        Checks for existing files and returns information about them.
        """

        existing = {
            'audio': None,
            'subtitles': [],
            'should_skip': False
        }
        
        audio_path = base_path.with_suffix(f".{self.config.audio_format}")
        if audio_path.exists():
            existing['audio'] = str(audio_path)
            if not self.config.overwrite_existing:
                existing['should_skip'] = True
                logger.info(f"Audio file already exists: {audio_path}")
        
        if self.config.download_subtitles:
            subtitle_files = list(base_path.parent.glob(f"{base_path.name}*.vtt"))
            existing['subtitles'] = [str(f) for f in subtitle_files]
        
        return existing
    
    def verify_download_results(self, base_path: Path) -> dict:
        """
        Verifies that expected files were created after download.
        """

        results = {
            'audio_file': None,
            'subtitle_files': [],
            'success': False
        }
        
        audio_path = base_path.with_suffix(f".{self.config.audio_format}")
        if audio_path.exists():
            results['audio_file'] = str(audio_path)
            logger.debug(f"Verified audio file: {audio_path}")
        else:
            logger.warning(f"Expected audio file not found: {audio_path}")
            return results
        
        if self.config.download_subtitles:
            subtitle_pattern = f"{base_path.name}*.vtt"
            subtitle_files = list(base_path.parent.glob(subtitle_pattern))
            results['subtitle_files'] = [str(f) for f in subtitle_files]
            logger.debug(f"Found {len(subtitle_files)} subtitle files")
        
        results['success'] = True
        return results
    
    
    def cleanup_failed_download(self, base_path: Path):
        """
        Cleans up partial files from a failed download.
        """

        try:
            patterns = [
                f"{base_path}.*",
                f"{base_path}.part*",
                f"{base_path}.temp*"
            ]
            
            for pattern in patterns:
                for file_path in base_path.parent.glob(pattern):
                    try:
                        if file_path.is_file():
                            file_path.unlink()
                            logger.debug(f"Cleaned up partial file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Could not clean up file {file_path}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def remove_empty_directories(self, root_dir: Path):
        """
        Removes empty directories under the specified root directory.
        """

        try:
            for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
                path = Path(dirpath)

                if not any(path.iterdir()):
                    try:
                        path.rmdir()
                        logger.debug(f"Removed empty directory: {path}")
                        
                    except OSError as e:
                        logger.warning(f"Could not remove directory {path}: {e}")
        
        except Exception as e:
            logger.warning(f"Error during empty directory removal: {e}")