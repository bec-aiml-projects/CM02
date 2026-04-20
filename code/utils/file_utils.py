"""
Coder Buddy - File Utilities
================================
Handles saving generated project files to disk,
ZIP packaging, and other file-system operations.
"""

import os
import io
import zipfile
from pathlib import Path
from config import OUTPUT_DIR


def save_generated_files(
    files: dict[str, str],
    project_name: str = "my_project",
) -> str:
    """
    Save generated code files to the output directory with proper extensions.

    Parameters
    ----------
    files : dict[str, str]
        Mapping of relative file paths to their content.
    project_name : str
        Name of the project subdirectory.

    Returns
    -------
    str
        The absolute path to the saved project directory.
    """
    # Sanitize project name
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in project_name
    ).strip("_")

    if not safe_name:
        safe_name = "generated_project"

    project_dir = Path(OUTPUT_DIR) / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for relative_path, content in files.items():
        # Security: prevent path traversal
        clean_path = relative_path.lstrip("/").lstrip("\\")
        if ".." in clean_path:
            continue

        file_path = project_dir / clean_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        saved_files.append(str(file_path))

    return str(project_dir.resolve())


def create_zip_archive(files: dict[str, str], project_name: str = "my_project") -> bytes:
    """
    Create a ZIP archive of the generated files in memory.

    Parameters
    ----------
    files : dict[str, str]
        Mapping of relative file paths to their content.
    project_name : str
        Root folder name inside the ZIP.

    Returns
    -------
    bytes
        The ZIP file content as bytes for download.
    """
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in project_name
    ).strip("_") or "project"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for relative_path, content in files.items():
            clean_path = relative_path.lstrip("/").lstrip("\\")
            if ".." in clean_path:
                continue
            archive_path = f"{safe_name}/{clean_path}"
            zf.writestr(archive_path, content)

    return buffer.getvalue()


def get_file_tree(directory: str, prefix: str = "") -> str:
    """
    Generate a visual file tree string for a directory.

    Parameters
    ----------
    directory : str
        Path to the root directory.
    prefix : str
        Prefix for indentation (used in recursion).

    Returns
    -------
    str
        A formatted file tree string.
    """
    path = Path(directory)
    if not path.is_dir():
        return f"Not a directory: {directory}"

    entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = []

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.append(get_file_tree(str(entry), prefix + extension))

    return "\n".join(lines)


def get_file_tree_from_dict(files: dict[str, str]) -> str:
    """
    Generate a visual file tree from the generated files dictionary.

    Parameters
    ----------
    files : dict[str, str]
        Mapping of relative file paths to their content.

    Returns
    -------
    str
        A formatted file tree string.
    """
    if not files:
        return "(no files)"

    # Build tree structure
    tree: dict = {}
    for path in sorted(files.keys()):
        parts = path.replace("\\", "/").strip("/").split("/")
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    def render(node: dict, prefix: str = "") -> list[str]:
        lines = []
        items = list(node.items())
        for i, (name, children) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if children:
                ext = "    " if is_last else "│   "
                lines.extend(render(children, prefix + ext))
        return lines

    return "\n".join(render(tree))
