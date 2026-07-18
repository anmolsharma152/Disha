"use client"

import { Badge } from "@/components/ui/badge"

interface AgentStatusProps {
  currentAgent: string | null
  loading: boolean
  error: string | null
}

const AGENT_LABELS: Record<string, string> = {
  scraper: "Researching companies",
  financial_analyst: "Analyzing financials",
  career_strategy: "Matching career options",
  learning_companion: "Building learning path",
  synthesize: "Synthesizing results",
  error_recovery: "Recovering from error",
}

export function AgentStatus({ currentAgent, loading, error }: AgentStatusProps) {
  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-destructive">
        <span className="size-2 rounded-full bg-destructive" />
        <span>{error}</span>
      </div>
    )
  }

  if (!loading) return null

  const label = currentAgent
    ? AGENT_LABELS[currentAgent] ?? `Running ${currentAgent}`
    : "Initializing"

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="size-2 animate-pulse rounded-full bg-primary" />
      <span>{label}</span>
      {currentAgent && (
        <Badge variant="outline" className="text-[10px]">
          {currentAgent}
        </Badge>
      )}
    </div>
  )
}
