import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/svelte'
import FormSection from './FormSection.svelte'

const profileStep = {
  key: 'profile',
  label: 'Profile',
  fields: [
    { key: 'display_name', label: 'Display Name', type: 'text' },
    { key: 'country', label: 'Country', type: 'text' },
  ],
}

describe('FormSection', () => {
  it('renders step label and all field labels', () => {
    render(FormSection, {
      step: profileStep,
      answers: {},
      currentStep: 'profile',
      onUpdate: vi.fn(),
    })
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Display Name')).toBeInTheDocument()
    expect(screen.getByText('Country')).toBeInTheDocument()
  })

  it('shows checkmark icon for completed section', () => {
    const { container } = render(FormSection, {
      step: profileStep,
      answers: {},
      currentStep: 'food',
      onUpdate: vi.fn(),
    })
    // Completed step renders an SVG checkmark
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    // The checkmark is inside a green circle
    expect(svg.closest('div').className).toContain('bg-sage')
  })

  it('shows step number for current section', () => {
    const { container } = render(FormSection, {
      step: profileStep,
      answers: {},
      currentStep: 'profile',
      onUpdate: vi.fn(),
    })
    // Profile is step 1
    const numberBadge = container.querySelector('.bg-amber')
    expect(numberBadge).toBeInTheDocument()
    expect(numberBadge.textContent.trim()).toBe('1')
  })

  it('shows muted style for pending section', () => {
    // Profile is current, so food (step index 1) is pending
    const foodStep = {
      key: 'food',
      label: 'Food',
      fields: [{ key: 'diet', label: 'Diet', type: 'text' }],
    }
    const { container } = render(FormSection, {
      step: foodStep,
      answers: {},
      currentStep: 'profile',
      onUpdate: vi.fn(),
    })
    // Pending step has muted text
    expect(container.querySelector('.text-ink-tertiary')).toBeInTheDocument()
  })

  it('passes field values from answers', () => {
    render(FormSection, {
      step: profileStep,
      answers: { display_name: 'Hugo' },
      currentStep: 'profile',
      onUpdate: vi.fn(),
    })
    expect(screen.getByDisplayValue('Hugo')).toBeInTheDocument()
  })
})
