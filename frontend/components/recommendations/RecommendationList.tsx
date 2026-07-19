"use client"

import { useState } from "react"
import type { CareerRecommendation } from "@/types/api"
import { RecommendationCard } from "./RecommendationCard"
import { Button } from "@/components/ui/button"

const PREVIEW = 5

function RecommendationList({
  recommendations: recs,
}: {
  recommendations: CareerRecommendation[]
}) {
  const [expanded, setExpanded] = useState(false)

  if (!recs?.length) return null

  const valid = recs.filter(
    (r) => r && typeof r === "object" && !("error" in r && r.error) && r.title
  )
  if (valid.length === 0) return null

  const visible = expanded ? valid : valid.slice(0, PREVIEW)
  const hidden = valid.length - visible.length

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight">
            Top matches
          </h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Ranked for this query
            {valid.length > PREVIEW
              ? ` · showing ${visible.length} of ${valid.length}`
              : ` · ${valid.length} role${valid.length === 1 ? "" : "s"}`}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {visible.map((rec, i) => (
          <RecommendationCard
            key={rec.job_id || `${rec.company}-${rec.title}-${i}`}
            recommendation={rec}
            rank={i + 1}
          />
        ))}
      </div>

      {hidden > 0 && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => setExpanded(true)}
        >
          Show {hidden} more match{hidden === 1 ? "" : "es"}
        </Button>
      )}
      {expanded && valid.length > PREVIEW && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={() => setExpanded(false)}
        >
          Show fewer
        </Button>
      )}
    </section>
  )
}

export { RecommendationList }
