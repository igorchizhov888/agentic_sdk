"""Storage for A/B testing data"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class ABTestStorage:
    """SQLite storage for A/B tests"""
    
    def __init__(self, db_path: str = "ab_tests.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create A/B test tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                version_a INTEGER NOT NULL,
                version_b INTEGER NOT NULL,
                split_percentage INTEGER NOT NULL,
                min_samples INTEGER DEFAULT 100,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                winner_version INTEGER,
                metadata TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                trace_id TEXT NOT NULL,
                success INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                cost REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(test_id) REFERENCES ab_tests(test_id)
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_results 
            ON ab_test_results(test_id, version)
        """)
        
        self.conn.commit()
    
    def create_test(self, test_id: str, prompt_name: str, 
                   version_a: int, version_b: int, 
                   split_percentage: int, min_samples: int,
                   metadata: Dict[str, Any] = None):
        """Create a new A/B test"""
        self.conn.execute("""
            INSERT INTO ab_tests 
            (test_id, prompt_name, version_a, version_b, split_percentage, 
             min_samples, status, started_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?)
        """, (
            test_id,
            prompt_name,
            version_a,
            version_b,
            split_percentage,
            min_samples,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))
        self.conn.commit()
    
    def get_active_test(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """Get active test for a prompt"""
        cursor = self.conn.execute("""
            SELECT * FROM ab_tests 
            WHERE prompt_name = ? AND status = 'running'
            LIMIT 1
        """, (prompt_name,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def record_result(self, test_id: str, version: int, trace_id: str,
                     success: bool, duration: float, cost: float = 0.0):
        """Record a test result"""
        self.conn.execute("""
            INSERT INTO ab_test_results
            (test_id, version, trace_id, success, duration_seconds, cost, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            version,
            trace_id,
            int(success),
            duration,
            cost,
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_test_results(self, test_id: str) -> Dict[str, Dict[str, Any]]:
        """Get aggregated results for a test"""
        # Get test info to know which versions
        test_cursor = self.conn.execute("""
            SELECT version_a, version_b FROM ab_tests WHERE test_id = ?
        """, (test_id,))
        test_row = test_cursor.fetchone()
        
        if not test_row:
            return {}
        
        version_a = test_row['version_a']
        version_b = test_row['version_b']
        
        # Get results for each version
        cursor = self.conn.execute("""
            SELECT 
                version,
                COUNT(*) as total_requests,
                SUM(success) as success_count,
                AVG(duration_seconds) as avg_duration,
                SUM(cost) as total_cost
            FROM ab_test_results
            WHERE test_id = ?
            GROUP BY version
        """, (test_id,))
        
        results = {}
        for row in cursor.fetchall():
            version = row['version']
            stats = {
                'total_requests': row['total_requests'],
                'success_count': row['success_count'],
                'success_rate': row['success_count'] / row['total_requests'] if row['total_requests'] > 0 else 0,
                'avg_duration': row['avg_duration'],
                'total_cost': row['total_cost']
            }
            
            # Map to version_a or version_b
            if version == version_a:
                results['version_a'] = stats
            elif version == version_b:
                results['version_b'] = stats
        
        return results
    
    def complete_test(self, test_id: str, winner_version: Optional[int] = None):
        """Mark test as completed"""
        self.conn.execute("""
            UPDATE ab_tests 
            SET status = 'completed', ended_at = ?, winner_version = ?
            WHERE test_id = ?
        """, (datetime.now().isoformat(), winner_version, test_id))
        self.conn.commit()
    
    def cancel_test(self, test_id: str):
        """Cancel a running test"""
        self.conn.execute("""
            UPDATE ab_tests 
            SET status = 'cancelled', ended_at = ?
            WHERE test_id = ?
        """, (datetime.now().isoformat(), test_id))
        self.conn.commit()
    
    def list_tests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tests"""
        if status:
            cursor = self.conn.execute(
                "SELECT * FROM ab_tests WHERE status = ? ORDER BY started_at DESC",
                (status,)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM ab_tests ORDER BY started_at DESC"
            )
        
        return [dict(row) for row in cursor.fetchall()]
