# Conversation Agent — Design System

## Direction

Clean, personal, approachable. A conversational onboarding that feels like someone genuinely interested in getting to know you — not processing an intake form.

**Who:** A curious newcomer sharing personal preferences through conversation.
**Task:** Complete a 3-step conversational profile naturally (profile → food → anime).
**Feel:** Light and focused. Chapters in a story, not steps in a form.

## Palette

Defined in `app.css` via Tailwind `@theme`.

| Token | Value | Role |
|---|---|---|
| `canvas` | `#FAFAFA` | Page background — light neutral |
| `surface` | `#FFFFFF` | Raised elements — clean white |
| `ink` | `#1A1A1A` | Primary text — near-black |
| `ink-secondary` | `#6B6B6B` | Supporting text |
| `ink-tertiary` | `#999999` | Metadata, labels |
| `ink-muted` | `#BBBBBB` | Placeholders, disabled |
| `amber` | `#BB5500` | Accent — the user's voice |
| `amber-hover` | `#9A4500` | Accent hover state |
| `amber-soft` | `#FFF4EB` | Light amber wash |
| `sage` | `#6B8F71` | Completion, growth — a chapter finished |
| `sage-soft` | `#EDF3EE` | Light sage wash |

## Depth

Subtle neutral shadows. Shadow color: `rgba(0, 0, 0, 0.06)`.

Applied as: `shadow-[0_1px_4px_rgba(0,0,0,0.06)]`

No borders on bubbles. The surface-to-canvas contrast plus warm shadow provides enough definition.

## Borders

Low-opacity ink: `border-ink/8` (standard), `border-ink/10` (inputs), `border-ink/6` (subtle tags).

Used for: header bottom edge, input fields, source tags, step connectors.

## Typography

- **Headings:** `font-grotesk` — Space Grotesk, SF Pro Display, system-ui. Geometric, modern.
- **Body:** `font-ui` — Inter, Roboto, Helvetica, sans-serif. Clean readability.
- **Message text:** `text-[15px] leading-relaxed` — slightly above base for comfortable reading in bubbles.

## Spacing

Base unit: 4px. Generous padding throughout — conversations need room to breathe.

- Bubble padding: `px-5 py-3` (20px / 12px)
- Message gap: `space-y-5` (20px)
- Page padding: `px-6 py-8` in message area
- Header padding: `px-6 py-5`

## Border Radius

- Bubbles: `rounded-2xl` with one flat corner (`rounded-br-sm` for user, `rounded-bl-sm` for assistant)
- Inputs/buttons: `rounded-xl`
- Form field wrappers: `rounded-xl`
- Step markers: `rounded-full`
- Source tags: `rounded-md`

## Components

### Chat Bubbles
- **User:** `bg-amber text-white` — amber is the user's voice
- **Assistant:** `bg-surface` with neutral shadow
- Both: `max-w-[75%]`, generous padding, flat corner pointing toward sender

### Step Progress
Chapter markers, not pills. Numbered circles connected by lines.
- **Completed:** `bg-sage text-white` circle with checkmark, sage label
- **Current:** `bg-amber text-white` circle with number, ink label with `font-medium`
- **Pending:** `bg-ink/5 text-ink-tertiary` circle, tertiary label
- **Connectors:** `h-px w-10 mx-3`, sage/30 when completed, ink/8 when pending

### Chat Input
- Input field: `bg-canvas` (inset feel), `border-ink/10`, amber focus ring (`ring-amber/25 border-amber/40`)
- Send button: `bg-amber text-white`, `hover:bg-amber-hover`, `active:scale-[0.98]`

### Source Tags
Inline references below assistant messages: `text-xs text-ink-tertiary bg-canvas border-ink/6 rounded-md`

### Typing Indicator
Matches assistant bubble styling. Three `w-1.5 h-1.5` dots in `bg-ink-muted` with staggered bounce animation.

### Empty State
Removed — the assistant now sends a proactive greeting on load, so the empty state is replaced by the auto-init message.
