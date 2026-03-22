# Mnemosyne Memory System

## 项目概述

Mnemosyne 是一个智能记忆系统，基于 FastAPI 后端 + React 前端构建，支持与 DeepSeek AI 对话。

## 技术栈

### 后端 (server/)
- **框架**: FastAPI + Python 3.11+
- **数据库**: 内存数据库 (开发中) / Milvus (生产)
- **AI 集成**: DeepSeek API (OpenAI-compatible)
- **配置**: pydantic-settings + .env

### 前端 (web/)
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **样式**: Tailwind CSS
- **状态管理**: TanStack Query + Zustand
- **UI 组件**: 自定义组件库

## 启动方式

### 后端
```bash
cd server
pip install -r requirements.txt
python -m app.main
# 服务运行在 http://localhost:8000
```

### 前端
```bash
cd web
npm install
npm run dev
# 服务运行在 http://localhost:3000
```

## 环境变量

### 后端 (.env)
```
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 前端
使用 Vite 代理连接到后端，无需额外配置。

## 主要功能

1. **记忆管理**: 创建、编辑、搜索记忆
2. **对话功能**: 与 DeepSeek AI 对话，基于记忆上下文
3. **后端管理**: 配置 Milvus 等向量数据库连接

## API 端点

- `/api/v1/memory/*` - 记忆管理
- `/api/v1/chat/*` - 对话管理
- `/api/v1/backend/*` - 后端连接管理
