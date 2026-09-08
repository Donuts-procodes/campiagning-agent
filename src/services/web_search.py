from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DDG_HTML_URL = "https://html.duckduckgo.com/html/"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Execute zero-key live web search via DuckDuckGo and return structured snippets.

    Args:
        query: The search query string.
        max_results: Max number of result snippets to return (default 5).

    Returns:
        List of dicts: [{"title": ..., "snippet": ..., "url": ...}]
    """
    if not query or not query.strip():
        return []

    clean_query = query.strip()
    encoded_query = urllib.parse.quote(clean_query)
    url = f"{DDG_HTML_URL}?q={encoded_query}"

    try:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=7.0, follow_redirects=True) as client:
            res = await client.get(url)
            if res.status_code != 200:
                logger.warning(f"DuckDuckGo search returned HTTP {res.status_code} for query: {clean_query}")
                return []

            html = res.text
            # Extract snippets and URLs
            raw_snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, flags=re.DOTALL)
            raw_urls = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"', html)
            raw_titles = re.findall(r'<a class="result__url"[^>]*>(.*?)</a>', html, flags=re.DOTALL)

            results: list[dict[str, str]] = []
            count = min(len(raw_snippets), max_results)

            for i in range(count):
                snippet_text = re.sub(r"<[^>]+>", "", raw_snippets[i]).strip().replace("\n", " ")
                snippet_text = re.sub(r"\s+", " ", snippet_text)

                url_text = raw_urls[i].strip() if i < len(raw_urls) else ""
                title_text = (
                    re.sub(r"<[^>]+>", "", raw_titles[i]).strip()
                    if i < len(raw_titles)
                    else clean_query
                )

                if snippet_text:
                    results.append({
                        "title": title_text,
                        "snippet": snippet_text,
                        "url": url_text,
                    })

            logger.info(f"Live web search fetched {len(results)} items for query '{clean_query}'")
            return results

    except Exception as e:
        logger.warning(f"Web search failed for query '{clean_query}': {e}")
        return []


async def perform_market_research(
    company_name: str,
    product_service: str,
    target_icp: str,
    competitors: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Synthesize 2-3 focused market research queries and aggregate live findings."""
    queries = [
        f"{company_name} {product_service} latest news",
        f"{target_icp} market trends and challenges 2026",
    ]
    if competitors:
        comp_str = " ".join(competitors[:2])
        queries.append(f"{comp_str} alternatives vs {product_service} comparison")

    aggregated: list[dict[str, Any]] = []
    for q in queries:
        items = await search_web(q, max_results=3)
        for it in items:
            it["query"] = q
            aggregated.append(it)

    return aggregated
