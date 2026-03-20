import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to import mnemosyne
# Assuming this script is in service/examples/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import time
from mnemosyne.memory.main import Memory
from mnemosyne.embeddings.fastembed import FastEmbedEmbedding
from mnemosyne.embeddings.configs import FastEmbedConfig
from mnemosyne.vector_stores.milvus import MilvusVectorStore
from mnemosyne.vector_stores.configs import MilvusConfig
from mnemosyne.llms.openai import OpenAILLM
from mnemosyne.llms.configs import OpenAILLMConfig
from mnemosyne.llms.simple_local_llm import SimpleLocalLLM
from mnemosyne.reranker.bm25 import BM25Reranker
from mnemosyne.reranker.configs import RerankerConfig
from mnemosyne.graphs.base import GraphStoreBase
import atexit
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dummy Graph Store
class DummyGraphStore(GraphStoreBase):
    def add_node(self, entity: str, properties: Dict[str, Any], user_id: str, embedding: Optional[List[float]] = None) -> str:
        # logger.debug(f"DummyGraphStore: Adding node {entity}")
        return "dummy_id"
    
    def add_relationship(self, source: str, target: str, relation_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        # logger.debug(f"DummyGraphStore: Adding relationship {source} -> {target}")
        return True
    
    def bfs_expand(self, entities: List[str], depth: int = 2, user_id: Optional[str] = None) -> List[str]:
        return []
    
    def get_node_centrality(self, entity: str) -> float:
        return 0.0
    
    def get_neighbors(self, entity: str, relation_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return []
        
    def delete_node(self, entity: str) -> bool:
        return True
    
    def query(self, cypher_query: str, params: Optional[Dict] = None) -> List[Dict]:
        return []

# Load .env from service root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    logger.info(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
else:
    logger.warning(f".env file not found at {env_path}")

def verify_memory():
    logger.info("Starting memory system verification (Connecting to Docker Milvus at localhost:19530)...")
    
    # Track latencies
    latencies = {}

    # 1. Configure Components
    start_time = time.time()
    
    # Embedding: FastEmbed
    logger.info("Initializing FastEmbed...")
    embed_start = time.time()
    embed_config = FastEmbedConfig(
        model="BAAI/bge-small-en-v1.5",
        dimension=384
    )
    embedding = FastEmbedEmbedding(embed_config)
    latencies['init_embedding'] = time.time() - embed_start
    
    # Vector Store: Milvus
    # IMPORTANT: Match vector_size with embedding dimension
    logger.info("Initializing Milvus...")
    milvus_start = time.time()
    vector_store_config = MilvusConfig(
        collection_name="test_mnemosyne_docker_verification",
        vector_size=384,
        host=os.getenv("MILVUS_HOST", "localhost"),
        port=int(os.getenv("MILVUS_PORT", 19530)),
        index_type="FLAT", # HNSW is usually preferred for production but FLAT is fine for small tests
        index_params={} 
    )
    try:
        vector_store = MilvusVectorStore(vector_store_config)
        latencies['init_milvus'] = time.time() - milvus_start
    except Exception as e:
        logger.error(f"Failed to initialize Milvus: {e}")
        logger.error("Please ensure Docker Milvus is running and accessible.")
        return

    # LLM: SimpleLocalLLM (Qwen)
    logger.info("Initializing SimpleLocalLLM (Qwen)...")
    llm_start = time.time()
    
    # We will use SimpleLocalLLM as the main LLM for Memory
    llm = SimpleLocalLLM()
    
    latencies['init_llm'] = time.time() - llm_start
    
    # Reranker: BM25
    logger.info("Initializing BM25 Reranker...")
    rerank_start = time.time()
    reranker_config = RerankerConfig()
    reranker = BM25Reranker(reranker_config)
    latencies['init_reranker'] = time.time() - rerank_start
    
    # 2. Initialize Memory
    logger.info("Initializing Memory System...")
    
    memory = Memory(
        embedding=embedding,
        vector_store=vector_store,
        graph_store=DummyGraphStore(), # Use dummy graph
        llm=llm,
        reranker=reranker
    )
    latencies['total_init'] = time.time() - start_time
    
    # 3. Verify Capabilities & Latency Analysis
    
    user_id = "test_user_verification"
    content = "The quick brown fox jumps over the lazy dog. Mnemosyne is a memory system."
    query = "what is mnemosyne?"

    logger.info("-" * 30)
    logger.info("PERFORMANCE ANALYSIS")
    logger.info("-" * 30)

    # Test Case 1: Add with LLM Inference (Default)
    logger.info("Test 1: Add Memory (infer=True)...")
    try:
        start = time.time()
        memory.add(content, user_id=user_id, infer=True)
        duration = time.time() - start
        latencies['add_infer_true'] = duration
        logger.info(f"  -> Duration: {duration:.4f}s")
    except Exception as e:
        logger.error(f"Failed Test 1: {e}")

    # Test Case 2: Add without LLM Inference (Fast Path)
    logger.info("Test 2: Add Memory (infer=False)...")
    try:
        start = time.time()
        # Profile internal steps of add(infer=False)
        # 1. Embedding
        t0 = time.time()
        emb = memory.embedding.embed(content)
        t_embed = time.time() - t0
        logger.info(f"  -> Embedding Only: {t_embed:.4f}s")
        
        # 2. Vector Store Insert
        t0 = time.time()
        # We need to mock the payload as memory.add does
        import uuid
        mid = str(uuid.uuid4())
        payload = {
            "user_id": user_id,
            "content": content,
            "metadata": {},
            "original_message": content
        }
        memory.vector_store.insert(vectors=[emb], payloads=[payload], ids=[mid])
        t_insert = time.time() - t0
        logger.info(f"  -> Milvus Insert Only: {t_insert:.4f}s")
        
        # Now run the actual method to confirm
        memory.add(content, user_id=user_id, infer=False)
        duration = time.time() - start
        latencies['add_infer_false'] = duration
        logger.info(f"  -> Total Duration: {duration:.4f}s")
    except Exception as e:
        logger.error(f"Failed Test 2: {e}")

    # Test Case 3: Search Memory (use_graph=True)...
    logger.info("Test 3: Search Memory (use_graph=True)...")
    try:
        start = time.time()
        
        # Profile breakdown
        logger.info("  [Breakdown Analysis]")
        
        # 1. Query Embedding
        t0 = time.time()
        q_vec = memory.embedding.embed(query)
        t_embed = time.time() - t0
        logger.info(f"  -> 1. Query Embedding: {t_embed:.4f}s")
        
        # 2. Vector Search
        t0 = time.time()
        memory.vector_store.search(query_vector=q_vec, limit=10, filters={"user_id": user_id})
        t_vec = time.time() - t0
        logger.info(f"  -> 2. Vector Search:   {t_vec:.4f}s")
        
        # 3. Entity Extraction (LLM)
        t0 = time.time()
        memory.llm.extract_entities(query)
        t_extract = time.time() - t0
        logger.info(f"  -> 3. LLM Entity Extr: {t_extract:.4f}s")
        
        # 4. Graph Expansion
        t0 = time.time()
        # Mock expansion as we used dummy store
        memory.graph_store.bfs_expand(["mnemosyne"], depth=2, user_id=user_id)
        t_graph = time.time() - t0
        logger.info(f"  -> 4. Graph Expansion: {t_graph:.4f}s")

        # Full Search
        logger.info("  [Full Operation]")
        t0 = time.time()
        memory.search(query, user_id=user_id)
        duration = time.time() - t0
        latencies['search_default'] = duration
        logger.info(f"  -> Total Search Time:  {duration:.4f}s")
        
    except Exception as e:
        logger.error(f"Failed Test 3: {e}")
        import traceback
        traceback.print_exc()
        
    # Hack to test search without graph: verify if we can pass it or need to modify main.py
    # Since I cannot pass use_graph to memory.search, I will access _reader directly for this test
    # Test Case 4: Search Memory (use_graph=False)...
    logger.info("Test 4: Search Memory (use_graph=False)...")
    try:
        start = time.time()
        memory._reader.search(query, user_id=user_id, use_graph=False)
        duration = time.time() - start
        latencies['search_no_graph'] = duration
        logger.info(f"  -> Duration: {duration:.4f}s")
    except Exception as e:
        logger.error(f"Failed Test 4: {e}")

    logger.info("-" * 30)
    logger.info("LATENCY SUMMARY")
    logger.info("-" * 30)
    for stage, duration in latencies.items():
        logger.info(f"{stage:<20}: {duration:.4f}s")
    logger.info("-" * 30)

if __name__ == "__main__":
    verify_memory()
