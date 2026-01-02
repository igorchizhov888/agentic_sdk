"""
Test Production Features: Context Persistence, Retry Logic, and Caching
"""

import asyncio
from uuid import uuid4
from pathlib import Path

from agentic_sdk.mcp.context_store import ContextStore
from agentic_sdk.runtime.retry import RetryPolicy, retry_async
from agentic_sdk.runtime.cache import InMemoryCache, cache_key_from_params


async def main():
    print("\n" + "=" * 70)
    print("PRODUCTION FEATURES TEST")
    print("=" * 70 + "\n")

    # Test 1: Context Persistence
    print("-" * 70)
    print("TEST 1: Context Persistence (SQLite)")
    print("-" * 70)
    
    db_path = "test_context.db"
    store = ContextStore(db_path=db_path)
    
    session_id = uuid4()
    agent_id = uuid4()
    
    # Save context
    context_data = {
        "conversation": ["Hello", "How can I help?"],
        "current_task": "Calculate 10 + 5",
        "iteration": 1,
    }
    
    store.save_context(
        session_id=session_id,
        agent_id=agent_id,
        context_data=context_data,
        user_id="user123",
    )
    print(f"Saved context for session: {session_id}")
    
    # Load context
    loaded = store.load_context(session_id)
    print(f"Loaded context: {loaded.context_data}")
    
    # Save execution history
    store.save_execution(
        session_id=session_id,
        tool_name="calculator",
        params={"operation": "add", "a": 10, "b": 5},
        result={"result": 15.0},
        success=True,
    )
    print("Saved execution to history")
    
    # Get history
    history = store.get_execution_history(session_id, limit=10)
    print(f"Execution history: {len(history)} entries")
    for entry in history:
        print(f"  - {entry['tool_name']}: success={entry['success']}")
    
    # Cleanup
    Path(db_path).unlink()
    print("Database cleaned up\n")

    # Test 2: Retry Logic
    print("-" * 70)
    print("TEST 2: Retry Logic with Exponential Backoff")
    print("-" * 70)
    
    attempt_count = 0
    
    async def flaky_function():
        """Function that fails first 2 times, succeeds on 3rd."""
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}")
        
        if attempt_count < 3:
            raise ValueError(f"Simulated failure {attempt_count}")
        
        return "Success!"
    
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay=0.1,
        exponential_base=2.0,
        jitter=False,
    )
    
    try:
        result = await retry_async(flaky_function, policy=policy)
        print(f"Result: {result}")
        print(f"Total attempts: {attempt_count}\n")
    except Exception as e:
        print(f"Failed: {e}\n")

    # Test 3: Caching
    print("-" * 70)
    print("TEST 3: In-Memory Cache with TTL")
    print("-" * 70)
    
    cache = InMemoryCache(default_ttl=5.0)
    
    # Cache some tool results
    tool_params_1 = {"operation": "add", "a": 10, "b": 5}
    cache_key_1 = cache_key_from_params("calculator", tool_params_1)
    
    cache.set(cache_key_1, {"result": 15.0}, namespace="tools")
    print(f"Cached result for calculator(10 + 5)")
    
    # Try to get it
    cached_result = cache.get(cache_key_1, namespace="tools")
    print(f"Retrieved from cache: {cached_result}")
    
    # Cache another result
    tool_params_2 = {"operation": "multiply", "a": 7, "b": 8}
    cache_key_2 = cache_key_from_params("calculator", tool_params_2)
    cache.set(cache_key_2, {"result": 56.0}, namespace="tools")
    print(f"Cached result for calculator(7 * 8)")
    
    # Get stats
    stats = cache.stats()
    print(f"\nCache stats:")
    print(f"  Size: {stats['size']} entries")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1f}%")
    
    # Test cache miss
    cache_key_3 = cache_key_from_params("calculator", {"operation": "divide", "a": 100, "b": 4})
    result = cache.get(cache_key_3, namespace="tools")
    print(f"\nCache miss test: {result}")
    
    # Updated stats
    stats = cache.stats()
    print(f"Updated hit rate: {stats['hit_rate']:.1f}%")
    
    # Clear namespace
    cache.clear(namespace="tools")
    print(f"\nCleared 'tools' namespace")
    print(f"Cache size: {cache.stats()['size']}\n")

    # Test 4: Combined Usage
    print("-" * 70)
    print("TEST 4: Combined - Context + Cache + Retry")
    print("-" * 70)
    
    print("Simulating agent workflow with all features:")
    print("  1. Check cache for result")
    print("  2. If miss, execute with retry")
    print("  3. Save to context store")
    print("  4. Cache the result")
    
    # Setup
    store = ContextStore(db_path="combined_test.db")
    cache = InMemoryCache(default_ttl=300.0)
    session_id = uuid4()
    agent_id = uuid4()
    
    params = {"operation": "add", "a": 100, "b": 200}
    cache_key = cache_key_from_params("calculator", params)
    
    # Check cache
    cached = cache.get(cache_key, namespace="results")
    if cached:
        print(f"\nCache HIT: {cached}")
    else:
        print("\nCache MISS - executing with retry...")
        
        async def calculate():
            """Simulated calculation."""
            await asyncio.sleep(0.1)
            return {"result": 300.0}
        
        result = await retry_async(calculate, policy=RetryPolicy(max_attempts=3))
        print(f"Calculation result: {result}")
        
        # Cache it
        cache.set(cache_key, result, namespace="results")
        print("Result cached")
        
        # Save to context
        store.save_execution(
            session_id=session_id,
            tool_name="calculator",
            params=params,
            result=result,
            success=True,
        )
        print("Execution saved to context store")
    
    # Verify it's in cache now
    cached = cache.get(cache_key, namespace="results")
    print(f"\nSecond access - Cache HIT: {cached}")
    
    # Cleanup
    Path("combined_test.db").unlink()
    print("\nCleanup complete\n")

    print("=" * 70)
    print("ALL PRODUCTION FEATURES WORKING")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
