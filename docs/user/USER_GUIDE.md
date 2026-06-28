# MOBIUS User Guide

## What is MOBIUS?

MOBIUS is your personal AI operating system—a intelligent partner that remembers, advises, and helps you think better. It's not a chatbot. It's designed to become your second brain.

## Getting Started

1. **Register** at `/register` with your email and password
2. **Explore the dashboard** — see today's focus, recent memories, and AI recommendations
3. **Start a conversation** — ask about architecture, startups, code, or anything
4. **Capture ideas** — say "I have an idea" in chat or use the Ideas page

## Features

### Conversation

Talk to MOBIUS naturally. It:
- Remembers context from past conversations
- Retrieves relevant memories automatically
- Explains trade-offs, not just answers
- Challenges weak assumptions respectfully
- Streams responses in real-time

### Memory

MOBIUS automatically stores important information from conversations:
- **Preferences** — "I prefer FastAPI" → stored as long-term memory
- **Projects** — references to things you're building
- **Manual memories** — add via the Memories page

Memories are retrieved semantically—MOBIUS finds what's relevant, not everything.

### Idea Capture

When you say **"I have an idea"**, MOBIUS:
1. Captures and summarizes it
2. Estimates business value and implementation effort
3. Identifies weaknesses
4. Suggests improvements
5. Creates actionable tasks
6. Links to related ideas

You can also capture ideas manually on the Ideas page.

### Voice

Upload audio for transcription (requires OpenAI API key). Voice input in chat is coming in Phase 3 mobile apps.

### Search

Search across memories, ideas, and conversations with hybrid semantic + keyword search.

### Dashboard

Your command center:
- **Today's Focus** — what MOBIUS thinks you should work on
- **Recommendations** — proactive nudges (e.g., "You haven't touched X in 4 days")
- **Quick Actions** — new chat, capture idea, add memory

## Tips for Best Results

1. **Be specific** — "Help me design auth for a FastAPI + Next.js app" beats "help with auth"
2. **Share context** — mention your projects, constraints, and goals
3. **Ask for trade-offs** — "What are the pros and cons of X vs Y?"
4. **Use idea capture** — MOBIUS gives structured startup analysis
5. **Let it remember** — say "remember that I prefer..." for explicit memory storage

## Privacy

- Your data stays in your database
- Choose your AI provider (OpenAI, Anthropic, or local Ollama)
- With Ollama, conversations never leave your machine
- MOBIUS never sends emails or takes actions without your confirmation

## Keyboard Shortcuts (Chat)

| Key | Action |
|-----|--------|
| Enter | Send message |
| Shift+Enter | New line |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MOBIUS gives generic answers | Configure an AI provider API key in `.env` |
| "Session expired" | Log in again; tokens expire after 15 minutes |
| Idea analysis is basic | Full analysis requires LLM provider configuration |
| Voice not working | Requires `OPENAI_API_KEY` for Whisper/TTS |

## Roadmap

See [IMPLEMENTATION_PLAN.md](../architecture/IMPLEMENTATION_PLAN.md) for upcoming features: coding agent, architecture review, mobile apps, calendar, email, and more.
