# Design System Master File — Mnemosyne

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Mnemosyne — Holographic Cognitive Memory System
**Generated:** 2026-05-31 16:36:06
**Updated:** 2026-05-31 (aligned with actual project tokens)
**Category:** AI Platform / SaaS Dashboard
**Stack:** React + Tailwind CSS + Zustand + React Query

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable | Tailwind |
|------|-----|-------------|----------|
| Primary/Accent | `#f59e0b` | `--color-amber` | `text-amber-500` `bg-amber-500` |
| Accent Highlight | `#fef3c7` | `--color-amber-highlight` | `bg-amber-50` |
| Background | `#faf9f7` | `--color-background` | `bg-background` |
| Card Surface | `#ffffff` | `--color-card` | `bg-card` |
| Text Primary | `#1a1a1a` | `--color-text-primary` | `text-text-primary` |
| Text Secondary | `#64748b` | `--color-text-secondary` | `text-text-secondary` |
| Text Muted | `#8b8680` | `--color-text-muted` | `text-text-muted` |
| Border | `#e2ddd8` | `--color-border` | `border-border` |
| Border Light | `#f0eeeb` | `--color-border-light` | `border-border-light` |
| Success | `#22c55e` | `--color-success` | `text-success` |
| Layer Semantic | `#8b5cf6` | `--color-layer-semantic` | — |
| Layer Episodic | `#3b82f6` | `--color-layer-episodic` | — |
| Layer Procedural | `#10b981` | `--color-layer-procedural` | — |
| Layer Working | `#f97316` | `--color-layer-working` | — |

**Color Strategy:** Warm amber accent on neutral warm-white surface. High contrast text (4.7:1+). Layer colors reserved for memory category differentiation.

### Typography

- **Font Family:** Inter (single font, weight variations)
- **Style Name:** Minimal Swiss
- **Mood:** clean, functional, neutral, professional, readable
- **CSS:** `font-family: 'Inter', system-ui, -apple-system, sans-serif` (already in `index.css`)

**Weight scale:**

| Weight | Usage |
|--------|-------|
| 400 (regular) | Body text, inputs |
| 500 (medium) | Labels, badges, secondary headings |
| 600 (semibold) | Primary headings, card titles |
| 700 (bold) | Hero text, key metrics |

**Line height:** 1.5 for body, 1.25 for headings. Max line length: 72ch for prose content.

### Spacing Scale (Tailwind default)

| Token | Value | Usage |
|-------|-------|-------|
| `p-2` / `gap-2` | 8px | Icon gaps, badge padding |
| `p-3` / `gap-3` | 12px | Compact card padding |
| `p-4` / `gap-4` | 16px | Standard card/panel padding |
| `p-6` / `gap-6` | 24px | Section padding |
| `p-8` | 32px | Page padding, large gaps |

### Shadow Depths

| Level | Tailwind | Usage |
|-------|----------|-------|
| Subtle | `shadow-sm` | Cards at rest |
| Standard | `shadow-md` | Hovered cards, dropdowns |
| Elevated | `shadow-lg` | Modals, featured cards |
| Overlay | `shadow-xl` | Full-screen modals |

### Z-Index Scale

| Level | Value | Usage |
|-------|-------|-------|
| Base | `z-0` | Content |
| Dropdown | `z-40` | Dropdowns, popovers, tooltips |
| Navbar | `z-50` | Fixed sidebar, header |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-md` | 6px | Inputs, badges |
| `rounded-lg` | 8px | Cards, buttons |
| `rounded-xl` | 12px | Modals, panels |
| `rounded-full` | 9999px | Avatars, pills, toggle indicators |

---

## Component Specs

### Buttons

```tsx
// Primary (amber filled)
<button className="px-4 py-2 bg-amber-500 text-white rounded-lg font-medium
  hover:bg-amber-600 active:bg-amber-700
  transition-colors duration-200 cursor-pointer
  focus-visible:outline-2 focus-visible:outline-amber-500 focus-visible:outline-offset-2
  disabled:opacity-50 disabled:cursor-not-allowed">
  {children}
</button>

// Ghost (text-only, for secondary actions)
<button className="px-3 py-1.5 text-text-secondary rounded-lg
  hover:bg-gray-100 hover:text-text-primary
  transition-colors duration-200 cursor-pointer
  focus-visible:outline-2 focus-visible:outline-amber-500 focus-visible:outline-offset-2">
  {children}
</button>
```

**Rules:**
- Always show loading state (spinner + disabled) during async operations
- Minimum touch target 44x44px on mobile (`px-4 py-2` = 32px + text, add `min-h-[44px]` for mobile)

### Cards

```tsx
// Interactive card with hover
<div className="rounded-lg bg-card border border-border-light p-4
  transition-all duration-200 cursor-pointer
  hover:shadow-md hover:border-amber/30
  focus-visible:outline-2 focus-visible:outline-amber-500 focus-visible:outline-offset-2">
  {children}
</div>

// Selected card state
<div className="rounded-lg bg-card border p-4
  transition-all duration-200 cursor-pointer
  border-[var(--color-amber)] shadow-[0_2px_8px_rgba(245,158,11,0.15)]
  bg-gradient-to-br from-amber-50 to-white">
  {children}
</div>
```

**Rules:**
- Always `cursor-pointer` on clickable cards
- Hover transition 200ms, not scale transforms (prevents layout shift)
- Selected state uses amber border + warm gradient background
- Internal spacing: use `space-y-4` for consistent card body spacing

### Inputs

```tsx
<input className="px-3 py-2 border border-border-light rounded-lg
  text-sm text-text-primary bg-card
  placeholder:text-text-muted
  transition-colors duration-200
  focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20" />
```

### Sidebar / Navigation

```tsx
// Active nav item
<button className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm
  bg-amber-50 text-amber-700 font-medium
  transition-colors duration-200 cursor-pointer">
// Inactive nav item
<button className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm
  text-text-secondary hover:bg-gray-100
  transition-colors duration-200 cursor-pointer">
```

**Rules:**
- Active state: `bg-amber-50 text-amber-700 font-medium`
- Inactive: `text-text-secondary hover:bg-gray-100`
- Sidebar width: `w-64` (256px), with `border-r border-border`

### Skeleton Loading

```tsx
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
  <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
  <div className="h-4 bg-gray-200 rounded w-5/6" />
</div>
```

### Empty State

```tsx
<div className="flex flex-col items-center justify-center h-full text-center py-12">
  <p className="text-text-muted mb-2">{emptyMessage}</p>
  {actionButton}
</div>
```

### Error State

```tsx
<div className="flex flex-col items-center justify-center h-full text-center py-12">
  <p className="text-red-500 mb-2">{error.message}</p>
  <button onClick={refetch} className="text-amber-600 hover:underline cursor-pointer">重试</button>
</div>
```

### Badges / Tags

```tsx
// Active/pressed tag
<span className="px-2 py-1 rounded-full text-xs bg-amber-500 text-white cursor-pointer">
// Inactive tag
<span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-text-secondary hover:bg-gray-200 cursor-pointer transition-colors duration-200">
```

---

## Page Patterns

### Dashboard Layout (3-column)

```
┌──────────────────────────────────────────────┐
│ Header (h-14, border-b, bg-card)             │
├──────────┬───────────────────────┬───────────┤
│ Sidebar  │ Main Content          │ Detail    │
│ w-64     │ flex-1                │ w-80      │
│ border-r │ overflow-y-auto       │ border-l  │
│ p-4      │ p-6                   │ p-4       │
├──────────┴───────────────────────┴───────────┤
│ Status bar (h-8, text-xs, text-text-muted)    │
└──────────────────────────────────────────────┘
```

**Current implementation:** `App.tsx` mode-based conditional rendering:
- `mode === 'memory'` → `<MemorySidebar /> <MemoryList /> <MemoryDetail />`
- `mode === 'chat'` → `<ChatSidebar /> <ChatPanel />`
- `mode === 'backend'` → `<BackendSidebar /> <BackendDetail />`

---

## Style Guidelines

**Style:** Warm Minimal + Glassmorphism accents

**Keywords:** clean, warm, amber glow, frosted panels, high readability, professional, neutral background

**Key Effects:**
- Cards: `bg-card` (white) on `bg-background` (warm off-white `#faf9f7`)
- Selected state: `bg-gradient-to-br from-amber-50 to-white` + amber border
- Divider: `border-border` (`#e2ddd8`) — visible but subtle
- Hover feedback: color/opacity transition 150-200ms, no scale transforms

### Light Mode ONLY

Mnemosyne is light-mode only. No dark mode needed. Ensure:
- Text contrast minimum 4.5:1 (body text `#1a1a1a` on `#faf9f7` = 13.5:1 ✅)
- Muted text minimum 3:1 (`#8b8680` on `#faf9f7` = 3.1:1 ✅)
- Glass/transparent cards: use `bg-white/80` or higher opacity

---

## Anti-Patterns (Do NOT Use)

- ❌ **Emojis as UI icons** — Use Lucide/Heroicons SVG (project already uses emojis in ChatPanel: 💬 — migrate to `<MessageCircle />` icon)
- ❌ **console.log in production** — Already cleaned. Verify with grep before commit.
- ❌ **Hardcoded hex colors** — Use CSS variables or Tailwind amber classes.
- ❌ **Scale transforms on hover** — Shifts layout. Use color/shadow transitions instead.
- ❌ **Missing `cursor-pointer`** on clickable cards/buttons
- ❌ **`bg-white/10` on light backgrounds** — Invisible glass. Use `bg-white/80` minimum.
- ❌ **Dark mode** — Project is light-mode only
- ❌ **Excessive animation** — Use 150-200ms max for micro-interactions
- ❌ **Instant state changes** — Always use `transition-colors duration-200`
- ❌ **Emoji in ChatMessage avatars** — `👤` `🤖` in ChatMessage.tsx. Replace with SVG icons.

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

### Visual Quality
- [ ] No emojis as icons (use Lucide SVG instead)
- [ ] All colors use CSS variables or Tailwind classes (no hex in JSX)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-200ms)

### Component States
- [ ] Loading: skeleton/spinner rendered
- [ ] Empty: guided message, not blank page
- [ ] Error: message + retry button
- [ ] Active/selected: visually distinct

### Layout
- [ ] No content hidden behind fixed navbars/sidebars
- [ ] Responsive at 375px (mobile), 768px (tablet), 1024px (desktop)
- [ ] No horizontal scroll on mobile

### Accessibility
- [ ] Text contrast 4.5:1 minimum
- [ ] Focus states visible (`focus-visible:outline-2 focus-visible:outline-amber-500`)
- [ ] Form inputs have labels or aria-label
- [ ] No `console.log` residuals

### Performance
- [ ] `prefers-reduced-motion` respected
- [ ] Images lazy-loaded where applicable
