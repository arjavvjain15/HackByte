import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabaseClient'
import { AuthCtx } from './AuthCtx'

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) fetchProfile(session.user.id)
      else setLoading(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null)
      if (session?.user) fetchProfile(session.user.id)
      else { setProfile(null); setLoading(false) }
    })
    return () => subscription.unsubscribe()
  }, [])

  async function fetchProfile(uid) {
    try {
      // maybeSingle() returns null (not 406) when no profile row exists yet
      const { data } = await supabase.from('profiles').select('*').eq('id', uid).maybeSingle()
      if (data) setProfile(data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  async function signInWithGoogle() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) throw error
  }

  async function signOut() {
    await supabase.auth.signOut()
    setUser(null); setProfile(null)
  }

  return (
    <AuthCtx.Provider value={{ user, profile, loading, isAdmin: profile?.is_admin === true, signInWithGoogle, signOut }}>
      {children}
    </AuthCtx.Provider>
  )
}


