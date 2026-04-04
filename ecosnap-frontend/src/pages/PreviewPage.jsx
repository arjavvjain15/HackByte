/**
 * PreviewPage  (/preview)
 * Dev-only hub to jump to any screen without logging in.
 * Remove from production router before shipping.
 */
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

const SCREENS = [
  {
    id: 'landing',
    title: 'Login / Landing',
    desc: 'Google OAuth entry screen',
    emoji: '🔑',
    route: '/preview/landing',
    tag: 'Auth',
    tagColor: '#6366f1',
  },
  {
    id: 'dashboard',
    title: 'User Dashboard',
    desc: 'My reports, activity, mini-map, badges',
    emoji: '📊',
    route: '/preview/dashboard',
    tag: 'User',
    tagColor: '#10b981',
  },
  {
    id: 'report',
    title: 'Report Flow',
    desc: 'Camera → AI Analysis → Location → Review',
    emoji: '📷',
    route: '/preview/report',
    tag: 'User',
    tagColor: '#10b981',
  },
  {
    id: 'ai-result',
    title: 'AI Result Screen',
    desc: 'Hazard classified, severity, department',
    emoji: '🤖',
    route: '/preview/ai-result',
    tag: 'Screen',
    tagColor: '#f59e0b',
  },
  {
    id: 'map',
    title: 'Map View',
    desc: 'Full hazard map with pins',
    emoji: '🗺️',
    route: '/preview/map',
    tag: 'User',
    tagColor: '#10b981',
  },
  {
    id: 'nearby',
    title: 'Nearby Hazards',
    desc: 'Community feed sorted by distance',
    emoji: '📍',
    route: '/preview/nearby',
    tag: 'User',
    tagColor: '#10b981',
  },
  {
    id: 'badges',
    title: 'Badges Page',
    desc: 'Earned and locked achievement badges',
    emoji: '🏆',
    route: '/preview/badges',
    tag: 'User',
    tagColor: '#10b981',
  },
  {
    id: 'letter',
    title: 'Complaint Letter',
    desc: 'AI-generated formal complaint modal',
    emoji: '📋',
    route: '/preview/letter',
    tag: 'Modal',
    tagColor: '#8b5cf6',
  },
  {
    id: 'admin',
    title: 'Admin Dashboard',
    desc: 'Manage all reports, update statuses',
    emoji: '🛡️',
    route: '/preview/admin',
    tag: 'Admin',
    tagColor: '#ef4444',
  },
]

export function PreviewPage() {
  const nav = useNavigate()
  const [hoveredId, setHoveredId] = useState(null)

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
      fontFamily: 'Inter, sans-serif',
      color: '#f8fafc',
    }}>
      {/* ── Top bar ── */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(15,23,42,0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '0 20px',
        display: 'flex', alignItems: 'center', gap: 12, height: 52,
      }}>
        {/* Badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 7,
          background: 'linear-gradient(90deg, #10b98120, #6366f120)',
          border: '1px solid rgba(99,102,241,.35)',
          borderRadius: 99, padding: '3px 10px 3px 6px',
        }}>
          <span style={{
            display: 'inline-block', width: 7, height: 7,
            borderRadius: '50%', background: '#10b981',
            boxShadow: '0 0 0 3px rgba(16,185,129,.25)',
            animation: 'pulse 2s infinite',
          }} />
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: .5, color: '#a5f3c9' }}>
            PREVIEW MODE ON
          </span>
        </div>

        <div style={{ flex: 1, fontSize: 12, color: 'rgba(255,255,255,.45)' }}>
          Dev-only · Auth bypassed · Mock data loaded
        </div>

        <button
          id="preview-back-to-app-btn"
          onClick={() => nav('/')}
          style={{
            background: 'rgba(255,255,255,.07)',
            border: '1px solid rgba(255,255,255,.12)',
            color: '#e2e8f0',
            borderRadius: 8, padding: '5px 14px',
            fontSize: 12, fontWeight: 500, cursor: 'pointer',
            fontFamily: 'Inter, sans-serif',
            transition: 'background .15s',
          }}
          onMouseEnter={e => e.target.style.background = 'rgba(255,255,255,.13)'}
          onMouseLeave={e => e.target.style.background = 'rgba(255,255,255,.07)'}
        >
          ← Back to App
        </button>
      </div>

      {/* ── Hero ── */}
      <div style={{ padding: '40px 24px 20px', maxWidth: 620, margin: '0 auto' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: 'rgba(99,102,241,.15)', border: '1px solid rgba(99,102,241,.3)',
          borderRadius: 99, padding: '3px 12px', fontSize: 11, fontWeight: 500,
          color: '#a5b4fc', marginBottom: 16, letterSpacing: .4,
        }}>
          🔬 DEVELOPER PREVIEW
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: '0 0 8px', lineHeight: 1.25 }}>
          EcoSnap{' '}
          <span style={{ background: 'linear-gradient(90deg,#10b981,#6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Screen Explorer
          </span>
        </h1>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,.5)', margin: 0, lineHeight: 1.6 }}>
          Jump to any screen instantly. Auth is skipped and all pages use mock data.
          {' '}<span style={{ color: '#f59e0b' }}>Remove this route before shipping to production.</span>
        </p>
      </div>

      {/* ── Grid ── */}
      <div style={{
        maxWidth: 640, margin: '0 auto', padding: '8px 20px 60px',
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(268px, 1fr))', gap: 14,
      }}>
        {SCREENS.map(s => {
          const hovered = hoveredId === s.id
          return (
            <div
              key={s.id}
              id={`preview-card-${s.id}`}
              onMouseEnter={() => setHoveredId(s.id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{
                background: hovered
                  ? 'rgba(255,255,255,.075)'
                  : 'rgba(255,255,255,.04)',
                border: `1px solid ${hovered ? 'rgba(255,255,255,.18)' : 'rgba(255,255,255,.08)'}`,
                borderRadius: 16,
                padding: '18px 18px 16px',
                cursor: 'pointer',
                transition: 'all .2s ease',
                transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
                boxShadow: hovered ? '0 12px 32px rgba(0,0,0,.4)' : 'none',
                display: 'flex', flexDirection: 'column', gap: 12,
              }}
              onClick={() => nav(s.route)}
            >
              {/* Card top row */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                {/* Emoji icon */}
                <div style={{
                  width: 44, height: 44, borderRadius: 12, fontSize: 22,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: 'rgba(255,255,255,.06)',
                  border: '1px solid rgba(255,255,255,.08)',
                  flexShrink: 0,
                }}>
                  {s.emoji}
                </div>
                {/* Tag */}
                <span style={{
                  fontSize: 9, fontWeight: 600, letterSpacing: .6, textTransform: 'uppercase',
                  padding: '3px 8px', borderRadius: 99,
                  background: `${s.tagColor}20`,
                  color: s.tagColor,
                  border: `1px solid ${s.tagColor}40`,
                }}>
                  {s.tag}
                </span>
              </div>

              {/* Title & desc */}
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: '#f1f5f9' }}>
                  {s.title}
                </div>
                <div style={{ fontSize: 11.5, color: 'rgba(255,255,255,.45)', lineHeight: 1.5 }}>
                  {s.desc}
                </div>
              </div>

              {/* Open button */}
              <button
                id={`preview-open-${s.id}`}
                onClick={e => { e.stopPropagation(); nav(s.route) }}
                style={{
                  alignSelf: 'flex-start',
                  background: hovered ? 'rgba(255,255,255,.12)' : 'rgba(255,255,255,.06)',
                  border: '1px solid rgba(255,255,255,.12)',
                  color: '#e2e8f0',
                  borderRadius: 8, padding: '5px 14px',
                  fontSize: 11, fontWeight: 500, cursor: 'pointer',
                  fontFamily: 'Inter, sans-serif',
                  transition: 'all .15s',
                  display: 'flex', alignItems: 'center', gap: 5,
                }}
              >
                Open →
              </button>
            </div>
          )
        })}
      </div>

      {/* Pulse keyframe */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: .4; }
        }
      `}</style>
    </div>
  )
}
