"""
Quick Start Example for Mnemosyne Memory System
"""

from mnemosyne import Memory


def main():
    """Basic usage example."""
    
    # Initialize memory system
    # Will load configuration from environment variables
    print("Initializing Mnemosyne Memory System...")
    memory = Memory()
    
    try:
        # Add a single memory
        print("\n1. Adding single memory...")
        memory_id = memory.add(
            messages="I work at Google as a software engineer in San Francisco",
            user_id="user_123"
        )
        print(f"   Added memory: {memory_id}")
        
        # Add multiple memories in batch (faster)
        print("\n2. Adding batch memories...")
        messages = [
            "I love coffee, especially espresso",
            "I enjoy hiking on weekends",
            "My favorite programming language is Python"
        ]
        memory_ids = memory.add_batch(messages, user_id="user_123")
        print(f"   Added {len(memory_ids)} memories")
        
        # Search for memories
        print("\n3. Searching memories...")
        query = "What are my interests and hobbies?"
        results = memory.search(query, user_id="user_123", limit=5)
        
        print(f"   Found {len(results)} results for: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"   {i}. [Score: {result['score']:.3f}] {result['content']}")
        
        # Get a specific memory
        print("\n4. Getting specific memory...")
        specific = memory.get(memory_id)
        if specific:
            print(f"   Memory {memory_id}: {specific['content']}")
        
        # Get all memories for user
        print("\n5. Getting all memories for user...")
        all_memories = memory.get_all(user_id="user_123")
        print(f"   Total memories: {len(all_memories)}")
        
        # Update a memory
        print("\n6. Updating memory...")
        memory.update(
            memory_id=memory_id,
            data="I work at Google as a senior software engineer in Mountain View"
        )
        print(f"   Updated memory: {memory_id}")
        
        # Search again to see updated content
        results = memory.search("where do I work", user_id="user_123", limit=1)
        if results:
            print(f"   Updated content: {results[0]['content']}")
        
        # Delete a memory
        print("\n7. Deleting memory...")
        success = memory.delete(memory_id)
        print(f"   Deleted: {success}")
        
        print("\n✅ Quick start completed successfully!")
        
    finally:
        # Clean up connections
        memory.close()
        print("\n🔒 Memory system closed")


if __name__ == "__main__":
    main()
