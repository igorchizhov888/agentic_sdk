import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class PromptStorage:
    """SQLite storage for versioned prompts"""
    
    def __init__(self, db_path: str = "prompts.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self._create_tables()
    
    def _create_tables(self):
        """Create prompts table if it doesn't exist"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                template TEXT NOT NULL,
                variables TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                is_active INTEGER DEFAULT 0,
                metadata TEXT,
                UNIQUE(name, version)
            )
        """)
        self.conn.commit()

    def save_prompt(self, name: str, version: int, template: str, 
                    variables: List[str], created_by: str, metadata: Dict[str, Any]) -> int:
        """Save a new prompt version"""
        cursor = self.conn.execute("""
            INSERT INTO prompts (name, version, template, variables, created_at, created_by, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            version,
            template,
            json.dumps(variables),
            datetime.now().isoformat(),
            created_by,
            json.dumps(metadata)
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_next_version(self, name: str) -> int:
        """Get the next version number for a prompt"""
        cursor = self.conn.execute(
            "SELECT MAX(version) as max_ver FROM prompts WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return (row['max_ver'] or 0) + 1
    
    def load_prompt(self, name: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Load a prompt by name and version"""
        if version is None:
            cursor = self.conn.execute(
                "SELECT * FROM prompts WHERE name = ? AND is_active = 1",
                (name,)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM prompts WHERE name = ? AND version = ?",
                (name, version)
            )
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        return {
            'id': row['id'],
            'name': row['name'],
            'version': row['version'],
            'template': row['template'],
            'variables': json.loads(row['variables']),
            'created_at': row['created_at'],
            'created_by': row['created_by'],
            'is_active': bool(row['is_active']),
            'metadata': json.loads(row['metadata']) if row['metadata'] else {}
        }

    def set_active(self, name: str, version: int):
        """Make a specific version active (deactivate others)"""
        # Deactivate all versions of this prompt
        self.conn.execute(
            "UPDATE prompts SET is_active = 0 WHERE name = ?",
            (name,)
        )
        
        # Activate the specified version
        self.conn.execute(
            "UPDATE prompts SET is_active = 1 WHERE name = ? AND version = ?",
            (name, version)
        )
        self.conn.commit()
    
    def get_active_version(self, name: str) -> Optional[int]:
        """Get the currently active version number"""
        cursor = self.conn.execute(
            "SELECT version FROM prompts WHERE name = ? AND is_active = 1",
            (name,)
        )
        row = cursor.fetchone()
        return row['version'] if row else None
    
    def get_all_versions(self, name: str) -> List[Dict[str, Any]]:
        """Get all versions of a prompt"""
        cursor = self.conn.execute(
            "SELECT * FROM prompts WHERE name = ? ORDER BY version DESC",
            (name,)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'version': row['version'],
                'created_at': row['created_at'],
                'created_by': row['created_by'],
                'is_active': bool(row['is_active']),
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            })
        return results
