"""
Disha - Career Tools
LangChain-compatible tools for career intelligence layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger("disha.tools.career")


# ──────────────────────────────────────────────────────────────
# Input/Output Schemas
# ──────────────────────────────────────────────────────────────

class EvaluateResumeInput(BaseModel):
    """Input schema for evaluate_resume_against_job tool."""
    resume_text: str = Field(..., min_length=100, description="Full resume text content")
    job_description: str = Field(..., min_length=50, description="Job description text")
    job_requirements: Optional[str] = Field(None, description="Extracted requirements section")
    job_tech_stack: Optional[List[str]] = Field(default_factory=list, description="Required tech stack")
    job_skills_required: Optional[List[str]] = Field(default_factory=list, description="Required skills")
    job_skills_preferred: Optional[List[str]] = Field(default_factory=list, description="Preferred skills")


class SkillMatch(BaseModel):
    """Individual skill match result."""
    skill: str
    present_in_resume: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None


class EvaluateResumeOutput(BaseModel):
    """Output schema for evaluate_resume_against_job tool."""
    overall_match_score: float = Field(ge=0.0, le=100.0, description="Overall match percentage")
    skill_matches: List[SkillMatch]
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    matched_skills: List[str]
    resume_strengths: List[str]
    resume_gaps: List[str]
    recommendations: List[str]
    ats_keywords_matched: List[str]
    ats_keywords_missing: List[str]


# ──────────────────────────────────────────────────────────────
# Core Evaluation Logic
# ──────────────────────────────────────────────────────────────

def extract_skills_from_text(text: str, known_skills: List[str]) -> Dict[str, float]:
    """Stub kept for legacy references."""
    return {}

def extract_ats_keywords(job_description: str) -> List[str]:
    """Stub kept for legacy references."""
    return []


# ──────────────────────────────────────────────────────────────
# LangChain Tool
# ──────────────────────────────────────────────────────────────

@tool("evaluate_resume_against_job", args_schema=EvaluateResumeInput, return_direct=False)
def evaluate_resume_against_job(
    resume_text: str,
    job_description: str,
    job_requirements: Optional[str] = None,
    job_tech_stack: Optional[List[str]] = None,
    job_skills_required: Optional[List[str]] = None,
    job_skills_preferred: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluate a resume against a job description for skill match and ATS compatibility.
    
    STUB IMPLEMENTATION - Uses keyword matching for demonstration.
    In production, this would use LLM-based extraction and semantic matching.

    Args:
        resume_text: Full resume text content
        job_description: Job description text
        job_requirements: Extracted requirements section (optional)
        job_tech_stack: Required tech stack (optional)
        job_skills_required: Required skills (optional)
        job_skills_preferred: Preferred skills (optional)

    Returns:
        Dictionary with match score, skill analysis, and recommendations
    """
    logger.info("Evaluating resume against job description using Gemini 2.5 Flash...")
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Combine all job requirements text
    full_job_text = " ".join(filter(None, [
        job_description,
        job_requirements,
        f"Tech Stack: {', '.join(job_tech_stack or [])}",
        f"Required: {', '.join(job_skills_required or [])}",
        f"Preferred: {', '.join(job_skills_preferred or [])}",
    ]))

    prompt = f"""
    You are an expert technical recruiter and LLM Judge.
    Evaluate the following candidate's resume against the provided job description and requirements.
    
    Job Description & Requirements:
    {full_job_text}
    
    Candidate Resume:
    {resume_text}
    
    Analyze the match carefully. Identify all matched skills, missing required skills, and missing preferred skills.
    Assign a confidence score (0.0 to 1.0) for each skill match based on how explicitly it is demonstrated in the resume.
    Provide actionable recommendations.
    """
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
        structured_llm = llm.with_structured_output(EvaluateResumeOutput)
        result = structured_llm.invoke(prompt)
        
        logger.info(f"Evaluation complete: {result.overall_match_score}% match")
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Failed to evaluate resume: {e}")
        # Fallback response
        fallback = EvaluateResumeOutput(
            overall_match_score=0.0,
            skill_matches=[],
            missing_required_skills=[],
            missing_preferred_skills=[],
            matched_skills=[],
            resume_strengths=[],
            resume_gaps=[],
            recommendations=[f"Error evaluating resume: {str(e)}"],
            ats_keywords_matched=[],
            ats_keywords_missing=[]
        )
        return fallback.model_dump()


# ──────────────────────────────────────────────────────────────
# Tool Registry
# ──────────────────────────────────────────────────────────────

CAREER_TOOLS = [
    evaluate_resume_against_job,
]

CAREER_TOOL_MAP = {t.name: t for t in CAREER_TOOLS}


def get_career_tool(name: str):
    """Retrieve career tool by name."""
    return CAREER_TOOL_MAP.get(name)


def list_career_tools() -> List[str]:
    """List available career tool names."""
    return list(CAREER_TOOL_MAP.keys())


# ──────────────────────────────────────────────────────────────
# Test Block
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("Testing evaluate_resume_against_job tool")
    print("=" * 60)
    
    # Sample resume
    sample_resume = """
    Sample Candidate
    B.Tech Computer Science
    
    EXPERIENCE:
    - ML Engineer Intern at TechCorp (2023-2024)
      Built RAG pipelines with LangChain and Pinecone
      Fine-tuned Llama-2 7B on domain data using LoRA
      Deployed models with vLLM on Kubernetes
    
    - Research Assistant (2022-2023)
      Worked on multi-agent systems with LangGraph
      Published paper on agentic workflows
    
    SKILLS:
    Python, PyTorch, TensorFlow, JAX, LangChain, LangGraph, 
    RAG, LlamaIndex, MLflow, Weights & Biases, Kubernetes, 
    Docker, AWS, PostgreSQL, Redis, FastAPI, gRPC
    """
    
    # Sample job
    sample_job = """
    Senior ML Engineer - Agentic AI
    Location: Bangalore, Karnataka (Hybrid)
    
    We are looking for an ML Engineer to build autonomous agent systems.
    
    Required:
    - Python, PyTorch, LangGraph, LangChain
    - Experience with RAG pipelines and LLM fine-tuning
    - Kubernetes, Docker, MLflow
    - 3+ years ML engineering experience
    
    Preferred:
    - vLLM, Triton Inference Server
    - Ray, KubeRay for distributed training
    - Multi-agent orchestration (AutoGen, CrewAI)
    - LLMOps: model monitoring, drift detection, A/B testing
    """
    
    result = evaluate_resume_against_job.invoke({
        "resume_text": sample_resume,
        "job_description": sample_job,
        "job_tech_stack": ["Python", "PyTorch", "LangGraph", "LangChain", "Kubernetes", "Docker", "MLflow"],
        "job_skills_required": ["RAG", "LLM Fine-tuning", "Multi-Agent Systems"],
        "job_skills_preferred": ["vLLM", "Triton", "Ray", "KubeRay", "AutoGen", "CrewAI", "LLMOps", "Model Monitoring", "Drift Detection", "A/B Testing"],
    })
    
    print(f"Overall Match: {result['overall_match_score']}%")
    print(f"Matched Skills: {result['matched_skills']}")
    print(f"Missing Required: {result['missing_required_skills']}")
    print(f"Missing Preferred: {result['missing_preferred_skills']}")
    print(f"Strengths: {result['resume_strengths']}")
    print(f"Gaps: {result['resume_gaps']}")
    print(f"Recommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")
    print(f"ATS Keywords Matched: {result['ats_keywords_matched']}")
    print(f"ATS Keywords Missing: {result['ats_keywords_missing']}")
    
    print("\n" + "=" * 60)
    print("✓ Tool test completed!")
    print("=" * 60)