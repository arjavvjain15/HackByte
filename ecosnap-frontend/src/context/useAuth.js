import { useContext } from 'react'
import { AuthCtx } from './AuthCtx'

export const useAuth = () => {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
