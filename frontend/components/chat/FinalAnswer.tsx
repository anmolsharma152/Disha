interface FinalAnswerProps {
  answer: string | null
}

export function FinalAnswer({ answer }: FinalAnswerProps) {
  if (!answer) return null

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm leading-relaxed text-foreground">
      {answer}
    </div>
  )
}
