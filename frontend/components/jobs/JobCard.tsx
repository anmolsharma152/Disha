"use client"

import type { JobOpening } from "@/types/api"

function formatLocation(job: JobOpening): string | null {
  if (job.location_city || job.location_state || job.location_country) {
    return [job.location_city, job.location_state, job.location_country]
      .filter(Boolean)
      .join(", ")
  }
  return job.location_raw || null
}

function JobCard({ job }: { job: JobOpening }) {
  const location = formatLocation(job)
  const linkHref = job.application_url || job.source_url || null
  const remote =
    job.remote_policy && job.remote_policy !== "unknown"
      ? String(job.remote_policy).replace(/_/g, " ")
      : null
  const meta = [location, remote].filter(Boolean).join(" · ")

  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border bg-card/50 px-3.5 py-3">
      <div className="min-w-0 space-y-0.5">
        <p className="text-[11px] font-medium text-muted-foreground">
          {job.company_name || "Company"}
        </p>
        <p className="truncate text-sm font-medium leading-snug">
          {job.title || "Untitled role"}
        </p>
        {meta && (
          <p className="text-xs capitalize text-muted-foreground">{meta}</p>
        )}
      </div>
      {linkHref && (
        <a
          href={linkHref}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-xs font-medium text-primary hover:underline"
        >
          Open
        </a>
      )}
    </div>
  )
}

export { JobCard }
