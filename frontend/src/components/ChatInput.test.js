import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import ChatInput from './ChatInput.svelte'

describe('ChatInput', () => {
  // --- Basic input ---

  it('calls onSend with trimmed text on submit', async () => {
    const onSend = vi.fn()
    render(ChatInput, { onSend })

    const input = screen.getByPlaceholderText('Type a message...')
    await userEvent.type(input, '  hello  ')
    await fireEvent.submit(input.closest('form'))

    expect(onSend).toHaveBeenCalledWith('hello')
    expect(input).toHaveValue('')
  })

  it('does not send when input is empty', async () => {
    const onSend = vi.fn()
    render(ChatInput, { onSend })

    const input = screen.getByPlaceholderText('Type a message...')
    await fireEvent.submit(input.closest('form'))

    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables input and button when disabled', () => {
    const onSend = vi.fn()
    render(ChatInput, { onSend, disabled: true })

    const input = screen.getByRole('textbox')
    const button = screen.getByRole('button', { name: 'Send' })
    expect(input).toBeDisabled()
    expect(button).toBeDisabled()
  })

  // --- Chips (< 5 options) ---

  describe('chips', () => {
    const activeQuestion = {
      options: ['opt_a', 'opt_b', 'opt_c'],
      option_labels: ['Alpha', 'Beta', 'Gamma'],
    }

    it('renders chip buttons', () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })
      expect(screen.getByText('Alpha')).toBeInTheDocument()
      expect(screen.getByText('Beta')).toBeInTheDocument()
      expect(screen.getByText('Gamma')).toBeInTheDocument()
    })

    it('clicking chip calls onSend with value', async () => {
      const onSend = vi.fn()
      render(ChatInput, { onSend, activeQuestion })

      // The chip button contains both the kbd and label text
      const chip = screen.getByText('Beta').closest('button')
      await fireEvent.click(chip)

      expect(onSend).toHaveBeenCalledWith('opt_b')
    })

    it('number key shortcut selects chip', async () => {
      const onSend = vi.fn()
      render(ChatInput, { onSend, activeQuestion })

      const input = screen.getByRole('textbox')
      await fireEvent.keyDown(input, { key: '2' })

      expect(onSend).toHaveBeenCalledWith('opt_b')
    })
  })

  // --- Autocomplete (>= 5 options) ---

  describe('autocomplete', () => {
    const activeQuestion = {
      options: ['apple', 'banana', 'cherry', 'date', 'elderberry'],
      option_labels: ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry'],
    }

    it('shows dropdown on focus', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)

      const listbox = screen.getByRole('listbox')
      expect(listbox).toBeInTheDocument()
      const options = screen.getAllByRole('option')
      expect(options.length).toBe(5)
      expect(options[0]).toHaveTextContent('Apple')
      expect(options[4]).toHaveTextContent('Elderberry')
    })

    it('filters dropdown as user types', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)
      await userEvent.type(input, 'ber')

      const options = screen.getAllByRole('option')
      expect(options.length).toBe(1)
      expect(options[0]).toHaveTextContent('Elderberry')
    })

    it('highlights matched text in dropdown items', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)
      await userEvent.type(input, 'ber')

      const option = screen.getByRole('option')
      // "Elder" + "ber" (highlighted) + "ry"
      const spans = option.querySelectorAll('span')
      expect(spans.length).toBe(3)
      expect(spans[0].textContent).toBe('Elder')
      expect(spans[1].textContent).toBe('ber')
      expect(spans[1].className).toContain('text-amber')
      expect(spans[2].textContent).toBe('ry')
    })

    it('ArrowDown + Tab fills option into input without submitting', async () => {
      const onSend = vi.fn()
      render(ChatInput, { onSend, activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)
      await fireEvent.keyDown(input, { key: 'ArrowDown' })
      await fireEvent.keyDown(input, { key: 'Tab' })

      expect(input).toHaveValue('apple')
      expect(onSend).not.toHaveBeenCalled()
    })

    it('Escape closes dropdown', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)
      expect(screen.getByRole('listbox')).toBeInTheDocument()

      await fireEvent.keyDown(input, { key: 'Escape' })
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })

    it('sets ARIA attributes on input', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      expect(input).toHaveAttribute('aria-controls', 'autocomplete-listbox')
      expect(input).toHaveAttribute('aria-expanded', 'false')

      await fireEvent.focus(input)
      expect(input).toHaveAttribute('aria-expanded', 'true')
    })

    it('highlights active option with aria-selected', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)
      await fireEvent.keyDown(input, { key: 'ArrowDown' })

      const options = screen.getAllByRole('option')
      expect(options[0]).toHaveAttribute('aria-selected', 'true')
      expect(options[1]).toHaveAttribute('aria-selected', 'false')
    })

    it('Enter submits free text even if it does not match an option', async () => {
      const onSend = vi.fn()
      render(ChatInput, { onSend, activeQuestion })

      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'custom value')
      await fireEvent.submit(input.closest('form'))

      expect(onSend).toHaveBeenCalledWith('custom value')
    })

    it('renders virtualized items for large option sets', async () => {
      const manyOptions = Array.from({ length: 100 }, (_, i) => `option_${i}`)
      const manyLabels = Array.from({ length: 100 }, (_, i) => `Option ${i}`)
      const bigQuestion = { options: manyOptions, option_labels: manyLabels }

      render(ChatInput, { onSend: vi.fn(), activeQuestion: bigQuestion })

      const input = screen.getByRole('combobox')
      await fireEvent.focus(input)

      // Should render fewer DOM nodes than total items (virtualized)
      const renderedOptions = screen.getAllByRole('option')
      expect(renderedOptions.length).toBeLessThan(100)
      expect(renderedOptions.length).toBeGreaterThan(0)
    })
  })

  // --- Default value ---

  it('Tab fills default value into input', async () => {
    const onSend = vi.fn()
    const activeQuestion = { default_value: '42' }
    render(ChatInput, { onSend, activeQuestion })

    const input = screen.getByRole('textbox')
    await fireEvent.keyDown(input, { key: 'Tab' })

    expect(input).toHaveValue('42')
    expect(onSend).not.toHaveBeenCalled()
  })

  // --- Ghost text ---

  describe('ghost text', () => {
    const activeQuestion = {
      options: ['apple', 'banana', 'cherry', 'date', 'elderberry'],
      option_labels: ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry'],
    }

    it('shows ghost suffix when typing matches an option prefix', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'app')

      const ghost = document.querySelector('[aria-hidden="true"] .text-ink-muted')
      expect(ghost).toBeInTheDocument()
      expect(ghost.textContent).toBe('le')
    })

    it('does not show ghost text when no prefix match', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'xyz')

      const ghostOverlay = document.querySelector('[aria-hidden="true"]')
      expect(ghostOverlay).not.toBeInTheDocument()
    })

    it('shows default value as ghost text on empty input', () => {
      const questionWithDefault = { default_value: '42' }
      render(ChatInput, { onSend: vi.fn(), activeQuestion: questionWithDefault })

      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('Tab accepts ghost text suggestion', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'app')
      await fireEvent.keyDown(input, { key: 'Escape' }) // close dropdown
      await fireEvent.keyDown(input, { key: 'Tab' })

      expect(input).toHaveValue('Apple')
    })

    it('ghost text is case-insensitive', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'BAN')

      const ghost = document.querySelector('[aria-hidden="true"] .text-ink-muted')
      expect(ghost).toBeInTheDocument()
      expect(ghost.textContent).toBe('ana')
    })

    it('multi-select suggests based on current segment', async () => {
      const multiQuestion = { ...activeQuestion, multi_select: true }
      render(ChatInput, { onSend: vi.fn(), activeQuestion: multiQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'apple, ban')

      const ghost = document.querySelector('[aria-hidden="true"] .text-ink-muted')
      expect(ghost).toBeInTheDocument()
      expect(ghost.textContent).toBe('ana')
    })

    it('Tab in multi-select appends comma after accepting ghost text', async () => {
      const multiQuestion = { ...activeQuestion, multi_select: true }
      render(ChatInput, { onSend: vi.fn(), activeQuestion: multiQuestion })
      const input = screen.getByRole('combobox')
      await userEvent.type(input, 'app')
      await fireEvent.keyDown(input, { key: 'Escape' }) // close dropdown
      await fireEvent.keyDown(input, { key: 'Tab' })

      expect(input).toHaveValue('Apple, ')
    })
  })
})
