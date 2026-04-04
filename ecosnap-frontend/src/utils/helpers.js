export function formatDate(d) {
  if (!d) return ''
  const date = new Date(d), now = new Date()
  const diff = now - date
  const mins = Math.floor(diff / 60000)
  const hrs  = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (mins < 1)  return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hrs  < 24) return `${hrs}h ago`
  if (days === 1) return '1d ago'
  if (days < 30)  return `${days}d ago`
  return date.toLocaleDateString('en-IN', { day:'numeric', month:'short' })
}

export function formatDist(km) {
  if (km == null) return ''
  return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)} km`
}

export function fmtHazard(t) {
  if (!t) return 'Unknown hazard'
  return t.replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase())
}

export function statusLabel(s) {
  return { open:'Open', in_review:'In review', resolved:'Done' }[s] || s || '—'
}

export function statusProgress(s) {
  return { open:15, in_review:55, resolved:100 }[s] || 0
}

export function statusBarClass(s) {
  return { open:'pbar-open', in_review:'pbar-review', resolved:'pbar-resolved' }[s] || 'pbar-open'
}

export function sevBadgeClass(s) {
  return { high:'sev-high', medium:'sev-medium', low:'sev-low', resolved:'sev-resolved' }[s?.toLowerCase()] || 'sev-low'
}

export function markerColor(r) {
  if (r.status === 'resolved') return '#639922'
  return { high:'#E24B4A', medium:'#EF9F27', low:'#639922' }[r.severity?.toLowerCase()] || '#999'
}

export function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371
  const d2r = (d) => (d * Math.PI) / 180
  const dLat = d2r(lat2 - lat1), dLng = d2r(lng2 - lng1)
  const a = Math.sin(dLat/2)**2 + Math.cos(d2r(lat1)) * Math.cos(d2r(lat2)) * Math.sin(dLng/2)**2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
}

export const BADGES = [
  { id:'first_report',   emoji:'🌿', name:'First report',    desc:'Filed your first hazard report' },
  { id:'five_reports',   emoji:'🔥', name:'5 reports',       desc:'Filed 5 hazard reports' },
  { id:'community_voice',emoji:'📍', name:'Community voice', desc:'Received your first upvote' },
  { id:'ten_resolved',   emoji:'🏆', name:'10 resolved',     desc:'Had 10 reports resolved' },
  { id:'escalator',      emoji:'⚡', name:'Escalator',       desc:'Triggered an escalation' },
]

export const SUPABASE_BUCKET = 'hazard-photos'

export const DEMO_REPORTS = [
  { id:'d1', hazard_type:'oil_spill',       severity:'high',   status:'open',      department:'Municipal Sanitation',         lat:20.596, lng:78.963, upvotes:12, created_at: new Date(Date.now()-7200000).toISOString(),   distance_km:0.4 },
  { id:'d2', hazard_type:'e_waste',         severity:'medium', status:'in_review', department:'Pollution Control Board',       lat:20.603, lng:78.975, upvotes:5,  created_at: new Date(Date.now()-259200000).toISOString(), distance_km:0.9 },
  { id:'d3', hazard_type:'drain_blockage',  severity:'low',    status:'resolved',  department:'Drainage & Sewage Department',  lat:20.587, lng:78.952, upvotes:7,  created_at: new Date(Date.now()-1036800000).toISOString(),distance_km:1.2 },
  { id:'d4', hazard_type:'illegal_dumping', severity:'high',   status:'open',      department:'Municipal Sanitation',         lat:20.611, lng:78.991, upvotes:9,  created_at: new Date(Date.now()-18000000).toISOString(),  distance_km:1.8 },
  { id:'d5', hazard_type:'water_pollution', severity:'high',   status:'in_review', department:'Environmental Protection Agency',lat:20.579,lng:78.941, upvotes:6, created_at: new Date(Date.now()-86400000).toISOString(),  distance_km:2.3 },
]

export const DEMO_NOTIFICATIONS = [
  { id:'n1', hazard_type:'drain_blockage',  new_status:'resolved', created_at: new Date(Date.now()-172800000).toISOString(), read:false },
  { id:'n2', hazard_type:'e_waste',         new_status:'in_review', created_at: new Date(Date.now()-86400000).toISOString(), read:false },
  { id:'n3', hazard_type:'illegal_dumping', new_status:'in_review', created_at: new Date(Date.now()-18000000).toISOString(), read:true  },
]
