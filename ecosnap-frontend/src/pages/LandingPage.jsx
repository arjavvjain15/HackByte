import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import { Spinner } from '../components/common/Spinner'
import toast from 'react-hot-toast'

export function LandingPage() {
  const { user, isAdmin, loading, signInWithGoogle } = useAuth()
  const nav = useNavigate()

  useEffect(() => {
    if (!loading && user) nav(isAdmin ? '/admin' : '/dashboard', { replace: true })
  }, [user, isAdmin, loading, nav])

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh', background:'#fff' }}>
      <Spinner size={28} />
    </div>
  )

  const handleLogin = async () => {
    try { await signInWithGoogle() }
    catch { toast.error('Login failed. Try again.') }
  }

  return (
    <div style={{ minHeight:'100vh', background:'#fff', display:'flex', flexDirection:'column' }}>
      {/* Header */}
      <div style={{ padding:'16px 20px', display:'flex', alignItems:'center', gap:8, borderBottom:'0.5px solid var(--border)' }}>
        <div style={{ width:8, height:8, borderRadius:'50%', background:'var(--green)' }} />
        <span style={{ fontWeight:600, fontSize:15, color:'var(--text)' }}>EcoSnap</span>
        <span style={{ marginLeft:'auto', fontSize:10, background:'var(--green-light)', color:'var(--green-dark)', padding:'2px 7px', borderRadius:4, fontWeight:500 }}>Beta</span>
      </div>

      {/* Hero */}
      <div style={{ flex:1, display:'flex', flexDirection:'column', justifyContent:'center', padding:'0 28px 32px' }}>
        <div style={{ marginBottom:32 }}>
          <div style={{ display:'inline-flex', alignItems:'center', gap:6, background:'var(--green-light)', color:'var(--green-dark)', borderRadius:99, padding:'4px 10px', fontSize:11, fontWeight:500, marginBottom:16 }}>
            <svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="var(--green)"/></svg>
            AI-Powered Reporting
          </div>
          <h1 style={{ fontSize:32, fontWeight:700, lineHeight:1.2, color:'var(--text)', marginBottom:12 }}>
            Patch the<br />
            <span style={{ color:'var(--green)' }}>Reality</span>
          </h1>
          <p style={{ fontSize:13, color:'var(--text2)', lineHeight:1.6, maxWidth:280 }}>
            Take a photo of an environmental hazard. AI identifies it, drafts a formal complaint, and pins it on the community map — in under 30 seconds.
          </p>
        </div>

        {/* Steps */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:32 }}>
          {[
            { emoji:'📸', label:'Snap a photo', desc:'Open camera in one tap' },
            { emoji:'🤖', label:'AI classifies it', desc:'Vision + Gemini pipeline' },
            { emoji:'📍', label:'GPS tagged', desc:'Auto-attaches coordinates' },
            { emoji:'📋', label:'Letter generated', desc:'Formal complaint drafted' },
          ].map(({ emoji, label, desc }) => (
            <div key={label} style={{
              background:'var(--bg2)', borderRadius:'var(--r-md)',
              padding:'10px 12px',
            }}>
              <div style={{ fontSize:20, marginBottom:4 }}>{emoji}</div>
              <div style={{ fontSize:11, fontWeight:500, marginBottom:2 }}>{label}</div>
              <div style={{ fontSize:10, color:'var(--text2)' }}>{desc}</div>
            </div>
          ))}
        </div>

        {/* Trust strip */}
        <div style={{ display:'flex', gap:14, marginBottom:28, flexWrap:'wrap' }}>
          {['🔒 Secure', '📡 GPS Verified', '⚡ AI Powered'].map(t => (
            <span key={t} style={{ fontSize:11, color:'var(--text2)', display:'flex', alignItems:'center', gap:4 }}>{t}</span>
          ))}
        </div>

        {/* CTA */}
        <button
          id="google-login-btn"
          onClick={handleLogin}
          style={{
            width:'100%', padding:'13px 16px',
            background:'var(--green)', color:'#fff', border:'none',
            borderRadius:'var(--r-lg)', fontSize:14, fontWeight:500,
            cursor:'pointer', fontFamily:'Inter,sans-serif',
            display:'flex', alignItems:'center', justifyContent:'center', gap:10,
            boxShadow:'0 2px 14px rgba(29,158,117,.3)',
          }}
        >
          {/* Google logo */}
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path fill="#fff" d="M9 3.5c1.5 0 2.8.5 3.8 1.5L15.2 2.7C13.6 1.2 11.4.3 9 .3c-3.8 0-7 2.2-8.6 5.5l2.7 2.1C3.9 5.4 6.2 3.5 9 3.5z"/>
            <path fill="#fff" d="M17.5 9.2c0-.7-.1-1.3-.2-1.9H9v3.6h4.8c-.2 1.1-.8 2-1.7 2.6l2.6 2c1.5-1.4 2.4-3.5 2.4-6.3 0-.1-.1 0-.6 0z"/>
            <path fill="#fff" d="M3.1 10.6C2.9 10 2.8 9.5 2.8 9s.1-1 .3-1.6L.4 5.3C-.2 6.4-.5 7.7-.5 9s.3 2.6.9 3.7l2.7-2.1z"/>
            <path fill="#fff" d="M9 17.7c2.4 0 4.5-.8 6-2.2l-2.6-2c-.8.6-1.9.9-3.4.9-2.8 0-5.1-1.9-5.9-4.4L.4 12.1C2 15.5 5.2 17.7 9 17.7z"/>
          </svg>
          Continue with Google
        </button>

        <p style={{ textAlign:'center', fontSize:11, color:'var(--text3)', marginTop:12 }}>
          Free · No app download · Works on any phone
        </p>
      </div>
    </div>
  )
}
