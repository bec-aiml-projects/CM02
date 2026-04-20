"""
Coder Buddy - Architect Agent
================================
The second agent in the pipeline. Takes the Planner's high-level
project plan and translates it into detailed, actionable engineering
tasks for the Coder Agent.

Enhanced with RAG codebase context to understand existing projects.
"""

from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, wait_for_rate_limit


ARCHITECT_SYSTEM_PROMPT = """You are the Senior Software Architect for 'Coder Buddy', an elite AI development team.

Your job is to take a high-level project plan (produced by the Planner Agent) and translate it into a precise set of engineering implementation tasks.

{codebase_context}

You MUST output your tasks in the following EXACT structure using markdown:

## Implementation Tasks

For EACH file that needs to be created, output a task block like this:

### Task: [filename.ext]
- **File Path**: `relative/path/to/file.ext`
- **Language**: Python / JavaScript / HTML / CSS / etc.
- **Purpose**: One-line description of what this file does.

#### Detailed Specifications:
1. **Imports / Dependencies**: List exactly which modules / libraries to import.
2. **Classes**: For each class, specify:
   - Class name and what it inherits from (if anything).
   - Constructor parameters with types.
   - Methods: name, parameters, return type, and a brief description of logic.
3. **Functions**: For standalone functions:
   - Function name, parameters with types, return type.
   - Step-by-step logic description (pseudocode-level).
4. **Constants / Configuration**: Any constants, env vars, or config values.
5. **Error Handling**: Specific error cases to handle and how.
6. **Connections**: How this file connects to other files in the project.

#### Implementation Notes:
- Any special patterns to follow (singleton, factory, etc.).
- Performance considerations.
- Security considerations.

## Execution Order
List the files in the order they should be implemented (dependencies first).

## Integration Points
Describe how the components connect and communicate.

RULES:
- Do NOT write actual code. Provide specifications detailed enough for a Coder to implement.
- Ensure consistent naming conventions across all tasks.
- Every function must have defined inputs, outputs, and error cases.
- Think about testability — each component should be independently testable.
- If existing codebase context is provided, RESPECT the existing code patterns, naming conventions, and architecture. New features should integrate seamlessly with existing code.
"""

ARCHITECT_USER_PROMPT = """Here is the project plan from the Planner Agent:

---
{project_plan}
---

Original user request for context:
---
{user_request}
---

Translate this plan into detailed, actionable implementation tasks following the required structure."""


def create_architect_chain(codebase_context: str = ""):
    """Creates and returns the Architect Agent's LLM chain."""
    llm = get_llm()

    # Inject codebase context into the system prompt
    system_prompt = ARCHITECT_SYSTEM_PROMPT.replace(
        "{codebase_context}",
        codebase_context if codebase_context else
        "(No existing codebase context provided — this is a new project.)"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", ARCHITECT_USER_PROMPT),
    ])
    return prompt | llm


def run_architect(state: dict) -> dict:
    """
    LangGraph node function for the Architect Agent.

    Reads `project_plan` and `user_request` from state,
    generates detailed architecture tasks, and writes to `architecture_tasks`.

    If `codebase_context` is available in state (from RAG), it's injected
    into the system prompt so the Architect understands existing code.
    """
    try:
        wait_for_rate_limit()

        # Get RAG context if available
        codebase_context = state.get("codebase_context", "")
        chain = create_architect_chain(codebase_context)

        response = chain.invoke({
            "project_plan": state["project_plan"],
            "user_request": state["user_request"],
        })
        return {
            "architecture_tasks": response.content,
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
            "architecture_tasks": "",
            "error": f"Architect Agent Error: {error_msg}{suggestion}",
        }
