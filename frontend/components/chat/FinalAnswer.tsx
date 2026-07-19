"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Button } from "@/components/ui/button"

interface FinalAnswerProps {
  answer: string | null
}

export function FinalAnswer({ answer }: FinalAnswerProps) {
  const [open, setOpen] = useState(true)

  if (!answer) return null

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight">Summary</h2>
          <p className="text-xs text-muted-foreground">
            Narrative overview of this search
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Collapse" : "Expand"}
        </Button>
      </div>

      {open && (
        <div className="rounded-xl border bg-muted/20 px-4 py-4 sm:px-5 sm:py-5">
          <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:mb-2 prose-headings:mt-4 prose-headings:text-base prose-p:my-2 prose-li:my-0.5 prose-ul:my-2">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
          </div>
        </div>
      )}
    </section>
  )
}
