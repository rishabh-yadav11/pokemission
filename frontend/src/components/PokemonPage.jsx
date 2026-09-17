import React, { useState, useEffect, useMemo } from 'react'
import { getPokemon, safeSprite } from '../api'

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
      style={{ backgroundColor: TYPE_COLORS[type.trim()] || '#6B7280' }}>
      {type.trim()}
    </span>
  )
}

function SpecBar({ label, value, max, unit }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-poke-gray">{label}</span>
        <span className="text-white font-mono">{value}{unit}</span>
      </div>
      <div className="h-1.5 bg-poke-dark rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-poke-accent to-poke-accent rounded-full transition-all" style={{ width: `${pct}%` }}></div>
      </div>
    </div>
  )
}

export default function PokemonPage() {
  const [pokemon, setPokemon] = useState([])
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getPokemon()
      .then((data) => {
        setPokemon(data)
        if (data.length > 0) setSelected(data[0])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    if (!search.trim()) return pokemon
    const q = search.toLowerCase()
    return pokemon.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.type?.toLowerCase().includes(q) ||
      p.id?.toLowerCase().includes(q)
    )
  }, [pokemon, search])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-poke-accent"></div>
      </div>
    )
  }

  const maxHeight = Math.max(...pokemon.map((r) => r.height_m || 0))
  const maxMass = Math.max(...pokemon.map((r) => r.mass_kg || 0))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h2 className="text-2xl font-bold">Pokémon ({pokemon.length})</h2>
        <input
          type="text"
          placeholder="Search by name, type, or ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full sm:w-72 bg-poke-card border border-gray-800 rounded-lg px-4 py-2 text-sm text-white placeholder-poke-gray focus:outline-none focus:border-poke-accent/50"
        />
      </div>

      <div className="flex gap-2 flex-wrap max-h-48 overflow-y-auto p-2 bg-poke-card/50 rounded-xl border border-gray-800/50">
        {filtered.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelected(p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              selected?.id === p.id
                ? 'bg-poke-accent/10 text-poke-accent border border-poke-accent/30'
                : 'bg-poke-dark text-poke-gray border border-gray-800 hover:border-gray-700'
            }`}
          >
            {p.name}
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="w-full text-center py-4 text-poke-gray text-sm">No Pokémon match your search.</div>
        )}
      </div>

      {selected && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-6">
            {safeSprite(selected.sprite_url) ? (
              <img
                src={safeSprite(selected.sprite_url)}
                alt={selected.name}
                className="w-full h-80 object-contain rounded-xl"
                referrerPolicy="no-referrer"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
            ) : (
              <div className="w-full h-80 bg-poke-dark rounded-xl flex items-center justify-center text-6xl">⚡</div>
            )}
            <h3 className="text-xl font-bold mt-4">{selected.name}</h3>
            <div className="flex gap-1 mt-2 flex-wrap">
              {selected.type?.split('/').map(t => <TypeBadge key={t} type={t.trim()} />)}
            </div>
            <p className="text-poke-gray text-sm mt-3">{selected.description}</p>
            <div className="flex gap-2 mt-3">
              <span className="px-2 py-0.5 text-xs bg-poke-card text-poke-gray rounded border border-gray-800">
                #{selected.id?.replace('pk-', '')}
              </span>
            </div>
          </div>

          <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-6">
            <h4 className="text-sm font-semibold text-poke-gray uppercase tracking-wider mb-6">Stats</h4>
            <SpecBar label="Height" value={selected.height_m || 0} max={maxHeight} unit="m" />
            <SpecBar label="Weight" value={selected.mass_kg || 0} max={maxMass} unit="kg" />
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="rounded-lg bg-poke-dark p-4">
                <div className="text-poke-gray text-xs">Types</div>
                <div className="text-xl font-bold font-mono">{selected.types_count}</div>
              </div>
              <div className="rounded-lg bg-poke-dark p-4">
                <div className="text-poke-gray text-xs">Abilities</div>
                <div className="text-xl font-bold font-mono">{selected.abilities_count}</div>
              </div>
              <div className="rounded-lg bg-poke-dark p-4">
                <div className="text-poke-gray text-xs">Abilities</div>
                <div className="text-sm font-bold font-mono truncate">{selected.abilities || 'N/A'}</div>
              </div>
              <div className="rounded-lg bg-poke-dark p-4">
                <div className="text-poke-gray text-xs">Base XP</div>
                <div className="text-xl font-bold font-mono">{selected.base_experience || 0}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
