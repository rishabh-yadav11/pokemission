import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const navLinks = [
  { path: '/', label: 'Dashboard' },
  { path: '/generations', label: 'Generations' },
  { path: '/pokemon', label: 'Pokémon' },
  { path: '/subscribe', label: 'Subscribe' },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="bg-poke-card border-b border-gray-800/50 sticky top-0 z-50">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <span className="text-3xl group-hover:animate-bounce">[PKMN]</span>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                PokéMission
              </h1>
              <p className="text-[10px] text-poke-gray uppercase tracking-widest">Pokémon API Explorer</p>
            </div>
          </Link>
          <nav className="flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-poke-accent/10 text-poke-accent shadow-lg shadow-poke-accent/5'
                      : 'text-poke-gray hover:text-white hover:bg-white/5'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
