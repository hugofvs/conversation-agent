from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
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
    enum_label,
    field_to_step,
    normalize_enum_value,
)
from .rag import VectorStore
from .session import get_or_create_session, get_session

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


def apply_state_updates(state: AssistantState, patch: dict) -> None:
    """Apply a field-name → value patch to the state, validating via Pydantic.

    Works across steps: each field is routed to the step that owns it.
    After merging, missing fields are recomputed and the step advances if complete.
    """
    # Group fields by step
    by_step: dict[FlowStep, dict] = {}
    for key, value in patch.items():
        step = field_to_step(key)
        if step is None:
            continue
        by_step.setdefault(step, {})[key] = value

    for step, fields in by_step.items():
        answers = state._answers_for_step(step)
        model_cls = _STEP_ANSWERS_MAP[step]
        current = answers.model_dump()
        for key, value in fields.items():
            if key in current:
                current[key] = value
        try:
            updated = model_cls.model_validate(current)
        except Exception:
            # Retry with normalized enum values
            current = answers.model_dump()
            for key, value in fields.items():
                if key in current:
                    if isinstance(value, str):
                        current[key] = normalize_enum_value(value)
                    elif isinstance(value, list):
                        current[key] = [
                            normalize_enum_value(v) if isinstance(v, str) else v
                            for v in value
                        ]
                    else:
                        current[key] = value
            try:
                updated = model_cls.model_validate(current)
            except Exception:
                continue
        setattr(state, step.value, updated)

    # Recompute missing fields for all touched steps and advance
    for step in by_step:
        state.compute_missing_fields(step)
    # Advance from current step if complete
    state.advance_step()


def _apply_state_patch(patch: dict, state: AssistantState) -> None:
    """Apply state_patch from the LLM response as a fallback when update_state tool wasn't called."""
    if state.current_step == FlowStep.DONE:
        return
    # Only apply fields that are still None (fallback behavior)
    step = state.current_step
    answers = state._answers_for_step(step)
    filtered = {
        k: v for k, v in patch.items()
        if hasattr(answers, k) and getattr(answers, k) is None and v is not None
    }
    if filtered:
        apply_state_updates(state, filtered)


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
    option_labels = [enum_label(o) for o in options] if options else None
    response.next_question = QuestionSpec(
        field_name=field,
        question_text=question_text,
        options=options,
        option_labels=option_labels,
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


class StateUpdateRequest(BaseModel):
    session_id: str
    updates: dict


class StateUpdateResponse(BaseModel):
    state: AssistantState
    next_question: QuestionSpec | None = None


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id, session = get_or_create_session(req.session_id)
    assert _vector_store is not None

    # Snapshot state before agent run so we can detect if the LLM updated it
    missing_before = (
        list(session.state.compute_missing_fields())
        if session.state.current_step != FlowStep.DONE else []
    )
    has_prior_turns = len(session.history) > 0

    deps = AgentDeps(
        state=session.state,
        vector_store=_vector_store,
        has_prior_turns=has_prior_turns,
        missing_before=missing_before,
        user_message=req.message,
    )

    result = await agent.run(
        req.message,
        deps=deps,
        message_history=session.history,
    )

    # Append new messages to session history
    session.history.extend(result.new_messages())

    # Fallback: apply state_patch when LLM skips the update_state tool call
    if result.output.state_patch:
        _apply_state_patch(result.output.state_patch, session.state)

    _attach_next_question(result.output, session.state)

    return ChatResponse(
        session_id=session_id,
        response=result.output,
        state=session.state,
    )


@app.patch("/state", response_model=StateUpdateResponse)
async def patch_state(req: StateUpdateRequest):
    session = get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    apply_state_updates(session.state, req.updates)

    # Derive next_question from current state
    stub = AssistantResponse(mode=ResponseMode.FLOW_QUESTION, message="")
    _attach_next_question(stub, session.state)

    return StateUpdateResponse(
        state=session.state,
        next_question=stub.next_question,
    )
