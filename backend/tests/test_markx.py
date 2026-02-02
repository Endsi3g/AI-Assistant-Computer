
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import markx_actions

@pytest.mark.asyncio
async def test_weather_report_structure():
    with patch('webbrowser.open') as mock_open:
        result = await markx_actions.weather_report("New York", "today")
        assert "Opened weather report" in result
        mock_open.assert_called_once()
        args, _ = mock_open.call_args
        assert "New+York" in args[0]

@pytest.mark.asyncio
async def test_send_message_missing_library():
    # If pyautogui is missing, it should handle gracefully
    if markx_actions.pyautogui is None:
        result = await markx_actions.send_message("Mom", "Hello")
        assert "pyautogui is not installed" in result

@pytest.mark.asyncio
async def test_web_search_fallback():
    # Test fallback when API key is missing
    with patch('webbrowser.open') as mock_open:
        result = await markx_actions.markx_web_search("cats")
        assert "Opened search results" in result
        mock_open.assert_called_once()
