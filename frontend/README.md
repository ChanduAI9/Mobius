# MOBIUS Frontend

Next.js 15 web application for MOBIUS — dark-first UI for chat, dashboard, memory, ideas, knowledge, projects, and search.

## Setup

```bash
npm install
cp ../.env.example ../.env
npm run dev
```

Open http://localhost:3000

Set `NEXT_PUBLIC_API_URL` to your backend URL (default `http://localhost:8000`).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run type-check` | TypeScript validation |
| `npm run lint` | ESLint |

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard |
| `/chat` | Streaming conversation with agent selector |
| `/memories` | Memory browser |
| `/ideas` | Idea capture and analysis |
| `/knowledge` | Knowledge spaces, sources, search |
| `/projects` | Kanban, roadmap, analytics |
| `/search` | Global search |

## Structure

```
src/
├── app/           # Next.js App Router pages
├── components/    # UI and layout components
└── lib/           # API client, utilities
```

## Docker

Built via root `docker-compose.yml`. The frontend container expects `NEXT_PUBLIC_API_URL` to point to a reachable backend (use your host IP for phone/LAN access).
