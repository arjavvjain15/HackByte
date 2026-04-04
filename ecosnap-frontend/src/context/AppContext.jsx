import { useState, useCallback } from 'react'
import { AppCtx } from './AppCtx'

export function AppProvider({ children }) {
  const [reports,       setReports]       = useState([])
  const [myReports,     setMyReports]     = useState([])
  const [nearbyReports, setNearbyReports] = useState([])
  const [notifications, setNotifications] = useState([])
  const [badges,        setBadges]        = useState([])
  const [upvoted,       setUpvoted]       = useState(new Set())
  const [userLoc,       setUserLoc]       = useState(null)
  const [mapCenter,     setMapCenter]     = useState([20.5937, 78.9629])

  const toggleUpvote = useCallback((id) => {
    setUpvoted(p => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n })
  }, [])

  const addReport = useCallback((r) => {
    setReports(p => [r, ...p])
    setMyReports(p => [r, ...p])
  }, [])

  const patchReportCount = useCallback((id, delta) => {
    const patch = list => list.map(r => r.id === id ? { ...r, upvotes: (r.upvotes||0) + delta } : r)
    setReports(patch); setNearbyReports(patch)
  }, [])

  return (
    <AppCtx.Provider value={{
      reports, setReports, myReports, setMyReports,
      nearbyReports, setNearbyReports,
      notifications, setNotifications,
      badges, setBadges,
      upvoted, toggleUpvote,
      userLoc, setUserLoc,
      mapCenter, setMapCenter,
      addReport, patchReportCount,
    }}>
      {children}
    </AppCtx.Provider>
  )
}
