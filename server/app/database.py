from datetime import datetime
import uuid
from typing import Optional
from .models import (
    Memory, MemoryStatus, MemoryPriority, MemoryTag, MemoryAccess,
    ChatSession, ChatMessage, ChatRole, ChatConfig,
    BackendConnection, BackendProvider, BackendStatus, BackendHealth,
    CollectionStats, StorageMetrics
)


# In-memory data stores (replace with actual database in production)
class Database:
    def __init__(self):
        self.memories: dict[str, Memory] = {}
        self.chat_sessions: dict[str, ChatSession] = {}
        self.backends: dict[BackendProvider, BackendConnection] = {}
        self.chat_config = ChatConfig()
        self._init_sample_data()

    def _init_sample_data(self):
        """Initialize with sample data for testing"""
        # Sample memories
        for i in range(5):
            memory = Memory(
                id=str(uuid.uuid4()),
                title=f"记忆 {i + 1}: {['项目会议', '技术方案', '用户反馈', '产品规划', '代码审查'][i]}",
                content=f"这是关于{['项目会议讨论了Q2季度目标', '采用微服务架构设计方案', '用户反映应用启动较慢', '计划在下月发布新功能', '代码需要优化性能问题'][i]}的详细记忆内容。",
                status=MemoryStatus.ACTIVE if i < 3 else MemoryStatus.ARCHIVED,
                priority=MemoryPriority.MEDIUM if i < 4 else MemoryPriority.HIGH,
                importance=(i % 5) + 1,
                tags=[
                    MemoryTag(id="1", name="工作", color="#f59e0b"),
                    MemoryTag(id="2", name="重要", color="#ef4444") if i % 2 == 0 else MemoryTag(id="3", name="日常", color="#10b981"),
                ],
                layer=["semantic", "episodic", "procedural", "working"][i % 4],
                access=MemoryAccess(
                    lastAccessedAt=datetime.now(),
                    accessCount=i * 10 + 5,
                    lastModifiedAt=datetime.now()
                )
            )
            self.memories[memory.id] = memory

        # Sample chat sessions
        for i in range(3):
            session = ChatSession(
                id=str(uuid.uuid4()),
                title=f"对话 {i + 1}: {['讨论项目计划', '代码问题解答', '架构设计咨询'][i]}",
                messages=[
                    ChatMessage(
                        id=str(uuid.uuid4()),
                        role=ChatRole.USER,
                        content="你好，我想讨论一下项目计划",
                        createdAt=datetime.now()
                    ),
                    ChatMessage(
                        id=str(uuid.uuid4()),
                        role=ChatRole.ASSISTANT,
                        content="好的，让我先查一下相关的记忆...",
                        createdAt=datetime.now()
                    )
                ],
                memoryCount=3,
                createdAt=datetime.now(),
                updatedAt=datetime.now()
            )
            self.chat_sessions[session.id] = session

        # Sample backend
        milvus_backend = BackendConnection(
            provider=BackendProvider.MILVUS,
            status=BackendStatus.CONNECTED,
            host="localhost",
            port=19530,
            database="memory_db",
            health=BackendHealth(
                status=BackendStatus.CONNECTED,
                latency=5.2,
                lastChecked=datetime.now()
            ),
            metrics=StorageMetrics(
                totalMemory=10 * 1024 * 1024 * 1024,
                usedMemory=2 * 1024 * 1024 * 1024,
                vectorCount=15234,
                diskUsage=50 * 1024 * 1024 * 1024
            ),
            collections=[
                CollectionStats(
                    name="semantic_layer",
                    memoryCount=5000,
                    vectorDimension=768,
                    indexType="HNSW"
                ),
                CollectionStats(
                    name="episodic_layer",
                    memoryCount=3000,
                    vectorDimension=768,
                    indexType="IVF"
                )
            ]
        )
        self.backends[BackendProvider.MILVUS] = milvus_backend


# Singleton database instance
db = Database()
