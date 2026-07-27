import axios from 'axios'

const MISSION_API = import.meta.env.VITE_MISSION_SERVICE_URL || '/api/mission'
const SUBSCRIBER_API = import.meta.env.VITE_SUBSCRIBER_SERVICE_URL || '/api/subscriber'

const missionClient = axios.create({ baseURL: MISSION_API, timeout: 15000 })
const subscriberClient = axios.create({ baseURL: SUBSCRIBER_API, timeout: 15000 })

export const getGenerations = () => missionClient.get('/generations').then(r => r.data)
export const getGenerationPokemon = (id) => missionClient.get(`/generations/${id}/pokemon`).then(r => r.data)
export const getLatestGeneration = () => missionClient.get('/generations/latest').then(r => r.data)
export const getPokemon = () => missionClient.get('/pokemon').then(r => r.data)
export const getOnePokemon = (id) => missionClient.get(`/pokemon/${id}`).then(r => r.data)
export const getTypes = () => missionClient.get('/types').then(r => r.data)

export const subscribe = (data) => subscriberClient.post('/subscribe', data).then(r => r.data)
export const getAlerts = (subscriberId) => subscriberClient.get(`/${subscriberId}/alerts`).then(r => r.data)
export const markAlertRead = (subscriberId, alertId) => subscriberClient.put(`/${subscriberId}/alerts/${alertId}/read`).then(r => r.data)
export const unsubscribe = (subscriberId) => subscriberClient.delete(`/${subscriberId}`).then(r => r.data)
