import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/svelte'
import SidePanel from './SidePanel.svelte'

describe('SidePanel', () => {
  it('renders panel heading and all three sections', () => {
    render(SidePanel, {
      onboardingState: { profile: {}, food: {}, anime: {} },
      currentStep: 'profile',
      onToggle: vi.fn(),
      onFieldUpdate: vi.fn(),
    })
    expect(screen.getByText('Your Answers')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Food')).toBeInTheDocument()
    expect(screen.getByText('Anime')).toBeInTheDocument()
  })

  it('renders toggle button', () => {
    render(SidePanel, {
      onboardingState: { profile: {}, food: {}, anime: {} },
      currentStep: 'profile',
      onToggle: vi.fn(),
      onFieldUpdate: vi.fn(),
    })
    expect(screen.getByRole('button', { name: 'Toggle answers panel' })).toBeInTheDocument()
  })

  it('calls onToggle when toggle button clicked', async () => {
    const onToggle = vi.fn()
    render(SidePanel, {
      onboardingState: { profile: {}, food: {}, anime: {} },
      currentStep: 'profile',
      onToggle,
      onFieldUpdate: vi.fn(),
    })

    await fireEvent.click(screen.getByRole('button', { name: 'Toggle answers panel' }))
    expect(onToggle).toHaveBeenCalledOnce()
  })

  it('shows backdrop when open on mobile', () => {
    const { container } = render(SidePanel, {
      onboardingState: { profile: {}, food: {}, anime: {} },
      currentStep: 'profile',
      open: true,
      onToggle: vi.fn(),
      onFieldUpdate: vi.fn(),
    })
    // Backdrop overlay
    expect(container.querySelector('[role="presentation"]')).toBeInTheDocument()
  })

  it('hides backdrop when closed', () => {
    const { container } = render(SidePanel, {
      onboardingState: { profile: {}, food: {}, anime: {} },
      currentStep: 'profile',
      open: false,
      onToggle: vi.fn(),
      onFieldUpdate: vi.fn(),
    })
    expect(container.querySelector('[role="presentation"]')).not.toBeInTheDocument()
  })
})
