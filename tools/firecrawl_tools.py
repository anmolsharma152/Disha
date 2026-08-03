"""
Disha - Firecrawl Scraper Tools
LangChain-compatible tools for cloud-based web scraping, site mapping, and schema extraction via Firecrawl API.
"""

from __future__ import annotations

import logging
import os
import datetime
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field, HttpUrl, field_validator

from tools.scraper_tools import is_safe_url

logger = logging.getLogger("disha.tools.firecrawl")

# Lazy import check for firecrawl
try:
    from firecrawl import FirecrawlApp
    HAS_FIRECRAWL = True
except ImportError:
    FirecrawlApp = None
    HAS_FIRECRAWL = False


def get_firecrawl_client() -> Optional[Any]:
    """Retrieve an initialized FirecrawlApp client if API key and package exist."""
    if not HAS_FIRECRAWL:
        logger.warning("[Firecrawl] firecrawl-py package is not installed.")
        return None
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logger.warning("[Firecrawl] FIRECRAWL_API_KEY environment variable is not set.")
        return None
    try:
        return FirecrawlApp(api_key=api_key)
    except Exception as e:
        logger.error("[Firecrawl] Failed to initialize FirecrawlApp: %s", e)
        return None


# ──────────────────────────────────────────────────────────────
# Pydantic Input/Output Schemas
# ──────────────────────────────────────────────────────────────


class FirecrawlScrapeInput(BaseModel):
    url: HttpUrl = Field(..., description="Target webpage URL to scrape via Firecrawl")
    extract_markdown: bool = Field(True, description="Whether to extract page markdown")

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        s = str(v)
        if not is_safe_url(s):
            raise ValueError(f"SSRF Protection: Access to URL '{s}' is blocked.")
        return s


class FirecrawlMapInput(BaseModel):
    url: HttpUrl = Field(..., description="Base company career URL to map (e.g., https://company.com/careers)")
    search_keyword: Optional[str] = Field("engineer|developer|ml|ai|data", description="Keyword filter for sub-URLs")

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        s = str(v)
        if not is_safe_url(s):
            raise ValueError(f"SSRF Protection: Access to URL '{s}' is blocked.")
        return s


class FirecrawlSearchInput(BaseModel):
    query: str = Field(..., description="Job search query (e.g. 'Agentic AI Engineer Bangalore')")
    limit: int = Field(10, ge=1, le=30, description="Max search results to return")


# ──────────────────────────────────────────────────────────────
# LangChain Compatible Tools
# ──────────────────────────────────────────────────────────────


@tool("fetch_webpage_firecrawl", args_schema=FirecrawlScrapeInput, return_direct=False)
def fetch_webpage_firecrawl(url: HttpUrl, extract_markdown: bool = True) -> Dict[str, Any]:
    """
    Scrape a webpage via Firecrawl cloud API for dynamic JS rendering.

    Args:
        url: Webpage URL to scrape
        extract_markdown: Whether to convert page content to markdown

    Returns:
        Dict with url, markdown, metadata, and fetch timestamp
    """
    url_str = str(url)
    client = get_firecrawl_client()
    if not client:
        return {
            "url": url_str,
            "markdown": "",
            "metadata": {"error": "Firecrawl client uninitialized (missing API key or package)"},
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    try:
        logger.info("[Firecrawl] Scraping URL: %s", url_str)
        response = client.scrape_url(url_str, params={"formats": ["markdown"] if extract_markdown else ["html"]})
        
        # Firecrawl responses can be dict or object
        markdown_content = ""
        metadata = {}
        if isinstance(response, dict):
            markdown_content = response.get("markdown") or response.get("content") or ""
            metadata = response.get("metadata") or {}
        else:
            markdown_content = getattr(response, "markdown", "") or getattr(response, "content", "")
            metadata = getattr(response, "metadata", {}) or {}

        return {
            "url": url_str,
            "markdown": markdown_content,
            "title": metadata.get("title", ""),
            "metadata": metadata,
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("[Firecrawl] Scrape failed for %s: %s", url_str, e)
        return {
            "url": url_str,
            "markdown": "",
            "metadata": {"error": str(e)},
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


@tool("map_company_careers_firecrawl", args_schema=FirecrawlMapInput, return_direct=False)
def map_company_careers_firecrawl(url: HttpUrl, search_keyword: Optional[str] = "engineer|developer|ml|ai|data") -> Dict[str, Any]:
    """
    Map all relevant sub-URLs under a company's career section via Firecrawl map_url().

    Args:
        url: Career base URL (e.g. https://razorpay.com/jobs)
        search_keyword: Regex / keyword filter for sub-URLs

    Returns:
        Dict with list of discovered job posting URLs
    """
    url_str = str(url)
    client = get_firecrawl_client()
    if not client:
        return {"url": url_str, "links": [], "error": "Firecrawl client uninitialized"}

    try:
        logger.info("[Firecrawl] Mapping career portal: %s", url_str)
        params = {}
        if search_keyword:
            params["search"] = search_keyword
            
        res = client.map_url(url_str, params=params)
        links = []
        if isinstance(res, dict):
            links = res.get("links") or res.get("urls") or []
        else:
            links = getattr(res, "links", []) or getattr(res, "urls", []) or []

        return {
            "url": url_str,
            "links": list(links)[:25],
            "total_found": len(links),
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("[Firecrawl] Map failed for %s: %s", url_str, e)
        return {"url": url_str, "links": [], "error": str(e)}


@tool("search_jobs_firecrawl", args_schema=FirecrawlSearchInput, return_direct=False)
def search_jobs_firecrawl(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Execute web-wide search for job postings via Firecrawl search API.

    Args:
        query: Role/company search query
        limit: Max results

    Returns:
        Dict with search hits containing URLs, titles, and snippets
    """
    client = get_firecrawl_client()
    if not client:
        return {"query": query, "results": [], "error": "Firecrawl client uninitialized"}

    try:
        logger.info("[Firecrawl] Executing search for: '%s'", query)
        res = client.search(query, params={"limit": limit})
        results = []
        if isinstance(res, dict):
            results = res.get("data") or res.get("results") or []
        else:
            results = getattr(res, "data", []) or getattr(res, "results", []) or []

        return {
            "query": query,
            "results": results,
            "total": len(results),
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("[Firecrawl] Search failed for '%s': %s", query, e)
        return {"query": query, "results": [], "error": str(e)}
