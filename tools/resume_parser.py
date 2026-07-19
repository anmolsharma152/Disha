"""
Resume text extraction + profile field inference.

Supports PDF and plain text. Uses Gemini structured output when an API key
is available; falls back to lightweight heuristics otherwise.
"""

from __future__ import annotations

import io
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("disha.tools.resume_parser")

# Common tech/skills lexicon for heuristic fallback (not a personal profile)
_SKILL_LEXICON = [
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++",
    "c#", "kotlin", "scala", "ruby", "php", "swift", "r", "matlab",
    "pytorch", "tensorflow", "jax", "keras", "scikit-learn", "sklearn", "pandas",
    "numpy", "spark", "hadoop", "airflow", "dbt", "kafka", "flink",
    "langchain", "langgraph", "llamaindex", "rag", "llm", "openai", "huggingface",
    "transformers", "vllm", "mlflow", "kubeflow", "wandb", "weights & biases",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "helm", "ci/cd",
    "aws", "gcp", "azure", "s3", "lambda", "ec2", "bigquery", "snowflake",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "pinecone", "weaviate", "qdrant", "milvus", "chroma", "pgvector",
    "fastapi", "django", "flask", "spring", "react", "next.js", "node.js",
    "graphql", "grpc", "rest", "microservices", "system design",
    "linux", "git", "prometheus", "grafana", "datadog",
    "nlp", "computer vision", "deep learning", "machine learning", "mlops",
    "llmops", "data engineering", "data science", "sql", "nosql",
]


class ResumeProfileExtract(BaseModel):
    """Structured fields extracted from a resume for Disha preferences."""

    display_name: Optional[str] = Field(None, description="Candidate full name if present")
    skills: List[str] = Field(default_factory=list, description="Technical and tool skills")
    target_roles: List[str] = Field(
        default_factory=list,
        description="Likely target job titles based on experience and headline",
    )
    target_cities: List[str] = Field(
        default_factory=list,
        description="Cities/regions mentioned as location or preference",
    )
    experience_years: Optional[float] = Field(
        None, description="Approximate years of professional experience"
    )
    prefer_remote: Optional[bool] = Field(
        None, description="True if resume signals remote preference"
    )
    willing_to_relocate: Optional[bool] = Field(
        None, description="True if resume signals relocation openness"
    )
    education: Optional[str] = Field(None, description="Highest/recent education one-liner")
    summary: Optional[str] = Field(
        None, description="1-2 sentence professional summary derived from resume"
    )
    min_base_salary_inr: Optional[int] = Field(
        None,
        description="Only set if an explicit salary expectation in INR/LPA appears",
    )


def extract_text_from_pdf(data: bytes) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: List[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n".join(parts).strip()


def extract_text_from_upload(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text = extract_text_from_pdf(data)
        if not text or len(text) < 40:
            raise ValueError("Could not extract enough text from PDF (scanned PDFs need OCR)")
        return text
    if name.endswith(".txt") or name.endswith(".md"):
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                return data.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text resume")
    # Try PDF magic then utf-8
    if data[:4] == b"%PDF":
        return extract_text_from_pdf(data)
    try:
        return data.decode("utf-8").strip()
    except UnicodeDecodeError as e:
        raise ValueError(
            "Unsupported file type. Upload a PDF or .txt resume."
        ) from e


def _heuristic_extract(text: str) -> ResumeProfileExtract:
    lower = text.lower()
    skills: List[str] = []
    seen = set()
    for skill in _SKILL_LEXICON:
        if skill in lower and skill not in seen:
            # Prefer title-cased display for multi-word
            display = skill.upper() if skill in ("aws", "gcp", "sql", "nlp", "mlops", "llmops", "rag", "llm") else skill.title()
            if skill == "c++":
                display = "C++"
            elif skill == "node.js":
                display = "Node.js"
            elif skill == "next.js":
                display = "Next.js"
            elif skill == "k8s":
                display = "Kubernetes"
            skills.append(display)
            seen.add(skill)

    # Years: "3 years", "3+ years experience"
    years = None
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:experience|exp)",
        lower,
    )
    if m:
        try:
            years = float(m.group(1))
        except ValueError:
            years = None

    cities = []
    for city in (
        "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "chennai",
        "delhi", "gurgaon", "gurugram", "noida", "jaipur", "remote",
    ):
        if city in lower:
            cities.append(city)

    roles = []
    for role in (
        "software engineer", "backend engineer", "frontend engineer",
        "full stack", "ml engineer", "machine learning engineer",
        "data scientist", "data engineer", "research engineer",
        "sde", "devops", "sre", "product manager",
    ):
        if role in lower:
            roles.append(role.title())

    name = None
    first_lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:5]
    if first_lines:
        candidate = first_lines[0]
        if 2 <= len(candidate.split()) <= 5 and len(candidate) < 60:
            if not re.search(r"@|http|curriculum|resume|cv\b", candidate, re.I):
                name = candidate

    prefer_remote = "remote" in lower and any(
        w in lower for w in ("prefer", "open to", "seeking", "available")
    ) or False
    if "remote" in lower:
        prefer_remote = True

    return ResumeProfileExtract(
        display_name=name,
        skills=skills[:40],
        target_roles=roles[:8],
        target_cities=list(dict.fromkeys(cities))[:10],
        experience_years=years,
        prefer_remote=prefer_remote if "remote" in lower else None,
        willing_to_relocate=True if "relocat" in lower else None,
        education=None,
        summary=None,
        min_base_salary_inr=None,
    )


def _llm_extract(text: str) -> ResumeProfileExtract:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    structured = llm.with_structured_output(ResumeProfileExtract)
    prompt = f"""
Extract a job-search profile from this resume text for an India-focused
career matching product.

Rules:
- skills: concrete tools, languages, frameworks (normalize casing, max ~40)
- target_roles: plausible titles they would apply for (from experience/headline)
- target_cities: only locations clearly associated with the candidate
- experience_years: best estimate of professional years (not education years)
- min_base_salary_inr: ONLY if an explicit INR/LPA expectation appears; else null
- Do not invent employers or degrees not in the text

Resume:
{text[:20000]}
"""
    result = structured.invoke(prompt)
    if isinstance(result, ResumeProfileExtract):
        return result
    return ResumeProfileExtract.model_validate(result)


def extract_profile_from_resume_text(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Returns (profile_dict, method) where method is 'llm' or 'heuristic'.
    """
    cleaned = (text or "").strip()
    if len(cleaned) < 80:
        raise ValueError("Resume text too short to extract a useful profile")

    has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    if has_key:
        try:
            extracted = _llm_extract(cleaned)
            method = "llm"
        except Exception as e:
            logger.warning("[Resume] LLM extract failed, using heuristic: %s", e)
            extracted = _heuristic_extract(cleaned)
            method = "heuristic"
    else:
        logger.info("[Resume] No Gemini key — heuristic extraction")
        extracted = _heuristic_extract(cleaned)
        method = "heuristic"

    profile = {
        "display_name": extracted.display_name,
        "skills": extracted.skills or [],
        "target_roles": extracted.target_roles or [],
        "target_cities": extracted.target_cities or [],
        "experience_years": extracted.experience_years,
        "prefer_remote": extracted.prefer_remote
        if extracted.prefer_remote is not None
        else True,
        "willing_to_relocate": extracted.willing_to_relocate
        if extracted.willing_to_relocate is not None
        else True,
        "excluded_keywords": [],
        "excluded_domains": [],
        "min_base_salary_inr": extracted.min_base_salary_inr,
        # Extra metadata kept in memory profile for UI/summary (ignored by scorer if unknown)
        "education": extracted.education,
        "summary": extracted.summary,
    }
    # Prefer deterministic date-range years over LLM guess
    from tools.experience import apply_deterministic_experience

    profile = apply_deterministic_experience(profile, cleaned)
    return profile, method


def process_resume_upload(filename: str, data: bytes) -> Tuple[Dict[str, Any], str, str, str]:
    """
    Full pipeline: bytes → text → profile.

    Returns: profile, method, text, cleaned_filename
    """
    if not data:
        raise ValueError("Empty file")
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("File too large (max 8MB)")

    safe_name = os.path.basename(filename or "resume.pdf")
    text = extract_text_from_upload(safe_name, data)
    profile, method = extract_profile_from_resume_text(text)
    return profile, method, text, safe_name
