from mnemosyne.adapter.mapper.memory_mapper import MemoryMapper


def test_mapper_uses_created_at_when_updated_at_missing():
    mapper = MemoryMapper()
    mapped = mapper.from_mnemosyne(
        {
            "id": "m1",
            "content": "hello",
            "created_at": 1700000000,
            "metadata": {}
        }
    )

    assert mapped.updatedAt == mapped.createdAt
