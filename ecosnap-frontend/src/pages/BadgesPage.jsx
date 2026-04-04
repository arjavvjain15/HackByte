import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { SkeletonBadge } from '../components/common/Skeletons'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { getUserBadges, getNotifications } from '../services/api'
import { BADGES, DEMO_NOTIFICATIONS, fmtHazard, formatDate } from '../utils/helpers'

export function BadgesPage() {
  const { user, profile, signOut } = useAuth()
  const { badges, setBadges, notifications, setNotifications } = useApp()
  const nav = useNavigate()
  const did = useRef(false)

  useEffect(() => {
    if (did.current || !user) return
    did.current = true
    getUserBadges(user.id)
      .then(d => setBadges(Array.isArray(d.badges ?? d) ? (d.badges || d) : []))
      .catch(() => setBadges([{ badge_id:'first_report' }, { badge_id:'community_voice' }]))
    getNotifications(user.id)
      .then(d => setNotifications(Array.isArray(d) ? d : []))
      .catch(() => setNotifications(DEMO_NOTIFICATIONS))
  }, [user, setBadges, setNotifications])

  const earnedIds = new Set(badges.map(b => b.badge_id))
  const earnedCount = BADGES.filter(b => earnedIds.has(b.id)).length
  const displayName = profile?.full_name || user?.user_metadata?.full_name || 'User'
  const email = user?.email || ''

  return (
    <Layout showFAB={false}>
      <div className="page-enter">

        {/* ── Profile card ── */}
        <div style={{ padding:'20px 14px 14px', background:'var(--bg)', borderBottom:'0.5px solid var(--border)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:12 }}>
            <div style={{
              width:44, height:44, borderRadius:'50%',
              background:'var(--green-light)',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:20, flexShrink:0,
            }}>
              {displayName.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex:1 }}>
              <div style={{ fontWeight:500, fontSize:14 }}>{displayName}</div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>{email}</div>
            </div>
            <button
              id="signout-profile-btn"
              onClick={signOut}
              style={{ background:'none', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', padding:'5px 10px', cursor:'pointer', fontSize:11, color:'var(--text2)', fontFamily:'Inter,sans-serif' }}
            >
              Sign out
            </button>
          </div>
        </div>

        <div style={{ padding:'12px 14px' }}>

          {/* ── Badge progress ── */}
          <div style={{ marginBottom:14 }}>
            <div className="sec-head">
              <span className="sec-title">Badges</span>
              <span style={{ fontSize:11, color:'var(--green-dark)', fontWeight:500 }}>{earnedCount}/{BADGES.length} earned</span>
            </div>

            {/* Progress bar */}
            <div className="pbar" style={{ marginBottom:10 }}>
              <div className="pbar-fill pbar-resolved" style={{ width:`${(earnedCount/BADGES.length)*100}%` }} />
            </div>

            {/* Earned */}
            {earnedCount > 0 && (
              <>
                <div style={{ fontSize:10, color:'var(--green-dark)', fontWeight:500, marginBottom:6, textTransform:'uppercase', letterSpacing:.5 }}>✅ Earned</div>
                <div style={{ display:'flex', gap:6, marginBottom:12, flexWrap:'wrap' }}>
                  {BADGES.filter(b => earnedIds.has(b.id)).map(b => (
                    <div key={b.id} className="badge-chip earned" title={b.desc}>
                      <div style={{ fontSize:16, marginBottom:2 }}>{b.emoji}</div>
                      <div style={{ fontSize:9, color:'var(--green-dark)', lineHeight:1.2 }}>{b.name}</div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Locked */}
            <div style={{ fontSize:10, color:'var(--text3)', fontWeight:500, marginBottom:6, textTransform:'uppercase', letterSpacing:.5 }}>🔒 Locked</div>
            <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
              {BADGES.filter(b => !earnedIds.has(b.id)).map(b => (
                <div key={b.id} className="badge-chip locked" title={b.desc}>
                  <div style={{ fontSize:16, marginBottom:2 }}>{b.emoji}</div>
                  <div style={{ fontSize:9, color:'var(--text2)', lineHeight:1.2 }}>{b.name}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Activity / Notifications ── */}
          <div style={{ marginTop:16 }}>
            <div className="sec-head">
              <span className="sec-title">Recent activity</span>
              <span style={{ fontSize:9, color:'var(--text3)' }}>{notifications.filter(n=>!n.read).length} unread</span>
            </div>
            {notifications.length === 0 ? (
              <div style={{ textAlign:'center', padding:'16px 0', color:'var(--text3)', fontSize:12 }}>No notifications yet</div>
            ) : notifications.map(n => {
              const dotColor = { resolved:'var(--olive)', in_review:'var(--orange)', open:'var(--blue)' }[n.new_status] || 'var(--green)'
              return (
                <div key={n.id} className="notif-row">
                  <div className="dot" style={{ background:dotColor, marginTop:4 }} />
                  <div style={{ flex:1, fontSize:11, color:'var(--text2)', lineHeight:1.45 }}>
                    <span style={{ color:'var(--text)', fontWeight:500 }}>
                      {n.new_status === 'resolved' ? 'Your report was resolved' :
                       n.new_status === 'in_review' ? 'Report is now in review' : 'Status updated'}
                    </span>
                    {' — '}
                    {fmtHazard(n.hazard_type)} passed to authority.
                  </div>
                  <span style={{ fontSize:9, color:'var(--text3)', whiteSpace:'nowrap' }}>{formatDate(n.created_at)}</span>
                </div>
              )
            })}
          </div>

          {/* ── Quick links ── */}
          <div style={{ marginTop:20, borderTop:'0.5px solid var(--border)', paddingTop:14 }}>
            {[
              { label:'🗺️  Community Map', to:'/map' },
              { label:'📋  Nearby reports', to:'/nearby' },
              { label:'➕  File a new report', to:'/report' },
            ].map(({ label, to }) => (
              <div
                key={to}
                onClick={() => nav(to)}
                style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 0', borderBottom:'0.5px solid var(--border)', cursor:'pointer' }}
              >
                <span style={{ fontSize:13, color:'var(--text)' }}>{label}</span>
                <span style={{ color:'var(--text3)', fontSize:16 }}>›</span>
              </div>
            ))}
          </div>
          <div style={{ height:16 }} />
        </div>
      </div>
    </Layout>
  )
}
