import axios from 'axios'

const MISSION_API = import.meta.env.VITE_MISSION_SERVICE_URL || '/api/mission'
const SUBSCRIBER_API = import.meta.env.VITE_SUBSCRIBER_SERVICE_URL || '/api/subscriber'

const missionClient = axios.create({ baseURL: MISSION_API, timeout: 15000 })
const subscriberClient = axios.create({ baseURL: SUBSCRIBER_API, timeout: 15000 })

// UUID v4 regex for sid validation
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function encodePathParam(param) {
  return encodeURIComponent(param)
}

function validateSid(sid) {
  return UUID_V4_REGEX.test(sid)
}

// Safe sprite URL helper - only allow https, fallback to placeholder
export function safeSprite(url) {
  if (!url) return null
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:') return null
    return url
  } catch {
    return null
  }
}

export const getGenerations = () => missionClient.get('/generations').then(r => r.data)
export const getGenerationPokemon = (id) =>
  missionClient.get(`/generations/${encodePathParam(id)}/pokemon`).then(r => r.data)
export const getLatestGeneration = () => missionClient.get('/generations/latest').then(r => r.data)
export const getPokemon = () => missionClient.get('/pokemon').then(r => r.data)
export const getOnePokemon = (id) => missionClient.get(`/pokemon/${encodePathParam(id)}`).then(r => r.data)
export const getTypes = () => missionClient.get('/types').then(r => r.data)

export const subscribe = (data) => subscriberClient.post('/subscribe', data).then(r => r.data)
export const getAlerts = (subscriberId) => {
  if (!validateSid(subscriberId)) throw new Error('Invalid subscriber ID')
  return subscriberClient.get(`/${encodePathParam(subscriberId)}/alerts`).then(r => r.data)
}
export const markAlertRead = (subscriberId, alertId) => {
  if (!validateSid(subscriberId) || !validateSid(alertId)) throw new Error('Invalid ID')
  return subscriberClient.put(`/${encodePathParam(subscriberId)}/alerts/${encodePathParam(alertId)}/read`).then(r => r.data)
}
export const unsubscribe = (subscriberId, email) => {
  if (!validateSid(subscriberId)) throw new Error('Invalid subscriber ID')
  return subscriberClient.delete(`/${encodePathParam(subscriberId)}`, { params: { email } }).then(r => r.data)
}