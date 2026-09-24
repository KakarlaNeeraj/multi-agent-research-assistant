import re
from typing import Dict, Tuple
from core.state import Source


def run_critic_agent(report_md: str, sources: Dict[int, Source], llm_client=None) -> Tuple[bool, str]:
    """
    Validates the report for:
    1. Presence of inline citations e.g. [1], [2].
    2. Cited numbers actually exist in the sources dict.
    3. (With an LLM) every claim is supported by the source text it cites.
    """
    citation_pattern = re.compile(r'\[(\d+)\]')
    found_citations = citation_pattern.findall(report_md)

    valid_source_ids = set(str(k) for k in sources.keys())
    missing_sources = set(found_citations) - valid_source_ids

    if not found_citations:
        return False, "Critic Warning: No inline numerical citations found in the draft report."

    if missing_sources:
        return False, f"Critic Error: Report references hallucinated source IDs {missing_sources} not present in evidence base."

    if llm_client:
        body = report_md.split("\n## References")[0]  # check the claims, not the bibliography
        source_text = "\n\n".join(f"[{s.id}] {s.snippet}" for s in sources.values())
        verdict = llm_client(
            "You are a strict fact-checker. List every claim in the report that is NOT supported "
            "by the source text it cites. If every claim is supported, reply exactly: ALL SUPPORTED",
            f"SOURCES:\n{source_text}\n\nREPORT:\n{body}"
        )
        if not verdict.strip().upper().startswith("ALL SUPPORTED"):
            return False, f"Critic Error: Unsupported claims found:\n{verdict.strip()}"

    critique = (
        f"✓ Quality Check Passed: Found {len(found_citations)} valid citation instances "
        f"across {len(set(found_citations))} unique verified sources."
    )
    return True, critique
