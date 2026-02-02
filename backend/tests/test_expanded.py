
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import markx_actions

@pytest.mark.asyncio
async def test_aircraft_report_opensky():
    # Mock httpx client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "states": [
            ["abc", "CALLSIGN1", "US", 0, 0, 0, 0, 0, False, 0, 0, 0, 0, 0, 0, False, 0],
            ["def", "CALLSIGN2", "US", 0, 0, 0, 0, 0, False, 0, 0, 0, 0, 0, 0, False, 0]
        ]
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await markx_actions.aircraft_report()
        assert "confirm 2 aircraft" in result
        assert "CALLSIGN1" in result

@pytest.mark.asyncio
async def test_weather_report_wttr():
    # Mock wttr.in response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "New York: Sunny 25C"
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with patch("webbrowser.open"): # Suppress browser opening
            result = await markx_actions.weather_report("New York")
            assert "Sunny 25C" in result

@pytest.mark.asyncio
async def test_messaging_platforms():
    # Verify logic for determining shortcuts
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        await markx_actions.send_message("Chan", "Hi", "Discord")
        # Just verifying it calls the automation thread
        mock_thread.assert_called_once()
