/* ─── Preview Mode: all mock data lives here ─────────────────────────────── */

export const MOCK_USER = {
  id: 'preview-user-001',
  email: 'alex.preview@ecosnap.dev',
  user_metadata: { full_name: 'Alex Preview', avatar_url: '' },
}

export const MOCK_PROFILE = {
  id: 'preview-user-001',
  full_name: 'Alex Preview',
  email: 'alex.preview@ecosnap.dev',
  is_admin: false,
}

export const MOCK_ADMIN_PROFILE = {
  id: 'preview-admin-001',
  full_name: 'Admin Preview',
  email: 'admin@ecosnap.dev',
  is_admin: true,
}

export const MOCK_REPORTS = [
  {
    id: 'r1',
    hazard_type: 'oil_spill',
    severity: 'high',
    status: 'open',
    department: 'Municipal Sanitation',
    lat: 20.596,
    lng: 78.963,
    upvotes: 12,
    created_at: new Date(Date.now() - 7200000).toISOString(),
    distance_km: 0.4,
    photo_url: '',
    user_id: 'preview-user-001',
  },
  {
    id: 'r2',
    hazard_type: 'e_waste',
    severity: 'medium',
    status: 'in_review',
    department: 'Pollution Control Board',
    lat: 20.603,
    lng: 78.975,
    upvotes: 5,
    created_at: new Date(Date.now() - 259200000).toISOString(),
    distance_km: 0.9,
    photo_url: '',
    user_id: 'preview-user-001',
  },
  {
    id: 'r3',
    hazard_type: 'drain_blockage',
    severity: 'low',
    status: 'resolved',
    department: 'Drainage & Sewage Department',
    lat: 20.587,
    lng: 78.952,
    upvotes: 7,
    created_at: new Date(Date.now() - 1036800000).toISOString(),
    distance_km: 1.2,
    photo_url: '',
    user_id: 'preview-user-001',
  },
  {
    id: 'r4',
    hazard_type: 'illegal_dumping',
    severity: 'high',
    status: 'open',
    department: 'Municipal Sanitation',
    lat: 20.611,
    lng: 78.991,
    upvotes: 9,
    created_at: new Date(Date.now() - 18000000).toISOString(),
    distance_km: 1.8,
    photo_url: '',
    user_id: 'preview-user-002',
  },
  {
    id: 'r5',
    hazard_type: 'water_pollution',
    severity: 'high',
    status: 'in_review',
    department: 'Environmental Protection Agency',
    lat: 20.579,
    lng: 78.941,
    upvotes: 6,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    distance_km: 2.3,
    photo_url: '',
    user_id: 'preview-user-003',
  },
]

export const MOCK_NOTIFICATIONS = [
  { id: 'n1', hazard_type: 'drain_blockage', new_status: 'resolved', created_at: new Date(Date.now() - 172800000).toISOString(), read: false },
  { id: 'n2', hazard_type: 'e_waste', new_status: 'in_review', created_at: new Date(Date.now() - 86400000).toISOString(), read: false },
  { id: 'n3', hazard_type: 'illegal_dumping', new_status: 'in_review', created_at: new Date(Date.now() - 18000000).toISOString(), read: true },
]

export const MOCK_BADGES = [
  { badge_id: 'first_report' },
  { badge_id: 'five_reports' },
  { badge_id: 'community_voice' },
]

export const MOCK_AI_RESULT = {
  hazard_type: 'oil_spill',
  severity: 'high',
  department: 'Municipal Sanitation',
  photo_url: '',
}

export const MOCK_SUBMITTED_REPORT = {
  id: 'DEMO-PREVIEW-001',
  hazard_type: 'oil_spill',
  severity: 'high',
  status: 'open',
  department: 'Municipal Sanitation',
  lat: 20.596,
  lng: 78.963,
  upvotes: 0,
  created_at: new Date().toISOString(),
  photo_url: '',
  complaint: null,
}

export const MOCK_USER_LOC = { lat: 20.5937, lng: 78.9629 }
