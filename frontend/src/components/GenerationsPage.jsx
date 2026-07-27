import React, { useState, useEffect } from 'react'
import { getGenerations, getGenerationPokemon } from '../api'

const TYPE_COLORS = {
  normal: '#A8A878', fire: '#F08030', water: '#6890F0', electric: '#F8D030',
  grass: '#78C850', ice: '#98D8D8', fighting: '#C03028', poison: '#A040A0',
  ground: '#E0C068', flying: '#A890F0', psychic: '#F85888', bug: '#A8B820',
  rock: '#B8A038', ghost: '#705898', dragon: '#7038F8', dark: '#705848',
  steel: '#B8B8D0', fairy: '#EE99AC',
}

function TypeBadge({ type }) {
  return (
    <span className="px-1.5 py-0.5 text-[9px] text-white rounded-full font-bold uppercase"
      style={{ backgroundColor: TYPE_COLORS[type] || '#6B7280' }}>
      {type}
    </span>
  )
}

export default function GenerationsPage() {
  const [generations, setGenerations] = useState([])
  const [selectedGen, setSelectedGen] = useState(null)
  const [genPokemon, setGenPokemon] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingPoke, setLoadingPoke] = useState(false)

  useEffect(() => {
    getGenerations()
      .then(setGenerations)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = async (gen) => {
    setSelectedGen(gen)
    setLoadingPoke(true)
    setGenPokemon([])
    try {
      const data = await getGenerationPokemon(gen.id)
      setGenPokemon(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingPoke(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-poke-accent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Generations</h2>
      <p className="text-poke-gray">Click a generation to see the Pokémon discovered in that era.</p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...generations].reverse().map((gen) => (
          <button
            key={gen.id}
            onClick={() => handleSelect(gen)}
            className={`rounded-xl border p-5 text-left transition-all ${
              selectedGen?.id === gen.id
                ? 'bg-poke-accent/10 border-poke-accent/40'
                : 'bg-poke-card border-gray-800/50 hover:border-poke-accent/30'
            }`}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">🗺️</span>
              <div>
                <h3 className="font-semibold text-sm">{gen.name}</h3>
                <p className="text-[10px] text-poke-gray">
                  {gen.date_utc
                    ? new Date(gen.date_utc).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
                    : 'TBD'}
                </p>
              </div>
            </div>
            <p className="text-xs text-poke-gray/80">{gen.details}</p>
          </button>
        ))}
      </div>

      {selectedGen && (
        <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              {selectedGen.name} — Pokémon
            </h3>
            <button
              onClick={() => { setSelectedGen(null); setGenPokemon([]) }}
              className="text-xs text-poke-gray hover:text-white transition-colors"
            >
              Close
            </button>
          </div>

          {loadingPoke ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-poke-accent"></div>
            </div>
          ) : genPokemon.length === 0 ? (
            <div className="text-center py-8 text-poke-gray text-sm">
              No Pokémon data available for this generation.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {genPokemon.map((p) => (
                <div key={p.id}
                  className="rounded-xl bg-poke-dark border border-gray-800/50 p-3 text-center hover:border-poke-accent/30 transition-all group"
                >
                  {p.sprite_url ? (
                    <img src={p.sprite_url} alt={p.name}
                      className="w-16 h-16 object-contain mx-auto group-hover:scale-110 transition-transform" />
                  ) : (
                    <div className="w-16 h-16 mx-auto flex items-center justify-center text-2xl">⚡</div>
                  )}
                  <p className="text-xs font-medium mt-2 truncate">{p.name}</p>
                  <div className="flex gap-1 justify-center mt-1 flex-wrap">
                    {p.type?.split('/').map(t => <TypeBadge key={t} type={t.trim()} />)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {generations.length === 0 && (
        <div className="text-center py-12 text-poke-gray">No generations found.</div>
      )}
    </div>
  )
}
