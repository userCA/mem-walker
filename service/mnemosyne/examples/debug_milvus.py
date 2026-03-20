
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pymilvus import connections, utility

def main():
    print("Debugging Milvus Connection...")
    try:
        connections.connect(host="localhost", port=19530)
        print("Successfully connected to Milvus!")
        print(f"Collections: {utility.list_collections()}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
