import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('axios', () => {
  const mockAxios = {
    create: vi.fn(() => ({
      get: mockGet,
      post: mockPost,
      put: mockPut,
      delete: mockDelete,
    })),
  }
  return { default: mockAxios }
})

describe('API functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exports all expected functions', async () => {
    const api = await import('../api')
    expect(api.getGenerations).toBeDefined()
    expect(api.getGenerationPokemon).toBeDefined()
    expect(api.getLatestGeneration).toBeDefined()
    expect(api.getPokemon).toBeDefined()
    expect(api.getOnePokemon).toBeDefined()
    expect(api.getTypes).toBeDefined()
    expect(api.subscribe).toBeDefined()
    expect(api.getAlerts).toBeDefined()
    expect(api.markAlertRead).toBeDefined()
    expect(api.unsubscribe).toBeDefined()
  })

  it('getGenerations calls correct endpoint', async () => {
    const api = await import('../api')
    mockGet.mockResolvedValue({ data: ['gen1', 'gen2'] })

    const result = await api.getGenerations()
    expect(mockGet).toHaveBeenCalledWith('/generations')
    expect(result).toEqual(['gen1', 'gen2'])
  })

  it('getPokemon calls correct endpoint', async () => {
    const api = await import('../api')
    mockGet.mockResolvedValue({ data: ['pk1', 'pk2'] })

    const result = await api.getPokemon()
    expect(mockGet).toHaveBeenCalledWith('/pokemon')
    expect(result).toEqual(['pk1', 'pk2'])
  })

  it('getGenerationPokemon calls correct endpoint', async () => {
    const api = await import('../api')
    mockGet.mockResolvedValue({ data: ['poke1'] })

    const result = await api.getGenerationPokemon('gen-1')
    expect(mockGet).toHaveBeenCalledWith('/generations/gen-1/pokemon')
    expect(result).toEqual(['poke1'])
  })

  it('getTypes calls correct endpoint', async () => {
    const api = await import('../api')
    mockGet.mockResolvedValue({ data: [{ name: 'fire' }] })

    const result = await api.getTypes()
    expect(mockGet).toHaveBeenCalledWith('/types')
    expect(result).toEqual([{ name: 'fire' }])
  })

  it('subscribe posts to correct endpoint', async () => {
    const api = await import('../api')
    mockPost.mockResolvedValue({ data: { id: 'sub-1' } })

    const result = await api.subscribe({ name: 'Ash', email: 'ash@pokemon.com' })
    expect(mockPost).toHaveBeenCalledWith('/subscribe', { name: 'Ash', email: 'ash@pokemon.com' })
    expect(result).toEqual({ id: 'sub-1' })
  })

  it('unsubscribe calls correct endpoint', async () => {
    const api = await import('../api')
    mockDelete.mockResolvedValue({ data: { status: 'unsubscribed' } })

    const result = await api.unsubscribe('12345678-1234-4123-8123-123456789012', 'test@example.com')
    expect(mockDelete).toHaveBeenCalledWith('/12345678-1234-4123-8123-123456789012', { params: { email: 'test@example.com' } })
    expect(result).toEqual({ status: 'unsubscribed' })
  })
})
