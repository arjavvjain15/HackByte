import { useState, useEffect, useRef, useCallback } from 'react'
import { HazardMap } from '../components/map/HazardMap'
import { SevBadge, StBadge, StatusDot } from '../components/common/Badges'
import { Spinner } from '../components/common/Spinner'
import { useAuth } from '../context/useAuth'
import { useGeolocation } from '../hooks/useGeolocation'
import { fmtHazard, formatDate, DEMO_REPORTS } from '../utils/helpers'
import toast from 'react-hot-toast'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const BCOLORS = ['#E24B4A','#378ADD','#EF9F27','#5DCAA5','#D85A30']
const DEPTS = [
  { color:'#E24B4A', name:'Municipal Sanitation' },
  { color:'#378ADD', name:'Drainage & Sewage' },
  { color:'#EF9F27', name:'Pollution Control' },
  { color:'#639922', name:'Parks & Forests' },
]

async function adminReq(path, opts = {}) {
  const { data } = await import('../lib/supabaseClient').then(m => m.supabase.auth.getSession())
  const token = data?.session?.access_token
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function AdminPage() {
  const { signOut } = useAuth()
  useGeolocation() // side-effect: sets userLoc in context → map shows "You are here"

  const [reports,    setReports]    = useState([])
  const [stats,      setStats]      = useState(null)
  const [breakdown,  setBreakdown]  = useState({ by_type:[], by_area:[] })
  const [selected,   setSelected]   = useState(null)
  const [loading,    setLoading]    = useState(false)
  const [actionBusy, setActionBusy] = useState(false)
  const [navItem,    setNavItem]    = useState('overview')
  const [rightTab,   setRightTab]   = useState('Reports')
  const [sortBy,     setSortBy]     = useState('newest')
  const [filter,     setFilter]     = useState('all')
  const did = useRef(false)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [dash, brk] = await Promise.all([
        adminReq('/api/admin/dashboard?include_escalations=true&limit=500'),
        adminReq('/api/admin/breakdown'),
      ])
      setStats(dash.stats || null)
      setReports(Array.isArray(dash.reports) ? dash.reports : DEMO_REPORTS)
      setBreakdown(brk || { by_type:[], by_area:[] })
      console.log('[Admin] loaded stats:', dash.stats, '| reports:', dash.reports?.length)
    } catch (e) {
      console.error('[Admin] load failed', e)
      toast.error('Failed to load: ' + e.message)
      setReports(DEMO_REPORTS)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if (did.current) return; did.current = true
    fetchAll()
  }, [fetchAll])

  async function patchStatus(newStatus) {
    if (!selected) return
    setActionBusy(true)
    const prevStatus = selected.status
    try {
      await adminReq('/api/admin/reports', {
        method: 'PATCH',
        body: JSON.stringify({ ids: [selected.id], status: newStatus }),
      })

      // Update the report in local state
      setReports(p => p.map(r => r.id === selected.id ? { ...r, status: newStatus } : r))
      setSelected(s => ({ ...s, status: newStatus }))

      // Update stat counters immediately so cards reflect change without reload
      setStats(prev => {
        if (!prev) return prev
        const updated = { ...prev }
        // Decrement old status bucket
        if (prevStatus === 'open' && updated.open > 0)         updated.open -= 1
        if (prevStatus === 'resolved' && updated.resolved > 0) updated.resolved -= 1
        if (prevStatus === 'escalated' && updated.escalated > 0) updated.escalated -= 1
        // Increment new status bucket
        if (newStatus === 'open')      updated.open += 1
        if (newStatus === 'resolved')  updated.resolved += 1
        if (newStatus === 'escalated') updated.escalated += 1
        return updated
      })

      toast.success(`Marked as ${newStatus.replace('_', ' ')}`)

      // Task 2: trigger escalation email notification when status becomes escalated
      if (newStatus === 'escalated') {
        try {
          await adminReq('/api/notify/escalation', {
            method: 'POST',
            body: JSON.stringify({
              report_id:   selected.id,
              hazard_type: selected.hazard_type,
              severity:    selected.severity,
              location:    selected.lat && selected.lng
                ? `${selected.lat.toFixed(5)}, ${selected.lng.toFixed(5)}`
                : selected.department || 'Unknown location',
            }),
          })
          toast('📧 Escalation email sent', { icon:'⚡' })
        } catch (emailErr) {
          // Non-fatal — log but don't block the flow
          console.warn('[Admin] escalation notify failed:', emailErr.message)
        }
      }
    } catch (e) {
      toast.error('Action failed: ' + e.message)
    } finally { setActionBusy(false) }
  }

  const getNavList = () => {
    switch (navItem) {
      case 'resolved':    return reports.filter(r => r.status === 'resolved')
      case 'escalations': return reports.filter(r => (r.upvotes||0) >= 5 && r.status !== 'resolved')
      case 'reports':
      case 'overview':
      default: {
        let list = [...reports]
        if (filter === 'high')     list = list.filter(r => r.severity === 'high')
        if (filter === 'open')     list = list.filter(r => r.status === 'open')
        if (filter === 'resolved') list = list.filter(r => r.status === 'resolved')
        if (sortBy === 'upvotes')  list.sort((a,b) => (b.upvotes||0)-(a.upvotes||0))
        else if (sortBy === 'severity') list.sort((a,b) => ['high','medium','low'].indexOf(a.severity) - ['high','medium','low'].indexOf(b.severity))
        return list
      }
    }
  }
  const displayList = getNavList()

  // Task 3: Live computed subtitle values — replace static '+6 this week' / 'last 30 days' strings
  const now = Date.now()
  const oneWeekAgo  = now - 7  * 24 * 60 * 60 * 1000
  const oneMonthAgo = now - 30 * 24 * 60 * 60 * 1000
  const newThisWeek    = reports.filter(r => new Date(r.created_at).getTime() > oneWeekAgo).length
  const resolvedMonth  = reports.filter(r => r.status === 'resolved' && new Date(r.created_at).getTime() > oneMonthAgo).length

  const openCount      = stats?.open      ?? reports.filter(r => r.status === 'open').length
  const resolvedCount  = stats?.resolved  ?? reports.filter(r => r.status === 'resolved').length
  const escalatedCount = stats?.escalated ?? reports.filter(r => (r.upvotes||0) >= 5 && r.status !== 'resolved').length

  const NAV = [
    { id:'overview',    label:'Overview',    count:null },
    { id:'reports',     label:'All Reports', count:reports.length, alert:false },
    { id:'map',         label:'Area Map',    count:null },
    { id:'analytics',   label:'Analytics',  count:'New' },
    { id:'resolved',    label:'Resolved',    count:resolvedCount, alert:false },
    { id:'escalations', label:'Escalations', count:escalatedCount, alert:escalatedCount > 0 },
  ]

  const chartData = rightTab === 'By type'
    ? (breakdown.by_type || [])
    : rightTab === 'By area'
    ? (breakdown.by_area || [])
    : (() => {
        const map = reports.reduce((acc,r) => { acc[r.hazard_type||'other'] = (acc[r.hazard_type||'other']||0)+1; return acc }, {})
        return Object.entries(map).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([label,count])=>({label,count}))
      })()
  const maxChart = Math.max(...chartData.map(d => d.count || 0), 1)

  async function exportCSV() {
    try {
      const { data } = await import('../lib/supabaseClient').then(m => m.supabase.auth.getSession())
      const token = data?.session?.access_token
      const res = await fetch(`${BASE}/api/admin/reports/export`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'ecosnap_reports.csv'
      a.click()
      toast.success('CSV downloaded')
    } catch (e) { toast.error('Export failed: ' + e.message) }
  }

  return (
    <div style={{ display:'flex', height:'100vh', overflow:'hidden', fontFamily:'Inter,sans-serif', background:'var(--bg3)' }}>

      {/* ── Sidebar ── */}
      <aside className="admin-sidebar">
        <div style={{ padding:'14px 16px', borderBottom:'0.5px solid var(--border)', display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ width:8, height:8, borderRadius:'50%', background:'var(--green)' }} />
          <span style={{ fontSize:13, fontWeight:500 }}>EcoSnap Authority</span>
          <span style={{ marginLeft:'auto', fontSize:10, background:'var(--green-light)', color:'var(--green-dark)', borderRadius:4, padding:'2px 6px' }}>Beta</span>
        </div>

        <nav style={{ padding:8, flex:1 }}>
          {NAV.map(n => (
            <div
              key={n.id}
              id={`admin-nav-${n.id}`}
              className={`admin-nav-item${navItem === n.id ? ' active' : ''}`}
              onClick={() => { setNavItem(n.id); setSelected(null) }}
              style={{ cursor:'pointer' }}
            >
              <span>{n.label}</span>
              {n.count !== null && (
                <span className={`admin-nav-count${n.alert ? ' alert' : ''}`}>
                  {loading && typeof n.count === 'number' ? '…' : n.count}
                </span>
              )}
            </div>
          ))}
        </nav>

        <div style={{ padding:'8px 16px 12px', borderTop:'0.5px solid var(--border)' }}>
          <div style={{ fontSize:10, color:'var(--text3)', marginBottom:6, textTransform:'uppercase', letterSpacing:.5 }}>Departments</div>
          {DEPTS.map(d => (
            <div key={d.name} style={{ display:'flex', alignItems:'center', gap:6, fontSize:12, color:'var(--text2)', marginBottom:4 }}>
              <div className="dot" style={{ background:d.color }} />
              {d.name}
            </div>
          ))}
          <div style={{ marginTop:12 }}>
            <button id="admin-signout" onClick={signOut}
              style={{ width:'100%', padding:'6px', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', background:'none', cursor:'pointer', fontSize:11, color:'var(--text2)', fontFamily:'Inter,sans-serif' }}>
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', marginLeft:220 }}>

        {/* Topbar */}
        <div style={{ background:'var(--bg)', borderBottom:'0.5px solid var(--border)', padding:'10px 16px', display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
          <span style={{ fontSize:14, fontWeight:500, marginRight:4 }}>
            {NAV.find(n => n.id === navItem)?.label || navItem}
          </span>

          {(navItem === 'overview' || navItem === 'reports') && (
            [['all','All areas'],['high','High severity'],['open','Open only'],['resolved','Resolved']].map(([k,l]) => (
              <button key={k} className={`filter-pill${filter===k?' active':''}`} onClick={() => setFilter(k)}>{l}</button>
            ))
          )}

          {(navItem === 'overview' || navItem === 'reports') && (
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}
              style={{ padding:'4px 10px', border:'0.5px solid var(--border2)', borderRadius:99, fontSize:11, background:'var(--bg)', color:'var(--text2)', fontFamily:'Inter,sans-serif', cursor:'pointer', marginLeft:4 }}>
              <option value="newest">Newest first</option>
              <option value="upvotes">Most upvoted</option>
              <option value="severity">By severity</option>
            </select>
          )}

          <button id="export-csv-btn" onClick={exportCSV}
            style={{ marginLeft:'auto', padding:'5px 12px', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', fontSize:12, background:'var(--bg)', color:'var(--text)', cursor:'pointer', fontFamily:'Inter,sans-serif' }}>
            Export CSV
          </button>
          {loading && <Spinner size={14} />}
        </div>

        {/* Content */}
        <div style={{ flex:1, display:'flex', overflow:'hidden' }}>

          {/* Map panel — hidden only for Analytics */}
          {navItem !== 'analytics' && (
            <div style={{ flex:1, position:'relative', overflow:'hidden' }}>
              <HazardMap reports={displayList} height="100%" showUser={true} />

              <div style={{ position:'absolute', top:10, left:10, zIndex:20, background:'var(--bg)', border:'0.5px solid var(--border)', borderRadius:'var(--r-sm)', padding:4, display:'flex', gap:2 }}>
                {['Pins','Heat','Clusters'].map((t,i) => (
                  <span key={t} style={{ fontSize:10, padding:'3px 8px', borderRadius:5, cursor:'pointer', background:i===0?'var(--green)':'none', color:i===0?'#fff':'var(--text2)' }}>{t}</span>
                ))}
              </div>

              {navItem === 'escalations' && (
                <div style={{ position:'absolute', top:10, left:'50%', transform:'translateX(-50%)', background:'rgba(226,75,74,.9)', color:'#fff', borderRadius:99, fontSize:11, padding:'5px 14px', zIndex:900, fontWeight:500, whiteSpace:'nowrap' }}>
                  ⚡ Showing {displayList.length} escalated reports (5+ upvotes)
                </div>
              )}
            </div>
          )}

          {/* Analytics panel */}
          {navItem === 'analytics' && (
            <div style={{ flex:1, overflowY:'auto', padding:20 }}>
              <div style={{ fontSize:14, fontWeight:500, marginBottom:16 }}>Analytics Overview</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginBottom:20 }}>
                {[
                  { l:'Total', v: stats?.total ?? reports.length },
                  { l:'Open',  v: openCount },
                  { l:'Resolved', v: resolvedCount },
                  { l:'Escalated', v: escalatedCount },
                  { l:'In Review', v: stats?.in_review ?? reports.filter(r=>r.status==='in_review').length },
                  { l:'High Severity', v: reports.filter(r=>r.severity==='high').length },
                ].map(({l,v}) => (
                  <div key={l} style={{ padding:12, background:'var(--bg)', border:'0.5px solid var(--border)', borderRadius:'var(--r-md)' }}>
                    <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4 }}>{l}</div>
                    <div style={{ fontSize:22, fontWeight:600 }}>{loading ? '—' : v}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:12, fontWeight:500, marginBottom:10 }}>Hazard breakdown</div>
              {chartData.map(({label,count},i) => (
                <div key={label} className="bar-row" style={{ marginBottom:8 }}>
                  <span className="bar-lbl">{fmtHazard(label)}</span>
                  <div className="bar-track" style={{ flex:1, margin:'0 8px' }}>
                    <div className="bar-fill" style={{ width:`${(count/maxChart)*100}%`, background:BCOLORS[i]||'#999', height:8, borderRadius:4 }} />
                  </div>
                  <span className="bar-cnt">{count}</span>
                </div>
              ))}
            </div>
          )}

          {/* ── Right panel ── */}
          <div style={{ width:280, background:'var(--bg)', borderLeft:'0.5px solid var(--border)', display:'flex', flexDirection:'column', overflow:'hidden' }}>

            {/* Stats */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, padding:12, borderBottom:'0.5px solid var(--border)' }}>
              {[
                // s values are live-computed from reports \u2014 no longer static strings
                { l:'Open reports',   v:openCount,      cls:'danger',  s:`+${newThisWeek} this week` },
                { l:'Resolved',       v:resolvedCount,  cls:'success', s:`${resolvedMonth} last 30d` },
                { l:'Escalated',      v:escalatedCount, cls:'danger',  s:'5+ upvotes' },
                { l:'Avg resolve',    v:stats?.avg_resolution_hours ? `${(stats.avg_resolution_hours/24).toFixed(1)}d` : '—', cls:'', s:'days' },
              ].map(({ l,v,cls,s }) => (
                <div key={l} className="admin-stat">
                  <div style={{ fontSize:10, color:'var(--text3)', marginBottom:3 }}>{l}</div>
                  <div style={{ fontSize:18, fontWeight:500, color: cls==='danger'?'var(--red-dark)':cls==='success'?'var(--green-dark)':'var(--text)' }}>
                    {loading ? '—' : v}
                  </div>
                  <div style={{ fontSize:10, color:'var(--text3)', marginTop:1 }}>{s}</div>
                </div>
              ))}
            </div>

            {/* Right tabs — STATEFUL */}
            <div style={{ display:'flex', borderBottom:'0.5px solid var(--border)', padding:'0 12px' }}>
              {['Reports','By area','By type'].map(t => (
                <div
                  key={t}
                  id={`admin-tab-${t.replace(' ','-').toLowerCase()}`}
                  onClick={() => setRightTab(t)}
                  style={{
                    fontSize:11, padding:'8px 8px', cursor:'pointer', userSelect:'none',
                    color: rightTab === t ? 'var(--green-dark)' : 'var(--text2)',
                    borderBottom: `2px solid ${rightTab === t ? 'var(--green)' : 'transparent'}`,
                    transition:'color .15s, border-color .15s',
                  }}
                >{t}</div>
              ))}
            </div>

            {/* Breakdown chart */}
            <div style={{ padding:'10px 12px', borderBottom:'0.5px solid var(--border)' }}>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:6 }}>
                {rightTab === 'By area' ? 'Area breakdown' : rightTab === 'By type' ? 'Type breakdown' : 'Hazard breakdown'}
              </div>
              {chartData.length === 0
                ? <div style={{ fontSize:11, color:'var(--text3)' }}>No data</div>
                : chartData.map(({label,count},i) => (
                  <div key={label} className="bar-row">
                    <span className="bar-lbl">{fmtHazard(label)}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width:`${(count/maxChart)*100}%`, background:BCOLORS[i]||'#999' }} />
                    </div>
                    <span className="bar-cnt">{count}</span>
                  </div>
                ))
              }
            </div>

            {/* List header */}
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 12px 6px' }}>
              <span style={{ fontSize:12, fontWeight:500 }}>
                {navItem === 'escalations' ? 'Escalated' : navItem === 'resolved' ? 'Resolved' : 'Latest'} reports
                <span style={{ fontSize:10, color:'var(--text3)', fontWeight:400 }}> ({displayList.length})</span>
              </span>
              {loading && <Spinner size={12} />}
            </div>

            {/* Report cards */}
            <div style={{ flex:1, overflowY:'auto', padding:'0 8px 8px' }}>
              {displayList.map(r => (
                <div
                  key={r.id}
                  id={`admin-rc-${r.id}`}
                  className={`rc${selected?.id === r.id ? ' rc-selected' : ''}`}
                  onClick={() => setSelected(selected?.id === r.id ? null : r)}
                  style={{ cursor:'pointer' }}
                >
                  <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:4 }}>
                    <SevBadge severity={r.severity} />
                    <span style={{ fontSize:10, color:'var(--text3)', marginLeft:'auto' }}>#{String(r.id).slice(-3).toUpperCase()}</span>
                  </div>
                  <div style={{ fontSize:12, fontWeight:500, marginBottom:2 }}>{fmtHazard(r.hazard_type)}</div>
                  <div style={{ fontSize:11, color:'var(--text2)' }}>{formatDate(r.created_at)}</div>
                  <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:5 }}>
                    <span style={{ fontSize:10, color:'var(--text2)', background:'var(--bg2)', borderRadius:99, padding:'1px 6px' }}>
                      {r.upvotes||0} upvotes
                    </span>
                    {(r.upvotes||0) >= 5 && r.status !== 'resolved' && (
                      <span style={{ fontSize:10, color:'var(--red-dark)' }}>⚡ Escalated</span>
                    )}
                    <div style={{ marginLeft:'auto' }}><StatusDot status={r.status} /></div>
                  </div>
                </div>
              ))}
              {!loading && displayList.length === 0 && (
                <div style={{ textAlign:'center', padding:'24px 0', color:'var(--text3)', fontSize:12 }}>
                  No reports in this view
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div style={{ padding:'10px 12px', borderTop:'0.5px solid var(--border)', display:'flex', flexDirection:'column', gap:6 }}>
              {selected && (
                <div style={{ fontSize:11, color:'var(--text2)', marginBottom:2 }}>
                  Selected: <strong style={{ color:'var(--text)' }}>{fmtHazard(selected.hazard_type)}</strong>
                  {' · '}<StBadge status={selected.status} />
                </div>
              )}
              <button
                id="admin-mark-review"
                className="action-btn btn-green"
                onClick={() => patchStatus('in_review')}
                disabled={!selected || actionBusy || selected?.status === 'in_review'}
                style={{ opacity: selected && !actionBusy ? 1 : .45, display:'flex', alignItems:'center', justifyContent:'center', gap:6 }}
              >
                {actionBusy && <Spinner size={13} color="#fff" />}
                Mark as in review
              </button>
              <button
                id="admin-mark-resolved"
                className="action-btn btn-outline"
                onClick={() => patchStatus('resolved')}
                disabled={!selected || actionBusy || selected?.status === 'resolved'}
                style={{ opacity: selected && !actionBusy ? 1 : .45 }}
              >
                Mark as resolved
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
