"""Unit tests for models.py utility functions and state logic."""
from __future__ import annotations

from conversation_agent.models import (
    AssistantState,
    FlowStep,
    ProfileAnswers,
    FoodAnswers,
    AnimeAnswers,
    AgeRange,
    DietType,
    Allergen,
    AnimeGenre,
    SubDubPref,
    enum_label,
    normalize_enum_value,
    field_to_step,
)


# ── enum_label ────────────────────────────────────────────────────────


def test_enum_label_special_cases():
    assert enum_label("under_18") == "Under 18"
    assert enum_label("25_34") == "25-34"
    assert enum_label("45_plus") == "45+"
    assert enum_label("slice_of_life") == "Slice of Life"
    assert enum_label("sci_fi") == "Sci-Fi"


def test_enum_label_generic():
    assert enum_label("omnivore") == "Omnivore"
    assert enum_label("shonen") == "Shonen"


# ── normalize_enum_value ──────────────────────────────────────────────


def test_normalize_enum_value_special_cases():
    assert normalize_enum_value("Under 18") == "under_18"
    assert normalize_enum_value("25-34") == "25_34"
    assert normalize_enum_value("45+") == "45_plus"
    assert normalize_enum_value("Slice of Life") == "slice_of_life"
    assert normalize_enum_value("Sci-Fi") == "sci_fi"


def test_normalize_enum_value_generic():
    assert normalize_enum_value("Omnivore") == "omnivore"
    assert normalize_enum_value("some value") == "some_value"


# ── field_to_step ─────────────────────────────────────────────────────


def test_field_to_step_mappings():
    assert field_to_step("display_name") == FlowStep.PROFILE
    assert field_to_step("age_range") == FlowStep.PROFILE
    assert field_to_step("country") == FlowStep.PROFILE
    assert field_to_step("diet") == FlowStep.FOOD
    assert field_to_step("allergies") == FlowStep.FOOD
    assert field_to_step("spice_ok") == FlowStep.FOOD
    assert field_to_step("favorite_genres") == FlowStep.ANIME
    assert field_to_step("sub_or_dub") == FlowStep.ANIME
    assert field_to_step("top_3_anime") == FlowStep.ANIME


def test_field_to_step_unknown():
    assert field_to_step("nonexistent") is None


# ── AssistantState ────────────────────────────────────────────────────


def test_compute_missing_fields_all_missing():
    state = AssistantState()
    missing = state.compute_missing_fields()
    assert missing == ["display_name", "age_range", "country"]


def test_compute_missing_fields_partial():
    state = AssistantState(profile=ProfileAnswers(display_name="Hugo"))
    missing = state.compute_missing_fields()
    assert "display_name" not in missing
    assert "age_range" in missing
    assert "country" in missing


def test_compute_missing_fields_none_when_complete():
    state = AssistantState(
        profile=ProfileAnswers(
            display_name="Hugo", age_range=AgeRange.AGE_25_34, country="PT"
        )
    )
    missing = state.compute_missing_fields()
    assert missing == []


def test_compute_missing_fields_done_step():
    state = AssistantState(current_step=FlowStep.DONE)
    assert state.compute_missing_fields() == []


def test_advance_step_profile_to_food():
    state = AssistantState(
        profile=ProfileAnswers(
            display_name="Hugo", age_range=AgeRange.AGE_25_34, country="PT"
        )
    )
    state.advance_step()
    assert state.current_step == FlowStep.FOOD


def test_advance_step_stays_if_incomplete():
    state = AssistantState(profile=ProfileAnswers(display_name="Hugo"))
    state.advance_step()
    assert state.current_step == FlowStep.PROFILE


def test_advance_step_to_done():
    state = AssistantState(
        current_step=FlowStep.ANIME,
        anime=AnimeAnswers(
            favorite_genres=[AnimeGenre.SHONEN],
            sub_or_dub=SubDubPref.SUB,
            top_3_anime=["Naruto"],
        ),
    )
    state.advance_step()
    assert state.current_step == FlowStep.DONE


def test_advance_step_noop_when_done():
    state = AssistantState(current_step=FlowStep.DONE)
    state.advance_step()
    assert state.current_step == FlowStep.DONE
