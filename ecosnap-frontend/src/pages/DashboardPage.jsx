import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { ReportCard } from '../components/reports/ReportCard'
import { MiniMap } from '../components/map/MiniMap'
import { SkeletonCard, SkeletonRow } from '../components/common/Skeletons'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { useReports } from '../hooks/useReports'
import { getNotifications, getUserBadges } from '../services/api'
import { BADGES, DEMO_NOTIFICATIONS, fmtHazard, formatDate } from '../utils/helpers'

export function DashboardPage() {
  const { user, profile, signOut } = useAuth()
  const { notifications, setNotifications, badges, setBadges, userLoc, nearbyReports } = useApp()
  const { myReports, loadMine, fetchMine } = useReports()
  const [tab, setTab]     = useState('reports') // reports | activity
  const [loadN, setLoadN] = useState(false)
  const nav = useNavigate()
  const didFetch = useRef(false)

  useEffect(() => {
    if (didFetch.current) return
    didFetch.current = true
    fetchMine()
    loadNotifs()
    loadBadges()
  }, [])

  async function loadNotifs() {
    if (!user) return
    setLoadN(true)
    try { const d = await getNotifications(user.id); setNotifications(Array.isArray(d) ? d : []) }
    catch { setNotifications(DEMO_NOTIFICATIONS) }
    finally { setLoadN(false) }
  }

  async function loadBadges() {
    if (!user) return
    try { const d = await getUserBadges(user.id); setBadges(Array.isArray(d.badges ?? d) ? (d.badges || d) : []) }
    catch { setBadges([{ badge_id:'first_report' }, { badge_id:'five_reports' }, { badge_id:'community_voice' }]) }
  }

  const resolved   = myReports.filter(r => r.status === 'resolved').length
  const earnedIds  = new Set(badges.map(b => b.badge_id))
  const displayName = profile?.full_name || user?.user_metadata?.full_name || 'there'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning,' : hour < 17 ? 'Good afternoon,' : 'Good evening,'

  /* Notification dot color */
  function notifDotColor(s) {
    return { resolved:'var(--olive)', in_review:'var(--orange)', open:'var(--blue)' }[s] || 'var(--green)'
  }

  return (
    <Layout showFAB={true}>
      <div className="page-enter">

        {/* ── Header ── */}
        <div style={{ padding:'14px 14px 10px', background:'var(--bg)', borderBottom:'0.5px solid var(--border)' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
            <div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>{greeting}</div>
              <div style={{ fontSize:16, fontWeight:500 }}>{displayName}</div>
            </div>
            <button
              id="signout-btn"
              onClick={signOut}
              style={{ background:'none', border:'none', cursor:'pointer', fontSize:11, color:'var(--text3)', padding:'4px 8px',
                       border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)' }}
            >
              Sign out
            </button>
          </div>

          {/* Impact strip */}
          <div style={{ display:'flex', gap:6 }}>
            <div className="impact-chip">
              <div style={{ fontSize:14, fontWeight:500, color:'var(--green-dark)' }}>{myReports.length}</div>
              <div style={{ fontSize:9, color:'var(--green-dark)', opacity:.8 }}>Reports filed</div>
            </div>
            <div className="impact-chip">
              <div style={{ fontSize:14, fontWeight:500, color:'var(--green-dark)' }}>
                {myReports.reduce((a,r) => a+(r.upvotes||0), 0)}
              </div>
              <div style={{ fontSize:9, color:'var(--green-dark)', opacity:.8 }}>Upvotes given</div>
            </div>
            <div className="impact-chip">
              <div style={{ fontSize:14, fontWeight:500, color:'var(--green-dark)' }}>{resolved}</div>
              <div style={{ fontSize:9, color:'var(--green-dark)', opacity:.8 }}>Issues resolved</div>
            </div>
          </div>
        </div>

        <div style={{ padding:'0 14px' }}>

          {/* ── My Reports + Activity tabs ── */}
          <div style={{ marginTop:10 }}>
            <div className="sec-head">
              <span className="sec-title">Your reports</span>
              <span className="sec-link" onClick={() => nav('/nearby')}>See all</span>
            </div>

            {/* Tab row */}
            <div style={{ display:'flex', borderBottom:'0.5px solid var(--border)', marginBottom:8 }}>
              {[['reports','My Reports'],['activity','Recent activity']].map(([k,l]) => (
                <button key={k} id={`tab-${k}`} onClick={() => setTab(k)} style={{
                  flex:1, padding:'6px 0', fontSize:11, fontWeight:500,
                  cursor:'pointer', background:'none', border:'none', fontFamily:'Inter,sans-serif',
                  color: tab===k ? 'var(--green-dark)' : 'var(--text2)',
                  borderBottom: `2px solid ${tab===k ? 'var(--green)' : 'transparent'}`,
                  transition:'all .15s',
                }}>{l}</button>
              ))}
            </div>

            {/* Reports tab */}
            {tab === 'reports' && (
              <>
                {loadMine ? (
                  <><SkeletonCard /><SkeletonCard /></>
                ) : myReports.length === 0 ? (
                  <div style={{ textAlign:'center', padding:'24px 0', color:'var(--text3)', fontSize:13 }}>
                    <div style={{ fontSize:28, marginBottom:8 }}>🌿</div>
                    No reports yet — tap the button below to file your first!
                  </div>
                ) : (
                  myReports.map((r, i) => (
                    <div key={r.id} className="anim-fadeUp" style={{ animationDelay:`${i*40}ms` }}>
                      <ReportCard report={r} showProgress={true} showUpvote={false} />
                    </div>
                  ))
                )}
              </>
            )}

            {/* Activity tab */}
            {tab === 'activity' && (
              <div>
                {loadN ? (
                  <><SkeletonRow /><SkeletonRow /><SkeletonRow /></>
                ) : notifications.length === 0 ? (
                  <div style={{ textAlign:'center', padding:'20px 0', color:'var(--text3)', fontSize:12 }}>No activity yet</div>
                ) : notifications.map(n => (
                  <div key={n.id} className="notif-row">
                    <div className="dot" style={{ background: notifDotColor(n.new_status), marginTop:4 }} />
                    <div style={{ flex:1, fontSize:11, color:'var(--text2)', lineHeight:1.45 }}>
                      <strong style={{ color:'var(--text)', fontWeight:500 }}>
                        {n.new_status === 'resolved' ? 'Your report was resolved' :
                         n.new_status === 'in_review' ? 'Report is now in review' : 'Status updated'}
                      </strong>
                      {' — '}
                      {fmtHazard(n.hazard_type)} passed to authority.
                    </div>
                    <span style={{ fontSize:9, color:'var(--text3)', whiteSpace:'nowrap' }}>{formatDate(n.created_at)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Nearby mini-map section ── */}
          <div style={{ marginTop:14 }}>
            <div className="sec-head">
              <span className="sec-title">Nearby — help your community</span>
              <span className="sec-link" onClick={() => nav('/map')}>Map view</span>
            </div>
            <MiniMap reports={nearbyReports} userLoc={userLoc} />
          </div>

          {/* ── Badges ── */}
          <div style={{ marginTop:14 }}>
            <div className="sec-head">
              <span className="sec-title">Your badges</span>
              <span className="sec-link" onClick={() => nav('/badges')}>View all</span>
            </div>
            <div style={{ display:'flex', gap:6, overflowX:'auto', paddingBottom:4, scrollbarWidth:'none' }}>
              {BADGES.map(b => {
                const earned = earnedIds.has(b.id)
                return (
                  <div key={b.id} className={`badge-chip${earned?' earned':' locked'}`}>
                    <div style={{ fontSize:16, marginBottom:2 }}>{b.emoji}</div>
                    <div style={{ fontSize:9, color: earned ? 'var(--green-dark)' : 'var(--text2)', lineHeight:1.2 }}>{b.name}</div>
                  </div>
                )
              })}
            </div>
          </div>

          <div style={{ height:16 }} />
        </div>
      </div>
    </Layout>
  )
}
