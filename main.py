from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import time
from contextlib import asynccontextmanager
import uvicorn
from services.youtube_audio import YouTubeAudioService
from services.whisper_service import WhisperTranscriptionService
from models.youtube import (
    YouTubeURLRequest, 
    AudioDownloadResponse, 
    VideoInfoResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    WhisperModelsResponse,
    VideoInfoRequest,
    AudioDownloadRequest,
    ModelsResponse,
    HealthResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
youtube_service = None
whisper_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global youtube_service, whisper_service
    
    logger.info("Initializing services...")
    youtube_service = YouTubeAudioService()
    whisper_service = WhisperTranscriptionService()
    
    yield
    
    logger.info("Shutting down services...")

# Create FastAPI app with a subpath for API
app = FastAPI(
    title="YouTube Audio Transcription API",
    description="Download YouTube audio and transcribe it using OpenAI Whisper",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def redirect_to_docs():
    """Redirect root to API docs for convenience"""
    return RedirectResponse(url="/api/docs")

@app.get("/api")
async def root():
    """Root endpoint that returns a simple greeting"""
    return {"message": "Hello from YouTube Transcription API"}

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Quick test of services
        models = whisper_service.get_available_models()
        return HealthResponse(
            status="healthy",
            message="All services operational",
            timestamp=time.time(),
            services={
                "youtube_downloader": "operational",
                "whisper_transcriber": "operational",
                "available_models": len(models)
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"Service error: {str(e)}",
            timestamp=time.time(),
            services={}
        )

@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    """Get available Whisper models and current default"""
    try:
        models = whisper_service.get_available_models()
        current_model = whisper_service.current_model
        
        return ModelsResponse(
            success=True,
            models=models,
            current_model=current_model,
            message="Models retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/api/video-info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoInfoRequest):
    """Get YouTube video information"""
    try:
        logger.info(f"Getting video info for: {request.url}")
        
        video_info = youtube_service.get_video_info(request.url)
        
        return VideoInfoResponse(
            success=True,
            video_info=video_info,
            message="Video information retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")

@app.post("/api/download-audio", response_model=AudioDownloadResponse)
async def download_audio(request: AudioDownloadRequest):
    """Download audio from YouTube URL"""
    try:
        logger.info(f"Downloading audio for: {request.url}")
        
        audio_file = youtube_service.download_audio(request.url)
        
        return AudioDownloadResponse(
            success=True,
            audio_file=audio_file,
            message="Audio downloaded successfully"
        )
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download audio: {str(e)}")

@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """Main endpoint: Download YouTube audio and transcribe it"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting transcription for: {request.url}")
        
        # Step 1: Download audio
        logger.info("Downloading audio...")
        audio_file = youtube_service.download_audio(request.url)
        
        # Step 2: Transcribe
        logger.info(f"Transcribing with model: {request.model}")
        transcript = whisper_service.transcribe_audio(audio_file, request.model)
        
        # Step 3: Create segments
        logger.info("Creating segments...")
        segments = []
        segment_duration = 8.0  # 8 seconds per segment
        
        for i, segment in enumerate(transcript["segments"]):
            # Calculate which 8-second segment this belongs to
            segment_start = segment["start"]
            segment_index = int(segment_start // segment_duration)
            segment_timestamp = segment_index * segment_duration
            
            # Create YouTube link with timestamp
            base_url = request.url.split('&')[0]  # Remove any existing parameters
            youtube_link = f"{base_url}&t={int(segment_timestamp)}s"
            
            segments.append({
                "id": segment_index,
                "start_time": segment_timestamp,
                "end_time": min(segment_timestamp + segment_duration, transcript.get("duration", segment_timestamp + segment_duration)),
                "text": segment["text"].strip(),
                "youtube_link": youtube_link
            })
        
        # Clean up audio file
        youtube_service.cleanup_audio_file(audio_file)
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.2f} seconds")
        
        return TranscriptionResponse(
            success=True,
            transcript=transcript,
            segments=segments,
            processing_time=processing_time,
            message="Transcription completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.delete("/cleanup")
async def cleanup_files():
    """Clean up all downloaded audio files."""
    try:
        files_cleaned = youtube_service.cleanup_all_files()
        return {
            "success": True,
            "files_cleaned": files_cleaned,
            "message": f"Cleaned up {files_cleaned} files"
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8555) 