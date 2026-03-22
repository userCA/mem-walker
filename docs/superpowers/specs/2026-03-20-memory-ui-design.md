# Mnemosyne 前端交互界面设计规范

> "温暖极简主义 + 单焦点模式 + 多后端可扩展"

**版本**: v1.0
**日期**: 2026-03-20
**项目**: Mnemosyne 记忆系统 Web UI

---

## 1. 设计哲学

### 1.1 视觉风格
- **温暖极简 (Warm Minimal)**
- 浅色背景 + 柔和暖色调 (Notion/Linear 风格)
- 米白/浅灰背景 (#faf9f7, #fafafa)
- 琥珀/橙色点缀 (#f59e0b)
- 大量留白 + 圆角卡片

### 1.2 交互模式
- **单焦点设计** — 每个模式只做一件事，但做到极致
- **模式切换** — Tab-based 导航，而非堆砌所有功能

### 1.3 色彩系统
| 用途 | 色值 |
|------|------|
| 背景 | #faf9f7 |
| 卡片 | #ffffff |
| 主文字 | #1a1a1a |
| 次文字 | #64748b, #8b8680 |
| 边框 | #e2ddd8, #f0eeeb |
| 高亮 | #fef3c7 (琥珀) |
| 成功 | #22c55e (绿) |
| 分类-工作 | #ecfdf5 |
| 分类-个人 | #fce7f3 |
| 分类-项目 | #e0f2fe |
| 分类-学习 | #f0fdf4 |

---

## 2. 整体架构

### 2.1 页面结构
```
┌─────────────────────────────────────────────────────────┐
│  Header: Logo · Mode Tabs · Import/Export · Status    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    [Active Mode Content]                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 三个主模式
1. **🗂️ 记忆模式** — 记忆的 CRUD 管理
2. **💬 对话模式** — 基于记忆的对话体验
3. **🏪 后端模式** — 存储后端管理

---

## 3. 模式详细设计

### 3.1 记忆模式 (Memory Management)

**布局**: 三栏布局

| 左侧边栏 (220px) | 中间列表 (320px) | 右侧详情 (flex) |
|------------------|------------------|-----------------|
| 搜索框 | 记忆卡片列表 | 记忆内容 |
| 记忆概览统计 | (选中高亮) | 元数据网格 |
| 分类列表 | | 标签管理 |
| 快捷筛选 | | 关联图谱 |
| 新建记忆按钮 | | 相关记忆 |

**左侧边栏组件**:
- `SearchBar` — 搜索框，支持 ⌘K 快捷键
- `StatsOverview` — 2x2 网格：总记忆、情景层、语义层、关联数
- `CategoryList` — 可选分类：全部/工作/个人/项目/学习，带颜色标识和数量
- `QuickFilters` — 快捷筛选：最近7天/高相关度/多关联
- `NewMemoryButton` — 新建记忆按钮

**中间列表组件**:
- `MemoryCard` — 单条记忆卡片，显示：分类标签、时间、相似度、内容预览
- `SelectedState` — 选中状态：橙色边框 + 阴影
- `BatchActionsBar` — 批量操作栏：全选/导出/删除

**右侧详情组件**:
- `MemoryContent` — 记忆内容文本
- `MetadataGrid` — 元数据网格：相似度、分类、创建时间
- `TagManager` — 标签管理，可添加/删除标签
- `SemanticGraph` — 语义关联图谱可视化（实体节点 + 关系连线）
- `RelatedMemories` — 相关记忆列表

### 3.2 对话模式 (Memory Chat)

**布局**: 左右布局

| 左侧主区域 (flex) | 右侧配置面板 (260px) |
|-------------------|---------------------|
| 对话头：助手信息 | 配置标题 |
| 消息列表 | 会话统计（轮次/引用） |
| 输入框 + 状态指示 | 模型选择下拉框 |
| | 记忆层切换（情景/语义/全息） |
| | Top-K 滑块 |
| | 记忆统计 |
| | 保存配置按钮 |

**对话消息组件**:
- `UserMessage` — 用户消息，右对齐深色气泡
- `AIResponse` — AI 回复，左对齐浅色气泡
- `MemoryReferenceCard` — 参考记忆卡片，显示相似度分值
- `MemoryStatsFooter` — 显示使用的记忆数和 Tokens

**右侧配置组件**:
- `SessionStats` — 本次会话统计
- `ModelSelector` — 模型选择下拉框
- `MemoryLayerToggle` — 记忆层切换按钮组
- `RetrievalSlider` — Top-K 和相似度阈值滑块
- `MemoryStats` — 记忆统计

### 3.3 后端模式 (Storage Backend)

**布局**: 三栏布局

| 左侧后端列表 (280px) | 中间详情 (flex) | 右侧快速操作 (220px) |
|---------------------|-----------------|---------------------|
| 搜索框 | 连接信息网格 | 系统健康状态 |
| 后端卡片列表 | 性能指标 | 存储统计 |
| (选中高亮) | 记忆层映射图 | 快速操作按钮 |
| 添加后端按钮 | 扩展接口列表 | 添加新后端 |

**左侧后端列表组件**:
- `BackendCard` — 后端卡片，显示：图标、名称、状态指示灯、性能指标
- `BackendTypes` — 支持的后端类型：
  - 🔢 向量存储 (Milvus)
  - 🔗 图存储 (Neo4j)
  - ⚡ 缓存层 (Redis)
  - 🗄️ 元数据 (SQLite)

**中间详情组件**:
- `ConnectionInfo` — 连接信息：主机、端口、集合、状态
- `PerformanceMetrics` — 性能指标：总数、延迟、可用性、索引类型
- `MemoryLayerMapping` — 记忆层映射图：Layer 0/1/2 与后端的对应关系可视化
- `ExtensionPoints` — 扩展接口：支持的自定义后端列表

**右侧快速操作组件**:
- `SystemHealth` — 系统健康状态
- `StorageStats` — 存储统计
- `QuickActions` — 快速操作：重新连接/查看日志/诊断/备份
- `AddBackendButton` — 添加新后端

---

## 4. 核心组件库

### 4.1 通用组件
| 组件 | 说明 |
|------|------|
| `Button` | 按钮，支持 primary/secondary/danger 变体 |
| `Input` | 输入框，支持前缀图标 |
| `Select` | 下拉选择框 |
| `RangeSlider` | 范围滑块 |
| `Toggle` | 开关切换 |
| `Card` | 卡片容器 |
| `Badge` | 标签/徽章 |
| `Modal` | 模态对话框 |
| `Tooltip` | 提示气泡 |

### 4.2 业务组件
| 组件 | 说明 |
|------|------|
| `MemoryCard` | 记忆卡片 |
| `MemoryGraph` | 语义关联图谱 |
| `BackendCard` | 后端卡片 |
| `ChatMessage` | 聊天消息 |
| `ConfigPanel` | 配置面板 |

---

## 5. 状态管理

### 5.1 全局状态
```typescript
interface AppState {
  activeMode: 'memory' | 'chat' | 'backend';
  memories: Memory[];
  selectedMemoryId: string | null;
  categories: Category[];
  backends: Backend[];
  chatSession: ChatSession;
  config: AppConfig;
}
```

### 5.2 模式状态
- `MemoryState` — 记忆列表、筛选条件、排序方式
- `ChatState` — 对话历史、输入内容、配置
- `BackendState` — 后端列表、选中后端、连接状态

---

## 6. API 接口设计

### 6.1 记忆 API
```
GET    /api/memories          — 获取记忆列表
POST   /api/memories          — 创建记忆
GET    /api/memories/:id      — 获取单条记忆
PUT    /api/memories/:id      — 更新记忆
DELETE /api/memories/:id      — 删除记忆
POST   /api/memories/search    — 语义搜索
POST   /api/memories/batch     — 批量操作
```

### 6.2 后端 API
```
GET    /api/backends                — 获取后端列表
POST   /api/backends                — 添加后端
GET    /api/backends/:id            — 获取后端详情
PUT    /api/backends/:id            — 更新后端配置
DELETE /api/backends/:id            — 删除后端
POST   /api/backends/:id/test       — 测试连接
GET    /api/backends/:id/stats      — 获取后端统计
```

### 6.3 对话 API
```
POST   /api/chat                    — 发送对话消息
GET    /api/chat/history            — 获取对话历史
POST   /api/chat/clear              — 清除对话
GET    /api/chat/config             — 获取对话配置
PUT    /api/chat/config             — 更新对话配置
```

---

## 7. 技术选型

### 7.1 前端框架
- **React 18** — UI 框架
- **TypeScript** — 类型安全
- **Tailwind CSS** — 样式解决方案
- **React Query** — 数据获取和缓存
- **Zustand** — 轻量状态管理
- **React Router** — 路由管理

### 7.2 可视化
- **D3.js / React Flow** — 语义关联图谱
- **Recharts** — 统计图表

### 7.3 构建工具
- **Vite** — 开发服务器和构建
- **ESLint + Prettier** — 代码规范

---

## 8. 多后端扩展性

### 8.1 后端抽象接口
```typescript
interface VectorStoreAdapter {
  name: string;
  connect(config: ConnectionConfig): Promise<void>;
  disconnect(): Promise<void>;
  insert(vectors: Vector[]): Promise<string[]>;
  search(query: Vector, topK: number): Promise<SearchResult[]>;
  delete(id: string): Promise<void>;
  getStats(): Promise<StoreStats>;
}

interface GraphStoreAdapter {
  name: string;
  // similar interface pattern
}
```

### 8.2 支持的后端类型
| 类型 | 当前实现 | 可扩展 |
|------|----------|--------|
| 向量存储 | Milvus, SQLite+FAISS | Pinecone, Qdrant, Weaviate, ChromaDB |
| 图存储 | Neo4j | MemGraph, ArangoDB |
| 缓存 | Redis LRU | Memcached |
| 元数据 | SQLite | PostgreSQL, MySQL |

---

## 9. 用户操作文档概要

### 9.1 记忆管理
1. **创建记忆** — 点击"+ 新建记忆" → 填写内容 → 选择分类 → 保存
2. **编辑记忆** — 点击记忆卡片 → 编辑内容/标签 → 保存
3. **删除记忆** — 选中记忆 → 点击删除 → 确认
4. **搜索记忆** — 输入关键词 → 查看匹配结果
5. **筛选记忆** — 选择分类/时间/相关度筛选
6. **批量操作** — 勾选多条记忆 → 导出/删除

### 9.2 对话体验
1. **发送消息** — 输入问题 → 发送 → 查看 AI 回复和参考记忆
2. **配置对话** — 选择模型/记忆层/Top-K → 保存
3. **清除对话** — 点击清除 → 确认

### 9.3 后端管理
1. **查看后端状态** — 切换到后端模式 → 查看各后端连接状态
2. **添加后端** — 点击"添加后端" → 选择类型 → 填写配置 → 测试连接 → 保存
3. **测试连接** — 选中后端 → 点击"测试连接"
4. **查看统计** — 选中后端 → 查看性能指标

---

## 10. 设计资源

### 10.1 图谱文件
- 设计 Mockup: `.superpowers/brainstorm/memory-system-v7-backend.html`

### 10.2 设计决策记录
| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-20 | 初始设计，温暖极简风格，三模式架构 |

---

**审核状态**: 待用户确认
**下一步**: 进入实施计划阶段
