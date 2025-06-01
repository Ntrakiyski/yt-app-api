#!/usr/bin/env python3
"""
Launch script for YouTube Transcription AI
Creates a reverse proxy to serve both Streamlit UI and FastAPI on port 8501
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn
import httpx

# Global process list to track subprocesses
processes = []

def signal_handler(sig, frame):
    """Handle signals to gracefully shutdown both processes."""
    print("\n🛑 Shutting down servers...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    print("✅ All servers stopped.")
    sys.exit(0)

def run_fastapi():
    """Run the FastAPI server on port 8555."""
    print("🚀 Starting FastAPI server on http://0.0.0.0:8555")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8555",
            "--workers", "1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        processes.append(process)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[FastAPI] {line.strip()}")
        
        process.wait()
    except Exception as e:
        print(f"❌ FastAPI server error: {e}")

def run_streamlit():
    """Run the Streamlit server on port 8502."""
    print("🎨 Starting Streamlit server on http://0.0.0.0:8502")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8502",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        processes.append(process)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[Streamlit] {line.strip()}")
        
        process.wait()
    except Exception as e:
        print(f"❌ Streamlit server error: {e}")

# Create reverse proxy app
proxy_app = FastAPI(title="YouTube Transcription Proxy")

@proxy_app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api(request: Request, path: str):
    """Proxy API requests to FastAPI server."""
    url = f"http://localhost:8555/api/{path}"
    
    async with httpx.AsyncClient() as client:
        # Forward the request
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params
        )
        
        # Return the response
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )

@proxy_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_streamlit(request: Request, path: str = ""):
    """Proxy all other requests to Streamlit server."""
    url = f"http://localhost:8502/{path}"
    
    async with httpx.AsyncClient() as client:
        # Forward the request
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params
        )
        
        # Return the response
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )

def run_proxy():
    """Run the reverse proxy server on port 8501."""
    print("🔄 Starting reverse proxy on http://0.0.0.0:8501")
    uvicorn.run(proxy_app, host="0.0.0.0", port=8501, log_level="info")

def main():
    """Main function to start all services."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎵 Starting YouTube Transcription AI")
    print("=" * 50)
    
    # Start FastAPI in a thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Start Streamlit in a thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Wait a moment for services to start
    time.sleep(5)
    
    print("\n🌐 Services starting...")
    print("📱 Frontend: http://localhost:8501")
    print("🔧 API: http://localhost:8501/api/docs")
    print("💡 Press Ctrl+C to stop all services")
    print("=" * 50)
    
    # Run the proxy (this blocks)
    try:
        run_proxy()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 