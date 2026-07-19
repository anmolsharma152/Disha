"use client"

interface AgentStatusProps {
  currentAgent: string | null
  loading: boolean
  error: string | null
}

const AGENT_LABELS: Record<string, string> = {
  scraper: "Finding open roles…",
  financial_analyst: "Reviewing company signals…",
  career_strategy: "Ranking matches…",
  learning_companion: "Building learning ideas…",
  synthesize: "Writing summary…",
  guardrail: "Filtering results…",
  error_recovery: "Retrying with a broader search…",
  supervisor: "Planning next step…",
}

export function AgentStatus({ currentAgent, loading, error }: AgentStatusProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
        <p className="font-medium">Something went wrong</p>
        <p className="mt-1 text-xs opacity-90">{error}</p>
      </div>
    )
  }

  if (!loading) return null

  const label = currentAgent
    ? AGENT_LABELS[currentAgent] ?? `Working (${currentAgent})…`
    : "Starting search…"

  return (
    <div className="flex items-center gap-3 rounded-xl border bg-muted/40 px-4 py-3">
      <span className="relative flex size-2.5">
        <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-40" />
        <span className="relative inline-flex size-2.5 rounded-full bg-primary" />
      </span>
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  )
}
