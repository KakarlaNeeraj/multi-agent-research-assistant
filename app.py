import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.workflow import execute_research_workflow
from core.pdf_exporter import markdown_to_pdf_bytes

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sleek UI styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .badge-planner { color: #2563EB; font-weight: 600; }
    .badge-searcher { color: #0D9488; font-weight: 600; }
    .badge-writer { color: #D97706; font-weight: 600; }
    .badge-critic { color: #16A34A; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Helper function to create LLM caller
def get_llm_caller(provider: str, api_key: str, model_name: str, base_url: str = ""):
    if provider in ["Groq (Ultra-Fast)", "OpenAI", "Local LLM (Ollama / LM Studio / vLLM / Custom)"]:
        try:
            from openai import OpenAI
            client_kwargs = {}
            if provider.startswith("Groq"):
                client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
                client_kwargs["api_key"] = api_key.strip() if api_key else os.getenv("GROQ_API_KEY", "")
                target_model = model_name.strip() if model_name else "qwen/qwen3.8-27b"
            elif base_url:
                client_kwargs["base_url"] = base_url.strip()
                if api_key:
                    client_kwargs["api_key"] = api_key.strip()
                elif provider.startswith("Local"):
                    client_kwargs["api_key"] = "local-api-key"
                target_model = model_name.strip() if model_name else "gemini-2.5-flash"
            else:
                if api_key:
                    client_kwargs["api_key"] = api_key.strip()
                target_model = model_name.strip() if model_name else "gpt-4o-mini"

            if not client_kwargs.get("api_key"):
                return None

            client = OpenAI(**client_kwargs)

            def call_openai_compat(system_prompt: str, user_prompt: str) -> str:
                # Active fallback candidates if the proxy hits a 502/retired model error
                candidate_models = [target_model, "gemini-2.5-flash", "llama-3.3-70b-versatile", "mistral-large-latest", "gpt-4o"]
                models_to_try = [target_model] if provider.startswith("Groq") else list(dict.fromkeys(candidate_models))
                
                last_exc = None
                for m in models_to_try:
                    try:
                        response = client.chat.completions.create(
                            model=m,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.3
                        )
                        return response.choices[0].message.content
                    except Exception as e:
                        last_exc = e
                        print(f"Warning: Model '{m}' returned error ({e}), trying next candidate...")
                        continue
                raise last_exc
            return call_openai_compat
        except Exception as e:
            st.sidebar.error(f"LLM Connection Error: {e}")
            return None

    elif provider == "Google Gemini":
        if not api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name or "gemini-1.5-flash")
            def call_gemini(system_prompt: str, user_prompt: str) -> str:
                prompt = f"{system_prompt}\n\nUser Request:\n{user_prompt}"
                response = model.generate_content(prompt)
                return response.text
            return call_gemini
        except Exception as e:
            st.sidebar.error(f"Gemini Client Error: {e}")
            return None

    return None


# Sidebar controls
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/brain.png", width=64)
    st.title("Control Center")
    st.markdown("Configure agent swarms & LLM parameters.")
    
    st.markdown("---")
    st.subheader("⚙️ Model Configuration")
    llm_provider = st.selectbox(
        "LLM Provider",
        [
            "Groq (Ultra-Fast)",
            "Local LLM (Ollama / LM Studio / vLLM / Custom)",
            "OpenAI",
            "Google Gemini"
        ]
    )
    
    api_key = ""
    model_choice = ""
    local_base_url = ""

    if llm_provider == "Groq (Ultra-Fast)":
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", "")
        )
        model_choice = st.selectbox(
            "Groq Model",
            [
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b"
            ],
            index=0
        )
    elif llm_provider == "Local LLM (Ollama / LM Studio / vLLM / Custom)":
        local_base_url = st.text_input(
            "Local Endpoint (Base URL)",
            value=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:3001/v1"),
            help="Common examples:\n- FreeLLM / Custom: http://localhost:3001/v1\n- Ollama: http://localhost:11434/v1\n- LM Studio: http://localhost:1234/v1\n- vLLM / LocalAI: http://localhost:8000/v1"
        )
        local_model_preset = st.selectbox(
            "Select Model",
            [
                "gemini-2.5-flash",
                "llama-3.3-70b-versatile",
                "mistral-large-latest",
                "gpt-4o",
                "Custom Model Tag"
            ],
            index=0
        )
        if local_model_preset == "Custom Model Tag":
            model_choice = st.text_input("Enter Custom Model Tag", value="gemini-2.5-flash")
        else:
            model_choice = local_model_preset

        api_key = st.text_input(
            "API Key (Optional for Local)",
            type="password",
            value=os.getenv("LOCAL_LLM_API_KEY", "")
        )
    elif llm_provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model_choice = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
    elif llm_provider == "Google Gemini":
        api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        model_choice = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
        
    tavily_key = st.text_input("Tavily API Key (Optional)", type="password", value=os.getenv("TAVILY_API_KEY", ""), help="If left empty, defaults to DuckDuckGo search automatically.")
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key

    st.markdown("---")
    st.subheader("🎯 Research Parameters")
    report_type = st.selectbox("Target Tone / Format", ["Technical Whitepaper", "Executive Briefing", "Academic Review", "Market Analysis"])
    search_depth = st.slider("Sources per Sub-query", min_value=1, max_value=4, value=2)

    st.markdown("---")
    with st.expander("ℹ️ Project Architecture"):
        st.markdown("""
        **Multi-Agent Topology:**
        1. **Planner**: Query breakdown & outline.
        2. **Searcher**: Asynchronous web retrieval & source indexing `[1]`, `[2]`.
        3. **Writer**: Grounded synthesis with citations.
        4. **Critic**: Hallucination audit & verification.
        
        *Built purely with Python & Streamlit (No Full-Stack overhead).*
        """)

# Header
st.markdown('<div class="main-title">Multi-Agent Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Planning, Web Scraping, Fact Grounding & Cited Report Synthesis</div>', unsafe_allow_html=True)

# Main Query Input
col_input, col_btn = st.columns([5, 1])
with col_input:
    default_prompt = "Recent breakthroughs in Quantum Error Correction and Fault-Tolerant Quantum Computing"
    user_topic = st.text_input(
        "Enter any research topic:", value=default_prompt, label_visibility="collapsed",
        help="Enter the topic itself, e.g. 'Retrieval-Augmented Generation (RAG): components, advantages, limitations'."
    )
with col_btn:
    start_btn = st.button("🚀 Start Research", use_container_width=True, type="primary")

# Execution Area
if start_btn and user_topic:
    llm_caller = get_llm_caller(llm_provider, api_key, model_choice, base_url=local_base_url)
    if llm_caller is None:
        st.error("No LLM configured. Pick a provider and enter a key or endpoint in the sidebar (for Ollama, make sure it is running).")
        st.stop()

    st.markdown("---")
    st.subheader("🤖 Live Multi-Agent Swarm Execution")
    
    progress_bar = st.progress(0, text="Initializing state...")
    status_container = st.container()
    
    # Progress containers
    c1, c2, c3, c4 = st.columns(4)
    p_box = c1.empty()
    s_box = c2.empty()
    w_box = c3.empty()
    c_box = c4.empty()
    
    p_box.info("1. Planner: Waiting")
    s_box.info("2. Searcher: Waiting")
    w_box.info("3. Writer: Waiting")
    c_box.info("4. Critic: Waiting")
    
    log_expander = st.expander("📋 Live Multi-Agent Event Stream", expanded=True)
    
    final_state = None
    
    # Run the generator
    try:
        for stage, current_state in execute_research_workflow(
            topic=user_topic,
            report_type=report_type,
            llm_client=llm_caller,
            max_sources_per_query=search_depth
        ):
            final_state = current_state
        
            # Update logs
            with log_expander:
                if current_state.logs:
                    st.code("\n".join(current_state.logs[-6:]), language="text")
                
            # Stage visual transitions
            if stage == "planner_start":
                progress_bar.progress(15, text="Planner formulating outline & search queries...")
                p_box.warning("1. Planner: Working 🧠")
            elif stage == "planner_done":
                progress_bar.progress(30, text="Plan created!")
                p_box.success(f"1. Planner: Done ({len(current_state.plan.sections)} secs)")
            elif stage == "searcher_start":
                progress_bar.progress(45, text="Searcher querying live web...")
                s_box.warning("2. Searcher: Searching 🔍")
            elif stage == "searcher_done":
                progress_bar.progress(70, text="Sources harvested & indexed!")
                s_box.success(f"2. Searcher: {len(current_state.sources)} sources ✓")
            elif stage == "writer_start":
                progress_bar.progress(80, text="Writer synthesizing cited report...")
                w_box.warning("3. Writer: Synthesizing ✍️")
            elif stage == "writer_done":
                progress_bar.progress(90, text="Draft synthesized!")
                w_box.success("3. Writer: Done ✓")
            elif stage == "critic_start":
                progress_bar.progress(95, text="Critic verifying citations...")
                c_box.warning("4. Critic: Auditing 🛡️")
            elif stage == "critic_done":
                if current_state.is_approved:
                    progress_bar.progress(100, text="Research completed & verified!")
                    c_box.success("4. Critic: Verified ✓")
                else:
                    progress_bar.progress(100, text="Finished, but the critic found problems")
                    c_box.warning("4. Critic: Issues found ⚠️")
            elif stage == "insufficient_sources":
                progress_bar.progress(100, text="Stopped: not enough relevant sources")
                s_box.error("2. Searcher: too few sources ✗")
                w_box.info("3. Writer: Skipped")
                c_box.info("4. Critic: Skipped")
    except Exception as e:
        st.error(
            f"Pipeline stopped: {e}\n\n"
            "Check that your LLM is reachable (for Ollama: is it running? is the model pulled?) "
            "and that the API key/endpoint in the sidebar is correct."
        )
        st.stop()

    # Display Report
    if final_state and final_state.final_report:
        st.markdown("---")
        if final_state.is_approved:
            st.subheader("📑 Final Verified Research Report")
        else:
            st.subheader("📑 Draft Research Report (not fully verified)")
            st.warning(final_state.critique_notes)
        
        # Action buttons
        try:
            pdf_bytes = markdown_to_pdf_bytes(final_state.final_report, topic=user_topic)
        except Exception as e:
            st.warning(f"Note on PDF styling: {e}")
            pdf_bytes = final_state.final_report.encode("utf-8")
        
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])
        with btn_col1:
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"research_report_{user_topic[:20].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                label="📄 Download Markdown (.md)",
                data=final_state.final_report,
                file_name=f"research_report_{user_topic[:20].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("---")
        # Display Markdown
        st.markdown(final_state.final_report)
        
        # Display Indexed Sources in Expander
        with st.expander("🔗 Inspected Source Evidence Base", expanded=False):
            for s_id, s_obj in final_state.sources.items():
                st.markdown(f"**[{s_id}] {s_obj.title}**")
                st.markdown(f"*URL:* [{s_obj.url}]({s_obj.url})")
                st.markdown(f"> {s_obj.snippet}")
                st.markdown("---")
    else:
        st.error(final_state.critique_notes if final_state and final_state.critique_notes else "No report was produced.")

else:
    # Empty State & Project Walkthrough Guide
    st.info("💡 Enter a research topic above and click **Start Research** to observe the multi-agent planning, retrieval, and synthesis workflow.")
    
    st.markdown("### 🏛️ Multi-Agent Architecture at a Glance")
    arch_c1, arch_c2, arch_c3, arch_c4 = st.columns(4)
    with arch_c1:
        st.markdown("""
        #### 1. Planner Agent
        - Query decomposition
        - Search strategy design
        - Structural TOC generation
        """)
    with arch_c2:
        st.markdown("""
        #### 2. Search Agent
        - Live web retrieval
        - Noise filtering
        - Canonical citation indexing `[1]`, `[2]`
        """)
    with arch_c3:
        st.markdown("""
        #### 3. Writer Agent
        - Multi-source synthesis
        - Strict inline citation insertion
        - Executive summary + Bibliography
        """)
    with arch_c4:
        st.markdown("""
        #### 4. Critic Agent
        - Automated hallucination audit
        - Citation existence verification
        - Completeness confirmation
        """)
