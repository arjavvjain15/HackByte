import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { SkeletonCard } from '../components/common/Skeletons'
import { useUpvote } from '../hooks/useUpvote'
import { useReports } from '../hooks/useReports'

import { fmtHazard, formatDist, markerColor } from '../utils/helpers'
import { SevBadge, StBadge } from '../components/common/Badges'

export function NearbyPage() {
  const { nearbyReports, loadNearby, fetchNearby } = useReports()
  const { vote, upvoted } = useUpvote()
  const nav  = useNavigate()
  const did  = useRef(false)

  useEffect(() => {
    if (did.current) return
    did.current = true
    fetchNearby()
  }, [fetchNearby])

  return (
    <Layout showFAB={true}>
      <div className="page-enter">
        {/* Header */}
        <div style={{ padding:'14px 14px 10px', background:'var(--bg)', borderBottom:'0.5px solid var(--border)' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
            <div>
              <div style={{ fontWeight:500, fontSize:15 }}>Community hazards</div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>
                {nearbyReports.length} total reports found
              </div>
            </div>
            <span className="sec-link" onClick={() => nav('/map')} style={{ fontSize:11 }}>Map view</span>
          </div>
        </div>

        <div style={{ padding:'10px 14px' }}>
          {/* Loading */}
          {loadNearby && <><SkeletonCard /><SkeletonCard /><SkeletonCard /></>}

          {/* Empty */}
          {!loadNearby && nearbyReports.length === 0 && (
            <div style={{ textAlign:'center', padding:'28px 0' }}>
              <div style={{ fontSize:28, marginBottom:8 }}>🌿</div>
              <div style={{ fontSize:13, color:'var(--text2)' }}>No hazards recorded — your area looks clean!</div>
            </div>
          )}

          {/* Cards */}
          {!loadNearby && nearbyReports.map((r, i) => {
            const voted = upvoted.has(r.id)
            const color = markerColor(r)
            const dist  = r.distance_km ?? r.distance
            return (
              <div
                key={r.id || i}
                className="nearby-card anim-fadeUp"
                style={{ animationDelay:`${i*40}ms`, cursor:'pointer' }}
                onClick={() => nav(`/reports/${r.id}`)}
              >
                {/* Colored dot */}
                <div style={{ width:10, height:10, borderRadius:'50%', background:color, marginTop:3, flexShrink:0 }} />

                {/* Body */}
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:11, fontWeight:500, marginBottom:2 }}>{fmtHazard(r.hazard_type)}</div>
                  <div style={{ fontSize:10, color:'var(--text2)', marginBottom:5 }}>
                    {r.upvotes||0} upvotes · <SevBadge severity={r.severity} /> · <StBadge status={r.status} />
                  </div>
                  <button
                    id={`nearby-upvote-${r.id}`}
                    className={`upvote-btn${voted ? ' voted' : ''}`}
                    onClick={(e) => { e.stopPropagation(); vote(r.id) }}
                  >
                    ▲ {voted ? 'Upvoted' : 'Upvote'}
                  </button>
                </div>

                {/* Right side data */}
                <div style={{ fontSize:10, color:'var(--text2)', alignSelf:'flex-start', marginTop:2, textAlign:'right', display:'flex', flexDirection:'column', gap:3 }}>
                  <div>By <span style={{fontWeight:500, color:'var(--text)'}}>{r.display_name || 'Anonymous'}</span></div>
                  {dist != null ? <div style={{fontSize:9, color:'var(--text3)'}}>{formatDist(dist)} away</div> : null}
                </div>
              </div>
            )
          })}


          <div style={{ height:10 }} />
        </div>
      </div>
    </Layout>
  )
}
