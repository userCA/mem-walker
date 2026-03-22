# Mnemosyne Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React-based web UI for Mnemosyne memory system with three modes: Memory Management, Memory Chat, and Storage Backend Management.

**Architecture:** Three-tab SPA architecture with React 18 + TypeScript + Tailwind CSS. Backend uses existing Python service with FastAPI REST API layer. State managed via Zustand with React Query for server state.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, React Query, Zustand, React Router, react-hotkeys (keyboard shortcuts), D3.js/React Flow (for graph visualization), Recharts (for stats), Vite

---

## 1. Project Structure

```
web/
├── src/
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios instance with interceptors
│   │   ├── memories.ts         # Memory API calls
│   │   ├── backends.ts         # Backend API calls
│   │   └── chat.ts             # Chat API calls
│   │
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Base UI components (Button, Input, Card, Badge, Modal, Select, RangeSlider, Toggle, Tooltip, Textarea)
│   │   ├── layout/             # Layout components (Header)
│   │   ├── memory/             # Memory-specific (MemoryGraph)
│   │   └── chat/               # Chat-specific (MemoryReferenceCard, MemoryStatsFooter)
│   │
│   ├── features/               # Feature modules (single-focus)
│   │   ├── memory/             # Memory Management Mode (Sidebar, List, Detail, BatchActionsBar, Layout)
│   │   ├── chat/               # Memory Chat Mode (Messages, Input, Config, Layout)
│   │   └── backend/            # Backend Management Mode (List, Detail, SystemHealth, StorageStats, QuickActions, MemoryLayerMapping, Layout)
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useMemories.ts
│   │   ├── useBackends.ts
│   │   ├── useChat.ts
│   │   ├── useLocalStorage.ts
│   │   └── useHotkeys.ts
│   │
│   ├── stores/                 # Zustand stores
│   ├── types/                  # TypeScript types
│   ├── lib/                    # Utilities (cn.ts)
│   ├── App.tsx
│   └── main.tsx
│
├── server/                     # Python FastAPI backend
│   ├── main.py
│   ├── api/
│   └── models/
```

---

## 2. Task Breakdown

### Task 1: Project Scaffold

**Files to create:**
- `web/package.json`
- `web/tsconfig.json`
- `web/vite.config.ts`
- `web/tailwind.config.js`
- `web/index.html`
- `web/src/index.css`

- [ ] **Step 1: Create package.json** with React 18, TypeScript, Tailwind, React Query, Zustand, Axios, react-hotkeys, D3.js, Recharts

- [ ] **Step 2: Create tsconfig.json** with path aliases (@/*)

- [ ] **Step 3: Create vite.config.ts** with React plugin and proxy to backend

- [ ] **Step 4: Create tailwind.config.js** with warm minimal color palette from spec

- [ ] **Step 5: Create index.html** with Inter font

- [ ] **Step 6: Create src/index.css** with Tailwind directives and CSS variables

- [ ] **Step 7: Commit**

---

### Task 2: Base UI Components

**Files to create:**
- `web/src/lib/cn.ts`
- `web/src/components/ui/Button.tsx`
- `web/src/components/ui/Input.tsx`
- `web/src/components/ui/Card.tsx`
- `web/src/components/ui/Badge.tsx`
- `web/src/components/ui/Modal.tsx`
- `web/src/components/ui/Select.tsx`
- `web/src/components/ui/RangeSlider.tsx`
- `web/src/components/ui/Toggle.tsx`
- `web/src/components/ui/Tooltip.tsx`
- `web/src/components/ui/Textarea.tsx`

- [ ] **Step 1: Create lib/cn.ts** (clsx wrapper)

- [ ] **Step 2: Create Button.tsx** (primary/secondary/danger/ghost variants)

- [ ] **Step 3: Create Input.tsx** (with icon prefix support, ⌘K keyboard shortcut handler via useHotkeys hook)

- [ ] **Step 4: Create Card.tsx** (with selected state)

- [ ] **Step 5: Create Badge.tsx** (work/personal/project/study variants)

- [ ] **Step 6: Create Modal.tsx** (with backdrop)

- [ ] **Step 7: Create Select.tsx** (dropdown selection)

- [ ] **Step 8: Create RangeSlider.tsx** (range input with styled thumb)

- [ ] **Step 9: Create Toggle.tsx** (switch component for rerank toggle, etc.)

- [ ] **Step 10: Create Tooltip.tsx** (hover tooltip)

- [ ] **Step 11: Create Textarea.tsx** (multi-line input for system prompt)

- [ ] **Step 12: Commit**

---

### Task 3: TypeScript Types

**Files to create:**
- `web/src/types/memory.ts`
- `web/src/types/backend.ts`
- `web/src/types/chat.ts`
- `web/src/types/api.ts`

- [ ] **Step 1: Create memory.ts** (Memory, MemoryCategory, MemoryStats)

- [ ] **Step 2: Create backend.ts** (Backend, BackendType, BackendStats)

- [ ] **Step 3: Create chat.ts** (ChatMessage, ChatConfig, SessionStats)

- [ ] **Step 4: Create api.ts** (ApiResponse wrappers)

- [ ] **Step 5: Commit**

---

### Task 4: API Client Layer

**Files to create:**
- `web/src/api/client.ts`
- `web/src/api/memories.ts`
- `web/src/api/backends.ts`
- `web/src/api/chat.ts`

- [ ] **Step 1: Create client.ts** (Axios instance with error handling)

- [ ] **Step 2: Create memories.ts** (CRUD + search + stats)

- [ ] **Step 3: Create backends.ts** (CRUD + test + stats)

- [ ] **Step 4: Create chat.ts** (send + history + config)

- [ ] **Step 5: Commit**

---

### Task 5: React Query Hooks

**Files to create:**
- `web/src/hooks/useMemories.ts`
- `web/src/hooks/useBackends.ts`
- `web/src/hooks/useChat.ts`
- `web/src/hooks/useLocalStorage.ts`
- `web/src/hooks/useHotkeys.ts` (for ⌘K keyboard shortcuts)

- [ ] **Step 1: Create useMemories.ts** (list, get, create, update, delete, search)

- [ ] **Step 2: Create useBackends.ts** (CRUD + test connection)

- [ ] **Step 3: Create useChat.ts** (send message, clear, config)

- [ ] **Step 4: Create useLocalStorage.ts**

- [ ] **Step 5: Create useHotkeys.ts** (register keyboard shortcuts like ⌘K for search)

- [ ] **Step 6: Commit**

---

### Task 6: Zustand Stores

**Files to create:**
- `web/src/stores/appStore.ts`
- `web/src/stores/memoryStore.ts`
- `web/src/stores/chatStore.ts`
- `web/src/stores/backendStore.ts`

- [ ] **Step 1: Create appStore.ts** (activeMode state)

- [ ] **Step 2: Create memoryStore.ts** (selectedMemoryId, search, category filters)

- [ ] **Step 3: Create chatStore.ts** (config panel state)

- [ ] **Step 4: Create backendStore.ts** (selectedBackendId, modal state)

- [ ] **Step 5: Commit**

---

### Task 7: Memory Mode Components

**Files to create:**
- `web/src/features/memory/MemorySidebar.tsx` (includes StatsOverview, CategoryList, QuickFilters, SearchBar, NewMemoryButton)
- `web/src/features/memory/MemoryList.tsx` (memory cards with selection, scroll, BatchActionsBar)
- `web/src/features/memory/MemoryDetail.tsx` (includes MemoryContent, MetadataGrid, TagManager, RelatedMemories)
- `web/src/features/memory/MemoryLayout.tsx`
- `web/src/features/memory/BatchActionsBar.tsx`
- `web/src/components/memory/MemoryGraph.tsx` (D3.js/React Flow for semantic visualization)
- `web/src/features/memory/index.ts`

- [ ] **Step 1: Create MemorySidebar.tsx** including:
  - SearchBar with ⌘K shortcut (via useHotkeys)
  - StatsOverview (2x2 grid: total/episodic/semantic/relations)
  - CategoryList (全部/工作/个人/项目/学习 with color and count)
  - QuickFilters (最近7天/高相关度/多关联)
  - NewMemoryButton

- [ ] **Step 2: Create MemoryList.tsx** (memory cards with selection, scroll)

- [ ] **Step 3: Create BatchActionsBar.tsx** (select all, export, delete buttons)

- [ ] **Step 4: Create MemoryGraph.tsx** (D3.js/React Flow visualization with entity nodes and relation edges, interactive)

- [ ] **Step 5: Create MemoryDetail.tsx** including:
  - MemoryContent (memory text)
  - MetadataGrid (similarity, category, created time)
  - TagManager (add/remove tags)
  - RelatedMemories (list of related memories)
  - (Uses MemoryGraph for semantic associations)

- [ ] **Step 6: Create MemoryLayout.tsx** (three-column: Sidebar + List + Detail)

- [ ] **Step 7: Create index.ts**

- [ ] **Step 8: Commit**

---

### Task 8: Chat Mode Components

**Files to create:**
- `web/src/features/chat/ChatMessages.tsx`
- `web/src/features/chat/ChatInput.tsx`
- `web/src/features/chat/ChatConfig.tsx`
- `web/src/features/chat/ChatLayout.tsx`
- `web/src/components/chat/MemoryReferenceCard.tsx` (displays reference memory with similarity score)
- `web/src/components/chat/MemoryStatsFooter.tsx` (memory count and tokens used)
- `web/src/features/chat/index.ts`

- [ ] **Step 1: Create ChatMessages.tsx** (user/assistant messages, uses MemoryReferenceCard for references, uses MemoryStatsFooter, loading states)

- [ ] **Step 2: Create ChatInput.tsx** (input with keyboard hints ⏎, ⌫, ⇧)

- [ ] **Step 3: Create MemoryReferenceCard.tsx** (shows referenced memory content with similarity score)

- [ ] **Step 4: Create MemoryStatsFooter.tsx** (displays memory count and tokens used)

- [ ] **Step 5: Create ChatConfig.tsx** including sub-components:
  - SessionStats (turns, memory references)
  - ModelSelector (Claude, GPT-4, Gemini dropdown)
  - MemoryLayerToggle (情景/语义/全息)
  - RetrievalSlider (Top-K and similarity threshold sliders)
  - RerankToggle (BM25 reranking switch)
  - SystemPrompt (Textarea for custom prompt)
  - MemoryStats (total, episodic, semantic counts)
  - Save button

- [ ] **Step 6: Create ChatLayout.tsx** (header with avatar + title + history/clear buttons, messages area, ChatInput, ChatConfig sidebar)

- [ ] **Step 7: Create index.ts**

- [ ] **Step 8: Commit**

---

### Task 9: Backend Mode Components

**Files to create:**
- `web/src/features/backend/BackendList.tsx`
- `web/src/features/backend/BackendDetail.tsx`
- `web/src/features/backend/SystemHealth.tsx`
- `web/src/features/backend/StorageStats.tsx`
- `web/src/features/backend/QuickActions.tsx`
- `web/src/features/backend/MemoryLayerMapping.tsx` (visual layer mapping diagram)
- `web/src/features/backend/BackendLayout.tsx`
- `web/src/features/backend/index.ts`

- [ ] **Step 1: Create BackendList.tsx** (backend cards with status indicators, search, add button)

- [ ] **Step 2: Create BackendDetail.tsx** (connection info, performance metrics, MemoryLayerMapping)

- [ ] **Step 3: Create SystemHealth.tsx** (system health status indicator)

- [ ] **Step 4: Create StorageStats.tsx** (storage statistics display)

- [ ] **Step 5: Create QuickActions.tsx** (reconnect, view logs, diagnose, backup buttons)

- [ ] **Step 6: Create MemoryLayerMapping.tsx** (Layer 0/1/2 visualization with backend connections)

- [ ] **Step 7: Create BackendLayout.tsx** (three-column: List + Detail + QuickActions panel with SystemHealth, StorageStats, QuickActions, AddBackendButton)

- [ ] **Step 8: Create index.ts**

- [ ] **Step 9: Commit**

---

### Task 10: Main App Assembly

**Files to create:**
- `web/src/App.tsx`
- `web/src/main.tsx`
- `web/src/components/layout/Header.tsx` (Logo, ModeTabs, Import/Export buttons, Status indicator)
- `web/src/components/layout/index.ts`

- [ ] **Step 1: Create Header.tsx** including:
  - Logo (🧠 Mnemosyne)
  - ModeTabs (🗂️ 记忆 / 💬 对话 / 🏪 后端)
  - Import button
  - Export button
  - Status indicator

- [ ] **Step 2: Create App.tsx** (QueryClientProvider, Header, mode tabs, content switching via activeMode)

- [ ] **Step 3: Create main.tsx** (ReactDOM.createRoot)

- [ ] **Step 4: Create layout/index.ts**

- [ ] **Step 5: Commit**

---

### Task 11: FastAPI Backend Server

**Files to create:**
- `web/server/__init__.py`
- `web/server/main.py`
- `web/server/api/__init__.py`
- `web/server/api/memories.py`
- `web/server/api/backends.py`
- `web/server/api/chat.py`
- `web/server/models/__init__.py`
- `web/server/models/memory.py`
- `web/server/models/backend.py`
- `web/server/models/chat.py`

**Mock Data Structure** (must match frontend types):
```python
# memories_db = [
#   {"id": "mem_1", "content": "...", "category": "work", "tags": ["AI"], "user_id": "demo", "created_at": "2026-03-21T00:00:00Z", "updated_at": "2026-03-21T00:00:00Z", "similarity": 0.91}
# ]
#
# backends_db = [
#   {"id": "milvus_1", "name": "Milvus", "type": "milvus", "status": "connected", "host": "localhost", "port": 19530, "stats": {"total_count": 1000, "latency_ms": 12, "availability": 99.9, "index_type": "HNSW"}}
# ]
#
# chat_messages = []  # List of ChatMessage objects
```

- [ ] **Step 1: Create main.py** (FastAPI app with CORS and routers)

- [ ] **Step 2: Create memories.py** (CRUD endpoints with mock data matching frontend types)

- [ ] **Step 3: Create backends.py** (backend management endpoints with mock data)

- [ ] **Step 4: Create chat.py** (chat endpoints with config, mock messages list)

- [ ] **Step 5: Create Pydantic models** (Memory, Backend, Chat models matching frontend API types)

- [ ] **Step 6: Commit**

---

### Task 12: Integration & Testing

- [ ] **Step 1: Create .env.example**

- [ ] **Step 2: Run npm install and build**

- [ ] **Step 3: Verify TypeScript compilation**

- [ ] **Step 4: Commit**

---

## 3. Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Project Scaffold | package.json, tsconfig, vite, tailwind, index.html |
| 2 | Base UI Components | Button, Input, Card, Badge, Modal, Select, RangeSlider, Toggle, Tooltip |
| 3 | TypeScript Types | Memory, Backend, Chat, API types |
| 4 | API Client | Axios client + API endpoints for memories, backends, chat |
| 5 | React Query Hooks | useMemories, useBackends, useChat |
| 6 | Zustand Stores | App, Memory, Chat, Backend state |
| 7 | Memory Mode | Sidebar, List, Detail, Layout |
| 8 | Chat Mode | Messages, Input, Config, Layout |
| 9 | Backend Mode | List, Detail, Layout |
| 10 | Main App | App.tsx, main.tsx, mode switching |
| 11 | FastAPI Backend | API server with mock data |
| 12 | Integration Test | Build verification |

---

## 4. Verification Commands

```bash
# Install dependencies
cd web && npm install

# Type check
npm run type-check

# Build
npm run build

# Start dev server
npm run dev

# Start API server (in another terminal)
cd web/server && python -m uvicorn main:app --reload --port 8000
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-03-21-memory-ui-implementation.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
