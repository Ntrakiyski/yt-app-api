#!/usr/bin/env python3
"""
Launch script for YouTube Transcription AI
Starts both FastAPI backend and Streamlit UI together for easy development
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
    """Handle Ctrl+C to gracefully shutdown both processes."""
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
    print("🚀 Starting FastAPI server on http://localhost:8000")
    try:
        process = subprocess.Popen([
            sys.executable, "main.py"
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
    print("🎨 Starting Streamlit UI on http://localhost:8501")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "true",
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
    print("🎵 YouTube Transcription AI - Launch Script")
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
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🔧 Starting servers...")
    print("📝 Press Ctrl+C to stop both servers")
    print("-" * 50)
    
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Wait a bit for FastAPI to start
    time.sleep(3)
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Wait a bit more for Streamlit to start
    time.sleep(5)
    
    print("\n" + "=" * 50)
    print("✅ Both servers are running!")
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("🎨 Streamlit UI: http://localhost:8501")
    print("📝 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            for process in processes[:]:  # Create a copy to iterate
                if process.poll() is not None:  # Process has terminated
                    processes.remove(process)
            
            if not processes:  # All processes have died
                print("❌ All servers have stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 