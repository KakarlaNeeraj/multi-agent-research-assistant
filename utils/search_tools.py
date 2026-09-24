import os
from typing import List, Dict


def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Search the web using Tavily if TAVILY_API_KEY exists,
    otherwise fall back to DuckDuckGo (ddgs).

    Returns ONLY real results with real http(s) URLs. If nothing is found it
    returns an empty list - it never invents results or builds URLs itself.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    results: List[Dict[str, str]] = []

    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            res = client.search(query=query, max_results=max_results)
            for r in res.get("results", []):
                results.append({
                    "title": r.get("title", "Web Source"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                })
            if results:
                return _only_real_urls(results)
        except Exception as e:
            print(f"Tavily search error: {e}, falling back to DuckDuckGo")

    # DuckDuckGo fallback
    try:
        try:
            from ddgs import DDGS as DDGS_Client
        except ImportError:
            from duckduckgo_search import DDGS as DDGS_Client

        with DDGS_Client() as ddgs:
            for r in list(ddgs.text(query, max_results=max_results)):
                results.append({
                    "title": r.get("title", "Web Source"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")

    return _only_real_urls(results)


def _only_real_urls(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep only results with a real http(s) URL that is not a search-engine results page."""
    bad_patterns = ("search?query=", "google.com/search", "bing.com/search")
    return [
        r for r in results
        if r.get("url", "").startswith("http")
        and not any(p in r["url"] for p in bad_patterns)
    ]
