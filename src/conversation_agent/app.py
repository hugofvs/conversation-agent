from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic_ai import Embedder

from .agent import AgentDeps, agent
from .models import AssistantResponse, AssistantState
from .rag import VectorStore
from .session import get_or_create_session

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
CORPUS_PATH = PROJECT_ROOT / "data" / "rag_corpus.json"

_vector_store: VectorStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _vector_store
    embedder = Embedder("openai:text-embedding-3-small")
    _vector_store = VectorStore(embedder)
    await _vector_store.load_corpus(CORPUS_PATH)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: AssistantResponse
    state: AssistantState


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id, session = get_or_create_session(req.session_id)
    assert _vector_store is not None

    deps = AgentDeps(state=session.state, vector_store=_vector_store)

    result = await agent.run(
        req.message,
        deps=deps,
        message_history=session.history,
    )

    # Append new messages to session history
    session.history.extend(result.new_messages())

    return ChatResponse(
        session_id=session_id,
        response=result.output,
        state=session.state,
    )
