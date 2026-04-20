<<<<<<< HEAD
# Coder Buddy 🤖

**Your Elite AI Development Team** — Describe what you want to build, and our multi-agent pipeline will plan, architect, code, and review it for you.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Powered-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)

---

## 🏗️ Architecture

Coder Buddy uses a **multi-agent system** powered by [LangGraph](https://github.com/langchain-ai/langgraph) with four specialized agents:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   📋 Planner │────▶│  🏗️ Architect │────▶│  💻 Coder    │────▶│  🔍 Reviewer │
│              │     │              │     │              │     │              │
│ Designs the  │     │ Creates      │     │ Writes       │     │ Reviews code │
│ project plan │     │ engineering  │     │ production   │     │ quality &    │
│              │     │ tasks        │     │ code         │     │ security     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                ▲                     │
                                                │   Revision Loop     │
                                                └─────────────────────┘
```

### Agent Details

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Planner** | Designs a comprehensive project plan | User's request | Project plan with file structure, tech stack |
| **Architect** | Creates detailed engineering specs | Project plan | Implementation tasks with specs for each file |
| **Coder** | Generates production-quality code | Architecture tasks | Complete code files as JSON |
| **Reviewer** | QA review for quality & security | Generated code | Review report, may trigger revision |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Srilu_Project
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your API key
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🔑 Supported LLM Providers

| Provider | Models | Setup |
|----------|--------|-------|
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash | Get key from [Google AI Studio](https://aistudio.google.com/) |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo | Get key from [OpenAI Platform](https://platform.openai.com/) |

You can configure the provider either through:
- The **sidebar** in the Streamlit UI (recommended)
- The `.env` file for persistent settings

---

## 📁 Project Structure

```
Srilu_Project/
├── app.py                  # Streamlit frontend
├── config.py               # LLM configuration & factory
├── state.py                # Shared state schema (TypedDict)
├── graph.py                # LangGraph pipeline orchestration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
├── agents/
│   ├── __init__.py
│   ├── planner.py          # Planner Agent
│   ├── architect.py        # Architect Agent
│   ├── coder.py            # Coder Agent
│   └── reviewer.py         # Reviewer Agent
├── utils/
│   ├── __init__.py
│   └── file_utils.py       # File saving & tree generation
└── generated_projects/     # Output directory (auto-created)
```

---

## 🧪 Example Usage

### Using Templates

The app includes 5 pre-built templates:
- 🌐 **REST API** — FastAPI with JWT auth and SQLAlchemy
- 🕷️ **Web Scraper** — BeautifulSoup with pagination
- 🤖 **Discord Bot** — discord.py with slash commands
- 📊 **Data Dashboard** — Streamlit + Plotly dashboard
- ⚡ **CLI Tool** — Click-based TODO manager

### Custom Request Format

For best results, use this format:

```
I want to build a [Project Type] that does the following:
• [Core Feature 1]
• [Core Feature 2]

Tech Stack: Use [Language], [Library 1], [Library 2].
Special instructions: [Error handling, comments, etc.]
```

---

## 🚀 Future Features

- **RAG-Powered Codebase Context** — Upload existing code for context-aware generation
- **Multimodal Design-to-Code** — Upload UI wireframes to generate frontend code
- **Self-Healing Sandbox** — Auto-execute and debug generated code
- **Git Integration** — Auto-commit generated files with meaningful messages

---

## 📄 License

MIT License — Build whatever you want with Coder Buddy!
=======
# CM02
>>>>>>> 93197eb90c3b32393af7011c7cfbfcdf3df242bf
