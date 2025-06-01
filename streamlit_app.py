import streamlit as st
import requests
import json
import time
from typing import Optional, Dict, Any
import pandas as pd
from datetime import timedelta

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Transcription AI",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health() -> bool:
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """Get video information from YouTube URL."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/video-info",
            json={"url": url},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting video info: {str(e)}")
        return None

def get_available_models() -> Optional[Dict[str, Any]]:
    """Get available Whisper models."""
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def transcribe_video(url: str, model: str, segment_duration: int) -> Optional[Dict[str, Any]]:
    """Transcribe video using the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/transcribe",
            json={
                "url": url,
                "whisper_model": model,
                "segment_duration": segment_duration
            },
            timeout=300  # 5 minutes timeout
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None

def format_duration(seconds: int) -> str:
    """Format duration in seconds to readable format."""
    return str(timedelta(seconds=seconds))

def display_video_info(video_info: Dict[str, Any]):
    """Display video information in a nice format."""
    if not video_info.get("success"):
        st.error("Failed to get video information")
        return
    
    info = video_info.get("video_info", {})
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Video Information")
        st.write(f"**Title:** {info.get('title', 'Unknown')}")
        st.write(f"**Channel:** {info.get('uploader', 'Unknown')}")
        if info.get('duration'):
            st.write(f"**Duration:** {format_duration(info['duration'])}")
        if info.get('view_count'):
            st.write(f"**Views:** {info['view_count']:,}")
        if info.get('upload_date'):
            st.write(f"**Upload Date:** {info['upload_date']}")
    
    with col2:
        if info.get('thumbnail'):
            st.image(info['thumbnail'], caption="Video Thumbnail", use_column_width=True)

def display_transcription_results(results: Dict[str, Any]):
    """Display transcription results with segments and full transcript."""
    if not results.get("success"):
        st.error("Transcription failed")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Segments", results.get("total_segments", 0))
    with col2:
        st.metric("Processing Time", f"{results.get('processing_time', 0):.1f}s")
    with col3:
        st.metric("Model Used", results.get("whisper_model_used", "Unknown"))
    with col4:
        video_duration = results.get("video_info", {}).get("duration", 0)
        if video_duration:
            st.metric("Video Duration", format_duration(video_duration))
    
    # Transcript segments
    st.subheader("🎯 Transcript Segments")
    segments = results.get("transcript_segments", [])
    
    if segments:
        # Create a DataFrame for better display
        segment_data = []
        for segment in segments:
            segment_data.append({
                "Segment": f"#{segment['segment_id']}",
                "Time": f"{segment['start_time']:.1f}s - {segment['end_time']:.1f}s",
                "Text": segment['text'],
                "YouTube Link": segment['youtube_link']
            })
        
        df = pd.DataFrame(segment_data)
        
        # Display segments with clickable links
        for idx, segment in enumerate(segments):
            with st.expander(f"Segment #{segment['segment_id']} ({segment['start_time']:.1f}s - {segment['end_time']:.1f}s)"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(segment['text'])
                with col2:
                    st.markdown(f"[🔗 Jump to time]({segment['youtube_link']})")
    
    # Full transcript
    st.subheader("📄 Full Transcript")
    full_transcript = results.get("full_transcript", "")
    if full_transcript:
        st.text_area(
            "Complete transcript:",
            full_transcript,
            height=300,
            help="Full transcript of the video"
        )
        
        # Download option
        st.download_button(
            label="💾 Download Transcript",
            data=full_transcript,
            file_name=f"transcript_{results.get('video_info', {}).get('video_id', 'unknown')}.txt",
            mime="text/plain"
        )

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🎵 YouTube Transcription AI")
    st.markdown("Transform YouTube videos into timestamped transcripts with AI-powered speech recognition")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Health Check
        if check_api_health():
            st.success("✅ API is running")
        else:
            st.error("❌ API not available")
            st.info("Make sure the FastAPI server is running on http://localhost:8000")
            st.stop()
        
        # Get available models
        models_info = get_available_models()
        if models_info and models_info.get("success"):
            # Filter to production models only for UI
            production_models = ["small", "medium", "large"]
            all_models = [model["name"] for model in models_info.get("models", [])]
            models = [model for model in production_models if model in all_models]
            current_model = models_info.get("current_model", "small")
        else:
            # Fallback to production models only
            models = ["small", "medium", "large"]
            current_model = "small"
        
        # Model selection
        selected_model = st.selectbox(
            "🤖 Whisper Model",
            models,
            index=models.index(current_model) if current_model in models else 0,
            help="Larger models are more accurate but slower. Pre-loaded for instant use!"
        )
        
        # Segment duration
        segment_duration = st.slider(
            "⏱️ Segment Duration (seconds)",
            min_value=4,
            max_value=30,
            value=8,
            help="Length of each transcript segment"
        )
        
        # Model information
        if models_info and models_info.get("success"):
            st.subheader("📊 Model Info")
            for model in models_info.get("models", []):
                if model["name"] == selected_model:
                    st.write(f"**Size:** {model['size']}")
                    st.write(f"**Parameters:** {model['parameters']}")
                    st.write(f"**Memory:** {model['memory_required']}")
                    st.write(f"**Speed:** {model['relative_speed']}x")
                    break
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # URL Input
        st.subheader("🔗 YouTube URL")
        youtube_url = st.text_input(
            "Enter YouTube URL:",
            placeholder="https://youtu.be/dQw4w9WgXcQ",
            help="Paste any YouTube video URL here"
        )
        
        # Action buttons
        col_info, col_transcribe = st.columns(2)
        
        with col_info:
            get_info_btn = st.button("📹 Get Video Info", type="secondary", use_container_width=True)
        
        with col_transcribe:
            transcribe_btn = st.button("🎯 Start Transcription", type="primary", use_container_width=True)
    
    with col2:
        # Quick actions and help
        st.subheader("ℹ️ How to Use")
        st.markdown("""
        1. **Enter** a YouTube URL
        2. **Select** a Whisper model (larger = more accurate)
        3. **Adjust** segment duration if needed
        4. **Click** "Start Transcription"
        5. **Wait** for processing (may take 1-2 minutes)
        6. **Review** timestamped segments
        7. **Click** links to jump to specific times
        """)
        
        st.subheader("🚀 Features")
        st.markdown("""
        - ✅ Multiple Whisper model sizes
        - ✅ Clickable timestamp links
        - ✅ Full transcript download
        - ✅ Video metadata extraction
        - ✅ Automatic file cleanup
        """)
    
    # Handle actions
    if youtube_url:
        if get_info_btn:
            with st.spinner("Getting video information..."):
                video_info = get_video_info(youtube_url)
                if video_info:
                    display_video_info(video_info)
                else:
                    st.error("Failed to get video information. Please check the URL.")
        
        if transcribe_btn:
            if not youtube_url.strip():
                st.error("Please enter a YouTube URL")
            else:
                # Show video info first
                with st.spinner("Getting video information..."):
                    video_info = get_video_info(youtube_url)
                    if video_info:
                        display_video_info(video_info)
                        st.divider()
                    
                # Start transcription
                with st.spinner(f"Transcribing with {selected_model} model... This may take 1-2 minutes."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate progress (since we can't get real progress from API)
                    for i in range(100):
                        progress_bar.progress(i + 1)
                        if i < 20:
                            status_text.text("Downloading audio...")
                        elif i < 80:
                            status_text.text("Transcribing with AI...")
                        else:
                            status_text.text("Creating segments...")
                        time.sleep(0.1)
                    
                    results = transcribe_video(youtube_url, selected_model, segment_duration)
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if results:
                        st.success("✅ Transcription completed!")
                        st.divider()
                        display_transcription_results(results)
                    else:
                        st.error("❌ Transcription failed. Please try again.")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**API Status:** 🟢 Online" if check_api_health() else "**API Status:** 🔴 Offline")
    with col2:
        st.markdown("**Powered by:** OpenAI Whisper")
    with col3:
        st.markdown("**Built with:** FastAPI & Streamlit")

if __name__ == "__main__":
    main() 