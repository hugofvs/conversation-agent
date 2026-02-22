import { describe, it, expect, vi, beforeEach } from 'vitest'
import { patchState } from './stateApi.js'

describe('patchState', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends PATCH with correct body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ state: {}, next_question: null }),
    }))

    await patchState('sess-1', { display_name: 'Hugo' })

    expect(fetch).toHaveBeenCalledWith('/state', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: 'sess-1', updates: { display_name: 'Hugo' } }),
    })
  })

  it('returns parsed JSON on success', async () => {
    const payload = { state: { current_step: 'food' }, next_question: null }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(payload),
    }))

    const result = await patchState('sess-1', {})
    expect(result).toEqual(payload)
  })

  it('throws Error on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Not found'),
    }))

    await expect(patchState('sess-1', {})).rejects.toThrow('Not found')
  })
})
