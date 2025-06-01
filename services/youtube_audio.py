import os
import re
import tempfile
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import yt_dlp
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class YouTubeAudioService:
    """Service for downloading and processing YouTube audio."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the YouTube audio service.
        
        Args:
            temp_dir: Optional custom temporary directory for downloads
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.download_dir = Path(self.temp_dir) / "youtube_audio"
        self.download_dir.mkdir(exist_ok=True)
        
        # yt-dlp configuration for high-quality audio extraction
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp4]/bestaudio[ext=webm]/bestaudio/best[height<=720]/best',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'cookiefile': None,
            'no_check_certificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'extractaudio': True,
            'audioformat': 'best',  # Let yt-dlp choose the best audio format
            'prefer_ffmpeg': True,
        }
    
    def validate_youtube_url(self, url: str) -> Dict[str, Any]:
        """Validate and extract information from YouTube URL.
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            Dict containing validation result and video ID if valid
        """
        if not url or not isinstance(url, str):
            return {"valid": False, "error": "URL is required and must be a string"}
        
        # Patterns for different YouTube URL formats
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
        ]
        
        video_id = None
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            return {"valid": False, "error": "Invalid YouTube URL format"}
        
        return {
            "valid": True,
            "video_id": video_id,
            "url": url
        }
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract video metadata without downloading.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict containing video metadata
        """
        validation = self.validate_youtube_url(url)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    "success": True,
                    "video_id": info.get('id'),
                    "title": info.get('title'),
                    "description": info.get('description'),
                    "duration": info.get('duration'),  # in seconds
                    "uploader": info.get('uploader'),
                    "upload_date": info.get('upload_date'),
                    "view_count": info.get('view_count'),
                    "thumbnail": info.get('thumbnail'),
                    "webpage_url": info.get('webpage_url'),
                }
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            return {"success": False, "error": f"Failed to extract video info: {str(e)}"}
    
    def download_audio(self, url: str) -> Dict[str, Any]:
        """Download audio from YouTube video.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict containing download result and file path
        """
        validation = self.validate_youtube_url(url)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        try:
            logger.info(f"Starting audio download for: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info first to get the video ID and metadata
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id')
                
                if not video_id:
                    return {"success": False, "error": "Could not extract video ID"}
                
                logger.info(f"Video ID: {video_id}, Title: {info.get('title', 'Unknown')}")
                
                # Check if video has audio formats available
                formats = info.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                
                if not audio_formats:
                    return {"success": False, "error": "No audio formats available for this video"}
                
                # Download the audio
                ydl.download([url])
                
                # Find the downloaded file - check for common audio extensions
                possible_files = []
                for ext in ['.m4a', '.webm', '.mp4', '.mp3', '.wav', '.ogg', '.opus']:
                    file_path = self.download_dir / f"{video_id}{ext}"
                    if file_path.exists():
                        possible_files.append(file_path)
                
                # Also check for files with different naming patterns
                if not possible_files:
                    for file_path in self.download_dir.iterdir():
                        if file_path.is_file() and video_id in file_path.name:
                            possible_files.append(file_path)
                
                if not possible_files:
                    # List all files in download directory for debugging
                    all_files = list(self.download_dir.iterdir())
                    logger.error(f"No audio file found. Files in directory: {[f.name for f in all_files]}")
                    
                    # Clean up any non-audio files
                    for file_path in all_files:
                        if file_path.suffix in ['.mhtml', '.html', '.part']:
                            file_path.unlink()
                    
                    return {"success": False, "error": "Downloaded audio file not found. Video may be unavailable, age-restricted, or region-blocked."}
                
                # Use the first found file (should be the most recent)
                audio_file = possible_files[0]
                logger.info(f"Found audio file: {audio_file}")
                
                # Verify the file is actually an audio file (not .mhtml or similar)
                if audio_file.suffix in ['.mhtml', '.html']:
                    audio_file.unlink()  # Clean up
                    return {"success": False, "error": "Video download failed. Video may be unavailable, age-restricted, or region-blocked."}
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "audio_file_path": str(audio_file),
                    "file_size": audio_file.stat().st_size,
                    "video_info": {
                        "title": info.get('title'),
                        "duration": info.get('duration'),
                        "uploader": info.get('uploader'),
                    }
                }
                
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return {"success": False, "error": f"Failed to download audio: {str(e)}"}
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up a downloaded audio file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
            return False
    
    def cleanup_all_files(self) -> int:
        """Clean up all files in the download directory.
        
        Returns:
            Number of files cleaned up
        """
        try:
            files_cleaned = 0
            for file_path in self.download_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    files_cleaned += 1
            logger.info(f"Cleaned up {files_cleaned} files")
            return files_cleaned
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0 