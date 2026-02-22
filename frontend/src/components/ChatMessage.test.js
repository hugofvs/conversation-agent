import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/svelte'
import ChatMessage from './ChatMessage.svelte'

describe('ChatMessage', () => {
  it('renders user message right-aligned', () => {
    render(ChatMessage, { role: 'user', text: 'Hello there' })
    expect(screen.getByText('Hello there')).toBeInTheDocument()
    const container = screen.getByText('Hello there').closest('.flex')
    expect(container.className).toContain('justify-end')
  })

  it('renders assistant message left-aligned', () => {
    render(ChatMessage, { role: 'assistant', text: 'Hi back' })
    expect(screen.getByText('Hi back')).toBeInTheDocument()
    const container = screen.getByText('Hi back').closest('.flex')
    expect(container.className).toContain('justify-start')
  })

  it('renders error with red styling', () => {
    render(ChatMessage, { role: 'assistant', text: 'Something failed', isError: true })
    const el = screen.getByText('Something failed')
    expect(el.className).toContain('text-red-700')
  })
})
