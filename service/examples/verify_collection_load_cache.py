"""Verify collection.load() caching optimization in MilvusVectorStore.

This script:
1. Patches collection.load() to count invocations
2. Runs multiple search operations
3. Verifies load() is called only ONCE (at init), not on every search

Run with: cd service && python3 examples/verify_collection_load_cache.py
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# Setup path
service_path = str(Path(__file__).parent.parent)
sys.path.insert(0, service_path)

# Import vector_stores directly without triggering full mnemosyne package
vs_spec = importlib.util.spec_from_file_location(
    "vector_stores",
    os.path.join(service_path, "mnemosyne", "vector_stores", "__init__.py")
)
vector_stores = importlib.util.module_from_spec(vs_spec)

# We need to manually set up dependencies first
# Patch the imports that cause chain issues
sys.modules['mnemosyne'] = MagicMock()
sys.modules['mnemosyne.vector_stores'] = vector_stores

# Now load milvus directly
milvus_spec = importlib.util.spec_from_file_location(
    "milvus",
    os.path.join(service_path, "mnemosyne", "vector_stores", "milvus.py")
)
milvus_module = importlib.util.module_from_spec(milvus_spec)
sys.modules['mnemosyne.vector_stores.milvus'] = milvus_module

# Load the module
milvus_spec.loader.exec_module(milvus_module)

MilvusVectorStore = milvus_module.MilvusVectorStore
MilvusConfig = milvus_module.MilvusConfig

# Track load calls
load_call_count = 0
original_load = None


def counting_load(self):
    """Patched collection.load() that counts calls."""
    global load_call_count
    load_call_count += 1
    print(f"  [LOAD #{load_call_count}] collection.load() called")
    return original_load(self)


def main():
    global original_load, load_call_count

    print("=" * 60)
    print("Verifying collection.load() Caching Optimization")
    print("=" * 60)

    # Check Milvus connectivity
    try:
        from pymilvus import connections, utility
        connections.connect(host="localhost", port="19530")
        # Clean up any existing test collection
        if utility.has_collection("cache_test"):
            utility.drop_collection("cache_test")
            print("Cleaned up existing test collection")
    except Exception as e:
        print(f"Cannot connect to Milvus: {e}")
        print("Make sure Milvus is running on localhost:19530")
        return

    # Patch collection.load() BEFORE creating the vector store
    from pymilvus import Collection
    original_load = Collection.load
    Collection.load = counting_load

    try:
        # Create vector store
        print("\n1. Creating MilvusVectorStore (should call load once at init)...")
        config = MilvusConfig(
            collection_name="cache_test",
            vector_size=384,
            host="localhost",
            port="19530"
        )
        load_call_count = 0

        store = MilvusVectorStore(config)

        init_load_count = load_call_count
        print(f"   Init phase: collection.load() called {init_load_count} time(s)")

        # Insert some test vectors
        print("\n2. Inserting test vectors...")
        vectors = [[0.1] * 384 for _ in range(5)]
        payloads = [
            {"user_id": "test_user", "content": f"Test content {i}", "metadata": {}}
            for i in range(5)
        ]
        ids = store.insert(vectors, payloads)
        insert_load_count = load_call_count - init_load_count
        print(f"   Insert phase: collection.load() called {insert_load_count} time(s)")

        # Run multiple searches (this is where the optimization matters)
        print("\n3. Running 10 search queries (should NOT call load() again)...")
        load_call_count = 0  # Reset counter

        for i in range(10):
            results = store.search(
                query_vector=[0.1] * 384,
                limit=3,
                filters={"user_id": "test_user"}
            )

        search_load_count = load_call_count
        print(f"   Search phase: collection.load() called {search_load_count} time(s)")

        # Run BM25 searches
        print("\n4. Running 5 BM25 search queries (should NOT call load() again)...")
        load_call_count = 0  # Reset counter

        for i in range(5):
            results = store.bm25_search(
                query="test content",
                limit=3,
                filters={"user_id": "test_user"}
            )

        bm25_load_count = load_call_count
        print(f"   BM25 search phase: collection.load() called {bm25_load_count} time(s)")

        # Verify results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        total_load_calls = init_load_count + insert_load_count + search_load_count + bm25_load_count

        if search_load_count == 0 and bm25_load_count == 0:
            print("✅ OPTIMIZATION WORKING:")
            print(f"   - Init: {init_load_count} load() call(s)")
            print(f"   - 10 searches: {search_load_count} load() call(s)")
            print(f"   - 5 BM25 searches: {bm25_load_count} load() call(s)")
            print(f"   - Total load() calls: {total_load_calls}")
        else:
            print("❌ OPTIMIZATION NOT WORKING:")
            print(f"   - Search calls triggered {search_load_count} load() calls")
            print(f"   - BM25 calls triggered {bm25_load_count} load() calls")

        # Cleanup
        print("\n5. Cleaning up...")
        Collection.load = original_load  # Restore original
        store.delete_collection()
        connections.disconnect("default")
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        # Restore original
        try:
            Collection.load = original_load
        except:
            pass


if __name__ == "__main__":
    main()
