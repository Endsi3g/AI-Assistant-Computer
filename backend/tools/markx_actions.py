
"""
Mark-X Actions
Tools ported from Mark-X repository for desktop automation and information retrieval.
Now includes Real Jarvis features: Aircraft Tracking, Smart Weather, and Universal Messaging.
"""
import time
import asyncio
import webbrowser
import logging
import urllib.parse
import httpx
from typing import Optional, List, Dict

# Conditional import for pyautogui to avoid issues in headless environments
try:
    import pyautogui
except ImportError:
    pyautogui = None

# Conditional import for serpapi
try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None

logger = logging.getLogger(__name__)

async def send_message(receiver: str, message_text: str, platform: str = "WhatsApp") -> str:
    """
    Send a message via Windows desktop application (WhatsApp, Telegram, Discord, Slack).
    Uses pyautogui to control the mouse and keyboard.
    
    Args:
        receiver: Name of the contact/channel to message
        message_text: Content of the message
        platform: Platform to use (WhatsApp, Telegram, Discord, Slack)
        
    Returns:
        Status message
    """
    if not pyautogui:
        return "Error: pyautogui is not installed."

    platform_lower = platform.lower()
    
    # Determine search shortcut
    # WhatsApp/Telegram usually use Ctrl+F or just typing. Discord/Slack use Ctrl+K.
    search_shortcut = ["ctrl", "k"] if platform_lower in ["discord", "slack"] else ["ctrl", "f"]
    if platform_lower == "whatsapp":
        search_shortcut = ["ctrl", "f"] # Explicitly ensure WhatsApp uses Ctrl+F

    try:
        # Run in a separate thread because pyautogui is blocking
        def _automate_message():
            pyautogui.PAUSE = 0.1

            # Open Start Menu
            pyautogui.press("win")
            time.sleep(0.3)
            
            # Type platform name
            pyautogui.write(platform, interval=0.03)
            pyautogui.press("enter")
            time.sleep(2.0) # Wait for app to open

            # Search for contact/channel
            pyautogui.hotkey(*search_shortcut)
            time.sleep(0.5)
            
            # Type receiver name
            pyautogui.write(receiver, interval=0.03)
            time.sleep(1.0) # Wait for search results
            pyautogui.press("enter") # Select contact
            time.sleep(0.5)

            # Type message
            pyautogui.write(message_text, interval=0.01)
            pyautogui.press("enter") # Send
            
        await asyncio.to_thread(_automate_message)
        return f"Message sent to {receiver} via {platform}."

    except Exception as e:
        logger.error(f"Error executing send_message: {e}")
        return f"Failed to send message: {e}"

async def weather_report(city: str, time_query: str = "today") -> str:
    """
    Get a smart weather report using wttr.in API (text based) and open browser as backup.
    
    Args:
        city: City name
        time_query: 'today', 'tomorrow' (used for browser only, wttr.in gives current/3day)
        
    Returns:
        Spoken summary of the weather.
    """
    try:
        # Fetch text report from wttr.in (format j1 for JSON, or format 3 for one-line)
        # Using format 3: "City: Condition Temp"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://wttr.in/{city}?format=3")
            if resp.status_code == 200:
                weather_summary = resp.text.strip()
            else:
                weather_summary = f"I couldn't fetch the data directly."

        # Also open in browser for visual
        query = f"weather in {city} {time_query}"
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(url)
        
        return f"Weather report for {city}: {weather_summary}. I've also opened the forecast in your browser."
    except Exception as e:
        return f"Failed to get weather report: {e}"

async def aircraft_report(radius_km: int = 50) -> str:
    """
    Track aircraft flying nearby using OpenSky Network API.
    Uses generic coordinates (roughly New York) if system location unavailable, 
    or you can hardcode your lat/lon here.
    
    Args:
        radius_km: Radius to search in km (default 50)
        
    Returns:
        List of aircraft calls signs or count.
    """
    # OpenSky API Public URL
    # Bounding box calculation would be needed for precise area. 
    # For simplicity in this demo, we'll fetch 'all' states and filter, 
    # OR better: use a fixed bounding box for the user's approximate region (e.g. US East Coast)
    # Since we don't have user lat/lon tools here, we'll hit the API and just return a sample count 
    # or the first few planes if we define a box. 
    
    # Let's try to get a broad report or specific top flights.
    # Note: OpenSky 'all' endpoint is heavy.
    
    try:
        async with httpx.AsyncClient() as client:
            # Using a sample bounding box for New York area for demo purposes
            # lamin=40.5, lomin=-74.5, lamax=41.0, lomax=-73.5
            params = {
                "lamin": 40.0,
                "lomin": -75.0,
                "lamax": 42.0,
                "lomax": -72.0
            }
            resp = await client.get("https://opensky-network.org/api/states/all", params=params, timeout=10.0)
            
            if resp.status_code == 200:
                data = resp.json()
                states = data.get("states", [])
                if not states:
                    return "No aircraft detected in the standard patrol area (NY Region) right now."
                
                count = len(states)
                
                # Get first 3 callsigns
                callsigns = [s[1].strip() for s in states[:3] if s[1].strip()]
                planes_str = ", ".join(callsigns)
                
                return f"Radar checks confirm {count} aircraft in the sector. Identifying: {planes_str} and others."
            else:
                return "Radar systems (OpenSky API) are currently unreachable."
                
    except Exception as e:
        logger.error(f"Aircraft report failed: {e}")
        return "Sir, I'm unable to access the flight radar data at the moment."

async def markx_web_search(query: str, api_key: str = None) -> str:
    """
    Perform a search using SerpApi and return a summarized answer (Mark-X style).
    If SerpApi is not configured/installed, falls back to opening a browser.
    
    Args:
        query: Search query
        api_key: SerpApi Key (optional)
        
    Returns:
        Summarized answer string
    """
    if GoogleSearch and api_key:
        try:
            return await asyncio.to_thread(_serpapi_search, query, api_key)
        except Exception as e:
            logger.error(f"SerpApi failed: {e}")
            return f"Search failed: {e}"
    else:
        # Fallback to standard browser open
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(url)
        if not GoogleSearch:
            return "Opened search results in browser (SerpApi not installed)."
        else:
            return "Opened search results in browser (API Key missing)."

def _serpapi_search(query: str, api_key: str) -> str:
    """Blocking SerpApi call"""
    params = {
        "q": query,
        "engine": "google",
        "hl": "en",
        "gl": "us",
        "num": 3,
        "api_key": api_key
    }
    
    search = GoogleSearch(params)
    data = search.get_dict()
    
    organic = data.get("organic_results", [])
    if not organic:
        return "No relevant information found."
        
    # Simple summarization: take snippets
    snippets = [r.get("snippet", "") for r in organic if r.get("snippet")]
    
    if snippets:
        return " ".join(snippets[:2]) # Return first 2 snippets
    
    return "Found information but no clear summary available."
