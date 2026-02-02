"""
Computer Control Tools
Tools for controlling the computer: apps, browser, files, commands
"""
import os
import subprocess
import webbrowser
import platform
import asyncio
from datetime import datetime
from typing import Optional
import aiofiles


# Application name to executable mapping for Windows
WINDOWS_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "vscode": "code",
    "visual studio code": "code",
    "teams": "teams",
    "zoom": "zoom",
    "vlc": "vlc",
    "obs": "obs64",
    "steam": "steam",
}


class ComputerControl:
    """Tools for controlling the computer"""
    
    def __init__(self):
        self.system = platform.system()
        
    async def open_application(self, app_name: str) -> bool:
        """Open an application by name"""
        try:
            app_lower = app_name.lower()
            
            if self.system == "Windows":
                # Try to find in mapping first
                executable = WINDOWS_APPS.get(app_lower, app_name)
                
                # Try to open using start command
                process = await asyncio.create_subprocess_shell(
                    f'start "" "{executable}"',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
                
            elif self.system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_shell(
                    f'open -a "{app_name}"',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
                
            else:  # Linux
                process = await asyncio.create_subprocess_shell(
                    f'{app_name.lower()} &',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                return True
                
        except Exception as e:
            print(f"Error opening application: {e}")
            return False
    
    async def open_url(self, url: str) -> bool:
        """Open a URL in the default browser"""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Error opening URL: {e}")
            return False
    
    async def web_search(self, query: str) -> bool:
        """Perform a web search"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return True
        except Exception as e:
            print(f"Error performing search: {e}")
            return False
    
    async def run_command(self, command: str) -> str:
        """Execute a shell command and return output"""
        try:
            # Security: Block dangerous commands
            dangerous = ['rm -rf', 'del /f /s', 'format', 'mkfs', ':(){', 'fork bomb']
            if any(d in command.lower() for d in dangerous):
                return "Error: Command blocked for security reasons"
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                output += "\nErrors: " + stderr.decode('utf-8', errors='replace')
            
            return output[:2000]  # Limit output length
            
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    async def read_file(self, file_path: str) -> str:
        """Read contents of a file"""
        try:
            # Security: Expand path and check it's not system critical
            file_path = os.path.expanduser(file_path)
            
            # Block access to system directories
            blocked_paths = ['C:\\Windows', 'C:\\Program Files', '/etc', '/bin', '/usr']
            if any(file_path.startswith(p) for p in blocked_paths):
                return "Error: Access to system directories is restricted"
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Limit content length
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncated)"
            
            return content
            
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file"""
        try:
            file_path = os.path.expanduser(file_path)
            
            # Block access to system directories
            blocked_paths = ['C:\\Windows', 'C:\\Program Files', '/etc', '/bin', '/usr']
            if any(file_path.startswith(p) for p in blocked_paths):
                return False
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    
    async def get_system_info(self, info_type: str) -> str:
        """Get system information"""
        try:
            if info_type == "time":
                return datetime.now().strftime("The current time is %H:%M:%S")
                
            elif info_type == "date":
                return datetime.now().strftime("Today is %A, %B %d, %Y")
                
            elif info_type == "battery":
                try:
                    import psutil
                    battery = psutil.sensors_battery()
                    if battery:
                        status = "charging" if battery.power_plugged else "on battery"
                        return f"Battery is at {battery.percent}%, {status}"
                    return "No battery detected"
                except ImportError:
                    return "Battery information unavailable (psutil not installed)"
                    
            elif info_type == "memory":
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    return f"Memory usage: {mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)"
                except ImportError:
                    return "Memory information unavailable"
                    
            elif info_type == "cpu":
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=1)
                    return f"CPU usage: {cpu}%"
                except ImportError:
                    return "CPU information unavailable"
                    
            elif info_type == "all":
                results = []
                for t in ["time", "date", "battery", "memory", "cpu"]:
                    results.append(await self.get_system_info(t))
                return "\n".join(results)
                
            return f"Unknown info type: {info_type}"
            
        except Exception as e:
            return f"Error getting system info: {str(e)}"
