"""
Memory Manager

This module provides functionality for managing conversation and transaction history
using Cosmos DB for persistent storage.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

class MemoryItem(BaseModel):
    """Represents a single memory item."""
    id: str
    type: str  # 'conversation', 'transaction', 'insight', etc.
    content: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class MemoryManager:
    """
    Manages conversation and transaction history in Cosmos DB.
    
    This class provides methods to store, retrieve, and manage memories
    related to customer interactions and transactions.
    """
    
    @classmethod
    async def create(cls):
        """Async constructor for compatibility with FastAPI startup."""
        return cls()
    
    def __init__(self):
        """Initialize the memory manager."""
        # In a real implementation, this would initialize a Cosmos DB client
        self.memories: Dict[str, MemoryItem] = {}
        
    async def store_memory(self, memory: MemoryItem) -> str:
        """
        Store a memory item.
        
        Args:
            memory: The memory item to store.
            
        Returns:
            str: The ID of the stored memory.
        """
        # In a real implementation, this would store the memory in Cosmos DB
        self.memories[memory.id] = memory
        return memory.id
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve.
            
        Returns:
            Optional[MemoryItem]: The memory if found, None otherwise.
        """
        return self.memories.get(memory_id)
    
    async def search_memories(
        self, 
        query: str, 
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search for memories matching a query.
        
        Args:
            query: The search query.
            memory_type: Optional filter by memory type.
            limit: Maximum number of results to return.
            
        Returns:
            List[MemoryItem]: Matching memories, sorted by relevance.
        """
        # In a real implementation, this would use Cosmos DB's search capabilities
        results = []
        for memory in self.memories.values():
            if memory_type and memory.type != memory_type:
                continue
                
            # Simple text search for demonstration
            if query.lower() in json.dumps(memory.content).lower():
                results.append(memory)
                
        return results[:limit]
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for a user.
        
        Args:
            user_id: The ID of the user.
            limit: Maximum number of conversation items to return.
            
        Returns:
            List[MemoryItem]: Conversation history, most recent first.
        """
        # In a real implementation, this would query Cosmos DB
        user_memories = [
            m for m in self.memories.values() 
            if m.type == 'conversation' and m.content.get('user_id') == user_id
        ]
        
        # Sort by timestamp, most recent first
        user_memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        return user_memories[:limit]
    
    async def store_transaction(
        self, 
        transaction_data: Dict[str, Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a transaction in memory.
        
        Args:
            transaction_data: The transaction data to store.
            user_id: The ID of the user associated with the transaction.
            metadata: Additional metadata to store with the transaction.
            
        Returns:
            str: The ID of the stored transaction.
        """
        memory_id = f"txn_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        memory = MemoryItem(
            id=memory_id,
            type='transaction',
            content={
                'user_id': user_id,
                'transaction': transaction_data,
                'timestamp': datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        return await self.store_memory(memory)
    
    async def close(self):
        """Clean up resources."""
        # In a real implementation, this would close database connections
        pass
