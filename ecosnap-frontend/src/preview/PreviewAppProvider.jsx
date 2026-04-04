/**
 * PreviewAppProvider
 * Drop-in replacement for AppProvider that injects mock reports/notifications/badges.
 */
import { useCallback, useState } from 'react'
import { AppCtx } from '../context/AppCtx'
import {
  MOCK_REPORTS,
  MOCK_NOTIFICATIONS,
  MOCK_BADGES,
  MOCK_USER_LOC,
} from './mockData'

export function PreviewAppProvider({ children }) {
  const [reports, setReports]             = useState(MOCK_REPORTS)
  const [myReports, setMyReports]         = useState(MOCK_REPORTS.slice(0, 3))
  const [nearbyReports, setNearbyReports] = useState(MOCK_REPORTS)
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS)
  const [badges, setBadges]               = useState(MOCK_BADGES)
  const [upvoted, setUpvoted]             = useState(new Set())
  const [userLoc]                         = useState(MOCK_USER_LOC)
  const [mapCenter]                       = useState([MOCK_USER_LOC.lat, MOCK_USER_LOC.lng])

  const toggleUpvote = useCallback((id) => {
    setUpvoted(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n })
  }, [])

  const addReport = useCallback((r) => {
    setReports(p => [r, ...p])
    setMyReports(p => [r, ...p])
  }, [])

  const patchReportCount = useCallback((id, delta) => {
    const patch = list => list.map(r => r.id === id ? { ...r, upvotes: (r.upvotes || 0) + delta } : r)
    setReports(patch); setNearbyReports(patch)
  }, [])

  return (
    <AppCtx.Provider value={{
      reports, setReports, myReports, setMyReports,
      nearbyReports, setNearbyReports,
      notifications, setNotifications,
      badges, setBadges,
      upvoted, toggleUpvote,
      userLoc, setUserLoc: () => {},
      mapCenter, setMapCenter: () => {},
      addReport, patchReportCount,
    }}>
      {children}
    </AppCtx.Provider>
  )
}
