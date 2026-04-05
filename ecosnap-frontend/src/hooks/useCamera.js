import { useState, useCallback } from 'react'
import { supabase } from '../lib/supabaseClient'
import toast from 'react-hot-toast'

const BASE = import.meta.env.VITE_API_URL 

/** Get current Supabase session JWT */
async function getToken() {
  const { data } = await supabase.auth.getSession()
  return data?.session?.access_token ?? null
}

export function useCamera() {
  const [photo,     setPhoto]     = useState(null) // { file, preview, url }
  const [uploading, setUploading] = useState(false)

  const capture = useCallback((file) => {
    if (!file) return
    const preview = URL.createObjectURL(file)
    setPhoto({ file, preview, url: null })
  }, [])

  const retake = useCallback(() => {
    if (photo?.preview) URL.revokeObjectURL(photo.preview)
    setPhoto(null)
  }, [photo])

  /**
   * Upload via the backend POST /api/upload — uses service key, bypasses RLS.
   * Falls back to local preview URL if backend upload fails.
   */
  const upload = useCallback(async () => {
    if (!photo?.file) throw new Error('No photo')
    setUploading(true)
    try {
      const token = await getToken()
      const fd = new FormData()
      fd.append('file', photo.file)

      const res = await fetch(`${BASE}/api/upload`, {
        method: 'POST',
        body: fd,
        // Don't set Content-Type — browser sets it with the correct multipart boundary
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
        console.error('Backend upload error:', err)
        toast('Using local photo (upload unavailable)', { icon: '⚠️' })
        return photo.preview
      }

      const data = await res.json()
      const publicUrl = data.public_url
      setPhoto(p => ({ ...p, url: publicUrl }))
      return publicUrl
    } catch (e) {
      console.error('Photo upload error:', e)
      toast('Using local photo', { icon: '⚠️' })
      return photo.preview
    } finally {
      setUploading(false)
    }
  }, [photo])

  const cleanup = useCallback(() => {
    if (photo?.preview) URL.revokeObjectURL(photo.preview)
    setPhoto(null)
  }, [photo])

  return { photo, uploading, capture, retake, upload, cleanup }
}
