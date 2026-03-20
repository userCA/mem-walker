# Mnemosyne - Holographic Cognitive Memory System

A modular, extensible memory system for AI applications, inspired by mem0 architecture.

## Features

- **Two-Layer Memory Architecture**: Episodic (vector) + Semantic (graph) memory
- **Modular Design**: Easy to swap embedding, vector store, graph store, and LLM providers
- **Extensible**: Strategy pattern for search algorithms, clear extension points
- **Production Ready**: Error handling, logging, dependency injection

## Quick Start

### Installation

```bash
cd service
poetry install
```

### Environment Setup

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `MILVUS_HOST`: Milvus server host (default: localhost)
- `MILVUS_PORT`: Milvus server port (default: 19530)
- `NEO4J_URI`: Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_PASSWORD`: Neo4j password

### Basic Usage

```python
from mnemosyne import Memory

# Initialize (loads config from environment)
memory = Memory()

# Add memories
memory_id = memory.add(
    "I work at Google in San Francisco",
    user_id="user_123"
)

# Batch add
ids = memory.add_batch(
    ["I love coffee", "I enjoy hiking"],
    user_id="user_123"
)

# Search memories
results = memory.search(
    "What are my interests?",
    user_id="user_123",
    limit=5
)

for result in results:
    print(f"Score: {result['score']:.3f} - {result['content']}")

# Get all memories
all_memories = memory.get_all(user_id="user_123")

# Delete a memory
memory.delete(memory_id)

# Clean up
memory.close()
```

### Custom Configuration

```python
from mnemosyne import Memory, GlobalSettings
from mnemosyne.embeddings import OpenAIEmbedding
from mnemosyne.vector_stores import MilvusVectorStore

# Custom settings
settings = GlobalSettings.from_env()
settings.enable_fact_extraction = True
settings.enable_graph_memory = True

# Or inject custom components
custom_embedding = OpenAIEmbedding()
custom_vector_store = MilvusVectorStore()

memory = Memory(
    embedding=custom_embedding,
    vector_store=custom_vector_store,
    config=settings
)
```

## Architecture

```
mnemosyne/
├── embeddings/         # Text → Vector (OpenAI, extensible to HuggingFace, etc.)
├── vector_stores/      # Vector storage (Milvus, extensible to Pinecone, etc.)
├── graphs/             # Knowledge graph (Neo4j, extensible to MemGraph, etc.)
├── llms/               # LLM for fact extraction (OpenAI, extensible to Anthropic, etc.)
├── reranker/           # Result reranking (BM25, extensible to Cohere, etc.)
├── memory/             # Core memory module
│   ├── main.py         # Memory facade class
│   ├── storage.py      # Writer/Reader/Lifecycle
│   └── search.py       # Search strategies
├── configs/            # Configuration management
└── utils/              # Logging and utilities
```

## Extension Points

### Adding a Custom Embedding Provider

```python
from mnemosyne.embeddings import EmbeddingBase

class HuggingFaceEmbedding(EmbeddingBase):
    def embed(self, text, memory_action=None):
        # Your implementation
        pass
    
    def embed_batch(self, texts, batch_size=32):
        # Your implementation
        pass
    
    @property
    def dimension(self):
        return 768

# Use it
memory = Memory(embedding=HuggingFaceEmbedding())
```

### Adding a Custom Vector Store

```python
from mnemosyne.vector_stores import VectorStoreBase

class PineconeVectorStore(VectorStoreBase):
    # Implement all abstract methods
    pass

memory = Memory(vector_store=PineconeVectorStore())
```

## Development

### Run Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black mnemosyne/

# Lint
poetry run ruff mnemosyne/

# Type check
poetry run mypy mnemosyne/
```

## Design Principles

- **Low Latency**: All optimizations ensure zero additional latency
- **SOLID Principles**: Clean architecture with clear responsibilities
- **First Principles**: Focused on core value (storage + semantic retrieval)
- **Extensibility**: Easy to swap any component

## License

Apache 2.0

## Credits

Inspired by [mem0](https://github.com/mem0ai/mem0) architecture.
