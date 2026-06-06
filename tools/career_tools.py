"""
Project Alpha-Nexus - Career Tools
LangChain-compatible tools for career intelligence layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger("alpha_nexus.tools.career")


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
    """Extract skill mentions from text with confidence scores."""
    text_lower = text.lower()
    found = {}
    
    for skill in known_skills:
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            # Simple confidence based on context
            # Count occurrences
            count = text_lower.count(skill_lower)
            # Boost if in a technical context
            context_boost = 0.1 if any(ctx in text_lower for ctx in [
                "experience", "project", "built", "developed", "implemented",
                "designed", "architected", "proficient", "expert", "strong"
            ]) else 0
            found[skill] = min(0.9, 0.4 + count * 0.1 + context_boost)
    
    return found


def extract_ats_keywords(job_description: str) -> List[str]:
    """Extract likely ATS keywords from job description."""
    # Common keyword patterns in job descriptions
    import re
    
    # Extract capitalized phrases (likely proper nouns/tech terms)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', job_description)
    
    # Extract tech acronyms
    acronyms = re.findall(r'\b[A-Z]{2,}\b', job_description)
    
    # Common tech keywords
    tech_keywords = [
        "Python", "Java", "Go", "Rust", "TypeScript", "JavaScript",
        "React", "Vue", "Angular", "Node.js", "Django", "FastAPI",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "Kubernetes", "Docker", "AWS", "GCP", "Azure", "Terraform",
        "Kafka", "RabbitMQ", "gRPC", "REST", "GraphQL",
        "PyTorch", "TensorFlow", "JAX", "Hugging Face", "LangChain",
        "LangGraph", "LLM", "RAG", "MLOps", "LLMOps", "MLflow",
        "CI/CD", "GitLab", "GitHub Actions", "Jenkins",
    ]
    
    found = set()
    text_lower = job_description.lower()
    for kw in tech_keywords:
        if kw.lower() in text_lower:
            found.add(kw)
    
    found.update(capitalized[:20])
    found.update(acronyms[:10])
    
    return list(found)


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
    logger.info("Evaluating resume against job description...")
    
    # Combine all job requirements text
    full_job_text = " ".join(filter(None, [
        job_description,
        job_requirements,
    ]))
    
    # Collect all required skills
    all_required = set(job_tech_stack or []) | set(job_skills_required or [])
    all_preferred = set(job_skills_preferred or [])
    all_job_skills = all_required | all_preferred
    
    # Extract skills from resume
    resume_skills = extract_skills_from_text(resume_text, list(all_job_skills))
    
    # Build skill matches
    skill_matches = []
    matched_skills = []
    missing_required = []
    missing_preferred = []
    
    for skill in all_required:
        present = skill in resume_skills
        confidence = resume_skills.get(skill, 0.0)
        skill_matches.append(SkillMatch(
            skill=skill,
            present_in_resume=present,
            confidence=confidence,
            evidence=f"Found with confidence {confidence:.0%}" if present else "Not detected in resume",
        ))
        if present:
            matched_skills.append(skill)
        else:
            missing_required.append(skill)
    
    for skill in all_preferred:
        present = skill in resume_skills
        confidence = resume_skills.get(skill, 0.0)
        skill_matches.append(SkillMatch(
            skill=skill,
            present_in_resume=present,
            confidence=confidence,
            evidence=f"Found with confidence {confidence:.0%}" if present else "Not detected in resume",
        ))
        if present:
            matched_skills.append(skill)
        else:
            missing_preferred.append(skill)
    
    # Calculate overall match score
    required_weight = 0.7
    preferred_weight = 0.3
    
    required_score = len([s for s in all_required if s in resume_skills]) / max(len(all_required), 1)
    preferred_score = len([s for s in all_preferred if s in resume_skills]) / max(len(all_preferred), 1)
    
    overall_match = round((required_score * required_weight + preferred_score * preferred_weight) * 100, 1)
    
    # ATS keyword analysis
    ats_keywords = extract_ats_keywords(full_job_text)
    resume_lower = resume_text.lower()
    ats_matched = [kw for kw in ats_keywords if kw.lower() in resume_lower]
    ats_missing = [kw for kw in ats_keywords if kw.lower() not in resume_lower]
    
    # Strengths and gaps
    strengths = [s for s in matched_skills if resume_skills.get(s, 0) > 0.6]
    gaps = missing_required[:5] + missing_preferred[:3]
    
    # Recommendations
    recommendations = []
    if missing_required:
        recommendations.append(f"Add {', '.join(missing_required[:3])} to resume - these are required for the role")
    if missing_preferred:
        recommendations.append(f"Consider highlighting {', '.join(missing_preferred[:3])} if you have experience")
    if len(ats_missing) > 5:
        recommendations.append(f"Optimize for ATS: include keywords like {', '.join(ats_missing[:5])}")
    if overall_match < 50:
        recommendations.append("Overall match is low - consider if this role aligns with your background")
    elif overall_match < 75:
        recommendations.append("Good match - strengthen resume with specific project examples for missing skills")
    else:
        recommendations.append("Strong match - tailor cover letter to highlight top matched skills")
    
    result = EvaluateResumeOutput(
        overall_match_score=overall_match,
        skill_matches=skill_matches,
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        matched_skills=matched_skills,
        resume_strengths=strengths[:5],
        resume_gaps=gaps,
        recommendations=recommendations,
        ats_keywords_matched=ats_matched[:10],
        ats_keywords_missing=ats_missing[:10],
    )
    
    logger.info(f"Evaluation complete: {overall_match}% match ({len(matched_skills)}/{len(all_job_skills)} skills)")
    return result.model_dump()


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
    Anmol Sharma
    IIT Mandi - B.Tech Data Science & AI
    
    EXPERIENCE:
    - ML Engineer Intern at TechCorp (2023-2024)
      Built RAG pipelines with LangChain and Pinecone
      Fine-tuned Llama-2 7B on domain data using LoRA
      Deployed models with vLLM on Kubernetes
    
    - Research Assistant at IIT Mandi (2022-2023)
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