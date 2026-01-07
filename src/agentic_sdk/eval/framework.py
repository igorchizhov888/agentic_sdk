"""Evaluation framework for testing agent quality"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json
import sqlite3
from pathlib import Path


@dataclass
class TestCase:
    """A single test case for agent evaluation"""
    id: str
    task: str
    expected_output: Optional[str] = None
    expected_tools: Optional[List[str]] = None
    expected_steps: Optional[int] = None
    validator: Optional[Callable[[Any], bool]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EvaluationResult:
    """Result of running a test case"""
    test_case_id: str
    success: bool
    agent_output: str
    tools_used: List[str]
    steps_taken: int
    duration_seconds: float
    cost: float
    passed: bool
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EvaluationStorage:
    """Store evaluation results in SQLite"""
    
    def __init__(self, db_path: str = "evaluations.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create evaluation tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                prompt_version INTEGER,
                timestamp TEXT NOT NULL,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                avg_duration REAL,
                total_cost REAL,
                metadata TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                test_case_id TEXT NOT NULL,
                success INTEGER NOT NULL,
                agent_output TEXT,
                tools_used TEXT,
                steps_taken INTEGER,
                duration_seconds REAL,
                cost REAL,
                passed INTEGER NOT NULL,
                failure_reason TEXT,
                metadata TEXT,
                FOREIGN KEY(run_id) REFERENCES evaluation_runs(run_id)
            )
        """)
        
        self.conn.commit()
    
    def save_run(self, run_id: str, agent_name: str, prompt_version: Optional[int],
                 results: List[EvaluationResult], metadata: Dict[str, Any] = None):
        """Save evaluation run results"""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        avg_duration = sum(r.duration_seconds for r in results) / len(results) if results else 0
        total_cost = sum(r.cost for r in results)
        
        self.conn.execute("""
            INSERT INTO evaluation_runs 
            (run_id, agent_name, prompt_version, timestamp, total_tests, 
             passed_tests, failed_tests, avg_duration, total_cost, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            agent_name,
            prompt_version,
            datetime.now().isoformat(),
            len(results),
            passed,
            failed,
            avg_duration,
            total_cost,
            json.dumps(metadata or {})
        ))
        
        for result in results:
            self.conn.execute("""
                INSERT INTO evaluation_results
                (run_id, test_case_id, success, agent_output, tools_used,
                 steps_taken, duration_seconds, cost, passed, failure_reason, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                result.test_case_id,
                int(result.success),
                result.agent_output,
                json.dumps(result.tools_used),
                result.steps_taken,
                result.duration_seconds,
                result.cost,
                int(result.passed),
                result.failure_reason,
                json.dumps(result.metadata)
            ))
        
        self.conn.commit()
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation run summary"""
        cursor = self.conn.execute(
            "SELECT * FROM evaluation_runs WHERE run_id = ?",
            (run_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        return dict(row)
    
    def compare_runs(self, run_id1: str, run_id2: str) -> Dict[str, Any]:
        """Compare two evaluation runs"""
        run1 = self.get_run(run_id1)
        run2 = self.get_run(run_id2)
        
        if not run1 or not run2:
            return None
        
        return {
            'run1': run1,
            'run2': run2,
            'comparison': {
                'pass_rate_diff': (run2['passed_tests'] / run2['total_tests']) - 
                                 (run1['passed_tests'] / run1['total_tests']),
                'cost_diff': run2['total_cost'] - run1['total_cost'],
                'speed_diff': run2['avg_duration'] - run1['avg_duration']
            }
        }


class AgentEvaluator:
    """Evaluate agent performance on test suites"""
    
    def __init__(self, storage: Optional[EvaluationStorage] = None):
        self.storage = storage or EvaluationStorage()
    
    async def run_eval_suite(self, agent, test_cases: List[TestCase], 
                            run_id: Optional[str] = None,
                            prompt_version: Optional[int] = None) -> List[EvaluationResult]:
        """Run evaluation suite on an agent"""
        if run_id is None:
            run_id = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        results = []
        
        for test_case in test_cases:
            result = await self._evaluate_single(agent, test_case)
            results.append(result)
        
        # Save to database
        self.storage.save_run(
            run_id=run_id,
            agent_name=agent.config.name,
            prompt_version=prompt_version,
            results=results
        )
        
        return results
    
    async def _evaluate_single(self, agent, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case"""
        # Execute the task
        exec_result = await agent.execute(test_case.task)
        
        # Check if it passed
        passed = True
        failure_reason = None
        
        # Check expected tools
        if test_case.expected_tools:
            if set(exec_result.tools_invoked) != set(test_case.expected_tools):
                passed = False
                failure_reason = f"Expected tools {test_case.expected_tools}, got {exec_result.tools_invoked}"
        
        # Check expected steps
        if test_case.expected_steps:
            if exec_result.iterations != test_case.expected_steps:
                passed = False
                failure_reason = f"Expected {test_case.expected_steps} steps, got {exec_result.iterations}"
        
        # Check expected output
        if test_case.expected_output:
            if test_case.expected_output not in exec_result.output:
                passed = False
                failure_reason = f"Expected output not found"
        
        # Custom validator
        if test_case.validator and passed:
            try:
                if not test_case.validator(exec_result):
                    passed = False
                    failure_reason = "Custom validator failed"
            except Exception as e:
                passed = False
                failure_reason = f"Validator error: {str(e)}"
        
        return EvaluationResult(
            test_case_id=test_case.id,
            success=exec_result.success,
            agent_output=exec_result.output,
            tools_used=exec_result.tools_invoked,
            steps_taken=exec_result.iterations,
            duration_seconds=exec_result.duration_seconds,
            cost=exec_result.total_cost,
            passed=passed and exec_result.success,
            failure_reason=failure_reason
        )
