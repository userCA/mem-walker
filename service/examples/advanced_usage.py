"""
Advanced Usage Example - Custom Components and Search Strategies
"""

from mnemosyne import Memory, GlobalSettings
from mnemosyne.embeddings import OpenAIEmbedding
from mnemosyne.llms import OpenAILLM
from mnemosyne.memory import HybridSearchStrategy, VectorSearchStrategy
from mnemosyne.reranker import BM25Reranker
from mnemosyne.vector_stores import MilvusVectorStore


def custom_configuration_example():
    """Example with custom configuration."""
    print("=== Custom Configuration Example ===\n")
    
    # Load settings from environment
    settings = GlobalSettings.from_env()
    
    # Customize settings
    settings.enable_fact_extraction = True
    settings.enable_graph_memory = True
    settings.enable_reranking = True
    settings.log_level = "DEBUG"
    
    # Create memory with custom settings
    memory = Memory(config=settings)
    
    # Use the memory system
    memory_id = memory.add(
        "I prefer dark roast coffee beans",
        user_id="user_456"
    )
    
    results = memory.search("coffee preferences", user_id="user_456")
    print(f"Found {len(results)} results\n")
    
    memory.close()


def dependency_injection_example():
    """Example with custom component injection."""
    print("=== Dependency Injection Example ===\n")
    
    # Create custom components
    custom_embedding = OpenAIEmbedding()
    custom_llm = OpenAILLM()
    
    # Inject custom components
    memory = Memory(
        embedding=custom_embedding,
        llm=custom_llm
    )
    
    # Now the memory system uses your custom components
    memory_id = memory.add(
        "I'm learning machine learning",
        user_id="user_789"
    )
    
    print(f"Added memory with custom components: {memory_id}\n")
    
    memory.close()


def search_without_graph_example():
    """Example disabling graph memory for faster searches."""
    print("=== Search Without Graph Example ===\n")
    
    settings = GlobalSettings.from_env()
    settings.enable_graph_memory = False  # Faster but less contextual
    
    memory = Memory(config=settings)
    
    # Add some memories
    memory.add_batch([
        "I graduated from Stanford",
        "I studied computer science",
        "My thesis was on neural networks"
    ], user_id="user_abc")
    
    # Search will only use vector similarity (faster)
    results = memory.search(
        "education background",
        user_id="user_abc",
        limit=3
    )
    
    for result in results:
        print(f"- {result['content']}")
    
    print()
    memory.close()


def batch_operations_example():
    """Example with batch operations for better performance."""
    print("=== Batch Operations Example ===\n")
    
    memory = Memory()
    
    # Prepare many memories
    memories = [
        f"Memory entry number {i}"
        for i in range(100)
    ]
    
    # Batch add is much faster than individual adds
    import time
    start = time.time()
    memory_ids = memory.add_batch(memories, user_id="user_batch")
    elapsed = time.time() - start
    
    print(f"Added {len(memory_ids)} memories in {elapsed:.2f} seconds")
    print(f"Average: {elapsed/len(memory_ids)*1000:.1f} ms per memory\n")
    
    memory.close()


def main():
    """Run all examples."""
    try:
        custom_configuration_example()
        dependency_injection_example()
        search_without_graph_example()
        batch_operations_example()
        
        print("✅ All advanced examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
