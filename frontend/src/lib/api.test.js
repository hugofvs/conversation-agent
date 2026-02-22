import { describe, it, expect, vi, beforeEach } from 'vitest'
import { sendMessage } from './api.js'

describe('sendMessage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends POST with correct body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ reply: 'hi' }),
    }))

    await sendMessage('hello', 'sess-1')

    expect(fetch).toHaveBeenCalledWith('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'hello', session_id: 'sess-1', auto: false }),
    })
  })

  it('sends null session_id on first message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    }))

    await sendMessage('hi', null)

    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.session_id).toBeNull()
  })

  it('returns parsed JSON on success', async () => {
    const payload = { response: { message: 'hello' }, session_id: 'abc' }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(payload),
    }))

    const result = await sendMessage('test', null)
    expect(result).toEqual(payload)
  })

  it('throws Error on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Server error'),
    }))

    await expect(sendMessage('test', null)).rejects.toThrow('Server error')
  })
})
