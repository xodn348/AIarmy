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

### Option 1: Claude Pro/Team Subscription ($20-100/month)

```bash
# 1. Clone and install
git clone https://github.com/xodn348/AIarmy.git
cd AIarmy
pip install -e .

# 2. Configure with session key
cp .env.example .env
# Edit .env:
#   AUTH_MODE=session_key
#   CLAUDE_SESSION_KEY=<your session key from claude.ai>

# Get session key:
# 1. Go to claude.ai and login
# 2. Open DevTools (F12) → Application/Storage → Cookies
# 3. Copy value of "sessionKey" cookie (sk-ant-sid01-...)

# 3. Launch
aiarmy
```

### Option 2: Official API Key (Pay-as-you-go)

```bash
# 1. Clone and install
git clone https://github.com/xodn348/AIarmy.git
cd AIarmy
pip install -e .

# 2. Configure with API key
cp .env.example .env
# Edit .env:
#   AUTH_MODE=api_key
#   ANTHROPIC_API_KEY=<key from console.anthropic.com>

# 3. Launch
aiarmy
```

### Usage

```bash
# Interactive mode
aiarmy

# Single tasks
aiarmy ask "Write a Python function to parse JSON safely"
aiarmy ask "Research the latest MCP protocol updates"
aiarmy ask "Review this code for security issues: <paste code>"
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

## 🛠️ Tools

AIarmy agents have access to 20+ development tools:

### File Operations (4 tools)
- `file_read` - Read file contents
- `file_write` - Write to files (HITL)
- `file_delete` - Delete files (HITL)
- `file_rename` - Rename/move files (HITL)

### Shell & Process (1 tool)
- `shell_exec` - Execute shell commands (HITL)

### Git Operations (8 tools)
- `git_init` - Initialize repository
- `git_status` - Show status
- `git_diff` - Show changes
- `git_add` - Stage files
- `git_commit` - Commit changes
- `git_push` - Push to remote (HITL)
- `git_clone` - Clone repository (HITL)
- `git_log` - Show commit history

### Web (2 tools)
- `web_search` - Search the web (DuckDuckGo)
- `web_fetch` - Fetch URL content

### Search & Discovery (3 tools)
- `glob_search` - Find files by pattern
- `grep_search` - Search file contents
- `directory_list` - List directory contents

### System (2 tools)
- `package_install` - Install packages (HITL)
- `env_read` - Read environment variables

**HITL** = Human-in-the-loop approval required

## Configuration

All settings in `.env`:

```bash
# ── Authentication ─────────────────────────────────
AUTH_MODE=session_key                # or "api_key"

# If AUTH_MODE=api_key
ANTHROPIC_API_KEY=sk-ant-...         # From console.anthropic.com

# If AUTH_MODE=session_key
CLAUDE_SESSION_KEY=sk-ant-sid01-...  # From claude.ai cookies

# ── Agent Models ───────────────────────────────────
COMMANDER_MODEL=claude-opus-4-5      # Smart routing
SPECIALIST_MODEL=claude-sonnet-4-5   # Fast execution

# ── Budget & Safety ────────────────────────────────
MAX_TOKENS_PER_RUN=8000              # Per-task limit
MAX_TOKENS_PER_SESSION=100000        # Session budget
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
├── aiarmy/
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
