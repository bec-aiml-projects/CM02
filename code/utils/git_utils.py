"""
Coder Buddy - Automated Git Integration
==========================================
Automatically initializes git repositories for generated projects,
creates meaningful commit messages, and commits files step-by-step.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def init_and_commit(
    project_dir: str,
    generated_files: dict[str, str],
    project_name: str = "my_project",
    user_request: str = "",
) -> str:
    """
    Initialize a git repository and commit all generated files
    with meaningful commit messages.

    Parameters
    ----------
    project_dir : str
        Path to the project directory where files are saved.
    generated_files : dict[str, str]
        Mapping of file paths to their content.
    project_name : str
        Name of the project (used in commit messages).
    user_request : str
        Original user request (used in initial commit message).

    Returns
    -------
    str
        Git log summary string.
    """
    try:
        import git
    except ImportError:
        return (
            "Git integration skipped: `gitpython` not installed.\n"
            "Run: `pip install gitpython`"
        )

    project_path = Path(project_dir)
    if not project_path.exists():
        return f"Git error: Project directory does not exist: {project_dir}"

    try:
        # Check if git is available
        git.Git().version()
    except git.GitCommandError:
        return (
            "Git integration skipped: `git` command not found.\n"
            "Please install Git: https://git-scm.com/downloads"
        )

    try:
        # Initialize or open repo
        if (project_path / ".git").exists():
            repo = git.Repo(project_path)
            is_new = False
        else:
            repo = git.Repo.init(project_path)
            is_new = True

        # Configure user if not set
        try:
            repo.config_reader().get_value("user", "name")
        except Exception:
            with repo.config_writer() as cw:
                cw.set_value("user", "name", "Coder Buddy")
                cw.set_value("user", "email", "coderbuddy@ai.local")

        # Create .gitignore if it doesn't exist
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = _generate_gitignore(generated_files)
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            repo.index.add([".gitignore"])
            repo.index.commit("chore: add .gitignore")

        # Group files by category for structured commits
        file_groups = _categorize_files(generated_files)

        commit_count = 0
        for group_name, files in file_groups.items():
            # Ensure files exist on disk
            existing_files = []
            for filepath in files:
                full_path = project_path / filepath
                if full_path.exists():
                    existing_files.append(filepath)

            if not existing_files:
                continue

            # Stage files
            repo.index.add(existing_files)

            # Generate meaningful commit message
            commit_msg = _generate_commit_message(
                group_name, existing_files, project_name
            )

            try:
                repo.index.commit(commit_msg)
                commit_count += 1
            except git.GitCommandError:
                # Nothing to commit (files unchanged)
                pass

        # Generate log summary
        log_summary = _generate_git_log(repo, commit_count, is_new, project_name)
        return log_summary

    except Exception as e:
        return f"Git error: {str(e)}"


def _categorize_files(files: dict[str, str]) -> dict[str, list[str]]:
    """
    Group files into logical categories for structured commits.

    Returns dict mapping category name to list of file paths.
    """
    categories = {
        "config": [],       # Config/setup files
        "core": [],         # Main application logic
        "models": [],       # Data models
        "api": [],          # API/routes
        "ui": [],           # Frontend/templates
        "styles": [],       # CSS/styling
        "tests": [],        # Test files
        "docs": [],         # Documentation
        "utils": [],        # Utilities
        "other": [],        # Everything else
    }

    for filepath in files:
        lower = filepath.lower()
        name = Path(filepath).name.lower()
        ext = Path(filepath).suffix.lower()

        if name in {"requirements.txt", "package.json", "setup.py", "pyproject.toml",
                     ".env.example", "dockerfile", "docker-compose.yml",
                     "makefile", "config.py", "settings.py", ".env"}:
            categories["config"].append(filepath)
        elif name in {"readme.md", "changelog.md", "license", "contributing.md"}:
            categories["docs"].append(filepath)
        elif "test" in lower or "spec" in lower:
            categories["tests"].append(filepath)
        elif ext in {".html", ".jsx", ".tsx", ".vue", ".svelte"}:
            categories["ui"].append(filepath)
        elif ext in {".css", ".scss", ".sass", ".less"}:
            categories["styles"].append(filepath)
        elif "model" in lower or "schema" in lower:
            categories["models"].append(filepath)
        elif "route" in lower or "api" in lower or "endpoint" in lower:
            categories["api"].append(filepath)
        elif "util" in lower or "helper" in lower or "lib" in lower:
            categories["utils"].append(filepath)
        elif name in {"main.py", "app.py", "index.py", "index.js", "main.js",
                       "app.js", "server.py", "server.js"}:
            categories["core"].append(filepath)
        else:
            categories["other"].append(filepath)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def _generate_commit_message(
    category: str,
    files: list[str],
    project_name: str,
) -> str:
    """Generate a meaningful conventional commit message for a file group."""
    prefixes = {
        "config": "chore",
        "core": "feat",
        "models": "feat",
        "api": "feat",
        "ui": "feat",
        "styles": "style",
        "tests": "test",
        "docs": "docs",
        "utils": "feat",
        "other": "feat",
    }

    descriptions = {
        "config": "add project configuration and setup files",
        "core": "implement core application logic",
        "models": "add data models and schemas",
        "api": "implement API routes and endpoints",
        "ui": "add frontend templates and components",
        "styles": "add styles and CSS",
        "tests": "add unit tests",
        "docs": "add project documentation",
        "utils": "add utility functions and helpers",
        "other": "add additional project files",
    }

    prefix = prefixes.get(category, "feat")
    desc = descriptions.get(category, "add project files")

    file_list = ", ".join(Path(f).name for f in files[:5])
    if len(files) > 5:
        file_list += f" (+{len(files) - 5} more)"

    return f"{prefix}({project_name}): {desc}\n\nFiles: {file_list}"


def _generate_gitignore(files: dict[str, str]) -> str:
    """Generate a .gitignore based on the project type."""
    lines = [
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "venv/",
        ".venv/",
        "env/",
        ".env",
        "*.egg-info/",
        "dist/",
        "build/",
        "",
        "# Node",
        "node_modules/",
        "npm-debug.log*",
        "",
        "# IDE",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
    ]

    # Add language-specific ignores
    extensions = {Path(f).suffix for f in files}
    if ".py" in extensions:
        lines.extend([
            "# Python specific",
            ".mypy_cache/",
            ".pytest_cache/",
            "htmlcov/",
            ".coverage",
            "",
        ])
    if ".js" in extensions or ".ts" in extensions:
        lines.extend([
            "# JavaScript/TypeScript",
            "dist/",
            ".next/",
            ".nuxt/",
            "*.tsbuildinfo",
            "",
        ])

    return "\n".join(lines)


def _generate_git_log(
    repo,
    commit_count: int,
    is_new: bool,
    project_name: str,
) -> str:
    """Generate a formatted git log summary."""
    lines = [
        f"## 🔀 Git Integration {'(New Repository)' if is_new else '(Updated)'}\n",
        f"**Repository**: `{repo.working_dir}`",
        f"**Branch**: `{repo.active_branch.name}`",
        f"**Commits added**: {commit_count}\n",
    ]

    # Show recent commits
    try:
        commits = list(repo.iter_commits(max_count=10))
        if commits:
            lines.append("### Recent Commits")
            for c in commits:
                short_hash = c.hexsha[:7]
                timestamp = datetime.fromtimestamp(c.committed_date).strftime("%H:%M:%S")
                first_line = c.message.split("\n")[0]
                lines.append(f"- `{short_hash}` {timestamp} — {first_line}")
    except Exception:
        pass

    return "\n".join(lines)
