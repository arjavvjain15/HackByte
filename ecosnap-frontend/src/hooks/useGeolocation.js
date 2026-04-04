import { useState, useCallback, useEffect } from 'react'
import { useApp } from '../context/useApp'

export function useGeolocation() {
  const [loc,     setLoc]     = useState(null)
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const { setUserLoc, setMapCenter } = useApp()

  const get = useCallback(() => {
    if (!navigator.geolocation) { setError('Geolocation not supported'); return }
    setLoading(true); setError(null)
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const l = { lat: p.coords.latitude, lng: p.coords.longitude, accuracy: p.coords.accuracy }
        setLoc(l)
        setUserLoc(l)
        setMapCenter([l.lat, l.lng])
        setLoading(false)
      },
      (e) => {
        const msgs = { 1:'Location access denied. Pin manually.', 2:'Position unavailable.', 3:'GPS timed out.' }
        setError(msgs[e.code] || 'Could not get location')
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    )
  }, [setUserLoc, setMapCenter]) 

  // Trigger once on mount
  useEffect(() => {
    const timer = setTimeout(get, 0)
    return () => clearTimeout(timer)
  }, [get])

  return { loc, error, loading, retry: get }
}
