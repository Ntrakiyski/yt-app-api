import streamlit as st
import requests
import json
import time
from typing import Optional, Dict, Any
import pandas as pd
from datetime import timedelta
import os

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Transcription AI",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
def get_api_base_url():
    """Get the API base URL based on environment"""
    # In production, use the same domain as Streamlit
    if os.getenv('ENVIRONMENT') == 'production':
        return "https://yt-app.worfklow.org/api"
    else:
        # Development environment - check if we're running through proxy
        try:
            # Try the proxy first (when using run_app.py)
            response = requests.get("http://localhost:8501/api/health", timeout=2)
            if response.status_code == 200:
                return "http://localhost:8501/api"
        except:
            pass
        # Fallback to direct FastAPI connection
        return "http://localhost:8555/api"

API_BASE_URL = get_api_base_url()

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
    except Exception as e:
        st.error(f"Error getting video info: {e}")
    return None

def get_available_models() -> Optional[Dict[str, Any]]:
    """Get available Whisper models from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error getting models: {e}")
    return None

def transcribe_video(url: str, model: str) -> Optional[Dict[str, Any]]:
    """Transcribe a YouTube video using the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/transcribe",
            json={"url": url, "model": model},
            timeout=300  # 5 minutes timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error during transcription: {e}")
    return None

def format_duration(seconds: int) -> str:
    """Format duration from seconds to HH:MM:SS"""
    return str(timedelta(seconds=seconds))

def display_video_info(video_info: Dict[str, Any]):
    """Display video information in a nice format."""
    if video_info and video_info.get("success"):
        info = video_info.get("video_info", {})
        
        st.subheader("📹 Video Information")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if info.get("thumbnail"):
                st.image(info["thumbnail"], width=200)
        
        with col2:
            st.write(f"**Title:** {info.get('title', 'N/A')}")
            st.write(f"**Duration:** {format_duration(info.get('duration', 0))}")
            st.write(f"**Views:** {info.get('view_count', 'N/A'):,}" if info.get('view_count') else "**Views:** N/A")
            st.write(f"**Channel:** {info.get('uploader', 'N/A')}")
            
        if info.get("description"):
            with st.expander("📄 Description"):
                st.write(info["description"][:500] + "..." if len(info.get("description", "")) > 500 else info.get("description", ""))

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
            st.info("Make sure the FastAPI server is running on http://localhost:8555")
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
                    
                    results = transcribe_video(youtube_url, selected_model)
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if results and results.get("success"):
                        st.success(f"✅ Transcription completed in {results.get('processing_time', 0):.1f} seconds!")
                        
                        # Display transcript segments
                        if "segments" in results:
                            st.subheader("📝 Transcript Segments")
                            
                            segments_df = []
                            for segment in results["segments"]:
                                segments_df.append({
                                    "Segment": segment["id"] + 1,
                                    "Time": f"{segment['start_time']:.1f}s - {segment['end_time']:.1f}s",
                                    "Text": segment["text"],
                                    "YouTube Link": segment["youtube_link"]
                                })
                            
                            df = pd.DataFrame(segments_df)
                            
                            # Display as interactive table
                            for idx, row in df.iterrows():
                                with st.container():
                                    col1, col2, col3 = st.columns([1, 2, 6])
                                    
                                    with col1:
                                        st.write(f"**#{row['Segment']}**")
                                    
                                    with col2:
                                        st.write(f"`{row['Time']}`")
                                        if st.button(f"▶️ Play", key=f"play_{idx}", help="Open YouTube at this timestamp"):
                                            st.write(f"🔗 [Open YouTube at {row['Time']}]({row['YouTube Link']})")
                                    
                                    with col3:
                                        st.write(row['Text'])
                                    
                                    st.divider()
                            
                            # Full transcript download
                            st.subheader("📄 Full Transcript")
                            full_text = "\n\n".join([f"[{seg['start_time']:.1f}s] {seg['text']}" for seg in results["segments"]])
                            st.text_area("Complete Transcript", full_text, height=200)
                            
                            # Download button
                            video_title = video_info.get('video_info', {}).get('title', 'video') if 'video_info' in locals() else 'video'
                            safe_title = video_title.replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]  # Limit length and remove invalid chars
                            st.download_button(
                                label="💾 Download Transcript",
                                data=full_text,
                                file_name=f"transcript_{safe_title}.txt",
                                mime="text/plain"
                            )
                        
                        else:
                            st.error("No transcript segments found in the response.")
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