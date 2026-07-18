"""
Disha - Learning Companion Agent
Builds learning roadmaps from career gap signals + optional request preferences.
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from schemas import AgentState
from tools.profile import profile_label, resolve_profile

logger = logging.getLogger("disha.agents.learning")




# ══════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════

def extract_missing_skills_from_jobs(
    jobs: List[Dict[str, Any]],
    excluded_domains: List[str] | None = None,
) -> Dict[str, int]:
    """Aggregate missing skills from career recommendations with frequency."""
    skill_counts: Dict[str, int] = {}
    excluded = [e.lower() for e in (excluded_domains or []) if e]

    for job in jobs:
        if not isinstance(job, dict):
            continue
        missing = job.get("missing_skills") or []
        for skill in missing:
            skill_lower = str(skill).lower()
            if any(ex in skill_lower for ex in excluded):
                continue
            skill_counts[str(skill)] = skill_counts.get(str(skill), 0) + 1

    return dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True))


def categorize_skill(skill: str) -> str:
    """Categorize a skill into learning domains."""
    skill_lower = skill.lower()
    
    # Agentic AI
    if any(kw in skill_lower for kw in [
        "agent", "langgraph", "langchain", "autogen", "crewai", 
        "tool use", "function calling", "planning", "reasoning",
        "reflexion", "tree of thought", "react", "multi-agent"
    ]):
        return "agentic_ai"
    
    # LLMOps/Infra
    if any(kw in skill_lower for kw in [
        "vllm", "triton", "tgi", "bentoml", "mlflow", "kubeflow",
        "airflow", "prefect", "dagster", "ray", "kuberay",
        "model serving", "inference", "speculative decoding",
        "lora", "qlora", "peft", "mlops", "llmops",
        "kubernetes", "k8s", "gpu", "tpU", "monitoring", "drift",
        "feature store", "model registry", "a/b testing"
    ]):
        return "llmops_infrastructure"
    
    # RAG
    if any(kw in skill_lower for kw in [
        "rag", "retrieval", "vector", "embedding", "pinecone", 
        "weaviate", "milvus", "qdrant", "chroma", "pgvector",
        "rerank", "hybrid search", "graphrag", "self-rag", "crag"
    ]):
        return "rag_advanced"
    
    # MLOps Platform
    if any(kw in skill_lower for kw in [
        "mlflow", "wandb", "kubeflow", "feast", "evidently",
        "zenml", "dagster", "prefect", "airflow", "ml platform"
    ]):
        return "mlops_platform"
    
    # Backend Architecture
    if any(kw in skill_lower for kw in [
        "microservices", "distributed systems", "system design",
        "grpc", "kafka", "redis", "clickhouse", "postgresql",
        "scalability", "high availability", "load balancing"
    ]):
        return "backend_architecture"
    
    # Neuro-symbolic
    if any(kw in skill_lower for kw in [
        "neuro-symbolic", "symbolic reasoning", "logic", "problog",
        "constraint satisfaction", "smt", "verification"
    ]):
        return "neuro_symbolic"
    
    return "general"


def get_paper_recommendations(skill_gaps: Dict[str, int], top_n: int = 15) -> List[Dict[str, Any]]:
    """Map skill gaps to paper recommendations."""
    recommendations = []
    seen_papers = set()
    
    for skill, count in list(skill_gaps.items())[:top_n]:
        category = categorize_skill(skill)
        papers = ADVANCED_PAPERS.get(category, [])
        
        for paper in papers:
            paper_key = paper["id"]
            if paper_key in seen_papers:
                continue
            seen_papers.add(paper_key)
            
            recommendations.append({
                "arxiv_id": paper["id"],
                "title": paper["title"],
                "year": paper["year"],
                "relevance": paper["relevance"],
                "category": category,
                "tags": paper["tags"],
                "triggered_by": skill,
                "gap_frequency": count,
                "url": f"https://arxiv.org/abs/{paper['id']}",
                "priority": "high" if count >= 2 else "medium",
            })
    
    # Sort by priority (high first), then by gap frequency
    recommendations.sort(key=lambda x: (0 if x["priority"] == "high" else 1, -x["gap_frequency"]))
    return recommendations[:20]


def build_learning_phases(
    paper_recs: List[Dict[str, Any]], 
    skill_gaps: Dict[str, int]
) -> List[Dict[str, Any]]:
    """Build structured learning phases from recommendations."""
    # Group by category
    by_category = {}
    for paper in paper_recs:
        cat = paper["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(paper)
    
    # Phase ordering (foundational -> core -> advanced -> applied)
    phase_order = [
        ("neuro_symbolic", "Foundational: Neuro-Symbolic Reasoning"),
        ("agentic_ai", "Core: Agentic AI Architectures"),
        ("rag_advanced", "Core: Advanced RAG & Retrieval"),
        ("llmops_infrastructure", "Core: LLMOps & Model Serving Infrastructure"),
        ("mlops_platform", "Applied: ML Platform Engineering"),
        ("backend_architecture", "Applied: Backend Architecture for ML Systems"),
    ]
    
    phases = []
    for cat, title in phase_order:
        if cat in by_category and by_category[cat]:
            papers = by_category[cat]
            # Identify unique skills covered
            covered_skills = set()
            for p in papers:
                covered_skills.add(p["triggered_by"])
            
            phases.append({
                "phase_id": f"phase_{len(phases)+1}",
                "title": title,
                "category": cat,
                "description": f"Master {len(papers)} key papers covering {len(covered_skills)} skill gaps",
                "papers": papers,
                "skills_covered": sorted(list(covered_skills)),
                "estimated_weeks": 2 if cat in ["neuro_symbolic"] else 3,
                "resources": LEARNING_RESOURCES.get("courses", []) + LEARNING_RESOURCES.get("blogs_series", []),
                "milestones": [
                    f"Read and implement key concepts from {min(3, len(papers))} core papers",
                    f"Build a minimal prototype demonstrating {cat.replace('_', ' ')}",
                    "Write a technical summary blog post",
                ],
            })
    
    return phases


def node_learning_companion(state: AgentState) -> AgentState:
    """
    Learning Companion: gap analysis + optional Gemini roadmap from career signals.
    """
    profile = resolve_profile(state)
    label = profile_label(profile)
    logger.info("[Learning Companion] Analyzing skill gaps (%s)...", label)
    state["current_agent"] = "learning_companion"
    state["updated_at"] = datetime.now()

    career_recs = state.get("career_recommendations") or []
    if not career_recs or (
        len(career_recs) == 1 and career_recs[0].get("error")
    ):
        logger.warning("[Learning Companion] No career recommendations to analyze")
        state["learning_roadmap"] = {
            "error": "No career data available for gap analysis"
        }
        return state

    skill_gaps = extract_missing_skills_from_jobs(
        career_recs,
        excluded_domains=list(profile.get("excluded_domains") or []),
    )

    if not skill_gaps:
        logger.info("[Learning Companion] No structured skill gaps detected")
        state["learning_roadmap"] = {
            "status": "complete",
            "message": (
                "No skill-gap signals from current recommendations "
                "(often means job listings lack structured skills, "
                "or no candidate skills were provided)."
            ),
            "skill_gaps": {},
            "profile_label": label,
        }
        return state

    logger.info("[Learning Companion] Top skill gaps: %s", list(skill_gaps.items())[:10])

    # Compact prefs for the model — never dump a personal dossier by default
    prefs_for_llm = {
        "display_name": profile.get("display_name"),
        "skills": profile.get("skills") or [],
        "target_roles": profile.get("target_roles") or [],
        "experience_years": profile.get("experience_years"),
    }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
        prompt = f"""
You are an expert AI career coach helping a job seeker close skill gaps.
Optional preferences (may be empty): {json.dumps(prefs_for_llm)}

Skill gaps observed across target roles (skill -> frequency):
{json.dumps(skill_gaps)}

Generate a practical learning roadmap.
Output ONLY raw JSON matching this schema:
{{
  "profile": {{"label": "...", "target": "..."}},
  "gap_analysis": {{"top_gaps": {{"skill": count}}}},
  "paper_recommendations": [
    {{"arxiv_id": "...", "title": "...", "year": 2024, "relevance": "core", "tags": ["..."]}}
  ],
  "learning_phases": [
    {{"phase_id": "phase_1", "title": "...", "description": "...", "skills_covered": ["..."], "estimated_weeks": 2, "milestones": ["..."]}}
  ],
  "next_actions": ["..."]
}}
Do NOT use markdown code blocks. Output the raw JSON object.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]

        roadmap = json.loads(content)
        roadmap["generated_at"] = datetime.now().isoformat()
        roadmap["profile_label"] = label
    except Exception as e:
        logger.error("[Learning Companion] Failed to generate/parse LLM roadmap: %s", e)
        roadmap = {"error": f"LLM generation failed: {str(e)}"}

    state["learning_roadmap"] = roadmap
    return state