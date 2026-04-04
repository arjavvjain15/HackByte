/**
 * AIResultPreviewPage
 * Standalone preview of the AI classification result + success screen from the report flow.
 * Mirrors what the user sees at step 2 (AI result) and the post-submit success screen.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { SevBadge } from '../components/common/Badges'
import { ComplaintLetterModal } from '../components/letter/ComplaintLetterModal'
import { fmtHazard } from '../utils/helpers'
import { MOCK_SUBMITTED_REPORT, MOCK_AI_RESULT } from '../preview/mockData'

export function AIResultPreviewPage() {
  const nav = useNavigate()
  const [letterOpen, setLetterOpen] = useState(false)
  const [view, setView] = useState('result') // 'result' | 'success'

  const ai       = MOCK_AI_RESULT
  const report   = MOCK_SUBMITTED_REPORT

  return (
    <Layout showFAB={false}>
      {/* Preview toggle */}
      <div style={{
        background: 'linear-gradient(90deg,#10b981,#6366f1)',
        padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: '#fff', letterSpacing: .4 }}>
          🔬 PREVIEW — AI Result Screen
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          {['result', 'success'].map(v => (
            <button key={v} onClick={() => setView(v)} style={{
              background: view === v ? 'rgba(255,255,255,.25)' : 'rgba(255,255,255,.08)',
              border: '1px solid rgba(255,255,255,.2)',
              color: '#fff', borderRadius: 6, padding: '2px 10px',
              fontSize: 10, cursor: 'pointer', fontFamily: 'Inter,sans-serif',
            }}>
              {v === 'result' ? 'AI Result' : 'Success'}
            </button>
          ))}
        </div>
      </div>

      {/* ── AI Result view ── */}
      {view === 'result' && (
        <div className="page-enter" style={{ padding: '14px 14px 24px', background: 'var(--bg)' }}>
          {/* Step header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0 0 10px', borderBottom: '0.5px solid var(--border)', marginBottom: 14 }}>
            <button onClick={() => nav('/preview')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--text3)', padding: '0 4px' }}>←</button>
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Report a Hazard</div>
              <div style={{ fontSize: 11, color: 'var(--text2)' }}>Step 3 of 4 — AI Analysis</div>
            </div>
          </div>

          {/* Step dots */}
          <div style={{ display: 'flex', gap: 5, marginBottom: 14 }}>
            {['done','done','active',''].map((cls, i) => (
              <div key={i} className={`step-dot${cls ? ' '+cls : ''}`} style={{ flex: 1 }} />
            ))}
          </div>

          {/* AI result card */}
          <div style={{ background: 'var(--green-light)', borderRadius: 'var(--r-lg)', padding: '12px 14px', marginBottom: 14, border: '0.5px solid var(--green-mid)' }}>
            <div style={{ fontSize: 11, color: 'var(--green-dark)', fontWeight: 500, marginBottom: 6 }}>🤖 AI Classification Result</div>
            <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4 }}>{fmtHazard(ai.hazard_type)}</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <SevBadge severity={ai.severity} />
              <span style={{ fontSize: 11, color: 'var(--text2)' }}>→ {ai.department}</span>
            </div>
          </div>

          {/* Location attached */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', background: 'var(--green-light)', borderRadius: 'var(--r-md)', padding: '8px 10px', marginBottom: 16 }}>
            <span style={{ fontSize: 14 }}>📍</span>
            <span style={{ fontSize: 11, color: 'var(--green-dark)', fontWeight: 500 }}>Location attached</span>
            <span style={{ fontSize: 10, color: 'var(--green-dark)', marginLeft: 'auto', opacity: .7 }}>20.5937, 78.9629</span>
          </div>

          <button
            disabled
            style={{ width: '100%', padding: 12, background: 'var(--green)', color: '#fff', border: 'none',
              borderRadius: 'var(--r-lg)', fontSize: 13, fontWeight: 500, cursor: 'not-allowed', fontFamily: 'Inter,sans-serif' }}
          >
            Confirm Location →
          </button>
          <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--text3)', marginTop: 10 }}>
            (Location button disabled in preview — switch to "Success" to see next screen)
          </p>
        </div>
      )}

      {/* ── Success view ── */}
      {view === 'success' && (
        <div className="page-enter" style={{ padding: '60px 24px 32px', textAlign: 'center', background: 'var(--bg)' }}>
          <div style={{ fontSize: 56, marginBottom: 16 }} className="anim-bounceIn">✅</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Report submitted!</h2>
          <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 32, lineHeight: 1.6 }}>
            Your hazard has been mapped and the relevant department has been alerted.
            Neighbours can now upvote it to escalate.
          </p>

          <div style={{ background: 'var(--bg2)', borderRadius: 'var(--r-lg)', padding: '14px 16px', marginBottom: 24, textAlign: 'left' }}>
            <div style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
              <SevBadge severity={report.severity} />
              <span style={{ fontSize: 9, color: 'var(--text3)', marginLeft: 'auto' }}>#{String(report.id).slice(-6).toUpperCase()}</span>
            </div>
            <div style={{ fontWeight: 500, marginBottom: 2 }}>{fmtHazard(report.hazard_type)}</div>
            <div style={{ fontSize: 11, color: 'var(--text2)' }}>{report.department}</div>
          </div>

          <button
            id="view-letter-btn-preview"
            onClick={() => setLetterOpen(true)}
            style={{ width: '100%', padding: 12, background: 'var(--green)', color: '#fff', border: 'none',
              borderRadius: 'var(--r-lg)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'Inter,sans-serif', marginBottom: 10 }}
          >
            📋 View Complaint Letter
          </button>
          <button
            id="back-to-preview-btn"
            onClick={() => nav('/preview')}
            style={{ width: '100%', padding: 12, background: 'var(--bg)', border: '0.5px solid var(--border2)',
              borderRadius: 'var(--r-lg)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
          >
            ← Back to Preview Hub
          </button>

          <ComplaintLetterModal open={letterOpen} onClose={() => setLetterOpen(false)} report={report} />
        </div>
      )}
    </Layout>
  )
}
