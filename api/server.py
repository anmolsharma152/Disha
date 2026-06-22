"""
Project Alpha-Nexus - FastAPI Server
Async API gateway exposing the LangGraph orchestration.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main import run_alpha_nexus, stream_alpha_nexus
from schemas import AgentState

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("alpha_nexus.api")


# ──────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────


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


class ChatResponse(BaseModel):
    """Response model for /api/chat endpoint."""

    session_id: str
    final_answer: str
    answer_confidence: float
    iterations: int
    citations: list
    routing_key: str
    current_agent: Optional[str]
    total_tokens: int
    total_cost_usd: float
    completed_at: str
    job_openings: list[dict] = Field(default_factory=list, description="Structured job opening data")
    career_recommendations: list[dict] = Field(default_factory=list, description="Structured career match data")


# ──────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Alpha-Nexus API",
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
        "service": "alpha-nexus-api",
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
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint - executes the full Alpha-Nexus pipeline.
    Returns final synthesized answer with citations and confidence.
    """
    logger.info(f"Chat request: user={request.user_id}, query_len={len(request.query)}")

    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Run pipeline
        result = run_alpha_nexus(
            user_query=request.query,
            user_id=request.user_id,
            session_id=session_id,
            max_iterations=request.max_iterations,
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
            total_tokens=result.get("total_tokens", 0),
            total_cost_usd=result.get("total_cost_usd", 0.0),
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
            for i, state in enumerate(
                stream_alpha_nexus(
                    user_query=request.query,
                    user_id=request.user_id,
                    session_id=session_id,
                    max_iterations=request.max_iterations,
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
