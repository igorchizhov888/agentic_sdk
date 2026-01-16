"""
Working Memory for SmartAgent

Simple in-memory storage for task execution context.
Stores intermediate results, tool outputs, and variables during task execution.
Cleared after task completes.
"""

from typing import Any, Dict, Optional
from datetime import datetime


class WorkingMemory:
    """
    L1 Working Memory - Fast, volatile, task-scoped
    
    Used for:
    - Storing intermediate results
    - Tool outputs
    - Task variables
    - Temporary data
    
    Cleared when task completes.
    """
    
    def __init__(self):
        self._memory: Dict[str, Any] = {}
        self._created_at = datetime.now()
    
    def store(self, key: str, value: Any) -> None:
        """Store a value in working memory"""
        self._memory[key] = {
            'value': value,
            'stored_at': datetime.now().isoformat()
        }
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from working memory"""
        if key in self._memory:
            return self._memory[key]['value']
        return None
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory"""
        return key in self._memory
    
    def delete(self, key: str) -> bool:
        """Delete a key from memory"""
        if key in self._memory:
            del self._memory[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all working memory"""
        self._memory.clear()
    
    def keys(self) -> list:
        """Get all keys in memory"""
        return list(self._memory.keys())
    
    def size(self) -> int:
        """Get number of items in memory"""
        return len(self._memory)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export memory as dictionary"""
        return {k: v['value'] for k, v in self._memory.items()}
