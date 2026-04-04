import { useState, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { getAllReports, getMyReports, getNearbyReports } from '../services/api'
import { DEMO_REPORTS } from '../utils/helpers'

export function useReports() {
  const { user } = useAuth()
  const { reports, setReports, myReports, setMyReports, nearbyReports, setNearbyReports, userLoc } = useApp()
  const [loadAll,    setLoadAll]    = useState(false)
  const [loadMine,   setLoadMine]   = useState(false)
  const [loadNearby, setLoadNearby] = useState(false)

  const fetchAll = useCallback(async () => {
    setLoadAll(true)
    try {
      const d = await getAllReports()
      setReports(Array.isArray(d) ? d : d?.reports || DEMO_REPORTS)
    } catch { setReports(DEMO_REPORTS) }
    finally { setLoadAll(false) }
  }, [setReports])

  const fetchMine = useCallback(async () => {
    if (!user) return
    setLoadMine(true)
    try {
      const d = await getMyReports(user.id)
      setMyReports(Array.isArray(d) ? d : d?.reports || DEMO_REPORTS.slice(0,3))
    } catch { setMyReports(DEMO_REPORTS.slice(0,3)) }
    finally { setLoadMine(false) }
  }, [user, setMyReports])

  const fetchNearby = useCallback(async () => {
    if (!userLoc) return
    setLoadNearby(true)
    try {
      const d = await getNearbyReports(userLoc.lat, userLoc.lng)
      setNearbyReports(Array.isArray(d) ? d : d?.reports || DEMO_REPORTS)
    } catch { setNearbyReports(DEMO_REPORTS) }
    finally { setLoadNearby(false) }
  }, [userLoc, setNearbyReports])

  return { reports, myReports, nearbyReports, loadAll, loadMine, loadNearby, fetchAll, fetchMine, fetchNearby }
}
