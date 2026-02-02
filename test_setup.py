#!/usr/bin/env python3
"""
JARVIS AI Assistant - Setup Test Script
Tests all components and validates the installation
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}\n")

def print_check(name, status, details=""):
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    print(f"  {icon} {name}")
    if details:
        print(f"      {Colors.CYAN}{details}{Colors.RESET}")

def print_warning(text):
    print(f"  {Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"  {Colors.CYAN}ℹ {text}{Colors.RESET}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    ok = version.major >= 3 and version.minor >= 10
    print_check(
        f"Python version: {version.major}.{version.minor}.{version.micro}",
        ok,
        "Requires Python 3.10+" if not ok else ""
    )
    return ok

def check_node_version():
    """Check Node.js version"""
    import subprocess
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        major = int(version.lstrip('v').split('.')[0])
        ok = major >= 18
        print_check(f"Node.js version: {version}", ok, "Requires Node.js 18+" if not ok else "")
        return ok
    except Exception:
        print_check("Node.js", False, "Not installed")
        return False

def check_npm():
    """Check npm is available"""
    import subprocess
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print_check(f"npm version: {version}", True)
        return True
    except Exception:
        print_check("npm", False, "Not installed")
        return False

def check_docker():
    """Check Docker availability (optional)"""
    import subprocess
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print_check(f"Docker: {version}", True, "(Optional)")
        return True
    except Exception:
        print_warning("Docker not found (optional - for sandbox)")
        return False

def check_ollama():
    """Check Ollama availability (optional)"""
    import subprocess
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        version = result.stdout.strip() or "installed"
        print_check(f"Ollama: {version}", True, "(Optional)")
        return True
    except Exception:
        print_warning("Ollama not found (optional - for local AI)")
        return False

async def check_ollama_server():
    """Check if Ollama server is running"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                print_check("Ollama server", True, f"Models: {', '.join(models[:3])}")
                return True
    except Exception:
        pass
    print_warning("Ollama server not running (run 'ollama serve')")
    return False

def check_env_file():
    """Check environment configuration"""
    env_path = Path("backend/.env") if Path("backend/.env").exists() else Path(".env")
    
    if not env_path.exists():
        print_check(".env file", False, "Missing configuration file")
        return False
    
    with open(env_path) as f:
        content = f.read()
    
    has_groq = "GROQ_API_KEY" in content and "your_" not in content.lower()
    has_openai = "OPENAI_API_KEY" in content and content.split("OPENAI_API_KEY")[1].split("\n")[0].strip("= ") != ""
    
    if has_groq or has_openai:
        provider = "Groq" if has_groq else "OpenAI"
        print_check(f".env configured", True, f"{provider} API key found")
        return True
    else:
        print_check(".env file exists", True, "But API keys need configuration")
        return True

def check_backend_deps():
    """Check backend dependencies"""
    try:
        import fastapi
        import groq
        import edge_tts
        print_check("Backend dependencies", True, "FastAPI, Groq, Edge-TTS")
        return True
    except ImportError as e:
        print_check("Backend dependencies", False, f"Missing: {e.name}")
        return False

def check_frontend_deps():
    """Check frontend dependencies"""
    node_modules = Path("frontend/node_modules")
    if node_modules.exists():
        print_check("Frontend dependencies", True, "node_modules found")
        return True
    else:
        print_check("Frontend dependencies", False, "Run 'npm install' in frontend/")
        return False

async def test_ai_connection():
    """Test AI provider connection"""
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    
    try:
        from backend.config import settings
        
        if settings.groq_api_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=settings.groq_api_key)
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
                max_tokens=10
            )
            print_check("Groq API connection", True, f"Model: {response.model}")
            return True
    except Exception as e:
        print_check("Groq API connection", False, str(e)[:50])
    
    return False

def test_tools():
    """Test computer control tools"""
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    
    try:
        from backend.tools.computer_control import get_system_info
        info = get_system_info()
        if "time" in info.lower():
            print_check("Computer control tools", True, "get_system_info works")
            return True
    except Exception as e:
        print_check("Computer control tools", False, str(e)[:50])
    
    return False

async def run_all_tests():
    """Run all tests"""
    print_header("JARVIS Setup Test")
    print_info("Testing all components...\n")
    
    results = []
    
    # Prerequisites
    print(f"\n{Colors.BOLD}Prerequisites:{Colors.RESET}")
    results.append(check_python_version())
    results.append(check_node_version())
    results.append(check_npm())
    
    # Optional
    print(f"\n{Colors.BOLD}Optional Components:{Colors.RESET}")
    check_docker()
    check_ollama()
    await check_ollama_server()
    
    # Configuration
    print(f"\n{Colors.BOLD}Configuration:{Colors.RESET}")
    results.append(check_env_file())
    
    # Dependencies
    print(f"\n{Colors.BOLD}Dependencies:{Colors.RESET}")
    results.append(check_backend_deps())
    results.append(check_frontend_deps())
    
    # Connectivity
    print(f"\n{Colors.BOLD}Connectivity:{Colors.RESET}")
    ai_ok = await test_ai_connection()
    results.append(ai_ok)
    
    # Tools
    print(f"\n{Colors.BOLD}Tools:{Colors.RESET}")
    results.append(test_tools())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print_header("Test Summary")
    
    if passed == total:
        print(f"  {Colors.GREEN}{Colors.BOLD}All tests passed! ({passed}/{total}){Colors.RESET}")
        print(f"\n  {Colors.CYAN}To start Jarvis:{Colors.RESET}")
        print(f"    Windows: run start-jarvis.bat")
        print(f"    Mac/Linux: ./start-jarvis.sh")
        print(f"\n  {Colors.CYAN}Or manually:{Colors.RESET}")
        print(f"    Terminal 1: cd backend && python main.py")
        print(f"    Terminal 2: cd frontend && npm run dev")
        print(f"\n  {Colors.CYAN}Then open:{Colors.RESET} http://localhost:5173")
    else:
        print(f"  {Colors.YELLOW}{passed}/{total} tests passed{Colors.RESET}")
        print(f"\n  Please fix the issues above before running Jarvis.")
    
    return passed == total

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
