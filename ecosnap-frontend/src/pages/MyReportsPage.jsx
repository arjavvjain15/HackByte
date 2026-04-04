import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { ReportCard } from '../components/reports/ReportCard'
import { SkeletonCard } from '../components/common/Skeletons'
import { useReports } from '../hooks/useReports'

export function MyReportsPage() {
  const { myReports, loadMine, fetchMine } = useReports()
  const nav = useNavigate()
  const did = useRef(false)

  useEffect(() => {
    if (did.current) return
    did.current = true
    fetchMine()
  }, [fetchMine])

  return (
    <Layout showFAB={true}>
      <div className="page-enter">
        {/* Header */}
        <div style={{ padding:'14px 14px 10px', background:'var(--bg)', borderBottom:'0.5px solid var(--border)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <button
              onClick={() => nav(-1)}
              style={{ background:'none', border:'none', cursor:'pointer', fontSize:18, color:'var(--text3)', padding:'0 4px' }}
            >
              ←
            </button>
            <div>
              <div style={{ fontWeight:500, fontSize:15 }}>My Reports</div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>
                {loadMine ? 'Loading...' : `${myReports.length} report${myReports.length !== 1 ? 's' : ''} filed`}
              </div>
            </div>
          </div>
        </div>

        <div style={{ padding:'10px 14px' }}>
          {/* Loading */}
          {loadMine && <><SkeletonCard /><SkeletonCard /><SkeletonCard /></>}

          {/* Empty */}
          {!loadMine && myReports.length === 0 && (
            <div style={{ textAlign:'center', padding:'40px 0' }}>
              <div style={{ fontSize:36, marginBottom:12 }}>🌿</div>
              <div style={{ fontWeight:500, marginBottom:6 }}>No reports yet</div>
              <div style={{ fontSize:12, color:'var(--text2)', marginBottom:20 }}>
                Help your community by reporting a hazard
              </div>
              <button
                id="file-report-cta"
                onClick={() => nav('/report')}
                style={{ padding:'10px 20px', background:'var(--green)', color:'#fff', border:'none',
                  borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif' }}
              >
                ➕ File first report
              </button>
            </div>
          )}

          {/* Cards */}
          {!loadMine && myReports.map((r, i) => (
            <div key={r.id} className="anim-fadeUp" style={{ animationDelay:`${i * 40}ms` }}>
              <ReportCard report={r} showProgress={true} showUpvote={true} />
            </div>
          ))}

          <div style={{ height: 16 }} />
        </div>
      </div>
    </Layout>
  )
}
