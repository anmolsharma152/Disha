"""
Disha - Security & Multi-User Isolation Tests
"""

import pytest
from tools.scraper_tools import is_safe_url, validate_board_slug
from storage.user_memory import load_memory, save_memory, clear_memory, get_profile


def test_is_safe_url_valid():
    """Verify safe HTTP/HTTPS public URLs are allowed."""
    assert is_safe_url("https://boards.greenhouse.io/openai") is True
    assert is_safe_url("https://jobs.lever.co/anthropic") is True
    assert is_safe_url("http://feeds.bbci.co.uk/news/rss.xml") is True


def test_is_safe_url_ssrf_blocked():
    """Verify private/internal IPs, localhost, and AWS metadata URLs are blocked."""
    assert is_safe_url("http://127.0.0.1/admin") is False
    assert is_safe_url("http://localhost:8000/api") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://10.0.0.1/secret") is False
    assert is_safe_url("http://192.168.1.1/router") is False
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("gopher://localhost:70/") is False


def test_validate_board_slug_valid():
    """Verify alphanumeric slugs are accepted."""
    assert validate_board_slug("openai") == "openai"
    assert validate_board_slug("razorpay-tech_1") == "razorpay-tech_1"


def test_validate_board_slug_invalid():
    """Verify path traversal and malicious slugs raise ValueError."""
    with pytest.raises(ValueError):
        validate_board_slug("../../../etc/passwd")
    with pytest.raises(ValueError):
        validate_board_slug("openai; rm -rf /")
    with pytest.raises(ValueError):
        validate_board_slug("openai/jobs")


def test_multi_user_isolation():
    """Verify distinct user IDs maintain completely isolated memory without leakage."""
    user_a = "user_test_alpha"
    user_b = "user_test_beta"

    # Cleanup before test
    clear_memory(user_a)
    clear_memory(user_b)

    # User A profile
    save_memory({"profile": {"display_name": "Alice", "skills": ["Python", "PyTorch"]}}, user_id=user_a)
    # User B profile
    save_memory({"profile": {"display_name": "Bob", "skills": ["Java", "Spring"]}}, user_id=user_b)

    # Verify User A data
    prof_a = get_profile(user_a)
    assert prof_a["display_name"] == "Alice"
    assert "Python" in prof_a["skills"]
    assert "Java" not in prof_a["skills"]

    # Verify User B data
    prof_b = get_profile(user_b)
    assert prof_b["display_name"] == "Bob"
    assert "Java" in prof_b["skills"]
    assert "Python" not in prof_b["skills"]

    # Cleanup after test
    clear_memory(user_a)
    clear_memory(user_b)
