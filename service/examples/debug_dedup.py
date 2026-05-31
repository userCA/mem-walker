"""
详细调试脚本：追踪内存创建 ID 重复问题
"""

import requests
import json
import hashlib

BASE_URL = "http://localhost:8000/api/v1"

def test_memory_creation():
    test_cases = [
        ("记忆1", "这是第一条测试记忆"),
        ("记忆2", "这是第二条测试记忆，不同的内容"),
        ("记忆3", "这是第三条记忆，更多不同的内容"),
        ("记忆4", "第四条记忆，最后一条"),
    ]

    for i, (title, content) in enumerate(test_cases, 1):
        # 计算 content hash
        content_hash = hashlib.md5(content.strip().encode('utf-8')).hexdigest()
        print(f"\n{'='*60}")
        print(f"📝 第 {i} 次创建: [{title}]")
        print(f"   原始内容: {content}")
        print(f"   内容Hash: {content_hash}")

        payload = {
            "title": title,
            "content": content,
            "priority": "medium",
            "importance": 5,
            "layer": "episodic"
        }

        resp = requests.post(f"{BASE_URL}/memories/", json=payload, timeout=30)
        result = resp.json()

        if result.get("success"):
            data = result["data"]
            memory_id = data["id"]
            returned_content = data["content"]
            returned_hash = hashlib.md5(returned_content.strip().encode('utf-8')).hexdigest()
            print(f"   ✅ 成功")
            print(f"   返回ID: {memory_id}")
            print(f"   返回内容: {returned_content}")
            print(f"   返回Hash: {returned_hash}")
            print(f"   内容匹配: {'✅' if content == returned_content else '❌ 不同!'}")
        else:
            print(f"   ❌ 失败: {result.get('error')}")

    # 检查数据库中的实际记录
    print(f"\n{'='*60}")
    print("📊 数据库中的记录:")
    resp = requests.get(f"{BASE_URL}/memories/?page=1&page_size=100", timeout=30)
    result = resp.json()
    if result.get("success"):
        items = result["data"]["items"]
        print(f"   总数: {len(items)}")
        for item in items:
            content = item["content"]
            h = hashlib.md5(content.strip().encode('utf-8')).hexdigest()
            print(f"   - [{item['title']}] ID={item['id'][:8]}... Hash={h}")

if __name__ == "__main__":
    print("🚀 开始详细调试内存创建 ID 问题")
    test_memory_creation()
