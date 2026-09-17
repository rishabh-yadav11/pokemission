import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import GenerationsPage from './components/GenerationsPage'
import PokemonPage from './components/PokemonPage'
import SubscribePage from './components/SubscribePage'

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-poke-accent">404</h1>
      <p className="text-poke-gray mt-4 text-lg">Page not found</p>
      <p className="text-poke-gray mt-2">The page you're looking for doesn't exist or has been moved.</p>
      <button
        onClick={() => window.location.href = '/'}
        className="mt-6 px-6 py-3 rounded-lg bg-poke-accent/10 text-poke-accent font-semibold border border-poke-accent/30 hover:bg-poke-accent/20 transition-all"
      >
        Go Home
      </button>
    </div>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-poke-dark">
        <Header />
        <main className="container mx-auto px-4 py-6 max-w-7xl">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generations" element={<GenerationsPage />} />
            <Route path="/pokemon" element={<PokemonPage />} />
            <Route path="/subscribe" element={<SubscribePage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
