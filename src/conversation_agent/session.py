from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from pydantic_ai.messages import ModelMessage

from .models import AssistantState


@dataclass
class Session:
    state: AssistantState = field(default_factory=AssistantState)
    history: list[ModelMessage] = field(default_factory=list)


_store: dict[str, Session] = {}


def create_session() -> tuple[str, Session]:
    session_id = uuid.uuid4().hex[:12]
    session = Session()
    _store[session_id] = session
    return session_id, session


def get_session(session_id: str) -> Session | None:
    return _store.get(session_id)


def get_or_create_session(session_id: str | None) -> tuple[str, Session]:
    if session_id and session_id in _store:
        return session_id, _store[session_id]
    return create_session()
