"""
Disha - FastAPI Server
Async API gateway exposing the LangGraph orchestration.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main import run_disha, stream_disha
from schemas import AgentState
from storage.user_memory import (
    DEFAULT_USER_ID,
    clear_memory,
    memory_public_view,
    upsert_profile_from_resume,
)
from tools.resume_parser import process_resume_upload

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("disha.api")


# ──────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────


class UserPreferences(BaseModel):
    """
    Optional per-request preferences. Empty/omitted fields mean no hard filter.
    Not a stored personal dossier — pass only what this query should use.
    """

    display_name: Optional[str] = None
    skills: Optional[list[str]] = None
    target_cities: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None
    experience_years: Optional[float] = Field(default=None, ge=0, le=50)
    min_base_salary_inr: Optional[int] = Field(default=None, ge=0)
    prefer_remote: Optional[bool] = None
    willing_to_relocate: Optional[bool] = None
    excluded_keywords: Optional[list[str]] = None
    excluded_domains: Optional[list[str]] = None


class ChatRequest(BaseModel):
    """Request model for /api/chat endpoint."""

    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    user_id: str = Field(default="default", description="User identifier")
    session_id: Optional[str] = Field(
        default=None, description="Session ID (auto-generated if not provided)"
    )
    max_iterations: int = Field(
        default=6, ge=1, le=20, description="Maximum supervisor iterations"
    )
    stream: bool = Field(default=False, description="Whether to stream response")
    preferences: Optional[UserPreferences] = Field(
        default=None,
        description="Optional career preferences for this request only",
    )


class ChatResponse(BaseModel):
    """Response model for /api/chat endpoint."""

    session_id: str
    final_answer: str
    answer_confidence: float
    iterations: int
    citations: list
    routing_key: str
    current_agent: Optional[str]
    completed_at: str
    job_openings: list[dict] = Field(default_factory=list, description="Structured job opening data")
    career_recommendations: list[dict] = Field(default_factory=list, description="Structured career match data")


# ──────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Disha API",
    description="Personal Intelligence OS - Market Intelligence & Career Optimization",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "disha-api",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint with system info."""
    return {
        "api_version": "v1",
        "status": "operational",
        "graph_compiled": True,
        "checkpointer": "MemorySaver",
        "features": [
            "multi_agent_orchestration",
            "financial_analysis",
            "career_matching",
            "learning_roadmap",
            "india_localization",
            "streaming",
            "resume_memory",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/profile")
async def get_profile(user_id: str = DEFAULT_USER_ID):
    """Return the active user's resume-derived memory (single-user v1)."""
    return memory_public_view(user_id)


@app.delete("/api/profile")
async def delete_profile(user_id: str = DEFAULT_USER_ID):
    """Clear saved resume memory for the user."""
    cleared = clear_memory(user_id)
    return {"cleared": cleared, "user_id": user_id}


@app.post("/api/profile/resume")
async def upload_resume(
    file: UploadFile = File(..., description="PDF or TXT resume"),
    user_id: str = DEFAULT_USER_ID,
):
    """
    Upload a resume, extract preferences (skills, roles, cities, …),
    and store them as user memory for grounded search/matching.
    """
    filename = file.filename or "resume.pdf"
    lower = filename.lower()
    if not (
        lower.endswith(".pdf")
        or lower.endswith(".txt")
        or lower.endswith(".md")
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a PDF or .txt resume.",
        )

    try:
        data = await file.read()
        profile, method, text, safe_name = process_resume_upload(filename, data)
        memory = upsert_profile_from_resume(
            profile=profile,
            filename=safe_name,
            text_preview=text[:500],
            char_count=len(text),
            user_id=user_id or DEFAULT_USER_ID,
            extraction_method=method,
        )
        logger.info(
            "Resume uploaded user=%s skills=%d method=%s",
            user_id,
            len(profile.get("skills") or []),
            method,
        )
        return {
            "ok": True,
            "extraction_method": method,
            "memory": memory_public_view(user_id or DEFAULT_USER_ID),
            "profile": memory.get("profile"),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Resume upload failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Resume processing failed: {e}"
        ) from e


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint - executes the full Disha pipeline.
    Returns final synthesized answer with citations and confidence.
    """
    logger.info(f"Chat request: user={request.user_id}, query_len={len(request.query)}")

    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        prefs = (
            request.preferences.model_dump(exclude_none=True)
            if request.preferences
            else None
        )
        # Run pipeline
        result = run_disha(
            user_query=request.query,
            user_id=request.user_id,
            session_id=session_id,
            max_iterations=request.max_iterations,
            user_profile=prefs,
        )

        # Build response
        response = ChatResponse(
            session_id=result.get("session_id", session_id),
            final_answer=result.get("final_answer", "No answer generated"),
            answer_confidence=result.get("answer_confidence", 0.0),
            iterations=result.get("iteration", 0),
            citations=result.get("citations", []),
            routing_key=result.get("routing_key", "unknown"),
            current_agent=result.get("current_agent"),
            completed_at=datetime.utcnow().isoformat(),
            job_openings=result.get("job_openings", []),
            career_recommendations=result.get("career_recommendations", []),
        )

        logger.info(
            f"Chat completed: session={session_id}, confidence={response.answer_confidence}"
        )
        return response

    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pipeline execution failed: {str(e)}"
        )


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint - yields state updates in real-time.
    Uses Server-Sent Events (SSE) for progressive updates.
    """
    from fastapi.responses import StreamingResponse
    import json

    logger.info(
        f"Stream chat request: user={request.user_id}, query_len={len(request.query)}"
    )

    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        try:
            prefs = (
                request.preferences.model_dump(exclude_none=True)
                if request.preferences
                else None
            )
            for i, state in enumerate(
                stream_disha(
                    user_query=request.query,
                    user_id=request.user_id,
                    session_id=session_id,
                    max_iterations=request.max_iterations,
                    user_profile=prefs,
                )
            ):
                # Format as SSE
                event_data = {
                    "step": i + 1,
                    "current_agent": state.get("current_agent"),
                    "routing_key": state.get("routing_key"),
                    "iteration": state.get("iteration"),
                    "session_id": session_id,
                }

                # Include structured job data when available
                if state.get("job_openings"):
                    event_data["job_openings"] = state["job_openings"]

                # Include structured career recommendations when available
                if state.get("career_recommendations"):
                    event_data["career_recommendations"] = state["career_recommendations"]

                # Include final answer if available
                if state.get("final_answer"):
                    event_data["final_answer"] = state["final_answer"]
                    event_data["answer_confidence"] = state.get(
                        "answer_confidence", 0.0
                    )
                    event_data["citations"] = state.get("citations", [])

                yield f"data: {json.dumps(event_data)}\n\n"

                # Stop if completed
                if state.get("routing_key") == "end":
                    break

        except Exception as e:
            logger.exception(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────────────────────
# Run with: uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
