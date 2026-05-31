"""Benchmark script to measure search latency improvements.

Usage:
    python benchmark_search.py --queries 100 --verbose
"""

import argparse
import os
import sys
import time
from pathlib import Path
from statistics import mean, median
from typing import List
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mnemosyne import Memory
from mnemosyne.configs import GlobalSettings
from mnemosyne.embeddings import FastEmbedEmbedding
from mnemosyne.embeddings.configs import FastEmbedConfig
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

    # Check if local SLM should be used (office network optimization)
    enable_local_slm = os.getenv("ENABLE_LOCAL_SLM", "false").lower() == "true"
    local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "")

    if enable_local_slm and local_llm_base_url:
        # Use local LLM for faster inference in office network
        config.llm_config.api_key = os.getenv("LOCAL_SLM_API_KEY", "not-needed")
        config.llm_config.base_url = local_llm_base_url
        config.llm_config.model = os.getenv("LOCAL_LLM_MODEL", "Qwen3-30B-A3B")
        print(f"Using local LLM: {config.llm_config.base_url}")
    else:
        # Configure DeepSeek LLM from environment variables
        deepseek_api_key = os.getenv("ADAPTER_DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        deepseek_base_url = os.getenv("ADAPTER_DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        deepseek_model = os.getenv("ADAPTER_DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL") or "deepseek-chat"

        if deepseek_api_key:
            config.llm_config.api_key = deepseek_api_key
        if deepseek_base_url:
            config.llm_config.base_url = deepseek_base_url
        if deepseek_model:
            config.llm_config.model = deepseek_model

    # Use FastEmbed for local embedding (no API key needed)
    fastembed_config = FastEmbedConfig(
        model="BAAI/bge-small-en-v1.5",
        dimension=384
    )
    embedding = FastEmbedEmbedding(fastembed_config)
    config.embedding_config.dimension = 384
    config.vector_store_config.vector_size = 384

    # Drop existing collection to recreate with correct dimension
    print("Cleaning up existing collections...")
    try:
        from pymilvus import connections, utility
        connections.connect(host=config.vector_store_config.host, port=config.vector_store_config.port)
        if utility.has_collection("mnemosyne_memories"):
            utility.drop_collection("mnemosyne_memories")
            print("Dropped existing mnemosyne_memories collection.")
    except Exception as e:
        print(f"Cleanup warning (may be expected): {e}")

    memory = Memory(embedding=embedding, config=config)
    
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
