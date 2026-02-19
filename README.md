# 🪖 AIarmy

Your personal AI company — a multi-agent system with security-first design.

```
  █████╗ ██╗ █████╗ ██████╗ ███╗   ███╗██╗   ██╗
 ██╔══██╗██║██╔══██╗██╔══██╗████╗ ████║╚██╗ ██╔╝
 ███████║██║███████║██████╔╝██╔████╔██║ ╚████╔╝
 ██╔══██║██║██╔══██║██╔══██╗██║╚██╔╝██║  ╚██╔╝
 ██║  ██║██║██║  ██║██║  ██║██║ ╚═╝ ██║   ██║
 ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝   ╚═╝
```

## Your Team

| Agent | Role | What they do |
|-------|------|-------------|
| 👑 Commander | CEO / Orchestrator | Routes tasks, manages the team |
| 💻 Developer | Senior Engineer | Code, review, debug, git |
| 🔍 Researcher | Research Analyst | Research, docs, fact-finding |
| ✍️ Writer | Technical Writer | Documentation, blog, emails |
| 📊 Analyst | Business Analyst | Data analysis, metrics, ROI |

## Design Principles

Built on research of why 95% of AI agent deployments fail:

**Failure Prevention**
- Always define success criteria before running
- Budget limits per run and per session — no surprise bills
- Max turns enforced — agents can't loop forever
- Progressive autonomy — start cautious, earn trust

**Security (OWASP Agentic AI Top 10 compliant)**
- Prompt injection detection on every input
- Human-in-the-Loop (HITL) checkpoints before risky actions
- Least privilege — each agent only gets its needed tools
- Immutable audit log — every action recorded to SQLite
- Agent-specific permissions — no shared credentials

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/xodn348/AIarmy.git
cd AIarmy
pip install -e .

# 2. Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Launch interactive mode
airarmy

# Or run a single task
airarmy ask "Write a Python function to parse JSON safely"
airarmy ask "Research the latest MCP protocol updates"
airarmy ask "Review this code for security issues: <paste code>"
```

## Commands

In interactive mode:

| Command | Action |
|---------|--------|
| `help` | Show available commands |
| `team` | Show your AI team |
| `budget` | Show token usage this session |
| `log` | Show audit log |
| `clear` | Clear conversation history |
| `exit` | Quit |

## Configuration

All settings in `.env`:

```bash
ANTHROPIC_API_KEY=        # Required
COMMANDER_MODEL=claude-opus-4-5      # Smart routing
SPECIALIST_MODEL=claude-sonnet-4-5   # Fast execution
MAX_TOKENS_PER_RUN=8000              # Per-task limit
MAX_TOKENS_PER_SESSION=100000        # Daily budget
MAX_AGENT_TURNS=10                   # Prevents loops
HITL_REQUIRED_ACTIONS=file_delete,git_push,shell_exec
```

## Architecture

```
You (CLI)
    │
    ▼
Commander (Orchestrator)
    │  routes based on task type
    ├──▶ Developer   — code, git, debug
    ├──▶ Researcher  — research, docs
    ├──▶ Writer      — content, docs
    └──▶ Analyst     — data, metrics

Core Layer (every agent runs through this):
    Security  → prompt injection detection
    HITL      → human approval for risky actions
    Budget    → token tracking & limits
    Audit     → immutable SQLite log
    Memory    → conversation context
```

## Project Structure

```
AIarmy/
├── airarmy/
│   ├── agents/
│   │   ├── base.py         # Base agent (security + budget baked in)
│   │   ├── commander.py    # Orchestrator with LLM-based routing
│   │   ├── developer.py
│   │   ├── researcher.py
│   │   ├── writer.py
│   │   └── analyst.py
│   ├── core/
│   │   ├── config.py       # All settings from .env
│   │   ├── security.py     # Prompt injection + HITL
│   │   ├── budget.py       # Token tracking
│   │   ├── audit.py        # SQLite audit log
│   │   └── memory.py       # Conversation context
│   ├── tools/
│   │   ├── registry.py     # Tool registry (least-privilege)
│   │   └── file_ops.py     # File operations
│   └── cli.py              # Rich terminal interface
├── logs/                   # Audit logs (gitignored)
├── .env.example
└── pyproject.toml
```

## Roadmap

- [ ] MCP server integration (connect your own tools)
- [ ] Web search tool (Researcher agent)
- [ ] Git operations tool (Developer agent)
- [ ] Persistent long-term memory (SQLite)
- [ ] Multi-task parallel execution
- [ ] Web UI dashboard
- [ ] Slack/Discord bot interface
