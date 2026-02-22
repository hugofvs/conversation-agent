import { describe, it, expect } from 'vitest'
import { STEPS, formatFieldValue } from './fieldDefinitions.js'

describe('STEPS', () => {
  it('defines three steps in order', () => {
    expect(STEPS.map(s => s.key)).toEqual(['profile', 'food', 'anime'])
  })
})

describe('formatFieldValue', () => {
  const enumField = {
    type: 'enum',
    options: [
      { value: 'under_18', label: 'Under 18' },
      { value: '25_34', label: '25-34' },
    ],
  }

  const multiField = {
    type: 'multi',
    options: [
      { value: 'dairy', label: 'Dairy' },
      { value: 'nuts', label: 'Nuts' },
    ],
  }

  const listField = { type: 'list' }
  const textField = { type: 'text' }

  it('returns empty string for null value', () => {
    expect(formatFieldValue(textField, null)).toBe('')
  })

  it('formats enum value using option label', () => {
    expect(formatFieldValue(enumField, 'under_18')).toBe('Under 18')
    expect(formatFieldValue(enumField, '25_34')).toBe('25-34')
  })

  it('falls back to string for unknown enum value', () => {
    expect(formatFieldValue(enumField, 'unknown')).toBe('unknown')
  })

  it('formats multi value as comma-separated labels', () => {
    expect(formatFieldValue(multiField, ['dairy', 'nuts'])).toBe('Dairy, Nuts')
  })

  it('formats list value as comma-separated strings', () => {
    expect(formatFieldValue(listField, ['Naruto', 'One Piece'])).toBe('Naruto, One Piece')
  })

  it('converts non-null primitives to string', () => {
    expect(formatFieldValue(textField, 42)).toBe('42')
    expect(formatFieldValue(textField, true)).toBe('true')
  })
})
