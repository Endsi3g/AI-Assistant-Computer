
import pytest
import sys
import os
import shutil
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vector_memory import VectorMemoryService

TEST_DB_PATH = "data/test_vector_store"

@pytest.fixture
def vector_service():
    # Setup
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)
    
    service = VectorMemoryService(persist_path=TEST_DB_PATH)
    yield service
    
    # Teardown
    # ChromaDB client might hold locks, so cleanup might be tricky in Windows
    # We'll try our best
    try:
        if os.path.exists(TEST_DB_PATH):
            shutil.rmtree(TEST_DB_PATH)
    except:
        pass

def test_add_and_search(vector_service):
    # Add memory
    doc_id = vector_service.add_memory(
        text="Jarvis is a highly advanced AI system designed by Stark.",
        metadata={"category": "test"}
    )
    assert doc_id is not None
    
    # Search
    results = vector_service.search_memory("who created jarvis?")
    assert len(results) > 0
    assert "Stark" in results[0]['content']
    
def test_persistence(vector_service):
    # Add
    vector_service.add_memory("The sky is blue today.")
    count = vector_service.count()
    assert count == 1
