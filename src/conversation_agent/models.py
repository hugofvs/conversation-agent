from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class FlowStep(str, Enum):
    PROFILE = "profile"
    FOOD = "food"
    ANIME = "anime"
    DONE = "done"


class AgeRange(str, Enum):
    UNDER_18 = "under_18"
    AGE_18_24 = "18_24"
    AGE_25_34 = "25_34"
    AGE_35_44 = "35_44"
    AGE_45_PLUS = "45_plus"


class DietType(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    HALAL = "halal"
    KOSHER = "kosher"
    OTHER = "other"


class Allergen(str, Enum):
    DAIRY = "dairy"
    GLUTEN = "gluten"
    NUTS = "nuts"
    SHELLFISH = "shellfish"
    SOY = "soy"
    EGGS = "eggs"
    NONE = "none"


class AnimeGenre(str, Enum):
    SHONEN = "shonen"
    SHOJO = "shojo"
    SEINEN = "seinen"
    ISEKAI = "isekai"
    MECHA = "mecha"
    SLICE_OF_LIFE = "slice_of_life"
    HORROR = "horror"
    ROMANCE = "romance"
    COMEDY = "comedy"
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"


class SubDubPref(str, Enum):
    SUB = "sub"
    DUB = "dub"
    BOTH = "both"


class ResponseMode(str, Enum):
    FLOW_QUESTION = "flow_question"
    ANSWER = "answer"
    GUARDRAIL = "guardrail"
    DONE = "done"


# ── Step answer models ─────────────────────────────────────────────────

class ProfileAnswers(BaseModel):
    display_name: str | None = None
    age_range: AgeRange | None = None
    country: str | None = None


class FoodAnswers(BaseModel):
    diet: DietType | None = None
    allergies: list[Allergen] | None = None
    spice_ok: bool | None = None


class AnimeAnswers(BaseModel):
    favorite_genres: list[AnimeGenre] | None = None
    sub_or_dub: SubDubPref | None = None
    top_3_anime: list[str] | None = None


# ── State models ───────────────────────────────────────────────────────

class StepStatus(BaseModel):
    is_complete: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    last_question_asked: str | None = None


_STEP_ANSWERS_MAP: dict[FlowStep, type[BaseModel]] = {
    FlowStep.PROFILE: ProfileAnswers,
    FlowStep.FOOD: FoodAnswers,
    FlowStep.ANIME: AnimeAnswers,
}

_STEP_ORDER = [FlowStep.PROFILE, FlowStep.FOOD, FlowStep.ANIME]

_FIELD_TO_STEP: dict[str, FlowStep] = {
    field_name: step
    for step, model_cls in _STEP_ANSWERS_MAP.items()
    for field_name in model_cls.model_fields
}


def field_to_step(field_name: str) -> FlowStep | None:
    """Map a field name to the FlowStep that owns it."""
    return _FIELD_TO_STEP.get(field_name)


class AssistantState(BaseModel):
    current_step: FlowStep = FlowStep.PROFILE
    profile: ProfileAnswers = Field(default_factory=ProfileAnswers)
    food: FoodAnswers = Field(default_factory=FoodAnswers)
    anime: AnimeAnswers = Field(default_factory=AnimeAnswers)
    profile_status: StepStatus = Field(default_factory=StepStatus)
    food_status: StepStatus = Field(default_factory=StepStatus)
    anime_status: StepStatus = Field(default_factory=StepStatus)

    def _answers_for_step(self, step: FlowStep) -> BaseModel:
        return getattr(self, step.value)

    def _status_for_step(self, step: FlowStep) -> StepStatus:
        return getattr(self, f"{step.value}_status")

    def compute_missing_fields(self, step: FlowStep | None = None) -> list[str]:
        step = step or self.current_step
        if step == FlowStep.DONE:
            return []
        answers = self._answers_for_step(step)
        missing = [
            name
            for name, field_info in answers.model_fields.items()
            if getattr(answers, name) is None
        ]
        status = self._status_for_step(step)
        status.missing_fields = missing
        status.is_complete = len(missing) == 0
        return missing

    def advance_step(self) -> None:
        if self.current_step == FlowStep.DONE:
            return
        self.compute_missing_fields()
        status = self._status_for_step(self.current_step)
        if not status.is_complete:
            return
        idx = _STEP_ORDER.index(self.current_step)
        if idx + 1 < len(_STEP_ORDER):
            self.current_step = _STEP_ORDER[idx + 1]
        else:
            self.current_step = FlowStep.DONE


# ── Response models ────────────────────────────────────────────────────

_DISPLAY_LABELS: dict[str, str] = {
    "under_18": "Under 18",
    "18_24": "18-24",
    "25_34": "25-34",
    "35_44": "35-44",
    "45_plus": "45+",
    "slice_of_life": "Slice of Life",
    "sci_fi": "Sci-Fi",
}


_REVERSE_LABELS: dict[str, str] = {label.lower(): value for value, label in _DISPLAY_LABELS.items()}


def enum_label(value: str) -> str:
    """Convert a raw enum value to a human-readable label."""
    if value in _DISPLAY_LABELS:
        return _DISPLAY_LABELS[value]
    return value.replace("_", " ").title()


def normalize_enum_value(value: str) -> str:
    """Convert a human-readable label back to a raw enum value.

    Handles special-case labels via reverse lookup, then falls back to
    lowercasing and replacing spaces/hyphens with underscores.
    """
    lower = value.lower()
    if lower in _REVERSE_LABELS:
        return _REVERSE_LABELS[lower]
    return lower.replace("-", "_").replace(" ", "_")


class RagSource(BaseModel):
    title: str
    content: str
    score: float


class QuestionSpec(BaseModel):
    field_name: str
    question_text: str
    options: list[str] | None = None
    option_labels: list[str] | None = None
    default_value: str | None = None
    multi_select: bool = False


class AssistantResponse(BaseModel):
    message: str
    mode: ResponseMode
    next_question: QuestionSpec | None = None
    state_patch: dict | None = None
    sources: list[RagSource] | None = None
