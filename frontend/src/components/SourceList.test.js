import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/svelte'
import SourceList from './SourceList.svelte'

describe('SourceList', () => {
  it('renders nothing when sources is empty', () => {
    const { container } = render(SourceList, { sources: [] })
    expect(container.querySelectorAll('span')).toHaveLength(0)
  })

  it('renders tag per source title', () => {
    const sources = [
      { title: 'Wikipedia' },
      { title: 'MDN Docs' },
    ]
    render(SourceList, { sources })
    expect(screen.getByText('Wikipedia')).toBeInTheDocument()
    expect(screen.getByText('MDN Docs')).toBeInTheDocument()
  })
})
