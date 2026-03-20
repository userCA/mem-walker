# Phase 1 Low-Latency Optimization - Setup Guide

## Overview
This guide helps you set up and test the Phase 1 low-latency optimizations for Mnemosyne.

**Optimizations implemented:**
- ✅ Local Small Language Model (Qwen2.5-0.5B) for fast entity extraction in search
- ✅ LRU cache for embedding vectors
- ✅ Optimized vector search parameters (1.2x limit instead of 2x)

**Expected improvements:**
- P95 latency: 1.5s → < 500ms (66% reduction)
- P50 latency: 1.0s → < 300ms (70% reduction)

---

## Prerequisites

### 1. Install llama-cpp-python

```bash
# For CPU-only systems
pip install llama-cpp-python

# For GPU-accelerated systems (recommended)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### 2. Download the Qwen2.5-0.5B model

Download the quantized GGUF model file (~500MB):

```bash
# Create models directory
mkdir -p models

# Download from Hugging Face (using huggingface-cli)
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-GGUF \
  qwen2.5-0.5b-instruct-q4_k_m.gguf \
  --local-dir models

# Or manually download from:
# https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
```

### 3. Update configuration

The default configuration in `configs/settings.py` expects the model at:
```
./models/qwen2.5-0.5b-instruct-q4.gguf
```

To use a different model or path, update `LocalSLMConfig` in `service/mnemosyne/configs/settings.py`.

---

## Verification

### Option 1: Run the benchmark script

```bash
cd service/mnemosyne
python examples/benchmark_search.py --queries 100 --verbose
```

**Expected output:**
```
Mnemosyne Search Latency Benchmark
==================================================
Results
==================================================
Mean latency:    250.32 ms
Median latency:  235.10 ms
P50 latency:     235.10 ms
P95 latency:     420.50 ms  ✅ < 500ms target
P99 latency:     485.20 ms
==================================================
✅ Good! P95 latency < 500ms (Phase 1 target achieved)
```

### Option 2: Manual testing

```python
from mnemosyne import Memory

# Initialize with optimizations
memory = Memory()

# Add some memories
memory.add_batch([
    "I love Python programming",
    "Machine learning is fascinating",
    "Paris is the capital of France"
], user_id="test_user")

# Search (should be fast!)
import time
start = time.time()
results = memory.search("What do I like?", user_id="test_user")
elapsed = (time.time() - start) * 1000

print(f"Search latency: {elapsed:.2f}ms")
print(f"Results: {results}")
```

---

## Troubleshooting

### Error: "llama-cpp-python not installed"
```bash
pip install llama-cpp-python
```

### Error: "Failed to load local SLM"
- Check that the model file exists at the configured path
- Verify the model file is not corrupted (should be ~500MB)
- Check logs for specific error messages

### Fallback behavior
If LocalSLM fails to load, the system automatically falls back to OpenAI LLM with a warning:
```
WARNING: LocalSLM initialization failed, falling back to OpenAI LLM
```

This ensures the system continues to work, but without the latency improvements.

---

## Configuration Options

### Use CPU instead of GPU

Edit `service/mnemosyne/configs/settings.py`:

```python
@dataclass
class LocalSLMConfig:
    model_path: str = "./models/qwen2.5-0.5b-instruct-q4.gguf"
    n_gpu_layers: int = 0  # Change from -1 to 0
    n_ctx: int = 2048
```

### Adjust cache size

In `service/mnemosyne/memory/main.py`:

```python
self.embedding = CachedEmbedding(base_embedding, cache_size=2048)  # Increase from 1024
```

### Disable graph search temporarily

```python
config = GlobalSettings.from_env()
config.enable_graph_memory = False  # Disable for faster search
memory = Memory(config=config)
```

---

## Next Steps

After validating Phase 1:
1. Measure performance improvements in your production environment
2. Monitor cache hit rates: `memory.embedding.get_cache_info()`
3. Consider Phase 2 optimizations (async/await, parallelization)

For questions or issues, check the main implementation plan at:
`/implementation_plan.md`
