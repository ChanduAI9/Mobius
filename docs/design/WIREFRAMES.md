# MOBIUS UI/UX Wireframes

Design language: **Dark-first**, minimal, professional. Accent color: electric cyan (`#00D4FF`). Typography: Inter / system-ui.

## Design Tokens

| Token | Value |
|-------|-------|
| Background | `#0A0A0F` |
| Surface | `#12121A` |
| Surface Elevated | `#1A1A24` |
| Border | `#2A2A3A` |
| Text Primary | `#F0F0F5` |
| Text Secondary | `#8888A0` |
| Accent | `#00D4FF` |
| Success | `#00E676` |
| Warning | `#FFB300` |
| Error | `#FF5252` |

## Layout Shell

```
┌─────────────────────────────────────────────────────────────────┐
│  ◈ MOBIUS                              🔍 Search    👤 Profile  │
├──────────┬──────────────────────────────────────────────────────┤
│          │                                                      │
│  ◈ Dash  │                                                      │
│  💬 Chat  │              MAIN CONTENT AREA                       │
│  🧠 Memory│                                                      │
│  💡 Ideas │                                                      │
│  🔍 Search│                                                      │
│          │                                                      │
│  ─────── │                                                      │
│  ⚙ Settings                                                     │
│          │                                                      │
└──────────┴──────────────────────────────────────────────────────┘
     240px                    flex-1
```

## Dashboard (`/`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Good evening, Saichandu                                        │
│  Sunday, June 28 · 3 conversations today                          │
├─────────────────────────────┬───────────────────────────────────┤
│  TODAY'S FOCUS              │  AI RECOMMENDATIONS               │
│  ┌─────────────────────┐   │  ┌─────────────────────────────┐  │
│  │ Continue Meet2Discuss│   │  │ ⚡ Haven't touched Meet2     │  │
│  │ authentication       │   │  │    Discuss in 4 days       │  │
│  │                      │   │  │    [Continue →]            │  │
│  │ Last: 4 days ago     │   │  └─────────────────────────────┘  │
│  │ [Open Project]       │   │  ┌─────────────────────────────┐  │
│  └─────────────────────┘   │  │ 💡 2 ideas awaiting review   │  │
│                             │  └─────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────────┤
│  RECENT MEMORIES            │  RECENT IDEAS                     │
│  • Prefers FastAPI...       │  • Async video meetings           │
│  • MOBIUS uses pgvector     │  • AI code review tool            │
│  • Startup: Meet2Discuss    │  • Personal knowledge graph       │
├─────────────────────────────┴───────────────────────────────────┤
│  QUICK ACTIONS                                                  │
│  [💬 New Chat]  [💡 Capture Idea]  [🎤 Voice]  [📝 Add Memory]  │
└─────────────────────────────────────────────────────────────────┘
```

## Chat (`/chat`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Conversations          │  Architecture Discussion              │
│  ┌──────────────────┐   │  ─────────────────────────────────    │
│  │ + New Chat       │   │                                       │
│  ├──────────────────┤   │  You                          2:30 PM │
│  │ Architecture...  │◀──│  Help me design auth for MOBIUS      │
│  │ Idea: async vid  │   │                                       │
│  │ Python tips      │   │  MOBIUS                     2:30 PM   │
│  └──────────────────┘   │  ┌─────────────────────────────────┐  │
│                         │  │ For MOBIUS authentication, I'd  │  │
│                         │  │ recommend JWT with short-lived  │  │
│                         │  │ access tokens and refresh...    │  │
│                         │  │                                 │  │
│                         │  │ **Trade-offs:**                 │  │
│                         │  │ • JWT: stateless, scalable      │  │
│                         │  │ • Sessions: easier revocation   │  │
│                         │  └─────────────────────────────────┘  │
│                         │                                       │
│                         │  ┌───────────────────────────┐ 🎤 ➤  │
│                         │  │ Ask MOBIUS anything...    │       │
│                         │  └───────────────────────────┘       │
└─────────────────────────┴───────────────────────────────────────┘
```

Streaming indicator: pulsing cyan dot while MOBIUS thinks.

## Memories (`/memories`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Memories                                    [+ Add Memory]     │
│  Filter: [All Tiers ▼] [All Categories ▼]  🔍 Search...        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⭐ 0.9  LONG-TERM · preference · 2 days ago              │   │
│  │ Prefers FastAPI over Flask for new Python projects       │   │
│  │ #python #coding #preference                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⭐ 0.7  PROJECT · architecture · 1 week ago              │   │
│  │ MOBIUS uses PostgreSQL with pgvector for semantic search │   │
│  │ #mobius #architecture                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Ideas (`/ideas`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Ideas                                      [+ Capture Idea]      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 💡 Async Video Meeting Platform          status: new   │   │
│  │ Summary: Platform for async video discussions...       │   │
│  │                                                         │   │
│  │ Business Value: HIGH    Effort: MEDIUM    Feasibility: 70%│  │
│  │                                                         │   │
│  │ Weaknesses: Crowded market, needs differentiation      │   │
│  │ [View Analysis] [Create Tasks] [Discuss with MOBIUS]   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Search (`/search`)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍  authentication architecture                                │
├─────────────────────────────────────────────────────────────────┤
│  [All] [Memories] [Ideas] [Conversations]                        │
│                                                                  │
│  MEMORY · 89% match                                              │
│  JWT with refresh token rotation for MOBIUS auth                 │
│                                                                  │
│  CONVERSATION · 76% match                                        │
│  Architecture Discussion — "...OAuth vs JWT trade-offs..."       │
│                                                                  │
│  IDEA · 65% match                                                │
│  Zero-trust auth for microservices                               │
└─────────────────────────────────────────────────────────────────┘
```

## Auth Pages

Login and register: centered card on dark background with MOBIUS logo (◈), minimal fields, cyan CTA button.

## Mobile Considerations (Phase 3)

- Bottom tab bar: Dashboard, Chat, Capture (+), Memories, Profile
- Swipe gestures for conversation list
- Voice button prominently placed in chat input

## Accessibility

- WCAG 2.1 AA contrast ratios
- Keyboard navigation for all interactive elements
- Screen reader labels on icon buttons
- Focus rings visible in accent color
