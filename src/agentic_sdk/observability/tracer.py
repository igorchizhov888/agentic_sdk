"""Observability and tracing for agents"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager
import sqlite3
import json
import time
from uuid import uuid4


@dataclass
class SpanContext:
    """Context for a trace span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.attributes[key] = value
    
    def end(self) -> float:
        """End span and return duration"""
        return time.time() - self.start_time


class TraceStorage:
    """SQLite storage for traces"""
    
    def __init__(self, db_path: str = "traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create trace tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                task TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                success INTEGER,
                error TEXT,
                metadata TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                span_id TEXT UNIQUE NOT NULL,
                trace_id TEXT NOT NULL,
                parent_span_id TEXT,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                attributes TEXT,
                FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
            )
        """)
        
        # Create indexes for common queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_agent 
            ON traces(agent_id, start_time)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_spans_trace 
            ON spans(trace_id, start_time)
        """)
        
        self.conn.commit()
    
    def start_trace(self, trace_id: str, agent_id: str, session_id: str, 
                    task: str, metadata: Dict[str, Any] = None):
        """Start a new trace"""
        self.conn.execute("""
            INSERT INTO traces 
            (trace_id, agent_id, session_id, task, start_time, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trace_id,
            agent_id,
            session_id,
            task,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))
        self.conn.commit()
    
    def end_trace(self, trace_id: str, duration: float, 
                  success: bool, error: Optional[str] = None):
        """End a trace"""
        self.conn.execute("""
            UPDATE traces 
            SET end_time = ?, duration_seconds = ?, success = ?, error = ?
            WHERE trace_id = ?
        """, (
            datetime.now().isoformat(),
            duration,
            int(success),
            error,
            trace_id
        ))
        self.conn.commit()
    
    def record_span(self, span: SpanContext, duration: float):
        """Record a completed span"""
        self.conn.execute("""
            INSERT INTO spans
            (span_id, trace_id, parent_span_id, name, start_time, end_time, 
             duration_seconds, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            span.span_id,
            span.trace_id,
            span.parent_span_id,
            span.name,
            datetime.fromtimestamp(span.start_time).isoformat(),
            datetime.now().isoformat(),
            duration,
            json.dumps(span.attributes)
        ))
        self.conn.commit()
    
    def record_metric(self, trace_id: str, metric_name: str, 
                     metric_value: float, tags: Dict[str, str] = None):
        """Record a metric"""
        self.conn.execute("""
            INSERT INTO metrics
            (trace_id, metric_name, metric_value, timestamp, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (
            trace_id,
            metric_name,
            metric_value,
            datetime.now().isoformat(),
            json.dumps(tags or {})
        ))
        self.conn.commit()
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace by ID"""
        cursor = self.conn.execute(
            "SELECT * FROM traces WHERE trace_id = ?",
            (trace_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def get_spans(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace"""
        cursor = self.conn.execute(
            "SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time",
            (trace_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_metrics(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for a trace"""
        cursor = self.conn.execute(
            "SELECT * FROM metrics WHERE trace_id = ? ORDER BY timestamp",
            (trace_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def query_traces(self, agent_id: Optional[str] = None,
                     success: Optional[bool] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Query traces with filters"""
        query = "SELECT * FROM traces WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        if success is not None:
            query += " AND success = ?"
            params.append(int(success))
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


class AgentTracer:
    """
    Tracing and observability for agents.
    
    Features:
    - Distributed tracing
    - Span tracking for operations
    - Metrics collection
    - Performance monitoring
    """
    
    def __init__(self, storage: Optional[TraceStorage] = None):
        self.storage = storage or TraceStorage()
        self._current_trace: Optional[str] = None
        self._current_spans: List[SpanContext] = []
    
    @contextmanager
    def trace_execution(self, agent_id: str, session_id: str, task: str,
                       metadata: Dict[str, Any] = None):
        """
        Context manager for tracing agent execution.
        
        Usage:
            with tracer.trace_execution(agent_id, session_id, task):
                # agent execution here
                pass
        """
        trace_id = f"trace-{uuid4()}"
        self._current_trace = trace_id
        
        # Start trace
        self.storage.start_trace(
            trace_id=trace_id,
            agent_id=agent_id,
            session_id=session_id,
            task=task,
            metadata=metadata
        )
        
        start = time.time()
        success = True
        error = None
        
        try:
            yield trace_id
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration = time.time() - start
            
            # End trace
            self.storage.end_trace(
                trace_id=trace_id,
                duration=duration,
                success=success,
                error=error
            )
            
            self._current_trace = None
    
    @contextmanager
    def start_span(self, name: str, attributes: Dict[str, Any] = None,
                   parent_span_id: Optional[str] = None):
        """
        Context manager for creating a span.
        
        Usage:
            with tracer.start_span("llm_planning"):
                # operation here
                pass
        """
        if not self._current_trace:
            raise RuntimeError("No active trace. Use trace_execution first.")
        
        span = SpanContext(
            span_id=f"span-{uuid4()}",
            trace_id=self._current_trace,
            parent_span_id=parent_span_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {}
        )
        
        self._current_spans.append(span)
        
        try:
            yield span
        finally:
            duration = span.end()
            self.storage.record_span(span, duration)
            self._current_spans.remove(span)
    
    def record_metric(self, metric_name: str, metric_value: float,
                     tags: Dict[str, str] = None):
        """Record a metric for current trace"""
        if not self._current_trace:
            raise RuntimeError("No active trace")
        
        self.storage.record_metric(
            trace_id=self._current_trace,
            metric_name=metric_name,
            metric_value=metric_value,
            tags=tags
        )
    
    def get_trace_details(self, trace_id: str) -> Dict[str, Any]:
        """Get complete trace details with spans and metrics"""
        trace = self.storage.get_trace(trace_id)
        if not trace:
            return None
        
        spans = self.storage.get_spans(trace_id)
        metrics = self.storage.get_metrics(trace_id)
        
        return {
            'trace': trace,
            'spans': spans,
            'metrics': metrics
        }
    
    def query_traces(self, agent_id: Optional[str] = None,
                    success: Optional[bool] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Query traces with filters"""
        return self.storage.query_traces(
            agent_id=agent_id,
            success=success,
            limit=limit
        )
