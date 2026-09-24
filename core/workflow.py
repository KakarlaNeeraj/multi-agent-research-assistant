import time
from typing import Generator, Tuple
from core.state import ResearchState
from agents.planner import run_planner_agent
from agents.searcher import run_search_agent
from agents.writer import run_writer_agent
from agents.critic import run_critic_agent

MIN_SOURCES = 3       # below this, refuse to write a report
MAX_REVISIONS = 2     # writer <-> critic loops after the first draft


def execute_research_workflow(
    topic: str,
    report_type: str = "Technical Report",
    llm_client=None,
    max_sources_per_query: int = 2
) -> Generator[Tuple[str, ResearchState], None, ResearchState]:
    """
    Step-by-step generator yielding (current_stage_name, state)
    to power live UI progress bars and accordion visualizations in Streamlit.
    """
    state = ResearchState(topic=topic, report_type=report_type)

    # 1. Planning Stage
    yield ("planner_start", state)
    state.logs.append("🧠 [Planner Agent] Formulating research strategy, outline, and search queries...")
    state.plan = run_planner_agent(topic=topic, report_type=report_type, llm_client=llm_client)
    state.logs.append(f"✓ Topic: {state.plan.topic}")
    for sq in state.plan.search_queries:
        state.logs.append(f"   • query: {sq.query}")
    state.logs.append(f"✓ Plan created with {len(state.plan.sections)} sections and {len(state.plan.search_queries)} search queries.")
    yield ("planner_done", state)
    time.sleep(0.3)

    # 2. Search & Retrieval Stage
    yield ("searcher_start", state)
    state.logs.append("🔍 [Search Agent] Executing live web retrieval & source indexing...")
    sources, search_logs = run_search_agent(
        state.plan, max_sources_per_query=max_sources_per_query, llm_client=llm_client
    )
    state.sources = sources
    state.logs.extend(search_logs)
    state.logs.append(f"✓ Kept {len(sources)} relevant sources with real URLs.")
    yield ("searcher_done", state)

    # Fail loudly instead of writing a report with nothing to write from
    if len(sources) < MIN_SOURCES:
        state.is_approved = False
        state.critique_notes = (
            f"Insufficient reliable sources found ({len(sources)} of {MIN_SOURCES} needed). "
            "Try a more specific topic or check your search setup."
        )
        state.logs.append("⚠️ " + state.critique_notes)
        yield ("insufficient_sources", state)
        return state
    time.sleep(0.3)

    # 3 + 4. Writer <-> Critic loop
    feedback = ""
    for attempt in range(MAX_REVISIONS + 1):
        yield ("writer_start", state)
        label = "Synthesizing" if attempt == 0 else f"Revising (attempt {attempt + 1})"
        state.logs.append(f"✍️ [Writer Agent] {label} evidence into a structured, cited report...")
        state.draft_report = run_writer_agent(
            topic=state.plan.topic, plan=state.plan, sources=state.sources,
            llm_client=llm_client, feedback=feedback
        )
        state.logs.append("✓ Draft completed.")
        yield ("writer_done", state)
        time.sleep(0.3)

        yield ("critic_start", state)
        state.logs.append("🛡️ [Critic Agent] Checking that every claim is supported by its cited source...")
        is_valid, critique = run_critic_agent(state.draft_report, state.sources, llm_client)
        state.is_approved = is_valid
        state.critique_notes = critique
        state.final_report = state.draft_report
        state.logs.append(critique)
        yield ("critic_done", state)

        if is_valid:
            break
        feedback = critique

    return state
