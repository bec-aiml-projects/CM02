"""
Coder Buddy - RAG Codebase Context
=====================================
Loads an existing project's source files, embeds them into a vector store,
and provides semantic search for the Architect agent to understand
existing code structure before adding new features.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional


# Supported code file extensions
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".sql", ".sh",
    ".md", ".txt", ".env", ".cfg", ".ini", ".conf",
}

# Directories to skip
SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".venv", "venv", "env",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", "dist",
    "build", "egg-info", ".tox", ".nox", ".eggs",
}

# Max file size to index (500KB)
MAX_FILE_SIZE = 500_000


def load_project_files(project_path: str) -> list[dict]:
    """
    Recursively load all source code files from a project directory.

    Parameters
    ----------
    project_path : str
        Path to the root of the existing project.

    Returns
    -------
    list[dict]
        List of dicts with 'path', 'content', and 'extension' keys.
    """
    files = []
    root = Path(project_path)

    if not root.exists() or not root.is_dir():
        return files

    for filepath in root.rglob("*"):
        # Skip directories in the exclude list
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue

        if not filepath.is_file():
            continue

        ext = filepath.suffix.lower()
        if ext not in CODE_EXTENSIONS:
            continue

        if filepath.stat().st_size > MAX_FILE_SIZE:
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            relative_path = str(filepath.relative_to(root)).replace("\\", "/")
            files.append({
                "path": relative_path,
                "content": content,
                "extension": ext,
            })
        except Exception:
            continue

    return files


def _chunk_code(content: str, filepath: str, chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    """
    Split a code file into overlapping chunks for embedding.

    Uses line-aware splitting to avoid breaking in the middle of functions.
    """
    lines = content.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0

    for i, line in enumerate(lines):
        current_chunk.append(line)
        current_size += len(line) + 1

        if current_size >= chunk_size:
            chunk_text = "\n".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "source": filepath,
                    "start_line": i - len(current_chunk) + 2,
                    "end_line": i + 1,
                },
            })
            # Keep overlap
            overlap_lines = max(1, len(current_chunk) * overlap // current_size)
            current_chunk = current_chunk[-overlap_lines:]
            current_size = sum(len(l) + 1 for l in current_chunk)

    # Don't forget the last chunk
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        chunks.append({
            "content": chunk_text,
            "metadata": {
                "source": filepath,
                "start_line": len(lines) - len(current_chunk) + 1,
                "end_line": len(lines),
            },
        })

    return chunks


def build_vector_store(project_files: list[dict]):
    """
    Build a FAISS vector store from project files.

    Uses HuggingFace sentence-transformers for local, free embeddings.

    Parameters
    ----------
    project_files : list[dict]
        List of file dicts from load_project_files().

    Returns
    -------
    FAISS vector store instance, or None if building fails.
    """
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.documents import Document
    except ImportError as e:
        print(f"RAG dependencies not installed: {e}")
        print("Run: pip install faiss-cpu sentence-transformers langchain-community")
        return None

    # Chunk all files
    all_chunks = []
    for file_info in project_files:
        chunks = _chunk_code(file_info["content"], file_info["path"])
        for chunk in chunks:
            doc = Document(
                page_content=f"File: {chunk['metadata']['source']}\n\n{chunk['content']}",
                metadata=chunk["metadata"],
            )
            all_chunks.append(doc)

    if not all_chunks:
        return None

    # Create embeddings (uses all-MiniLM-L6-v2 by default, ~80MB first download)
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    # Build FAISS index
    vector_store = FAISS.from_documents(all_chunks, embeddings)
    return vector_store


def search_codebase(vector_store, query: str, top_k: int = 5) -> str:
    """
    Search the codebase vector store for relevant code snippets.

    Parameters
    ----------
    vector_store : FAISS
        The built vector store.
    query : str
        The search query (e.g., user's feature request).
    top_k : int
        Number of top results to return.

    Returns
    -------
    str
        Formatted string of relevant code snippets with file paths.
    """
    if vector_store is None:
        return ""

    results = vector_store.similarity_search(query, k=top_k)

    if not results:
        return "No relevant code found in the existing codebase."

    context_parts = ["## Existing Codebase Context (from RAG search)\n"]
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "unknown")
        start = doc.metadata.get("start_line", "?")
        end = doc.metadata.get("end_line", "?")
        context_parts.append(
            f"### Snippet {i} — `{source}` (lines {start}-{end})\n"
            f"```\n{doc.page_content}\n```\n"
        )

    return "\n".join(context_parts)


def get_project_summary(project_files: list[dict]) -> str:
    """
    Generate a quick text summary of the project structure.

    Returns a file tree and basic stats without needing embeddings.
    """
    if not project_files:
        return "No files found in the project."

    # Build file tree
    tree_lines = [f"**Project: {len(project_files)} files**\n"]

    # Group by directory
    dirs: dict[str, list[str]] = {}
    for f in project_files:
        parts = f["path"].split("/")
        if len(parts) > 1:
            dir_name = "/".join(parts[:-1])
        else:
            dir_name = "."
        if dir_name not in dirs:
            dirs[dir_name] = []
        dirs[dir_name].append(parts[-1])

    for dir_name in sorted(dirs.keys()):
        tree_lines.append(f"  {dir_name}/")
        for fname in sorted(dirs[dir_name]):
            tree_lines.append(f"    - {fname}")

    return "\n".join(tree_lines)
