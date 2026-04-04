import { useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useApp } from '../../context/useApp'
import { useUpvote } from '../../hooks/useUpvote'
import { fmtHazard, formatDate, markerColor } from '../../utils/helpers'
import { SevBadge, StBadge } from '../common/Badges'

/* ── Icon factories ── */
function makeIcon(color, size = 12) {
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.25)"></div>`,
    className: '', iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -(size/2+4)],
  })
}
const userIcon = L.divIcon({
  html: `<div style="width:12px;height:12px;border-radius:50%;background:var(--green);border:2.5px solid #fff;box-shadow:0 0 0 4px rgba(29,158,117,.2)"></div>`,
  className: '', iconSize: [12,12], iconAnchor: [6,6],
})
const pinIcon = L.divIcon({
  html: `<div style="width:14px;height:14px;border-radius:50%;background:#534AB7;border:2.5px solid #fff;box-shadow:0 1px 8px rgba(0,0,0,.3)"></div>`,
  className: '', iconSize: [14,14], iconAnchor: [7,7],
})

/* ── Sync map center when prop changes ── */
function MapSync({ center }) {
  const map = useMap()
  useEffect(() => { if (center) map.setView(center, map.getZoom(), { animate: true }) }, [center, map])
  useEffect(() => {
    const handleMaxZoom = (e) => {
      const { lat, lng } = e.detail
      if (lat && lng) map.setView({ lat, lng }, 18, { animate: true })
    }
    window.addEventListener('map-zoom-max', handleMaxZoom)
    return () => window.removeEventListener('map-zoom-max', handleMaxZoom)
  }, [map])
  return null
}

/* ── Click handler for pin-drop mode ── */
function ClickHandler({ active, onPick }) {
  useMapEvents({ click(e) { if (active) onPick({ lat: e.latlng.lat, lng: e.latlng.lng }) } })
  return null
}

export function HazardMap({
  reports = [],
  height = '100%',
  showUser = true,
  pinMode = false,
  pinnedLoc = null,
  onPick,
}) {
  const { mapCenter, userLoc } = useApp()
  const { vote, upvoted } = useUpvote()

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      {pinMode && (
        <div style={{
          position:'absolute', top:10, left:'50%', transform:'translateX(-50%)',
          background:'rgba(83,74,183,.9)', color:'#fff', borderRadius:99,
          fontSize:11, padding:'5px 14px', zIndex:900, fontWeight:500,
          boxShadow:'0 2px 8px rgba(0,0,0,.2)', whiteSpace:'nowrap',
        }}>
          📍 Tap map to pin your report location
        </div>
      )}

      <MapContainer center={mapCenter} zoom={13} style={{ height:'100%', width:'100%' }} id="hazard-map">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="" />
        <MapSync center={mapCenter} />
        <ClickHandler active={pinMode} onPick={onPick} />

        {/* User location */}
        {showUser && userLoc && (
          <Marker position={[userLoc.lat, userLoc.lng]} icon={userIcon}>
            <Popup>
              <div style={{ textAlign:'center' }}>
                <strong style={{ fontSize:12 }}>📍 Your location</strong>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Manual pin */}
        {pinnedLoc && (
          <Marker position={[pinnedLoc.lat, pinnedLoc.lng]} icon={pinIcon}>
            <Popup><strong style={{ fontSize:12 }}>📌 Report location</strong></Popup>
          </Marker>
        )}

        {/* Report markers */}
        {reports.map(r => {
          if (!r.lat || !r.lng) return null
          const color = markerColor(r)
          const voted = upvoted.has(r.id)
          return (
            <Marker key={r.id} position={[r.lat, r.lng]} icon={makeIcon(color)}>
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:5, marginBottom:4 }}>
                    <SevBadge severity={r.severity} />
                    <StBadge status={r.status} />
                  </div>
                  <div style={{ fontWeight:500, fontSize:12, marginBottom:2 }}>{fmtHazard(r.hazard_type)}</div>
                  <div style={{ fontSize:11, color:'var(--text2)', marginBottom:6 }}>
                    {r.department} · {formatDate(r.created_at)}
                  </div>
                  <button
                    id={`map-upvote-${r.id}`}
                    className={`upvote-btn${voted?' voted':''}`}
                    style={{ width:'100%', justifyContent:'center' }}
                    onClick={() => vote(r.id)}
                  >
                    ▲ {voted ? 'Upvoted' : 'Upvote'} ({r.upvotes||0})
                  </button>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}
