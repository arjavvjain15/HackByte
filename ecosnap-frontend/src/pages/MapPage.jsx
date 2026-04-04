import { useEffect, useRef } from 'react'
import { Layout } from '../components/layout/Layout'
import { HazardMap } from '../components/map/HazardMap'
import { Spinner } from '../components/common/Spinner'
import { useReports } from '../hooks/useReports'

export function MapPage() {
  const { reports, loadAll, fetchAll } = useReports()
  const did = useRef(false)

  useEffect(() => {
    if (did.current) return
    did.current = true
    fetchAll()
  }, [fetchAll])

  return (
    <Layout showFAB={true}>
      {/* Floating header */}
      <div style={{ position:'relative', zIndex:0 }}>
        {/* Header overlap */}
        <div style={{
          position:'fixed', top:0, left:0, right:0, zIndex:20,
          background:'var(--bg)', borderBottom:'0.5px solid var(--border)',
          padding:'14px 14px 10px',
          display:'flex', alignItems:'center', justifyContent:'space-between',
        }}>
          <div>
            <div style={{ fontWeight:500, fontSize:15 }}>Hazard Map</div>
            <div style={{ fontSize:11, color:'var(--text2)' }}>{reports.length} reports</div>
          </div>
          <button
            id="refresh-map-btn"
            onClick={fetchAll}
            style={{ background:'none', border:'0.5px solid var(--border2)', borderRadius:'var(--r-sm)', padding:'5px 10px', cursor:'pointer', fontSize:11, color:'var(--text2)', display:'flex', alignItems:'center', gap:5, fontFamily:'Inter,sans-serif' }}
            disabled={loadAll}
          >
            {loadAll ? <Spinner size={12} /> : '↺'} Refresh
          </button>
        </div>

        {/* Full screen map */}
        <div style={{ paddingTop:58, height:'100vh' }}>
          <HazardMap reports={reports} height="calc(100vh - 58px)" showUser={true} />
        </div>

        {/* Legend overlay */}
        <div style={{
          position:'fixed', bottom:140, left:12, zIndex:20,
          background:'#fff', border:'0.5px solid var(--border)', borderRadius:'var(--r-md)',
          padding:'8px 10px',
        }}>
          <div style={{ fontSize:10, color:'var(--text3)', marginBottom:5, fontWeight:500, textTransform:'uppercase', letterSpacing:.5 }}>Severity</div>
          {[['#E24B4A','High'],['#EF9F27','Medium'],['#639922','Resolved'],['#1D9E75','You']].map(([c,l]) => (
            <div key={l} style={{ display:'flex', alignItems:'center', gap:5, marginBottom:3, fontSize:11, color:'var(--text2)' }}>
              <div style={{ width:8, height:8, borderRadius:'50%', background:c, flexShrink:0 }} />
              {l}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
