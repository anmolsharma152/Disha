"""
Disha - Firecrawl Scraper Tools Unit Tests
"""

import pytest
from tools.firecrawl_tools import (
    fetch_webpage_firecrawl,
    map_company_careers_firecrawl,
    search_jobs_firecrawl,
)


def test_firecrawl_uninitialized_graceful_handling(monkeypatch):
    """Verify Firecrawl tools handle missing API keys gracefully without crashing."""
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    res_scrape = fetch_webpage_firecrawl.invoke({"url": "https://example.com/careers"})
    assert isinstance(res_scrape, dict)
    assert res_scrape["url"] == "https://example.com/careers"
    assert "error" in res_scrape["metadata"]

    res_map = map_company_careers_firecrawl.invoke({"url": "https://example.com/careers"})
    assert isinstance(res_map, dict)
    assert res_map["links"] == []
    assert "error" in res_map

    res_search = search_jobs_firecrawl.invoke({"query": "AI Engineer Bangalore"})
    assert isinstance(res_search, dict)
    assert res_search["results"] == []
    assert "error" in res_search


def test_firecrawl_ssrf_blocked():
    """Verify Firecrawl tools enforce SSRF URL validation."""
    with pytest.raises(ValueError):
        fetch_webpage_firecrawl.invoke({"url": "http://169.254.169.254/latest/meta-data/"})

    with pytest.raises(ValueError):
        map_company_careers_firecrawl.invoke({"url": "http://127.0.0.1:8000/internal"})
