
import os
import uuid
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

class VectorMemoryService:
    def __init__(self, persist_path: str = "data/vector_store"):
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not installed. Vector memory disabled.")
            self.client = None
            self.collection = None
            return

        # Ensure directory exists
        os.makedirs(persist_path, exist_ok=True)
        
        # Initialize Client
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Use a standard embedding function
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="jarvis_long_term_memory",
            embedding_function=self.ef
        )

    def add_memory(self, text: str, metadata: Dict = None):
        """Add a memory to the vector store."""
        if metadata is None:
            metadata = {}
            
        # Add timestamp if not present
        if "timestamp" not in metadata:
            from datetime import datetime
            metadata["timestamp"] = datetime.now().isoformat()

        doc_id = str(uuid.uuid4())
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id

    def search_memory(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for memories semantically."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Parse results into a cleaner format
        output = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                output.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": results['distances'][0][i] if 'distances' in results else 0
                })
        return output

    def count(self):
        return self.collection.count()
