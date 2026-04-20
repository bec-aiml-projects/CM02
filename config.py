"""
Coder Buddy - Configuration Module
===================================
Loads environment variables and provides LLM initialization
for all agents in the multi-agent pipeline.
Includes automatic retry logic for rate-limited APIs.

IMPORTANT: All settings are read DYNAMICALLY from os.environ
so that the Streamlit sidebar can override them at runtime.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

# ── Output Settings (static, read once) ─────────────────────────────
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./generated_projects")


def wait_for_rate_limit():
    """
    Pause between agent calls to avoid hitting free-tier rate limits.
    Reads the RETRY_DELAY from environment DYNAMICALLY (default 10 seconds).
    """
    delay = int(os.environ.get("RETRY_DELAY", "10"))
    if delay > 0:
        time.sleep(delay)


def get_llm():
    """
    Returns a LangChain LLM instance based on the configured provider.
    Supports OpenAI, Google Gemini, and Groq Cloud.

    All settings are read DYNAMICALLY from os.environ so that
    the Streamlit sidebar can change them at runtime.
    """
    # Read ALL settings dynamically each time get_llm() is called
    provider = os.environ.get("LLM_PROVIDER", "google").lower()
    model = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
    max_retries = int(os.environ.get("MAX_RETRIES", "3"))

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    google_key = os.environ.get("GOOGLE_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is not set. Please enter it in the sidebar.")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=openai_key,
            max_retries=max_retries,
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not google_key:
            raise ValueError("GOOGLE_API_KEY is not set. Please enter it in the sidebar.")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=google_key,
            max_retries=max_retries,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq
        if not groq_key:
            raise ValueError("GROQ_API_KEY is not set. Please enter it in the sidebar.")
        return ChatGroq(
            model=model,
            temperature=temperature,
            groq_api_key=groq_key,
            max_retries=max_retries,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            "Use 'openai', 'google', or 'groq'."
        )
