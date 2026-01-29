"""
Long-term Memory for Persistent Knowledge

SQLite-backed storage for knowledge that persists across all sessions.
Stores user profiles, preferences, facts, and learned patterns.
Never cleared automatically.
"""

import sqlite3
from typing import Any, Optional, Dict, List
from datetime import datetime
import json


class LongTermMemory:
    """
    L3 Long-term Memory - Persistent across all sessions
    
    Used for:
    - User profile and preferences
    - Historical patterns
    - Learned facts and knowledge
    - Cross-session context
    
    Never cleared automatically.
    """
    
    def __init__(self, user_id: str = "default", db_path: str = "long_term_memory.db"):
        self.user_id = user_id
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create long-term memory tables"""
        # Key-value storage
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, category, key)
            )
        """)
        
        # Facts and knowledge
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fact TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_category 
            ON long_term_memory(user_id, category)
        """)
        
        self.conn.commit()
    
    def store(self, key: str, value: Any, category: str = "general") -> None:
        """Store a value in long-term memory"""
        value_json = json.dumps(value)
        now = datetime.now().isoformat()
        
        self.conn.execute("""
            INSERT INTO long_term_memory (user_id, category, key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at,
                access_count = access_count + 1
        """, (self.user_id, category, key, value_json, now, now))
        self.conn.commit()
    
    def retrieve(self, key: str, category: str = "general") -> Optional[Any]:
        """Retrieve a value from long-term memory"""
        cursor = self.conn.execute("""
            SELECT value FROM long_term_memory
            WHERE user_id = ? AND category = ? AND key = ?
        """, (self.user_id, category, key))
        
        row = cursor.fetchone()
        if row:
            # Update access count
            self.conn.execute("""
                UPDATE long_term_memory 
                SET access_count = access_count + 1
                WHERE user_id = ? AND category = ? AND key = ?
            """, (self.user_id, category, key))
            self.conn.commit()
            return json.loads(row['value'])
        return None
    
    def exists(self, key: str, category: str = "general") -> bool:
        """Check if key exists in long-term memory"""
        cursor = self.conn.execute("""
            SELECT 1 FROM long_term_memory
            WHERE user_id = ? AND category = ? AND key = ?
        """, (self.user_id, category, key))
        return cursor.fetchone() is not None
    
    def delete(self, key: str, category: str = "general") -> bool:
        """Delete a key from long-term memory"""
        cursor = self.conn.execute("""
            DELETE FROM long_term_memory
            WHERE user_id = ? AND category = ? AND key = ?
        """, (self.user_id, category, key))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all items in a category"""
        cursor = self.conn.execute("""
            SELECT key, value FROM long_term_memory
            WHERE user_id = ? AND category = ?
        """, (self.user_id, category))
        
        result = {}
        for row in cursor.fetchall():
            result[row['key']] = json.loads(row['value'])
        return result
    
    def list_categories(self) -> List[str]:
        """List all categories for this user"""
        cursor = self.conn.execute("""
            SELECT DISTINCT category FROM long_term_memory
            WHERE user_id = ?
        """, (self.user_id,))
        return [row['category'] for row in cursor.fetchall()]
    
    def store_fact(self, fact: str, confidence: float = 1.0, source: str = None) -> int:
        """Store a fact in knowledge base"""
        cursor = self.conn.execute("""
            INSERT INTO knowledge_base (user_id, fact, confidence, source, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (self.user_id, fact, confidence, source, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for facts containing query string"""
        cursor = self.conn.execute("""
            SELECT id, fact, confidence, source, created_at
            FROM knowledge_base
            WHERE user_id = ? AND fact LIKE ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
        """, (self.user_id, f'%{query}%', limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(DISTINCT category) as total_categories,
                SUM(access_count) as total_accesses
            FROM long_term_memory
            WHERE user_id = ?
        """, (self.user_id,))
        
        stats = dict(cursor.fetchone())
        
        cursor = self.conn.execute("""
            SELECT COUNT(*) as total_facts FROM knowledge_base WHERE user_id = ?
        """, (self.user_id,))
        
        stats['total_facts'] = cursor.fetchone()['total_facts']
        return stats
    
    def clear_user(self) -> None:
        """Clear all memory for this user (use with caution!)"""
        self.conn.execute("DELETE FROM long_term_memory WHERE user_id = ?", (self.user_id,))
        self.conn.execute("DELETE FROM knowledge_base WHERE user_id = ?", (self.user_id,))
        self.conn.commit()
