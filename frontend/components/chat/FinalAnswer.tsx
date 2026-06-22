import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface FinalAnswerProps {
  answer: string | null
}

export function FinalAnswer({ answer }: FinalAnswerProps) {
  if (!answer) return null

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed text-foreground">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {answer}
      </ReactMarkdown>
    </div>
  )
}
