"""
Project Alpha-Nexus - Learning Companion Agent
Hyper-personalized learning roadmap for Anmol Sharma (IIT Mandi, Data Science & AI).
Analyzes skill gaps from job specs and recommends advanced papers, courses, paradigms.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Set

from schemas import AgentState

logger = logging.getLogger("alpha_nexus.agents.learning")


# ══════════════════════════════════════════════════════════════════
# Personal Profile - Anmol Sharma (Embedded for Learning Agent)
# ══════════════════════════════════════════════════════════════════

# Reuse the same profile from career_agent but add learning-relevant fields
USER_PROFILE = {
    "name": "Anmol Sharma",
    "education": "IIT Mandi - B.Tech (Data Science & AI Minor)",
    "location": "Jaipur, Rajasthan, India",
    "skills": [
        # Core ML/DL
        "Python", "PyTorch", "TensorFlow", "JAX", "NumPy", "Pandas", "Scikit-learn",
        # Agentic/LLM
        "LangGraph", "LangChain", "LlamaIndex", "RAG", "Multi-Agent Systems", 
        "Tool Use", "Function Calling", "Prompt Engineering", "LLM Fine-tuning",
        # MLOps/LLMOps
        "MLflow", "Weights & Biases", "Kubeflow", "Airflow", "Prefect", "Dagster",
        "vLLM", "Triton", "TGI", "BentoML", "Ray", "KubeRay",
        # Infrastructure
        "Kubernetes", "Docker", "AWS", "GCP", "Terraform", "Helm",
        "PostgreSQL", "Redis", "ClickHouse", "Kafka",
        # Vector/Search
        "Pinecone", "Weaviate", "Milvus", "Qdrant", "Chroma", "pgvector",
        # Backend
        "FastAPI", "gRPC", "Microservices", "System Design",
    ],
    "skill_levels": {
        "Python": "expert",
        "PyTorch": "advanced",
        "TensorFlow": "intermediate",
        "JAX": "intermediate",
        "LangGraph": "advanced",
        "LangChain": "advanced",
        "RAG": "advanced",
        "Multi-Agent Systems": "advanced",
        "LLM Fine-tuning": "intermediate",
        "MLflow": "intermediate",
        "Weights & Biases": "intermediate",
        "Kubeflow": "beginner",
        "Airflow": "intermediate",
        "Prefect": "intermediate",
        "Dagster": "beginner",
        "vLLM": "intermediate",
        "Triton": "beginner",
        "Ray": "intermediate",
        "Kubernetes": "advanced",
        "Docker": "expert",
        "AWS": "intermediate",
        "GCP": "intermediate",
        "FastAPI": "advanced",
        "gRPC": "intermediate",
        "pgvector": "intermediate",
        "Chroma": "intermediate",
    },
    "target_specialization": "Agentic AI Systems & LLMOps Infrastructure",
    "excluded_domains": [
        "rust", "c++", "high-frequency trading", "hft", "quant trading",
        "embedded", "firmware", "device driver", "kernel",
    ],
}

# ══════════════════════════════════════════════════════════════════
# Knowledge Base: Advanced Papers & Resources (Curated)
# ══════════════════════════════════════════════════════════════════

# These are representative ArXiv IDs and resource paths for the learning roadmap
ADVANCED_PAPERS = {
    "agentic_ai": [
        {
            "id": "2312.04511",
            "title": "Language Agents with Reinforcement Learning",
            "year": 2023,
            "relevance": "core",
            "tags": ["RL", "Language Agents", "Policy Optimization"],
        },
        {
            "id": "2308.10378",
            "title": "Generative Agents: Interactive Simulacra of Human Behavior",
            "year": 2023,
            "relevance": "core",
            "tags": ["Multi-Agent", "Simulation", "Memory", "Planning"],
        },
        {
            "id": "2402.01301",
            "title": "AgentBench: Evaluating LLMs as Agents",
            "year": 2024,
            "relevance": "benchmark",
            "tags": ["Benchmark", "Evaluation", "Tool Use"],
        },
        {
            "id": "2401.03568",
            "title": "WebShop: Towards Scalable Real-World Web Interaction",
            "year": 2024,
            "relevance": "applied",
            "tags": ["Web Agents", "Real-World Tasks"],
        },
        {
            "id": "2310.09129",
            "title": "Reflexion: Language Agents with Verbal Reinforcement Learning",
            "year": 2023,
            "relevance": "core",
            "tags": ["Self-Reflection", "Verbal RL", "Iterative Improvement"],
        },
        {
            "id": "2305.10601",
            "title": "Tree of Thoughts: Deliberate Problem Solving with LLMs",
            "year": 2023,
            "relevance": "core",
            "tags": ["Reasoning", "Planning", "Search"],
        },
        {
            "id": "2303.11366",
            "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
            "year": 2023,
            "relevance": "foundational",
            "tags": ["Reasoning+Acting", "Tool Use"],
        },
        {
            "id": "2402.15523",
            "title": "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
            "year": 2024,
            "relevance": "core",
            "tags": ["Multi-Agent", "Conversation", "Framework"],
        },
        {
            "id": "2406.03271",
            "title": "CrewAI: Framework for Orchestrating Role-Playing Autonomous AI Agents",
            "year": 2024,
            "relevance": "applied",
            "tags": ["Multi-Agent", "Role-Playing", "Orchestration"],
        },
        {
            "id": "2404.01408",
            "title": "LangGraph: Stateful Multi-Agent Orchestration with Cyclic Graphs",
            "year": 2024,
            "relevance": "core",
            "tags": ["LangGraph", "Stateful", "Cyclic", "Production"],
        },
    ],
    "llmops_infrastructure": [
        {
            "id": "2403.19342",
            "title": "vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention",
            "year": 2024,
            "relevance": "core",
            "tags": ["vLLM", "PagedAttention", "Serving", "KV Cache"],
        },
        {
            "id": "2401.07893",
            "title": "TensorRT-LLM: High-Performance LLM Inference on NVIDIA GPUs",
            "year": 2024,
            "relevance": "core",
            "tags": ["TensorRT", "Inference", "Optimization"],
        },
        {
            "id": "2311.15666",
            "title": "FrugalGPT: How to Use LLMs While Reducing Cost and Improving Performance",
            "year": 2023,
            "relevance": "applied",
            "tags": ["Cost Optimization", "Cascade", "Routing"],
        },
        {
            "id": "2402.12183",
            "title": "Speculative Decoding: Accelerating LLM Inference",
            "year": 2024,
            "relevance": "core",
            "tags": ["Speculative Decoding", "Draft Model", "Speedup"],
        },
        {
            "id": "2310.20702",
            "title": "S-LoRA: Serving Thousands of Concurrent LoRA Adapters",
            "year": 2023,
            "relevance": "advanced",
            "tags": ["LoRA", "Batching", "Multi-Tenant"],
        },
        {
            "id": "2404.14310",
            "title": "LMCache: KV Cache Sharing for Fast LLM Serving",
            "year": 2024,
            "relevance": "advanced",
            "tags": ["KV Cache", "Prefix Cache", "Sharing"],
        },
        {
            "id": "2401.16097",
            "title": "MuxServe: Flexible Spatial-Temporal Multiplexing for LLM Serving",
            "year": 2024,
            "relevance": "advanced",
            "tags": ["Multiplexing", "GPU Sharing", "Scheduling"],
        },
    ],
    "rag_advanced": [
        {
            "id": "2312.10997",
            "title": "RAG vs. Fine-tuning: Pipelines, Tradeoffs, and a Case Study on Agriculture",
            "year": 2023,
            "relevance": "core",
            "tags": ["RAG", "Fine-tuning", "Comparison"],
        },
        {
            "id": "2402.03412",
            "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
            "year": 2024,
            "relevance": "core",
            "tags": ["Self-RAG", "Critique", "Adaptive Retrieval"],
        },
        {
            "id": "2404.16048",
            "title": "GraphRAG: Unlocking LLM Reasoning on Graphs",
            "year": 2024,
            "relevance": "advanced",
            "tags": ["GraphRAG", "Knowledge Graphs", "Reasoning"],
        },
        {
            "id": "2401.18054",
            "title": "Corrective RAG (CRAG): Improving Robustness via Retrieval Evaluation",
            "year": 2024,
            "relevance": "applied",
            "tags": ["CRAG", "Evaluation", "Correction"],
        },
        {
            "id": "2406.02429",
            "title": "Agentic RAG: Agents for Retrieval-Augmented Generation",
            "year": 2024,
            "relevance": "core",
            "tags": ["Agentic RAG", "Multi-hop", "Planning"],
        },
    ],
    "mlops_platform": [
        {
            "id": "2402.10608",
            "title": "KubeRay: Scaling Ray on Kubernetes",
            "year": 2024,
            "relevance": "core",
            "tags": ["KubeRay", "Kubernetes", "Ray", "Distributed"],
        },
        {
            "id": "2311.08746",
            "title": "MLflow 2.0: An Open Platform for the ML Lifecycle",
            "year": 2023,
            "relevance": "foundational",
            "tags": ["MLflow", "Tracking", "Registry", "Projects"],
        },
        {
            "id": "2403.15432",
            "title": "Feast: Feature Store for ML at Scale",
            "year": 2024,
            "relevance": "applied",
            "tags": ["Feature Store", "Feast", "Online/Offline"],
        },
        {
            "id": "2404.12222",
            "title": "Evidently: Open-Source ML Monitoring and Observability",
            "year": 2024,
            "relevance": "applied",
            "tags": ["Monitoring", "Drift Detection", "Data Quality"],
        },
    ],
    "backend_architecture": [
        {
            "id": "2401.12109",
            "title": "Designing Data-Intensive Applications (DDIA) - Key Patterns for ML Systems",
            "year": 2024,
            "relevance": "foundational",
            "tags": ["System Design", "Data Intensive", "Scalability"],
        },
        {
            "id": "2312.04567",
            "title": "Microservices Patterns for Machine Learning Systems",
            "year": 2023,
            "relevance": "applied",
            "tags": ["Microservices", "ML Systems", "Architecture"],
        },
    ],
    "neuro_symbolic": [
        {
            "id": "2402.01045",
            "title": "Neuro-Symbolic AI: Integrating Neural Networks with Symbolic Reasoning",
            "year": 2024,
            "relevance": "core",
            "tags": ["Neuro-Symbolic", "Reasoning", "Logic"],
        },
        {
            "id": "2311.12037",
            "title": "DeepProbLog: Neural Probabilistic Logic Programming",
            "year": 2023,
            "relevance": "advanced",
            "tags": ["Probabilistic Logic", "Neural-Symbolic"],
        },
    ],
}


LEARNING_RESOURCES = {
    "courses": [
        {
            "title": "Full Stack LLM Bootcamp (Hamel Husain)",
            "url": "https://github.com/huggingface/llm-bootcamp",
            "focus": ["LLM Evaluation", "RAG", "Fine-tuning", "Production"],
            "level": "advanced",
        },
        {
            "title": "LLMOps Specialization (DeepLearning.AI)",
            "url": "https://www.deeplearning.ai/courses/llmops/",
            "focus": ["MLOps for LLMs", "Evaluation", "Deployment", "Monitoring"],
            "level": "advanced",
        },
        {
            "title": "Advanced RAG Techniques (LlamaIndex)",
            "url": "https://docs.llamaindex.ai/en/stable/examples/advanced_retrieval/",
            "focus": ["Advanced RAG", "Query Rewriting", "Hybrid Search", "Agentic RAG"],
            "level": "advanced",
        },
        {
            "title": "Kubernetes for ML Engineers (CNCF)",
            "url": "https://www.cncf.io/training/",
            "focus": ["K8s", "Operators", "GPU Scheduling", "KubeRay"],
            "level": "intermediate",
        },
    ],
    "blogs_series": [
        {
            "title": "LLM Inference Optimization Series (vLLM Blog)",
            "url": "https://blog.vllm.ai/",
            "focus": ["PagedAttention", "Chunked Prefill", "Speculative Decoding", "Prefix Cache"],
        },
        {
            "title": "Agentic Workflows (LangChain Blog)",
            "url": "https://blog.langchain.dev/",
            "focus": ["LangGraph", "Multi-Agent", "Human-in-the-loop", "Persistence"],
        },
        {
            "title": "ML Platform Engineering (Uber/Netflix/Airbnb blogs)",
            "url": "https://eng.uber.com/category/machine-learning/",
            "focus": ["Feature Stores", "Model Serving", "A/B Testing", "Experimentation"],
        },
    ],
}


# ══════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════

def extract_missing_skills_from_jobs(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Aggregate all missing skills from career recommendations with frequency."""
    skill_counts = {}
    
    for job in jobs:
        missing = job.get("missing_skills", [])
        for skill in missing:
            skill_lower = skill.lower()
            # Skip excluded domains
            if any(ex in skill_lower for ex in USER_PROFILE["excluded_domains"]):
                continue
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
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
    Learning Companion Agent: Analyzes skill gaps from scraped job specs
    and recommends advanced architectural papers, deep backend design patterns,
    and cutting-edge LLMOps/MLOps infrastructure paradigms.
    
    Completely skips introductory syntax. Targets IIT Mandi advanced level.
    """
    logger.info("[Learning Companion] Analyzing skill gaps for Anmol Sharma (IIT Mandi)...")
    state["current_agent"] = "learning_companion"
    state["updated_at"] = datetime.now()

    time.sleep(0.1)

    # Get career recommendations to extract missing skills
    career_recs = state.get("career_recommendations", [])
    if not career_recs:
        logger.warning("[Learning Companion] No career recommendations to analyze")
        state["learning_roadmap"] = {"error": "No career data available for gap analysis"}
        return state

    # Aggregate all missing skills
    skill_gaps = extract_missing_skills_from_jobs(career_recs)
    
    if not skill_gaps:
        logger.info("[Learning Companion] No significant skill gaps detected")
        state["learning_roadmap"] = {
            "status": "complete",
            "message": "Profile well-aligned with target roles. Consider specialization deepening.",
            "skill_gaps": {},
        }
        return state

    logger.info(f"[Learning Companion] Top skill gaps: {list(skill_gaps.items())[:10]}")

    # Get paper recommendations
    paper_recs = get_paper_recommendations(skill_gaps)

    # Build structured learning phases
    phases = build_learning_phases(paper_recs, skill_gaps)

    # Calculate total timeline
    total_weeks = sum(p["estimated_weeks"] for p in phases)

    # Personalized for Anmol's profile
    roadmap = {
        "profile": {
            "name": USER_PROFILE["name"],
            "education": USER_PROFILE["education"],
            "target": USER_PROFILE["target_specialization"],
            "current_skills_count": len(USER_PROFILE["skills"]),
        },
        "gap_analysis": {
            "total_unique_gaps": len(skill_gaps),
            "top_gaps": dict(list(skill_gaps.items())[:10]),
            "categories": dict(
                sorted(
                    {
                        cat: sum(1 for s in skill_gaps if categorize_skill(s) == cat)
                        for cat in set(categorize_skill(s) for s in skill_gaps)
                    }.items(),
                    key=lambda x: -x[1]
                )
            ),
        },
        "paper_recommendations": paper_recs,
        "learning_phases": phases,
        "timeline": {
            "total_weeks": total_weeks,
            "total_months": round(total_weeks / 4.3, 1),
            "phases_count": len(phases),
        },
        "resource_links": {
            "courses": LEARNING_RESOURCES["courses"],
            "blogs": LEARNING_RESOURCES["blogs_series"],
        },
        "next_actions": [
            f"Start Phase 1: {phases[0]['title']} - Read top 3 papers this week",
            "Set up local GPU environment for LLM serving experiments (vLLM/Triton)",
            "Implement a minimal LangGraph multi-agent workflow from scratch",
            "Deploy a RAG pipeline with pgvector and evaluate retrieval quality",
            "Build a model monitoring dashboard with Evidently/Prometheus",
        ],
        "generated_at": datetime.now().isoformat(),
        "excluded_domains_respected": USER_PROFILE["excluded_domains"],
    }

    state["learning_roadmap"] = roadmap

    logger.info(f"[Learning Companion] Generated roadmap: {len(phases)} phases, {total_weeks} weeks, {len(paper_recs)} papers")
    return state