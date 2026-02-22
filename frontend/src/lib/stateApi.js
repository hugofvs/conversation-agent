/**
 * Patch onboarding state fields without going through the LLM.
 * @param {string} sessionId
 * @param {Record<string, any>} updates - field_name → value map
 * @returns {Promise<{state: object, next_question: object|null}>}
 */
export async function patchState(sessionId, updates) {
  const res = await fetch('/state', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, updates }),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text)
  }

  return res.json()
}
