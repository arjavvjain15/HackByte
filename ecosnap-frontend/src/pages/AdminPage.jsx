import { useState, useEffect, useRef } from 'react'
import { HazardMap } from '../components/map/HazardMap'
import { SevBadge, StBadge, StatusDot } from '../components/common/Badges'
import { Spinner } from '../components/common/Spinner'
import { getAllReports } from '../services/api'
import { fmtHazard, formatDate, DEMO_REPORTS } from '../utils/helpers'
import { useAuth } from '../context/useAuth'
import toast from 'react-hot-toast'

const NAV = [
  { id:'overview',    label:'Overview',    count:null },
  { id:'reports',     label:'All Reports', count:12, alert:true },
  { id:'map',         label:'Area Map',    count:null },
  { id:'analytics',   label:'Analytics',  count:'New' },
  { id:'resolved',    label:'Resolved',    count:null },
  { id:'escalations', label:'Escalations', count:3, alert:true },
]
const DEPTS = [
  { color:'#E24B4A', name:'Municipal Sanitation' },
  { color:'#378ADD', name:'Drainage & Sewage' },
  { color:'#EF9F27', name:'Pollution Control' },
  { color:'#639922', name:'Parks & Forests' },
]

export function AdminPage() {
  const { signOut, user } = useAuth()
  const [reports,  setReports]  = useState([])
  const [selected, setSelected] = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [navItem,  setNavItem]  = useState('overview')
  const [sortBy,   setSortBy]   = useState('newest')
  const [filter,   setFilter]   = useState('all')
  const did = useRef(false)

  useEffect(() => {
    if (did.current) return; did.current = true
    fetchReports()
  }, [])

  async function fetchReports() {
    setLoading(true)
    try { const d = await getAllReports(); setReports(Array.isArray(d) ? d : d?.reports || DEMO_REPORTS) }
    catch { setReports(DEMO_REPORTS) }
    finally { setLoading(false) }
  }

  async function markInReview() {
    if (!selected) return
    toast.success('Marked as in review')
    setReports(p => p.map(r => r.id === selected.id ? { ...r, status:'in_review' } : r))
    setSelected(s => ({ ...s, status:'in_review' }))
  }
  async function markResolved() {
    if (!selected) return
    toast.success('Marked as resolved')
    setReports(p => p.map(r => r.id === selected.id ? { ...r, status:'resolved' } : r))
    setSelected(s => ({ ...s, status:'resolved' }))
  }

  /* Stats */
  const open     = reports.filter(r => r.status === 'open').length
  const resolved = reports.filter(r => r.status === 'resolved').length
  const escalated= reports.filter(r => (r.upvotes||0) >= 5 && r.status !== 'resolved').length

  /* Sorted/filtered list */
  let displayList = [...reports]
  if (filter === 'high')     displayList = displayList.filter(r => r.severity === 'high')
  if (filter === 'open')     displayList = displayList.filter(r => r.status === 'open')
  if (filter === 'resolved') displayList = displayList.filter(r => r.status === 'resolved')
  if (sortBy === 'upvotes') displayList.sort((a,b) => (b.upvotes||0)-(a.upvotes||0))
  else if (sortBy === 'severity') displayList.sort((a,b) => (['high','medium','low'].indexOf(a.severity))- (['high','medium','low'].indexOf(b.severity)))

  /* Breakdown for bar chart */
  const breakdown = Object.entries(
    reports.reduce((acc,r) => { acc[r.hazard_type] = (acc[r.hazard_type]||0)+1; return acc }, {})
  ).sort((a,b)=>b[1]-a[1]).slice(0,5)
  const maxCount = Math.max(...breakdown.map(([,n])=>n), 1)
  const BCOLORS  = ['#E24B4A','#378ADD','#EF9F27','#5DCAA5','#D85A30']

  return (
    <div style={{ display:'flex', height:'100vh', overflow:'hidden', fontFamily:'Inter,sans-serif', background:'var(--bg3)' }}>

      {/* ── Sidebar ── */}
      <aside className="admin-sidebar">
        {/* Logo */}
        <div style={{ padding:'14px 16px', borderBottom:'0.5px solid var(--border)', display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ width:8, height:8, borderRadius:'50%', background:'var(--green)' }} />
          <span style={{ fontSize:13, fontWeight:500 }}>EcoSnap Authority</span>
          <span style={{ marginLeft:'auto', fontSize:10, background:'var(--green-light)', color:'var(--green-dark)', borderRadius:4, padding:'2px 6px' }}>Beta</span>
        </div>

        {/* Nav */}
        <nav style={{ padding:8, flex:1 }}>
          {NAV.map(n => (
            <div
              key={n.id}
              id={`admin-nav-${n.id}`}
              className={`admin-nav-item${navItem===n.id?' active':''}`}
              onClick={() => setNavItem(n.id)}
            >
              <span>{n.label}</span>
              {n.count !== null && (
                <span className={`admin-nav-count${n.alert?' alert':''}`}>{n.count}</span>
              )}
            </div>
          ))}
        </nav>

        {/* Departments */}
        <div style={{ padding:'8px 16px 12px', borderTop:'0.5px solid var(--border)' }}>
          <div style={{ fontSize:10, color:'var(--text3)', marginBottom:6, textTransform:'uppercase', letterSpacing:.5 }}>Departments</div>
          {DEPTS.map(d => (
            <div key={d.name} style={{ display:'flex', alignItems:'center', gap:6, fontSize:12, color:'var(--text2)', marginBottom:4 }}>
              <div className="dot" style={{ background:d.color }} />
              {d.name}
            </div>
          ))}
          <div style={{ marginTop:12 }}>
            <button
              id="admin-signout"
              onClick={signOut}
              style={{ width:'100%', padding:'6px', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', background:'none', cursor:'pointer', fontSize:11, color:'var(--text2)', fontFamily:'Inter,sans-serif' }}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main area ── */}
      <main style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', marginLeft:220 }}>

        {/* Topbar */}
        <div style={{ background:'var(--bg)', borderBottom:'0.5px solid var(--border)', padding:'10px 16px', display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
          <span style={{ fontSize:14, fontWeight:500, marginRight:4, textTransform:'capitalize' }}>{navItem}</span>

          {/* Filter pills */}
          {[['all','All areas'],['high','High severity'],['open','Open only'],['resolved','Resolved']].map(([k,l]) => (
            <button key={k} className={`filter-pill${filter===k?' active':''}`} onClick={() => setFilter(k)}>{l}</button>
          ))}

          {/* Sort */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            style={{ padding:'4px 10px', border:'0.5px solid var(--border2)', borderRadius:99, fontSize:11, background:'var(--bg)', color:'var(--text2)', fontFamily:'Inter,sans-serif', cursor:'pointer', marginLeft:4 }}
          >
            <option value="newest">Newest first</option>
            <option value="upvotes">Most upvoted</option>
            <option value="severity">By severity</option>
          </select>

          <button
            id="export-csv-btn"
            onClick={() => toast('CSV export coming soon!')}
            style={{ marginLeft:'auto', padding:'5px 12px', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', fontSize:12, background:'var(--bg)', color:'var(--text)', cursor:'pointer', fontFamily:'Inter,sans-serif' }}
          >
            Export CSV
          </button>
        </div>

        {/* Content */}
        <div style={{ flex:1, display:'flex', overflow:'hidden' }}>

          {/* ── Map panel ── */}
          <div style={{ flex:1, position:'relative', overflow:'hidden' }}>
            <HazardMap reports={reports} height="100%" showUser={false} />

            {/* Map toggle overlay */}
            <div style={{ position:'absolute', top:10, left:10, zIndex:20, background:'var(--bg)', border:'0.5px solid var(--border)', borderRadius:'var(--r-sm)', padding:4, display:'flex', gap:2 }}>
              {['Pins','Heat','Clusters'].map((t,i) => (
                <span key={t} style={{ fontSize:10, padding:'3px 8px', borderRadius:5, cursor:'pointer', background:i===0?'var(--green)':'none', color:i===0?'#fff':'var(--text2)' }}>{t}</span>
              ))}
            </div>
          </div>

          {/* ── Right panel ── */}
          <div style={{ width:280, background:'var(--bg)', borderLeft:'0.5px solid var(--border)', display:'flex', flexDirection:'column', overflow:'hidden' }}>

            {/* Stats */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, padding:12, borderBottom:'0.5px solid var(--border)' }}>
              {[
                { l:'Open reports',  v:open,     cls:'danger',  s:'+6 this week' },
                { l:'Resolved',      v:resolved, cls:'success', s:'last 30 days' },
                { l:'Escalated',     v:escalated,cls:'danger',  s:'5+ upvotes' },
                { l:'Avg resolve',   v:'4.2d',   cls:'',        s:'days' },
              ].map(({ l,v,cls,s }) => (
                <div key={l} className="admin-stat">
                  <div style={{ fontSize:10, color:'var(--text3)', marginBottom:3 }}>{l}</div>
                  <div style={{ fontSize:18, fontWeight:500, color: cls==='danger'?'var(--red-dark)':cls==='success'?'var(--green-dark)':'var(--text)' }}>{loading?'—':v}</div>
                  <div style={{ fontSize:10, color:'var(--text3)', marginTop:1 }}>{s}</div>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div style={{ display:'flex', borderBottom:'0.5px solid var(--border)', padding:'0 12px' }}>
              {['Reports','By area','By type'].map((t,i) => (
                <div key={t} style={{ fontSize:11, padding:'8px 8px', cursor:'pointer', color:i===0?'var(--green-dark)':'var(--text2)', borderBottom:`2px solid ${i===0?'var(--green)':'transparent'}` }}>{t}</div>
              ))}
            </div>

            {/* Hazard breakdown chart */}
            <div style={{ padding:'10px 12px', borderBottom:'0.5px solid var(--border)' }}>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:6 }}>Hazard breakdown</div>
              {breakdown.map(([type, count], i) => (
                <div key={type} className="bar-row">
                  <span className="bar-lbl">{fmtHazard(type)}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width:`${(count/maxCount)*100}%`, background:BCOLORS[i]||'#999' }} />
                  </div>
                  <span className="bar-cnt">{count}</span>
                </div>
              ))}
            </div>

            {/* Reports list */}
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 12px 6px' }}>
              <span style={{ fontSize:12, fontWeight:500 }}>Latest reports</span>
              {loading && <Spinner size={12} />}
            </div>

            <div style={{ flex:1, overflowY:'auto', padding:'0 8px 8px' }}>
              {displayList.map(r => (
                <div
                  key={r.id}
                  id={`admin-rc-${r.id}`}
                  className={`rc${selected?.id===r.id?' rc-selected':''}`}
                  onClick={() => setSelected(r)}
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
                      <span style={{ fontSize:10, color:'var(--red-dark)' }}>Escalated</span>
                    )}
                    <div style={{ marginLeft:'auto' }}>
                      <StatusDot status={r.status} />
                    </div>
                  </div>
                </div>
              ))}

              {!loading && displayList.length === 0 && (
                <div style={{ textAlign:'center', padding:'24px 0', color:'var(--text3)', fontSize:12 }}>
                  No reports match filter
                </div>
              )}
            </div>

            {/* Action bar */}
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
                onClick={markInReview}
                disabled={!selected}
                style={{ opacity: selected ? 1 : .45 }}
              >
                Mark as in review
              </button>
              <button
                id="admin-mark-resolved"
                className="action-btn btn-outline"
                onClick={markResolved}
                disabled={!selected}
                style={{ opacity: selected ? 1 : .45 }}
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
