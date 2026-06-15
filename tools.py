"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size is not None:
        size_lower = size.lower()
        listings = [l for l in listings if size_lower in l["size"].lower()]

    _stopwords = {
        "looking", "for", "a", "an", "the", "under", "size", "want", "need",
    }
    keywords = [
        w.lower() for w in description.split()
        if len(w) > 2 and w.lower() not in _stopwords
    ]

    def score(listing):
        text = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            " ".join(listing.get("style_tags", [])),
        ]).lower()
        return sum(
            1 for kw in keywords
            if re.search(r'\b' + re.escape(kw) + r'\b', text)
        )

    scored = [(score(l), l) for l in listings]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    item_header = (
        f"Title: {new_item.get('title', '')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = (
            f"I'm considering buying this thrifted item:\n{item_header}\n\n"
            f"I don't have an existing wardrobe to pull from. "
            f"Give me general styling advice for this piece — what kinds of items pair well with it, "
            f"what vibe it suits, and a couple of ways someone could wear it."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {item['name']} ({', '.join(item.get('colors', []))})"
            + (f" — {item['notes']}" if item.get("notes") else "")
            for item in wardrobe_items
        )
        prompt = (
            f"I'm considering buying this thrifted item:\n{item_header}\n\n"
            f"Here are pieces I already own:\n{wardrobe_lines}\n\n"
            f"Suggest 1-2 specific outfit combinations using the new item paired with "
            f"named pieces from my wardrobe above. Be specific about which pieces to combine."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            f"Couldn't generate styling suggestions right now. "
            f"Try pairing the {new_item.get('title', 'item')} with basics in similar colors."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return (
            "I can't write a fit card without a complete outfit. Try rerunning the styling "
            "suggestion so I've got a full look to describe, and I'll caption it for you."
        )

    prompt = (
        f"Write a 2-4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
        f"Thrifted item: {new_item.get('title', 'a thrifted find')}\n"
        f"Price: ${new_item.get('price', '?')}\n"
        f"Platform: {new_item.get('platform', 'a thrift platform')}\n"
        f"Outfit: {outfit}\n\n"
        f"Rules:\n"
        f"- Sound like a real casual OOTD post, not a product description\n"
        f"- Mention the item name, price, and platform naturally — each once\n"
        f"- Capture the specific vibe of the outfit\n"
        f"- Keep it 2-4 sentences"
    )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            f"Couldn't generate a fit card right now. "
            f"Your {new_item.get('title', 'find')} from {new_item.get('platform', 'the thrift store')} "
            f"sounds like a great look though."
        )
