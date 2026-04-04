/**
 * LetterPreviewPage  (/preview/letter)
 * Shows the complaint letter modal open by default so you can inspect it directly.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ComplaintLetterModal } from '../components/letter/ComplaintLetterModal'
import { MOCK_SUBMITTED_REPORT } from '../preview/mockData'

export function LetterPreviewPage() {
  const nav = useNavigate()
  const [open, setOpen] = useState(true)

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', fontFamily: 'Inter,sans-serif' }}>
      {/* Preview bar */}
      <div style={{
        background: 'linear-gradient(90deg,#8b5cf6,#6366f1)',
        padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: '#fff', letterSpacing: .4 }}>
          🔬 PREVIEW — Complaint Letter Modal
        </span>
        <button
          onClick={() => nav('/preview')}
          style={{ marginLeft: 'auto', background: 'rgba(255,255,255,.15)', border: '1px solid rgba(255,255,255,.2)',
            color: '#fff', borderRadius: 6, padding: '2px 12px', fontSize: 10, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
        >
          ← Hub
        </button>
      </div>

      {/* Backdrop to make the modal visible */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 36px)', gap: 16 }}>
        {!open && (
          <>
            <div style={{ fontSize: 40, marginBottom: 8 }}>📋</div>
            <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--text)' }}>Complaint Letter Modal</div>
            <button
              id="reopen-letter-btn"
              onClick={() => setOpen(true)}
              style={{ padding: '10px 24px', background: 'var(--green)', color: '#fff', border: 'none',
                borderRadius: 'var(--r-lg)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'Inter,sans-serif' }}
            >
              Open Letter Modal
            </button>
          </>
        )}
      </div>

      <ComplaintLetterModal
        open={open}
        onClose={() => setOpen(false)}
        report={MOCK_SUBMITTED_REPORT}
      />
    </div>
  )
}
