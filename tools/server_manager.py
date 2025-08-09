#!/usr/bin/env python3
"""
TOO/SRV/SRVAA - Server manager with custom key handling
"""
import subprocess
import sys
import threading
import os
import signal
from pathlib import Path

def start_server():
    """TOO/SRV/SRVBB - Start uvicorn server"""
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])

def key_listener(server_process):
    """TOO/SRV/SRVCC - Listen for ESC key"""
    try:
        import msvcrt  # Windows only
        while server_process.poll() is None:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC key
                    print("\n🛑 ESC pressed - stopping server...")
                    server_process.terminate()
                    break
                elif key == b'\x03':  # CTRL+C
                    print("\n🛑 CTRL+C pressed - stopping server...")
                    server_process.terminate()
                    break
    except ImportError:
        print("⚠️  Custom key handling only available on Windows")
        server_process.wait()

def main():
    """TOO/SRV/SRVDD - Main server manager"""
    print("🚀 Starting DoneApp Server")
    print("💡 Press ESC or CTRL+C to stop")
    print("=" * 40)
    
    server = start_server()
    
    # TOO/SRV/SRVEE - Start key listener in separate thread
    listener_thread = threading.Thread(target=key_listener, args=(server,))
    listener_thread.daemon = True
    listener_thread.start()
    
    try:
        server.wait()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.terminate()
    
    print("✅ Server stopped cleanly")

if __name__ == "__main__":
    main()
