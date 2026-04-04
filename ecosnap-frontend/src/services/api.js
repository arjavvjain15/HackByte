const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/** POST multipart for photo + classify */
export async function classifyHazard(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/api/classify`, { method:'POST', body:fd })
  if (!res.ok) throw new Error('AI classification failed')
  return res.json()
}

/** POST /api/reports */
export const submitReport = (data) => req('/api/reports', { method:'POST', body:JSON.stringify(data) })

/** GET /api/reports */
export const getAllReports = () => req('/api/reports')

/** GET /api/reports?user_id=x */
export const getMyReports = (uid) => req(`/api/reports?user_id=${uid}`)

/** GET /api/reports/nearby */
export const getNearbyReports = (lat, lng, r = 5) =>
  req(`/api/reports/nearby?lat=${lat}&lng=${lng}&radius=${r}`)

/** POST /api/reports/:id/upvote */
export const upvoteReport = (id) => req(`/api/reports/${id}/upvote`, { method:'POST' })

/** DELETE /api/reports/:id/upvote */
export const removeUpvote = (id) => req(`/api/reports/${id}/upvote`, { method:'DELETE' })

/** GET /api/badges/:uid */
export const getUserBadges = (uid) => req(`/api/badges/${uid}`)

/** GET /api/notifications/:uid */
export const getNotifications = (uid) => req(`/api/notifications/${uid}`)
