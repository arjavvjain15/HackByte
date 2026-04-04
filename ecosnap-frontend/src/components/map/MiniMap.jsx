import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useEffect } from 'react'
import { markerColor, fmtHazard } from '../../utils/helpers'

function makeIcon(color) {
  return L.divIcon({
    html: `<div style="width:10px;height:10px;border-radius:50%;background:${color};border:1.5px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.25)"></div>`,
    className:'', iconSize:[10,10], iconAnchor:[5,5], popupAnchor:[0,-8],
  })
}
const youIcon = L.divIcon({
  html:`<div style="width:10px;height:10px;border-radius:50%;background:var(--green);border:2px solid #fff;box-shadow:0 0 0 4px rgba(29,158,117,.15)"></div>`,
  className:'', iconSize:[10,10], iconAnchor:[5,5],
})

function Sync({ center }) {
  const map = useMap()
  useEffect(() => { if (center) map.setView(center, map.getZoom()) }, [center, map])
  return null
}

export function MiniMap({ reports = [], center, userLoc }) {
  const c = center || (userLoc ? [userLoc.lat, userLoc.lng] : [20.5937, 78.9629])

  return (
    <div className="mini-map-wrap">
      <MapContainer center={c} zoom={13} style={{ height:'100%', width:'100%' }}
        zoomControl={false} attributionControl={false}
        dragging={false} scrollWheelZoom={false} doubleClickZoom={false} touchZoom={false}
        id="mini-map"
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Sync center={c} />
        {userLoc && <Marker position={[userLoc.lat, userLoc.lng]} icon={youIcon} />}
        {reports.slice(0,8).map(r =>
          r.lat && r.lng ? (
            <Marker key={r.id} position={[r.lat, r.lng]} icon={makeIcon(markerColor(r))}>
              <Popup><span style={{fontSize:10}}>{fmtHazard(r.hazard_type)}</span></Popup>
            </Marker>
          ) : null
        )}
      </MapContainer>
      {/* "You" label */}
      <div style={{
        position:'absolute', bottom:4, right:6,
        fontSize:9, color:'var(--text3)',
        background:'rgba(255,255,255,.85)', padding:'1px 5px', borderRadius:99,
      }}>
        {reports.length} nearby
      </div>
    </div>
  )
}
