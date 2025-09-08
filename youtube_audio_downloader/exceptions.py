class DownloaderException(Exception):
    """Base exception for all downloader-related errors."""
    pass


class InvalidURLError(DownloaderException):
    """Raised when the provided YouTube URL is invalid."""
    pass


class DownloadFailedError(DownloaderException):
    """Raised when the yt-dlp download process fails."""
    pass


class FileSystemError(DownloaderException):
    """Raised when there are filesystem-related issues."""
    pass


class ConfigurationError(DownloaderException):
    """Raised when there are configuration-related issues."""
    pass


class VideoUnavailableError(DownloaderException):
    """Raised when the video is unavailable (private, deleted, etc.)."""
    pass


class NetworkError(DownloaderException):
    """Raised when there are network-related issues."""
    pass


class LowQualityError(DownloaderException):
    """Raised when the video's audio quality is below the configured minimum."""
    pass