
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ProactiveCore

def test_proactive_core_safe_init():
    """Test that ProactiveCore initializes without error even if CrewAI is missing."""
    core = ProactiveCore()
    assert core is not None
    # If CrewAI is missing, crew should be None or agents not initialized
    # We just want to ensure it doesn't raise ImportError
    
def test_swarm_execution_safe():
    """Test that running swarm returns a safe message if dependencies are missing."""
    core = ProactiveCore()
    result = core.run_swarm("Test Objective")
    assert isinstance(result, str)
    # Should either be the result (if installed) or the error message
