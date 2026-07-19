"use client"

import { useCallback, useEffect, useState } from "react"
import { API_ENDPOINTS } from "@/lib/api"
import type { UserPreferences } from "@/types/api"

export interface ResumeMeta {
  filename?: string
  uploaded_at?: string
  char_count?: number
  extraction_method?: string
  text_preview?: string
}

export interface ProfileMemory {
  user_id: string
  has_profile: boolean
  profile: UserPreferences & {
    education?: string | null
    summary?: string | null
  }
  resume: ResumeMeta | null
  source?: string | null
  updated_at?: string | null
  skill_count: number
}

export function useProfile(userId = "default") {
  const [memory, setMemory] = useState<ProfileMemory | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch(
        `${API_ENDPOINTS.PROFILE}?user_id=${encodeURIComponent(userId)}`
      )
      if (!res.ok) throw new Error(`Failed to load profile (${res.status})`)
      const data = (await res.json()) as ProfileMemory
      setMemory(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const uploadResume = useCallback(
    async (file: File) => {
      setUploading(true)
      setError(null)
      try {
        const body = new FormData()
        body.append("file", file)
        const res = await fetch(
          `${API_ENDPOINTS.PROFILE_RESUME}?user_id=${encodeURIComponent(userId)}`,
          { method: "POST", body }
        )
        if (!res.ok) {
          let detail = res.statusText
          try {
            const j = await res.json()
            detail = j.detail || detail
          } catch {
            /* ignore */
          }
          throw new Error(detail)
        }
        const data = await res.json()
        setMemory(data.memory as ProfileMemory)
        return data as { ok: boolean; extraction_method: string; memory: ProfileMemory }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(msg)
        throw e
      } finally {
        setUploading(false)
      }
    },
    [userId]
  )

  const clearProfile = useCallback(async () => {
    setError(null)
    const res = await fetch(
      `${API_ENDPOINTS.PROFILE}?user_id=${encodeURIComponent(userId)}`,
      { method: "DELETE" }
    )
    if (!res.ok) throw new Error("Failed to clear profile")
    await refresh()
  }, [userId, refresh])

  return {
    memory,
    loading,
    uploading,
    error,
    refresh,
    uploadResume,
    clearProfile,
  }
}
