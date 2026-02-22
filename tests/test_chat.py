"""Integration tests for the /chat endpoint."""
from __future__ import annotations

from pydantic_ai.models.function import FunctionModel

from conversation_agent.agent import agent
from conversation_agent.models import (
    AgeRange,
    Allergen,
    AnimeGenre,
    AssistantState,
    DietType,
    FlowStep,
    FoodAnswers,
    ProfileAnswers,
    AnimeAnswers,
    SubDubPref,
)

from .conftest import create_session, make_chat_fn, make_output_only_fn

# ── Session management ────────────────────────────────────────────────


async def test_new_session_created(client):
    fn = make_output_only_fn(
        {
            "message": "Welcome!",
            "mode": "flow_question",
            "next_question": {
                "field_name": "display_name",
                "question_text": "What's your name?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post("/chat", json={"message": "hi"})

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["state"]["current_step"] == "profile"


async def test_session_reuse(client):
    fn1 = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"display_name": "Alex"}})],
        output={
            "message": "Hi Alex!",
            "mode": "flow_question",
            "state_patch": {"display_name": "Alex"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn1)):
        r1 = await client.post("/chat", json={"message": "I'm Alex"})
    sid = r1.json()["session_id"]
    assert r1.json()["state"]["profile"]["display_name"] == "Alex"

    fn2 = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"age_range": "25_34"}})],
        output={
            "message": "Got it!",
            "mode": "flow_question",
            "state_patch": {"age_range": "25_34"},
            "next_question": {
                "field_name": "country",
                "question_text": "Where are you from?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn2)):
        r2 = await client.post(
            "/chat", json={"message": "I'm 30", "session_id": sid}
        )

    data2 = r2.json()
    assert data2["session_id"] == sid
    assert data2["state"]["profile"]["display_name"] == "Alex"
    assert data2["state"]["profile"]["age_range"] == "25_34"


async def test_unknown_session_id_creates_new(client):
    fn = make_output_only_fn(
        {
            "message": "Welcome!",
            "mode": "flow_question",
            "next_question": {
                "field_name": "display_name",
                "question_text": "What's your name?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "hi", "session_id": "bogus123"}
        )

    data = resp.json()
    assert data["session_id"] != "bogus123"
    assert data["state"]["current_step"] == "profile"


# ── Onboarding flow & update_state tool ───────────────────────────────


async def test_update_state_sets_profile_field(client):
    fn = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"display_name": "Alex"}})],
        output={
            "message": "Nice to meet you, Alex!",
            "mode": "flow_question",
            "state_patch": {"display_name": "Alex"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post("/chat", json={"message": "I'm Alex"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["profile"]["display_name"] == "Alex"
    assert data["state"]["current_step"] == "profile"
    # _attach_next_question should populate enum options for age_range
    nq = data["response"]["next_question"]
    assert nq["field_name"] == "age_range"
    assert nq["options"] == [e.value for e in AgeRange]


async def test_profile_complete_advances_to_food(client):
    state = AssistantState(
        profile=ProfileAnswers(display_name="Alex", age_range=AgeRange.AGE_25_34),
    )
    sid = create_session(state)

    fn = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"country": "US"}})],
        output={
            "message": "Profile complete! Let's talk food.",
            "mode": "flow_question",
            "state_patch": {"country": "US"},
            "next_question": {
                "field_name": "diet",
                "question_text": "What's your diet?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "I'm from the US", "session_id": sid}
        )

    data = resp.json()
    assert data["state"]["current_step"] == "food"
    # After advancing to food, response must include diet enum options
    nq = data["response"]["next_question"]
    assert nq["field_name"] == "diet"
    assert nq["options"] == [e.value for e in DietType]


async def test_multiple_fields_single_update(client):
    fn = make_chat_fn(
        tool_calls=[
            (
                "update_state",
                {
                    "patch": {
                        "display_name": "Alex",
                        "age_range": "25_34",
                        "country": "US",
                    }
                },
            )
        ],
        output={
            "message": "All profile info captured!",
            "mode": "flow_question",
            "state_patch": {
                "display_name": "Alex",
                "age_range": "25_34",
                "country": "US",
            },
            "next_question": {
                "field_name": "diet",
                "question_text": "What's your diet?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "I'm Alex, 30, from the US"}
        )

    data = resp.json()
    assert data["state"]["current_step"] == "food"
    # After advancing to food, response must include diet enum options
    nq = data["response"]["next_question"]
    assert nq["field_name"] == "diet"
    assert nq["options"] == [e.value for e in DietType]


async def test_full_flow_profile_to_done(client):
    session_id = None

    # Step 1: Fill profile
    fn = make_chat_fn(
        tool_calls=[
            (
                "update_state",
                {
                    "patch": {
                        "display_name": "Alex",
                        "age_range": "25_34",
                        "country": "US",
                    }
                },
            )
        ],
        output={
            "message": "Profile done!",
            "mode": "flow_question",
            "next_question": {
                "field_name": "diet",
                "question_text": "What's your diet?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post("/chat", json={"message": "I'm Alex, 30, US"})
    data = resp.json()
    session_id = data["session_id"]
    assert data["state"]["current_step"] == "food"

    # Step 2: Fill food
    fn = make_chat_fn(
        tool_calls=[
            (
                "update_state",
                {
                    "patch": {
                        "diet": "vegan",
                        "allergies": ["none"],
                        "spice_ok": True,
                    }
                },
            )
        ],
        output={
            "message": "Food done!",
            "mode": "flow_question",
            "next_question": {
                "field_name": "favorite_genres",
                "question_text": "Favorite genres?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat",
            json={
                "message": "vegan, no allergies, spice ok",
                "session_id": session_id,
            },
        )
    data = resp.json()
    assert data["state"]["current_step"] == "anime"

    # Step 3: Fill anime
    fn = make_chat_fn(
        tool_calls=[
            (
                "update_state",
                {
                    "patch": {
                        "favorite_genres": ["shonen"],
                        "sub_or_dub": "sub",
                        "top_3_anime": ["Naruto"],
                    }
                },
            )
        ],
        output={"message": "All done!", "mode": "done"},
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat",
            json={"message": "shonen, sub, Naruto", "session_id": session_id},
        )
    data = resp.json()
    assert data["state"]["current_step"] == "done"


# ── State patch fallback ──────────────────────────────────────────────


async def test_state_patch_fallback(client):
    fn = make_output_only_fn(
        {
            "message": "I'll call you Alex!",
            "mode": "flow_question",
            "state_patch": {"display_name": "Alex"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post("/chat", json={"message": "My name is Alex"})

    data = resp.json()
    # _apply_state_patch must have been called — display_name is set
    assert data["state"]["profile"]["display_name"] == "Alex"
    # _attach_next_question picks up next missing field (age_range) with enum options
    nq = data["response"]["next_question"]
    assert nq["field_name"] == "age_range"
    assert nq["options"] == [e.value for e in AgeRange]


async def test_state_patch_no_overwrite(client):
    state = AssistantState(profile=ProfileAnswers(display_name="Alex"))
    sid = create_session(state)

    fn = make_output_only_fn(
        {
            "message": "Hello Alex!",
            "mode": "flow_question",
            "state_patch": {"display_name": "NewName"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "call me NewName", "session_id": sid}
        )

    data = resp.json()
    assert data["state"]["profile"]["display_name"] == "Alex"


async def test_state_patch_advances_step(client):
    state = AssistantState(
        profile=ProfileAnswers(display_name="Alex", age_range=AgeRange.AGE_25_34),
    )
    sid = create_session(state)

    fn = make_output_only_fn(
        {
            "message": "Great, moving to food!",
            "mode": "flow_question",
            "state_patch": {"country": "US"},
            "next_question": {
                "field_name": "diet",
                "question_text": "What's your diet?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "I'm from the US", "session_id": sid}
        )

    data = resp.json()
    # _apply_state_patch must have been called — step advanced to food
    assert data["state"]["current_step"] == "food"
    # _attach_next_question picks up food step's first missing field with enum options
    nq = data["response"]["next_question"]
    assert nq["field_name"] == "diet"
    assert nq["options"] == [e.value for e in DietType]


# ── Next question attachment ──────────────────────────────────────────


async def test_next_question_options_attached(client):
    state = AssistantState(profile=ProfileAnswers(display_name="Alex"))
    sid = create_session(state)

    fn = make_output_only_fn(
        {
            "message": "How old are you?",
            "mode": "flow_question",
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "next", "session_id": sid}
        )

    nq = resp.json()["response"]["next_question"]
    assert nq["field_name"] == "age_range"
    assert nq["options"] == [e.value for e in AgeRange]
    assert nq["multi_select"] is False


async def test_allergies_multi_select(client):
    state = AssistantState(
        current_step=FlowStep.FOOD,
        profile=ProfileAnswers(
            display_name="Alex", age_range=AgeRange.AGE_25_34, country="US"
        ),
        food=FoodAnswers(diet=DietType.VEGAN),
    )
    sid = create_session(state)

    fn = make_output_only_fn(
        {
            "message": "Any allergies?",
            "mode": "flow_question",
            "next_question": {
                "field_name": "allergies",
                "question_text": "Any allergies?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "next", "session_id": sid}
        )

    nq = resp.json()["response"]["next_question"]
    assert nq["field_name"] == "allergies"
    assert nq["multi_select"] is True
    assert nq["default_value"] == "none"


# ── Response modes ────────────────────────────────────────────────────


async def test_answer_mode_with_rag(client):
    fn = make_chat_fn(
        tool_calls=[("rag_search", {"query": "what is this app?"})],
        output={
            "message": "Based on my search, this app helps with onboarding.",
            "mode": "answer",
            "sources": [
                {
                    "title": "Test Doc",
                    "content": "Test content about the topic.",
                    "score": 0.95,
                }
            ],
        },
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "what is this app?"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["response"]["mode"] == "answer"
    assert len(data["response"]["sources"]) > 0


async def test_guardrail_mode(client):
    fn = make_output_only_fn(
        {"message": "I can only help with onboarding.", "mode": "guardrail"}
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "what's the meaning of life?"}
        )

    data = resp.json()
    assert data["response"]["mode"] == "guardrail"
    assert data["response"]["next_question"] is None


async def test_done_mode(client):
    state = AssistantState(
        current_step=FlowStep.DONE,
        profile=ProfileAnswers(
            display_name="Alex", age_range=AgeRange.AGE_25_34, country="US"
        ),
        food=FoodAnswers(
            diet=DietType.VEGAN, allergies=[Allergen.NUTS], spice_ok=True
        ),
        anime=AnimeAnswers(
            favorite_genres=[AnimeGenre.SHONEN],
            sub_or_dub=SubDubPref.SUB,
            top_3_anime=["Naruto"],
        ),
    )
    sid = create_session(state)

    fn = make_output_only_fn(
        {"message": "All done! Here's your summary.", "mode": "done"}
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post(
            "/chat", json={"message": "summary", "session_id": sid}
        )

    data = resp.json()
    assert data["response"]["mode"] == "done"
    assert data["state"]["current_step"] == "done"


# ── Edge cases ────────────────────────────────────────────────────────


async def test_missing_message_field_422(client):
    resp = await client.post("/chat", json={})
    assert resp.status_code == 422


async def test_empty_message(client):
    fn = make_output_only_fn(
        {
            "message": "Welcome! What's your name?",
            "mode": "flow_question",
            "next_question": {
                "field_name": "display_name",
                "question_text": "What's your name?",
            },
        }
    )
    with agent.override(model=FunctionModel(fn)):
        resp = await client.post("/chat", json={"message": ""})

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "response" in data


async def test_concurrent_sessions_independent(client):
    fn1 = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"display_name": "Alice"}})],
        output={
            "message": "Hi Alice!",
            "mode": "flow_question",
            "state_patch": {"display_name": "Alice"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn1)):
        r1 = await client.post("/chat", json={"message": "I'm Alice"})

    fn2 = make_chat_fn(
        tool_calls=[("update_state", {"patch": {"display_name": "Bob"}})],
        output={
            "message": "Hi Bob!",
            "mode": "flow_question",
            "state_patch": {"display_name": "Bob"},
            "next_question": {
                "field_name": "age_range",
                "question_text": "How old are you?",
            },
        },
    )
    with agent.override(model=FunctionModel(fn2)):
        r2 = await client.post("/chat", json={"message": "I'm Bob"})

    d1, d2 = r1.json(), r2.json()
    assert d1["session_id"] != d2["session_id"]
    assert d1["state"]["profile"]["display_name"] == "Alice"
    assert d2["state"]["profile"]["display_name"] == "Bob"
