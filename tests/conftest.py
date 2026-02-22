from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from conversation_agent import app as app_module
from conversation_agent import session as session_module
from conversation_agent.app import app
from conversation_agent.models import AssistantState, RagSource
from conversation_agent.session import Session


# ---------------------------------------------------------------------------
# MockVectorStore — duck-typed replacement for VectorStore
# ---------------------------------------------------------------------------

class MockVectorStore:
    """Returns canned RagSource results without calling any embedding API."""

    async def search(self, query: str, top_k: int = 3) -> list[RagSource]:
        return [
            RagSource(
                title="Test Doc",
                content="Test content about the topic.",
                score=0.95,
            ),
        ]


# ---------------------------------------------------------------------------
# Test lifespan (no-op, no real embeddings)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _test_lifespan(app_):
    app_module._vector_store = MockVectorStore()
    yield


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
    app.router.lifespan_context = _test_lifespan
    app_module._vector_store = MockVectorStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_sessions():
    session_module._store.clear()
    yield
    session_module._store.clear()


# ---------------------------------------------------------------------------
# Session pre-population helper
# ---------------------------------------------------------------------------

def create_session(state: AssistantState) -> str:
    """Insert a Session with the given state directly into the store."""
    session_id = uuid.uuid4().hex[:12]
    session_module._store[session_id] = Session(state=state)
    return session_id


# ---------------------------------------------------------------------------
# FunctionModel helpers
# ---------------------------------------------------------------------------

def _output_response(output: dict[str, Any], agent_info: AgentInfo) -> ModelResponse:
    """Build a ModelResponse that calls the agent's output tool."""
    tool = agent_info.output_tools[0]
    args = output
    if tool.outer_typed_dict_key:
        args = {tool.outer_typed_dict_key: args}
    return ModelResponse(parts=[ToolCallPart(tool_name=tool.name, args=args)])


def make_chat_fn(
    tool_calls: list[tuple[str, dict[str, Any]]],
    output: dict[str, Any],
):
    """Two-step callback: first call issues tool calls, second emits structured output."""
    call_count = 0

    def chat_fn(messages: list[ModelMessage], agent_info: AgentInfo) -> ModelResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            parts = [
                ToolCallPart(tool_name=name, args=args) for name, args in tool_calls
            ]
            return ModelResponse(parts=parts)
        return _output_response(output, agent_info)

    return chat_fn


def make_output_only_fn(output: dict[str, Any]):
    """Single-step callback: immediately returns structured output (no tool calls)."""

    def chat_fn(messages: list[ModelMessage], agent_info: AgentInfo) -> ModelResponse:
        return _output_response(output, agent_info)

    return chat_fn
