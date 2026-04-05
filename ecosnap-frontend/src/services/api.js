import { supabase } from '../lib/supabaseClient'

const BASE = import.meta.env.VITE_API_URL 

/** Get the current Supabase session JWT (or null if not logged in) */
async function getToken() {
  const { data } = await supabase.auth.getSession()
  return data?.session?.access_token ?? null
}

/** Build auth headers — always include Bearer token if available */
async function authHeaders(extra = {}) {
  const token = await getToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  }
}

async function req(path, opts = {}) {
  const headers = await authHeaders(opts.headers)
  const res = await fetch(`${BASE}${path}`, { ...opts, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/** POST /api/classify — sends photo URL + coords for AI classification */
export async function classifyHazard(photoUrl, lat = 0, lng = 0) {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}/api/classify`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ photo_url: photoUrl, lat, lng }),
  })
  if (!res.ok) throw new Error('AI classification failed')
  return res.json()
}

/** POST /api/reports */
export const submitReport = (data) =>
  req('/api/reports', { method: 'POST', body: JSON.stringify(data) })

/** GET /api/reports */
export const getAllReports = () => req('/api/reports')

/** GET /api/reports?user_id=x */
export const getMyReports = (uid) => req(`/api/reports?user_id=${uid}`)

/** GET /api/reports/nearby — radius in metres (backend min=100, max=50000) */
export const getNearbyReports = (lat, lng, radiusKm = 5) =>
  req(`/api/reports/nearby?lat=${lat}&lng=${lng}&radius=${radiusKm * 1000}`)

/** POST /api/reports/:id/upvote */
export const upvoteReport = (id) =>
  req(`/api/reports/${id}/upvote`, { method: 'POST' })

/** DELETE /api/reports/:id/upvote */
export const removeUpvote = (id) =>
  req(`/api/reports/${id}/upvote`, { method: 'DELETE' })

/** GET /api/me/badges — returns badge states for the authenticated user */
export const getUserBadges = () => req('/api/me/badges')

/** GET /api/me/dashboard — returns activity/notifications for the authenticated user */
export const getNotifications = () => req('/api/me/dashboard')
