"use client"

import { useChat } from "@/hooks"
import { useProfile } from "@/hooks/useProfile"
import { ChatInput } from "@/components/chat/ChatInput"
import { AgentStatus } from "@/components/chat/AgentStatus"
import { FinalAnswer } from "@/components/chat/FinalAnswer"
import { JobList } from "@/components/jobs"
import { RecommendationList } from "@/components/recommendations"
import { ResumePanel } from "@/components/profile/ResumePanel"
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

  const {
    memory,
    loading: profileLoading,
    uploading,
    error: profileError,
    uploadResume,
    clearProfile,
  } = useProfile("default")

  const hasResults =
    jobOpenings.length > 0 ||
    careerRecommendations.length > 0 ||
    !!finalAnswer

  const hasRecs = careerRecommendations.some(
    (r) => r && typeof r === "object" && "title" in r && r.title
  )

  const showDashboard = hasRecs || !!finalAnswer || jobOpenings.length > 0
  const hasMemory = !!memory?.has_profile

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 pb-32 pt-6 sm:px-6 sm:pt-8 lg:px-8">
      <header className="mb-6 flex items-start justify-between gap-4 lg:mb-8">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
            Disha
          </h1>
          <p className="text-sm text-muted-foreground">
            Resume-grounded search and ranked matches
            {hasMemory && memory?.skill_count
              ? ` · ${memory.skill_count} skills in memory`
              : ""}
          </p>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex flex-1 flex-col gap-6">
        <ResumePanel
          memory={memory}
          loading={profileLoading}
          uploading={uploading}
          error={profileError}
          onUpload={uploadResume}
          onClear={clearProfile}
        />

        {!loading && !hasResults && !error && (
          <div className="rounded-xl border border-dashed bg-muted/20 px-5 py-8 text-center">
            <p className="text-sm font-medium">
              {hasMemory
                ? "Search with your resume memory"
                : "Upload a resume, then search"}
            </p>
            <p className="mx-auto mt-1.5 max-w-md text-xs leading-relaxed text-muted-foreground">
              {hasMemory
                ? "Queries use your stored skills and target roles to rank openings. Try a company like PhonePe."
                : "Without a resume, matching stays neutral. Upload a PDF so recommendations reflect real skills."}
            </p>
          </div>
        )}

        <AgentStatus
          currentAgent={currentAgent}
          loading={loading}
          error={error}
        />

        {showDashboard && (
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12 lg:gap-8">
            <div className="min-w-0 space-y-6 lg:col-span-7 xl:col-span-8">
              {hasRecs ? (
                <RecommendationList recommendations={careerRecommendations} />
              ) : jobOpenings.length > 0 ? (
                <JobList jobs={jobOpenings} defaultOpen />
              ) : null}

              {hasRecs && jobOpenings.length > 0 && (
                <JobList jobs={jobOpenings} defaultOpen={false} />
              )}
            </div>

            <aside className="min-w-0 space-y-4 lg:col-span-5 xl:col-span-4 lg:sticky lg:top-6 lg:self-start">
              {finalAnswer ? (
                <FinalAnswer answer={finalAnswer} />
              ) : loading ? (
                <div className="rounded-xl border bg-muted/20 px-4 py-5 text-sm text-muted-foreground">
                  Summary will appear here when the search finishes.
                </div>
              ) : hasRecs ? (
                <div className="rounded-xl border bg-muted/20 px-4 py-5 text-sm text-muted-foreground">
                  Ranked matches are ready. Summary is still generating…
                </div>
              ) : null}
            </aside>
          </div>
        )}
      </main>

      <footer className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto max-w-6xl px-4 py-3 sm:px-6 sm:py-4 lg:px-8">
          <ChatInput onSend={sendMessage} disabled={loading || uploading} />
        </div>
      </footer>
    </div>
  )
}
