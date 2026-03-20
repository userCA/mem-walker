import os
import sys
import time
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from service.mnemosyne.memory.main import Memory
from service.mnemosyne.configs import GlobalSettings
from service.mnemosyne.embeddings.fastembed import FastEmbedEmbedding
from service.mnemosyne.embeddings.configs import FastEmbedConfig
from service.mnemosyne.memory.profiles import UserProfileKBManager, MemoryType

def main():
    print("=== Architecture Verification Demo ===")
    
    # 0. Cleanup (Optional, just to be safe)
    config = GlobalSettings.from_env()
    
    # Setup FastEmbed (384 dim)
    fastembed_config = FastEmbedConfig(model="BAAI/bge-small-en-v1.5", dimension=384)
    # Update config to match
    config.embedding_config.dimension = 384
    config.vector_store_config.vector_size = 384
    
    # Drop collections to start fresh (Clean state)
    try:
        from pymilvus import connections, utility
        connections.connect(host=config.vector_store_config.host, port=config.vector_store_config.port)
        if utility.has_collection("mnemosyne_memories"):
            utility.drop_collection("mnemosyne_memories")
        if utility.has_collection("user_profile_knowledge_base"):
            utility.drop_collection("user_profile_knowledge_base")
        print("[0] Cleaned up collections.")
    except Exception as e:
        print(f"[Warn] Cleanup failed: {e}")

    # 1. Initialize Memory System
    print("\n[1] Initializing Memory System...")
    embedding = FastEmbedEmbedding(fastembed_config)
    
    # We pass explicit config and embedding
    memory = Memory(embedding=embedding, config=config)
    
    user_id = "u_arch_test"
    
    # 2. Test Default Context (Legacy API)
    print("\n[2] Testing Default Context (Generic Memory)...")
    try:
        # Add
        mid = memory.add("I am testing the new architecture.", user_id=user_id, infer=False) # Disable infer to skip LLM cost/error
        print(f"  -> Added generic memory: {mid}")
        
        # Search
        results = memory.search("testing architecture", user_id=user_id)
        if results:
            print(f"  -> Found generic memory: {results[0]['content'][:30]}... (Score: {results[0]['score']})")
        else:
            print("  -> [ERROR] Generic memory not found!")
    except Exception as e:
        print(f"  -> [ERROR] Default Context test failed: {e}")
        import traceback
        traceback.print_exc()

    # 3. Test Profile Context (New API)
    print("\n[3] Testing Profile Context...")
    try:
        profile_ctx = memory.context("profile")
        
        # Add
        mid = profile_ctx.add(
            "User prefers scalable architectures.", 
            user_id=user_id, 
            agent_id="architect_agent",
            memory_type=MemoryType.PREFERENCE
        )
        print(f"  -> Added profile memory: {mid}")
        
        time.sleep(1) # Indexing wait
        
        # Search
        results = profile_ctx.search(
            "scalable architecture", 
            user_id=user_id,
            agent_id="architect_agent"
        )
        
        if results:
            print(f"  -> Found profile memory: {results[0]['content']} (Score: {results[0]['score']})")
        else:
            print("  -> [ERROR] Profile memory not found!")
            
    except Exception as e:
        print(f"  -> [ERROR] Profile Context test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Verification Completed ===")

if __name__ == "__main__":
    main()
