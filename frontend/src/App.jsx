import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import GenerationsPage from './components/GenerationsPage'
import PokemonPage from './components/PokemonPage'
import SubscribePage from './components/SubscribePage'

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
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
