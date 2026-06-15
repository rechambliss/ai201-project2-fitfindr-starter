"""Tests for the three FitFindr tools."""

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_listings_returns_results():
    results = search_listings("vintage graphic tee", max_price=50)
    assert len(results) > 0


def test_search_listings_impossible_query_returns_empty_list():
    # Gibberish query + tight constraints — must return [] and not raise
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_listings_price_filter():
    results = search_listings("tee", max_price=20)
    assert len(results) > 0
    for item in results:
        assert item["price"] <= 20


# ── suggest_outfit ────────────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe_returns_nonempty_string():
    # Uses a real listing so the prompt has meaningful item details
    listing = search_listings("vintage graphic tee", max_price=50)[0]
    result = suggest_outfit(listing, get_empty_wardrobe())
    assert isinstance(result, str) and len(result.strip()) > 0


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit_returns_error_message():
    # Empty outfit hits the guard before any LLM call — no API key needed
    listing = search_listings("vintage graphic tee", max_price=50)[0]
    result = create_fit_card("", listing)
    assert isinstance(result, str) and len(result.strip()) > 0
