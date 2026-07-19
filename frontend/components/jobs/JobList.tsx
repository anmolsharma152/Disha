"use client"

import type { JobOpening } from "@/types/api"
import { JobCard } from "./JobCard"

function JobList({ jobs }: { jobs: JobOpening[] }) {
  if (!jobs?.length) return null

  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">Open Positions</h2>
        <span className="text-xs text-muted-foreground">
          {jobs.length} found
        </span>
      </div>
      <div className="space-y-2">
        {jobs.map((job, i) => (
          <JobCard
            key={job.job_id || job.source_url || `job-${i}`}
            job={job}
          />
        ))}
      </div>
    </section>
  )
}

export { JobList }
