import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_status(msg, color="white"):
    print(f"[JARVIS] {msg}")

def main():
    print_status("Initializing Jarvis AI Assistant...")
    
    # Paths
    base_dir = Path.cwd()
    backend_dir = base_dir / "backend"
    frontend_dir = base_dir / "frontend"
    
    # Environment Check
    if not backend_dir.exists() or not frontend_dir.exists():
        print_status("Error: Directory structure check failed. Please run this from the 'AI-Assistant-for-Computer' folder.")
        input("Press Enter to exit...")
        return

    # Start Backend
    print_status("Launching Backend...")
    backend_env = os.environ.copy()
    
    # Detect venv
    venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
    python_cmd = str(venv_python) if venv_python.exists() else "python"
    
    try:
        backend_process = subprocess.Popen(
            [python_cmd, "main.py"], 
            cwd=str(backend_dir),
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        print_status(f"Failed to start backend: {e}")
        input("Press Enter to exit...")
        return

    # Start Frontend
    print_status("Launching Frontend...")
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"], 
            cwd=str(frontend_dir),
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        print_status(f"Failed to start frontend: {e}")
        input("Press Enter to exit...")
        return

    print_status("Services started. Waiting for initialization...")
    time.sleep(5)
    
    url = "http://localhost:5173"
    print_status(f"Opening Interface at {url}")
    webbrowser.open(url)
    
    print_status("Jarvis is running.")
    print_status("Close the pop-up windows to stop the servers.")
    
    try:
        while True:
            time.sleep(1)
            # Check if processes are alive
            if backend_process.poll() is not None:
                print_status("Backend stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print_status("Frontend stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print_status("Stopping...")
    finally:
        # Cleanup is handled by closing console windows usually, 
        # but we can try to terminate if this script is closed.
        pass

if __name__ == "__main__":
    main()
