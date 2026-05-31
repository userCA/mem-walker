"""
调试脚本：单独测试内存创建 ID 问题
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_memory_creation():
    test_cases = [
        ("记忆1", "这是第一条测试记忆"),
        ("记忆2", "这是第二条测试记忆，不同的内容"),
        ("记忆3", "这是第三条记忆，更多不同的内容"),
        ("记忆4", "第四条记忆，最后一条"),
    ]

    created_ids = []

    for title, content in test_cases:
        payload = {
            "title": title,
            "content": content,
            "priority": "medium",
            "importance": 5,
            "layer": "episodic"
        }

        print(f"\n📝 创建: [{title}] content={content[:30]}...")
        resp = requests.post(f"{BASE_URL}/memories/", json=payload, timeout=30)
        result = resp.json()

        if result.get("success"):
            memory_id = result["data"]["id"]
            created_ids.append(memory_id)
            print(f"   ✅ 成功，ID: {memory_id}")
        else:
            print(f"   ❌ 失败: {result.get('error')}")

    # 检查所有 ID 是否唯一
    print(f"\n{'='*60}")
    print(f"创建了 {len(created_ids)} 个记忆")
    print(f"唯一 ID 数量: {len(set(created_ids))}")
    print(f"IDs: {created_ids}")

    # 列出所有记忆
    print(f"\n{'='*60}")
    print("列出所有记忆:")
    resp = requests.get(f"{BASE_URL}/memories/?page=1&page_size=100", timeout=30)
    result = resp.json()
    if result.get("success"):
        items = result["data"]["items"]
        print(f"总记忆数: {len(items)}")
        for item in items:
            print(f"  - ID={item['id']}, title={item['title']}, content={item['content'][:40]}...")

if __name__ == "__main__":
    print("🚀 开始调试内存创建 ID 问题")
    print(f"目标: {BASE_URL}")
    test_memory_creation()
