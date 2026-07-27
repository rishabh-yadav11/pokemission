import React, { useState, useEffect } from 'react'
import { getPokemon, getGenerations } from '../api'

function TypeBadge({ type }) {
  const colors = {
    normal: 'bg-gray-500', fire: 'bg-orange-500', water: 'bg-blue-500',
    electric: 'bg-yellow-400', grass: 'bg-green-500', ice: 'bg-cyan-300',
    fighting: 'bg-red-700', poison: 'bg-purple-500', ground: 'bg-amber-600',
    flying: 'bg-indigo-300', psychic: 'bg-pink-500', bug: 'bg-lime-500',
    rock: 'bg-yellow-700', ghost: 'bg-violet-600', dragon: 'bg-indigo-600',
    dark: 'bg-gray-700', steel: 'bg-gray-400', fairy: 'bg-pink-300',
  }
  return (
    <span className={`px-2 py-0.5 text-[10px] text-white rounded-full font-bold uppercase ${colors[type] || 'bg-gray-500'}`}>
      {type}
    </span>
  )
}

export default function Dashboard() {
  const [pokemon, setPokemon] = useState([])
  const [generations, setGenerations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getPokemon(), getGenerations()])
      .then(([p, g]) => {
        setPokemon(p.slice(0, 12))
        setGenerations(g)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-poke-accent"></div>
      </div>
    )
  }

  const latestGen = generations.length > 0 ? generations[generations.length - 1] : null

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-poke-card via-poke-dark to-poke-card border border-gray-800/50 p-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-poke-accent/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-poke-red/5 rounded-full blur-3xl"></div>
        <div className="relative">
          <div className="flex items-center gap-2 text-poke-accent text-sm font-mono mb-4">
            <span className="w-2 h-2 bg-poke-green rounded-full animate-pulse"></span>
            POKÉAPI ONLINE
          </div>
          <h2 className="text-3xl font-bold mb-2">PokéMission Control</h2>
          <p className="text-poke-gray">Explore Pokémon data — species, types, regions, and generations from PokéAPI</p>
        </div>
      </div>

      {latestGen && (
        <div className="rounded-2xl bg-gradient-to-br from-poke-card to-poke-dark border border-gray-800/50 p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold">Latest Generation</h3>
            <span className="px-3 py-1 bg-poke-accent/10 text-poke-accent text-xs rounded-full font-mono">
              #{latestGen.gen_number}
            </span>
          </div>
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h4 className="text-2xl font-bold mb-4">{latestGen.name}</h4>
              <p className="text-poke-gray text-sm mb-4">{latestGen.details}</p>
              <div className="flex items-center gap-2 text-poke-gray text-sm">
                <span>🗺️</span>
                <span>Region: {latestGen.region_name || 'Unknown'}</span>
              </div>
            </div>
            <div className="flex justify-center">
              <div className="w-48 h-48 bg-poke-dark rounded-full flex items-center justify-center border border-gray-800">
                <span className="text-6xl">⚡</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {pokemon.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4">Featured Pokémon</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pokemon.map((p) => (
              <div key={p.id} className="rounded-xl bg-poke-card border border-gray-800/50 p-5 hover:border-poke-accent/30 transition-all">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm">{p.name}</h4>
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {p.type?.split('/').map(t => <TypeBadge key={t} type={t.trim()} />)}
                    </div>
                  </div>
                  {p.sprite_url ? (
                    <img src={p.sprite_url} alt={p.name} className="w-16 h-16 object-contain" />
                  ) : (
                    <span className="text-2xl">⚡</span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-poke-gray">
                  <span>#{p.id?.replace('pk-', '')}</span>
                  <span>·</span>
                  <span>{p.height_m}m</span>
                  <span>·</span>
                  <span>{p.mass_kg}kg</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {generations.length > 0 && (
        <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-8">
          <h3 className="text-xl font-semibold mb-4">Generation Timeline</h3>
          <div className="flex items-start gap-6">
            <div className="flex-1">
              <p className="text-poke-gray text-sm mb-4">
                {generations.length} generations of Pokémon games, from {generations[0]?.name} to {generations[generations.length - 1]?.name}.
              </p>
              <div className="flex flex-wrap gap-2">
                {generations.map(gen => (
                  <span key={gen.id} className="px-3 py-1 bg-poke-dark rounded-full text-xs text-poke-gray border border-gray-800">
                    {gen.name.replace('Generation ', 'Gen ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
