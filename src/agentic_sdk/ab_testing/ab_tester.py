"""A/B Testing framework for prompts"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import random
from uuid import uuid4

from .storage import ABTestStorage


@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    prompt_name: str
    version_a: int
    version_b: int
    split_percentage: int
    min_samples: int
    status: str
    started_at: str


@dataclass
class ABTestResult:
    """Results from an A/B test"""
    test_id: str
    version_a_stats: Dict[str, Any]
    version_b_stats: Dict[str, Any]
    recommendation: str
    confidence: float


class ABTester:
    """
    A/B testing framework for prompts.
    
    Automatically routes traffic between prompt versions
    and collects performance metrics.
    """
    
    def __init__(self, storage: Optional[ABTestStorage] = None):
        self.storage = storage or ABTestStorage()
    
    def start_test(self, prompt_name: str, version_a: int, version_b: int,
                   split_percentage: int = 50, min_samples: int = 100,
                   metadata: Dict[str, Any] = None) -> str:
        """
        Start a new A/B test.
        
        Args:
            prompt_name: Name of the prompt to test
            version_a: First version (baseline)
            version_b: Second version (candidate)
            split_percentage: % of traffic to version_a (0-100)
            min_samples: Minimum samples per version before analysis
            metadata: Additional test metadata
            
        Returns:
            test_id: Unique identifier for this test
        """
        # Check if test already running
        active = self.storage.get_active_test(prompt_name)
        if active:
            raise ValueError(f"Test already running for '{prompt_name}': {active['test_id']}")
        
        test_id = f"test-{uuid4()}"
        
        self.storage.create_test(
            test_id=test_id,
            prompt_name=prompt_name,
            version_a=version_a,
            version_b=version_b,
            split_percentage=split_percentage,
            min_samples=min_samples,
            metadata=metadata
        )
        
        return test_id
    
    def get_version_for_request(self, prompt_name: str) -> Optional[int]:
        """
        Determine which prompt version to use for this request.
        
        Returns:
            version number if A/B test is active, None otherwise
        """
        test = self.storage.get_active_test(prompt_name)
        if not test:
            return None
        
        # Random selection based on split percentage
        random_value = random.randint(1, 100)
        
        if random_value <= test['split_percentage']:
            return test['version_a']
        else:
            return test['version_b']
    
    def record_result(self, prompt_name: str, version: int, trace_id: str,
                     success: bool, duration: float, cost: float = 0.0):
        """
        Record the result of a request.
        
        Args:
            prompt_name: Name of the prompt
            version: Version that was used
            trace_id: Trace ID from observability
            success: Whether request succeeded
            duration: Duration in seconds
            cost: Cost in dollars
        """
        test = self.storage.get_active_test(prompt_name)
        if not test:
            return  # No active test
        
        self.storage.record_result(
            test_id=test['test_id'],
            version=version,
            trace_id=trace_id,
            success=success,
            duration=duration,
            cost=cost
        )
    
    def get_results(self, test_id: str) -> ABTestResult:
        """
        Get current results for a test.
        
        Returns aggregated statistics and recommendation.
        """
        # Get aggregated stats
        stats = self.storage.get_test_results(test_id)
        
        version_a_stats = stats.get('version_a', {})
        version_b_stats = stats.get('version_b', {})
        
        # Calculate recommendation
        recommendation, confidence = self._calculate_recommendation(
            version_a_stats, 
            version_b_stats
        )
        
        return ABTestResult(
            test_id=test_id,
            version_a_stats=version_a_stats,
            version_b_stats=version_b_stats,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _calculate_recommendation(self, stats_a: Dict, stats_b: Dict) -> tuple[str, float]:
        """
        Calculate which version is better.
        
        Returns:
            (recommendation, confidence)
        """
        if not stats_a or not stats_b:
            return "Insufficient data", 0.0
        
        # Check if we have enough samples
        if stats_a.get('total_requests', 0) < 10 or stats_b.get('total_requests', 0) < 10:
            return "Need more samples", 0.0
        
        # Compare success rates
        success_a = stats_a.get('success_rate', 0)
        success_b = stats_b.get('success_rate', 0)
        
        # Compare durations
        duration_a = stats_a.get('avg_duration', 0)
        duration_b = stats_b.get('avg_duration', 0)
        
        # Simple scoring (can be enhanced with statistical tests)
        score_a = success_a * 1000 - duration_a  # Higher success, lower duration = better
        score_b = success_b * 1000 - duration_b
        
        # Calculate confidence based on sample size
        total_samples = stats_a['total_requests'] + stats_b['total_requests']
        confidence = min(0.95, total_samples / 200)  # Max 95% confidence at 200 samples
        
        if score_b > score_a * 1.05:  # 5% improvement threshold
            improvement = ((score_b - score_a) / score_a) * 100
            return f"Version B is better ({improvement:.1f}% improvement)", confidence
        elif score_a > score_b * 1.05:
            improvement = ((score_a - score_b) / score_b) * 100
            return f"Version A is better ({improvement:.1f}% improvement)", confidence
        else:
            return "No significant difference", confidence
    
    def complete_test(self, test_id: str, promote_winner: bool = False) -> Optional[int]:
        """
        Complete a test and optionally promote the winner.
        
        Returns:
            winner_version if promote_winner=True, None otherwise
        """
        results = self.get_results(test_id)
        
        winner = None
        if promote_winner and results.confidence >= 0.8:
            # Determine winner from recommendation
            if "Version B is better" in results.recommendation:
                # Get version_b from test
                test = self.storage.conn.execute(
                    "SELECT version_b FROM ab_tests WHERE test_id = ?",
                    (test_id,)
                ).fetchone()
                winner = test['version_b'] if test else None
            elif "Version A is better" in results.recommendation:
                test = self.storage.conn.execute(
                    "SELECT version_a FROM ab_tests WHERE test_id = ?",
                    (test_id,)
                ).fetchone()
                winner = test['version_a'] if test else None
        
        self.storage.complete_test(test_id, winner)
        return winner
    
    def cancel_test(self, test_id: str):
        """Cancel a running test"""
        self.storage.cancel_test(test_id)
    
    def list_tests(self, status: Optional[str] = None) -> list:
        """List all tests"""
        return self.storage.list_tests(status)
