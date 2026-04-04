/**
 * PreviewAuthProvider
 * Drop-in replacement for AuthProvider that injects mock data.
 * Reads `?role=admin` or `?role=user` (default: user) from URL.
 */
import { AuthCtx } from '../context/AuthCtx'
import { MOCK_USER, MOCK_PROFILE, MOCK_ADMIN_PROFILE } from './mockData'

export function PreviewAuthProvider({ children, forceAdmin = false }) {
  const isAdmin = forceAdmin || new URLSearchParams(window.location.search).get('role') === 'admin'
  const profile = isAdmin ? MOCK_ADMIN_PROFILE : MOCK_PROFILE

  const mockValue = {
    user: MOCK_USER,
    profile,
    loading: false,
    isAdmin,
    signInWithGoogle: () => Promise.resolve(),
    signOut: () => Promise.resolve(),
  }

  return <AuthCtx.Provider value={mockValue}>{children}</AuthCtx.Provider>
}
