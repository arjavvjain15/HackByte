import { useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { upvoteReport, removeUpvote, notifyEscalation } from '../services/api'
import toast from 'react-hot-toast'

const ESCALATION_THRESHOLD = 5

export function useUpvote() {
  const { user } = useAuth()
  const { upvoted, toggleUpvote, patchReportCount, reports, nearbyReports, myReports } = useApp()

  const vote = useCallback(async (id) => {
    if (!user) { toast.error('Sign in to upvote'); return }
    const wasVoted = upvoted.has(id)
    // Optimistic UI update
    toggleUpvote(id)
    patchReportCount(id, wasVoted ? -1 : 1)

    try {
      await (wasVoted ? removeUpvote(id) : upvoteReport(id))

      // ── Auto-escalation (Task 5) ──────────────────────────────────────
      // After a successful upvote (not removal), check if the report has crossed
      // the escalation threshold. If so, fire the escalation notification.
      if (!wasVoted) {
        // Find the report in any of the in-memory lists
        const allLists = [...reports, ...nearbyReports, ...myReports]
        const report = allLists.find(r => r.id === id)
        const newCount = (report?.upvotes || 0) + 1 // +1 because patchReportCount was optimistic

        if (report && newCount > ESCALATION_THRESHOLD && report.status !== 'escalated' && report.status !== 'resolved') {
          try {
            await notifyEscalation({
              report_id:   id,
              hazard_type: report.hazard_type || 'unknown',
              severity:    report.severity    || 'medium',
              location:    report.lat && report.lng
                ? `${report.lat.toFixed(5)}, ${report.lng.toFixed(5)}`
                : report.department || 'Unknown location',
            })
            toast('⚡ Report escalated — authorities notified!', { icon:'🚨', duration:4000 })
          } catch (escalateErr) {
            // Non-fatal: escalation notification failed but upvote succeeded
            console.warn('[useUpvote] escalation notify failed:', escalateErr.message)
          }
        }
      }
    } catch {
      // Revert optimistic update on error
      toggleUpvote(id)
      patchReportCount(id, wasVoted ? 1 : -1)
      toast.error('Vote failed, You have already upvoted')
    }
  }, [user, upvoted, toggleUpvote, patchReportCount, reports, nearbyReports, myReports])

  return { vote, upvoted }
}
