"""Shared tech/skill lexicon for resume + job description enrichment."""

from __future__ import annotations

import re
from typing import List, Set

# Normalized key → display label
SKILL_TERMS: dict[str, str] = {
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "golang": "Go",
    " go ": "Go",
    "rust": "Rust",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "sql": "SQL",
    "bash": "Bash",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "jax": "JAX",
    "keras": "Keras",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "spark": "Spark",
    "airflow": "Airflow",
    "kafka": "Kafka",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "langsmith": "LangSmith",
    "llamaindex": "LlamaIndex",
    "llama-index": "LlamaIndex",
    "rag": "RAG",
    "llm": "LLM",
    "mcp": "MCP",
    "vllm": "vLLM",
    "mlflow": "MLflow",
    "wandb": "W&B",
    "weights & biases": "W&B",
    "huggingface": "Hugging Face",
    "transformers": "Transformers",
    "peft": "PEFT",
    "lora": "LoRA",
    "qlora": "QLoRA",
    "bitsandbytes": "bitsandbytes",
    "onnx": "ONNX",
    "faiss": "FAISS",
    "chromadb": "ChromaDB",
    "chroma": "Chroma",
    "pinecone": "Pinecone",
    "weaviate": "Weaviate",
    "qdrant": "Qdrant",
    "milvus": "Milvus",
    "pgvector": "pgvector",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "helm": "Helm",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "react": "React",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "grpc": "gRPC",
    "graphql": "GraphQL",
    "microservices": "Microservices",
    "system design": "System Design",
    "nlp": "NLP",
    "computer vision": "Computer Vision",
    "deep learning": "Deep Learning",
    "machine learning": "Machine Learning",
    "mlops": "MLOps",
    "llmops": "LLMOps",
    "multi-agent": "Multi-Agent Systems",
    "multi agent": "Multi-Agent Systems",
    "prompt engineering": "Prompt Engineering",
    "fine-tuning": "Fine-tuning",
    "fine tuning": "Fine-tuning",
    "ollama": "Ollama",
    "unsloth": "Unsloth",
    "git": "Git",
    "ci/cd": "CI/CD",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "datadog": "Datadog",
    "ray": "Ray",
    "triton": "Triton",
    "whisper": "Whisper",
    "wasm": "WASM",
}


def extract_skills_from_text(text: str, limit: int = 40) -> List[str]:
    """Find known skills in free text (title + description) with word boundaries."""
    if not text:
        return []
    blob = text.lower()
    found: List[str] = []
    seen: Set[str] = set()
    keys = sorted(SKILL_TERMS.keys(), key=len, reverse=True)
    for key in keys:
        k = key.strip()
        # Escape for regex; allow flexible separators for multi-word
        if " " in k or "&" in k or "/" in k:
            parts = re.split(r"[\s/&]+", k)
            pat = r"\b" + r"[\s/&]+".join(re.escape(p) for p in parts if p) + r"\b"
        else:
            # Short tokens need strict boundaries (avoid 'rag' in 'average', 'go' in 'ongoing')
            pat = r"\b" + re.escape(k) + r"\b"
            if k in {"go", "r", "c"}:
                # Too ambiguous alone — skip unless written as tech form
                if k == "go":
                    pat = r"\b(?:golang|go\s*lang)\b"
                elif k == "r":
                    pat = r"\br\b(?=\s*(?:lang|programming|studio)|\s*[,;/]|$)"
                else:
                    continue
        try:
            if re.search(pat, blob, flags=re.I):
                label = SKILL_TERMS[key]
                low = label.lower()
                if low not in seen:
                    seen.add(low)
                    found.append(label)
        except re.error:
            continue
        if len(found) >= limit:
            break
    return found


# Titles that are almost never right for AI/SWE seekers unless query asks for them
NON_TECH_TITLE_MARKERS = (
    "account development",
    "account executive",
    "account manager",
    "sales engineer",  # borderline - keep if "sales" in query
    "partner sales",
    "business development",
    "bdr",
    "sdr",
    "recruiter",
    "talent acquisition",
    "human resources",
    " hr ",
    "people operations",
    "marketing manager",
    "brand manager",
    "content creator",
    "copywriter",
    "customer experience",
    "customer success",
    "customer support",
    "technical support",
    "collections manager",
    "cluster collection",
    "compliance officer",
    "payroll",
    "legal counsel",
    "office manager",
    "receptionist",
    "intern - sales",
)

TECH_TITLE_MARKERS = (
    "engineer",
    "developer",
    "scientist",
    "architect",
    "sde",
    "swe",
    "ml ",
    "machine learning",
    "llm",
    "ai ",
    "data ",
    "backend",
    "front-end",
    "frontend",
    "full stack",
    "fullstack",
    "platform",
    "devops",
    "sre",
    "research",
    "infrastructure",
    "software",
    "systems",
    "applied ai",
    "agentic",
    "nlp",
)


def is_likely_non_tech_title(title: str) -> bool:
    t = f" {(title or '').lower()} "
    if any(m in t for m in NON_TECH_TITLE_MARKERS):
        # Exception: "sales engineer" might still be tech-adjacent; keep if also eng-heavy
        if "engineer" in t and "sales" in t:
            return True  # sales engineer is sales-primary for most seekers
        return True
    return False


def is_likely_tech_title(title: str) -> bool:
    t = f" {(title or '').lower()} "
    return any(m in t for m in TECH_TITLE_MARKERS)


def title_tokens(text: str) -> Set[str]:
    return {w for w in re.findall(r"[a-z0-9+#.]{2,}", (text or "").lower()) if w not in {
        "and", "the", "for", "with", "from", "senior", "junior", "staff", "lead",
        "remote", "hybrid", "india", "role", "roles", "job", "jobs", "find", "open",
    }}
