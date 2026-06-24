import axios from 'axios'

// If VITE_API_URL is set (e.g. in .env), use it directly.
// Otherwise fall back to the Vite dev proxy at /api.
const BASE = import.meta.env.VITE_API_URL || '/api'

const http = axios.create({ baseURL: BASE, timeout: 30000 })

// Chat needs a much longer timeout — the LLM + RAG can take 20-40s
const chatHttp = axios.create({ baseURL: BASE, timeout: 120000 })

export const fetchRates = (loanType) =>
  http.get('/rates', { params: { loan_type: loanType } }).then(r => r.data.rates)

export const fetchAllRates = () =>
  http.get('/rates').then(r => r.data.rates)

export const sendChat = (sessionId, message) =>
  chatHttp.post('/chat', { session_id: sessionId, message }).then(r => r.data.reply)

export const clearSession = (sessionId) =>
  http.delete(`/chat/${sessionId}`)

export const fetchBanks = () =>
  http.get('/banks').then(r => r.data)
