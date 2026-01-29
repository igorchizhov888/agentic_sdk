"""
Hierarchical Memory Manager

Coordinates all three memory levels:
- L1 Working Memory (task-scoped)
- L2 Session Memory (session-scoped)  
- L3 Long-term Memory (persistent)
"""

from typing import Any, Optional, Dict, List
from .working_memory import WorkingMemory
from .session_memory import SessionMemory
from .long_term_memory import LongTermMemory


class HierarchicalMemory:
    """
    Manages three-level memory hierarchy.
    
    Provides unified interface for storing and retrieving data
    across working, session, and long-term memory.
    """
    
    def __init__(self, user_id: str = "default", session_id: str = None):
        """
        Initialize hierarchical memory.
        
        Args:
            user_id: User identifier for long-term memory
            session_id: Session identifier for session memory
        """
        self.user_id = user_id
        self.session_id = session_id
        
        # Initialize all three levels
        self.working = WorkingMemory()
        self.session = SessionMemory(session_id) if session_id else None
        self.long_term = LongTermMemory(user_id)
    
    def store(self, key: str, value: Any, level: str = "working", **kwargs) -> None:
        """
        Store value in specified memory level.
        
        Args:
            key: Key to store under
            value: Value to store
            level: Memory level ("working", "session", "long_term")
            **kwargs: Additional args (e.g., category for long_term)
        """
        if level == "working":
            self.working.store(key, value)
        elif level == "session":
            if not self.session:
                raise ValueError("Session memory not initialized (no session_id)")
            self.session.store(key, value)
        elif level == "long_term":
            category = kwargs.get("category", "general")
            self.long_term.store(key, value, category)
        else:
            raise ValueError(f"Invalid memory level: {level}")
    
    def retrieve(self, key: str, level: str = None, **kwargs) -> Optional[Any]:
        """
        Retrieve value from memory.
        
        If level is specified, searches only that level.
        If level is None, searches all levels (working -> session -> long_term).
        
        Args:
            key: Key to retrieve
            level: Memory level to search (None = search all)
            **kwargs: Additional args (e.g., category for long_term)
        """
        if level:
            # Search specific level
            if level == "working":
                return self.working.retrieve(key)
            elif level == "session":
                if not self.session:
                    return None
                return self.session.retrieve(key)
            elif level == "long_term":
                category = kwargs.get("category", "general")
                return self.long_term.retrieve(key, category)
            else:
                raise ValueError(f"Invalid memory level: {level}")
        else:
            # Search all levels (working -> session -> long_term)
            value = self.working.retrieve(key)
            if value is not None:
                return value
            
            if self.session:
                value = self.session.retrieve(key)
                if value is not None:
                    return value
            
            category = kwargs.get("category", "general")
            return self.long_term.retrieve(key, category)
    
    def promote(self, key: str, from_level: str, to_level: str, **kwargs) -> bool:
        """
        Promote data from one memory level to another.
        
        Example: Promote frequently used session data to long-term memory.
        
        Args:
            key: Key to promote
            from_level: Source memory level
            to_level: Destination memory level
            **kwargs: Additional args for storage
        """
        value = self.retrieve(key, level=from_level)
        if value is None:
            return False
        
        self.store(key, value, level=to_level, **kwargs)
        return True
    
    def clear_working(self) -> None:
        """Clear working memory (typically after task completion)"""
        self.working.clear()
    
    def clear_session(self) -> None:
        """Clear session memory (typically after session ends)"""
        if self.session:
            self.session.clear_session()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all memory levels"""
        summary = {
            "working": {
                "size": self.working.size(),
                "keys": self.working.keys()
            },
            "session": None,
            "long_term": self.long_term.get_stats()
        }
        
        if self.session:
            summary["session"] = {
                "session_id": self.session_id,
                "keys": self.session.keys()
            }
        
        return summary
    
    def store_fact(self, fact: str, confidence: float = 1.0, source: str = None) -> int:
        """Store a fact in long-term knowledge base"""
        return self.long_term.store_fact(fact, confidence, source)
    
    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search facts in long-term knowledge base"""
        return self.long_term.search_facts(query, limit)
