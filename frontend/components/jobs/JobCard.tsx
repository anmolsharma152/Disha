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

function formatLocation(job: JobOpening): string | null {
  if (job.location_city || job.location_state || job.location_country) {
    return [job.location_city, job.location_state, job.location_country]
      .filter(Boolean)
      .join(", ")
  }
  return job.location_raw || null
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
  const techStack = job.tech_stack ?? []
  const remotePolicy = job.remote_policy ?? "unknown"
  const expLevel = job.experience_level ?? "unknown"
  const empType = job.employment_type ?? "full_time"

  const badges: React.ReactNode[] = []
  const remoteLabel = REMOTE_LABELS[remotePolicy]
  if (remoteLabel) {
    badges.push(
      <Badge key="remote" variant="outline" className="text-[10px]">
        {remoteLabel}
      </Badge>
    )
  }
  const expLabel = EXP_LABELS[expLevel]
  if (expLabel) {
    badges.push(
      <Badge key="exp" variant="secondary" className="text-[10px]">
        {expLabel}
      </Badge>
    )
  }
  const empLabel = EMP_TYPE_LABELS[empType]
  if (empLabel) {
    badges.push(
      <Badge key="emp" variant="ghost" className="text-[10px]">
        {empLabel}
      </Badge>
    )
  }

  const linkHref = job.application_url || job.source_url || null

  return (
    <Card size="sm">
      <CardHeader>
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {job.company_name || "Company"}
        </div>
        <CardTitle>{job.title || "Untitled role"}</CardTitle>
        {badges.length > 0 && (
          <div className="flex flex-wrap gap-1">{badges}</div>
        )}
      </CardHeader>
      <CardContent className="space-y-1.5">
        {location && (
          <p className="text-xs text-muted-foreground">{location}</p>
        )}
        {comp && (
          <p className="text-xs font-medium text-foreground">{comp}</p>
        )}
        {techStack.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {techStack.slice(0, 5).map((tech) => (
              <span
                key={tech}
                className="inline-flex h-5 items-center rounded bg-muted px-1.5 text-[10px] font-medium text-muted-foreground"
              >
                {tech}
              </span>
            ))}
            {techStack.length > 5 && (
              <span className="inline-flex h-5 items-center text-[10px] text-muted-foreground">
                +{techStack.length - 5}
              </span>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="gap-2">
        {linkHref ? (
          <a
            href={linkHref}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-primary hover:underline"
          >
            {job.application_url ? "Apply" : "View Job"}
          </a>
        ) : null}
        {job.source_domain ? (
          <span className="text-[10px] text-muted-foreground">
            {job.source_domain}
          </span>
        ) : null}
      </CardFooter>
    </Card>
  )
}

export { JobCard }
