"""Benchmark with graph/infer disabled."""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from mnemosyne import Memory
from mnemosyne.configs import GlobalSettings
from mnemosyne.embeddings import FastEmbedEmbedding
from mnemosyne.embeddings.configs import FastEmbedConfig

print("=== Benchmark: DeepSeek + 禁用 graph/infer ===\n")

config = GlobalSettings.from_env()

# 禁用 graph memory (跳过 LLM 实体提取)
config.enable_graph_memory = False
config.enable_reranking = False  # 禁用 reranking

# FastEmbed embedding
fastembed_config = FastEmbedConfig(model="BAAI/bge-small-en-v1.5", dimension=384)
embedding = FastEmbedEmbedding(fastembed_config)
config.embedding_config.dimension = 384
config.vector_store_config.vector_size = 384

# 使用 Milvus
from pymilvus import connections, utility

try:
    connections.connect(host=config.vector_store_config.host, port=config.vector_store_config.port)
    if utility.has_collection("mnemosyne_memories"):
        utility.drop_collection("mnemosyne_memories")
        print("Dropped existing collection")
except Exception as e:
    print(f"Cleanup: {e}")

memory = Memory(embedding=embedding, config=config)

# 添加样本
sample_memories = [
    "Machine learning is a subset of AI that learns from data",
    "Python is a popular programming language for data science",
    "Neural networks are inspired by biological neurons",
    "Paris is the capital of France",
    "Elon Musk is the CEO of Tesla and SpaceX",
]
print("Adding memories...")
memory.add_batch(sample_memories, user_id="benchmark_user")

# 测试查询
queries = [
    "What is machine learning?",
    "Tell me about Python programming",
    "How does neural network work?",
] * 5

print(f"Running {len(queries)} queries with graph disabled...\n")

latencies = []
for q in queries:
    start = time.time()
    results = memory.search(q, user_id="benchmark_user", limit=10)
    elapsed = (time.time() - start) * 1000
    latencies.append(elapsed)

latencies.sort()
p50 = latencies[len(latencies) // 2]
p95 = latencies[int(len(latencies) * 0.95)]
p99 = latencies[int(len(latencies) * 0.99)]

print("=" * 50)
print("Results (DeepSeek + 禁用 graph/infer)")
print("=" * 50)
print(f"Mean latency:  {sum(latencies)/len(latencies):.2f} ms")
print(f"P50 latency:   {p50:.2f} ms")
print(f"P95 latency:   {p95:.2f} ms")
print(f"P99 latency:   {p99:.2f} ms")
print(f"Min latency:   {min(latencies):.2f} ms")
print(f"Max latency:   {max(latencies):.2f} ms")

if p95 < 300:
    print("Excellent! P95 < 300ms")
elif p95 < 500:
    print("Good! P95 < 500ms")
elif p95 < 1000:
    print("Acceptable. P95 < 1s")
else:
    print("Poor. P95 > 1s")

memory.close()
