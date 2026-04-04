import { fmtHazard, formatDate, statusProgress, statusBarClass, statusLabel } from '../../utils/helpers'
import { SevBadge, StBadge, StatusDot } from '../common/Badges'
import { useUpvote } from '../../hooks/useUpvote'

export function ReportCard({ report, showProgress = true, showUpvote = true, compact = false }) {
  const { vote, upvoted } = useUpvote()
  const isVoted   = upvoted.has(report.id)
  const progress  = statusProgress(report.status)
  const barClass  = statusBarClass(report.status)
  const isResolved = report.status === 'resolved'

  return (
    <div className={`rc${isResolved ? ' rc-resolved' : ''}`}>
      {/* Top row: severity + ID */}
      <div style={{ display:'flex', alignItems:'center', gap:5, marginBottom:3 }}>
        <SevBadge severity={report.severity} />
        <span style={{ fontSize:9, color:'var(--text3)', marginLeft:'auto' }}>
          #{String(report.id).slice(-3).toUpperCase()}
        </span>
      </div>

      {/* Hazard type */}
      <div style={{ fontSize:11, fontWeight:500, marginBottom:compact?2:3 }}>
        {fmtHazard(report.hazard_type)}
      </div>

      {/* Location + time */}
      {!compact && (
        <div style={{ fontSize:10, color:'var(--text2)', marginBottom:4 }}>
          {report.department || 'Unknown dept'} · {formatDate(report.created_at)}
        </div>
      )}

      {/* Footer: upvotes + status */}
      <div style={{ display:'flex', alignItems:'center', gap:5 }}>
        <span style={{ fontSize:9, color:'var(--text3)' }}>{report.upvotes || 0} upvotes</span>
        <StBadge status={report.status} />
        {showUpvote && (
          <button
            id={`upvote-${report.id}`}
            className={`upvote-btn${isVoted ? ' voted' : ''}`}
            onClick={(e) => { e.stopPropagation(); vote(report.id) }}
            style={{ marginLeft:'auto' }}
          >
            ▲ {isVoted ? 'Upvoted' : 'Upvote'}
          </button>
        )}
      </div>

      {/* Progress bar */}
      {showProgress && (
        <div className="pbar">
          <div className={`pbar-fill ${barClass}`} style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  )
}
