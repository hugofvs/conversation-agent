import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/svelte'
import FormField from './FormField.svelte'

const textField = { key: 'display_name', label: 'Display Name', type: 'text' }

const enumField = {
  key: 'age_range', label: 'Age Range', type: 'enum',
  options: [
    { value: 'under_18', label: 'Under 18' },
    { value: '25_34', label: '25-34' },
  ],
}

const multiField = {
  key: 'allergies', label: 'Allergies', type: 'multi',
  options: [
    { value: 'dairy', label: 'Dairy' },
    { value: 'nuts', label: 'Nuts' },
  ],
}

const boolEnumField = {
  key: 'spice_ok', label: 'Spice OK?', type: 'enum',
  options: [
    { value: true, label: 'Yes' },
    { value: false, label: 'No' },
  ],
}

const listField = { key: 'top_3_anime', label: 'Top 3 Anime', type: 'list' }

describe('FormField', () => {
  it('renders label', () => {
    render(FormField, { fieldDef: textField, onUpdate: vi.fn() })
    expect(screen.getByText('Display Name')).toBeInTheDocument()
  })

  it('renders text input and calls onUpdate on change', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: textField, onUpdate })

    const input = screen.getByPlaceholderText('...')
    await fireEvent.change(input, { target: { value: 'Hugo' } })
    expect(onUpdate).toHaveBeenCalledWith('display_name', 'Hugo')
  })

  it('renders text input with existing value', () => {
    render(FormField, { fieldDef: textField, value: 'Alice', onUpdate: vi.fn() })
    expect(screen.getByDisplayValue('Alice')).toBeInTheDocument()
  })

  it('renders select for enum field', () => {
    render(FormField, { fieldDef: enumField, onUpdate: vi.fn() })
    expect(screen.getByText('Under 18')).toBeInTheDocument()
    expect(screen.getByText('25-34')).toBeInTheDocument()
  })

  it('calls onUpdate with selected enum value', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: enumField, onUpdate })

    const select = screen.getByRole('combobox')
    await fireEvent.change(select, { target: { value: '25_34' } })
    expect(onUpdate).toHaveBeenCalledWith('age_range', '25_34')
  })

  it('converts boolean string values for enum fields', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: boolEnumField, onUpdate })

    const select = screen.getByRole('combobox')
    await fireEvent.change(select, { target: { value: 'true' } })
    expect(onUpdate).toHaveBeenCalledWith('spice_ok', true)

    await fireEvent.change(select, { target: { value: 'false' } })
    expect(onUpdate).toHaveBeenCalledWith('spice_ok', false)
  })

  it('renders checkboxes for multi field', () => {
    render(FormField, { fieldDef: multiField, onUpdate: vi.fn() })
    expect(screen.getByText('Dairy')).toBeInTheDocument()
    expect(screen.getByText('Nuts')).toBeInTheDocument()
  })

  it('calls onUpdate with array when checkbox checked', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: multiField, onUpdate })

    const checkboxes = screen.getAllByRole('checkbox')
    await fireEvent.click(checkboxes[0]) // Dairy
    expect(onUpdate).toHaveBeenCalledWith('allergies', ['dairy'])
  })

  it('calls onUpdate with null when all checkboxes unchecked', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: multiField, value: ['dairy'], onUpdate })

    const checkboxes = screen.getAllByRole('checkbox')
    await fireEvent.click(checkboxes[0]) // Dairy (uncheck)
    expect(onUpdate).toHaveBeenCalledWith('allergies', null)
  })

  it('renders list input and parses comma-separated values', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: listField, onUpdate })

    const input = screen.getByPlaceholderText('Comma-separated...')
    await fireEvent.change(input, { target: { value: 'Naruto, One Piece' } })
    expect(onUpdate).toHaveBeenCalledWith('top_3_anime', ['Naruto', 'One Piece'])
  })

  it('calls onUpdate with null for empty list input', async () => {
    const onUpdate = vi.fn()
    render(FormField, { fieldDef: listField, onUpdate })

    const input = screen.getByPlaceholderText('Comma-separated...')
    await fireEvent.change(input, { target: { value: '  ' } })
    expect(onUpdate).toHaveBeenCalledWith('top_3_anime', null)
  })

  it('highlights active field', () => {
    const { container } = render(FormField, {
      fieldDef: textField, isActive: true, onUpdate: vi.fn(),
    })
    expect(container.querySelector('.bg-amber-soft')).toBeInTheDocument()
  })

  it('disables input when disabled', () => {
    render(FormField, { fieldDef: textField, disabled: true, onUpdate: vi.fn() })
    expect(screen.getByPlaceholderText('...')).toBeDisabled()
  })
})
