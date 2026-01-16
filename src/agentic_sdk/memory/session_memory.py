"""
Session Memory for Agent Context

SQLite-backed storage for conversation history and session context.
Persists across tasks within a session, cleared when session ends.
"""

import sqlite3
from typing import Any, Optional, Dict
from datetime import datetime
import json


class SessionMemory:
    """
    L2 Session Memory - Persistent within session
    
    Used for:
    - Conversation history
    - User preferences for session
    - Recent decisions
    - Context across multiple tasks
    
    Cleared when session ends.
    """
    
    def __init__(self, session_id: str, db_path: str = "session_memory.db"):
        self.session_id = session_id
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
    
    def _create_table(self):
        """Create session memory table"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS session_memory (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                stored_at TEXT NOT NULL,
                PRIMARY KEY (session_id, key)
            )
        """)
        self.conn.commit()
    
    def store(self, key: str, value: Any) -> None:
        """Store a value in session memory"""
        value_json = json.dumps(value)
        self.conn.execute("""
            INSERT OR REPLACE INTO session_memory (session_id, key, value, stored_at)
            VALUES (?, ?, ?, ?)
        """, (self.session_id, key, value_json, datetime.now().isoformat()))
        self.conn.commit()
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from session memory"""
        cursor = self.conn.execute("""
            SELECT value FROM session_memory
            WHERE session_id = ? AND key = ?
        """, (self.session_id, key))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row['value'])
        return None
    
    def exists(self, key: str) -> bool:
        """Check if key exists in session memory"""
        cursor = self.conn.execute("""
            SELECT 1 FROM session_memory
            WHERE session_id = ? AND key = ?
        """, (self.session_id, key))
        return cursor.fetchone() is not None
    
    def delete(self, key: str) -> bool:
        """Delete a key from session memory"""
        cursor = self.conn.execute("""
            DELETE FROM session_memory
            WHERE session_id = ? AND key = ?
        """, (self.session_id, key))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def clear_session(self) -> None:
        """Clear all memory for this session"""
        self.conn.execute("""
            DELETE FROM session_memory WHERE session_id = ?
        """, (self.session_id,))
        self.conn.commit()
    
    def keys(self) -> list:
        """Get all keys for this session"""
        cursor = self.conn.execute("""
            SELECT key FROM session_memory WHERE session_id = ?
        """, (self.session_id,))
        return [row['key'] for row in cursor.fetchall()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export session memory as dictionary"""
        result = {}
        for key in self.keys():
            result[key] = self.retrieve(key)
        return result
