const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export const API_ENDPOINTS = {
  CHAT: `${API_BASE_URL}/api/chat`,
  CHAT_STREAM: `${API_BASE_URL}/api/chat/stream`,
  HEALTH: `${API_BASE_URL}/health`,
  STATUS: `${API_BASE_URL}/api/v1/status`,
  PROFILE: `${API_BASE_URL}/api/profile`,
  PROFILE_RESUME: `${API_BASE_URL}/api/profile/resume`,
} as const

export const DEFAULT_HEADERS = {
  "Content-Type": "application/json",
} as const
