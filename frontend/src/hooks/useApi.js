/**
 * useApi — custom React hook for API calls
 *
 * WHAT IT IS:
 *   A reusable hook that wraps fetch() calls to the API Gateway backend.
 *   It manages loading/error/data state so components don't have to.
 *
 * WHY IT EXISTS:
 *   Every component that needs data would otherwise repeat the same
 *   fetch → loading → error → data pattern. Putting it in one hook
 *   keeps components clean and focused on rendering.
 *
 * USAGE:
 *   const { data, loading, error } = useApi('/stats')
 */

import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || ''

export function useApi(path, options = {}) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const fetchData = useCallback(async () => {
    if (!API_BASE) {
      setError('API_URL not configured. Set VITE_API_URL in .env.local')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}${path}`, options)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `HTTP ${res.status}`)
      }
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [path])

  useEffect(() => { fetchData() }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

export async function uploadInvoice(file, onProgress) {
  if (!API_BASE) throw new Error('API_URL not configured')

  // Step 1: get presigned URL from our API
  const res = await fetch(`${API_BASE}/upload`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({
      filename:     file.name,
      content_type: file.type || 'application/pdf',
    }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || 'Failed to get upload URL')
  }
  const { upload_url } = await res.json()

  // Step 2: upload directly to S3 using the presigned URL
  onProgress?.('uploading')
  const uploadRes = await fetch(upload_url, {
    method:  'PUT',
    headers: { 'Content-Type': file.type || 'application/pdf' },
    body:    file,
  })
  if (!uploadRes.ok) throw new Error('S3 upload failed')

  onProgress?.('processing')
  return true
}
