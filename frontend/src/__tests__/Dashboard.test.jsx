import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Dashboard from '../components/Dashboard'

vi.mock('../api', () => ({
  getPokemon: vi.fn(),
  getGenerations: vi.fn(),
  safeSprite: vi.fn(() => null),
}))

import { getPokemon, getGenerations } from '../api'

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  )

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    getPokemon.mockReturnValue(new Promise(() => {}))
    getGenerations.mockReturnValue(new Promise(() => {}))

    renderDashboard()
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders featured pokemon after loading', async () => {
    const mockPokemon = [
      { id: 'pk-1', name: 'Bulbasaur', type: 'grass/poison', height_m: 0.7, mass_kg: 6.9, sprite_url: null },
      { id: 'pk-4', name: 'Charmander', type: 'fire', height_m: 0.6, mass_kg: 8.5, sprite_url: null },
    ]
    const mockGenerations = [
      { id: 'gen-1', name: 'Generation I', gen_number: 1, details: 'First gen', region_name: 'Kanto' },
    ]

    getPokemon.mockResolvedValue(mockPokemon)
    getGenerations.mockResolvedValue(mockGenerations)

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Bulbasaur')).toBeInTheDocument()
      expect(screen.getByText('Charmander')).toBeInTheDocument()
    })

    expect(screen.getByText('PokéMission Control')).toBeInTheDocument()
  })

  it('renders generation timeline', async () => {
    const mockGenerations = [
      { id: 'gen-1', name: 'Generation I', gen_number: 1, details: 'First gen', region_name: 'Kanto', date_utc: null },
    ]

    getPokemon.mockResolvedValue([])
    getGenerations.mockResolvedValue(mockGenerations)

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Generation Timeline')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    getPokemon.mockRejectedValue(new Error('API Error'))
    getGenerations.mockRejectedValue(new Error('API Error'))

    renderDashboard()

    await waitFor(() => {
      expect(screen.queryByText('PokéMission Control')).toBeInTheDocument()
    })
  })
})
