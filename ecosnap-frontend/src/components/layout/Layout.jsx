import { BottomNav } from './BottomNav'
import { FAB } from './FAB'

export function Layout({ children, showFAB = true, showNav = true }) {
  return (
    <div className="page" style={{ paddingBottom: showNav ? (showFAB ? 130 : 70) : 0 }}>
      {children}
      {showNav && <BottomNav />}
      {showFAB && <FAB />}
    </div>
  )
}
