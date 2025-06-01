#!/usr/bin/env python3
"""
Simple test script for YouTube audio service.
Run this to verify the service works before moving to the next task.
"""

import sys
import asyncio
from services.youtube_audio import YouTubeAudioService

def test_url_validation():
    """Test YouTube URL validation."""
    print("Testing YouTube URL validation...")
    service = YouTubeAudioService()
    
    # Test valid URLs
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "youtu.be/dQw4w9WgXcQ"
    ]
    
    # Test invalid URLs
    invalid_urls = [
        "https://example.com/video",
        "not a url",
        "",
        None
    ]
    
    print("Valid URLs:")
    for url in valid_urls:
        result = service.validate_youtube_url(url)
        print(f"  {url} -> {result}")
    
    print("\nInvalid URLs:")
    for url in invalid_urls:
        result = service.validate_youtube_url(url)
        print(f"  {url} -> {result}")

def test_video_info():
    """Test video info extraction (requires internet)."""
    print("\nTesting video info extraction...")
    service = YouTubeAudioService()
    
    # Use a short, well-known video (Rick Roll has ID dQw4w9WgXcQ)
    test_url = "https://youtu.be/dQw4w9WgXcQ"
    
    try:
        result = service.get_video_info(test_url)
        if result["success"]:
            print(f"  ✅ Video info extracted successfully!")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Duration: {result.get('duration', 'N/A')} seconds")
            print(f"  Uploader: {result.get('uploader', 'N/A')}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

def main():
    """Run all tests."""
    print("🚀 Testing YouTube Audio Service")
    print("=" * 50)
    
    test_url_validation()
    test_video_info()
    
    print("\n" + "=" * 50)
    print("✅ Testing complete!")
    print("\nNote: To test audio download, you'll need to install FFmpeg")
    print("and run the FastAPI server with: python main.py")

if __name__ == "__main__":
    main() 