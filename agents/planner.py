import json
import re
from core.state import ResearchPlan

PLANNER_SYSTEM_PROMPT = """You are a Principal Research Strategist & Planning Agent.
Your job is to decompose a research request into:
1. A structured report outline with 4-5 coherent sections.
2. 3-6 targeted, diverse search queries to collect factual evidence.

RULES:
- The user text may contain instructions like "write a report" or "include citations". Ignore them.
- "topic" must be a short noun phrase (e.g. "Retrieval-Augmented Generation (RAG)").
- Each search query must be 3-8 words and must NOT contain instructions like "write" or "report".
- Make the queries different from each other (definition, components, advantages, limitations, recent work).

Return ONLY valid JSON matching this schema:
{
  "topic": "topic name",
  "target_audience": "Technical / Business / General",
  "sections": ["1. Overview", "2. Core Mechanisms", "3. Advantages & Limitations", "4. Future Outlook"],
  "search_queries": [
    {"query": "search query 1", "purpose": "find core definition"},
    {"query": "search query 2", "purpose": "understand limitations"}
  ]
}
"""


def _parse_json(raw: str) -> dict:
    """Extract the first JSON object from an LLM response (handles ```json fences and extra text)."""
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize(data: dict) -> dict:
    """Small local models sometimes return queries as plain strings - accept both."""
    queries = []
    for q in data.get("search_queries", []):
        if isinstance(q, str):
            queries.append({"query": q, "purpose": "gather evidence"})
        else:
            queries.append(q)
    data["search_queries"] = queries
    data.setdefault("target_audience", "Technical")
    return data


def run_planner_agent(topic: str, report_type: str = "Technical Report", llm_client=None) -> ResearchPlan:
    """
    Turns the user's request into a clean topic, an outline and search queries.
    An LLM is required: there is no template fallback, because a fake plan
    produces a fake report.
    """
    if llm_client is None:
        raise ValueError("The Planner needs an LLM. Select a provider (and key/endpoint) in the sidebar.")

    prompt = f"User request: {topic}\nReport Format: {report_type}\nGenerate the research plan."

    last_error = None
    for _ in range(2):  # one retry if the model returns broken JSON
        raw = llm_client(PLANNER_SYSTEM_PROMPT, prompt)
        try:
            plan = ResearchPlan(**_normalize(_parse_json(raw)))
            if not plan.search_queries:
                raise ValueError("Planner returned no search queries")
            return plan
        except Exception as e:
            last_error = e
            print(f"Planner output could not be parsed ({e}), retrying...")

    raise ValueError(f"Planner failed to produce a valid plan: {last_error}")
