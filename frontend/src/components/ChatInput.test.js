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

      const input = screen.getByRole('textbox')
      await fireEvent.focus(input)

      expect(screen.getByText('Apple')).toBeInTheDocument()
      expect(screen.getByText('Banana')).toBeInTheDocument()
      expect(screen.getByText('Elderberry')).toBeInTheDocument()
    })

    it('filters dropdown as user types', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('textbox')
      await fireEvent.focus(input)
      await userEvent.type(input, 'ber')

      expect(screen.getByText('Elderberry')).toBeInTheDocument()
      expect(screen.queryByText('Apple')).not.toBeInTheDocument()
      expect(screen.queryByText('Date')).not.toBeInTheDocument()
    })

    it('ArrowDown + Tab selects option', async () => {
      const onSend = vi.fn()
      render(ChatInput, { onSend, activeQuestion })

      const input = screen.getByRole('textbox')
      await fireEvent.focus(input)
      await fireEvent.keyDown(input, { key: 'ArrowDown' })
      await fireEvent.keyDown(input, { key: 'Tab' })

      expect(onSend).toHaveBeenCalledWith('apple')
    })

    it('Escape closes dropdown', async () => {
      render(ChatInput, { onSend: vi.fn(), activeQuestion })

      const input = screen.getByRole('textbox')
      await fireEvent.focus(input)
      expect(screen.getByText('Apple')).toBeInTheDocument()

      await fireEvent.keyDown(input, { key: 'Escape' })
      expect(screen.queryByText('Apple')).not.toBeInTheDocument()
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
})
