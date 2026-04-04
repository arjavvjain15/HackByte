import { useState, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { getAllReports, getMyReports } from '../services/api'
import { DEMO_REPORTS } from '../utils/helpers'

export function useReports() {
  const { user } = useAuth()
  const { reports, setReports, myReports, setMyReports, nearbyReports, setNearbyReports } = useApp()
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
    setLoadNearby(true)
    try {
      const d = await getAllReports()
      setNearbyReports(Array.isArray(d) ? d : d?.reports || DEMO_REPORTS)
    } catch { setNearbyReports(DEMO_REPORTS) }
    finally { setLoadNearby(false) }
  }, [setNearbyReports])

  return { reports, myReports, nearbyReports, loadAll, loadMine, loadNearby, fetchAll, fetchMine, fetchNearby }
}
