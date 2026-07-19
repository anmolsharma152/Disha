"use client"

import { useState } from "react"
import type { JobOpening } from "@/types/api"
import { JobCard } from "./JobCard"
import { Button } from "@/components/ui/button"

const PREVIEW = 6

/**
 * Secondary list of raw openings. Collapsed by default when many roles,
 * so ranked matches stay the primary focus.
 */
function JobList({
  jobs,
  defaultOpen = false,
}: {
  jobs: JobOpening[]
  defaultOpen?: boolean
}) {
  const [sectionOpen, setSectionOpen] = useState(defaultOpen)
  const [showAll, setShowAll] = useState(false)

  if (!jobs?.length) return null

  const visible = showAll ? jobs : jobs.slice(0, PREVIEW)
  const hidden = jobs.length - visible.length

  return (
    <section className="space-y-3">
      <button
        type="button"
        onClick={() => setSectionOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-lg border bg-muted/30 px-3.5 py-3 text-left transition-colors hover:bg-muted/50"
      >
        <div>
          <h2 className="text-sm font-semibold tracking-tight">
            All openings found
          </h2>
          <p className="text-xs text-muted-foreground">
            {jobs.length} role{jobs.length === 1 ? "" : "s"} from this search
            {!sectionOpen ? " · tap to browse" : ""}
          </p>
        </div>
        <span className="text-xs text-muted-foreground">
          {sectionOpen ? "Hide" : "Show"}
        </span>
      </button>

      {sectionOpen && (
        <div className="space-y-3 pl-0.5">
          <div className="flex flex-col gap-2">
            {visible.map((job, i) => (
              <JobCard
                key={job.job_id || job.source_url || `job-${i}`}
                job={job}
              />
            ))}
          </div>
          {hidden > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setShowAll(true)}
            >
              Show {hidden} more
            </Button>
          )}
          {showAll && jobs.length > PREVIEW && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={() => setShowAll(false)}
            >
              Show fewer
            </Button>
          )}
        </div>
      )}
    </section>
  )
}

export { JobList }
