import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/svelte'
import StepProgress from './StepProgress.svelte'

function getCheckmarks(container) {
  return container.querySelectorAll('svg')
}

function getNumberBadges(container) {
  // Number badges are the small circles containing just a digit (1, 2, or 3)
  const badges = []
  container.querySelectorAll('.w-6.h-6.rounded-full').forEach(el => {
    const text = el.textContent.trim()
    if (/^[123]$/.test(text)) badges.push(text)
  })
  return badges
}

describe('StepProgress', () => {
  it('profile step: Profile current, others pending', () => {
    const { container } = render(StepProgress, { currentStep: 'profile' })
    expect(getCheckmarks(container)).toHaveLength(0)
    expect(getNumberBadges(container)).toEqual(['1', '2', '3'])
  })

  it('food step: Profile completed, Food current', () => {
    const { container } = render(StepProgress, { currentStep: 'food' })
    expect(getCheckmarks(container)).toHaveLength(1)
    const badges = getNumberBadges(container)
    expect(badges).toContain('2')
    expect(badges).not.toContain('1')
  })

  it('anime step: Profile+Food completed, Anime current', () => {
    const { container } = render(StepProgress, { currentStep: 'anime' })
    expect(getCheckmarks(container)).toHaveLength(2)
    const badges = getNumberBadges(container)
    expect(badges).toContain('3')
    expect(badges).not.toContain('1')
    expect(badges).not.toContain('2')
  })

  it('done step: all completed', () => {
    const { container } = render(StepProgress, { currentStep: 'done' })
    expect(getCheckmarks(container)).toHaveLength(3)
    expect(getNumberBadges(container)).toEqual([])
  })
})
