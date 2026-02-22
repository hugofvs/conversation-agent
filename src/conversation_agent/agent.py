from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .models import (
    AgeRange,
    Allergen,
    AnimeAnswers,
    AnimeGenre,
    AssistantResponse,
    AssistantState,
    DietType,
    FlowStep,
    FoodAnswers,
    ProfileAnswers,
    SubDubPref,
    _STEP_ANSWERS_MAP,
)
from .rag import VectorStore


@dataclass
class AgentDeps:
    state: AssistantState
    vector_store: VectorStore


agent = Agent(
    "openai:gpt-4o-mini",
    output_type=AssistantResponse,
    deps_type=AgentDeps,
    retries=2,
)


def _enum_values(enum_cls: type) -> str:
    return ", ".join(e.value for e in enum_cls)


def _format_answers(answers) -> str:
    lines = []
    for name in answers.model_fields:
        val = getattr(answers, name)
        if val is not None:
            lines.append(f"  {name}: {val}")
    return "\n".join(lines) if lines else "  (none yet)"


_STEP_FIELDS: dict[FlowStep, dict[str, str]] = {
    FlowStep.PROFILE: {
        "display_name": "a free-text string (the user's preferred name)",
        "age_range": f"one of: {_enum_values(AgeRange)}",
        "country": "a free-text string (country of residence)",
    },
    FlowStep.FOOD: {
        "diet": f"one of: {_enum_values(DietType)}",
        "allergies": f"a list from: {_enum_values(Allergen)}",
        "spice_ok": "true or false",
    },
    FlowStep.ANIME: {
        "favorite_genres": f"a list from: {_enum_values(AnimeGenre)}",
        "sub_or_dub": f"one of: {_enum_values(SubDubPref)}",
        "top_3_anime": "a list of up to 3 anime titles (free-text strings)",
    },
}


@agent.system_prompt(dynamic=True)
async def build_system_prompt(ctx: RunContext[AgentDeps]) -> str:
    state = ctx.deps.state
    step = state.current_step
    missing = state.compute_missing_fields()

    prompt_parts = [
        "You are a friendly onboarding assistant guiding the user through a 3-step profile setup.",
        "The steps are: Profile → Food → Anime.",
        "",
        f"Current step: {step.value}",
    ]

    if step != FlowStep.DONE:
        answers = state._answers_for_step(step)
        prompt_parts.append(f"Filled fields:\n{_format_answers(answers)}")
        prompt_parts.append(f"Missing fields: {', '.join(missing) if missing else 'none'}")
        prompt_parts.append("")
        prompt_parts.append("Valid values for current step fields:")
        for field_name, desc in _STEP_FIELDS[step].items():
            prompt_parts.append(f"  - {field_name}: {desc}")
    else:
        prompt_parts.append("All steps are complete! Summarize the user's profile.")

    prompt_parts.extend([
        "",
        "## Behavior rules",
        "",
        "1. INTENT CLASSIFICATION: For each user message, determine the intent:",
        "   - FLOW: The user is answering onboarding questions. Extract answers and call update_state.",
        "   - QUESTION: The user is asking a question about the app, the process, diet types, anime genres, etc. Use rag_search to find relevant info, then answer.",
        "   - OUT_OF_SCOPE: The user is asking about something completely unrelated (e.g. politics, math homework). Politely redirect them back to the onboarding.",
        "",
        "2. For FLOW intent:",
        "   - Extract ALL answers the user provided in their message (they may answer multiple fields at once).",
        "   - Call update_state with a dict mapping field names to values. Use the exact enum values listed above.",
        "   - After updating, ask the next missing field. If the step is complete, acknowledge it and introduce the next step.",
        "   - Set mode='flow_question' in your response. Include next_question if there are still missing fields.",
        "",
        "3. For QUESTION intent:",
        "   - Call rag_search with the user's question to find relevant information.",
        "   - Answer based on the RAG results. Include the sources in your response.",
        "   - Set mode='answer' in your response.",
        "   - After answering, gently remind them where they are in the flow.",
        "",
        "4. For OUT_OF_SCOPE intent:",
        "   - Set mode='guardrail' in your response.",
        "   - Politely explain you can only help with onboarding and related questions.",
        "",
        "5. When all steps are DONE, set mode='done' and give a friendly summary.",
        "",
        "6. For the FIRST message of the conversation (empty/greeting), welcome the user and ask the first question of the Profile step.",
        "",
        "7. IMPORTANT: Always call update_state when the user provides answers. Never skip this tool call.",
    ])

    return "\n".join(prompt_parts)


@agent.tool
async def rag_search(ctx: RunContext[AgentDeps], query: str, top_k: int = 3) -> str:
    """Search the knowledge base for information about the app, onboarding process, diet types, or anime genres."""
    sources = await ctx.deps.vector_store.search(query, top_k=top_k)
    if not sources:
        return "No relevant information found."
    parts = []
    for s in sources:
        parts.append(f"[{s.title}] (score: {s.score})\n{s.content}")
    return "\n\n---\n\n".join(parts)


@agent.tool
async def update_state(ctx: RunContext[AgentDeps], patch: dict[str, object]) -> str:
    """Update the current step's answers with extracted values from the user's message.

    Args:
        patch: A dict mapping field names to their values. Use exact enum values.
              Example for profile step: {"display_name": "Alex", "age_range": "25_34"}
              Example for food step: {"diet": "vegan", "allergies": ["nuts", "dairy"], "spice_ok": true}
    """
    state = ctx.deps.state
    step = state.current_step

    if step == FlowStep.DONE:
        return "All steps already complete. No update needed."

    answers = state._answers_for_step(step)
    model_cls = _STEP_ANSWERS_MAP[step]

    # Merge the patch into existing answers
    current = answers.model_dump()
    for key, value in patch.items():
        if key in current:
            current[key] = value

    # Validate via Pydantic
    try:
        updated = model_cls.model_validate(current)
    except Exception as e:
        return f"Validation error: {e}. Please check the values and try again."

    # Apply back to state
    setattr(state, step.value, updated)

    # Recompute missing fields and advance if complete
    missing = state.compute_missing_fields()
    if not missing:
        state.advance_step()
        if state.current_step == FlowStep.DONE:
            return "Step complete! All steps are now done."
        return f"Step '{step.value}' complete! Moving to '{state.current_step.value}' step."

    return f"Updated. Still missing: {', '.join(missing)}"
