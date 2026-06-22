import type { StreamEvent } from "@/types/api"

export async function* parseSSEStream(
  response: Response
): AsyncGenerator<StreamEvent> {
  if (!response.body) {
    throw new Error("Response body is null — streaming not supported")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const parts = buffer.split("\n\n")
      buffer = parts.pop() ?? ""

      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (line.startsWith("data: ")) {
            const raw = line.slice(6).trim()
            let event: StreamEvent
            try {
              event = JSON.parse(raw)
            } catch (parseErr) {
              console.error("SSE JSON parse error:", parseErr, "raw:", raw)
              throw parseErr
            }
            if (event.error) {
              throw new Error(event.error)
            }
            yield event
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
