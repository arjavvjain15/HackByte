import { useState } from 'react'
import { BottomSheet } from '../common/BottomSheet'
import toast from 'react-hot-toast'

function buildFallbackLetter(report) {
  const d     = new Date().toLocaleDateString('en-IN', { day:'numeric', month:'long', year:'numeric' })
  const hType = (report.hazard_type || '').replace(/_/g,' ').replace(/\b\w/g, l => l.toUpperCase())
  const dept  = report.department || 'Concerned Authority'
  return `To,
The Head,
${dept}

Subject: Formal Complaint — ${hType} [Severity: ${(report.severity||'').toUpperCase()}]

Date: ${d}

Dear Sir/Madam,

I am writing to report an environmental hazard requiring immediate attention.

REPORT DETAILS:
━━━━━━━━━━━━━━━
• Hazard Type  : ${hType}
• Severity     : ${(report.severity||'unknown').toUpperCase()}
• GPS Location : ${report.lat?.toFixed(5)}°N, ${report.lng?.toFixed(5)}°E
• Photo URL    : ${report.photo_url || 'Attached via EcoSnap'}
• Report ID    : ${report.id || 'AUTO-' + Date.now()}
• Date Filed   : ${d}

REQUESTED ACTION:
━━━━━━━━━━━━━━━━
1. Immediate on-site inspection
2. Appropriate cleanup / remediation
3. Follow-up notification to reporter
4. Preventive measures going forward

This report was submitted through EcoSnap, an AI-powered civic hazard reporting platform. Photo evidence and GPS coordinates are available for verification.

Kindly treat this with urgency.

Yours sincerely,
EcoSnap Community Reporter
ecosnap.app
`
}

export function ComplaintLetterModal({ open, onClose, report }) {
  const [copied, setCopied] = useState(false)

  if (!report) return null
  const letter = report.complaint || buildFallbackLetter(report)

  const copy = async () => {
    await navigator.clipboard.writeText(letter).catch(() => {})
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2500)
  }

  const share = async () => {
    const data = { title: 'EcoSnap Complaint Letter', text: letter }
    try {
      if (navigator.share && navigator.canShare(data)) { await navigator.share(data); toast.success('Shared!') }
      else { await copy() }
    } catch (e) { if (e.name !== 'AbortError') await copy() }
  }

  return (
    <BottomSheet open={open} onClose={onClose} title="Complaint Letter">
      <div style={{ padding:'12px 16px 24px' }}>
        <p style={{ fontSize:11, color:'var(--text2)', marginBottom:8 }}>
          AI-generated formal complaint ready to send.
        </p>

        {/* Letter body */}
        <pre id="complaint-letter-text" style={{
          fontFamily:'monospace', fontSize:11.5, lineHeight:1.7,
          color:'var(--text)', background:'var(--bg2)',
          border:'0.5px solid var(--border)', borderRadius:'var(--r-md)',
          padding:'12px 14px', whiteSpace:'pre-wrap', wordBreak:'break-word',
          maxHeight:340, overflowY:'auto', marginBottom:12,
        }}>
          {letter}
        </pre>

        {/* Action buttons */}
        <div style={{ display:'flex', gap:8 }}>
          <button
            id="copy-letter-btn"
            onClick={copy}
            style={{
              flex:1, padding:'9px', borderRadius:'var(--r-md)',
              border:'0.5px solid var(--border2)',
              background: copied ? 'var(--green-light)' : 'var(--bg)',
              color: copied ? 'var(--green-dark)' : 'var(--text)',
              fontSize:12, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif',
              transition:'all .15s',
            }}
          >
            {copied ? '✓ Copied!' : '⎘ Copy'}
          </button>
          <button
            id="share-letter-btn"
            onClick={share}
            style={{
              flex:1, padding:'9px', borderRadius:'var(--r-md)',
              background:'var(--green)', color:'#fff', border:'none',
              fontSize:12, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif',
            }}
          >
            ↗ Share
          </button>
        </div>
      </div>
    </BottomSheet>
  )
}
