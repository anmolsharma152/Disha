"use client"

import { useChat } from "@/hooks"
import { ChatInput } from "@/components/chat/ChatInput"
import { AgentStatus } from "@/components/chat/AgentStatus"
import { FinalAnswer } from "@/components/chat/FinalAnswer"

export default function Home() {
  const {
    sendMessage,
    loading,
    error,
    currentAgent,
    finalAnswer,
  } = useChat()

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Disha</h1>
        <p className="text-sm text-muted-foreground">
          Market Intelligence &amp; Career Optimization
        </p>
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

        <FinalAnswer answer={finalAnswer} />
      </main>

      <footer className="mt-8">
        <ChatInput onSend={sendMessage} disabled={loading} />
      </footer>
    </div>
  )
}
