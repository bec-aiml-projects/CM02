"""
Coder Buddy - Self-Healing Execution Sandbox
===============================================
Runs generated code in an isolated temporary environment,
captures errors, and provides tracebacks for the Coder agent
to auto-fix in a self-healing loop.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional


# Maximum execution time (seconds)
SANDBOX_TIMEOUT = 30

# Maximum output capture (characters)
MAX_OUTPUT = 5000

# File extensions that can be executed
EXECUTABLE_EXTENSIONS = {
    ".py": "python",
    ".js": "node",
    ".ts": "npx ts-node",
    ".sh": "bash",
}


class SandboxResult:
    """Result of running code in the sandbox."""

    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0,
        error_summary: str = "",
        files_tested: list[str] = None,
    ):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.error_summary = error_summary
        self.files_tested = files_tested or []

    def to_report(self) -> str:
        """Generate a human-readable report."""
        status = "PASS" if self.success else "FAIL"
        icon = "✅" if self.success else "❌"

        report_parts = [
            f"## {icon} Sandbox Execution: {status}\n",
            f"**Files tested**: {', '.join(self.files_tested) or 'None'}\n",
            f"**Return code**: {self.return_code}\n",
        ]

        if self.stdout:
            report_parts.append(
                f"\n### 📤 Standard Output\n```\n{self.stdout[:MAX_OUTPUT]}\n```\n"
            )

        if self.stderr:
            report_parts.append(
                f"\n### ⚠️ Standard Error\n```\n{self.stderr[:MAX_OUTPUT]}\n```\n"
            )

        if self.error_summary:
            report_parts.append(
                f"\n### 🔍 Error Analysis\n{self.error_summary}\n"
            )

        return "\n".join(report_parts)

    def to_fix_prompt(self) -> str:
        """Generate a prompt for the Coder agent to fix the errors."""
        if self.success:
            return ""

        return (
            f"## ❌ SANDBOX EXECUTION FAILED — AUTO-FIX REQUIRED\n\n"
            f"The code was executed in a sandbox and produced errors.\n"
            f"You MUST fix these errors and regenerate the code.\n\n"
            f"### Error Output (stderr):\n"
            f"```\n{self.stderr[:3000]}\n```\n\n"
            f"### Standard Output (stdout):\n"
            f"```\n{self.stdout[:1000]}\n```\n\n"
            f"### Files that were tested:\n"
            f"{chr(10).join(f'- `{f}`' for f in self.files_tested)}\n\n"
            f"Fix ALL errors. The code must run without any tracebacks or exceptions.\n"
        )


def run_in_sandbox(
    generated_files: dict[str, str],
    entry_point: Optional[str] = None,
) -> SandboxResult:
    """
    Run generated code in a temporary sandbox directory.

    Parameters
    ----------
    generated_files : dict[str, str]
        Mapping of file paths to their content.
    entry_point : str, optional
        Specific file to execute. If None, auto-detects the entry point.

    Returns
    -------
    SandboxResult
        Result of the execution with stdout, stderr, and status.
    """
    if not generated_files:
        return SandboxResult(
            success=False,
            error_summary="No files to execute.",
        )

    # Create temporary directory
    sandbox_dir = tempfile.mkdtemp(prefix="coderbuddy_sandbox_")

    try:
        # Write all generated files to the sandbox
        for filepath, content in generated_files.items():
            # Sanitize path
            clean_path = filepath.lstrip("/").lstrip("\\")
            if ".." in clean_path:
                continue

            full_path = Path(sandbox_dir) / clean_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

        # Find the entry point file
        if entry_point is None:
            entry_point = _find_entry_point(generated_files)

        if entry_point is None:
            return SandboxResult(
                success=True,
                error_summary="No executable entry point found (no .py/.js files). Skipping execution.",
                files_tested=[],
            )

        # Determine the executor
        ext = Path(entry_point).suffix.lower()
        executor = EXECUTABLE_EXTENSIONS.get(ext)

        if executor is None:
            return SandboxResult(
                success=True,
                error_summary=f"No executor for {ext} files. Skipping.",
                files_tested=[entry_point],
            )

        # Run the code
        entry_path = Path(sandbox_dir) / entry_point
        cmd = f"{executor} \"{entry_path}\""

        # Check if requirements.txt exists and install deps
        req_path = Path(sandbox_dir) / "requirements.txt"
        if req_path.exists() and ext == ".py":
            _install_requirements(sandbox_dir, req_path)

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
            cwd=sandbox_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        success = result.returncode == 0
        error_summary = ""

        if not success:
            error_summary = _analyze_error(result.stderr, entry_point)

        return SandboxResult(
            success=success,
            stdout=result.stdout[:MAX_OUTPUT],
            stderr=result.stderr[:MAX_OUTPUT],
            return_code=result.returncode,
            error_summary=error_summary,
            files_tested=[entry_point],
        )

    except subprocess.TimeoutExpired:
        return SandboxResult(
            success=False,
            stderr=f"Execution timed out after {SANDBOX_TIMEOUT} seconds.",
            error_summary="The code took too long to execute. Check for infinite loops.",
            files_tested=[entry_point] if entry_point else [],
        )
    except Exception as e:
        return SandboxResult(
            success=False,
            stderr=str(e),
            error_summary=f"Sandbox error: {str(e)}",
            files_tested=[entry_point] if entry_point else [],
        )
    finally:
        # Clean up sandbox directory
        try:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        except Exception:
            pass


def _find_entry_point(files: dict[str, str]) -> Optional[str]:
    """
    Auto-detect the entry point file to execute.

    Priority order:
    1. main.py / app.py / index.py / run.py
    2. Any file with `if __name__` guard
    3. Any .py file
    4. index.js / main.js / app.js
    """
    # Priority filenames
    priority_names = [
        "main.py", "app.py", "index.py", "run.py",
        "main.js", "index.js", "app.js",
    ]

    # Check priority names (handle nested paths)
    for priority in priority_names:
        for filepath in files:
            if filepath.endswith(priority):
                return filepath

    # Check for __name__ == "__main__" guard
    for filepath, content in files.items():
        if filepath.endswith(".py") and '__name__' in content and '__main__' in content:
            return filepath

    # Fall back to first .py file
    for filepath in files:
        if filepath.endswith(".py"):
            return filepath

    # Fall back to first .js file
    for filepath in files:
        if filepath.endswith(".js"):
            return filepath

    return None


def _install_requirements(sandbox_dir: str, req_path: Path) -> None:
    """Attempt to install requirements in the sandbox (best effort)."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path),
             "--quiet", "--target", str(Path(sandbox_dir) / "_libs")],
            capture_output=True,
            timeout=60,
        )
    except Exception:
        pass


def _analyze_error(stderr: str, filepath: str) -> str:
    """Provide a brief analysis of the error for the user."""
    if not stderr:
        return "Process exited with non-zero code but no error output."

    lines = stderr.strip().split("\n")

    # Get the last few meaningful lines (usually the actual error)
    error_lines = [l for l in lines if l.strip()]
    if not error_lines:
        return "Unknown error."

    # Common error patterns
    last_line = error_lines[-1]

    if "ModuleNotFoundError" in last_line or "ImportError" in last_line:
        module = last_line.split("'")[-2] if "'" in last_line else "unknown"
        return (
            f"**Missing module**: `{module}`\n"
            f"The code imports a module that isn't installed. "
            f"Add it to requirements.txt or remove the dependency."
        )
    elif "SyntaxError" in last_line:
        return (
            f"**Syntax error** in `{filepath}`\n"
            f"The code has invalid Python syntax. Check indentation, "
            f"brackets, and quotes."
        )
    elif "NameError" in last_line:
        return (
            f"**Undefined variable/function**\n"
            f"A name is used before it's defined. Check import statements "
            f"and variable declarations."
        )
    elif "TypeError" in last_line:
        return (
            f"**Type mismatch**\n"
            f"A function was called with wrong arguments or types. "
            f"Check function signatures."
        )
    elif "FileNotFoundError" in last_line:
        return (
            f"**Missing file**\n"
            f"The code references a file that doesn't exist. "
            f"Check file paths and ensure all needed files are generated."
        )
    else:
        return f"**Error**: `{last_line}`"
