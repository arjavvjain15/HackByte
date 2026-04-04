import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { SevBadge, StBadge } from '../components/common/Badges'
import { Spinner } from '../components/common/Spinner'
import { useAuth } from '../context/useAuth'
import { useUpvote } from '../hooks/useUpvote'
import { getReport, getResolutionPlan } from '../services/api'
import { fmtHazard, formatDate } from '../utils/helpers'
import { supabase } from '../lib/supabaseClient'
import toast from 'react-hot-toast'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SEV_COLOR = { high:'#E24B4A', medium:'#EF9F27', low:'#5DCAA5' }
const STATUS_COLOR = { open:'var(--text3)', in_review:'#EF9F27', escalated:'#E24B4A', resolved:'#1D9E75' }

async function adminReq(path, opts = {}) {
  const { data } = await supabase.auth.getSession()
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

export function ReportDetailPage() {
  const { id } = useParams()
  const nav = useNavigate()
  const { isAdmin } = useAuth()
  const { vote, upvoted } = useUpvote()

  const [report,      setReport]      = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState(null)
  const [actionBusy,  setActionBusy]  = useState(false)

  // Resolution plan state (admin only)
  const [plan,        setPlan]        = useState(null)
  const [planLoading, setPlanLoading] = useState(false)
  const [planOpen,    setPlanOpen]    = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getReport(id)
      .then(d => { if (!cancelled) setReport(d) })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id])

  async function fetchPlan() {
    setPlanLoading(true)
    try {
      const d = await getResolutionPlan(id)
      setPlan(d.resolution_plan?.resources || d.resolution_plan || d)
      setPlanOpen(true)
      console.log(d.resolution_plan?.resources || d.resolution_plan || d)
    } catch (e) {
      toast.error('Could not load plan: ' + e.message)
    } finally {
      setPlanLoading(false)
    }
  }

  // Admin: change status directly from the detail page
  async function patchStatus(newStatus) {
    setActionBusy(true)
    try {
      await adminReq('/api/admin/reports', {
        method: 'PATCH',
        body: JSON.stringify({ ids: [id], status: newStatus }),
      })
      setReport(r => ({ ...r, status: newStatus }))
      toast.success(`Marked as ${newStatus.replace('_', ' ')}`)

      // Trigger resolved email if applicable
      if (newStatus === 'resolved' && report?.user_email) {
        try {
          await adminReq('/api/notify/resolved', {
            method: 'POST',
            body: JSON.stringify({
              report_id:   id,
              user_email:  report.user_email,
              hazard_type: report.hazard_type,
            }),
          })
          toast('📧 Creator notified', { icon:'✅' })
        } catch (err) {
          console.warn('Failed to notify creator:', err)
        }
      }
    } catch (e) {
      toast.error('Action failed: ' + e.message)
    } finally {
      setActionBusy(false)
    }
  }

  const isVoted = upvoted.has(id)

  /* ── Loading ── */
  if (loading) return (
    <Layout>
      <div style={{ display:'flex', justifyContent:'center', padding:'40px 0' }}>
        <Spinner size={28} />
      </div>
    </Layout>
  )

  /* ── Error ── */
  if (error || !report) return (
    <Layout>
      <div style={{ padding:24, textAlign:'center' }}>
        <div style={{ fontSize:36, marginBottom:12 }}>⚠️</div>
        <div style={{ fontWeight:500, marginBottom:6 }}>Report not found</div>
        <div style={{ fontSize:12, color:'var(--text2)', marginBottom:20 }}>{error}</div>
        <button onClick={() => nav(-1)}
          style={{ padding:'10px 20px', background:'var(--green)', color:'#fff', border:'none',
            borderRadius:'var(--r-lg)', fontSize:13, cursor:'pointer', fontFamily:'Inter,sans-serif' }}>
          ← Go back
        </button>
      </div>
    </Layout>
  )

  const r = report
  const currentStatus = r.status

  return (
    <Layout showFAB={false}>
      <div className="page-enter">

        {/* ── Sticky header ── */}
        <div style={{ position:'sticky', top:0, zIndex:50, background:'var(--bg)',
          borderBottom:'0.5px solid var(--border)', padding:'12px 14px',
          display:'flex', alignItems:'center', gap:10 }}>
          <button onClick={() => nav(-1)}
            style={{ background:'none', border:'none', cursor:'pointer', fontSize:18,
              color:'var(--text3)', padding:'0 4px' }}>←</button>
          <div style={{ flex:1 }}>
            <div style={{ fontWeight:500, fontSize:15 }}>{fmtHazard(r.hazard_type)}</div>
            <div style={{ fontSize:11, color:'var(--text2)' }}>#{String(r.id).slice(-6).toUpperCase()}</div>
          </div>
          <SevBadge severity={r.severity} />
        </div>

        {/* ── Photo ── */}
        {r.photo_url && (
          <div style={{ width:'100%', aspectRatio:'16/9', overflow:'hidden', background:'var(--bg2)' }}>
            <img src={r.photo_url} alt="Hazard photo"
              style={{ width:'100%', height:'100%', objectFit:'cover' }}
              onError={e => { e.target.style.display = 'none' }}
            />
          </div>
        )}

        <div style={{ padding:'14px 14px 24px' }}>

          {/* ── Status strip ── */}
          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14,
            padding:'8px 12px', background:'var(--bg2)', borderRadius:'var(--r-md)' }}>
            <span style={{ fontSize:11, color:'var(--text2)', flex:1 }}>Status</span>
            <span style={{ fontSize:12, fontWeight:500, color: STATUS_COLOR[currentStatus] || 'var(--text)' }}>
              {currentStatus?.replace('_',' ').replace(/\b\w/g, l => l.toUpperCase()) || '—'}
            </span>
            <StBadge status={currentStatus} />
          </div>

          {/* ── Key details grid ── */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginBottom:14 }}>
            {[
              { l:'Severity',   v: r.severity?.replace(/\b\w/g, l => l.toUpperCase()), color: SEV_COLOR[r.severity] },
              { l:'Department', v: r.department || '—' },
              { l:'Upvotes',    v: `▲ ${r.upvotes || 0}` },
              { l:'Reported',   v: formatDate(r.created_at) },
            ].map(({ l, v, color }) => (
              <div key={l} style={{ padding:'8px 10px', background:'var(--bg2)',
                borderRadius:'var(--r-md)', border:'0.5px solid var(--border)' }}>
                <div style={{ fontSize:10, color:'var(--text3)', marginBottom:2 }}>{l}</div>
                <div style={{ fontSize:12, fontWeight:500, color: color || 'var(--text)' }}>{v}</div>
              </div>
            ))}
          </div>

          {/* ── Summary ── */}
          {r.summary && (
            <div style={{ marginBottom:14 }}>
              <div style={{ fontSize:11, fontWeight:500, color:'var(--text2)', marginBottom:6 }}>📋 Summary</div>
              <div style={{ fontSize:13, lineHeight:1.6, color:'var(--text)',
                padding:'10px 12px', background:'var(--bg2)', borderRadius:'var(--r-md)',
                border:'0.5px solid var(--border)' }}>
                {r.summary}
              </div>
            </div>
          )}

          {/* ── Complaint ── */}
          {r.complaint && (
            <div style={{ marginBottom:14 }}>
              <div style={{ fontSize:11, fontWeight:500, color:'var(--text2)', marginBottom:6 }}>📝 Complaint</div>
              <div style={{ fontSize:12, lineHeight:1.7, color:'var(--text2)',
                padding:'10px 12px', background:'var(--bg2)', borderRadius:'var(--r-md)',
                border:'0.5px solid var(--border)', whiteSpace:'pre-wrap' }}>
                {r.complaint}
              </div>
            </div>
          )}

          {/* ── Location ── */}
          {(r.lat || r.lng) && (
            <div style={{ marginBottom:14, padding:'8px 12px', background:'var(--bg2)',
              borderRadius:'var(--r-md)', border:'0.5px solid var(--border)',
              display:'flex', alignItems:'center', gap:8 }}>
              <span style={{ fontSize:16 }}>📍</span>
              <div>
                <div style={{ fontSize:11, color:'var(--text2)' }}>Location</div>
                <div style={{ fontSize:12, fontWeight:500 }}>
                  {r.lat?.toFixed(5)}, {r.lng?.toFixed(5)}
                </div>
              </div>
              <a href={`https://maps.google.com/?q=${r.lat},${r.lng}`}
                target="_blank" rel="noopener noreferrer"
                style={{ marginLeft:'auto', fontSize:11, color:'var(--green-dark)', textDecoration:'none' }}>
                Open map ↗
              </a>
            </div>
          )}

          {/* ── AI resources ── */}
          {r.resources && (
            <div style={{ marginBottom:14 }}>
              <div style={{ fontSize:11, fontWeight:500, color:'var(--text2)', marginBottom:6 }}>🤖 AI Analysis</div>
              <div style={{ fontSize:12, color:'var(--text2)', padding:'10px 12px',
                background:'var(--bg2)', borderRadius:'var(--r-md)', border:'0.5px solid var(--border)' }}>
                {typeof r.resources === 'string' ? r.resources : JSON.stringify(r.resources, null, 2)}
              </div>
            </div>
          )}

          {/* ── Admin actions ── */}
          {isAdmin && (
            <div style={{ display:'flex', flexDirection:'column', gap:8, marginBottom:12 }}>
              <div style={{ fontSize:11, fontWeight:500, color:'var(--text2)', marginBottom:2 }}>
                🔧 Admin actions
              </div>
              <button
                id={`admin-review-${id}`}
                onClick={() => patchStatus('in_review')}
                disabled={actionBusy || currentStatus === 'in_review'}
                style={{
                  width:'100%', padding:'11px',
                  background: currentStatus === 'in_review' ? 'var(--bg2)' : 'var(--green)',
                  color: currentStatus === 'in_review' ? 'var(--text3)' : '#fff',
                  border: currentStatus === 'in_review' ? '0.5px solid var(--border)' : 'none',
                  borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer',
                  fontFamily:'Inter,sans-serif', display:'flex', alignItems:'center',
                  justifyContent:'center', gap:8, opacity: actionBusy ? 0.6 : 1,
                }}>
                {actionBusy ? <Spinner size={14} color="#fff" /> : null}
                {currentStatus === 'in_review' ? '✓ Already in review' : 'Mark as in review'}
              </button>
              <button
                id={`admin-resolve-${id}`}
                onClick={() => patchStatus('resolved')}
                disabled={actionBusy || currentStatus === 'resolved'}
                style={{
                  width:'100%', padding:'11px',
                  background:'none',
                  color: currentStatus === 'resolved' ? 'var(--text3)' : 'var(--text)',
                  border:'0.5px solid var(--border2)',
                  borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer',
                  fontFamily:'Inter,sans-serif', opacity: actionBusy ? 0.6 : 1,
                }}>
                {currentStatus === 'resolved' ? '✓ Already resolved' : 'Mark as resolved'}
              </button>
            </div>
          )}

          {/* ── Upvote button (non-admin / non-resolved) ── */}
          {!isAdmin && currentStatus !== 'resolved' && (
            <button
              id={`upvote-detail-${id}`}
              className={`upvote-btn${isVoted ? ' voted' : ''}`}
              onClick={() => vote(id)}
              style={{ width:'100%', padding:'11px', marginBottom:12,
                borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500 }}>
              ▲ {isVoted ? 'Upvoted' : 'Upvote this report'} · {r.upvotes || 0}
            </button>
          )}

          {/* ── Get Plan (admin only) ── */}
          {isAdmin && (
            <div style={{ marginTop:4 }}>
              <button
                id={`get-plan-${id}`}
                onClick={fetchPlan}
                disabled={planLoading}
                style={{ width:'100%', padding:'11px', border:'0.5px solid var(--border2)',
                  borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer',
                  background:'var(--bg2)', color:'var(--text)', fontFamily:'Inter,sans-serif',
                  display:'flex', alignItems:'center', justifyContent:'center', gap:8,
                  opacity: planLoading ? 0.65 : 1 }}>
                {planLoading ? <Spinner size={14} /> : '🛠️'}
                {planLoading ? 'Generating plan...' : 'Get Plan'}
              </button>

              {/* Resolution Plan card */}
              {planOpen && plan && (
                <div style={{ marginTop:12, padding:'14px', background:'var(--bg2)',
                  border:'0.5px solid var(--border)', borderRadius:'var(--r-md)' }}>
                  <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:10 }}>
                    <span style={{ fontSize:13, fontWeight:500 }}>🛠️ Resolution Plan</span>
                    <button onClick={() => setPlanOpen(false)}
                      style={{ background:'none', border:'none', cursor:'pointer',
                        fontSize:16, color:'var(--text3)' }}>✕</button>
                  </div>
                  {[
                    { icon:'👷', l:'Workers',        v: plan.workers },
                    { icon:'🚛', l:'Vehicles',       v: plan.vehicles?.join ? plan.vehicles.join(', ') : plan.vehicles },
                    { icon:'⏱️', l:'Estimated Time', v: plan.estimated_time },
                    { icon:'⚡', l:'Priority',       v: <span style={{ color: plan.priority === 'high' ? 'var(--red-dark)' : plan.priority === 'medium' ? 'var(--orange-dark)' : 'var(--green-dark)' }}>{plan.priority?.toUpperCase()}</span> },
                  ].map(({ icon, l, v }) => v != null && (
                    <div key={l} style={{ display:'flex', alignItems:'center',
                      padding:'7px 0', borderBottom:'0.5px solid var(--border)' }}>
                      <span style={{ fontSize:14, marginRight:8 }}>{icon}</span>
                      <span style={{ fontSize:12, color:'var(--text2)', flex:1 }}>{l}</span>
                      <span style={{ fontSize:12, fontWeight:500 }}>{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </Layout>
  )
}
