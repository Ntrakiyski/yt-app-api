# YouTube Audio Transcription API

A comprehensive FastAPI application that downloads YouTube audio, transcribes it using OpenAI's Whisper, and provides timestamped segments with clickable YouTube links.

## Features

- 🎵 **YouTube Audio Download**: Download high-quality audio from YouTube videos using yt-dlp
- 🗣️ **AI Transcription**: Transcribe audio using OpenAI's open-source Whisper models
- ⏱️ **Timestamped Segments**: Divide transcripts into 8-second segments with precise timestamps
- 🔗 **Clickable Links**: Generate YouTube links that jump to specific timestamps
- 📝 **Multiple Models**: Support for all Whisper model sizes (tiny, base, small, medium, large)
- 🚀 **GPU Support**: Automatic GPU acceleration when available
- 🧹 **Auto Cleanup**: Automatic cleanup of temporary audio files

## Setup and Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** (required for audio processing)
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` or `sudo yum install ffmpeg`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd yt-final
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Verify FFmpeg installation:
```bash
ffmpeg -version
```

## Running the Application

### Development Server (API only)

```bash
python main.py
```

### Streamlit Web UI (Recommended for Users)

**Easy Launch (Both API + UI):**
```bash
python run_app.py
```
This starts both the FastAPI backend (port 8000) and Streamlit frontend (port 8501).

**Manual Launch:**
```bash
# Terminal 1: Start the API
python main.py

# Terminal 2: Start the UI
streamlit run streamlit_app.py
```

**Access the Applications:**
- 🎨 **Streamlit UI**: http://localhost:8501 (User-friendly interface)
- 🌐 **API Documentation**: http://localhost:8000/docs (Developer interface)

### Production Server (API only)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Uvicorn directly (with hot reload)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Deployment

### Quick Start with Docker

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Or build and run manually:
```bash
# Build the image
docker build -t youtube-transcriber .

# Run the container
docker run -p 8000:8000 youtube-transcriber
```

### Production Deployment (Coolify)

The application is ready for deployment on **Coolify** or any Docker-based platform:

1. **Dockerfile**: Production-ready with all dependencies
2. **Health checks**: Built-in health monitoring at `/health`
3. **Port**: Runs on port 8000
4. **Auto-cleanup**: Manages temporary files automatically

For Coolify deployment:
- Repository: Push to GitHub/GitLab
- Build: Dockerfile auto-detected
- Port: 8000
- Health check: `/health` endpoint available

### Docker Features

- ✅ **Multi-stage build optimized**
- ✅ **FFmpeg and system dependencies included**
- ✅ **Pre-loaded Whisper models** (small, medium, large)
- ✅ **Health checks configured**
- ✅ **Automatic cleanup of temporary files**
- ✅ **Production-ready with Uvicorn**
- ✅ **Zero startup delay** - models ready instantly

## API Endpoints

Once running, your API will be available at http://localhost:8000

### Core Endpoints

- `GET /api` - Basic health check returning "Hello"
- `GET /health` - Detailed health check with service status
- `GET /version` - API version and feature information
- `GET /models` - List available Whisper models

### YouTube & Transcription

- `POST /video-info` - Extract YouTube video metadata
- `POST /download-audio` - Download audio from YouTube video  
- `POST /transcribe` - **Main endpoint**: Complete transcription pipeline
- `DELETE /cleanup` - Clean up temporary audio files

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### Basic Transcription

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://youtu.be/dQw4w9WgXcQ",
       "whisper_model": "small",
       "segment_duration": 8
     }'
```

### Get Video Information

```bash
curl -X POST "http://localhost:8000/video-info" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://youtu.be/dQw4w9WgXcQ"}'
```

### Check Available Models

```bash
curl "http://localhost:8000/models"
```

## Response Format

### Transcription Response

```json
{
  "success": true,
  "video_info": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Example Video",
    "duration": 240,
    "uploader": "Example Channel"
  },
  "transcript_segments": [
    {
      "segment_id": 1,
      "start_time": 0,
      "end_time": 8,
      "text": "Welcome to this video...",
      "youtube_link": "https://youtube.com/watch?v=dQw4w9WgXcQ&t=0s"
    }
  ],
  "full_transcript": "Complete transcript text...",
  "processing_time": 45.2,
  "whisper_model_used": "small",
  "total_segments": 15
}
```

## Whisper Models

### Available Models

| Model  | Size   | Parameters | Memory | Speed | Use Case | UI Available |
|--------|--------|------------|--------|-------|----------|--------------|
| tiny   | 39 MB  | 39 M       | ~1 GB  | 32x   | Fast, basic accuracy | API only |
| base   | 74 MB  | 74 M       | ~1 GB  | 16x   | Balanced speed/quality | API only |
| small  | 244 MB | 244 M      | ~2 GB  | 6x    | Better accuracy | ✅ Pre-loaded |
| medium | 769 MB | 769 M      | ~5 GB  | 2x    | High accuracy | ✅ Pre-loaded |
| large  | 1550 MB| 1550 M     | ~10 GB | 1x    | Best accuracy | ✅ Pre-loaded |

### Model Selection Strategy

- **Streamlit UI**: Shows only production-quality models (small, medium, large)
- **API**: Supports all models for developer flexibility
- **Docker**: Pre-loads small, medium, and large models for zero startup delay
- **Default**: Small model provides the best balance of speed and accuracy

## Development

### Project Structure

```
├── main.py                 # FastAPI application
├── streamlit_app.py        # Streamlit web UI
├── run_app.py              # Launch script for both API + UI
├── services/
│   ├── youtube_audio.py    # YouTube download service
│   └── whisper_service.py  # Whisper transcription service
├── models/
│   └── youtube.py          # Pydantic models
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── .dockerignore          # Docker ignore file
├── test_youtube_service.py # Test script
└── README.md              # This file
```

### Testing

Run the test script to verify your setup:

```bash
python test_youtube_service.py
```

### Environment Variables

No environment variables are required for basic operation. The application uses:
- Pre-loaded models in Docker (instant startup)
- Automatic model downloading for development (first use only)
- Temporary file management
- GPU detection and utilization when available

## Performance Notes

- **Docker Deployment**: Models are pre-loaded, zero startup delay
- **Development**: Models download on first use (1-2 minutes initial delay)
- **GPU Acceleration**: Automatically detected and used when available
- **Memory Usage**: Varies by model size (see table above)
- **Processing Time**: Depends on video length and model size
- **File Cleanup**: Temporary audio files are automatically cleaned up

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in your system PATH
2. **CUDA out of memory**: Use a smaller Whisper model or CPU processing
3. **YouTube download fails**: Check internet connection and YouTube URL validity
4. **Model download slow**: Only affects development setup (Docker has pre-loaded models)

### Logs

The application logs important events. Check console output for:
- Model loading progress
- Download status
- Transcription progress
- Error details

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]