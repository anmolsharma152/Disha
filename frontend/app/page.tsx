"use client"

import { useChat } from "@/hooks"
import { ChatInput } from "@/components/chat/ChatInput"
import { AgentStatus } from "@/components/chat/AgentStatus"
import { FinalAnswer } from "@/components/chat/FinalAnswer"
import { JobList } from "@/components/jobs"
import { RecommendationList } from "@/components/recommendations"
import { ThemeToggle } from "@/components/layout"

export default function Home() {
  const {
    sendMessage,
    loading,
    error,
    currentAgent,
    finalAnswer,
    jobOpenings,
    careerRecommendations,
  } = useChat()

  const hasResults =
    jobOpenings.length > 0 ||
    careerRecommendations.length > 0 ||
    !!finalAnswer

  const hasRecs = careerRecommendations.some(
    (r) => r && typeof r === "object" && "title" in r && r.title
  )

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 pb-28 pt-6 sm:px-6 sm:pt-8">
      <header className="mb-8 flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
            Disha
          </h1>
          <p className="text-sm text-muted-foreground">
            Find roles, rank matches, get a short summary
          </p>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex flex-1 flex-col gap-8">
        {!loading && !hasResults && !error && (
          <div className="rounded-xl border border-dashed bg-muted/20 px-5 py-8 text-center">
            <p className="text-sm font-medium">Start with a company or role</p>
            <p className="mx-auto mt-1.5 max-w-sm text-xs leading-relaxed text-muted-foreground">
              Try a specific company first (e.g. PhonePe). You&apos;ll see ranked
              matches, then a summary — not a wall of raw cards.
            </p>
          </div>
        )}

        <AgentStatus
          currentAgent={currentAgent}
          loading={loading}
          error={error}
        />

        {/* Ranked matches first — the primary decision surface */}
        {hasRecs && (
          <RecommendationList recommendations={careerRecommendations} />
        )}

        {/* Summary after ranking is available */}
        {finalAnswer && <FinalAnswer answer={finalAnswer} />}

        {/* Raw openings secondary + collapsed by default when we have recs */}
        {jobOpenings.length > 0 && (
          <JobList jobs={jobOpenings} defaultOpen={!hasRecs} />
        )}
      </main>

      <footer className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto max-w-2xl px-4 py-3 sm:px-6 sm:py-4">
          <ChatInput onSend={sendMessage} disabled={loading} />
        </div>
      </footer>
    </div>
  )
}
