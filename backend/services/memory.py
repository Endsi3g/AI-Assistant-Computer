"""
Memory Service
Persistent memory using Supabase for conversations, knowledge, and preferences
"""
import os
from datetime import datetime
from typing import Optional
from config import get_settings

# For now, use local JSON file as fallback if Supabase not configured
import json
import aiofiles
from .vector_memory import VectorMemoryService


class MemoryService:
    """Persistent memory service with local fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase_client = None
        self.local_memory_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'data', 
            'memory.json'
        )
        
        # Initialize Supabase if configured
        if self.settings.supabase_url and self.settings.supabase_key:
            try:
                from supabase import create_client
                self.supabase_client = create_client(
                    self.settings.supabase_url,
                    self.settings.supabase_key
                )
                print("[OK] Supabase memory connected")
            except Exception as e:
                print(f"[WARNING] Supabase not configured, using local storage: {e}")
        else:
            print("[WARNING] Using local memory storage")
        
        # Ensure local storage directory exists
        os.makedirs(os.path.dirname(self.local_memory_path), exist_ok=True)
        
        # Initialize local memory file if needed
        if not os.path.exists(self.local_memory_path):
            with open(self.local_memory_path, 'w') as f:
                json.dump({
                    "conversations": [],
                    "memories": [],
                    "preferences": {}
                }, f)
        
        # Initialize Vector Memory
        try:
             self.vector_store = VectorMemoryService(persist_path=os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_store'))
             print("[OK] ChromaDB vector memory connected")
        except Exception as e:
             print(f"[WARNING] ChromaDB failed to initialize: {e}")
             self.vector_store = None
    
    async def _load_local_memory(self) -> dict:
        """Load memory from local JSON file"""
        try:
            async with aiofiles.open(self.local_memory_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception:
            return {"conversations": [], "memories": [], "preferences": {}}
    
    async def _save_local_memory(self, data: dict):
        """Save memory to local JSON file"""
        async with aiofiles.open(self.local_memory_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    async def store_conversation(self, user_message: str, assistant_message: str):
        """Store a conversation exchange"""
        conversation = {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "created_at": datetime.now().isoformat()
        }
        
        if self.supabase_client:
            try:
                self.supabase_client.table("conversations").insert(conversation).execute()
            except Exception as e:
                print(f"Error storing to Supabase: {e}")
                # Fallback to local
                data = await self._load_local_memory()
                data["conversations"].append(conversation)
                await self._save_local_memory(data)
        else:
            data = await self._load_local_memory()
            data["conversations"].append(conversation)
            await self._save_local_memory(data)
    
    async def store_memory(self, category: str, content: str, importance: int = 5):
        """Store a memory item"""
        memory = {
            "category": category,
            "content": content,
            "importance": importance,
            "created_at": datetime.now().isoformat()
        }
        
        if self.supabase_client:
            try:
                self.supabase_client.table("memories").insert(memory).execute()
            except Exception as e:
                print(f"Error storing memory to Supabase: {e}")
                data = await self._load_local_memory()
                data["memories"].append(memory)
                await self._save_local_memory(data)
        else:
            data = await self._load_local_memory()
            data["memories"].append(memory)
            await self._save_local_memory(data)
            
        # Store in Vector DB as well for semantic search
        if self.vector_store:
            try:
                self.vector_store.add_memory(
                    text=content,
                    metadata={"category": category, "importance": importance, "source": "memory_service"}
                )
            except Exception as e:
                print(f"Error adding to Vector DB: {e}")
    
    async def search_memory(self, query: str, category: str = "all") -> list:
        """Search memories by query and optional category"""
        query_lower = query.lower()
        results = []
        
        if self.supabase_client:
            try:
                # Build query
                db_query = self.supabase_client.table("memories").select("*")
                
                if category != "all":
                    db_query = db_query.eq("category", category)
                
                response = db_query.execute()
                
                # Filter by content match (simple search)
                for item in response.data:
                    if query_lower in item["content"].lower():
                        results.append(item)
                        
            except Exception as e:
                print(f"Error searching Supabase: {e}")
                # Fallback to local
                data = await self._load_local_memory()
                results = self._search_local(data["memories"], query_lower, category)
        else:
            data = await self._load_local_memory()
            results = self._search_local(data["memories"], query_lower, category)
        
        # Sort by importance
        results.sort(key=lambda x: x.get("importance", 5), reverse=True)
        
        # If we have vector store, perform a check there too and merge/augment (Simple augmentation for now)
        if self.vector_store:
            try:
                vector_results = self.vector_store.search_memory(query, n_results=5)
                # Normalize vector results to match memory dict format
                for vr in vector_results:
                    # Check if already in results to avoid duplicates (naive check)
                    if not any(r['content'] == vr['content'] for r in results):
                        results.append({
                            "content": vr['content'],
                            "category": vr['metadata'].get("category", "all"),
                            "importance": vr['metadata'].get("importance", 5),
                            "created_at": vr['metadata'].get("timestamp", ""),
                            "source": "vector"
                        })
            except Exception as e:
                print(f"Error searching Vector DB: {e}")

        return results[:10]  # Return top 10
    
    def _search_local(self, memories: list, query: str, category: str) -> list:
        """Search local memory store"""
        results = []
        for memory in memories:
            if category != "all" and memory.get("category") != category:
                continue
            if query in memory.get("content", "").lower():
                results.append(memory)
        return results
    
    async def get_recent_conversations(self, limit: int = 10) -> list:
        """Get recent conversations for context"""
        if self.supabase_client:
            try:
                response = self.supabase_client.table("conversations") \
                    .select("*") \
                    .order("created_at", desc=True) \
                    .limit(limit) \
                    .execute()
                return response.data
            except Exception as e:
                print(f"Error fetching from Supabase: {e}")
                data = await self._load_local_memory()
                return data["conversations"][-limit:]
        else:
            data = await self._load_local_memory()
            return data["conversations"][-limit:]
    
    async def set_preference(self, key: str, value):
        """Set a user preference"""
        if self.supabase_client:
            try:
                # Upsert preference
                self.supabase_client.table("preferences").upsert({
                    "key": key,
                    "value": json.dumps(value),
                    "updated_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                print(f"Error saving preference to Supabase: {e}")
                data = await self._load_local_memory()
                data["preferences"][key] = value
                await self._save_local_memory(data)
        else:
            data = await self._load_local_memory()
            data["preferences"][key] = value
            await self._save_local_memory(data)
    
    async def get_preference(self, key: str, default=None):
        """Get a user preference"""
        if self.supabase_client:
            try:
                response = self.supabase_client.table("preferences") \
                    .select("value") \
                    .eq("key", key) \
                    .single() \
                    .execute()
                return json.loads(response.data["value"]) if response.data else default
            except Exception:
                data = await self._load_local_memory()
                return data["preferences"].get(key, default)
        else:
            data = await self._load_local_memory()
            return data["preferences"].get(key, default)

    # ========================================
    # MEMORY ENHANCEMENT METHODS
    # ========================================
    
    async def get_context_summary(self, limit: int = 20) -> str:
        """Generate a context summary from recent conversations"""
        conversations = await self.get_recent_conversations(limit)
        
        if not conversations:
            return ""
        
        # Build context summary
        context_parts = []
        for conv in conversations[-5:]:  # Last 5 conversations for immediate context
            user_msg = conv.get("user_message", "")[:100]
            context_parts.append(f"User asked about: {user_msg}")
        
        return "\n".join(context_parts)
    
    async def summarize_conversation(self, messages: list) -> str:
        """Create a summary of a conversation"""
        if len(messages) < 2:
            return ""
        
        # Simple extractive summary - take key points
        summary_parts = []
        for msg in messages[:10]:  # Limit to first 10 messages
            content = msg.get("assistant_message", msg.get("content", ""))[:200]
            if content:
                summary_parts.append(content)
        
        return " | ".join(summary_parts)[:500]
    
    async def store_summary(self, session_id: str, summary: str):
        """Store a conversation summary"""
        await self.store_memory(
            category="conversation_summary",
            content=f"[{session_id}] {summary}",
            importance=7
        )
    
    async def get_session_context(self, session_id: str) -> dict:
        """Get context for a specific session"""
        data = await self._load_local_memory()
        
        # Find related memories
        related = []
        for memory in data.get("memories", []):
            if session_id in memory.get("content", ""):
                related.append(memory)
        
        # Get recent conversations
        recent = await self.get_recent_conversations(5)
        
        return {
            "session_id": session_id,
            "related_memories": related[:5],
            "recent_conversations": recent,
        }
    
    async def extract_entities(self, text: str) -> list:
        """Extract key entities from text (simple implementation)"""
        # Simple keyword extraction based on capitalization and patterns
        import re
        
        entities = []
        
        # Find capitalized words (potential names/places)
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(caps[:5])
        
        # Find email patterns
        emails = re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
        entities.extend(emails)
        
        # Find URLs
        urls = re.findall(r'https?://\S+', text)
        entities.extend(urls[:3])
        
        return list(set(entities))
    
    async def store_entities(self, entities: list, source: str = "conversation"):
        """Store extracted entities as memories"""
        for entity in entities:
            await self.store_memory(
                category="entity",
                content=f"{entity} (from {source})",
                importance=4
            )
    
    async def build_system_context(self) -> str:
        """Build context string for system prompt injection"""
        parts = []
        
        # Add user preferences
        data = await self._load_local_memory()
        prefs = data.get("preferences", {})
        if prefs:
            pref_str = ", ".join([f"{k}: {v}" for k, v in list(prefs.items())[:5]])
            parts.append(f"User preferences: {pref_str}")
        
        # Add recent context
        context = await self.get_context_summary(5)
        if context:
            parts.append(f"Recent context:\n{context}")
        
        # Add relevant memories
        memories = data.get("memories", [])
        if memories:
            important = sorted(memories, key=lambda x: x.get("importance", 0), reverse=True)[:3]
            mem_str = ", ".join([m.get("content", "")[:50] for m in important])
            parts.append(f"Key memories: {mem_str}")
        
        return "\n\n".join(parts)
    
    async def should_summarize(self, message_count: int) -> bool:
        """Check if we should trigger summarization"""
        return message_count > 0 and message_count % 10 == 0
