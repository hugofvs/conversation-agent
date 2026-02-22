# Conversation Agent

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Svelte 5](https://img.shields.io/badge/Svelte-5-FF3E00.svg)](https://svelte.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.2-38B2AC.svg)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](#testing)

An AI-powered onboarding assistant that guides users through a multi-step profile setup via natural conversation. 

## Features

- **3-step onboarding flow:** Profile, Food preferences, and Anime tastes, collected conversationally
- **Intent classification:** The LLM distinguishes between answers, questions, and off-topic messages (GUARDRAIL)
- **RAG knowledge base:** Answers questions during the onboarding process using semantic search
- **Editable side panel:** Users can fill fields directly via a form and sync back into the conversation
- **Output validation:** Ensures the LLM always calls the state update tool when the user provides an answer

## Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API key

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/hugofvs/conversation-agent.git
cd conversation-agent

# Backend
uv sync

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure environment

Create a `.env` file in the project root:

```
OPENAI_API_KEY=...
```

### 3. Build the frontend

```bash
cd frontend && npm run build && cd ..
```

### 4. Run

```bash
uv run uvicorn conversation_agent.app:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

### Development mode

Run the backend and frontend dev server separately for hot reload:

```bash
# Terminal 1 - Backend
uv run uvicorn conversation_agent.app:app --reload

# Terminal 2 - Frontend (proxies /chat and /state to backend)
cd frontend && npm run dev
```

The frontend dev server runs on [http://localhost:5173](http://localhost:5173) and proxies API requests to the backend.

## Project Structure

```
conversation-agent/
├── src/conversation_agent/      # Python backend
│   ├── agent.py                 # Pydantic AI agent, system prompt, tools
│   ├── app.py                   # FastAPI endpoints and state logic
│   ├── models.py                # Pydantic models, enums, state machine
│   ├── rag.py                   # Vector store for semantic search
│   └── session.py               # In-memory session management
│
├── tests/                       # Python test suite
│   ├── conftest.py              # Fixtures, mock model helpers
│   ├── test_chat.py             # /chat endpoint integration tests
│   ├── test_state.py            # /state endpoint and state logic tests
│   ├── test_models.py           # Model and enum utility tests
│   └── test_rag.py              # VectorStore unit tests
│
├── frontend/src/                # Svelte 5 frontend
│   ├── App.svelte               # Main app with chat and form logic
│   ├── components/              # ChatInput, SidePanel, FormField, etc.
│   └── lib/                     # API clients and field definitions
│
├── data/
│   └── rag_corpus.json          # Knowledge base (15 documents)
│
└── pyproject.toml               # Python dependencies and config
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the frontend |
| `POST` | `/chat` | Send a message and get an AI response with state updates |
| `PATCH` | `/state` | Update onboarding fields directly (bypasses LLM) |

### POST /chat

```json
{
  "message": "I'm Hugo, 30 years old",
  "session_id": "abc123",
  "auto": false
}
```

Response includes the assistant message, response mode (`flow_question`, `answer`, `guardrail`, `done`), updated state, and optionally the next question spec with field options.

### PATCH /state

```json
{
  "session_id": "abc123",
  "updates": { "display_name": "Hugo", "age_range": "25_34" }
}
```

Returns the updated state and next question. Injects synthetic messages into conversation history so the LLM stays in sync.

## Testing

### Backend

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=conversation_agent --cov-report=term-missing
```

### Frontend

```bash
cd frontend

# Run tests once
npm run test:run

# Run with coverage
npx vitest run --coverage

# Watch mode
npm test
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | OpenAI gpt-4o-mini via [Pydantic AI](https://ai.pydantic.dev) |
| Embeddings | OpenAI text-embedding-3-small |
| Backend | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| Frontend | [Svelte 5](https://svelte.dev) + [Vite](https://vite.dev) |
| Styling | [Tailwind CSS 4](https://tailwindcss.com) |
| Validation | [Pydantic](https://docs.pydantic.dev) |
| Testing | [pytest](https://docs.pytest.org) + [Vitest](https://vitest.dev) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## License

This project is provided as-is for educational and demonstration purposes.
