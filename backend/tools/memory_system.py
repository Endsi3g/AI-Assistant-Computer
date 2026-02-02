import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class MemorySystem:
    def __init__(self, root_dir: str = "memory_store"):
        self.root = Path(root_dir)
        self.folders = {
            "projects": self.root / "projects",
            "areas": self.root / "areas",
            "resources": self.root / "resources",
            "archive": self.root / "archive",
            "inbox": self.root / "inbox",
            "daily": self.root / "daily"
        }
        for p in self.folders.values():
            p.mkdir(parents=True, exist_ok=True)

    def create_note(self, title: str, content: str, category: str = "inbox") -> str:
        """Create a new note in the specified category."""
        if category not in self.folders:
            return f"Error: Invalid category. Choose from: {list(self.folders.keys())}"
        
        filename = f"{title.lower().replace(' ', '_')}.md"
        path = self.folders[category] / filename
        
        # Avoid overwrite unless intentional? For now, simplistic.
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")
            
        return f"Note created: {path}"

    def log_daily(self, content: str) -> str:
        """Append to today's daily log."""
        today = datetime.now().strftime("%Y-%m-%d")
        path = self.folders["daily"] / f"{today}.md"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n\n## {timestamp}\n{content}"
        
        mode = 'a' if path.exists() else 'w'
        with open(path, mode, encoding='utf-8') as f:
            if mode == 'w':
                f.write(f"# Daily Log: {today}\n")
            f.write(entry)
            
        return f"Logged to {today}.md"

    def move_note(self, filename: str, from_cat: str, to_cat: str) -> str:
        """Move a note between PARA categories."""
        if from_cat not in self.folders or to_cat not in self.folders:
            return "Error: Invalid category."
            
        src = self.folders[from_cat] / filename
        dst = self.folders[to_cat] / filename
        
        if not src.exists():
            return f"Error: Note {filename} not found in {from_cat}"
            
        shutil.move(str(src), str(dst))
        return f"Moved {filename} from {from_cat} to {to_cat}"

    def search_notes(self, query: str) -> str:
        """Simple text search across all notes."""
        results = []
        for cat, folder in self.folders.items():
            for fpath in folder.glob("*.md"):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            results.append(f"[{cat.upper()}] {fpath.name}")
                except Exception:
                    continue
        
        if not results:
            return "No matches found."
        return "\n".join(results)

def run_memory_tool(action: str, **kwargs) -> str:
    mem = MemorySystem()
    if action == "create":
        return mem.create_note(kwargs['title'], kwargs['content'], kwargs.get('category', 'inbox'))
    elif action == "log":
        return mem.log_daily(kwargs['content'])
    elif action == "move":
        return mem.move_note(kwargs['filename'], kwargs['from_cat'], kwargs['to_cat'])
    elif action == "search":
        return mem.search_notes(kwargs['query'])
    else:
        return "Unknown action. Use: create, log, move, search"
