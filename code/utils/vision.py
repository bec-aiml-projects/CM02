"""
Coder Buddy - Vision Module (Design-to-Code)
===============================================
Processes uploaded wireframe/sketch images using vision-capable LLMs
to generate detailed text descriptions of UI layouts.
The description is then fed to the Planner Agent.
"""

import os
import base64
from typing import Optional


VISION_PROMPT = """You are a UI/UX expert analyzing a wireframe or design sketch.

Describe the UI layout in EXTREME DETAIL so a developer can recreate it exactly. Include:

1. **Overall Layout**: Page structure, grid system, number of sections
2. **Header/Navigation**: Position, menu items, logo placement, style
3. **Hero Section**: Content, imagery, call-to-action buttons, typography
4. **Content Sections**: Each section's purpose, layout (cards, lists, grids), spacing
5. **Forms/Inputs**: Types of inputs, labels, validation indicators, button styles
6. **Footer**: Links, columns, social icons
7. **Color Scheme**: Describe the apparent color palette (dark/light, accent colors)
8. **Typography**: Heading sizes, font weights, text alignment
9. **Interactive Elements**: Buttons, dropdowns, modals, hover states
10. **Responsive Hints**: How the layout might adapt to mobile

Be specific about positions (left, right, center, full-width), sizes (small, medium, large),
and relationships between elements (grouped, spaced, stacked, side-by-side).

Output a well-structured description that a frontend developer can directly implement."""


def analyze_design_image(
    image_bytes: bytes,
    image_mime: str = "image/png",
    additional_context: str = "",
) -> str:
    """
    Analyze a wireframe/design image using a vision-capable LLM.

    Automatically selects the right vision model based on the configured provider.

    Parameters
    ----------
    image_bytes : bytes
        Raw image bytes.
    image_mime : str
        MIME type of the image (e.g., 'image/png', 'image/jpeg').
    additional_context : str
        Optional additional context from the user about the design.

    Returns
    -------
    str
        Detailed text description of the UI layout.
    """
    provider = os.environ.get("LLM_PROVIDER", "google").lower()
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

    # Encode image to base64
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:{image_mime};base64,{b64_image}"

    user_content = VISION_PROMPT
    if additional_context:
        user_content += f"\n\nAdditional context from the user:\n{additional_context}"

    try:
        if provider == "google":
            return _analyze_with_google(image_bytes, user_content, temperature)
        elif provider == "openai":
            return _analyze_with_openai(image_url, user_content, temperature)
        elif provider == "groq":
            return _analyze_with_groq(image_url, user_content, temperature)
        else:
            return f"Vision not supported for provider: {provider}"
    except Exception as e:
        return f"Vision analysis failed: {str(e)}"


def _analyze_with_google(
    image_bytes: bytes,
    prompt: str,
    temperature: float,
) -> str:
    """Use Google Gemini's native vision capabilities."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_API_KEY is required for vision analysis."

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=temperature,
        google_api_key=api_key,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
                },
            },
        ]
    )

    response = llm.invoke([message])
    return response.content


def _analyze_with_openai(
    image_url: str,
    prompt: str,
    temperature: float,
) -> str:
    """Use OpenAI GPT-4 Vision."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "Error: OPENAI_API_KEY is required for vision analysis."

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=temperature,
        api_key=api_key,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    )

    response = llm.invoke([message])
    return response.content


def _analyze_with_groq(
    image_url: str,
    prompt: str,
    temperature: float,
) -> str:
    """Use Groq with Llama Vision model."""
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return "Error: GROQ_API_KEY is required for vision analysis."

    # Groq supports llama-3.2-90b-vision-preview and llama-3.2-11b-vision-preview
    llm = ChatGroq(
        model="llama-3.2-11b-vision-preview",
        temperature=temperature,
        groq_api_key=api_key,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    )

    response = llm.invoke([message])
    return response.content


def get_supported_vision_models() -> dict[str, list[str]]:
    """Return a mapping of providers to their vision-capable models."""
    return {
        "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
        "openai": ["gpt-4o", "gpt-4o-mini"],
        "groq": ["llama-3.2-90b-vision-preview", "llama-3.2-11b-vision-preview"],
    }
