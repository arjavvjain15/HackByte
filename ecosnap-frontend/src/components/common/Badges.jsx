import { sevBadgeClass } from '../../utils/helpers'

export function SevBadge({ severity }) {
  const cls = sevBadgeClass(severity)
  const label = severity ? severity.charAt(0).toUpperCase() + severity.slice(1) : '—'
  return <span className={`sev-badge ${cls}`}>{label}</span>
}

export function StBadge({ status }) {
  const map = { open:['st-open','Open'], in_review:['st-review','In review'], resolved:['st-resolved','Done'] }
  const [cls, label] = map[status] || ['st-open', status || '—']
  return <span className={`st-badge ${cls}`}>{label}</span>
}

export function StatusDot({ status }) {
  const cls = { open:'dot-open', in_review:'dot-review', resolved:'dot-resolved' }[status] || 'dot-open'
  return <div className={`dot ${cls}`} />
}
