/**
 * PreviewWrapper
 * Wraps any page with both mock providers so it renders without real auth/API.
 * Usage: <PreviewWrapper forceAdmin><AdminPage /></PreviewWrapper>
 */
import { PreviewAuthProvider } from './PreviewAuthProvider'
import { PreviewAppProvider }  from './PreviewAppProvider'

export function PreviewWrapper({ children, forceAdmin = false }) {
  return (
    <PreviewAuthProvider forceAdmin={forceAdmin}>
      <PreviewAppProvider>
        {children}
      </PreviewAppProvider>
    </PreviewAuthProvider>
  )
}
