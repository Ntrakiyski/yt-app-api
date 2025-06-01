#!/usr/bin/env python3
"""
Launch script for YouTube Transcription AI
Starts both FastAPI backend and Streamlit UI together for production deployment
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

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
    """Run the FastAPI server."""
    print("🚀 Starting FastAPI server on http://0.0.0.0:8000")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "1"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        processes.append(process)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[API] {line.rstrip()}")
        
    except Exception as e:
        print(f"❌ Error starting FastAPI: {e}")

def run_streamlit():
    """Run the Streamlit UI."""
    print("🎨 Starting Streamlit UI on http://0.0.0.0:8501")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
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
                print(f"[UI] {line.rstrip()}")
                
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['fastapi', 'streamlit', 'uvicorn']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("📦 Please install dependencies: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main function to start both servers."""
    print("🎵 YouTube Transcription AI - Production Launch")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if files exist
    if not Path("main.py").exists():
        print("❌ main.py not found!")
        sys.exit(1)
    
    if not Path("streamlit_app.py").exists():
        print("❌ streamlit_app.py not found!")
        sys.exit(1)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🔧 Starting production servers...")
    print("🌐 Frontend: http://0.0.0.0:8501 (Streamlit UI)")
    print("🔌 Backend: http://0.0.0.0:8000 (FastAPI)")
    print("-" * 50)
    
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Wait a bit for FastAPI to start
    time.sleep(3)
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Wait for Streamlit to start
    time.sleep(8)
    
    print("\n" + "=" * 50)
    print("✅ Both servers are running!")
    print("🎨 Primary UI: http://0.0.0.0:8501 (User Interface)")
    print("📖 API Docs: http://0.0.0.0:8000/docs (Developer Interface)")
    print("💾 Health Check: http://0.0.0.0:8000/health")
    print("=" * 50)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for process in processes[:]:  # Create a copy to iterate
                if process.poll() is not None:  # Process has terminated
                    print(f"⚠️ Process {process.pid} terminated unexpectedly")
                    processes.remove(process)
            
            if not processes:  # All processes have died
                print("❌ All servers have stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 