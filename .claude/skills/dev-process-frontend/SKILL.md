---
name: dev-process-frontend
description: "mnemosyne 前端开发流程规范（React/TypeScript）—— dev-process-optimizer 的子 skill。预防：API 端点与后端不对齐、Zustand store 职责混乱、React Query 键不稳定、生产 debug 日志、类型与后端 DTO 不同步。覆盖：web/src/ 的 components/ hooks/ stores/ types/ api/。"
---

# 前端开发流程规范（mnemosyne React/TypeScript）

> 子 skill，架构/跨层问题先看 `dev-process-optimizer`。

防止重复犯错。每条规则源于 mnemosyne 前端代码审查发现。

---

## 修改前快速检查

```
□ 改了 API 调用？确认后端对应端点存在（对比 adapter/router/ 和 web/src/api/）
□ 新增 store 字段？它是 UI 状态（zustand）还是服务端数据（react-query）？
□ 改了 types/？确认后端 DTO 有对应字段且 camelCase/snake_case 对齐
□ 涉及 MemoryCard/ChatMessage 组件？确认 loading、empty、error 三种状态都处理
□ 新增组件？确认它挂载在 App.tsx 的 mode 条件分支内
```

---

## 规则 1：API 端点与后端对齐 —— 前端定义的每个端点后端必须存在

**模式：** 前端 `web/src/api/` 定义了 API 函数，但后端 `adapter/router/` 没有对应路由。调用时 404 被 axios 拦截器捕获，用户看到的是模糊的 "请求失败"。

**真实案例：** 前端 `chatApi` 定义了 `deleteMessage`、`clearSession`、`regenerateMessage` 三个端点函数，但后端 `chat_controller.py` 没有暴露这些路由。

**检查清单：**
- 前端 `web/src/api/memory.ts` 的每个导出函数 → grep 后端 `adapter/router/memory.py` 确认对应路由
- 前端 `web/src/api/chat.ts` 的每个导出函数 → grep 后端 `adapter/router/chat.py` 确认对应路由
- 前端 `web/src/api/backend.ts` 的每个导出函数 → grep 后端 `adapter/router/backend.py` 确认对应路由
- 新增前端 API 函数前，先确认后端端点已实现；否则先实现后端

---

## 规则 2：Zustand Store 只存 UI 状态，服务端数据用 React Query

**模式：** 把 API 返回的数据存入 zustand store，导致 store 数据与服务器状态不同步，需要手动同步逻辑。

**当前正确拆分：**
- `appStore.ts` — 全局 UI（mode、sidebarCollapsed、theme），部分 localStorage 持久化
- `memoryStore.ts` — 记忆列表 UI（filters、sort、viewMode、selected）
- `chatStore.ts` — 聊天 UI（currentSessionId、config、presets）
- `backendStore.ts` — 后端管理 UI（selectedProvider、modals、connectionTest）

**检查清单：**
- 新增状态前问："这是用户看到的 UI 状态，还是从服务器获取的数据？"
- UI 状态 → zustand store。服务端数据 → React Query（`useQuery`/`useMutation`）
- 不要在 zustand store 中缓存 API 响应数据
- 如果需要在 store 中引用 API 数据（如 `selectedMemoryId`），只存 ID，不存完整对象

---

## 规则 3：React Query 键必须稳定 —— 避免对象字面量作为键

**模式：** query key factory 接受 params 对象，如果调用者每次渲染都创建新的对象字面量，会导致无限重新获取。

**当前模式（正确）：**
```typescript
// query key factory
export const memoryKeys = {
  all: ['memories'] as const,
  lists: () => [...memoryKeys.all, 'list'] as const,
  list: (params: MemoryQueryParams) => [...memoryKeys.lists(), params] as const,
}
```

**检查清单：**
- 新增 query key factory 时，确保调用者传入的 params 引用稳定（用 `useMemo` 或用原始值）
- 不要在 key factory 中使用内联对象字面量 `list({ page: 1 })`，应使用稳定的引用
- grep `queryKey:` 在 `hooks/` —— 确认所有键都是通过 key factory 创建的，不手写字符串

---

## 规则 4：生产代码禁止 console.log —— 使用统一的日志工具

**模式：** 组件和 hooks 中残留 `console.log()` 调试语句，生产环境控制台输出噪音。

**真实案例：** `useChat.ts` 第 25-38 行有 `console.log` 调试语句。`ChatPanel.tsx` 组件中也有残留。

**检查清单：**
- 提交前 grep `console\.(log|debug|warn)` 在 `web/src/` 中
- 如果确实需要日志，使用统一的 logger 工具（`web/src/lib/` 中定义）
- 错误日志用 `console.error` 保留（用于生产排查）

---

## 规则 5：类型定义与后端 DTO 保持同步

**模式：** 后端 `adapter/dto/` 新增或修改字段后，前端 `web/src/types/` 没有同步更新。TypeScript 编译通过（字段是可选的），但 UI 永远展示 undefined。

**当前类型映射：**
| 后端 DTO | 前端类型文件 |
|----------|------------|
| `memory_dto.py` | `web/src/types/memory.ts` |
| `chat_dto.py` | `web/src/types/chat.ts` |
| `backend_dto.py` | `web/src/types/backend.ts` |
| `common.py` | `web/src/types/api.ts` |

**检查清单：**
- 后端 DTO 新增字段 → 同步更新前端对应类型文件
- 注意 camelCase/snake_case 转换 —— 后端 Pydantic 用 `alias` 做转换，前端类型 key 必须是 camelCase
- 枚举值必须双向对齐（如 `MemoryStatus`、`MemoryPriority`）
- datetime 字段：后端返回 ISO 字符串，前端类型定义为 `string`（不是 `Date`）

---

## 规则 6：组件必须覆盖 loading / empty / error 三种状态

**模式：** 组件只写了正常数据渲染，没处理加载中、空数据、错误三种边界状态。

**当前组件应遵循的模式（参考 `MemoryCard.tsx`）：**
```typescript
if (isLoading) return <Skeleton />;
if (isError) return <ErrorState message={error.message} />;
if (!data || data.length === 0) return <EmptyState />;
return <DataView data={data} />;
```

**检查清单：**
- 新增数据展示组件 → 确认四种状态都有渲染分支
- 错误状态要有重试按钮（调用 `refetch()`）
- 空状态要有引导性文案（不是空白页面）

---

## 规则 7：App.tsx 的 mode 条件渲染 —— 新增页面必须挂载

**模式：** `App.tsx` 第 75-118 行通过 `mode` 状态条件渲染不同面板。新增页面组件后忘记在 App.tsx 中注册，组件代码存在但永远不被渲染。

**当前路由结构：**
```
mode === 'memory'  → <MemorySidebar /> <MemoryList /> <MemoryDetail />
mode === 'chat'    → <ChatSidebar /> <ChatPanel />
mode === 'backend' → <BackendSidebar /> <BackendDetail />
```

**检查清单：**
- 新增页面/面板 → 在 `App.tsx` 的对应 mode 分支中挂载
- 如果是新 mode → 需要更新 `appStore.ts` 的 `mode` 类型联合
- 新增 mode → 更新 `Header.tsx` 的导航切换逻辑

---

## 规则 8：zustand store 模式一致性

**模式：** 四个 zustand store 使用略不同的 set 模式。有的展开嵌套状态，有的直接替换。不一致增加阅读成本。

**标准模式（参考 `memoryStore.ts`）：**
```typescript
import { create } from 'zustand';

interface MemoryStore {
  filters: MemoryFilters;
  setFilters: (filters: Partial<MemoryFilters>) => void;
}

export const useMemoryStore = create<MemoryStore>((set) => ({
  filters: defaultFilters,
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
}));
```

**检查清单：**
- 新增 store 或 action → 参照 `memoryStore.ts` 的 set 模式
- 嵌套状态更新使用展开 `...state.xxx` 合并，不直接替换
- localStorage 持久化只用 `partialize` 选项（参考 `appStore.ts`），不手动读写

---

## 规则 9：axios 拦截器 —— 不吞错，给用户有意义的提示

**模式：** axios 响应拦截器捕获错误后统一 toast 提示。如果拦截器返回 `Promise.reject` 且 hook 中也处理了 error，用户看到两条错误提示。

**检查清单：**
- `web/src/api/client.ts` 的拦截器负责通用错误（网络断开、500）
- hook 层的 `onError` 负责业务错误（404、409、422）
- 不要在两层都弹出 toast
- 后端错误响应格式：`{ code, message, status_code }` —— 前端 toast 应展示 `message` 字段

---

## 规则 10：CSS 变量使用项目统一的设计令牌

**模式：** 组件中硬编码颜色值（`#3b82f6`、`#ef4444`），与 `index.css` 中定义的 CSS 变量不一致。主题切换时这些硬编码颜色不会变化。

**当前可用的设计令牌（参考 `web/src/index.css`）：**
- `--accent`、`--focus-ring` — 主色调和焦点光圈
- `--surface`、`--surface-soft` — 背景层级
- `--hairline` — 边框颜色
- `--text-primary`、`--text-secondary` — 文字层级
- `--radius-sm`、`--radius-md` — 圆角

**检查清单：**
- 新增 CSS 中颜色值必须是 `var(--xxx)` 引用，不是硬编码
- 新增输入元素必须有统一的 `:focus` 样式：`border-color: var(--accent)` + `box-shadow: 0 0 0 3px var(--focus-ring)`
- grep `#[0-9a-fA-F]{6}` 在 `web/src/components/` 的 `.css` 文件中 —— 应该极少

---

## 修改后验证

```
□ TypeScript 编译通过：cd web && npm run type-check
□ ESLint 无新警告：cd web && npm run lint
□ 无 console.log 残留：grep console.log web/src/
□ 如果改了 types/ → 确认与后端 DTO 字段对齐（对比 service/mnemosyne/adapter/dto/）
□ 如果改了 API 端点 → git diff web/src/api/ 和 service/mnemosyne/adapter/router/ 双向核对
□ 如果新增组件 → 确认在 App.tsx 中挂载且 loading/empty/error 三种状态已处理
□ 如果改了 CSS → 确认颜色是 var(--xxx) 不是硬编码
□ 手动验证：npm run dev 启动后在浏览器中过一遍修改的功能路径
```
