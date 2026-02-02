
import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scheduler import SchedulerService

# We patch AsyncIOScheduler to avoid real event loop issues during unit tests
# unless we really want to test the scheduling engine itself.
# For this unit test, we just want to verify our Service wrapper logic.

@patch('services.scheduler.AsyncIOScheduler')
def test_scheduler_mocked(MockScheduler):
    """Test that scheduler service calls the underlying scheduler correctly."""
    mock_sched_instance = MockScheduler.return_value
    mock_sched_instance.running = False
    
    service = SchedulerService()
    
    # Test Start
    service.start()
    mock_sched_instance.start.assert_called_once()
    
    # Test Shutdown
    mock_sched_instance.running = True
    service.shutdown()
    mock_sched_instance.shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_daily_briefing_job_logic():
    """Test the daily briefing logic isolated from the scheduler."""
    mock_memory = MagicMock()
    # Mock store_memory to return a future since it's awaited
    f = asyncio.Future()
    f.set_result(True)
    mock_memory.store_memory.return_value = f
    
    # We don't strictly need the actual scheduler for this test
    with patch('services.scheduler.AsyncIOScheduler'):
        service = SchedulerService(memory_service=mock_memory)
        
        # Trigger the logic directly
        await service.run_daily_briefing()
        
        # Verify it attempted to store the briefing
        assert mock_memory.store_memory.called
