"use client"

import type { JobOpening } from "@/types/api"
import { ScrollArea } from "@/components/ui/scroll-area"
import { JobCard } from "./JobCard"

function JobList({ jobs }: { jobs: JobOpening[] }) {
  if (jobs.length === 0) return null

  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">Open Positions</h2>
        <span className="text-xs text-muted-foreground">
          {jobs.length} found
        </span>
      </div>
      <ScrollArea className="max-h-[32rem] pr-3">
        <div className="space-y-2">
          {jobs.map((job) => (
            <JobCard key={job.job_id} job={job} />
          ))}
        </div>
      </ScrollArea>
    </section>
  )
}

export { JobList }
