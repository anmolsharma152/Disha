"use client"

import type { CareerRecommendation } from "@/types/api"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const PRIORITY_STYLES: Record<string, string> = {
  high: "border-l-2 border-l-amber-500",
  medium: "",
  low: "opacity-70",
}

const FIT_VARIANTS: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  good: "default",
  poor: "secondary",
  below: "destructive",
  unavailable: "outline",
}

function RecommendationCard({
  recommendation: rec,
}: {
  recommendation: CareerRecommendation
}) {
  const priorityClass = PRIORITY_STYLES[rec.priority] ?? ""

  return (
    <Card size="sm" className={priorityClass}>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {rec.company}
            </div>
            <CardTitle>{rec.title}</CardTitle>
          </div>
          <div className="shrink-0 text-right">
            <div className="text-lg font-bold leading-none tabular-nums">
              {Math.round(rec.match_score)}%
            </div>
            <div className="text-[10px] text-muted-foreground">match</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1">
          <Badge variant="outline" className="text-[10px]">
            {rec.remote_policy === "remote"
              ? "Remote"
              : rec.remote_policy === "hybrid"
                ? "Hybrid"
                : rec.remote_policy === "onsite"
                  ? "On-site"
                  : rec.remote_policy}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            Skills: {Math.round(rec.skill_match_pct)}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-muted-foreground">{rec.location}</p>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="space-y-0.5">
            <span className="text-muted-foreground">Compensation</span>
            <p className="font-medium">
              {rec.compensation.display_crores > 0
                ? `₹${rec.compensation.display_crores.toFixed(2)}Cr`
                : `₹${rec.compensation.display_lpa.toFixed(1)}L`}
            </p>
          </div>
          <div className="space-y-0.5 text-right">
            <span className="text-muted-foreground">Fit</span>
            <div>
              <Badge
                variant={FIT_VARIANTS[rec.compensation.fit] ?? "outline"}
                className="text-[10px]"
              >
                {rec.compensation.fit}
              </Badge>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-1 text-[10px]">
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
            {rec.experience_fit}
          </span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
            {rec.remote_fit}
          </span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
            {rec.visa_fit}
          </span>
        </div>

        {rec.matched_skills.length > 0 && (
          <div>
            <span className="text-[10px] font-medium text-muted-foreground">
              Matched skills
            </span>
            <div className="mt-0.5 flex flex-wrap gap-1">
              {rec.matched_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex h-5 items-center rounded bg-primary/10 px-1.5 text-[10px] font-medium text-primary"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {rec.missing_skills.length > 0 && (
          <div>
            <span className="text-[10px] font-medium text-muted-foreground">
              Missing skills
            </span>
            <div className="mt-0.5 flex flex-wrap gap-1">
              {rec.missing_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex h-5 items-center rounded bg-muted px-1.5 text-[10px] text-muted-foreground line-through"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {rec.reasoning && (
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            {rec.reasoning}
          </p>
        )}
      </CardContent>
      <CardFooter className="gap-2">
        {rec.application_url ? (
          <a
            href={rec.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-primary hover:underline"
          >
            Apply
          </a>
        ) : rec.source_url ? (
          <a
            href={rec.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-primary hover:underline"
          >
            View Details
          </a>
        ) : null}
      </CardFooter>
    </Card>
  )
}

export { RecommendationCard }
