"""Benchmark script to measure search latency improvements.

Usage:
    python benchmark_search.py --queries 100 --verbose
"""

import argparse
import time
from statistics import mean, median
from typing import List

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mnemosyne import Memory
from mnemosyne.configs import GlobalSettings
from mnemosyne.utils import setup_logging


def measure_latency(memory: Memory, queries: List[str], user_id: str = "benchmark_user") -> dict:
    """
    Measure search latency for a list of queries.
    
    Returns:
        Dict with latency statistics
    """
    latencies = []
    
    for query in queries:
        start = time.time()
        results = memory.search(query, user_id=user_id, limit=10)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        latencies.append(elapsed)
    
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    
    return {
        "mean": mean(latencies),
        "median": median(latencies),
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "min": min(latencies),
        "max": max(latencies),
        "count": len(latencies)
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Mnemosyne search latency")
    parser.add_argument("--queries", type=int, default=100, help="Number of test queries")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level="DEBUG" if args.verbose else "INFO")
    
    # Test queries
    test_queries = [
        "What is machine learning?",
        "Tell me about Python programming",
        "How does neural network work?",
        "What is the capital of France?",
        "Explain quantum computing",
        "Who is Elon Musk?",
        "What did Steve Jobs say about innovation?",
        "How to learn deep learning?",
        "What is the meaning of life?",
        "Explain general relativity",
    ] * (args.queries // 10)
    
    print("=" * 60)
    print("Mnemosyne Search Latency Benchmark")
    print("=" * 60)
    print(f"Number of queries: {len(test_queries)}")
    print(f"Graph memory: enabled")
    print(f"Reranking: enabled")
    print()
    
    # Initialize Memory
    print("Initializing Memory system...")
    config = GlobalSettings.from_env()
    memory = Memory(config=config)
    
    # Add some sample memories
    sample_memories = [
        "Machine learning is a subset of AI that learns from data",
        "Python is a popular programming language for data science",
        "Neural networks are inspired by biological neurons",
        "Paris is the capital of France",
        "Elon Musk is the CEO of Tesla and SpaceX",
    ]
    
    print("Adding sample memories...")
    user_id = "benchmark_user"
    memory.add_batch(sample_memories, user_id=user_id)
    print()
    
    # Run benchmark
    print("Running benchmark...")
    stats = measure_latency(memory, test_queries, user_id=user_id)
    
    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Mean latency:    {stats['mean']:.2f} ms")
    print(f"Median latency:  {stats['median']:.2f} ms")
    print(f"P50 latency:     {stats['p50']:.2f} ms")
    print(f"P95 latency:     {stats['p95']:.2f} ms")
    print(f"P99 latency:     {stats['p99']:.2f} ms")
    print(f"Min latency:     {stats['min']:.2f} ms")
    print(f"Max latency:     {stats['max']:.2f} ms")
    print("=" * 60)
    
    # Performance assessment
    if stats['p95'] < 300:
        print("✅ Excellent! P95 latency < 300ms (Phase 1 target achieved)")
    elif stats['p95'] < 500:
        print("✅ Good! P95 latency < 500ms (Phase 1 target achieved)")
    elif stats['p95'] < 1000:
        print("⚠️  Acceptable. P95 latency < 1s (consider Phase 2 optimizations)")
    else:
        print("❌ Poor. P95 latency > 1s (check config and model setup)")
    
    # Cleanup
    memory.close()


if __name__ == "__main__":
    main()
