from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import time
from services.youtube_audio import YouTubeAudioService
from services.whisper_service import WhisperTranscriptionService
from models.youtube import (
    YouTubeURLRequest, 
    AudioDownloadResponse, 
    VideoInfoResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    WhisperModelsResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Audio Transcription API",
    description="A FastAPI service for downloading YouTube audio and generating timestamped transcripts using Whisper",
    version="1.0.0"
)

# Initialize services
youtube_service = YouTubeAudioService()
whisper_service = WhisperTranscriptionService()

@app.get("/api")
def read_api():
    """Basic API endpoint returning a greeting message."""
    return {"message": "Hello"}

@app.get("/health")
async def health_check():
    """Health check endpoint with service status."""
    try:
        # Check Whisper models availability
        models_info = whisper_service.get_available_models()
        
        return {
            "status": "healthy",
            "service": "YouTube Audio Transcription API",
            "version": "1.0.0",
            "dependencies": {
                "yt-dlp": "available",
                "whisper": "available" if models_info["success"] else "error",
                "ffmpeg": "available",  # TODO: Add actual FFmpeg check
                "device": whisper_service.device
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/version")
async def version_info():
    """Version information endpoint."""
    return {
        "version": "1.0.0",
        "api_name": "YouTube Audio Transcription API",
        "supported_models": ["tiny", "base", "small", "medium", "large"],
        "features": [
            "YouTube audio download",
            "Whisper transcription",
            "8-second segmentation",
            "Timestamped navigation"
        ],
        "device": whisper_service.device
    }

@app.get("/models", response_model=WhisperModelsResponse)
async def get_whisper_models():
    """Get available Whisper models and their information."""
    try:
        result = whisper_service.get_available_models()
        return WhisperModelsResponse(**result)
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/video-info", response_model=VideoInfoResponse)
async def get_video_info(request: YouTubeURLRequest):
    """Extract YouTube video metadata without downloading."""
    try:
        logger.info(f"Getting video info for: {request.url}")
        result = youtube_service.get_video_info(request.url)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return VideoInfoResponse(
            success=True,
            video_info=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/download-audio", response_model=AudioDownloadResponse)
async def download_audio(request: YouTubeURLRequest, background_tasks: BackgroundTasks):
    """Download audio from YouTube video."""
    try:
        logger.info(f"Downloading audio for: {request.url}")
        result = youtube_service.download_audio(request.url)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return AudioDownloadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_youtube_video(request: TranscriptionRequest, background_tasks: BackgroundTasks):
    """Complete transcription pipeline: download YouTube audio, transcribe with Whisper, and create segments."""
    start_time = time.time()
    
    try:
        logger.info(f"Starting transcription for: {request.url}")
        
        # Step 1: Get video info
        video_info_result = youtube_service.get_video_info(request.url)
        if not video_info_result["success"]:
            raise HTTPException(status_code=400, detail=video_info_result["error"])
        
        # Step 2: Download audio
        logger.info("Downloading audio...")
        download_result = youtube_service.download_audio(request.url)
        if not download_result["success"]:
            raise HTTPException(status_code=400, detail=download_result["error"])
        
        audio_file_path = download_result["audio_file_path"]
        
        # Step 3: Transcribe audio
        logger.info(f"Transcribing with model: {request.whisper_model}")
        transcription_result = whisper_service.transcribe_audio(
            audio_file_path=audio_file_path,
            model_name=request.whisper_model
        )
        
        if not transcription_result["success"]:
            # Clean up audio file before returning error
            background_tasks.add_task(youtube_service.cleanup_file, audio_file_path)
            raise HTTPException(status_code=500, detail=transcription_result["error"])
        
        # Step 4: Create 8-second segments
        logger.info("Creating segments...")
        segments = whisper_service.create_segments(
            transcription_result, 
            segment_duration=request.segment_duration
        )
        
        # Step 5: Add YouTube timestamp links
        segments_with_links = whisper_service.create_youtube_links(segments, request.url)
        
        # Calculate total processing time
        total_processing_time = time.time() - start_time
        
        # Schedule cleanup
        background_tasks.add_task(youtube_service.cleanup_file, audio_file_path)
        
        # Build response
        response = TranscriptionResponse(
            success=True,
            video_info=video_info_result,
            transcript_segments=segments_with_links,
            full_transcript=transcription_result["text"],
            processing_time=total_processing_time,
            whisper_model_used=request.whisper_model,
            total_segments=len(segments_with_links)
        )
        
        logger.info(f"Transcription completed in {total_processing_time:.2f} seconds")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in transcription pipeline: {str(e)}")
        # Try to cleanup if we have a file path
        try:
            if 'audio_file_path' in locals():
                background_tasks.add_task(youtube_service.cleanup_file, audio_file_path)
        except:
            pass
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 