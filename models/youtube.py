from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class YouTubeURLRequest(BaseModel):
    """Request model for YouTube URL operations."""
    url: str
    
    @validator('url')
    def validate_youtube_url(cls, v):
        """Basic validation for YouTube URL format."""
        if not v:
            raise ValueError('URL is required')
        
        # Basic check for YouTube domains
        youtube_domains = ['youtube.com', 'youtu.be', 'youtube.co.uk', 'm.youtube.com']
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError('URL must be a valid YouTube URL')
        
        return v

class VideoInfo(BaseModel):
    """Model for YouTube video metadata."""
    video_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    thumbnail: Optional[str] = None
    webpage_url: Optional[str] = None

class AudioDownloadResponse(BaseModel):
    """Response model for audio download operations."""
    success: bool
    video_id: Optional[str] = None
    audio_file_path: Optional[str] = None
    file_size: Optional[int] = None
    video_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class VideoInfoResponse(BaseModel):
    """Response model for video info operations."""
    success: bool
    video_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TranscriptSegment(BaseModel):
    """Model for transcript segments with timestamps."""
    segment_id: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str
    confidence: Optional[float] = None
    youtube_link: str  # YouTube URL with timestamp

class TranscriptionRequest(BaseModel):
    """Request model for transcription operations."""
    url: str
    whisper_model: Optional[str] = "base"  # tiny, base, small, medium, large
    segment_duration: Optional[int] = 8  # seconds
    
    @validator('url')
    def validate_youtube_url(cls, v):
        """Validate YouTube URL."""
        if not v:
            raise ValueError('URL is required')
        
        youtube_domains = ['youtube.com', 'youtu.be', 'youtube.co.uk', 'm.youtube.com']
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError('URL must be a valid YouTube URL')
        
        return v
    
    @validator('whisper_model')
    def validate_whisper_model(cls, v):
        """Validate Whisper model selection."""
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if v not in valid_models:
            raise ValueError(f'whisper_model must be one of: {", ".join(valid_models)}')
        return v
    
    @validator('segment_duration')
    def validate_segment_duration(cls, v):
        """Validate segment duration."""
        if v < 1 or v > 60:
            raise ValueError('segment_duration must be between 1 and 60 seconds')
        return v

class TranscriptionResponse(BaseModel):
    """Response model for transcription operations."""
    success: bool
    video_info: Optional[Dict[str, Any]] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    full_transcript: Optional[str] = None
    processing_time: Optional[float] = None
    whisper_model_used: Optional[str] = None
    total_segments: Optional[int] = None
    error: Optional[str] = None

class WhisperModel(BaseModel):
    """Model for Whisper model information."""
    name: str
    size: str  # e.g., "39 MB", "244 MB"
    parameters: str  # e.g., "39 M", "244 M"
    memory_required: str  # e.g., "~1 GB", "~2 GB"
    relative_speed: float  # relative to base model
    available: bool
    multilingual: bool

class WhisperModelsResponse(BaseModel):
    """Response model for available Whisper models."""
    success: bool
    models: Optional[List[WhisperModel]] = None
    current_model: Optional[str] = None
    device: Optional[str] = None
    error: Optional[str] = None 