import { NavLink } from 'react-router-dom'
import { useApp } from '../../context/useApp'

export function BottomNav() {
  const { notifications } = useApp()
  const unread = notifications.filter(n => !n.read).length

  return (
    <nav className="tab-bar">
      <NavLink to="/dashboard" id="nav-home" className={({isActive}) => `tab-item${isActive?' active':''}`}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
          <rect x="1" y="1" width="6" height="6" rx="1"/>
          <rect x="9" y="1" width="6" height="6" rx="1"/>
          <rect x="1" y="9" width="6" height="6" rx="1"/>
          <rect x="9" y="9" width="6" height="6" rx="1"/>
        </svg>
        <span className="tab-label">Home</span>
      </NavLink>

      <NavLink to="/map" id="nav-map" className={({isActive}) => `tab-item${isActive?' active':''}`}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
          <path d="M8 1L1 5v10h4V9h6v6h4V5L8 1z"/>
        </svg>
        <span className="tab-label">Map</span>
      </NavLink>

      <NavLink to="/nearby" id="nav-nearby" className={({isActive}) => `tab-item${isActive?' active':''}`}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
          <circle cx="8" cy="8" r="7"/>
          <path d="M8 5v3l2 2" strokeLinecap="round"/>
        </svg>
        <span className="tab-label">My reports</span>
      </NavLink>

      <NavLink to="/badges" id="nav-badges" className={({isActive}) => `tab-item${isActive?' active':''}`}>
        <div style={{ position:'relative', display:'flex' }}>
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" width={18} height={18}>
            <circle cx="8" cy="6" r="3"/>
            <path d="M2 14c0-3.31 2.69-6 6-6s6 2.69 6 6"/>
          </svg>
          {unread > 0 && (
            <span style={{
              position:'absolute', top:-4, right:-6,
              background:'var(--red)', color:'#fff',
              borderRadius:99, fontSize:8, fontWeight:600,
              padding:'1px 3px', minWidth:12, textAlign:'center',
            }}>{unread}</span>
          )}
        </div>
        <span className="tab-label">Profile</span>
      </NavLink>
    </nav>
  )
}
