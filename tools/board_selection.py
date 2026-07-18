"""
Disha - Query-aware ATS board selection.

Maps a user query to Greenhouse/Lever boards, title-filter keywords,
and optional side channels (RSS / Playwright) so the scraper does not
always hit the same hardcoded company list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Sequence, Tuple


# ──────────────────────────────────────────────────────────────
# Catalog (board slugs verified against public Greenhouse API where noted)
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BoardEntry:
    """One ATS career board."""

    company: str
    board: str
    source: Literal["greenhouse", "lever"]
    aliases: Tuple[str, ...]
    tags: frozenset[str]
    # Prefer in default career scrapes when no company is named
    default: bool = False


# tags: india | ai | ml | fintech | infra | data | product | remote_friendly
GREENHOUSE_CATALOG: Tuple[BoardEntry, ...] = (
    # India / India-hiring product companies (live boards)
    BoardEntry("PhonePe", "phonepe", "greenhouse", ("phonepe", "phone pe"), frozenset({"india", "fintech", "backend"}), True),
    BoardEntry("Postman", "postman", "greenhouse", ("postman",), frozenset({"india", "developer_tools", "backend", "ai"}), True),
    BoardEntry("Druva", "druva", "greenhouse", ("druva",), frozenset({"india", "infra", "security", "backend"}), True),
    # Global AI / ML platforms (often hire remotely / India-friendly)
    BoardEntry("Anthropic", "anthropic", "greenhouse", ("anthropic", "claude"), frozenset({"ai", "ml", "llm"}), True),
    BoardEntry("Databricks", "databricks", "greenhouse", ("databricks",), frozenset({"ai", "ml", "data", "infra"}), True),
    BoardEntry("Scale AI", "scaleai", "greenhouse", ("scale ai", "scaleai"), frozenset({"ai", "ml", "data"}), True),
    BoardEntry("Stripe", "stripe", "greenhouse", ("stripe",), frozenset({"fintech", "backend", "infra"}), False),
    BoardEntry("Cloudflare", "cloudflare", "greenhouse", ("cloudflare",), frozenset({"infra", "backend", "security"}), False),
    BoardEntry("Datadog", "datadog", "greenhouse", ("datadog",), frozenset({"infra", "backend", "observability"}), False),
    BoardEntry("MongoDB", "mongodb", "greenhouse", ("mongodb", "mongo"), frozenset({"data", "backend", "infra"}), False),
    BoardEntry("Vercel", "vercel", "greenhouse", ("vercel",), frozenset({"infra", "frontend", "backend"}), False),
    BoardEntry("Twilio", "twilio", "greenhouse", ("twilio",), frozenset({"backend", "infra", "product"}), False),
    BoardEntry("GitLab", "gitlab", "greenhouse", ("gitlab",), frozenset({"infra", "backend", "developer_tools"}), False),
    BoardEntry("Elastic", "elastic", "greenhouse", ("elastic", "elasticsearch"), frozenset({"data", "infra", "search"}), False),
    BoardEntry("Figma", "figma", "greenhouse", ("figma",), frozenset({"product", "frontend"}), False),
    BoardEntry("Airbnb", "airbnb", "greenhouse", ("airbnb",), frozenset({"product", "backend", "ml"}), False),
    BoardEntry("Coinbase", "coinbase", "greenhouse", ("coinbase",), frozenset({"fintech", "backend"}), False),
    BoardEntry("Brex", "brex", "greenhouse", ("brex",), frozenset({"fintech", "backend"}), False),
    BoardEntry("Affirm", "affirm", "greenhouse", ("affirm",), frozenset({"fintech", "backend"}), False),
    BoardEntry("Adyen", "adyen", "greenhouse", ("adyen",), frozenset({"fintech", "backend"}), False),
    BoardEntry("Fivetran", "fivetran", "greenhouse", ("fivetran",), frozenset({"data", "infra"}), False),
    BoardEntry("PlanetScale", "planetscale", "greenhouse", ("planetscale",), frozenset({"data", "infra"}), False),
    BoardEntry("Hightouch", "hightouch", "greenhouse", ("hightouch",), frozenset({"data"}), False),
    BoardEntry("Samsara", "samsara", "greenhouse", ("samsara",), frozenset({"infra", "ml"}), False),
    BoardEntry("Waymo", "waymo", "greenhouse", ("waymo",), frozenset({"ml", "ai"}), False),
    BoardEntry("Remote.com", "remotecom", "greenhouse", ("remote.com", "remotecom"), frozenset({"remote_friendly", "product"}), False),
    BoardEntry("New Relic", "newrelic", "greenhouse", ("new relic", "newrelic"), frozenset({"observability", "infra"}), False),
    BoardEntry("Block", "block", "greenhouse", ("block", "square", "squareup"), frozenset({"fintech", "backend"}), False),
    BoardEntry("Robinhood", "robinhood", "greenhouse", ("robinhood",), frozenset({"fintech", "backend"}), False),
    BoardEntry("Lyft", "lyft", "greenhouse", ("lyft",), frozenset({"backend", "ml"}), False),
)

LEVER_CATALOG: Tuple[BoardEntry, ...] = (
    BoardEntry("Groww", "groww", "lever", ("groww",), frozenset({"india", "fintech"}), True),
    BoardEntry("Dunzo", "dunzo", "lever", ("dunzo",), frozenset({"india", "backend"}), False),
    BoardEntry("Unacademy", "unacademy", "lever", ("unacademy",), frozenset({"india", "edtech"}), False),
    BoardEntry("UpGrad", "upgrad", "lever", ("upgrad", "upgrad"), frozenset({"india", "edtech"}), False),
)

# Playwright career pages (no reliable public JSON board). Only used when named.
PLAYWRIGHT_COMPANY_URLS: Dict[str, Tuple[str, ...]] = {
    "openai": ("https://boards.greenhouse.io/openai",),
    "razorpay": ("https://razorpay.com/jobs/",),
    "swiggy": ("https://careers.swiggy.com/",),
    "zomato": ("https://www.zomato.com/careers",),
    "cred": ("https://careers.cred.club/",),
}

FINANCIAL_TERMS = (
    "invest",
    "investment",
    "stock",
    "financial",
    "finance",
    "valuation",
    "market cap",
    "burn",
    "runway",
    "esop",
    "funding",
    "series a",
    "series b",
    "ipo",
    "risk flag",
)

# Query terms → title/description filters (OR). Longer phrases first when matching.
TOPIC_KEYWORDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("agentic", ("agentic", "multi-agent", "langgraph", "autonomous agent")),
    ("llmops", ("llmops", "mlops", "model serving", "vllm")),
    ("llm", ("llm", "large language", "generative ai", "genai", "gpt")),
    ("rag", ("rag", "retrieval")),
    ("machine learning", ("machine learning", "ml engineer", "deep learning")),
    ("ml ", ("machine learning", "ml engineer", " ml")),
    ("data science", ("data science", "data scientist")),
    ("data engineer", ("data engineer", "data platform", "etl")),
    ("backend", ("backend", "back-end", "back end", "platform engineer")),
    ("frontend", ("frontend", "front-end", "front end", "react")),
    ("full stack", ("full stack", "fullstack", "full-stack")),
    ("devops", ("devops", "sre", "platform engineer", "infrastructure")),
    ("kubernetes", ("kubernetes", "k8s", "sre")),
    ("security", ("security", "appsec", "infosec")),
    ("product manager", ("product manager", "product management", " pm ")),
    ("ai ", ("ai engineer", "artificial intelligence", "ml engineer", "llm")),
    ("nlp", ("nlp", "natural language")),
    ("computer vision", ("computer vision", "cv engineer")),
)

INDIA_TERMS = (
    "india",
    "indian",
    "bangalore",
    "bengaluru",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "pune",
    "hyderabad",
    "chennai",
    "mumbai",
    "remote india",
    "lpa",
    "inr",
)


@dataclass
class ScrapePlan:
    """Resolved scrape targets for one user query."""

    greenhouse: List[Tuple[str, str]] = field(default_factory=list)  # (company, board)
    lever: List[Tuple[str, str]] = field(default_factory=list)
    title_keywords: List[str] = field(default_factory=list)
    fetch_rss: bool = False
    playwright_urls: List[str] = field(default_factory=list)
    max_results_per_board: int = 20
    prefer_india_locations: bool = True
    reasons: List[str] = field(default_factory=list)

    @property
    def total_boards(self) -> int:
        return len(self.greenhouse) + len(self.lever)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _alias_in_query(query: str, alias: str) -> bool:
    """Match company alias with simple word-boundary rules."""
    alias = alias.lower().strip()
    if not alias:
        return False
    if " " in alias or "." in alias:
        return alias in query
    return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", query) is not None


def extract_mentioned_companies(
    query: str,
    catalog: Sequence[BoardEntry],
) -> List[BoardEntry]:
    """Return catalog entries whose aliases appear in the query."""
    q = _normalize(query)
    hits: List[BoardEntry] = []
    seen_boards: set[str] = set()
    # Longer aliases first so "scale ai" wins over "scale"
    ranked = sorted(catalog, key=lambda e: -max(len(a) for a in e.aliases))
    for entry in ranked:
        if entry.board in seen_boards:
            continue
        if any(_alias_in_query(q, a) for a in entry.aliases):
            hits.append(entry)
            seen_boards.add(entry.board)
    return hits


def extract_title_keywords(query: str) -> List[str]:
    """Extract role/tech filters from free text (deduped, stable order)."""
    q = _normalize(query)
    found: List[str] = []
    seen: set[str] = set()
    for needle, expansions in TOPIC_KEYWORDS:
        if needle in q:
            for term in expansions:
                t = term.strip().lower()
                if t and t not in seen:
                    seen.add(t)
                    found.append(t)
    return found


def is_financial_query(query: str) -> bool:
    q = _normalize(query)
    return any(term in q for term in FINANCIAL_TERMS)


def wants_india_focus(query: str) -> bool:
    q = _normalize(query)
    # Default product focus is India; only relax when user clearly wants global/US
    if any(x in q for x in ("united states", " us ", "usa", "bay area", "sf ", "silicon valley")):
        if not any(t in q for t in INDIA_TERMS):
            return False
    return True


def _dedupe_entries(entries: Sequence[BoardEntry]) -> List[BoardEntry]:
    seen: set[Tuple[str, str]] = set()
    out: List[BoardEntry] = []
    for e in entries:
        key = (e.source, e.board)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _default_career_boards(
    prefer_india: bool,
    title_keywords: Sequence[str],
    max_greenhouse: int,
    max_lever: int,
) -> Tuple[List[BoardEntry], List[BoardEntry]]:
    """Pick a focused default set when no company is named."""
    gh = [e for e in GREENHOUSE_CATALOG if e.default]
    lv = [e for e in LEVER_CATALOG if e.default]

    # If query is AI/ML heavy, boost AI-tagged defaults and drop pure fintech defaults last
    ai_heavy = any(
        k in {"agentic", "llm", "llmops", "rag", "machine learning", "ml engineer", "generative ai", "genai"}
        for k in title_keywords
    ) or any(
        t in " ".join(title_keywords)
        for t in ("langgraph", "langchain", "multi-agent")
    )

    def score(entry: BoardEntry) -> Tuple[int, int, str]:
        s = 0
        if prefer_india and "india" in entry.tags:
            s += 10
        if ai_heavy and ({"ai", "ml", "llm"} & entry.tags):
            s += 8
        if entry.default:
            s += 3
        if prefer_india and "india" not in entry.tags and not ai_heavy:
            s -= 2
        return (-s, len(entry.company), entry.company)

    gh_sorted = sorted(gh, key=score)
    lv_sorted = sorted(lv, key=score)

    # If AI-heavy and we still have room, add more AI boards beyond default flag
    if ai_heavy:
        extras = [
            e
            for e in GREENHOUSE_CATALOG
            if not e.default and ({"ai", "ml", "llm"} & e.tags)
        ]
        for e in sorted(extras, key=score):
            if e.board not in {x.board for x in gh_sorted}:
                gh_sorted.append(e)

    return gh_sorted[:max_greenhouse], lv_sorted[:max_lever]


def select_scrape_plan(
    query: str,
    *,
    max_greenhouse: int = 6,
    max_lever: int = 3,
    max_results_per_board: int = 20,
    fallback: bool = False,
) -> ScrapePlan:
    """
    Build a scrape plan from the user query.

    Rules:
    - Named companies → only those boards (plus Playwright URLs if catalog has them).
    - Career/default → curated default India + AI boards.
    - Financial intent → RSS on; light/no ATS unless a company is named.
    - Title keywords from query used as post-fetch OR filters.
    - fallback=True → broader board set, drop topic filters, relax India preference.
    """
    if fallback:
        max_greenhouse = max(max_greenhouse, 10)
        max_lever = max(max_lever, 4)
        max_results_per_board = max(max_results_per_board, 30)

    q = _normalize(query)
    plan = ScrapePlan(max_results_per_board=max_results_per_board)
    plan.title_keywords = extract_title_keywords(query)
    plan.prefer_india_locations = wants_india_focus(query)
    financial = is_financial_query(query)

    mentioned_gh = extract_mentioned_companies(query, GREENHOUSE_CATALOG)
    mentioned_lv = extract_mentioned_companies(query, LEVER_CATALOG)

    # Playwright companies not in Greenhouse catalog
    for name, urls in PLAYWRIGHT_COMPANY_URLS.items():
        if _alias_in_query(q, name):
            plan.playwright_urls.extend(urls)
            plan.reasons.append(f"playwright:{name}")

    if mentioned_gh or mentioned_lv or plan.playwright_urls:
        plan.greenhouse = [(e.company, e.board) for e in mentioned_gh[:max_greenhouse]]
        plan.lever = [(e.company, e.board) for e in mentioned_lv[:max_lever]]
        plan.reasons.append("company_match")
        # Company-specific: still allow RSS if purely financial about that co
        plan.fetch_rss = financial and not (plan.greenhouse or plan.lever)
        if financial:
            plan.reasons.append("financial_with_company")
        if fallback:
            # Named company failed once — broaden beyond that company
            plan.reasons.append("fallback_broaden")
            plan.title_keywords = []
            plan.prefer_india_locations = False
            gh, lv = _default_career_boards(
                prefer_india=False,
                title_keywords=[],
                max_greenhouse=max_greenhouse,
                max_lever=max_lever,
            )
            # Keep named boards first, then defaults
            seen_gh = {b for _, b in plan.greenhouse}
            seen_lv = {b for _, b in plan.lever}
            for e in gh:
                if e.board not in seen_gh:
                    plan.greenhouse.append((e.company, e.board))
                    seen_gh.add(e.board)
            for e in lv:
                if e.board not in seen_lv:
                    plan.lever.append((e.company, e.board))
                    seen_lv.add(e.board)
            plan.greenhouse = plan.greenhouse[:max_greenhouse]
            plan.lever = plan.lever[:max_lever]
        return plan

    if financial and not fallback:
        plan.fetch_rss = True
        plan.reasons.append("financial_rss_only")
        # Optional light AI company scrape for "invest in Indian AI" style queries
        if any(t in q for t in ("ai", "ml", "llm", "startup", "tech")):
            gh, _ = _default_career_boards(
                prefer_india=plan.prefer_india_locations,
                title_keywords=plan.title_keywords or ["ai"],
                max_greenhouse=min(3, max_greenhouse),
                max_lever=0,
            )
            plan.greenhouse = [(e.company, e.board) for e in gh]
            plan.reasons.append("financial_light_ats")
        return plan

    # Default career path (or full fallback career path)
    if fallback:
        plan.title_keywords = []
        plan.prefer_india_locations = False
        plan.fetch_rss = False
        # Use most of the catalog, not only default=True
        gh_all = list(GREENHOUSE_CATALOG)[:max_greenhouse]
        lv_all = list(LEVER_CATALOG)[:max_lever]
        plan.greenhouse = [(e.company, e.board) for e in gh_all]
        plan.lever = [(e.company, e.board) for e in lv_all]
        plan.reasons.append("fallback_career")
        return plan

    gh, lv = _default_career_boards(
        prefer_india=plan.prefer_india_locations,
        title_keywords=plan.title_keywords,
        max_greenhouse=max_greenhouse,
        max_lever=max_lever,
    )
    plan.greenhouse = [(e.company, e.board) for e in gh]
    plan.lever = [(e.company, e.board) for e in lv]
    plan.fetch_rss = False
    plan.reasons.append("default_career")
    if plan.title_keywords:
        plan.reasons.append("topic_filters:" + ",".join(plan.title_keywords[:5]))
    if plan.prefer_india_locations:
        plan.reasons.append("india_focus")
    return plan


def job_matches_keywords(
    job: Dict,
    keywords: Sequence[str],
) -> bool:
    """
    OR-match keywords against title, description, and skill fields.
    Empty keywords → always True (no topic filter).
    """
    if not keywords:
        return True
    title = (job.get("title") or "").lower()
    desc = (job.get("description_raw") or job.get("description") or "").lower()
    skills = " ".join(job.get("skills_required") or []) + " " + " ".join(
        job.get("tech_stack") or []
    )
    blob = f"{title} {desc} {skills.lower()}"
    return any(kw.lower() in blob for kw in keywords)


def job_matches_india_preference(job: Dict, prefer_india: bool) -> bool:
    """Soft India filter: when prefer_india, keep India/remote/unknown; drop clear US-only if many locals exist is done by caller — here we only hard-drop obvious US-only when location is explicit."""
    if not prefer_india:
        return True
    loc = (job.get("location_raw") or "").lower()
    country = (job.get("location_country") or job.get("country") or "").lower()
    if country in ("in", "india"):
        return True
    if any(c in loc for c in INDIA_TERMS if len(c) > 3):
        return True
    if "remote" in loc and "us" not in loc and "united states" not in loc:
        return True
    # Explicit US-only locations when we want India
    us_markers = (
        "united states",
        "usa",
        "san francisco",
        "new york",
        "seattle",
        "austin",
        "bay area",
        "palo alto",
        "mountain view",
    )
    if any(m in loc for m in us_markers) and not any(
        c in loc for c in ("india", "bangalore", "bengaluru", "hyderabad", "remote - india")
    ):
        return False
    # Unknown / empty location: keep (normalizer may fill later)
    return True
