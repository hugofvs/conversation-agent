import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/svelte'
import TypingIndicator from './TypingIndicator.svelte'

describe('TypingIndicator', () => {
  it('renders three bouncing dots', () => {
    const { container } = render(TypingIndicator)
    const dots = container.querySelectorAll('.animate-bounce')
    expect(dots).toHaveLength(3)
  })

  it('applies staggered animation delays', () => {
    const { container } = render(TypingIndicator)
    const dots = container.querySelectorAll('.animate-bounce')
    expect(dots[0].style.animationDelay).toBe('0ms')
    expect(dots[1].style.animationDelay).toBe('150ms')
    expect(dots[2].style.animationDelay).toBe('300ms')
  })
})
