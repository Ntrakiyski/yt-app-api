from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class VideoInfoRequest(BaseModel):
    """Request model for video info operations."""
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

class AudioDownloadRequest(BaseModel):
    """Request model for audio download operations."""
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
    audio_file: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class VideoInfoResponse(BaseModel):
    """Response model for video info operations."""
    success: bool
    video_info: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
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
    model: Optional[str] = "small"  # tiny, base, small, medium, large
    
    @validator('url')
    def validate_youtube_url(cls, v):
        """Validate YouTube URL."""
        if not v:
            raise ValueError('URL is required')
        
        youtube_domains = ['youtube.com', 'youtu.be', 'youtube.co.uk', 'm.youtube.com']
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError('URL must be a valid YouTube URL')
        
        return v
    
    @validator('model')
    def validate_whisper_model(cls, v):
        """Validate Whisper model selection."""
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if v not in valid_models:
            raise ValueError(f'model must be one of: {", ".join(valid_models)}')
        return v

class TranscriptionResponse(BaseModel):
    """Response model for transcription operations."""
    success: bool
    transcript: Optional[Dict[str, Any]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    processing_time: Optional[float] = None
    message: Optional[str] = None
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

class ModelsResponse(BaseModel):
    """Response model for available models."""
    success: bool
    models: Optional[List[WhisperModel]] = None
    current_model: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: Optional[str] = None
    timestamp: Optional[float] = None
    services: Optional[Dict[str, Any]] = None 