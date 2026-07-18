export type RemotePolicy =
  | "onsite"
  | "hybrid"
  | "remote"
  | "remote_friendly"
  | "unknown"

export type ExperienceLevel =
  | "intern"
  | "entry"
  | "junior"
  | "mid"
  | "senior"
  | "staff"
  | "principal"
  | "director"
  | "vp"
  | "c_level"
  | "unknown"

export type ScraperSource =
  | "career_page"
  | "ats_greenhouse"
  | "ats_lever"
  | "ats_workday"
  | "ats_ashby"
  | "ats_bamboo"
  | "linkedin"
  | "glassdoor"
  | "indeed"
  | "rss_feed"
  | "sec_filing"
  | "financial_api"
  | "manual"

export type EmploymentType =
  | "full_time"
  | "part_time"
  | "contract"
  | "internship"
  | "temp"

export type CompensationSource =
  | "posted"
  | "estimated"
  | "glassdoor"
  | "levels_fyi"
  | "h1b"

export type Priority = "high" | "medium" | "low"

export type CompensationFit = "good" | "poor" | "below" | "unavailable"

export interface ChatRequest {
  query: string
  user_id?: string
  session_id?: string | null
  max_iterations?: number
  stream?: boolean
}

export interface ChatResponse {
  session_id: string
  final_answer: string
  answer_confidence: number
  iterations: number
  citations: Record<string, unknown>[]
  routing_key: string
  current_agent: string | null
  total_tokens: number
  total_cost_usd: number
  completed_at: string
  job_openings: JobOpening[]
  career_recommendations: CareerRecommendation[]
}

export interface StreamEvent {
  step: number
  current_agent?: string | null
  routing_key: string
  iteration: number
  session_id: string
  job_openings?: JobOpening[]
  career_recommendations?: CareerRecommendation[]
  final_answer?: string
  answer_confidence?: number
  citations?: Record<string, unknown>[]
  error?: string
}

export interface JobOpening {
  job_id: string
  company_name: string
  title: string
  title_normalized?: string | null
  location_raw: string
  location_city?: string | null
  location_state?: string | null
  location_country?: string | null
  remote_policy: RemotePolicy
  timezone?: string | null
  experience_level: ExperienceLevel
  department?: string | null
  team?: string | null
  employment_type: EmploymentType
  tech_stack: string[]
  skills_required: string[]
  skills_preferred: string[]
  certifications: string[]
  payout_min?: number | null
  payout_max?: number | null
  equity_min?: number | null
  equity_max?: number | null
  bonus_target?: number | null
  sign_on_bonus?: number | null
  currency: string
  compensation_source: CompensationSource
  compensation_confidence: number
  visa_sponsorship?: boolean | null
  h1b_eligible?: boolean | null
  security_clearance?: string | null
  description_raw: string
  description_clean?: string | null
  requirements_raw?: string | null
  benefits_raw?: string | null
  source_url: string
  source_domain: string
  scraper_source: ScraperSource
  posted_date?: string | null
  scraped_at?: string
  expires_at?: string | null
  is_active: boolean
  payout_midpoint?: number | null
  total_comp_estimate?: number | null
  application_url?: string | null
  job_hash?: string | null
}

export interface CompensationDetail {
  base_midpoint?: number | null
  total_estimate?: number | null
  fit: CompensationFit
  meets_minimum: boolean
  currency: string
  display_lpa: number
  display_crores: number
}

export interface CareerRecommendation {
  job_id: string
  company: string
  title: string
  title_normalized?: string | null
  location: string
  remote_policy: string
  match_score: number
  skill_match_pct: number
  matched_skills: string[]
  missing_skills: string[]
  compensation: CompensationDetail
  experience_fit: string
  remote_fit: string
  visa_fit: string
  application_url?: string | null
  source_url?: string | null
  reasoning: string
  priority: Priority
  analyzed_at: string
}
