"use client"

import { useState } from "react"
import type { CareerRecommendation } from "@/types/api"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

function locationLine(rec: CareerRecommendation): string | null {
  if (
    rec.location &&
    rec.location !== "None, None" &&
    rec.location !== "None"
  ) {
    return rec.location
  }
  return null
}

function compLine(rec: CareerRecommendation): string | null {
  const c = rec.compensation
  if (!c) return null
  if (typeof c.display_lpa === "number" && c.display_lpa > 0) {
    return `₹${c.display_lpa.toFixed(1)} LPA`
  }
  if (typeof c.display_crores === "number" && c.display_crores > 0) {
    return `₹${c.display_crores.toFixed(2)} Cr`
  }
  return null
}

function scoreTone(score: number): string {
  if (score >= 70) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 50) return "text-amber-600 dark:text-amber-400"
  return "text-muted-foreground"
}

function RecommendationCard({
  recommendation: rec,
  rank,
}: {
  recommendation: CareerRecommendation
  rank?: number
}) {
  const [open, setOpen] = useState(false)
  const score =
    typeof rec.match_score === "number" && Number.isFinite(rec.match_score)
      ? Math.round(rec.match_score)
      : 0
  const loc = locationLine(rec)
  const comp = compLine(rec)
  const matched = rec.matched_skills ?? []
  const missing = rec.missing_skills ?? []
  const link = rec.application_url || rec.source_url || null
  const remote =
    rec.remote_policy && rec.remote_policy !== "unknown"
      ? rec.remote_policy.replace(/_/g, " ")
      : null

  const meta = [loc, remote, comp].filter(Boolean).join(" · ")

  return (
    <article
      className={cn(
        "flex h-full flex-col rounded-xl border bg-card p-4 shadow-sm transition-colors",
        "hover:border-foreground/20"
      )}
    >
      <div className="flex items-start gap-3">
        {typeof rank === "number" && (
          <span className="mt-0.5 w-6 shrink-0 text-center text-xs font-medium tabular-nums text-muted-foreground">
            {rank}
          </span>
        )}
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-medium text-muted-foreground">
                {rec.company || "Company"}
              </p>
              <h3 className="text-sm font-semibold leading-snug tracking-tight">
                {rec.title || "Untitled role"}
              </h3>
            </div>
            <div className="shrink-0 text-right">
              <p
                className={cn(
                  "text-base font-semibold tabular-nums leading-none",
                  scoreTone(score)
                )}
              >
                {score}
              </p>
              <p className="mt-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                score
              </p>
            </div>
          </div>

          {meta && (
            <p className="text-xs text-muted-foreground capitalize">{meta}</p>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1">
            {link && (
              <a
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium text-primary hover:underline"
              >
                {rec.application_url ? "Apply →" : "View posting →"}
              </a>
            )}
            {(rec.reasoning || matched.length > 0 || missing.length > 0) && (
              <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                {open ? "Hide details" : "Why this match?"}
              </button>
            )}
          </div>

          {open && (
            <div className="mt-3 space-y-2 border-t pt-3">
              {rec.reasoning && (
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {rec.reasoning}
                </p>
              )}
              {matched.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {matched.slice(0, 8).map((s) => (
                    <Badge key={s} variant="secondary" className="text-[10px]">
                      {s}
                    </Badge>
                  ))}
                </div>
              )}
              {missing.length > 0 && (
                <p className="text-[11px] text-muted-foreground">
                  Gaps: {missing.slice(0, 5).join(", ")}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

export { RecommendationCard }
