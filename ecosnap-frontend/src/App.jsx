import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { AppProvider } from './context/AppContext'
import { LandingPage }   from './pages/LandingPage'
import { DashboardPage } from './pages/DashboardPage'
import { ReportPage }    from './pages/ReportPage'
import { MapPage }       from './pages/MapPage'
import { NearbyPage }    from './pages/NearbyPage'
import { BadgesPage }    from './pages/BadgesPage'
import { MyReportsPage } from './pages/MyReportsPage'
import { AdminPage }       from './pages/AdminPage'
import { PageSpinner }     from './components/common/Spinner'
/* ─── Preview (dev-only) ─── */
import { PreviewPage }     from './pages/PreviewPage'
import { AIResultPreviewPage } from './pages/AIResultPreviewPage'
import { LetterPreviewPage }   from './pages/LetterPreviewPage'
import { PreviewWrapper }  from './preview/PreviewWrapper'

/* ─── Route guards ─── */
function ProtectedRoute({ children }) {
  const { user, isAdmin, loading } = useAuth()
  if (loading) return <PageSpinner />
  if (!user)    return <Navigate to="/" replace />
  if (isAdmin)  return <Navigate to="/admin" replace />
  return children
}

function AdminRoute({ children }) {
  const { user, isAdmin, loading } = useAuth()
  if (loading) return <PageSpinner />
  if (!user)   return <Navigate to="/" replace />
  if (!isAdmin) return <Navigate to="/dashboard" replace />
  return children
}

function PublicRoute({ children }) {
  const { user, isAdmin, loading } = useAuth()
  if (loading) return <PageSpinner />
  if (user)    return <Navigate to={isAdmin ? '/admin' : '/dashboard'} replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/"              element={<PublicRoute><LandingPage /></PublicRoute>} />
      <Route path="/auth/callback" element={<PublicRoute><LandingPage /></PublicRoute>} />

      {/* User */}
      <Route path="/dashboard"  element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/report"     element={<ProtectedRoute><ReportPage />   </ProtectedRoute>} />
      <Route path="/map"        element={<ProtectedRoute><MapPage />       </ProtectedRoute>} />
      <Route path="/nearby"     element={<ProtectedRoute><NearbyPage />   </ProtectedRoute>} />
      <Route path="/badges"     element={<ProtectedRoute><BadgesPage />   </ProtectedRoute>} />
      <Route path="/my-reports" element={<ProtectedRoute><MyReportsPage /></ProtectedRoute>} />

      {/* Admin */}
      <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />

      {/* Dev-only bypass — no auth required, remove before production */}
      <Route path="/admin-preview" element={<AdminPage />} />

      {/* ── Preview hub + all screen previews (dev-only) ──────────────── */}
      <Route path="/preview"              element={<PreviewPage />} />
      <Route path="/preview/landing"      element={<PreviewWrapper><LandingPage /></PreviewWrapper>} />
      <Route path="/preview/dashboard"    element={<PreviewWrapper><DashboardPage /></PreviewWrapper>} />
      <Route path="/preview/report"       element={<PreviewWrapper><ReportPage /></PreviewWrapper>} />
      <Route path="/preview/map"          element={<PreviewWrapper><MapPage /></PreviewWrapper>} />
      <Route path="/preview/nearby"       element={<PreviewWrapper><NearbyPage /></PreviewWrapper>} />
      <Route path="/preview/badges"       element={<PreviewWrapper><BadgesPage /></PreviewWrapper>} />
      <Route path="/preview/admin"        element={<PreviewWrapper forceAdmin><AdminPage /></PreviewWrapper>} />
      <Route path="/preview/ai-result"    element={<PreviewWrapper><AIResultPreviewPage /></PreviewWrapper>} />
      <Route path="/preview/letter"       element={<PreviewWrapper><LetterPreviewPage /></PreviewWrapper>} />
      {/* ──────────────────────────────────────────────────────────────── */}

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppProvider>
          <AppRoutes />
          <Toaster
            position="top-center"
            gutter={8}
            toastOptions={{
              duration: 3500,
              style: {
                background: '#fff',
                color: '#111',
                border: '0.5px solid rgba(0,0,0,0.1)',
                borderRadius: '10px',
                fontSize: '13px',
                fontWeight: '500',
                padding: '10px 14px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                fontFamily: 'Inter, sans-serif',
              },
              success: { iconTheme: { primary: '#1D9E75', secondary: '#fff' } },
              error:   { iconTheme: { primary: '#E24B4A', secondary: '#fff' } },
            }}
          />
        </AppProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
