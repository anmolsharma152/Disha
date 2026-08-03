# Disha Implementation Task List

- [x] SSRF Protection & URL Validation (`is_safe_url`) in `tools/scraper_tools.py`
- [x] Path Traversal Regex Validation (`validate_board_slug`) in `tools/scraper_tools.py`
- [x] Restrict CORS `ALLOWED_ORIGINS` in `api/server.py`
- [x] Rate Limiting Middleware (`check_rate_limit`) on `/api/chat` endpoints in `api/server.py`
- [x] Prompt Injection Framing (<untrusted_content> XML tags) in `tools/career_tools.py`
- [x] Wire Error Recovery Node routing (`state["routing_key"] = "error_recovery"`) in `agents/scraper_agent.py`
- [x] Wire LLM Resume Judge (`evaluate_resume_against_job`) into `agents/career_agent.py`
- [x] Security & Multi-User Isolation Test Suite (`tests/test_security.py`)
- [x] Create `storage/db.py` with SQLAlchemy 2.0 models & `Vector(768)` `cosine_distance` RAG query methods
- [x] Multi-User Isolation: Generate client session UUID (`disha_user_id`) in `frontend/hooks/useProfile.ts`
- [x] Bind isolated `user_id` to SSE streaming chat requests in `frontend/hooks/useChat.ts`
- [x] Next.js 14 Production Build Verification (`npm run build` passed)
