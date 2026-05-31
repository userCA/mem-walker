"""
实际场景 API 测试文件

用于测试本地启动的 mnemosyne 后端服务。
启动服务: poetry run uvicorn mnemosyne.adapter.main:app --reload --port 8000

Usage:
    poetry run python examples/test_api_scenarios.py

或者直接运行:
    python examples/test_api_scenarios.py
"""

import requests
import time
import json
from typing import Optional

# 配置
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30


class MnemosyneAPITester:
    """Mnemosyne API 测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.created_memory_ids: list[str] = []

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()

    def print_result(self, title: str, data: dict):
        """格式化打印结果"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
        print(json.dumps(data, ensure_ascii=False, indent=2))

    # ========== Memory API ==========

    def test_create_memory(self, title: str = "测试记忆", content: str = "这是一条测试记忆内容") -> str:
        """创建记忆"""
        payload = {
            "title": title,
            "content": content,
            "priority": "medium",
            "importance": 5,
            "layer": "episodic"
        }
        result = self._request("POST", "/memories/", json=payload)
        if result.get("success") and result.get("data", {}).get("id"):
            memory_id = result["data"]["id"]
            self.created_memory_ids.append(memory_id)
            print(f"\n✅ 创建记忆成功: [{title}] ID={memory_id}")
            return memory_id
        raise Exception(f"创建记忆失败: {result}")

    def test_get_memory(self, memory_id: str) -> dict:
        """获取单个记忆"""
        return self._request("GET", f"/memories/{memory_id}")

    def test_list_memories(self, page: int = 1, page_size: int = 20) -> dict:
        """列出记忆（分页）"""
        return self._request("GET", f"/memories/?page={page}&page_size={page_size}")

    def test_search_memories(self, query: str, limit: int = 10) -> dict:
        """搜索记忆"""
        return self._request("GET", f"/memories/search?q={requests.utils.quote(query)}&limit={limit}")

    def test_update_memory(self, memory_id: str, content: str) -> dict:
        """更新记忆"""
        payload = {"content": content}
        return self._request("PATCH", f"/memories/{memory_id}", json=payload)

    def test_delete_memory(self, memory_id: str) -> dict:
        """删除记忆"""
        return self._request("DELETE", f"/memories/{memory_id}")

    def test_get_stats(self) -> dict:
        """获取记忆统计"""
        return self._request("GET", "/memories/stats")

    def test_get_tags(self) -> dict:
        """获取所有标签"""
        return self._request("GET", "/memories/tags")

    def test_get_layers(self) -> dict:
        """获取记忆层级"""
        return self._request("GET", "/memories/layers")

    # ========== Chat API ==========

    def test_create_session(self, title: str = "API测试会话") -> str:
        """创建聊天会话"""
        payload = {"title": title}
        result = self._request("POST", "/chat/sessions", json=payload)
        if result.get("success"):
            self.session_id = result["data"]["id"]
            print(f"\n✅ 创建会话成功: {self.session_id}")
            return self.session_id
        raise Exception(f"创建会话失败: {result}")

    def test_list_sessions(self, page: int = 1, page_size: int = 20) -> dict:
        """列出聊天会话"""
        return self._request("GET", f"/chat/sessions?page={page}&page_size={page_size}")

    def test_get_session(self, session_id: str) -> dict:
        """获取会话详情"""
        return self._request("GET", f"/chat/sessions/{session_id}")

    def test_send_message(self, session_id: str, content: str) -> dict:
        """发送消息"""
        payload = {"content": content}
        return self._request("POST", f"/chat/sessions/{session_id}/messages", json=payload)

    def test_get_chat_config(self) -> dict:
        """获取聊天配置"""
        return self._request("GET", "/chat/config")

    def test_get_chat_presets(self) -> dict:
        """获取聊天预设"""
        return self._request("GET", "/chat/presets")

    # ========== Backend API ==========

    def test_list_backends(self) -> dict:
        """列出后端"""
        return self._request("GET", "/backends/")

    def test_get_backend(self, provider: str = "sqlite") -> dict:
        """获取后端信息"""
        return self._request("GET", f"/backends/{provider}")

    def test_get_backend_metrics(self, provider: str = "sqlite") -> dict:
        """获取后端指标"""
        return self._request("GET", f"/backends/{provider}/metrics")

    def test_get_backend_collections(self, provider: str = "sqlite") -> dict:
        """获取后端集合"""
        return self._request("GET", f"/backends/{provider}/collections")

    def test_create_backend_collection(self, provider: str = "sqlite", name: str = "test") -> dict:
        """创建后端集合"""
        return self._request("POST", f"/backends/{provider}/collections?name={name}")

    def test_connect_backend(self, config: dict) -> dict:
        """连接后端"""
        return self._request("POST", "/backends/connect", json=config)

    def test_disconnect_backend(self, provider: str = "sqlite") -> dict:
        """断开后端"""
        return self._request("POST", f"/backends/{provider}/disconnect")

    # ========== 清理 ==========

    def cleanup_memories(self):
        """清理创建的测试记忆"""
        print(f"\n🧹 清理 {len(self.created_memory_ids)} 条测试记忆...")
        for memory_id in self.created_memory_ids:
            try:
                self.test_delete_memory(memory_id)
            except Exception as e:
                print(f"   删除 {memory_id} 失败: {e}")
        self.created_memory_ids.clear()


def run_all_tests():
    """运行所有测试场景"""
    print("\n🚀 Mnemosyne API 实际场景测试")
    print(f"📡 目标地址: {BASE_URL}")

    tester = MnemosyneAPITester()

    try:
        # ========== 1. Memory CRUD 场景 ==========
        print("\n\n" + "🔷"*20)
        print("  场景1: 记忆 CRUD 操作")
        print("🔷"*20)

        # 1.1 创建记忆
        memory_id = tester.test_create_memory(
            title="用户工作信息",
            content="我在 Anthropic 工作，是一名 AI 工程师"
        )

        # 1.2 获取单个记忆
        result = tester.test_get_memory(memory_id)
        tester.print_result("获取记忆详情", result)

        # 1.3 创建更多记忆（用于后续搜索）
        tester.test_create_memory("咖啡爱好", "我喜欢喝浓缩咖啡，每天两杯")
        tester.test_create_memory("编程语言", "我最擅长的编程语言是 Python 和 TypeScript")
        tester.test_create_memory("周末活动", "周末我喜欢徒步旅行和摄影")

        # 1.4 列出所有记忆
        result = tester.test_list_memories(page=1, page_size=10)
        tester.print_result("列出记忆（分页）", result)

        # 1.5 搜索记忆
        result = tester.test_search_memories("工作", limit=5)
        tester.print_result("搜索记忆: '工作'", result)

        result = tester.test_search_memories("coffee", limit=5)
        tester.print_result("搜索记忆: 'coffee'", result)

        # 1.6 更新记忆
        result = tester.test_update_memory(memory_id, "我在 Anthropic 工作，是一名高级 AI 工程师")
        tester.print_result("更新记忆", result)

        # 1.7 获取统计
        result = tester.test_get_stats()
        tester.print_result("记忆统计", result)

        # 1.8 获取标签和层级
        result = tester.test_get_tags()
        tester.print_result("所有标签", result)

        result = tester.test_get_layers()
        tester.print_result("记忆层级", result)

        # ========== 2. Chat 会话场景 ==========
        print("\n\n" + "🔷"*20)
        print("  场景2: 聊天会话功能")
        print("🔷"*20)

        # 2.1 创建会话
        session_id = tester.test_create_session("API集成测试会话")

        # 2.2 获取会话列表
        result = tester.test_list_sessions()
        tester.print_result("会话列表", result)

        # 2.3 获取单个会话
        result = tester.test_get_session(session_id)
        tester.print_result("会话详情", result)

        # 2.4 发送消息（如果配置了 LLM）
        try:
            result = tester.test_send_message(session_id, "你好！请介绍一下你自己。")
            tester.print_result("发送消息", result)
        except Exception as e:
            print(f"\n⚠️ 发送消息失败（可能是 LLM 未配置）: {e}")

        # 2.5 获取聊天配置
        result = tester.test_get_chat_config()
        tester.print_result("聊天配置", result)

        # 2.6 获取聊天预设
        result = tester.test_get_chat_presets()
        tester.print_result("聊天预设", result)

        # ========== 3. Backend 后端管理场景 ==========
        print("\n\n" + "🔷"*20)
        print("  场景3: 后端管理功能")
        print("🔷"*20)

        # 3.1 列出后端
        result = tester.test_list_backends()
        tester.print_result("后端列表", result)

        # 3.2 获取 SQLite 后端信息
        result = tester.test_get_backend("sqlite")
        tester.print_result("SQLite 后端信息", result)

        # 3.3 获取后端指标
        result = tester.test_get_backend_metrics("sqlite")
        tester.print_result("SQLite 后端指标", result)

        # 3.4 获取后端集合
        result = tester.test_get_backend_collections("sqlite")
        tester.print_result("SQLite 集合列表", result)

        # ========== 4. 复杂搜索场景 ==========
        print("\n\n" + "🔷"*20)
        print("  场景4: 复杂搜索场景")
        print("🔷"*20)

        # 添加一些特定场景的记忆
        tester.test_create_memory("项目经验", "我做过 React 前端开发和 FastAPI 后端开发")
        tester.test_create_memory("教育背景", "我在斯坦福大学获得了计算机科学硕士学位")
        tester.test_create_memory("语言能力", "我可以说中文、英语和日语")

        # 语义搜索
        search_queries = [
            "编程开发",
            "education school",
            "外国语言",
        ]

        for query in search_queries:
            result = tester.test_search_memories(query, limit=5)
            print(f"\n🔍 搜索: '{query}'")
            if result.get("success"):
                items = result.get("data", [])
                print(f"   找到 {len(items)} 条结果")
                for item in items[:3]:
                    print(f"   - [{item.get('score', 0):.3f}] {item.get('content', '')[:60]}...")

        print("\n\n" + "🎉"*20)
        print("  所有测试场景执行完成!")
        print("🎉"*20)

    except requests.exceptions.ConnectionError:
        print(f"\n❌ 错误: 无法连接到 {BASE_URL}")
        print("   请确保后端服务已启动:")
        print("   cd service && poetry run uvicorn mnemosyne.adapter.main:app --reload --port 8000")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e}")
        print(f"   响应内容: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        tester.cleanup_memories()


def run_quick_test():
    """快速测试 - 只测试最基本的功能"""
    tester = MnemosyneAPITester()

    try:
        print("\n🚀 快速测试: 健康检查 + 创建记忆")

        # 1. 列出记忆（健康检查）
        result = tester.test_list_memories()
        print(f"✅ API 连接正常，当前记忆数: {result.get('data', {}).get('total', 0)}")

        # 2. 创建一条记忆
        memory_id = tester.test_create_memory("快速测试", "这是一条快速测试记忆")
        print(f"✅ 创建记忆成功: {memory_id}")

        # 3. 搜索记忆
        result = tester.test_search_memories("快速测试")
        print(f"✅ 搜索成功，找到 {len(result.get('data', []))} 条结果")

        # 4. 删除记忆
        tester.test_delete_memory(memory_id)
        print(f"✅ 删除记忆成功")

        print("\n✅ 快速测试全部通过!")

    except Exception as e:
        print(f"\n❌ 快速测试失败: {e}")
    finally:
        tester.cleanup_memories()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_test()
    else:
        run_all_tests()
