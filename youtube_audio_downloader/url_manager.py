import re
import logging
from urllib.parse import urlparse, parse_qs

from .exceptions import InvalidURLError


logger = logging.getLogger(__name__)


class URLManager:
    """
    Handles URL validation and video ID extraction.
    """
    
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]
    
    @classmethod
    def extract_video_id(cls, url: str) -> str:
        """
        Extracts the YouTube video ID from various URL formats.
        """

        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string")
        
        url = url.strip()
        
        for pattern in cls.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                if cls._is_valid_video_id(video_id):
                    logger.debug(f"Extracted video ID: {video_id} from URL: {url}")
                    return video_id
        
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                    if cls._is_valid_video_id(video_id):
                        logger.debug(f"Extracted video ID from query params: {video_id}")
                        return video_id
                    
        except Exception:
            pass
        
        raise InvalidURLError(f"Could not extract valid video ID from URL: {url}")
    
    @classmethod
    def _is_valid_video_id(cls, video_id: str) -> bool:
        """
        Validates that a video ID matches YouTube's format.
        """
        if not video_id or len(video_id) != 11:
            return False
        
        pattern = r'^[a-zA-Z0-9_-]{11}$'
        return bool(re.match(pattern, video_id))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validates if a URL is a valid YouTube URL.
        """

        try:
            cls.extract_video_id(url)
            return True
        
        except InvalidURLError:
            return False
    
    @classmethod
    def normalize_url(cls, url: str) -> str:
        """
        Normalizes a YouTube URL to the standard format.
        """
        
        video_id = cls.extract_video_id(url)
        return f"https://www.youtube.com/watch?v={video_id}"