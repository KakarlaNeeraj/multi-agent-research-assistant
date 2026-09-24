import re
from typing import Dict
from core.state import ResearchPlan, Source

WRITER_SYSTEM_PROMPT = """You are a Principal Technical Writer and Synthesis AI Agent.
Write an in-depth, rigorous, structured research report based STRICTLY on the provided sources.

CRITICAL RULES:
1. CITATIONS: Every factual claim MUST be immediately followed by its citation tag, e.g. [1] or [2][4].
2. GROUNDING: Use ONLY the sources provided. If they don't cover something, say so explicitly.
   Do NOT add facts from memory. Do NOT cite numbers that are not in the source index.
3. STRUCTURE:
   - # [Report Title]
   - ## Executive Summary
   - ## [Section from Outline]
   - ...
   - ## Key Takeaways
4. Do NOT write a reference list. It is added automatically after your report.
5. TONE: Objective, clear, academic yet industry-actionable.
"""


def build_references(draft: str, sources: Dict[int, Source]) -> str:
    """Build the reference list in code from real search results - the LLM never writes URLs."""
    used = sorted({int(i) for i in re.findall(r"\[(\d+)\]", draft)})
    lines = [f"[{i}] {sources[i].title} - {sources[i].url}" for i in used if i in sources]
    return "\n\n## References\n" + "\n".join(lines) + "\n"


def run_writer_agent(
    topic: str,
    plan: ResearchPlan,
    sources: Dict[int, Source],
    llm_client=None,
    feedback: str = "",
) -> str:
    """
    Synthesizes the plan and sources into a cited markdown report.
    An LLM is required: there is no template fallback.
    `feedback` carries the critic's objections when the draft is being revised.
    """
    if llm_client is None:
        raise ValueError("The Writer needs an LLM. Select a provider (and key/endpoint) in the sidebar.")

    sources_text = "\n\n".join(
        f"SOURCE [{s.id}]:\nTitle: {s.title}\nURL: {s.url}\nExcerpt: {s.snippet}"
        for s in sources.values()
    )
    prompt = (
        f"Topic: {topic}\n"
        f"Outline Sections: {', '.join(plan.sections)}\n\n"
        f"Verified Source Index:\n{sources_text}\n\n"
        "Generate the complete, cited research report in clean Markdown following all rules."
    )
    if feedback:
        prompt += (
            "\n\nYour previous draft was rejected by the fact-checker. Fix these problems "
            f"(remove or rewrite unsupported claims):\n{feedback}"
        )

    draft = llm_client(WRITER_SYSTEM_PROMPT, prompt)
    return draft + build_references(draft, sources)
