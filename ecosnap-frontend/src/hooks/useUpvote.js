import { useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { useApp } from '../context/useApp'
import { upvoteReport, removeUpvote } from '../services/api'
import toast from 'react-hot-toast'

export function useUpvote() {
  const { user } = useAuth()
  const { upvoted, toggleUpvote, patchReportCount } = useApp()

  const vote = useCallback(async (id) => {
    if (!user) { toast.error('Sign in to upvote'); return }
    const wasVoted = upvoted.has(id)
    toggleUpvote(id)
    patchReportCount(id, wasVoted ? -1 : 1)
    try {
      await (wasVoted ? removeUpvote(id) : upvoteReport(id))
    } catch {
      // revert
      toggleUpvote(id)
      patchReportCount(id, wasVoted ? 1 : -1)
      toast.error('Vote failed, try again')
    }
  }, [user, upvoted, toggleUpvote, patchReportCount])

  return { vote, upvoted }
}
