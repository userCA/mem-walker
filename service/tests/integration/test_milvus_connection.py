import unittest
import random
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection,
    utility
)

class TestMilvusConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collection_name = "test_collection"
        try:
            connections.connect(
                alias="default",
                host="localhost",
                port="19530"
            )
            print("Successfully connected to Milvus")
        except Exception as e:
            raise unittest.SkipTest(f"Failed to connect to Milvus: {e}")

    @classmethod
    def tearDownClass(cls):
        try:
            if utility.has_collection(cls.collection_name):
                utility.drop_collection(cls.collection_name)
                print(f"Dropped collection: {cls.collection_name}")
            connections.disconnect("default")
            print("Disconnected from Milvus")
        except Exception as e:
            print(f"Error during teardown: {e}")

    def test_milvus_workflow(self):
        # 1. Create Collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128)
        ]
        schema = CollectionSchema(fields, "Test Collection")
        collection = Collection(
            name=self.collection_name, 
            schema=schema, 
            using="default", 
            shards_num=2
        )
        print(f"Created collection: {self.collection_name}")
        self.assertIsNotNone(collection)

        # 2. Insert Data
        vectors = [[random.random() for _ in range(128)] for _ in range(100)]
        mr = collection.insert([vectors])
        print(f"Inserted {len(mr.primary_keys)} records")
        collection.flush()
        self.assertEqual(len(mr.primary_keys), 100)

        # 3. Create Index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(
            field_name="vector", 
            index_params=index_params,
            index_name="vector_index"
        )
        print("Created index")

        # 4. Search
        collection.load()
        query_vector = [[random.random() for _ in range(128)]]
        results = collection.search(
            data=query_vector,
            anns_field="vector",
            param={"nprobe": 10},
            limit=5,
            output_fields=["id"],
            consistency_level="Strong"
        )
        print(f"Found {len(results[0])} results")
        self.assertTrue(len(results[0]) > 0)

if __name__ == "__main__":
    unittest.main()
