"use client"

import { useRef } from "react"
import type { ProfileMemory } from "@/hooks/useProfile"
import { Button } from "@/components/ui/button"

interface ResumePanelProps {
  memory: ProfileMemory | null
  loading: boolean
  uploading: boolean
  error: string | null
  onUpload: (file: File) => Promise<unknown>
  onClear: () => Promise<void>
}

export function ResumePanel({
  memory,
  loading,
  uploading,
  error,
  onUpload,
  onClear,
}: ResumePanelProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const profile = memory?.profile
  const skills = profile?.skills ?? []
  const roles = profile?.target_roles ?? []
  const cities = profile?.target_cities ?? []

  async function handleFile(file: File | undefined) {
    if (!file) return
    await onUpload(file)
    if (inputRef.current) inputRef.current.value = ""
  }

  return (
    <section className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h2 className="text-sm font-semibold tracking-tight">Your resume</h2>
          <p className="text-xs text-muted-foreground">
            Upload once — skills and roles ground matching for this user.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.md,application/pdf,text/plain"
            className="hidden"
            onChange={(e) => void handleFile(e.target.files?.[0])}
          />
          <Button
            type="button"
            size="sm"
            disabled={uploading || loading}
            onClick={() => inputRef.current?.click()}
          >
            {uploading ? "Reading…" : memory?.has_profile ? "Replace resume" : "Upload resume"}
          </Button>
          {memory?.has_profile && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={uploading}
              onClick={() => void onClear()}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {error && (
        <p className="mt-3 text-xs text-destructive">{error}</p>
      )}

      {loading && !memory && (
        <p className="mt-3 text-xs text-muted-foreground">Loading profile…</p>
      )}

      {memory?.has_profile ? (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs">
            {profile?.display_name && (
              <span className="font-medium text-foreground">
                {profile.display_name}
              </span>
            )}
            {typeof profile?.experience_years === "number" && (
              <span className="text-muted-foreground">
                ~{profile.experience_years} yrs experience
              </span>
            )}
            {memory.resume?.filename && (
              <span className="text-muted-foreground">
                {memory.resume.filename}
                {memory.resume.extraction_method
                  ? ` · ${memory.resume.extraction_method}`
                  : ""}
              </span>
            )}
          </div>

          {profile?.summary && (
            <p className="text-xs leading-relaxed text-muted-foreground">
              {profile.summary}
            </p>
          )}

          {skills.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-medium text-muted-foreground">
                Skills ({skills.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {skills.slice(0, 24).map((s) => (
                  <span
                    key={s}
                    className="rounded-md bg-muted px-2 py-0.5 text-[11px] text-foreground"
                  >
                    {s}
                  </span>
                ))}
                {skills.length > 24 && (
                  <span className="text-[11px] text-muted-foreground">
                    +{skills.length - 24} more
                  </span>
                )}
              </div>
            </div>
          )}

          {(roles.length > 0 || cities.length > 0) && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
              {roles.length > 0 && (
                <span>
                  <span className="font-medium text-foreground/80">Roles: </span>
                  {roles.slice(0, 4).join(", ")}
                </span>
              )}
              {cities.length > 0 && (
                <span>
                  <span className="font-medium text-foreground/80">Cities: </span>
                  {cities.slice(0, 6).join(", ")}
                </span>
              )}
            </div>
          )}
        </div>
      ) : (
        !loading && (
          <p className="mt-3 text-xs text-muted-foreground">
            No resume yet. Upload a PDF so search and rankings use your real
            skills instead of empty defaults.
          </p>
        )
      )}
    </section>
  )
}
