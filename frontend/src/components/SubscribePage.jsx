import React, { useState, useEffect, useCallback } from 'react'
import { subscribe, getAlerts, markAlertRead } from '../api'

const EVENT_OPTIONS = [
  { value: 'generation', label: '⚡ New Generation', desc: 'New Pokémon generation discovered' },
  { value: 'rare', label: '🌟 Rare Find', desc: 'Rare Pokémon sightings' },
  { value: 'region', label: '🗺️ New Region', desc: 'New region announced' },
]

export default function SubscribePage() {
  const [form, setForm] = useState({ name: '', email: '', event_types: ['generation'] })
  const [subscriberId, setSubscriberId] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const toggleEvent = (val) => {
    setForm((prev) => ({
      ...prev,
      event_types: prev.event_types.includes(val)
        ? prev.event_types.filter((v) => v !== val)
        : [...prev.event_types, val],
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const result = await subscribe(form)
      setSubscriberId(result.id)
      setMessage(result.message)
    } catch (err) {
      setError(err.response?.data?.detail || 'Subscription failed')
    } finally {
      setLoading(false)
    }
  }

  const fetchAlerts = useCallback(async () => {
    if (!subscriberId) return
    try {
      const data = await getAlerts(subscriberId)
      setAlerts(data)
    } catch {
      // ignore
    }
  }, [subscriberId])

  useEffect(() => {
    fetchAlerts()
    if (subscriberId) {
      const interval = setInterval(fetchAlerts, 15000)
      return () => clearInterval(interval)
    }
  }, [subscriberId, fetchAlerts])

  const handleMarkRead = async (alertId) => {
    try {
      await markAlertRead(subscriberId, alertId)
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, read: true } : a)))
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Poké Alerts</h2>
      <p className="text-poke-gray">Subscribe to get notified about new Pokémon discoveries, rare finds, and region updates from the PokéAPI.</p>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-poke-gray mb-1">Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                className="w-full bg-poke-dark border border-gray-800 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-poke-accent/50 transition-colors"
                placeholder="Ash Ketchum"
              />
            </div>
            <div>
              <label className="block text-sm text-poke-gray mb-1">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                className="w-full bg-poke-dark border border-gray-800 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-poke-accent/50 transition-colors"
                placeholder="ash@pokemon.com"
              />
            </div>
            <div>
              <label className="block text-sm text-poke-gray mb-2">Event Types</label>
              <div className="space-y-2">
                {EVENT_OPTIONS.map((opt) => (
                  <label key={opt.value} className="flex items-center gap-3 p-3 rounded-lg bg-poke-dark border border-gray-800 cursor-pointer hover:border-gray-700 transition-colors">
                    <input
                      type="checkbox"
                      checked={form.event_types.includes(opt.value)}
                      onChange={() => toggleEvent(opt.value)}
                      className="w-4 h-4 accent-poke-accent"
                    />
                    <div>
                      <div className="text-sm font-medium">{opt.label}</div>
                      <div className="text-xs text-poke-gray">{opt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-poke-accent/10 text-poke-accent font-semibold border border-poke-accent/30 hover:bg-poke-accent/20 transition-all disabled:opacity-50"
            >
              {loading ? 'Subscribing...' : 'Gotta Catch Em Alerts'}
            </button>
          </form>

          {message && (
            <div className="mt-4 p-4 rounded-lg bg-poke-green/10 border border-poke-green/30 text-poke-green text-sm">
              {message}
            </div>
          )}
          {error && (
            <div className="mt-4 p-4 rounded-lg bg-poke-red/10 border border-poke-red/30 text-poke-red text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-poke-card border border-gray-800/50 p-6">
          <h3 className="text-lg font-semibold mb-4">
            Alerts Feed
            {subscriberId && alerts.length > 0 && (
              <span className="ml-2 text-xs text-poke-gray font-normal">
                ({alerts.filter((a) => !a.read).length} new)
              </span>
            )}
          </h3>

          {!subscriberId ? (
            <div className="text-center py-12 text-poke-gray">
              <div className="text-4xl mb-3">⚡</div>
              <p className="text-sm">Subscribe above to get Poké alerts</p>
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12 text-poke-gray">
              <div className="text-4xl mb-3">📡</div>
              <p className="text-sm">Waiting for new alerts...</p>
              <p className="text-xs mt-1">Auto-refreshes every 15s</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border text-sm transition-all cursor-pointer ${
                    alert.read
                      ? 'bg-poke-dark/50 border-gray-800/30 opacity-60'
                      : 'bg-poke-dark border-poke-accent/20 hover:border-poke-accent/40'
                  }`}
                  onClick={() => !alert.read && handleMarkRead(alert.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`w-2 h-2 rounded-full ${
                          alert.read ? 'bg-gray-700' : 'bg-poke-accent animate-pulse'
                        }`}></span>
                        <span className="text-poke-gray text-xs uppercase">
                          {alert.event_type}
                        </span>
                      </div>
                      <p className={alert.read ? 'text-poke-gray' : 'text-white'}>{alert.message}</p>
                    </div>
                    <span className="text-[10px] text-poke-gray whitespace-nowrap">
                      {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
