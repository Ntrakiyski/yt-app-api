import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import whisper
import torch

logger = logging.getLogger(__name__)

class WhisperTranscriptionService:
    """Service for audio transcription using OpenAI Whisper."""
    
    def __init__(self):
        """Initialize the Whisper transcription service."""
        self.model = None
        self.current_model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model information
        self.model_info = {
            "tiny": {
                "size": "39 MB",
                "parameters": "39 M",
                "memory_required": "~1 GB",
                "relative_speed": 32.0,
                "multilingual": True,
            },
            "base": {
                "size": "74 MB", 
                "parameters": "74 M",
                "memory_required": "~1 GB",
                "relative_speed": 16.0,
                "multilingual": True,
            },
            "small": {
                "size": "244 MB",
                "parameters": "244 M", 
                "memory_required": "~2 GB",
                "relative_speed": 6.0,
                "multilingual": True,
            },
            "medium": {
                "size": "769 MB",
                "parameters": "769 M",
                "memory_required": "~5 GB",
                "relative_speed": 2.0,
                "multilingual": True,
            },
            "large": {
                "size": "1550 MB",
                "parameters": "1550 M",
                "memory_required": "~10 GB",
                "relative_speed": 1.0,
                "multilingual": True,
            }
        }
        
        logger.info(f"Whisper service initialized on device: {self.device}")
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available Whisper models.
        
        Returns:
            Dict containing model information and availability
        """
        models = []
        
        for model_name, info in self.model_info.items():
            try:
                # Check if model is available (try to load model info)
                available = True  # Whisper models are downloaded on first use
                models.append({
                    "name": model_name,
                    "size": info["size"],
                    "parameters": info["parameters"],
                    "memory_required": info["memory_required"],
                    "relative_speed": info["relative_speed"],
                    "available": available,
                    "multilingual": info["multilingual"]
                })
            except Exception as e:
                logger.warning(f"Model {model_name} availability check failed: {e}")
                models.append({
                    "name": model_name,
                    "size": info["size"],
                    "parameters": info["parameters"],
                    "memory_required": info["memory_required"],
                    "relative_speed": info["relative_speed"],
                    "available": False,
                    "multilingual": info["multilingual"]
                })
        
        return {
            "success": True,
            "models": models,
            "current_model": self.current_model_name,
            "device": self.device
        }
    
    def load_model(self, model_name: str = "base") -> Dict[str, Any]:
        """Load a Whisper model.
        
        Args:
            model_name: Name of the model to load (tiny, base, small, medium, large)
            
        Returns:
            Dict containing load result
        """
        if model_name not in self.model_info:
            return {
                "success": False,
                "error": f"Invalid model name. Available models: {list(self.model_info.keys())}"
            }
        
        try:
            logger.info(f"Loading Whisper model: {model_name}")
            start_time = time.time()
            
            # Load the model (will download if not cached)
            self.model = whisper.load_model(model_name, device=self.device)
            self.current_model_name = model_name
            
            load_time = time.time() - start_time
            logger.info(f"Model {model_name} loaded in {load_time:.2f} seconds")
            
            return {
                "success": True,
                "model_name": model_name,
                "device": self.device,
                "load_time": load_time,
                "model_info": self.model_info[model_name]
            }
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load model {model_name}: {str(e)}"
            }
    
    def transcribe_audio(self, audio_file_path: str, model_name: str = "base", 
                        language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using Whisper.
        
        Args:
            audio_file_path: Path to the audio file
            model_name: Whisper model to use
            language: Optional language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Dict containing transcription result with timestamps
        """
        if not os.path.exists(audio_file_path):
            return {"success": False, "error": "Audio file not found"}
        
        # Load model if not loaded or different model requested
        if self.model is None or self.current_model_name != model_name:
            load_result = self.load_model(model_name)
            if not load_result["success"]:
                return load_result
        
        try:
            logger.info(f"Transcribing audio: {audio_file_path}")
            start_time = time.time()
            
            # Transcribe with word-level timestamps
            options = {
                "word_timestamps": True,
                "verbose": False,
            }
            
            if language:
                options["language"] = language
            
            result = self.model.transcribe(audio_file_path, **options)
            
            processing_time = time.time() - start_time
            logger.info(f"Transcription completed in {processing_time:.2f} seconds")
            
            # Extract segments with word-level timestamps
            segments = []
            for segment in result["segments"]:
                segment_data = {
                    "id": segment["id"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Add word-level timestamps if available
                if "words" in segment:
                    for word in segment["words"]:
                        segment_data["words"].append({
                            "word": word["word"],
                            "start": word["start"],
                            "end": word["end"],
                            "probability": word.get("probability", 0.0)
                        })
                
                segments.append(segment_data)
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": segments,
                "processing_time": processing_time,
                "model_used": model_name,
                "device": self.device
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
    
    def create_segments(self, transcription_result: Dict[str, Any], 
                       segment_duration: int = 8) -> List[Dict[str, Any]]:
        """Create fixed-duration segments from transcription result.
        
        Args:
            transcription_result: Result from transcribe_audio
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of segments with fixed duration
        """
        if not transcription_result.get("success") or not transcription_result.get("segments"):
            return []
        
        segments = transcription_result["segments"]
        fixed_segments = []
        current_segment_id = 1
        
        # Get the total duration from the last segment
        if not segments:
            return []
        
        total_duration = segments[-1]["end"]
        current_time = 0
        
        while current_time < total_duration:
            segment_end = min(current_time + segment_duration, total_duration)
            
            # Collect words/text within this time range
            segment_text = ""
            segment_words = []
            
            for segment in segments:
                for word in segment.get("words", []):
                    word_start = word["start"]
                    word_end = word["end"]
                    
                    # Check if word overlaps with current segment
                    if (word_start < segment_end and word_end > current_time):
                        segment_text += word["word"]
                        segment_words.append(word)
            
            # Clean up text
            segment_text = segment_text.strip()
            
            # Only add segment if it has content
            if segment_text:
                fixed_segments.append({
                    "segment_id": current_segment_id,
                    "start_time": current_time,
                    "end_time": segment_end,
                    "text": segment_text,
                    "words": segment_words
                })
                current_segment_id += 1
            
            current_time = segment_end
        
        return fixed_segments
    
    def create_youtube_links(self, segments: List[Dict[str, Any]], 
                           base_youtube_url: str) -> List[Dict[str, Any]]:
        """Add YouTube timestamp links to segments.
        
        Args:
            segments: List of segments from create_segments
            base_youtube_url: Original YouTube URL
            
        Returns:
            List of segments with YouTube timestamp links
        """
        # Extract base URL without timestamp parameters
        if "?" in base_youtube_url:
            base_url = base_youtube_url.split("?")[0]
            if "watch" in base_url:
                video_id = base_youtube_url.split("v=")[1].split("&")[0]
                base_url = f"https://youtube.com/watch?v={video_id}"
        else:
            base_url = base_youtube_url
        
        for segment in segments:
            start_seconds = int(segment["start_time"])
            # Create YouTube timestamp URL
            timestamp_url = f"{base_url}&t={start_seconds}s"
            segment["youtube_link"] = timestamp_url
        
        return segments 