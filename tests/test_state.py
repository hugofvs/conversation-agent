"""Tests for PATCH /state endpoint and apply_state_updates edge cases."""
from __future__ import annotations

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from conversation_agent.agent import agent
from conversation_agent.models import (
    AgeRange,
    AssistantState,
    FlowStep,
    ProfileAnswers,
    FoodAnswers,
    DietType,
    Allergen,
)
from conversation_agent.app import (
    apply_state_updates,
    _display_value,
    _inject_form_history,
)
from conversation_agent.session import Session

from .conftest import create_session, make_output_only_fn


# ── PATCH /state endpoint ─────────────────────────────────────────────


async def test_patch_state_updates_field(client):
    sid = create_session(AssistantState())

    resp = await client.patch(
        "/state",
        json={"session_id": sid, "updates": {"display_name": "Hugo"}},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["profile"]["display_name"] == "Hugo"


async def test_patch_state_returns_next_question(client):
    sid = create_session(AssistantState(
        profile=ProfileAnswers(display_name="Hugo"),
    ))

    resp = await client.patch(
        "/state",
        json={"session_id": sid, "updates": {}},
    )

    data = resp.json()
    nq = data["next_question"]
    assert nq is not None
    assert nq["field_name"] == "age_range"


async def test_patch_state_advances_step(client):
    state = AssistantState(
        profile=ProfileAnswers(
            display_name="Hugo", age_range=AgeRange.AGE_25_34,
        ),
    )
    sid = create_session(state)

    resp = await client.patch(
        "/state",
        json={"session_id": sid, "updates": {"country": "Portugal"}},
    )

    data = resp.json()
    assert data["state"]["current_step"] == "food"


async def test_patch_state_not_found(client):
    resp = await client.patch(
        "/state",
        json={"session_id": "nonexistent", "updates": {"display_name": "X"}},
    )
    assert resp.status_code == 404


async def test_patch_state_injects_history(client):
    from conversation_agent import session as session_module

    sid = create_session(AssistantState())

    await client.patch(
        "/state",
        json={"session_id": sid, "updates": {"display_name": "Hugo"}},
    )

    session = session_module._store[sid]
    assert len(session.history) == 2
    # First is a ModelRequest with the field summary
    req_msg = session.history[0]
    assert isinstance(req_msg, ModelRequest)
    assert "display_name = Hugo" in req_msg.parts[0].content
    # Second is a ModelResponse acknowledgment
    resp_msg = session.history[1]
    assert isinstance(resp_msg, ModelResponse)


async def test_patch_state_empty_updates_no_history(client):
    from conversation_agent import session as session_module

    sid = create_session(AssistantState())

    await client.patch(
        "/state",
        json={"session_id": sid, "updates": {}},
    )

    session = session_module._store[sid]
    assert len(session.history) == 0


async def test_patch_state_with_enum_label(client):
    """Enum values like '25_34' are accepted via normalize fallback."""
    sid = create_session(AssistantState())

    resp = await client.patch(
        "/state",
        json={"session_id": sid, "updates": {"age_range": "25-34"}},
    )

    data = resp.json()
    assert data["state"]["profile"]["age_range"] == "25_34"


# ── apply_state_updates edge cases ────────────────────────────────────


def test_apply_state_updates_unknown_field():
    state = AssistantState()
    apply_state_updates(state, {"nonexistent_field": "value"})
    # Should be a no-op — no error
    assert state.profile.display_name is None


def test_apply_state_updates_normalize_enum():
    state = AssistantState()
    # Human-readable label that needs normalization
    apply_state_updates(state, {"age_range": "25-34"})
    assert state.profile.age_range == AgeRange.AGE_25_34


def test_apply_state_updates_normalize_list():
    state = AssistantState(current_step=FlowStep.FOOD)
    apply_state_updates(state, {"allergies": ["Dairy", "Nuts"]})
    assert state.food.allergies == [Allergen.DAIRY, Allergen.NUTS]


def test_apply_state_updates_cross_step():
    state = AssistantState()
    apply_state_updates(state, {
        "display_name": "Hugo",
        "diet": "vegan",
    })
    assert state.profile.display_name == "Hugo"
    assert state.food.diet == DietType.VEGAN


def test_apply_state_updates_invalid_value_skips():
    state = AssistantState()
    # Completely invalid value should be skipped via continue
    apply_state_updates(state, {"age_range": "not_a_real_age_range_value_at_all"})
    assert state.profile.age_range is None


# ── _display_value ────────────────────────────────────────────────────


def test_display_value_string():
    assert _display_value("25_34") == "25-34"


def test_display_value_bool():
    assert _display_value(True) == "yes"
    assert _display_value(False) == "no"


def test_display_value_list():
    assert _display_value(["dairy", "nuts"]) == "Dairy, Nuts"


# ── _inject_form_history ──────────────────────────────────────────────


def test_inject_form_history():
    session = Session()
    _inject_form_history(session, {"display_name": "Hugo", "age_range": "25_34"})
    assert len(session.history) == 2
    assert "display_name = Hugo" in session.history[0].parts[0].content
    assert "age_range = 25-34" in session.history[0].parts[0].content


# ── auto flag ─────────────────────────────────────────────────────────


async def test_auto_flag_passed_to_agent(client):
    fn = make_output_only_fn({
        "message": "Welcome!",
        "mode": "flow_question",
        "next_question": {
            "field_name": "display_name",
            "question_text": "What's your name?",
        },
    })
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "hi", "auto": True}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["response"]["message"] == "Welcome!"
