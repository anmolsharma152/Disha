"use client"

import { useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface ChatInputProps {
  onSend: (query: string) => void
  disabled?: boolean
}

const SUGGESTIONS = [
  "Software engineer roles at PhonePe",
  "Agentic AI roles in Bangalore",
  "ML engineer roles at Anthropic",
]

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput("")
  }

  return (
    <div className="space-y-3">
      {!disabled && !input && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSend(s)}
              className="rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex w-full gap-2">
        <Input
          type="text"
          placeholder="e.g. Backend roles at PhonePe in Bangalore"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
          className="flex-1"
        />
        <Button type="submit" disabled={disabled || !input.trim()}>
          {disabled ? "Working…" : "Search"}
        </Button>
      </form>
    </div>
  )
}
