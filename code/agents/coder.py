"""
Coder Buddy - Coder Agent
============================
The third agent in the pipeline. Takes the Architect's detailed
tasks and generates actual, production-ready code for each file.
"""

import json
import re
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm, wait_for_rate_limit


CODER_SYSTEM_PROMPT = """You are the Expert Software Developer for 'Coder Buddy', an elite AI development team.

Your job is to take the Architect's detailed implementation tasks and write production-quality code for every file specified.

OUTPUT FORMAT — THIS IS CRITICAL:
You MUST output ONLY a valid JSON object with no extra text before or after it.
The JSON must have this structure:

{{
    "files": {{
        "relative/path/to/file1.py": "full file content here...",
        "relative/path/to/file2.html": "full file content here..."
    }}
}}

IMPORTANT RULES:
- Output ONLY the JSON object. No markdown, no explanations, no code fences.
- Do NOT wrap the JSON in ```json ``` code blocks.
- Every file path from the architecture tasks must appear in your output.
- Use proper file extensions (.py, .html, .css, .js, .json, .md, .txt, .yaml, .toml, etc.)
- String values must have newlines escaped as \\n, quotes escaped as \\", and backslashes as \\\\
- The code must be COMPLETE — no placeholders, no TODOs.

CODE QUALITY REQUIREMENTS:
1. **Complete**: Every file must be fully implemented — no placeholders, no TODOs, no "implement here".
2. **Documented**: Include docstrings for all classes and functions. Add inline comments for complex logic.
3. **Error Handling**: Implement try/except blocks where appropriate. Handle edge cases.
4. **Type Hints**: Use Python type hints for all function signatures (if Python).
5. **Best Practices**: Follow PEP 8 (Python), ESLint standards (JS), and language-specific conventions.
6. **Imports**: Include all necessary imports at the top of each file.
7. **DRY**: Don't repeat yourself — use helper functions and shared utilities.

RULES:
- Output ONLY the JSON object. No markdown, no explanations, no code fences.
- Every file path from the architecture tasks must appear in your output.
- The code must work together as a cohesive project.
- If you receive review feedback, incorporate ALL the reviewer's suggestions.
"""

CODER_USER_PROMPT = """Here are the detailed implementation tasks from the Architect Agent:

---
{architecture_tasks}
---

Original user request for context:
---
{user_request}
---

{review_feedback}

Generate the complete code for EVERY file. Output ONLY a raw JSON object — do NOT use markdown code fences."""


CODER_REVISION_PROMPT = """The Reviewer Agent found issues with your code. Here is the review report:

---
REVIEW FEEDBACK:
{review_report}
---

Here is your previous code output that needs to be revised:
{previous_files}

Fix ALL identified issues and output the complete revised JSON."""


def create_coder_chain():
    """Creates and returns the Coder Agent's LLM chain."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", CODER_SYSTEM_PROMPT),
        ("human", CODER_USER_PROMPT),
    ])
    return prompt | llm


def _parse_code_response(content: str) -> dict[str, str]:
    """
    Parse the Coder's response to extract files.

    Handles multiple output formats that LLMs commonly produce:
    1. Pure JSON: {"files": {"path": "content"}}
    2. JSON wrapped in markdown code fences: ```json {...} ```
    3. Markdown format with file headers and code blocks
    4. Mixed formats

    Returns a dict mapping file paths to their content.
    """
    cleaned = content.strip()

    # ── Strategy 1: Try direct JSON parse ────────────────────────
    result = _try_parse_json(cleaned)
    if result:
        return result

    # ── Strategy 2: Remove markdown code fences and try JSON ─────
    unwrapped = _strip_code_fences(cleaned)
    if unwrapped != cleaned:
        result = _try_parse_json(unwrapped)
        if result:
            return result

    # ── Strategy 3: Find JSON object in the text ─────────────────
    result = _extract_json_from_text(cleaned)
    if result:
        return result

    # ── Strategy 4: Parse markdown-style file blocks ─────────────
    result = _parse_markdown_files(cleaned)
    if result:
        return result

    # ── Fallback: Return raw content with guessed extension ──────
    ext = _guess_extension(cleaned)
    return {f"generated_output{ext}": cleaned}


def _try_parse_json(text: str) -> dict[str, str] | None:
    """Try to parse text as JSON and extract files dict."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "files" in data and isinstance(data["files"], dict):
                return data["files"]
            # Check if top-level keys look like file paths
            if all(_looks_like_filepath(k) for k in data.keys()):
                return data
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ``` or ``` ... ```)."""
    # Match ```json\n...\n``` or ```\n...\n```
    pattern = r'^```(?:json|JSON)?\s*\n(.*?)\n\s*```\s*$'
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Also try without requiring end of string (in case there's trailing text)
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (fence)
        lines = lines[1:]
        # Find and remove last fence
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                lines = lines[:i]
                break
        return "\n".join(lines).strip()
    
    return text


def _extract_json_from_text(text: str) -> dict[str, str] | None:
    """Try to find and extract a JSON object from within text."""
    # Find the outermost { ... } in the text
    brace_depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start != -1:
                candidate = text[start:i + 1]
                result = _try_parse_json(candidate)
                if result:
                    return result
                # Reset and keep looking
                start = -1
    return None


def _parse_markdown_files(text: str) -> dict[str, str] | None:
    """
    Parse LLM output that uses markdown-style file headers with code blocks.

    Handles formats like:
        ### `filename.py`
        ```python
        code here...
        ```

    Or:
        **filename.py**
        ```
        code here...
        ```

    Or:
        // filename.js
        ```javascript
        code here...
        ```
    """
    files = {}

    # Pattern 1: ### `filename` or **filename** or ## filename followed by code block
    # Match file header patterns
    file_header_pattern = re.compile(
        r'(?:^|\n)'                              # start of line
        r'(?:#{1,4}\s*)?'                        # optional markdown headers
        r'(?:\*\*)?'                              # optional bold
        r'[`\'"]*'                                # optional backticks/quotes
        r'([\w\-./\\]+\.[\w]+)'                  # filename with extension (captured)
        r'[`\'"]*'                                # optional backticks/quotes
        r'(?:\*\*)?'                              # optional bold
        r'[:\s]*\n'                               # colon/whitespace, then newline
        r'```[\w]*\n'                             # opening code fence
        r'(.*?)'                                  # code content (captured)
        r'\n```',                                 # closing code fence
        re.DOTALL
    )

    for match in file_header_pattern.finditer(text):
        filepath = match.group(1).strip()
        code = match.group(2)
        files[filepath] = code

    # Pattern 2: Just code blocks with filenames in comments at top
    if not files:
        code_block_pattern = re.compile(
            r'```[\w]*\n'                        # opening fence
            r'(?:#|//|/\*|<!--)\s*'              # comment start
            r'(?:File|Filename)?:?\s*'           # optional "File:" prefix
            r'([\w\-./\\]+\.[\w]+)'              # filename (captured)
            r'.*?\n'                              # rest of comment line
            r'(.*?)'                              # code content (captured)
            r'\n```',                             # closing fence
            re.DOTALL
        )
        for match in code_block_pattern.finditer(text):
            filepath = match.group(1).strip()
            code = match.group(2)
            files[filepath] = code

    # Pattern 3: FILE: path/to/file or --- path/to/file --- followed by code
    if not files:
        file_section_pattern = re.compile(
            r'(?:FILE|File|FILENAME|Filename)[:\s]+'
            r'[`\'"]*'
            r'([\w\-./\\]+\.[\w]+)'              # filename
            r'[`\'"]*'
            r'[\s\-]*\n'
            r'```[\w]*\n'                         # code fence
            r'(.*?)'                              # code content
            r'\n```',
            re.DOTALL
        )
        for match in file_section_pattern.finditer(text):
            filepath = match.group(1).strip()
            code = match.group(2)
            files[filepath] = code

    return files if files else None


def _looks_like_filepath(key: str) -> bool:
    """Check if a string looks like a file path (has extension)."""
    return bool(re.match(r'^[\w\-./\\]+\.[\w]+$', key))


def _guess_extension(content: str) -> str:
    """Guess file extension based on content patterns."""
    content_lower = content[:500].lower()
    if "<!doctype html" in content_lower or "<html" in content_lower:
        return ".html"
    elif "import " in content_lower and "def " in content_lower:
        return ".py"
    elif "function " in content_lower or "const " in content_lower:
        return ".js"
    elif "body {" in content_lower or ".container" in content_lower:
        return ".css"
    elif content_lower.strip().startswith("{"):
        return ".json"
    return ".txt"


def run_coder(state: dict) -> dict:
    """
    LangGraph node function for the Coder Agent.

    Reads `architecture_tasks` and optionally `review_report` from state,
    generates code for all files, and writes to `generated_files`.
    """
    try:
        wait_for_rate_limit()
        chain = create_coder_chain()

        # Build review feedback section
        review_feedback = ""
        if state.get("needs_revision") and state.get("review_report"):
            previous_files_str = json.dumps(state.get("generated_files", {}), indent=2)
            review_feedback = (
                f"⚠️ REVISION REQUIRED — The Reviewer found issues:\n"
                f"{state['review_report']}\n\n"
                f"Previous code:\n{previous_files_str}\n\n"
                f"Fix ALL issues and regenerate the complete code."
            )

        response = chain.invoke({
            "architecture_tasks": state["architecture_tasks"],
            "user_request": state["user_request"],
            "review_feedback": review_feedback,
        })

        files = _parse_code_response(response.content)

        return {
            "generated_files": files,
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
            "generated_files": {},
            "error": f"Coder Agent Error: {error_msg}{suggestion}",
        }
