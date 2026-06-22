"use client"

import { useChat } from "@/hooks"
import { ChatInput } from "@/components/chat/ChatInput"
import { AgentStatus } from "@/components/chat/AgentStatus"
import { FinalAnswer } from "@/components/chat/FinalAnswer"
import { JobList } from "@/components/jobs"
import { RecommendationList } from "@/components/recommendations"
import { ThemeToggle } from "@/components/layout"
import { Separator } from "@/components/ui/separator"

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

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-4 py-6 sm:px-6 sm:py-8">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Disha</h1>
          <p className="text-sm text-muted-foreground">
            Market Intelligence &amp; Career Optimization
          </p>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 space-y-4">
        {!loading && !finalAnswer && !error && (
          <p className="text-sm text-muted-foreground">
            Ask about a company&apos;s market position, open roles, or career
            recommendations tailored to your profile.
          </p>
        )}

        <AgentStatus
          currentAgent={currentAgent}
          loading={loading}
          error={error}
        />

        <JobList jobs={jobOpenings} />

        {jobOpenings.length > 0 && careerRecommendations.length > 0 && (
          <Separator />
        )}

        <RecommendationList recommendations={careerRecommendations} />

        {(jobOpenings.length > 0 || careerRecommendations.length > 0) &&
          finalAnswer && <Separator />}

        <FinalAnswer answer={finalAnswer} />
      </main>

      <footer className="mt-8">
        <ChatInput onSend={sendMessage} disabled={loading} />
      </footer>
    </div>
  )
}
