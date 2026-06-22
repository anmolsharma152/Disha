"use client"

import type { JobOpening } from "@/types/api"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const REMOTE_LABELS: Record<string, string> = {
  onsite: "On-site",
  hybrid: "Hybrid",
  remote: "Remote",
  remote_friendly: "Remote-Friendly",
}

const EXP_LABELS: Record<string, string> = {
  intern: "Intern",
  entry: "Entry",
  junior: "Junior",
  mid: "Mid",
  senior: "Senior",
  staff: "Staff",
  principal: "Principal",
  director: "Director",
  vp: "VP",
  c_level: "C-Level",
}

const EMP_TYPE_LABELS: Record<string, string> = {
  full_time: "Full-Time",
  part_time: "Part-Time",
  contract: "Contract",
  internship: "Internship",
  temp: "Temporary",
}

function formatLocation(job: JobOpening): string {
  if (job.location_city || job.location_state || job.location_country) {
    return [job.location_city, job.location_state, job.location_country]
      .filter(Boolean)
      .join(", ")
  }
  return job.location_raw || "Location not specified"
}

function formatCompensation(job: JobOpening): string | null {
  if (job.payout_min != null && job.payout_max != null) {
    if (job.currency === "INR") {
      return `₹${(job.payout_min / 100000).toFixed(1)}L – ₹${(job.payout_max / 100000).toFixed(1)}L`
    }
    return `$${Math.round(job.payout_min / 1000)}K – $${Math.round(job.payout_max / 1000)}K`
  }
  if (job.total_comp_estimate != null) {
    if (job.currency === "INR") {
      return `₹${(job.total_comp_estimate / 100000).toFixed(1)}L (est.)`
    }
    return `$${Math.round(job.total_comp_estimate / 1000)}K (est.)`
  }
  return null
}

function JobCard({ job }: { job: JobOpening }) {
  const comp = formatCompensation(job)
  const location = formatLocation(job)
  const hasTechStack = job.tech_stack.length > 0

  return (
    <Card size="sm">
      <CardHeader>
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {job.company_name}
        </div>
        <CardTitle>{job.title}</CardTitle>
        <div className="flex flex-wrap gap-1">
          <Badge variant="outline" className="text-[10px]">
            {REMOTE_LABELS[job.remote_policy] ?? job.remote_policy}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            {EXP_LABELS[job.experience_level] ?? job.experience_level}
          </Badge>
          <Badge variant="ghost" className="text-[10px]">
            {EMP_TYPE_LABELS[job.employment_type] ?? job.employment_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-1.5">
        <p className="text-xs text-muted-foreground">{location}</p>
        {comp && (
          <p className="text-xs font-medium text-foreground">{comp}</p>
        )}
        {hasTechStack && (
          <div className="flex flex-wrap gap-1">
            {job.tech_stack.slice(0, 5).map((tech) => (
              <span
                key={tech}
                className="inline-flex h-5 items-center rounded bg-muted px-1.5 text-[10px] font-medium text-muted-foreground"
              >
                {tech}
              </span>
            ))}
            {job.tech_stack.length > 5 && (
              <span className="inline-flex h-5 items-center text-[10px] text-muted-foreground">
                +{job.tech_stack.length - 5}
              </span>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="gap-2">
        {job.application_url ? (
          <a
            href={job.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-primary hover:underline"
          >
            Apply
          </a>
        ) : (
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-primary hover:underline"
          >
            View Job
          </a>
        )}
        <span className="text-[10px] text-muted-foreground">
          {job.source_domain}
        </span>
      </CardFooter>
    </Card>
  )
}

export { JobCard }
