import { useNavigate } from 'react-router-dom'

export function FAB({ onClick }) {
  const nav = useNavigate()
  return (
    <button className="fab-btn" id="fab-report" onClick={onClick || (() => nav('/report'))} aria-label="Report a hazard">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="white" strokeWidth="1.5"/>
        <path d="M8 5v6M5 8h6" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
      Report a new hazard
    </button>
  )
}
