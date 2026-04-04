import { useState, useCallback } from 'react'
import { supabase } from '../lib/supabaseClient'
import { SUPABASE_BUCKET } from '../utils/helpers'
import toast from 'react-hot-toast'

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

  const upload = useCallback(async (uid = 'anon') => {
    if (!photo?.file) throw new Error('No photo')
    setUploading(true)
    try {
      const ext  = photo.file.name.split('.').pop() || 'jpg'
      const path = `${uid}/${Date.now()}.${ext}`
      const { error } = await supabase.storage.from(SUPABASE_BUCKET).upload(path, photo.file)
      if (error) throw error
      const { data } = supabase.storage.from(SUPABASE_BUCKET).getPublicUrl(path)
      setPhoto(p => ({ ...p, url: data.publicUrl }))
      return data.publicUrl
    } catch (e) {
      toast.error('Photo upload failed')
      throw e
    } finally { setUploading(false) }
  }, [photo])

  const cleanup = useCallback(() => {
    if (photo?.preview) URL.revokeObjectURL(photo.preview)
    setPhoto(null)
  }, [photo])

  return { photo, uploading, capture, retake, upload, cleanup }
}
