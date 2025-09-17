# Phase 2 – Core Feature Development (Chat + Knowledge Sources UI)

## Scope
Implement the internal dashboard UI for two pages using ANT Design: 1) Chat interface with Q&A/Docs/RFP modes and suggestion grid; 2) Knowledge Sources management with files table and upload modal. Backend wiring will be mocked with local API routes; full auth (Frontegg) is deferred.

## Assumptions
- Keep Phase 1 tech decisions (Next.js 14 App Router, TypeScript, ANT Design 5, pnpm)
- Local services/ports remain: backend 8082, document-processor 8081, frontend 3000
- Use temporary mock APIs under `apps/frontend/src/app/api/*` to unblock UI
- Persist lightweight client state in `localStorage` for recents until real APIs

## Deliverables
- Dashboard layout shell with collapsible left `Sider` and content area
- Left sidebar with Library/Collections tabs, search, and Recent (Last 7 Days)
- Page: Chat
  - Header tabs: Q&A, Docs, RFP
  - 2x2 suggested prompts grid
  - Message input with ⌘+Enter submit
  - Streaming area placeholder with mocked responses
- Page: Knowledge Sources
  - Files table with columns: Name, Source, Status, Updated, Actions
  - Filters: search, source, status, date range
  - Upload button → modal with tabs: Files, Web URLs (Integrations stub)
  - Drag-and-drop upload UI with validation; URL add form validation
- Mock API routes for chat and files; basic in-memory store for this session
- Basic responsive behavior (mobile: collapsed sider; content stacks)
- A11y: keyboard navigation for tabs and input; ARIA on actionable items
- Docs: how to run and smoke-test Phase 2 features

## Implementation Plan
1) Layout & Routing
- Create routes: `app/(dashboard)/chat/page.tsx` and `app/(dashboard)/knowledge/page.tsx`
- Add shared `components/DashboardLayout.tsx` using `Layout` with `Sider`

2) Sidebar
- Tabs: Library | Collections; search input; recent list mocked from local storage

3) Chat Page
- Header `Tabs` (qa | docs | rfp)
- Suggested prompts grid (click → prefill input)
- Message input with keyboard shortcut (⌘+Enter) and send button
- Chat transcript list with simple bubble UI; responses from mock API

4) Knowledge Sources Page
- Files `Table` with sortable columns, filters, status tags
- Upload button → `Modal` with `Tabs` (Files, Web URLs)
- Files tab: `Upload.Dragger` with accept list and size check
- Web URLs tab: `Form` with URL validations

5) Mock APIs
- `/api/chat` POST: echoes + small delay; streams simulated chunks
- `/api/files` GET/POST: in-memory list with simple statuses

6) State Management
- Lightweight local store (React context) for: active chat tab, recent conversations, files list; persist to `localStorage`

7) Styling & A11y
- Use ANT tokens; ensure color contrast; focus rings and keyboard navigation

8) Docs & Tests
- Update `docs/LOCAL_DEVELOPMENT.md` smoke steps
- Add Phase 2 usage notes in this doc

## Milestones & Acceptance Criteria
- M1: Layout + routes scaffolded (Chat and Knowledge pages render)
  - AC: Navigating to `/chat` and `/knowledge` shows distinct pages with sider
- M2: Sidebar with tabs, search, recent items
  - AC: Search filters list; recent items persist across reloads
- M3: Chat page core interactions
  - AC: Suggested prompts clickable; input submits on ⌘+Enter; transcript shows mocked reply
- M4: Knowledge page table + filters
  - AC: Table supports sort by Updated; filters by Status/Source; actions menu visible
- M5: Upload modal
  - AC: Drag-and-drop accepts only allowed types; URL form blocks invalid URLs
- M6: Mock APIs
  - AC: Network calls succeed; no console errors; reload preserves state via localStorage
- M7: Responsive & a11y passes quick checks
  - AC: Sider collapses under md; tab/enter can navigate and submit

## Todo checklist
- [ ] Scaffold dashboard layout shell and routes for chat and knowledge pages
- [ ] Implement left sidebar with Library/Collections tabs, search, and recent items
- [ ] Build Chat page: tabs (Q&A/Docs/RFP), suggestion cards, input with ⌘+Enter, chat stream placeholder
- [ ] Build Knowledge Sources page: files table with sort/filter/status and actions
- [ ] Implement Upload modal with Files + URL tabs; accept validations; progress UI
- [ ] Add mock API route handlers for chat and files in Next.js app
- [ ] Wire client state management and persistence for recents and active tabs
- [ ] Add responsive styles, accessibility, and theme tokens for ANT Design
- [ ] Write usage instructions and smoke tests for Phase 2 features

## Smoke Test (local)
- Start frontend: `pnpm --filter frontend dev`
- Visit `/chat`: send a message; see reply in <2s
- Visit `/knowledge`: upload a small `.txt` or add a URL; see row appear with status
- Refresh: recent conversations and files still visible

## Open Questions
- Exact recent conversation grouping rules beyond “Last 7 Days”
- Final file status lifecycle from processor
- Exact design tokens/theme direction
