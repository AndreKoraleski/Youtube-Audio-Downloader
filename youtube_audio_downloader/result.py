from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path

from .config import DownloaderConfig

@dataclass
class DownloadResult:
    """
    A data class to represent the result of a download operation.
    """
    status: str  
    video_id: str
    video_url: str
    audio_file_path: Optional[str] = None
    subtitle_files: Optional[List[str]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    duration: Optional[int] = None
    title: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Returns True if download was successful."""
        return self.status == DownloaderConfig.SUCCESS
    
    @property
    def failed(self) -> bool:
        """Returns True if download failed."""
        return self.status == DownloaderConfig.ERROR
    
    @property
    def audio_file_exists(self) -> bool:
        """Returns True if audio file exists on disk."""
        return self.audio_file_path and Path(self.audio_file_path).exists()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "audio_file_path": self.audio_file_path,
            "subtitle_files": self.subtitle_files,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "duration": self.duration,
            "title": self.title
        }
    
    @classmethod
    def success_result(cls, video_id: str, video_url: str, audio_path: str, 
                      subtitle_files: List[str] = None, metadata: Dict[str, Any] = None) -> 'DownloadResult':
        """Create a successful download result."""
        return cls(
            status=DownloaderConfig.SUCCESS,
            video_id=video_id,
            video_url=video_url,
            audio_file_path=audio_path,
            subtitle_files=subtitle_files or [],
            metadata=metadata or {},
            duration=metadata.get('duration') if metadata else None,
            title=metadata.get('title') if metadata else None
        )
    
    @classmethod
    def error_result(cls, video_id: str, video_url: str, error_message: str) -> 'DownloadResult':
        """Create a failed download result."""
        return cls(
            status=DownloaderConfig.ERROR,
            video_id=video_id,
            video_url=video_url,
            error_message=error_message
        )
    
    @classmethod
    def skipped_result(cls, video_id: str, video_url: str, reason: str) -> 'DownloadResult':
        """Create a skipped download result."""
        return cls(
            status=DownloaderConfig.SKIPPED,
            video_id=video_id,
            video_url=video_url,
            error_message=reason
        )