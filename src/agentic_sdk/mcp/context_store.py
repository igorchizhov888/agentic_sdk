"""
Context Store - Persistent storage for agent execution contexts
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class StoredContext(BaseModel):
    """Stored context record."""
    session_id: str
    agent_id: str
    user_id: Optional[str] = None
    context_data: Dict[str, Any]
    created_at: str
    updated_at: str


class ContextStore:
    """Persistent context storage using SQLite."""

    def __init__(self, db_path: str = "agentic_sdk.db"):
        self.db_path = Path(db_path)
        self._initialize_db()
        logger.info("context_store_initialized", db_path=str(self.db_path))

    def _initialize_db(self) -> None:
        """Create database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                session_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                context_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                params TEXT NOT NULL,
                result TEXT NOT NULL,
                success INTEGER NOT NULL,
                executed_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES contexts(session_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contexts_agent ON contexts(agent_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_session ON execution_history(session_id)
        """)
        
        conn.commit()
        conn.close()

    def save_context(
        self,
        session_id: UUID,
        agent_id: UUID,
        context_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        """Save or update context."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        session_str = str(session_id)
        
        cursor.execute("SELECT session_id FROM contexts WHERE session_id = ?", (session_str,))
        exists = cursor.fetchone() is not None
        
        if exists:
            cursor.execute(
                "UPDATE contexts SET context_data = ?, updated_at = ? WHERE session_id = ?",
                (json.dumps(context_data), now, session_str)
            )
        else:
            cursor.execute(
                """INSERT INTO contexts 
                (session_id, agent_id, user_id, context_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (session_str, str(agent_id), user_id, json.dumps(context_data), now, now)
            )
        
        conn.commit()
        conn.close()

    def load_context(self, session_id: UUID) -> Optional[StoredContext]:
        """Load context by session ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, agent_id, user_id, context_data, created_at, updated_at
            FROM contexts WHERE session_id = ?
        """, (str(session_id),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return StoredContext(
                session_id=row[0],
                agent_id=row[1],
                user_id=row[2],
                context_data=json.loads(row[3]),
                created_at=row[4],
                updated_at=row[5],
            )
        return None

    def save_execution(
        self,
        session_id: UUID,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
    ) -> None:
        """Save tool execution to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO execution_history
            (session_id, tool_name, params, result, success, executed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(session_id),
            tool_name,
            json.dumps(params),
            json.dumps(result),
            1 if success else 0,
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        conn.close()

    def get_execution_history(self, session_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tool_name, params, result, success, executed_at
            FROM execution_history
            WHERE session_id = ?
            ORDER BY executed_at DESC
            LIMIT ?
        """, (str(session_id), limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "tool_name": row[0],
                "params": json.loads(row[1]),
                "result": json.loads(row[2]),
                "success": bool(row[3]),
                "executed_at": row[4],
            }
            for row in rows
        ]
