"use client"

import type { CareerRecommendation } from "@/types/api"
import { RecommendationCard } from "./RecommendationCard"

function RecommendationList({
  recommendations: recs,
}: {
  recommendations: CareerRecommendation[]
}) {
  if (recs.length === 0) return null

  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">Career Recommendations</h2>
        <span className="text-xs text-muted-foreground">
          {recs.length} found
        </span>
      </div>
      <div className="space-y-2">
        {recs.map((rec) => (
          <RecommendationCard
            key={rec.job_id}
            recommendation={rec}
          />
        ))}
      </div>
    </section>
  )
}

export { RecommendationList }
