"""
Coder Buddy - Planner Agent
==============================
The first agent in the pipeline. Takes the user's natural-language
request and produces a structured, high-level project plan.
"""

from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, wait_for_rate_limit


PLANNER_SYSTEM_PROMPT = """You are the Lead Project Planner for 'Coder Buddy', an elite AI development team.

Your objective is to take a user's natural language request and break it down into a comprehensive, high-level project plan.

You MUST output your plan in the following EXACT structure using markdown formatting:

## Project Overview
A brief summary of what is being built, its purpose, and the problem it solves.

## Tech Stack Requirements
- List ALL necessary libraries, frameworks, and tools.
- Specify any environment variables or external services required.
- Note version constraints if applicable.

## File Structure
```
project_root/
├── folder/
│   ├── file.py
│   └── ...
└── ...
```
Provide a complete tree representation of the directories and files needed.

## Component Breakdown
For EACH core file in the file structure, provide:
- **File path**: The relative path.
- **Purpose**: What this file does.
- **Key elements**: Classes, functions, or components it should contain.
- **Dependencies**: What it imports or depends on.

## Data Flow
Describe how data moves through the application from input to output.

## Key Design Decisions
List any important architectural decisions and their rationale.

RULES:
- Do NOT write any actual code. Focus entirely on architecture and design.
- Be thorough — the Architect Agent depends on a complete plan.
- Think about error handling, edge cases, and scalability.
- If the user's request is vague, make reasonable assumptions and document them.
"""

PLANNER_USER_PROMPT = """Here is the user's project request:

---
{user_request}
---

Analyze this request and produce a comprehensive project plan following the required structure."""


def create_planner_chain():
    """Creates and returns the Planner Agent's LLM chain."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", PLANNER_USER_PROMPT),
    ])
    return prompt | llm


def run_planner(state: dict) -> dict:
    """
    LangGraph node function for the Planner Agent.

    Reads `user_request` from state, generates a project plan,
    and writes it to `project_plan`.

    If `design_description` is available (from vision module),
    it's appended to the user request for UI-aware planning.
    """
    try:
        wait_for_rate_limit()
        chain = create_planner_chain()

        # Combine user request with design description if available
        user_request = state["user_request"]
        design_desc = state.get("design_description", "")
        if design_desc:
            user_request += (
                "\n\n## UI Design Reference (from uploaded wireframe/sketch):\n"
                f"{design_desc}\n\n"
                "IMPORTANT: The UI should match the uploaded design as closely as possible. "
                "Use the design description above to plan the frontend layout, "
                "components, colors, and interactions."
            )

        response = chain.invoke({"user_request": user_request})
        return {
            "project_plan": response.content,
            "error": None,
        }
    except Exception as e:
        error_msg = str(e)
        suggestion = ""
        if any(kw in error_msg.upper() for kw in ["429", "RESOURCE_EXHAUSTED", "QUOTA"]):
            suggestion = (
                " 💡 TIP: Switch to Groq Cloud (free & fast) — "
                "get your key at https://console.groq.com/keys"
            )
        return {
            "project_plan": "",
            "error": f"Planner Agent Error: {error_msg}{suggestion}",
        }


