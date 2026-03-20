import os
import sys
import time
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from service.mnemosyne.profile_kb import UserProfileKBManager, MemoryType, Importance
from service.mnemosyne.embeddings.fastembed import FastEmbedEmbedding
from service.mnemosyne.embeddings.configs import FastEmbedConfig
from service.mnemosyne.configs import GlobalSettings

def main():
    config = GlobalSettings.from_env()
    print("\n[0] Cleaning up existing collection...")
    try:
        from pymilvus import connections, utility
        connections.connect(host=config.vector_store_config.host, port=config.vector_store_config.port)
        utility.drop_collection("user_profile_knowledge_base")
        print("Dropped existing collection.")
    except Exception as e:
        print(f"Cleanup warning: {e}")

    # 1. Initialize
    print("\n[1] Initializing Manager...")
    # NOTE: Ensure Milvus is running. Using FastEmbed as requested.
    
    try:
        # Create FastEmbed config manually since it's not in GlobalSettings yet
        fastembed_config = FastEmbedConfig(
            model="BAAI/bge-small-en-v1.5",
            dimension=384
        )
        embedding = FastEmbedEmbedding(fastembed_config)
        
        # NOTE: ProfileKBManager collection creation depends on dimension. 
        # FastEmbed default is 384, but ProfileKBManager might reuse config.embedding_config.dimension (likely 1536 from OpenAI default).
        # We need to ensure ProfileKBManager uses the correct dimension from the actual embedding model.
        # Checking manager.py... dim = self.config.embedding_config.dimension or 768. 
        # We should probably update the GlobalSettings object to reflect the new dimension to match FastEmbed.
        config.embedding_config.dimension = 384 
        config.vector_store_config.vector_size = 384
        
        kb = UserProfileKBManager(embedding, config)
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 2. Add Data
    user_id = "u_verified_001"
    agent_a = "agent_assistant"
    agent_b = "agent_rpg_master"
    
    print(f"\n[2] Adding memories for User {user_id}...")
    
    memories = [
        # Agent A memories
        (agent_a, "User likes Python programming.", MemoryType.PREFERENCE, Importance.CORE),
        (agent_a, "User asked about sort algorithms.", MemoryType.DIALOGUE, Importance.NORMAL),
        
        # Agent B memories
        (agent_b, "User plays as a Level 5 Mage.", MemoryType.KNOWLEDGE, Importance.CORE),
        (agent_b, "User joined the Fire Faction.", MemoryType.BEHAVIOR, Importance.NORMAL),
    ]
    
    for agent, content, mtype, imp in memories:
        mid = kb.add_memory(
            user_id=user_id,
            agent_id=agent,
            content=content,
            memory_type=mtype,
            importance=imp
        )
        print(f"  -> Added [{agent}]: {content[:30]}... (ID: {mid})")
        
    time.sleep(1) # Allow slight index sync time (Milvus consistent_level="Bounded" usually)
    
    # 3. Query - Agent A specific
    print(f"\n[3] Querying Agent A context ('liking')...")
    results_a = kb.query_memory(
        user_id=user_id,
        query_text="What does user like?",
        agent_id=agent_a,
        top_k=3
    )
    for res in results_a:
        print(f"  FOUND: [{res['agent_id']}] {res['content']} (Score: {res['score']})")
        
    # 4. Query - Agent B specific
    print(f"\n[4] Querying Agent B context ('game status')...")
    results_b = kb.query_memory(
        user_id=user_id,
        query_text="What is my game character?",
        agent_id=agent_b,
        top_k=3
    )
    for res in results_b:
        print(f"  FOUND: [{res['agent_id']}] {res['content']} (Score: {res['score']})")
        
    # 5. Query - Global (Cross-Agent)
    print(f"\n[5] Querying Global Profile (No Agent Filter)...")
    results_all = kb.query_memory(
        user_id=user_id,
        query_text="Tell me everything about the user",
        agent_id=None,
        top_k=5
    )
    for res in results_all:
        print(f"  FOUND: [{res['agent_id']}] {res['content']} (Score: {res['score']})")

    # Clean up (optional, keeping data for manual check if needed)
    # kb.close()
    print("\n=== Demo Completed ===")

if __name__ == "__main__":
    main()
