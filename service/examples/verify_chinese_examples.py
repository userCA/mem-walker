import os
import sys
import logging
from dotenv import load_dotenv
import time
import json
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from mnemosyne.memory.main import Memory
from mnemosyne.embeddings.fastembed import FastEmbedEmbedding
from mnemosyne.embeddings.configs import FastEmbedConfig
from mnemosyne.vector_stores.milvus import MilvusVectorStore
from mnemosyne.vector_stores.configs import MilvusConfig
from mnemosyne.llms.simple_local_llm import SimpleLocalLLM
from mnemosyne.reranker.bm25 import BM25Reranker
from mnemosyne.reranker.configs import RerankerConfig
from mnemosyne.graphs.base import GraphStoreBase

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s') # Simplified format for readability
logger = logging.getLogger(__name__)

# Dummy Graph Store (Same as before)
class DummyGraphStore(GraphStoreBase):
    def add_node(self, entity: str, properties: Dict[str, Any], user_id: str, embedding: Optional[List[float]] = None) -> str:
        return "dummy_id"
    def add_relationship(self, source: str, target: str, relation_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
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

def print_separator(title: str):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step: str, content: Any):
    print(f"\n[STEP] {step}")
    if isinstance(content, (dict, list)):
        print(json.dumps(content, ensure_ascii=False, indent=2))
    else:
        print(f"{content}")

def run_chinese_verification():
    # Load env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)

    print_separator("初始化系统 (System Initialization)")
    
    # 1. Init Components
    # Embedding
    embed_config = FastEmbedConfig(model="BAAI/bge-small-en-v1.5", dimension=384)
    embedding = FastEmbedEmbedding(embed_config)
    
    # Vector Store
    # Use a fresh collection to avoid dirty data from previous runs
    collection_name = "test_mnemosyne_chinese_examples_v3"
    vector_store_config = MilvusConfig(
        collection_name=collection_name,
        vector_size=384,
        host=os.getenv("MILVUS_HOST", "localhost"),
        port=int(os.getenv("MILVUS_PORT", 19530)),
        index_type="FLAT",
        index_params={} 
    )
    try:
        vector_store = MilvusVectorStore(vector_store_config)
    except Exception as e:
        logger.error(f"Milvus init failed: {e}")
        return

    # LLM
    llm = SimpleLocalLLM()
    
    # Reranker
    reranker_config = RerankerConfig()
    reranker = BM25Reranker(reranker_config)
    
    # Memory
    memory = Memory(
        embedding=embedding,
        vector_store=vector_store,
        graph_store=DummyGraphStore(),
        llm=llm,
        reranker=reranker
    )
    print("系统初始化完成。准备开始场景验证。")

    # Define Scenarios
    user_id = "user_chinese_demo_001"
    
    # ==========================================
    # 场景一：个人画像与偏好 (Personal Profile)
    # ==========================================
    print_separator("场景一：个人画像与偏好 (Personal Profile)")
    
    inputs = [
        "你好，我叫林峰，是一名在上海工作的人工智能算法工程师。",
        "平时工作压力比较大，所以我周末喜欢去爬山或者徒步，不喜欢宅在家里。",
        "饮食方面，我非常喜欢吃辣，尤其是川菜，但是对海鲜过敏。"
    ]
    
    print(f"模拟用户输入 (User Inputs):")
    for text in inputs:
        print(f"  -> {text}")
        memory.add(text, user_id=user_id, infer=True) # infer=True to extract entities (though graph is dummy, LLM is called)
    
    print("Waiting for persistence...")
    time.sleep(2) # Wait for Milvus flush
    
    query = "林峰有哪些个人喜好和饮食禁忌？"
    print_step("用户提问 (User Query)", query)
    
    # Search
    results = memory.search(query, user_id=user_id, limit=10)
    
    # Format Results
    retrieved_contexts = []
    for res in results:
        # Extract meaningful parts
        context = {
            "content": res.get("content"),
            "score": res.get("score"),
            "timestamp": res.get("timestamp") # Assuming timestamp exists or metadata
        }
        retrieved_contexts.append(context)
        
    print_step("系统检索到的记忆片段 (Retrieved Memory Chunks)", retrieved_contexts)
    
    # Generate Answer
    context_str = "\n".join([r['content'] for r in retrieved_contexts])
    prompt = f"基于以下记忆回答问题：\n{context_str}\n\n问题：{query}"
    answer = llm.generate(prompt)
    print_step("LLM生成的最终回答 (Final Answer)", answer)


    # ==========================================
    # 场景二：项目知识管理 (Project Knowledge)
    # ==========================================
    print_separator("场景二：项目知识管理 (Project Knowledge)")
    
    inputs_2 = [
        "我们正在开发一个代号为'深蓝 (DeepBlue)'的记忆增强模块。",
        "深蓝模块的核心目标是解决LLM的长期记忆遗忘问题。",
        "目前的开发进度：完成了向量数据库Milvus的对接，正在进行图数据库Neo4j的适配工作。",
        "下周一上午10点需要和产品团队过一下深蓝模块的API设计方案。"
    ]
    
    print(f"模拟用户输入 (User Inputs):")
    for text in inputs_2:
        print(f"  -> {text}")
        memory.add(text, user_id=user_id, infer=False) # infer=False for faster insert
        
    print("Waiting for persistence...")
    time.sleep(2)

    query_2 = "深蓝项目的目前进度怎么样？下周有什么安排？"
    print_step("用户提问 (User Query)", query_2)
    
    results_2 = memory.search(query_2, user_id=user_id, limit=10)
    
    retrieved_contexts_2 = [{"content": r.get("content"), "score": r.get("score")} for r in results_2]
    print_step("系统检索到的记忆片段 (Retrieved Memory Chunks)", retrieved_contexts_2)
    
    context_str_2 = "\n".join([r['content'] for r in retrieved_contexts_2])
    prompt_2 = f"基于以下记忆回答问题：\n{context_str_2}\n\n问题：{query_2}"
    answer_2 = llm.generate(prompt_2)
    print_step("LLM生成的最终回答 (Final Answer)", answer_2)


    # ==========================================
    # 场景三：信息修正与冲突 (Information Update)
    # ==========================================
    print_separator("场景三：信息修正 (Information Update)")
    
    # Previous info: "下周一上午10点需要和产品团队过一下深蓝模块的API设计方案。"
    update_input = "紧急通知：下周一关于深蓝模块API的会议改到下午2点进行了，地点在305会议室。"
    
    print(f"模拟用户输入 (User Update):")
    print(f"  -> {update_input}")
    memory.add(update_input, user_id=user_id, infer=False)
    
    query_3 = "下周一的API会议是什么时候？"
    print_step("用户提问 (User Query)", query_3)
    
    # We expect the system to retrieve both, or the latest one to be more relevant if time decay/ranking works well.
    # But currently it's vector similarity + BM25. Both should appear.
    results_3 = memory.search(query_3, user_id=user_id, limit=10)
    
    retrieved_contexts_3 = [{"content": r.get("content"), "score": r.get("score")} for r in results_3]
    print_step("系统检索到的记忆片段 (Retrieved Memory Chunks)", retrieved_contexts_3)
    
    context_str_3 = "\n".join([r['content'] for r in retrieved_contexts_3])
    # Prompt explicitly asks to resolve conflict based on latest info if possible, 
    # but standard RAG relies on LLM to figure it out or metadata. 
    # Let's see how SimpleLocalLLM handles it.
    prompt_3 = f"基于以下记忆回答问题（注意信息可能存在更新，请综合判断）：\n{context_str_3}\n\n问题：{query_3}"
    answer_3 = llm.generate(prompt_3)
    print_step("LLM生成的最终回答 (Final Answer)", answer_3)

if __name__ == "__main__":
    run_chinese_verification()
