import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import Header from '../components/Header'

const renderHeader = () =>
  render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  )

describe('Header', () => {
  it('renders the app title', () => {
    renderHeader()
    expect(screen.getByText('PokéMission')).toBeInTheDocument()
  })

  it('renders all navigation links', () => {
    renderHeader()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Generations')).toBeInTheDocument()
    expect(screen.getByText('Pokémon')).toBeInTheDocument()
    expect(screen.getByText('Subscribe')).toBeInTheDocument()
  })

  it('links have correct hrefs', () => {
    renderHeader()
    expect(screen.getByText('Dashboard').closest('a')).toHaveAttribute('href', '/')
    expect(screen.getByText('Generations').closest('a')).toHaveAttribute('href', '/generations')
    expect(screen.getByText('Pokémon').closest('a')).toHaveAttribute('href', '/pokemon')
    expect(screen.getByText('Subscribe').closest('a')).toHaveAttribute('href', '/subscribe')
  })

  it('renders the logo element', () => {
    renderHeader()
    expect(screen.getByText('Pokémon API Explorer')).toBeInTheDocument()
  })
})
