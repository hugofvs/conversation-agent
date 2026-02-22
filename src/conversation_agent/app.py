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
from .models import (
    AgeRange,
    Allergen,
    AnimeGenre,
    AssistantResponse,
    AssistantState,
    DietType,
    FlowStep,
    QuestionSpec,
    ResponseMode,
    SubDubPref,
    _STEP_ANSWERS_MAP,
)
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


# (options, default_value, multi_select) for each structured field
_FIELD_OPTIONS: dict[str, tuple[list[str], str | None, bool]] = {
    "age_range":       ([e.value for e in AgeRange], None, False),
    "diet":            ([e.value for e in DietType], None, False),
    "allergies":       ([e.value for e in Allergen], "none", True),
    "spice_ok":        (["yes", "no"], None, False),
    "favorite_genres": ([e.value for e in AnimeGenre], None, True),
    "sub_or_dub":      ([e.value for e in SubDubPref], None, False),
}


def _apply_state_patch(patch: dict, state: AssistantState) -> None:
    """Apply state_patch from the LLM response as a fallback when update_state tool wasn't called."""
    step = state.current_step
    if step == FlowStep.DONE:
        return
    answers = state._answers_for_step(step)
    model_cls = _STEP_ANSWERS_MAP[step]
    current = answers.model_dump()
    changed = False
    for key, value in patch.items():
        if key in current and current[key] is None and value is not None:
            current[key] = value
            changed = True
    if not changed:
        return
    try:
        updated = model_cls.model_validate(current)
    except Exception:
        return
    setattr(state, step.value, updated)
    missing = state.compute_missing_fields()
    if not missing:
        state.advance_step()


def _attach_next_question(
    response: AssistantResponse, state: AssistantState
) -> None:
    """Deterministically attach options to flow_question responses."""
    if response.mode != ResponseMode.FLOW_QUESTION:
        return
    missing = state.compute_missing_fields()
    if not missing:
        return
    field = missing[0]
    question_text = (
        response.next_question.question_text
        if response.next_question
        else ""
    )
    options, default, multi = _FIELD_OPTIONS.get(field, (None, None, False))
    response.next_question = QuestionSpec(
        field_name=field,
        question_text=question_text,
        options=options,
        default_value=default,
        multi_select=multi,
    )


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

    # Debug: check state after agent run
    import sys
    print(f"[DEBUG] profile after run: {session.state.profile.model_dump()}", file=sys.stderr)
    print(f"[DEBUG] current_step: {session.state.current_step}", file=sys.stderr)
    for msg in result.new_messages():
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                ptype = type(part).__name__
                if 'Tool' in ptype:
                    print(f"[DEBUG] {ptype}: {getattr(part, 'tool_name', '')} {getattr(part, 'content', '')[:200]}", file=sys.stderr)

    # Apply state_patch as fallback when LLM skips the update_state tool call
    if result.output.state_patch:
        _apply_state_patch(result.output.state_patch, session.state)

    _attach_next_question(result.output, session.state)

    return ChatResponse(
        session_id=session_id,
        response=result.output,
        state=session.state,
    )
