# Use Python 3.11 slim image for better performance
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for FFmpeg and audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for temporary audio files
RUN mkdir -p /tmp/youtube_audio

# Pre-download Whisper models for production use (small, medium, large)
# This adds ~1.1GB to the image but eliminates first-use delays
RUN python -c "import whisper; print('Downloading small model...'); whisper.load_model('small'); print('Downloading medium model...'); whisper.load_model('medium'); print('Downloading large model...'); whisper.load_model('large'); print('All models downloaded successfully!')"

# Expose ports for both services
EXPOSE 8000 8501

# Health check for Streamlit frontend
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run both FastAPI backend and Streamlit frontend
CMD ["python", "run_app.py"] 