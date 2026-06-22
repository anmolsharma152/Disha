"""
Project Alpha-Nexus - Scraper Tools
LangChain-compatible tools for data acquisition layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import feedparser
from langchain_core.tools import tool
from pydantic import BaseModel, Field, HttpUrl, field_validator

logger = logging.getLogger("alpha_nexus.tools")


# ──────────────────────────────────────────────────────────────
# Input/Output Schemas
# ──────────────────────────────────────────────────────────────


class FetchRSSInput(BaseModel):
    """Input schema for fetch_financial_news_rss tool."""

    feed_url: HttpUrl = Field(..., description="RSS/Atom feed URL to fetch")
    max_items: int = Field(
        5, ge=1, le=50, description="Maximum number of items to return"
    )
    timeout: int = Field(10, ge=1, le=60, description="Request timeout in seconds")

    @field_validator("feed_url", mode="before")
    @classmethod
    def validate_feed_url(cls, v: str) -> str:
        """Basic URL validation."""
        parsed = urlparse(str(v))
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid feed URL")
        return v


class RSSArticle(BaseModel):
    """Single article from RSS feed."""

    title: str
    link: str
    published: Optional[str] = None
    summary: Optional[str] = None
    source_domain: str


class FetchRSSOutput(BaseModel):
    """Output schema for fetch_financial_news_rss tool."""

    articles: List[RSSArticle]
    feed_title: Optional[str] = None
    feed_url: str
    fetched_at: str
    total_available: int


# ──────────────────────────────────────────────────────────────
# LangChain Tool
# ──────────────────────────────────────────────────────────────


@tool("fetch_financial_news_rss", args_schema=FetchRSSInput, return_direct=False)
def fetch_financial_news_rss(
    feed_url: str,
    max_items: int = 5,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Fetch and parse an RSS/Atom feed, returning the top N articles.

    Args:
        feed_url: RSS/Atom feed URL (e.g., 'http://feeds.bbci.co.uk/news/rss.xml')
        max_items: Maximum number of articles to return (1-50)
        timeout: Request timeout in seconds

    Returns:
        Dictionary with articles list, feed metadata, and fetch timestamp
    """
    import datetime

    logger.info(f"Fetching RSS feed: {feed_url}")

    try:
        # Parse feed with feedparser
        feed = feedparser.parse(str(feed_url))

        if feed.bozo:
            logger.warning(f"Feed parsing warning: {feed.bozo_exception}")

        # feed.entries is a list, feed.feed is a dict-like object
        feed_entries = getattr(feed, "entries", [])
        feed_info = getattr(feed, "feed", {})

        if not feed_entries:
            logger.warning("No entries found in feed")
            return {
                "articles": [],
                "feed_title": feed_info.get("title")
                if isinstance(feed_info, dict)
                else None,
                "feed_url": str(feed_url),
                "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
                "total_available": 0,
            }

        # Extract source domain
        parsed = urlparse(str(feed_url))
        source_domain = parsed.netloc

        # Build articles list
        articles = []
        for entry in feed_entries[:max_items]:
            # entry is a dict-like object
            title = (
                entry.get("title", "No title")
                if hasattr(entry, "get")
                else str(getattr(entry, "title", "No title"))
            )
            link = (
                entry.get("link", "")
                if hasattr(entry, "get")
                else str(getattr(entry, "link", ""))
            )
            published = (
                entry.get("published") or entry.get("updated")
                if hasattr(entry, "get")
                else (
                    getattr(entry, "published", None) or getattr(entry, "updated", None)
                )
            )
            summary = (
                entry.get("summary") or entry.get("description")
                if hasattr(entry, "get")
                else (
                    getattr(entry, "summary", None)
                    or getattr(entry, "description", None)
                )
            )

            article = RSSArticle(
                title=title,
                link=link,
                published=published,
                summary=summary,
                source_domain=source_domain,
            )
            articles.append(article.model_dump())

        result = FetchRSSOutput(
            articles=articles,
            feed_title=feed_info.get("title") if isinstance(feed_info, dict) else None,
            feed_url=str(feed_url),
            fetched_at=datetime.datetime.utcnow().isoformat() + "Z",
            total_available=len(feed_entries),
        )

        logger.info(
            f"Successfully fetched {len(articles)} articles from {source_domain}"
        )
        return result.model_dump()

    except Exception as e:
        logger.error(f"RSS fetch failed: {type(e).__name__}: {e}")
        return {
            "articles": [],
            "feed_title": None,
            "feed_url": str(feed_url),
            "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
            "total_available": 0,
            "error": str(e),
        }


# ──────────────────────────────────────────────────────────────
# Additional Scraper Tools (Placeholders for Phase 1)
# ──────────────────────────────────────────────────────────────


class ScrapedPage(BaseModel):
    """Result from web scraping."""

    url: str
    html: str
    markdown: str
    metadata: Dict[str, Any]


class PlaywrightScrapeInput(BaseModel):
    """Input for Playwright-based scraping."""

    url: HttpUrl
    wait_for_selector: Optional[str] = None
    wait_for_timeout: int = Field(5000, ge=0, le=60000)
    extract_markdown: bool = True
    user_agent: Optional[str] = None


class BeautifulSoupScrapeInput(BaseModel):
    """Input for BeautifulSoup-based scraping."""

    url: HttpUrl
    extract_selectors: Optional[Dict[str, str]] = Field(
        None, description="CSS selectors for targeted extraction"
    )
    parse_tables: bool = False


class PlaywrightScrapeOutput(BaseModel):
    """Output for Playwright scraping."""

    url: str
    html: str
    markdown: str
    title: str
    metadata: Dict[str, Any]
    scraped_at: str


@tool(
    "fetch_webpage_playwright", args_schema=PlaywrightScrapeInput, return_direct=False
)
def fetch_webpage_playwright(
    url: HttpUrl,
    wait_for_selector: Optional[str] = None,
    wait_for_timeout: int = 5000,
    extract_markdown: bool = True,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Scrape a webpage using Playwright for JS-heavy content.

    Args:
        url: Webpage URL to scrape
        wait_for_selector: CSS selector to wait for before extracting
        wait_for_timeout: Max wait time in milliseconds
        extract_markdown: Whether to convert HTML to markdown
        user_agent: Custom user agent string

    Returns:
        Dictionary with html, markdown, title, and metadata
    """
    import datetime
    from playwright.sync_api import sync_playwright
    import markdownify
    from bs4 import BeautifulSoup

    # Convert HttpUrl to string (fixes Pydantic validation bug)
    url_str = str(url)
    logger.info(f"Playwright scraping live: {url_str}")

    html_content = ""
    page_title = ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=user_agent)
            page.goto(url_str, wait_until="domcontentloaded", timeout=30000)

            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=wait_for_timeout)
                except Exception as e:
                    logger.warning(
                        f"Timeout waiting for selector {wait_for_selector}: {e}"
                    )
            else:
                page.wait_for_timeout(wait_for_timeout)

            html_content = page.content()
            page_title = page.title()
            browser.close()

    except Exception as e:
        logger.error(f"Playwright execution error: {e}")
        return {
            "url": url_str,
            "html": "",
            "markdown": "",
            "title": "",
            "metadata": {"error": str(e)},
            "scraped_at": datetime.datetime.now().isoformat() + "Z",
        }

    markdown_text = ""
    if extract_markdown and html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        # Strip out noisy tags
        for element in soup(["script", "style", "nav", "footer", "header", "svg"]):
            element.decompose()
        clean_html = str(soup)
        markdown_text = markdownify.markdownify(clean_html, heading_style="ATX").strip()

    return PlaywrightScrapeOutput(
        url=url_str,
        html=html_content,
        markdown=markdown_text,
        title=page_title,
        metadata={
            "scraper": "playwright",
            "wait_for_selector": wait_for_selector,
        },
        scraped_at=datetime.datetime.now().isoformat() + "Z",
    ).model_dump()


# Placeholder tool signatures (to be implemented)
# @tool("scrape_with_beautifulsoup", args_schema=BeautifulSoupScrapeInput)
# def scrape_with_beautifulsoup(...):
#     """Fast static HTML scraping with BeautifulSoup."""
#     pass


# ──────────────────────────────────────────────────────────────
# Tool Registry
# ──────────────────────────────────────────────────────────────

SCRAPER_TOOLS = [
    fetch_financial_news_rss,
    fetch_webpage_playwright,
    # scrape_with_beautifulsoup,
]

TOOL_MAP = {t.name: t for t in SCRAPER_TOOLS}


def get_tool(name: str):
    """Retrieve tool by name."""
    return TOOL_MAP.get(name)


def list_tools() -> List[str]:
    """List available tool names."""
    return list(TOOL_MAP.keys())


# ──────────────────────────────────────────────────────────────
# Test Block
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    # Test with BBC News RSS feed
    BBC_NEWS_RSS = "http://feeds.bbci.co.uk/news/rss.xml"

    print("=" * 60)
    print("Testing fetch_financial_news_rss tool")
    print("=" * 60)
    print(f"Feed: {BBC_NEWS_RSS}")
    print()

    # Call the tool directly (not via LangChain runtime)
    result = fetch_financial_news_rss.invoke(
        {
            "feed_url": BBC_NEWS_RSS,
            "max_items": 5,
        }
    )

    # Pretty print
    print(f"Feed Title: {result.get('feed_title')}")
    print(f"Fetched At: {result.get('fetched_at')}")
    print(f"Total Available: {result.get('total_available')}")
    print(f"Returned: {len(result.get('articles', []))}")
    print()

    for i, article in enumerate(result.get("articles", []), 1):
        print(f"{i}. {article['title']}")
        print(f"   Link: {article['link']}")
        if article.get("published"):
            print(f"   Published: {article['published']}")
        print()

    # Verify structure
    assert "articles" in result
    assert isinstance(result["articles"], list)
    assert len(result["articles"]) <= 5
    for article in result["articles"]:
        assert "title" in article
        assert "link" in article
        assert "source_domain" in article

    print("=" * 60)
    print("✓ All assertions passed - tool works correctly!")
    print("=" * 60)
