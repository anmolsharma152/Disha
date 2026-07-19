"use client"

import { useState, useCallback, useRef, useEffect } from "react"

import type { JobOpening, CareerRecommendation } from "@/types/api"
import { API_ENDPOINTS, DEFAULT_HEADERS } from "@/lib/api"
import { parseSSEStream } from "@/lib/sse"

export interface UseChatReturn {
  sendMessage: (query: string) => Promise<void>
  loading: boolean
  error: string | null
  currentAgent: string | null
  routingKey: string | null
  jobOpenings: JobOpening[]
  careerRecommendations: CareerRecommendation[]
  finalAnswer: string | null
}

export function useChat(): UseChatReturn {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [routingKey, setRoutingKey] = useState<string | null>(null)
  const [jobOpenings, setJobOpenings] = useState<JobOpening[]>([])
  const [careerRecommendations, setCareerRecommendations] = useState<
    CareerRecommendation[]
  >([])
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const sendMessage = useCallback(async (query: string) => {
    abortRef.current?.abort()

    setLoading(true)
    setError(null)
    setCurrentAgent(null)
    setRoutingKey(null)
    setJobOpenings([])
    setCareerRecommendations([])
    setFinalAnswer(null)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(API_ENDPOINTS.CHAT_STREAM, {
        method: "POST",
        headers: DEFAULT_HEADERS,
        body: JSON.stringify({
          query,
          stream: true,
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(
          `Server error: ${response.status} ${response.statusText}`
        )
      }

      for await (const event of parseSSEStream(response)) {
        if (controller.signal.aborted) break

        if (event.current_agent !== undefined) {
          setCurrentAgent(event.current_agent ?? null)
        }
        if (event.routing_key) {
          setRoutingKey(event.routing_key)
        }
        if (Array.isArray(event.job_openings)) {
          setJobOpenings(event.job_openings)
        }
        if (Array.isArray(event.career_recommendations)) {
          // Drop non-recommendation payloads (e.g. {error: ...})
          setCareerRecommendations(
            event.career_recommendations.filter(
              (r) => r && typeof r === "object" && "title" in r
            )
          )
        }
        if (event.final_answer) {
          setFinalAnswer(event.final_answer)
        }
      }
    } catch (err) {
      if (
        err instanceof DOMException &&
        (err.name === "AbortError" || err.name === "TimeoutError")
      ) {
        return
      }
      const message = err instanceof Error ? err.message : String(err)
      // Surface backend SSE errors clearly (e.g. synthesize crash)
      setError(message)
      console.error("[useChat]", err)
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
      abortRef.current = null
    }
  }, [])

  return {
    sendMessage,
    loading,
    error,
    currentAgent,
    routingKey,
    jobOpenings,
    careerRecommendations,
    finalAnswer,
  }
}
