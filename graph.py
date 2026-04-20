"""
Coder Buddy - LangGraph Pipeline
===================================
Orchestrates the multi-agent workflow using LangGraph.

Flow:
  Planner -> Architect -> Coder -> Reviewer -> Sandbox -> Git -> Finalize
                           ^         |
                           +----<----+  (revision loop if NEEDS_REVISION)
                           ^                   |
                           +------<------------+  (self-healing if sandbox fails)
"""

from langgraph.graph import StateGraph, END
from state import CoderBuddyState
from agents.planner import run_planner
from agents.architect import run_architect
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from utils.sandbox import run_in_sandbox
from utils.git_utils import init_and_commit
from utils.file_utils import save_generated_files


# ── Maximum self-healing sandbox attempts ────────────────────────
MAX_SANDBOX_ATTEMPTS = 2


def should_revise(state: CoderBuddyState) -> str:
    """
    Conditional edge after the Reviewer node.
    Routes back to the Coder if revision is needed, otherwise to sandbox.
    """
    if state.get("error"):
        return "finalize"
    if state.get("needs_revision", False):
        return "coder"
    return "sandbox"


def should_sandbox_retry(state: CoderBuddyState) -> str:
    """
    Conditional edge after the Sandbox node.
    If sandbox execution failed and we haven't exceeded attempts,
    route back to the Coder for self-healing. Otherwise proceed to git.
    """
    execution_result = state.get("execution_result", "")
    sandbox_attempts = state.get("sandbox_attempts", 0)

    if "FAIL" in execution_result and sandbox_attempts < MAX_SANDBOX_ATTEMPTS:
        return "coder"  # Self-healing: send error back to Coder
    return "git_commit"


def run_sandbox_node(state: CoderBuddyState) -> dict:
    """
    LangGraph node: Run generated code in a sandbox.
    Captures output and errors for self-healing.
    """
    files = state.get("generated_files", {})

    if not files:
        return {
            "execution_result": "No files to execute.",
            "sandbox_attempts": state.get("sandbox_attempts", 0),
        }

    # Check if there are any executable files
    has_executable = any(
        f.endswith((".py", ".js", ".ts", ".sh"))
        for f in files
    )

    if not has_executable:
        return {
            "execution_result": (
                "## Sandbox Skipped\n"
                "No executable files found (.py, .js, .ts). "
                "This is a static project (HTML/CSS) — no sandbox needed."
            ),
            "sandbox_attempts": state.get("sandbox_attempts", 0),
        }

    result = run_in_sandbox(files)
    report = result.to_report()

    # If sandbox failed, inject error info into review_report for the Coder
    current_attempts = state.get("sandbox_attempts", 0) + 1

    update = {
        "execution_result": report,
        "sandbox_attempts": current_attempts,
    }

    if not result.success and current_attempts <= MAX_SANDBOX_ATTEMPTS:
        # Inject sandbox errors as review feedback for self-healing
        update["review_report"] = result.to_fix_prompt()
        update["needs_revision"] = True

    return update


def run_git_node(state: CoderBuddyState) -> dict:
    """
    LangGraph node: Auto-commit generated files to git.
    """
    files = state.get("generated_files", {})
    if not files:
        return {"git_log": "No files to commit."}

    # First save files to disk (needed for git)
    project_name = "generated_project"
    # Try to extract project name from user request
    user_req = state.get("user_request", "")
    if user_req:
        words = user_req.split()[:3]
        project_name = "_".join(w.lower() for w in words if w.isalnum())
        if not project_name:
            project_name = "generated_project"

    try:
        project_dir = save_generated_files(files, project_name)
        git_log = init_and_commit(
            project_dir=project_dir,
            generated_files=files,
            project_name=project_name,
            user_request=user_req,
        )
        return {"git_log": git_log}
    except Exception as e:
        return {"git_log": f"Git integration error: {str(e)}"}


def finalize(state: CoderBuddyState) -> dict:
    """
    Final node: consolidates all outputs into a final summary for the user.
    """
    files = state.get("generated_files", {})
    review = state.get("review_report", "No review performed.")
    plan = state.get("project_plan", "")
    tasks = state.get("architecture_tasks", "")
    error = state.get("error")
    execution = state.get("execution_result", "")
    git_log = state.get("git_log", "")

    if error:
        final = f"## Error Occurred\n\n{error}"
    else:
        file_list = "\n".join([f"  - `{path}`" for path in files.keys()])
        final = (
            f"## Project Generation Complete!\n\n"
            f"### Generated Files ({len(files)} files):\n{file_list}\n\n"
            f"### Review Report:\n{review}\n"
        )
        if execution:
            final += f"\n### Sandbox Execution:\n{execution}\n"
        if git_log:
            final += f"\n### Git:\n{git_log}\n"

    return {"final_output": final}


def build_graph() -> StateGraph:
    """
    Builds and compiles the multi-agent LangGraph workflow.

    Flow: Planner -> Architect -> Coder -> Reviewer --(revise?)--> Coder
                                                     +--> Sandbox --(heal?)--> Coder
                                                                   +--> Git -> Finalize
    """
    graph = StateGraph(CoderBuddyState)

    # ── Add nodes ───────────────────────────────────────────────────
    graph.add_node("planner", run_planner)
    graph.add_node("architect", run_architect)
    graph.add_node("coder", run_coder)
    graph.add_node("reviewer", run_reviewer)
    graph.add_node("sandbox", run_sandbox_node)
    graph.add_node("git_commit", run_git_node)
    graph.add_node("finalize", finalize)

    # ── Define edges ────────────────────────────────────────────────
    graph.set_entry_point("planner")
    graph.add_edge("planner", "architect")
    graph.add_edge("architect", "coder")
    graph.add_edge("coder", "reviewer")

    # Reviewer -> revise or proceed to sandbox
    graph.add_conditional_edges(
        "reviewer",
        should_revise,
        {
            "coder": "coder",
            "sandbox": "sandbox",
            "finalize": "finalize",
        },
    )

    # Sandbox -> self-heal or proceed to git
    graph.add_conditional_edges(
        "sandbox",
        should_sandbox_retry,
        {
            "coder": "coder",
            "git_commit": "git_commit",
        },
    )

    graph.add_edge("git_commit", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def run_pipeline(user_request: str, codebase_context: str = "", design_description: str = ""):
    """
    Convenience function to run the full pipeline.

    Parameters
    ----------
    user_request : str
        The user's natural-language project description.
    codebase_context : str
        RAG-retrieved context from existing codebase (optional).
    design_description : str
        Vision-generated description of uploaded wireframe (optional).

    Yields
    ------
    dict
        Intermediate state updates from each agent step.
    """
    compiled_graph = build_graph()

    initial_state: CoderBuddyState = {
        "user_request": user_request,
        "project_plan": "",
        "architecture_tasks": "",
        "generated_files": {},
        "review_report": "",
        "needs_revision": False,
        "revision_count": 0,
        "final_output": "",
        "error": None,
        # New feature fields
        "codebase_context": codebase_context,
        "design_description": design_description,
        "execution_result": "",
        "sandbox_attempts": 0,
        "git_log": "",
    }

    for event in compiled_graph.stream(initial_state):
        yield event


def run_revision(previous_state: dict, user_feedback: str):
    """
    Re-run only the Coder -> Reviewer portion of the pipeline
    with user-provided feedback. Skips Planner and Architect.
    """
    combined_feedback = (
        f"## User Feedback (MUST ADDRESS ALL POINTS):\n{user_feedback}\n\n"
    )
    if previous_state.get("review_report"):
        combined_feedback += (
            f"## Previous Automated Review:\n{previous_state['review_report']}"
        )

    revision_state: CoderBuddyState = {
        "user_request": previous_state.get("user_request", ""),
        "project_plan": previous_state.get("project_plan", ""),
        "architecture_tasks": previous_state.get("architecture_tasks", ""),
        "generated_files": previous_state.get("generated_files", {}),
        "review_report": combined_feedback,
        "needs_revision": True,
        "revision_count": 0,
        "final_output": "",
        "error": None,
        # Preserve feature fields
        "codebase_context": previous_state.get("codebase_context", ""),
        "design_description": previous_state.get("design_description", ""),
        "execution_result": "",
        "sandbox_attempts": 0,
        "git_log": "",
    }

    # Build a mini-graph: Coder -> Reviewer -> Finalize
    graph = StateGraph(CoderBuddyState)
    graph.add_node("coder", run_coder)
    graph.add_node("reviewer", run_reviewer)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("coder")
    graph.add_edge("coder", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        lambda s: "coder" if s.get("needs_revision") else "finalize",
        {
            "coder": "coder",
            "finalize": "finalize",
        },
    )
    graph.add_edge("finalize", END)

    compiled = graph.compile()
    for event in compiled.stream(revision_state):
        yield event
