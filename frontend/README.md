# Alpha-Nexus Frontend

## Overview
Next.js 14 + React 18 + Tailwind CSS + Shadcn/UI interface layer for the Alpha-Nexus Personal Intelligence OS.

## Architecture

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Landing/Dashboard
│   ├── chat/              # Chat interface
│   │   └── page.tsx       # Real-time chat with SSE
│   ├── jobs/              # Job matching dashboard
│   │   └── page.tsx       # Career recommendations
│   ├── learning/          # Learning roadmap
│   │   └── page.tsx       # Phase-based learning path
│   ├── analytics/         # Financial analysis
│   │   └── page.tsx       # Company metrics & investment thesis
│   └── settings/          # User preferences
│       └── page.tsx       # Profile, API keys, notifications
├── components/            # Shared components
│   ├── ui/                # Shadcn/UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   ├── tabs.tsx
│   │   ├── accordion.tsx
│   │   └── ...
│   ├── chat/              # Chat-specific components
│   │   ├── MessageBubble.tsx
│   │   ├── StreamingResponse.tsx
│   │   ├── AgentStatusIndicator.tsx
│   │   └── CitationCard.tsx
│   ├── jobs/              # Job matching components
│   │   ├── JobCard.tsx
│   │   ├── SkillMatchBar.tsx
│   │   ├── CompensationBreakdown.tsx
│   │   └── FilterPanel.tsx
│   ├── learning/          # Learning components
│   │   ├── PhaseCard.tsx
│   │   ├── PaperCard.tsx
│   │   ├── Timeline.tsx
│   │   └── ProgressTracker.tsx
│   └── layout/            # Layout components
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       └── Footer.tsx
├── hooks/                 # Custom React hooks
│   ├── useChat.ts         # SSE chat hook
│   ├── useJobs.ts         # Job data fetching
│   ├── useLearning.ts     # Learning roadmap
│   └── useTheme.ts        # Dark/light mode
├── lib/                   # Utilities
│   ├── api.ts             # API client
│   ├── utils.ts           # Helpers
│   └── constants.ts       # App constants
├── types/                 # TypeScript types
│   ├── api.ts             # API response types
│   ├── schemas.ts         # Shared schemas (from Python)
│   └── index.ts
├── styles/                # Global styles
│   └── globals.css        # Tailwind + custom
└── public/                # Static assets
```

## Key Features

### 1. Real-time Chat Interface (`/chat`)
- SSE streaming from `/api/v1/chat/stream`
- Live agent status indicators (Supervisor → Scraper → Financial → Career → Learning → Synthesize)
- Expandable citations with source links
- Confidence score display
- Conversation history with persistence

### 2. Career Dashboard (`/jobs`)
- Filterable job cards (location, remote, salary, skill match)
- Skill gap visualization with progress bars
- Compensation breakdown (base, equity, bonus, total)
- One-click apply links
- Export to CSV/Notion

### 3. Learning Roadmap (`/learning`)
- Phase-based visualization (Neuro-Symbolic → Agentic AI → RAG → LLMOps → MLOps → Backend)
- Interactive paper cards with ArXiv links
- Progress tracking per phase
- Milestone checklists
- Resource library (courses, blogs, videos)

### 4. Analytics Dashboard (`/analytics`)
- Company metrics cards (market cap, revenue, headcount, margins)
- Investment thesis with risk flags
- Financial health scores (growth, profitability, valuation, FCF)
- Historical trends (when persistence is added)

### 5. Settings (`/settings`)
- Profile management (skills, location, salary targets)
- API key management (OpenAI, Anthropic, etc.)
- Notification preferences
- Theme toggle (dark/light/system)
- Data export/delete

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS + Shadcn/UI |
| State | React Query / Zustand |
| Real-time | Native SSE (EventSource) |
| Charts | Recharts / Tremor |
| Icons | Lucide React |
| Forms | React Hook Form + Zod |
| Markdown | React Markdown + Syntax Highlighting |

## Development

```bash
# Install dependencies
cd frontend
npm install

# Development server
npm run dev

# Build
npm run build

# Lint
npm run lint

# Test
npm test
```

## API Integration

The frontend connects to the FastAPI backend via:
- Base URL: `http://localhost:8000` (dev) / `https://api.alpha-nexus.com` (prod)
- WebSocket/SSE for streaming chat
- REST for all other operations

Environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Deployment

- Vercel (recommended for Next.js)
- Docker + Kubernetes for self-hosted
- Environment-specific configs in `.env.local`, `.env.production`

## Future Enhancements

- [ ] Real-time collaboration (multi-user sessions)
- [ ] Offline-first with PWA
- [ ] Mobile responsive optimizations
- [ ] Voice input/output (Web Speech API)
- [ ] Plugin system for custom agents
- [ ] Notion/Linear/GitHub integrations