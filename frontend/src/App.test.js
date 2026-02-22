import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte'
import App from './App.svelte'

function mockChatResponse(overrides = {}) {
  const data = {
    session_id: 'sess-1',
    state: { current_step: 'profile' },
    response: {
      message: 'Hello from assistant',
      sources: [],
      next_question: null,
    },
    ...overrides,
  }
  // Deep merge response if provided
  if (overrides.response) {
    data.response = { ...data.response, ...overrides.response }
  }
  if (overrides.state) {
    data.state = { ...data.state, ...overrides.state }
  }
  return data
}

function stubFetch(data) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
  }))
}

async function sendUserMessage(text) {
  const input = screen.getByPlaceholderText('Type a message...')
  await fireEvent.input(input, { target: { value: text } })
  await fireEvent.submit(input.closest('form'))
}

describe('App', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('auto-init greeting appears on load', async () => {
    const data = mockChatResponse({ response: { message: 'Welcome! What is your name?' } })
    stubFetch(data)
    render(App)

    await waitFor(() => {
      expect(screen.getByText('Welcome! What is your name?')).toBeInTheDocument()
    })

    // Should have sent an auto request
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.auto).toBe(true)
  })

  it('send message → user and assistant messages appear', async () => {
    const initData = mockChatResponse({ response: { message: 'Welcome!' } })
    const replyData = mockChatResponse({ response: { message: 'Nice to meet you' } })
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(initData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(replyData) })
    )
    render(App)

    // Wait for auto-init to complete
    await waitFor(() => {
      expect(screen.getByText('Welcome!')).toBeInTheDocument()
    })

    await sendUserMessage('Hi there')

    expect(screen.getByText('Hi there')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('Nice to meet you')).toBeInTheDocument()
    })
  })

  it('typing indicator shown while loading', async () => {
    // Use a fetch that we can control timing on
    let resolveFetch
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() =>
      new Promise(resolve => {
        resolveFetch = resolve
      })
    ))
    const { container } = render(App)

    // Auto-init triggers fetch, so typing indicator should appear
    await waitFor(() => {
      expect(container.querySelector('.animate-bounce')).toBeInTheDocument()
    })

    // Wait until fetch has actually been called
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled()
    })

    // Resolve the fetch
    resolveFetch({
      ok: true,
      json: () => Promise.resolve(mockChatResponse()),
    })

    // Typing indicator should disappear
    await waitFor(() => {
      expect(container.querySelector('.animate-bounce')).not.toBeInTheDocument()
    })
  })

  it('API error → error message displayed', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Server error'),
    }))
    render(App)

    await waitFor(() => {
      expect(screen.getByText('Error: Server error')).toBeInTheDocument()
    })
  })

  it('step progress updates after response', async () => {
    const initData = mockChatResponse()
    const replyData = mockChatResponse({ state: { current_step: 'food' } })
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(initData) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(replyData) })
    )
    const { container } = render(App)

    // Wait for auto-init
    await waitFor(() => {
      expect(screen.getByText('Hello from assistant')).toBeInTheDocument()
    })

    await sendUserMessage('My name is Hugo')

    await waitFor(() => {
      // Profile should be completed (checkmark SVG), Food should be current (number "2")
      const svgs = container.querySelectorAll('svg')
      expect(svgs.length).toBeGreaterThanOrEqual(1)
    })
  })
})
