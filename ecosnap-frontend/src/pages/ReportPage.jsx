import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { HazardMap } from '../components/map/HazardMap'
import { ComplaintLetterModal } from '../components/letter/ComplaintLetterModal'
import { SevBadge } from '../components/common/Badges'
import { Spinner } from '../components/common/Spinner'
import { useCamera } from '../hooks/useCamera'
import { useGeolocation } from '../hooks/useGeolocation'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { classifyHazard, submitReport } from '../services/api'
import { fmtHazard } from '../utils/helpers'
import toast from 'react-hot-toast'

const STEPS = ['Photo', 'AI Analysis', 'Location', 'Review']

export function ReportPage() {
  const nav = useNavigate()
  const { user } = useAuth()
  const { addReport } = useApp()
  const { photo, capture, retake, upload, uploading } = useCamera()
  const { loc, error: gpsErr, loading: gpsLoad, retry: retryGps } = useGeolocation()

  const [step,      setStep]      = useState(0)  // 0-3 + 4=success
  const [ai,        setAi]        = useState(null)
  const [aiLoad,    setAiLoad]    = useState(false)
  const [pinnedLoc, setPinnedLoc] = useState(null)
  const [submitting,setSubmitting]= useState(false)
  const [submitted, setSubmitted] = useState(null)
  const [letterOpen,setLetterOpen]= useState(false)

  const fileRef = useRef()

  const chosenLoc = loc || pinnedLoc

  /* ── Step 0 → 1: take photo + classify ── */
  async function handlePhotoConfirm() {
    if (!photo) return
    setStep(1); setAiLoad(true)
    try {
      const photoUrl = await upload(user?.id)
      const result   = await classifyHazard(photo.file)
      setAi({ ...result, photo_url: photoUrl })
    } catch { setAi({ hazard_type:'unknown_hazard', severity:'medium', department:'Municipal Authority', photo_url: photo?.preview }) }
    finally { setAiLoad(false); setStep(2) }
  }

  /* ── Step 2 → 3 ── */
  function handleLocConfirm() {
    if (!chosenLoc) { toast.error('Please enable GPS or pin a location on the map'); return }
    setStep(3)
  }

  /* ── Final submit ── */
  async function handleSubmit() {
    if (!chosenLoc) { toast.error('Location required'); return }
    setSubmitting(true)
    try {
      const payload = {
        hazard_type:  ai?.hazard_type || 'unknown',
        severity:     ai?.severity    || 'medium',
        department:   ai?.department  || 'Municipal Authority',
        lat: chosenLoc.lat, lng: chosenLoc.lng,
        photo_url:    ai?.photo_url || '',
        user_id:      user?.id || 'anon',
      }
      const result = await submitReport(payload).catch(() => ({ ...payload, id: 'DEMO-'+Date.now(), status:'open', upvotes:0, created_at: new Date().toISOString() }))
      addReport(result)
      setSubmitted(result)
      toast.success('Hazard reported! 🌿')
    } catch { toast.error('Submission failed') }
    finally { setSubmitting(false) }
  }

  /* ─────────────── SUCCESS SCREEN ─────────────── */
  if (submitted) return (
    <Layout showFAB={false}>
      <div className="page-enter" style={{ padding:'60px 24px 32px', textAlign:'center', background:'var(--bg)' }}>
        <div style={{ fontSize:56, marginBottom:16 }} className="anim-bounceIn">✅</div>
        <h2 style={{ fontSize:20, fontWeight:600, marginBottom:8 }}>Report submitted!</h2>
        <p style={{ fontSize:13, color:'var(--text2)', marginBottom:32, lineHeight:1.6 }}>
          Your hazard has been mapped and the relevant department has been alerted.
          Neighbours can now upvote it to escalate.
        </p>

        <div style={{ background:'var(--bg2)', borderRadius:'var(--r-lg)', padding:'14px 16px', marginBottom:24, textAlign:'left' }}>
          <div style={{ display:'flex', gap:6, marginBottom:4 }}>
            <SevBadge severity={submitted.severity} />
            <span style={{ fontSize:9, color:'var(--text3)', marginLeft:'auto' }}>#{String(submitted.id).slice(-6).toUpperCase()}</span>
          </div>
          <div style={{ fontWeight:500, marginBottom:2 }}>{fmtHazard(submitted.hazard_type)}</div>
          <div style={{ fontSize:11, color:'var(--text2)' }}>{submitted.department}</div>
        </div>

        <button
          id="view-letter-btn"
          onClick={() => setLetterOpen(true)}
          style={{ width:'100%', padding:12, background:'var(--green)', color:'#fff', border:'none',
            borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif', marginBottom:10 }}
        >
          📋 View Complaint Letter
        </button>
        <button
          id="go-dashboard-btn"
          onClick={() => nav('/dashboard')}
          style={{ width:'100%', padding:12, background:'var(--bg)', border:'0.5px solid var(--border2)',
            borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif' }}
        >
          Back to Dashboard
        </button>

        <ComplaintLetterModal open={letterOpen} onClose={() => setLetterOpen(false)} report={submitted} />
      </div>
    </Layout>
  )

  /* ─────────────── REPORT WIZARD ─────────────── */
  return (
    <Layout showFAB={false}>
      <div className="page-enter" style={{ background:'var(--bg)', minHeight:'100vh' }}>
        {/* Top bar */}
        <div style={{ display:'flex', alignItems:'center', gap:12, padding:'14px 14px 10px', borderBottom:'0.5px solid var(--border)' }}>
          <button onClick={() => step > 0 ? setStep(s => s-1) : nav(-1)} style={{ background:'none', border:'none', cursor:'pointer', fontSize:18, color:'var(--text3)', padding:'0 4px' }}>←</button>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:14, fontWeight:500 }}>Report a Hazard</div>
            <div style={{ fontSize:11, color:'var(--text2)' }}>Step {step+1} of {STEPS.length} — {STEPS[step]}</div>
          </div>
        </div>

        {/* Step dots */}
        <div style={{ display:'flex', gap:5, padding:'8px 14px 0', marginBottom:10 }}>
          {STEPS.map((_,i) => (
            <div key={i} className={`step-dot${i===step?' active':i<step?' done':''}`} style={{ flex:1 }} />
          ))}
        </div>

        <div style={{ padding:'0 14px 24px' }}>

          {/* ── STEP 0: Camera ── */}
          {step === 0 && (
            <div className="anim-fadeIn">
              <p style={{ fontSize:12, color:'var(--text2)', marginBottom:14 }}>Take or upload a photo of the hazard.</p>
              {!photo ? (
                <div
                  id="camera-pick-area"
                  onClick={() => fileRef.current.click()}
                  style={{
                    border:'1.5px dashed var(--border2)', borderRadius:'var(--r-lg)',
                    height:200, display:'flex', flexDirection:'column',
                    alignItems:'center', justifyContent:'center', gap:8,
                    cursor:'pointer', background:'var(--bg2)', marginBottom:14,
                  }}
                >
                  <div style={{ fontSize:36 }}>📷</div>
                  <div style={{ fontSize:13, fontWeight:500 }}>Open Camera</div>
                  <div style={{ fontSize:11, color:'var(--text3)' }}>or select from gallery</div>
                </div>
              ) : (
                <div style={{ position:'relative', marginBottom:14 }}>
                  <img src={photo.preview} alt="Preview" style={{ width:'100%', borderRadius:'var(--r-lg)', maxHeight:260, objectFit:'cover', border:'0.5px solid var(--border)' }} />
                  <button
                    id="retake-btn"
                    onClick={retake}
                    style={{ position:'absolute', top:8, right:8, background:'rgba(0,0,0,.55)', color:'#fff', border:'none', borderRadius:'var(--r-sm)', padding:'5px 10px', fontSize:11, cursor:'pointer' }}
                  >
                    Retake
                  </button>
                </div>
              )}
              <input hidden type="file" accept="image/*" capture="environment" ref={fileRef} onChange={e => capture(e.target.files[0])} />
              <button
                id="confirm-photo-btn"
                disabled={!photo || uploading}
                onClick={handlePhotoConfirm}
                style={{ width:'100%', padding:12, background: photo ? 'var(--green)' : 'var(--bg3)',
                  color: photo ? '#fff' : 'var(--text3)', border:'none', borderRadius:'var(--r-lg)',
                  fontSize:13, fontWeight:500, cursor: photo ? 'pointer' : 'not-allowed', fontFamily:'Inter,sans-serif',
                  display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}
              >
                {uploading ? <><Spinner size={16} color="#fff" /> Uploading...</> : 'Confirm Photo →'}
              </button>
            </div>
          )}

          {/* ── STEP 1: AI loading ── */}
          {step === 1 && (
            <div className="anim-fadeIn" style={{ textAlign:'center', paddingTop:40 }}>
              <div style={{ width:60, height:60, background:'var(--green-light)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 16px', fontSize:28 }}>
                🤖
              </div>
              {aiLoad ? (
                <>
                  <div style={{ fontWeight:500, marginBottom:8 }}>Analyzing with AI...</div>
                  <div style={{ fontSize:12, color:'var(--text2)', marginBottom:24 }}>Identifying hazard + severity</div>
                  <Spinner size={28} />
                </>
              ) : (
                <div style={{ fontSize:13, color:'var(--text2)' }}>Processing done, moving to results...</div>
              )}
            </div>
          )}

          {/* ── STEP 2: AI result + GPS ── */}
          {step === 2 && ai && (
            <div className="anim-fadeIn">
              {/* AI result card */}
              <div style={{ background:'var(--green-light)', borderRadius:'var(--r-lg)', padding:'12px 14px', marginBottom:14, border:'0.5px solid var(--green-mid)' }}>
                <div style={{ fontSize:11, color:'var(--green-dark)', fontWeight:500, marginBottom:6 }}>🤖 AI Classification Result</div>
                <div style={{ fontWeight:600, fontSize:16, marginBottom:4 }}>{fmtHazard(ai.hazard_type)}</div>
                <div style={{ display:'flex', gap:6, alignItems:'center', marginBottom:4 }}>
                  <SevBadge severity={ai.severity} />
                  <span style={{ fontSize:11, color:'var(--text2)' }}>→ {ai.department}</span>
                </div>
              </div>

              {/* GPS status */}
              <div style={{ marginBottom:12 }}>
                <div style={{ fontSize:12, fontWeight:500, marginBottom:8 }}>📍 Location</div>
                {gpsLoad && (
                  <div style={{ display:'flex', gap:8, alignItems:'center', fontSize:12, color:'var(--text2)', padding:'10px 0' }}>
                    <Spinner size={14} /> Getting GPS location...
                  </div>
                )}
                {loc && (
                  <div style={{ display:'flex', gap:6, alignItems:'center', background:'var(--green-light)', borderRadius:'var(--r-md)', padding:'8px 10px' }}>
                    <span style={{ fontSize:14 }}>📍</span>
                    <span style={{ fontSize:11, color:'var(--green-dark)', fontWeight:500 }}>Location attached</span>
                    <span style={{ fontSize:10, color:'var(--green-dark)', marginLeft:'auto', opacity:.7 }}>
                      {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}
                    </span>
                  </div>
                )}
                {gpsErr && !loc && (
                  <div style={{ background:'var(--orange-light)', borderRadius:'var(--r-md)', padding:'10px 12px', marginBottom:10, border:'0.5px solid var(--orange)' }}>
                    <div style={{ fontSize:11, color:'var(--orange-dark)', fontWeight:500 }}>⚠ {gpsErr}</div>
                    <div style={{ fontSize:11, color:'var(--orange-dark)', marginTop:4 }}>Pin your location on the map below</div>
                    <button onClick={retryGps} style={{ marginTop:6, fontSize:10, color:'var(--green-dark)', cursor:'pointer', background:'none', border:'none', textDecoration:'underline', fontFamily:'Inter,sans-serif' }}>Try GPS again</button>
                  </div>
                )}
              </div>

              {/* Map pin fallback */}
              {!loc && (
                <div style={{ marginBottom:14 }}>
                  <div style={{ fontSize:11, color:'var(--text2)', marginBottom:6 }}>Tap on the map to pin your location:</div>
                  <div style={{ borderRadius:'var(--r-md)', overflow:'hidden', border:'0.5px solid var(--border2)' }}>
                    <HazardMap height={200} reports={[]} showUser={false} pinMode={true} pinnedLoc={pinnedLoc} onPick={setPinnedLoc} />
                  </div>
                  {pinnedLoc && (
                    <div style={{ fontSize:11, color:'var(--green-dark)', marginTop:6, fontWeight:500 }}>
                      📌 Pinned: {pinnedLoc.lat.toFixed(4)}, {pinnedLoc.lng.toFixed(4)}
                    </div>
                  )}
                </div>
              )}

              <button
                id="confirm-loc-btn"
                onClick={handleLocConfirm}
                disabled={!chosenLoc}
                style={{ width:'100%', padding:12, background: chosenLoc ? 'var(--green)' : 'var(--bg3)',
                  color: chosenLoc ? '#fff' : 'var(--text3)', border:'none', borderRadius:'var(--r-lg)',
                  fontSize:13, fontWeight:500, cursor: chosenLoc ? 'pointer' : 'not-allowed', fontFamily:'Inter,sans-serif' }}
              >
                Confirm Location →
              </button>
            </div>
          )}

          {/* ── STEP 3: Review & Submit ── */}
          {step === 3 && ai && (
            <div className="anim-fadeIn">
              <p style={{ fontSize:12, color:'var(--text2)', marginBottom:14 }}>Review your report before submitting.</p>

              {/* Photo thumb */}
              {photo?.preview && (
                <img src={photo.preview} alt="Hazard" style={{ width:'100%', height:160, objectFit:'cover', borderRadius:'var(--r-lg)', marginBottom:12, border:'0.5px solid var(--border)' }} />
              )}

              {/* Summary card */}
              <div style={{ background:'var(--bg2)', borderRadius:'var(--r-lg)', padding:'12px 14px', marginBottom:16 }}>
                <Row k="Hazard type" v={fmtHazard(ai.hazard_type)} />
                <Row k="Severity"    v={<SevBadge severity={ai.severity} />} />
                <Row k="Department"  v={ai.department} />
                <Row k="Location"    v={chosenLoc ? `${chosenLoc.lat.toFixed(4)}, ${chosenLoc.lng.toFixed(4)}` : '—'} />
              </div>

              <button
                id="submit-report-btn"
                onClick={handleSubmit}
                disabled={submitting}
                style={{ width:'100%', padding:12, background:'var(--green)', color:'#fff', border:'none',
                  borderRadius:'var(--r-lg)', fontSize:13, fontWeight:500, cursor:'pointer', fontFamily:'Inter,sans-serif',
                  display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}
              >
                {submitting ? <><Spinner size={16} color="#fff" /> Submitting...</> : '✓ Submit Report'}
              </button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

function Row({ k, v }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderBottom:'0.5px solid var(--border)' }}>
      <span style={{ fontSize:11, color:'var(--text2)' }}>{k}</span>
      <span style={{ fontSize:11, fontWeight:500, color:'var(--text)' }}>{v}</span>
    </div>
  )
}
