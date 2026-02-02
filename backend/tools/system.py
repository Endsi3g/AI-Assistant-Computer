import os
import subprocess
import platform
import glob
from typing import List, Dict, Union, Optional

class SystemTools:
    """
    High-privilege system tools for 'True Jarvis' mode.
    WARNING: These tools bypass the sandbox. Secure consent required.
    """
    
    def open_application(self, app_name: str) -> str:
        """
        Open a local application.
        Args:
            app_name: Name of the application or executable path
        """
        system = platform.system()
        try:
            if system == "Windows":
                # Try simple start first
                try:
                    os.startfile(app_name)
                    return f"Launched {app_name}"
                except FileNotFoundError:
                    # Try using 'start' command which handles PATH better
                    subprocess.run(f"start {app_name}", shell=True, check=True)
                    return f"Launched {app_name} via shell"
            elif system == "Darwin": # macOS
                subprocess.run(["open", "-a", app_name], check=True)
                return f"Launched {app_name}"
            else: # Linux
                subprocess.run(["xdg-open", app_name], check=True)
                return f"Launched {app_name}"
        except Exception as e:
            return f"Failed to launch {app_name}: {str(e)}"

    def execute_shell(self, command: str) -> str:
        """
        Execute a shell command.
        Args:
            command: The command to execute (e.g. 'dir', 'ipconfig')
        """
        try:
            # Use PowerShell on Windows for better consistency
            shell_cmd = ["powershell", "-Command", command] if platform.system() == "Windows" else command
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            return output.strip() or "Command executed with no output."
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as e:
            return f"Execution error: {str(e)}"

    def read_file_system(self, path: str) -> str:
        """
        Read a file or list a directory from the real file system.
        Args:
            path: Absolute or relative path
        """
        if not os.path.exists(path):
            return f"Path not found: {path}"
            
        try:
            if os.path.isdir(path):
                items = os.listdir(path)
                return f"Directory {path} contains:\n" + "\n".join(items)
            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(4096) # Read first 4KB
                    if len(content) == 4096:
                        content += "\n... (truncated)"
                    return content
        except Exception as e:
            return f"Access error: {str(e)}"

    def get_definitions(self) -> List[Dict]:
        """Return tool definitions for the AI agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Open a local application or file on the user's computer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of app (e.g. 'notepad', 'chrome') or path"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "Execute a shell command on the host machine. Use with caution.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_system",
                    "description": "Read contents of a file or directory from the host file system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to file or directory"
                            }
                        },
                        "required": ["path"]
                    }
                }
            }
        ]
