from DrissionPage import ChromiumPage, ChromiumOptions
import json
import os
from pathlib import Path
from typing import Optional, Dict

class StealthBrowser:
    """
    A stealth browser wrapper using DrissionPage to bypass detection adjustments.
    """
    def __init__(self, headless: bool = True, session_name: Optional[str] = None):
        self.session_name = session_name
        self.options = ChromiumOptions()
        
        # Core stealth settings
        if headless:
            self.options.headless()
        
        self.options.set_argument('--disable-blink-features=AutomationControlled')
        self.options.set_argument('--no-sandbox')
        self.options.set_argument('--disable-infobars')
        self.options.set_pref('credentials_enable_service', False)
        self.options.set_user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

        # Connect/Launch
        self.page = ChromiumPage(self.options)
        
        # Load session if provided
        if session_name:
            self.load_session(session_name)

    def navigate(self, url: str):
        """Navigate to a URL with stealth wait."""
        self.page.get(url)
        # Random wait logic or intelligent wait could go here
        return self.page.html

    def save_session(self, name: Optional[str] = None):
        """Save cookies and storage to a session file."""
        target_name = name or self.session_name
        if not target_name:
            raise ValueError("No session name provided.")
            
        session_dir = Path.home() / ".jarvis" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Cookies
        cookies = self.page.cookies.as_dict()
        cookie_path = session_dir / f"{target_name}_cookies.json"
        with open(cookie_path, 'w') as f:
            json.dump(cookies, f, indent=2)
            
        return str(cookie_path)

    def load_session(self, name: str):
        """Load session cookies."""
        session_dir = Path.home() / ".jarvis" / "sessions"
        cookie_path = session_dir / f"{name}_cookies.json"
        
        if cookie_path.exists():
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
                # DrissionPage handles cookies slightly differently, simple iteration often works
                for k, v in cookies.items():
                    self.page.set.cookies(name=k, value=v)
            return True
        return False

    def close(self):
        self.page.quit()

def open_stealth_browser(url: str, headless: bool = True, session: Optional[str] = None) -> str:
    """
    Tool function to open a URL in stealth mode.
    Returns the page title or status.
    """
    browser = StealthBrowser(headless=headless, session_name=session)
    try:
        browser.navigate(url)
        title = browser.page.title
        if session:
            browser.save_session()
        return f"Successfully opened {url}. Page Title: {title}"
    finally:
        if headless:
            browser.close()
        else:
            # In headed mode, we might want to keep it open? 
            # For now, let's close it to avoid zombie processes unless specified otherwise.
            # Or assume the user wants to see it and then we detach? 
            # DrissionPage detaches by default if we don't quit.
            pass
