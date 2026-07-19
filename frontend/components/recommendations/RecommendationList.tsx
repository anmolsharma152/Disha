"use client"

import type { CareerRecommendation } from "@/types/api"
import { RecommendationCard } from "./RecommendationCard"

function RecommendationList({
  recommendations: recs,
}: {
  recommendations: CareerRecommendation[]
}) {
  if (!recs?.length) return null

  // Skip error-only payloads from empty career agent
  const valid = recs.filter((r) => r && !("error" in r && r.error) && r.title)

  if (valid.length === 0) return null

  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">Career Recommendations</h2>
        <span className="text-xs text-muted-foreground">
          {valid.length} found
        </span>
      </div>
      <div className="space-y-2">
        {valid.map((rec, i) => (
          <RecommendationCard
            key={rec.job_id || `${rec.company}-${rec.title}-${i}`}
            recommendation={rec}
          />
        ))}
      </div>
    </section>
  )
}

export { RecommendationList }
