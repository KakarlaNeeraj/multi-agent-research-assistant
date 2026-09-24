from typing import Dict, List, Tuple
from core.state import ResearchPlan, Source
from utils.search_tools import search_web


def is_relevant(topic: str, title: str, snippet: str, llm_client) -> bool:
    """Ask the LLM whether a search result is actually useful for the topic."""
    if not llm_client:
        return True
    try:
        answer = llm_client(
            "You judge search-result relevance. Answer with only YES or NO.",
            f"Topic: {topic}\nTitle: {title}\nSnippet: {snippet[:400]}\n"
            "Is this result directly useful for researching the topic?"
        )
        if not answer:
            return True
        cleaned = answer.strip().upper()
        return cleaned.startswith("YES") or ("YES" in cleaned and not cleaned.startswith("NO"))
    except Exception as e:
        print(f"Relevance check warning: {e}, keeping source")
        return True


def run_search_agent(
    plan: ResearchPlan,
    max_sources_per_query: int = 2,
    llm_client=None,
) -> Tuple[Dict[int, Source], List[str]]:
    """
    Executes all search queries from the planner agent.
    - Skips results that have no real URL (no fabricated sources).
    - Deduplicates URLs.
    - Drops irrelevant results when an LLM is available.
    - Creates an indexed dictionary of Sources ([1], [2], ...).
    """
    sources_dict: Dict[int, Source] = {}
    seen_urls = set()
    logs: List[str] = []
    current_id = 1

    for sq in plan.search_queries:
        logs.append(f"🔍 Searching: '{sq.query}' ({sq.purpose})")
        raw_results = search_web(sq.query, max_results=max_sources_per_query)

        if not raw_results:
            logs.append("  ✗ No results returned for this query")
            continue

        for r in raw_results:
            url = r.get("url", "").strip()
            if not url.startswith("http") or url in seen_urls:
                continue
            seen_urls.add(url)

            title = r.get("title", "").strip() or f"Source {current_id}"
            snippet = r.get("snippet", "")

            if llm_client and not is_relevant(plan.topic, title, snippet, llm_client):
                logs.append(f"  ✗ Dropped irrelevant: {title[:60]}")
                continue

            sources_dict[current_id] = Source(
                id=current_id, title=title, url=url, snippet=snippet
            )
            logs.append(f"  ✓ Indexed [{current_id}]: {title[:60]}...")
            current_id += 1

    return sources_dict, logs
