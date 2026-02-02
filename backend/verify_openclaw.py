import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Path: {sys.path}")

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing OpenClaw Tool Imports...")
    
    from tools.stealth_browser import StealthBrowser
    print("✅ StealthBrowser imported")
    
    from tools.youtube import YouTubeTool
    print("✅ YouTubeTool imported")
    
    from tools.email_sender import EmailSender
    print("✅ EmailSender imported")
    
    from tools.memory_system import MemorySystem
    print("✅ MemorySystem imported")
    
    print("\nRunning Functional Tests...")
    
    # Test Memory System (Safe)
    mem = MemorySystem(root_dir="test_memory")
    mem.create_note("Test Note", "This is a test", "inbox")
    print("✅ MemorySystem created note")
    
    # Test YouTube Metadata (Network)
    yt = YouTubeTool()
    # Use a safe, standard video (e.g., "Me at the zoo")
    meta = yt.get_metadata("https://www.youtube.com/watch?v=jNQXAC9IVRw")
    if meta['title']:
        print(f"✅ YouTube Metadata fetched: {meta['title']}")
    
    print("\nAll systems operational.")

except Exception as e:
    print(f"\n❌ Verification Failed: {str(e)}")
    import traceback
    traceback.print_exc()
