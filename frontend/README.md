# Disha — Frontend

Market Intelligence & Career Optimization for India's AI/ML job landscape.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 3.4 |
| Components | Shadcn/UI (planned) |

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Landing page
│   └── globals.css        # Tailwind imports
├── components/            # Shared components
│   ├── chat/              # Chat interface components
│   ├── jobs/              # Job display components
│   └── ui/                # UI primitives (Shadcn/UI)
├── hooks/                 # Custom React hooks (useChat SSE)
└── types/                 # TypeScript type definitions
```

## Development

```bash
# Install dependencies
npm install

# Development server (default: http://localhost:3000)
npm run dev

# Production build
npm run build

# Lint
npm run lint
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Non-streaming pipeline execution |
| `/api/chat/stream` | POST | SSE streaming pipeline execution |
| `/health` | GET | Health check |

Set the API URL in `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## SSE Streaming

The primary interaction uses `POST /api/chat/stream` with Server-Sent Events (SSE).
Since the endpoint uses POST, the frontend uses `fetch()` with `ReadableStream`
instead of the native `EventSource` API.

Each SSE event contains:

- Agent routing state (`step`, `current_agent`, `routing_key`)
- Structured data (`job_openings[]`, `career_recommendations[]`) when available
- Final answer (`final_answer`, `answer_confidence`, `citations[]`) on completion
