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
    <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b bg-muted/30 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">Summary</h2>
          <p className="text-[11px] text-muted-foreground">
            Overview of this search
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 shrink-0"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Collapse" : "Expand"}
        </Button>
      </div>

      {open && (
        <div className="max-h-[min(70vh,36rem)] overflow-y-auto px-4 py-4">
          <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:mb-2 prose-headings:mt-4 prose-headings:first:mt-0 prose-headings:text-sm prose-p:my-2 prose-p:text-xs prose-li:my-0.5 prose-li:text-xs prose-ul:my-2">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
          </div>
        </div>
      )}
    </section>
  )
}
