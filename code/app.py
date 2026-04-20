"""
Coder Buddy - Streamlit Application
=======================================
A premium, interactive frontend for the multi-agent code generation pipeline.

Features:
  - Multi-provider LLM support (Google Gemini, Groq Cloud, OpenAI)
  - Real-time pipeline progress with agent status
  - Auto-save files with proper extensions
  - ZIP download for generated projects
  - User-controlled revision loop (Revise & Regenerate)
  - Live UI preview for HTML/web projects

Run with: streamlit run app.py
"""

import sys
import os
import time
import streamlit as st
import streamlit.components.v1 as components

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import run_pipeline, run_revision
from utils.file_utils import (
    save_generated_files,
    create_zip_archive,
    get_file_tree,
    get_file_tree_from_dict,
)
from utils.rag import load_project_files, build_vector_store, search_codebase, get_project_summary
from utils.vision import analyze_design_image, get_supported_vision_models


# ╔══════════════════════════════════════════════════════════════════╗
# ║                     PAGE CONFIGURATION                          ║
# ╚══════════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Coder Buddy — AI Development Team",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      CUSTOM STYLING                             ║
# ╚══════════════════════════════════════════════════════════════════╝
st.markdown("""
<style>
    /* ── Import Google Font ────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global Styles ─────────────────────────────────────── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hero Header ───────────────────────────────────────── */
    .hero-container {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 20px;
        padding: 3rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(48, 43, 99, 0.3);
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 60%);
        animation: pulse 8s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1) rotate(0deg); }
        50% { transform: scale(1.1) rotate(5deg); }
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-size: 1.15rem;
        color: rgba(255, 255, 255, 0.75);
        font-weight: 300;
        position: relative;
        z-index: 1;
        max-width: 600px;
    }

    /* ── Agent Status Cards ────────────────────────────────── */
    .agent-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .agent-card:hover {
        border-color: rgba(139, 92, 246, 0.5);
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
        transform: translateY(-2px);
    }

    .agent-card-active {
        border-color: rgba(96, 165, 250, 0.6);
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.2);
        animation: glow 2s ease-in-out infinite;
    }

    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(96, 165, 250, 0.2); }
        50% { box-shadow: 0 0 30px rgba(96, 165, 250, 0.4); }
    }

    .agent-card-done {
        border-color: rgba(52, 211, 153, 0.5);
    }

    .agent-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.3rem;
    }

    .agent-desc {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
    }

    /* ── Code Output ───────────────────────────────────────── */
    .file-header {
        background: linear-gradient(90deg, #1e1b4b, #312e81);
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #c4b5fd;
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-bottom: none;
    }

    /* ── Sidebar Styling ───────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29, #1a1a2e);
    }

    .sidebar-section {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }

    .sidebar-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255, 255, 255, 0.4);
        margin-bottom: 0.8rem;
    }

    /* ── Button Styling ────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5) !important;
    }

    /* ── Groq Badge ────────────────────────────────────────── */
    .groq-badge {
        background: linear-gradient(135deg, #f97316, #ef4444);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 100px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-left: 0.5rem;
    }

    /* ── Revision Section ──────────────────────────────────── */
    .revision-box {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(251, 191, 36, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    /* ── File Tree ─────────────────────────────────────────── */
    .file-tree-box {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #a5b4fc;
    }
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                       SESSION STATE                             ║
# ╚══════════════════════════════════════════════════════════════════╝
defaults = {
    "pipeline_running": False,
    "pipeline_results": {},
    "active_agent": None,
    "completed_agents": [],
    "project_name": "my_project",
    "revision_running": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ╔══════════════════════════════════════════════════════════════════╗
# ║                        HERO HEADER                              ║
# ╚══════════════════════════════════════════════════════════════════╝
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🤖 Coder Buddy</div>
    <div class="hero-subtitle">
        Your elite AI development team — describe what you want to build,
        and our agents will plan, architect, code, and review it for you.
    </div>
</div>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                         SIDEBAR                                 ║
# ╚══════════════════════════════════════════════════════════════════╝
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-title">🔑 LLM Provider</div>',
        unsafe_allow_html=True,
    )

    provider = st.selectbox(
        "Provider",
        ["Groq Cloud  ⚡ FREE & Fast", "Google Gemini", "OpenAI"],
        index=0,
        label_visibility="collapsed",
    )

    if "Groq Cloud" in provider:
        api_key = st.text_input("Groq API Key", type="password", key="groq_key")
        model = st.selectbox("Model", [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ])
        st.markdown(
            "💡 *[Get free key →](https://console.groq.com/keys)*",
        )
    elif provider == "Google Gemini":
        api_key = st.text_input("Google API Key", type="password", key="google_key")
        model = st.selectbox("Model", [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ])
    else:
        api_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
        model = st.selectbox("Model", [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ])

    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    st.markdown('</div>', unsafe_allow_html=True)

    # Apply settings to environment
    if api_key:
        if "Groq Cloud" in provider:
            os.environ["GROQ_API_KEY"] = api_key
            os.environ["LLM_PROVIDER"] = "groq"
            os.environ["RETRY_DELAY"] = "0"  # Groq has generous limits
        elif provider == "Google Gemini":
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["LLM_PROVIDER"] = "google"
            os.environ["RETRY_DELAY"] = "10"
        else:
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["RETRY_DELAY"] = "0"
        os.environ["LLM_MODEL"] = model
        os.environ["LLM_TEMPERATURE"] = str(temperature)

    st.markdown("---")

    # Pipeline visualization
    st.markdown("### 🔄 Agent Pipeline")

    agents_info = [
        ("📋", "Planner", "Designs the project plan"),
        ("🏗️", "Architect", "Creates engineering tasks"),
        ("💻", "Coder", "Writes the actual code"),
        ("🔍", "Reviewer", "Reviews code quality"),
        ("🧪", "Sandbox", "Tests the generated code"),
        ("🔀", "Git", "Auto-commits to repository"),
    ]

    for icon, name, desc in agents_info:
        agent_key = name.lower()
        if agent_key in st.session_state.completed_agents:
            status_class = "agent-card agent-card-done"
            badge = "✅"
        elif st.session_state.active_agent == agent_key:
            status_class = "agent-card agent-card-active"
            badge = "⏳"
        else:
            status_class = "agent-card"
            badge = "⬜"

        st.markdown(f"""
        <div class="{status_class}">
            <div class="agent-name">{icon} {name} {badge}</div>
            <div class="agent-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.75rem;'>"
        "Built with LangGraph + Streamlit<br>"
        "Coder Buddy v2.0"
        "</div>",
        unsafe_allow_html=True,
    )


# ╔══════════════════════════════════════════════════════════════════╗
# ║                       MAIN CONTENT                              ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── Project Templates ──────────────────────────────────────────────
TEMPLATES = {
    "🌐 REST API": (
        "I want to build a REST API using Python and FastAPI that:\n"
        "- Has user authentication with JWT tokens\n"
        "- CRUD operations for a resource (e.g., blog posts)\n"
        "- Uses SQLite with SQLAlchemy ORM\n"
        "- Includes input validation with Pydantic\n"
        "Special instructions: Include error handling, logging, and API documentation."
    ),
    "🕷️ Web Scraper": (
        "I want to build a Web Scraper using Python that:\n"
        "- Scrapes product listings from e-commerce sites\n"
        "- Extracts product name, price, rating, and availability\n"
        "- Saves data to CSV and JSON formats\n"
        "- Handles pagination and rate limiting\n"
        "Tech Stack: Use requests, BeautifulSoup4, and pandas.\n"
        "Special instructions: Include retry logic and user-agent rotation."
    ),
    "🤖 Discord Bot": (
        "I want to build a Discord Bot using Python that:\n"
        "- Responds to slash commands\n"
        "- Has a moderation system (kick, ban, mute)\n"
        "- Includes a fun trivia game feature\n"
        "- Logs all actions to a file\n"
        "Tech Stack: Use discord.py.\n"
        "Special instructions: Use async/await patterns and include error handling."
    ),
    "📊 Data Dashboard": (
        "I want to build a Data Dashboard using Python and Streamlit that:\n"
        "- Loads CSV/Excel data files\n"
        "- Shows interactive charts (bar, line, scatter, pie)\n"
        "- Has filters for date range and categories\n"
        "- Exports filtered data to CSV\n"
        "Tech Stack: Use streamlit, pandas, plotly.\n"
        "Special instructions: Make it visually appealing with a dark theme."
    ),
    "⚡ CLI Tool": (
        "I want to build a CLI tool using Python that:\n"
        "- Manages personal TODO tasks\n"
        "- Supports add, list, complete, and delete operations\n"
        "- Stores data in a local JSON file\n"
        "- Has colorful terminal output\n"
        "Tech Stack: Use click and rich.\n"
        "Special instructions: Include help text for all commands and input validation."
    ),
}

# Input section
col_input, col_templates = st.columns([3, 2])

with col_input:
    st.markdown("### 💡 Describe Your Project")
    user_input = st.text_area(
        "What would you like to build?",
        height=250,
        placeholder=(
            "I want to build a [Project Type] that does the following:\n\n"
            "• Feature 1\n"
            "• Feature 2\n\n"
            "Tech Stack: Use Python, ...\n"
            "Special instructions: ..."
        ),
        key="user_input",
        label_visibility="collapsed",
    )

    col_name, col_btn = st.columns([2, 1])
    with col_name:
        project_name = st.text_input(
            "Project Name",
            value="my_project",
            key="proj_name_input",
            label_visibility="collapsed",
            placeholder="Project name (e.g., my_api)",
        )
        st.session_state.project_name = project_name

    with col_btn:
        generate_btn = st.button(
            "🚀 Generate Project",
            use_container_width=True,
            disabled=st.session_state.pipeline_running,
        )

with col_templates:
    st.markdown("### 📝 Quick Templates")
    for name, template_text in TEMPLATES.items():
        if st.button(name, key=f"tmpl_{name}", use_container_width=True):
            st.session_state["user_input"] = template_text
            st.rerun()


# ╔══════════════════════════════════════════════════════════════════╗
# ║                ADVANCED INPUTS (RAG + Vision)                    ║
# ╚══════════════════════════════════════════════════════════════════╝
with st.expander("🔬 Advanced: Existing Codebase & Design Upload", expanded=False):
    adv_col1, adv_col2 = st.columns(2)

    # ── Feature 1: RAG Codebase Context ───────────────────────────
    with adv_col1:
        st.markdown("#### 📂 Existing Project (RAG Context)")
        st.caption(
            "Point to an existing project folder so the AI agents can "
            "understand your codebase before adding new features."
        )
        existing_project_path = st.text_input(
            "Project folder path:",
            placeholder="e.g., C:/Users/you/Projects/my_app",
            key="rag_project_path",
        )

        if existing_project_path and os.path.isdir(existing_project_path):
            project_files = load_project_files(existing_project_path)
            if project_files:
                st.success(f"Found **{len(project_files)}** code files")
                with st.expander("View project structure"):
                    st.code(get_project_summary(project_files), language="text")

                # Build vector store (cached in session)
                if "rag_vector_store" not in st.session_state or st.session_state.get("_rag_path") != existing_project_path:
                    with st.spinner("Building code index (first time only)..."):
                        vs = build_vector_store(project_files)
                        st.session_state.rag_vector_store = vs
                        st.session_state._rag_path = existing_project_path
                    if vs:
                        st.success("Code index ready!")
                    else:
                        st.warning("Could not build index. Install: `pip install faiss-cpu sentence-transformers`")
            else:
                st.warning("No supported code files found in that directory.")
        elif existing_project_path:
            st.warning("Directory not found. Please check the path.")

    # ── Feature 2: Wireframe/Design Upload ────────────────────────
    with adv_col2:
        st.markdown("#### 🎨 Upload Wireframe / Design")
        st.caption(
            "Upload a UI sketch, wireframe, or screenshot. "
            "A vision AI will analyze it and guide the code generation."
        )
        uploaded_design = st.file_uploader(
            "Upload wireframe image:",
            type=["png", "jpg", "jpeg", "webp"],
            key="design_upload",
        )

        if uploaded_design:
            st.image(uploaded_design, caption="Uploaded Design", width=300)

            if st.button("🔍 Analyze Design", key="analyze_design_btn"):
                with st.spinner("Analyzing design with vision AI..."):
                    image_bytes = uploaded_design.getvalue()
                    description = analyze_design_image(
                        image_bytes,
                        image_mime=uploaded_design.type or "image/png",
                    )
                    st.session_state.design_description = description

            if st.session_state.get("design_description"):
                with st.expander("View design analysis"):
                    st.markdown(st.session_state.design_description)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                    RUN THE PIPELINE                             ║
# ╚══════════════════════════════════════════════════════════════════╝
if generate_btn and user_input:
    if not api_key:
        st.error("⚠️ Please enter your API key in the sidebar first!")
    else:
        st.session_state.pipeline_running = True
        st.session_state.pipeline_results = {}
        st.session_state.completed_agents = []
        st.session_state.active_agent = None

        st.markdown("---")
        st.markdown("## 🔄 Pipeline Running...")

        # Progress containers
        progress_bar = st.progress(0, text="Initializing pipeline...")
        status_container = st.empty()

        agent_order = ["planner", "architect", "coder", "reviewer", "sandbox", "git_commit", "finalize"]
        agent_labels = {
            "planner": "📋 Planner Agent — Designing project plan...",
            "architect": "🏗️ Architect Agent — Creating engineering tasks...",
            "coder": "💻 Coder Agent — Writing code...",
            "reviewer": "🔍 Reviewer Agent — Reviewing code quality...",
            "sandbox": "🧪 Sandbox — Testing generated code...",
            "git_commit": "🔀 Git — Auto-committing files...",
            "finalize": "✨ Finalizing output...",
        }

        accumulated_state = {}

        try:
            # Gather RAG context if available
            codebase_context = ""
            if st.session_state.get("rag_vector_store"):
                codebase_context = search_codebase(
                    st.session_state.rag_vector_store, user_input
                )

            # Get design description if available
            design_desc = st.session_state.get("design_description", "")

            for event in run_pipeline(user_input, codebase_context, design_desc):
                for node_name, node_output in event.items():
                    accumulated_state.update(node_output)

                    # Update progress
                    if node_name in agent_order:
                        step_idx = agent_order.index(node_name) + 1
                        progress = step_idx / len(agent_order)
                        label = agent_labels.get(node_name, "Processing...")
                        progress_bar.progress(progress, text=label)

                        st.session_state.active_agent = node_name
                        if node_name != "finalize":
                            st.session_state.completed_agents.append(node_name)

                        status_container.info(f"✅ **{node_name.title()}** complete!")
                        time.sleep(0.5)

            # Auto-save files to disk
            files = accumulated_state.get("generated_files", {})
            if files:
                try:
                    save_path = save_generated_files(files, project_name)
                    accumulated_state["_save_path"] = save_path
                except Exception:
                    pass  # Don't fail pipeline if save fails

            st.session_state.pipeline_results = accumulated_state
            st.session_state.pipeline_running = False
            st.session_state.active_agent = None
            progress_bar.progress(1.0, text="✅ Pipeline complete!")

        except Exception as e:
            st.session_state.pipeline_running = False
            st.error(f"❌ Pipeline error: {str(e)}")
            st.exception(e)

        st.rerun()

elif generate_btn and not user_input:
    st.warning("✏️ Please describe your project first!")


# ╔══════════════════════════════════════════════════════════════════╗
# ║                  HANDLE REVISION REQUEST                        ║
# ╚══════════════════════════════════════════════════════════════════╝
if st.session_state.get("revision_running"):
    st.markdown("---")
    st.markdown("## 🔄 Revision Running...")

    progress_bar = st.progress(0, text="Revising code with your feedback...")
    status_container = st.empty()

    feedback = st.session_state.get("_revision_feedback", "")
    prev_state = st.session_state.pipeline_results

    accumulated_state = dict(prev_state)  # Copy previous state

    try:
        agent_order = ["coder", "reviewer", "finalize"]
        for event in run_revision(prev_state, feedback):
            for node_name, node_output in event.items():
                accumulated_state.update(node_output)

                if node_name in agent_order:
                    step_idx = agent_order.index(node_name) + 1
                    progress = step_idx / len(agent_order)
                    progress_bar.progress(progress, text=f"{'💻' if node_name == 'coder' else '🔍' if node_name == 'reviewer' else '✨'} {node_name.title()} Agent working...")
                    status_container.info(f"✅ **{node_name.title()}** complete!")
                    time.sleep(0.5)

        # Auto-save revised files
        files = accumulated_state.get("generated_files", {})
        if files:
            try:
                save_path = save_generated_files(files, st.session_state.project_name)
                accumulated_state["_save_path"] = save_path
            except Exception:
                pass

        st.session_state.pipeline_results = accumulated_state
        st.session_state.revision_running = False
        progress_bar.progress(1.0, text="✅ Revision complete!")

    except Exception as e:
        st.session_state.revision_running = False
        st.error(f"❌ Revision error: {str(e)}")
        st.exception(e)

    st.rerun()


# ╔══════════════════════════════════════════════════════════════════╗
# ║                     DISPLAY RESULTS                             ║
# ╚══════════════════════════════════════════════════════════════════╝
results = st.session_state.pipeline_results

if results and not st.session_state.pipeline_running and not st.session_state.revision_running:
    st.markdown("---")
    st.markdown("## 🎯 Results")

    files = results.get("generated_files", {})

    # ── Tab layout ─────────────────────────────────────────────────
    tab_names = [
        "📊 Overview",
        "💻 Code & Files",
        "🌐 Live Preview",
        "📋 Project Plan",
        "🏗️ Architecture",
        "🔍 Review & Revise",
        "🧪 Sandbox",
        "🔀 Git Log",
    ]
    tab_overview, tab_code, tab_preview, tab_plan, tab_arch, tab_review, tab_sandbox, tab_git = st.tabs(tab_names)

    # ────────────────────────── OVERVIEW TAB ──────────────────────
    with tab_overview:
        st.success(f"✅ Successfully generated **{len(files)}** files!")

        if results.get("final_output"):
            st.markdown(results["final_output"])

        if results.get("error"):
            st.error(f"⚠️ Error: {results['error']}")

        # File tree
        if files:
            st.markdown("### 📂 Project File Tree")
            tree = get_file_tree_from_dict(files)
            st.code(tree, language="text")

        # Download section
        if files:
            st.markdown("### 📥 Download Project")
            col_zip, col_save, col_info = st.columns([1, 1, 2])

            with col_zip:
                zip_bytes = create_zip_archive(files, st.session_state.project_name)
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_bytes,
                    file_name=f"{st.session_state.project_name}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

            with col_save:
                if st.button("💾 Save to Disk", use_container_width=True):
                    try:
                        save_path = save_generated_files(
                            files, st.session_state.project_name
                        )
                        st.success(f"✅ Saved to: `{save_path}`")
                    except Exception as e:
                        st.error(f"❌ Failed to save: {str(e)}")

            with col_info:
                save_path = results.get("_save_path", "")
                if save_path:
                    st.info(f"📁 Auto-saved to: `{save_path}`")
                else:
                    st.info(f"📁 **{len(files)}** files ready to download/save.")

    # ────────────────────── CODE & FILES TAB ─────────────────────
    with tab_code:
        if files:
            # File selector with extension info
            file_list = list(files.keys())
            selected_file = st.selectbox(
                "📄 Select a file to view:",
                file_list,
                key="file_selector",
            )

            if selected_file:
                # Detect language for syntax highlighting
                ext_map = {
                    ".py": "python", ".js": "javascript", ".jsx": "javascript",
                    ".ts": "typescript", ".tsx": "typescript",
                    ".html": "html", ".css": "css", ".json": "json",
                    ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
                    ".sql": "sql", ".sh": "bash", ".toml": "toml",
                    ".txt": "text", ".env": "text", ".gitignore": "text",
                    ".xml": "xml", ".cfg": "text", ".ini": "text",
                }
                ext = os.path.splitext(selected_file)[1].lower()
                lang = ext_map.get(ext, "text")

                # File info header
                file_content = files[selected_file]
                line_count = file_content.count("\n") + 1
                char_count = len(file_content)

                st.markdown(f"""
                <div class="file-header">
                    📄 {selected_file} &nbsp;·&nbsp; {line_count} lines &nbsp;·&nbsp; {char_count} chars
                </div>
                """, unsafe_allow_html=True)

                st.code(file_content, language=lang, line_numbers=True)

                # Individual file download
                st.download_button(
                    label=f"⬇️ Download {os.path.basename(selected_file)}",
                    data=file_content,
                    file_name=os.path.basename(selected_file),
                    key=f"dl_{selected_file}",
                )
        else:
            st.info("No code generated.")

    # ────────────────────── LIVE PREVIEW TAB ─────────────────────
    with tab_preview:
        # Find HTML files for preview
        html_files = {k: v for k, v in files.items() if k.endswith((".html", ".htm"))}

        if html_files:
            st.markdown("### 🌐 Live UI Preview")
            st.info("💡 This renders the generated HTML directly in the browser.")

            if len(html_files) > 1:
                preview_file = st.selectbox(
                    "Select HTML file to preview:",
                    list(html_files.keys()),
                    key="preview_selector",
                )
            else:
                preview_file = list(html_files.keys())[0]

            html_content = html_files[preview_file]

            # Try to inline CSS files if referenced
            css_files = {k: v for k, v in files.items() if k.endswith(".css")}
            for css_path, css_content in css_files.items():
                css_filename = os.path.basename(css_path)
                # Replace <link> tags with inline <style>
                if css_filename in html_content:
                    # Find and replace the link tag
                    import re
                    link_pattern = rf'<link[^>]*href=["\'][^"\']*{re.escape(css_filename)}["\'][^>]*>'
                    replacement = f"<style>\n{css_content}\n</style>"
                    html_content = re.sub(link_pattern, replacement, html_content)

            # Try to inline JS files if referenced
            js_files = {k: v for k, v in files.items() if k.endswith(".js")}
            for js_path, js_content in js_files.items():
                js_filename = os.path.basename(js_path)
                if js_filename in html_content:
                    import re
                    script_pattern = rf'<script[^>]*src=["\'][^"\']*{re.escape(js_filename)}["\'][^>]*>\s*</script>'
                    replacement = f"<script>\n{js_content}\n</script>"
                    html_content = re.sub(script_pattern, replacement, html_content)

            st.markdown(f"**Previewing:** `{preview_file}`")
            components.html(html_content, height=600, scrolling=True)

        else:
            st.markdown("### 🌐 Live Preview")
            st.warning(
                "No HTML files found in the generated project. "
                "Live preview is available for web projects (HTML/CSS/JS)."
            )
            st.markdown(
                "💡 **Tip:** For non-web projects, use the **Code & Files** tab "
                "to view and download individual files."
            )

    # ────────────────────── PROJECT PLAN TAB ─────────────────────
    with tab_plan:
        plan = results.get("project_plan", "")
        if plan:
            st.markdown(plan)
        else:
            st.info("No project plan generated.")

    # ────────────────────── ARCHITECTURE TAB ─────────────────────
    with tab_arch:
        arch = results.get("architecture_tasks", "")
        if arch:
            st.markdown(arch)
        else:
            st.info("No architecture tasks generated.")

    # ────────────────────── REVIEW & REVISE TAB ──────────────────
    with tab_review:
        review = results.get("review_report", "")
        if review:
            st.markdown("### 📋 Latest Review Report")
            st.markdown(review)
        else:
            st.info("No review report available.")

        # ── User Revision Controls ───────────────────────────────
        st.markdown("---")
        st.markdown("### 🔄 Revise & Regenerate")
        st.markdown(
            "Not satisfied with the code? Provide your feedback below and the "
            "**Coder Agent** will revise the code based on your instructions, "
            "then the **Reviewer** will re-check it."
        )

        revision_feedback = st.text_area(
            "Your feedback / revision instructions:",
            height=150,
            placeholder=(
                "Examples:\n"
                "• Fix the error handling in the database controller\n"
                "• Add input validation for all API endpoints\n"
                "• Make the code more modular with separate utility functions\n"
                "• Add comments explaining the business logic"
            ),
            key="revision_feedback_input",
        )

        col_revise, col_info_rev = st.columns([1, 2])
        with col_revise:
            revise_btn = st.button(
                "🔄 Revise & Regenerate",
                use_container_width=True,
                disabled=st.session_state.revision_running or not revision_feedback,
            )
        with col_info_rev:
            st.caption(
                "⚡ This skips the Planner & Architect and re-runs only "
                "**Coder → Reviewer** with your feedback."
            )

        if revise_btn and revision_feedback:
            st.session_state.revision_running = True
            st.session_state._revision_feedback = revision_feedback
            st.rerun()

    # ────────────────────── SANDBOX TAB ────────────────────────────
    with tab_sandbox:
        execution = results.get("execution_result", "")
        if execution:
            st.markdown("### 🧪 Sandbox Execution Results")
            st.markdown(execution)

            sandbox_attempts = results.get("sandbox_attempts", 0)
            if sandbox_attempts > 0:
                st.info(f"Self-healing attempts: **{sandbox_attempts}** / 2")

            if "FAIL" in execution:
                st.warning(
                    "The generated code has errors. You can:\n"
                    "- Go to **Review & Revise** tab to provide feedback\n"
                    "- Check the error details above for clues\n"
                    "- The sandbox tried to auto-fix up to 2 times"
                )
        else:
            st.info(
                "Sandbox execution results will appear here after code generation.\n\n"
                "The sandbox automatically runs your generated code to catch errors "
                "and triggers self-healing if needed."
            )

    # ────────────────────── GIT LOG TAB ───────────────────────────
    with tab_git:
        git_log = results.get("git_log", "")
        if git_log:
            st.markdown("### 🔀 Git Integration")
            st.markdown(git_log)
        else:
            st.info(
                "Git commit log will appear here after code generation.\n\n"
                "Coder Buddy automatically initializes a git repository, "
                "creates meaningful commit messages per file category, "
                "and commits your project step-by-step."
            )

    # ── Bottom Actions ─────────────────────────────────────────────
    st.markdown("---")
    col_new, col_dl = st.columns([1, 1])
    with col_new:
        if st.button("🆕 Start New Project", use_container_width=True):
            st.session_state.pipeline_results = {}
            st.session_state.completed_agents = []
            st.session_state.active_agent = None
            st.rerun()
    with col_dl:
        if files:
            zip_bytes = create_zip_archive(files, st.session_state.project_name)
            st.download_button(
                label="⬇️ Download All Files (ZIP)",
                data=zip_bytes,
                file_name=f"{st.session_state.project_name}.zip",
                mime="application/zip",
                use_container_width=True,
                key="bottom_zip_dl",
            )
