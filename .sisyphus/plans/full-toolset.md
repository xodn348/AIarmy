# AIarmy Full Toolset Implementation

## TL;DR

> **Quick Summary**: Transform AIarmy from a text-only LLM wrapper into a fully autonomous development agent by implementing the tool execution loop and 15+ development tools (shell, git, web, search, packages).
> 
> **Deliverables**:
> - Agent tool execution loop (Anthropic Tool Use API integration)
> - 15+ tools: shell_exec, git_*, web_search, web_fetch, glob_search, grep_search, file_rename, directory_list, package_install
> - Updated agent configurations with proper tool permissions
> - All tools integrated with HITL, audit, budget systems
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 (tool loop) → Task 2-5 (tools) → Task 6 (agent configs) → Task 7 (verify)

---

## Context

### Original Request
User wants AIarmy to have the same capabilities as Claude Code — able to execute shell commands, manage git repos, search the web, install packages, find files, etc. Currently AIarmy only has file_read/file_write/file_delete.

### Critical Gap Discovered
**Agents cannot actually USE tools.** BaseAgent.run() calls LLM once, gets text, returns it. There is NO tool execution loop. This is the #1 blocker — without it, adding more tools is pointless.

### Research Findings
- Claude Code has 20+ tools across 8 categories
- Anthropic Tool Use API is the correct way to implement tool calling
- Tool registry pattern already exists and is well-designed
- HITL/audit/budget systems are ready to receive tool calls

---

## Work Objectives

### Core Objective
Enable AIarmy agents to autonomously execute development tasks using tools, matching Claude Code's core capabilities.

### Concrete Deliverables
- Modified `agents/base.py` with agentic tool execution loop
- Modified `tools/registry.py` with tool schema generation
- New `tools/shell_ops.py` (shell_exec)
- New `tools/git_ops.py` (git_init, git_commit, git_push, git_status, git_diff, git_clone)
- New `tools/web_ops.py` (web_search, web_fetch)
- New `tools/search_ops.py` (glob_search, grep_search)
- New `tools/system_ops.py` (file_rename, directory_list, package_install, env_read)
- Updated agent allowed_tools lists
- Updated `tools/__init__.py` to import all tool modules

### Must Have
- Tool execution loop that handles multi-turn tool calling
- HITL approval for dangerous operations (shell_exec, git_push, package_install)
- All tool calls logged to audit.db
- Budget enforcement during tool loop iterations
- Graceful error handling (tool failures don't crash the agent)

### Must NOT Have (Guardrails)
- No browser automation (too heavy, save for later)
- No LSP integration (requires language server setup)
- No MCP protocol implementation (future enhancement)
- No sandboxing beyond basic path validation (keep simple)
- No new heavy dependencies — use stdlib (subprocess, pathlib, re) + existing httpx

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: None
- **Framework**: None

### Agent-Executed QA Scenarios (MANDATORY)

All verification via CLI interaction with `aiarmy`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Sequential - CRITICAL PATH):
└── Task 1: Agent tool execution loop + registry schema generation

Wave 2 (Parallel - after Wave 1):
├── Task 2: Shell operations (shell_exec)
├── Task 3: Git operations (git_init/commit/push/status/diff/clone)
├── Task 4: Web operations (web_search, web_fetch)
└── Task 5: Search + System operations (glob, grep, file_rename, dir_list, package_install, env_read)

Wave 3 (Sequential - after Wave 2):
├── Task 6: Update agent configs + tools/__init__.py imports
└── Task 7: End-to-end verification + commit
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2,3,4,5 | None (must be first) |
| 2 | 1 | 6 | 3,4,5 |
| 3 | 1 | 6 | 2,4,5 |
| 4 | 1 | 6 | 2,3,5 |
| 5 | 1 | 6 | 2,3,4 |
| 6 | 2,3,4,5 | 7 | None |
| 7 | 6 | None | None (final) |

---

## TODOs

- [ ] 1. Agent Tool Execution Loop (CRITICAL)

  **What to do**:
  
  1. **Modify `tools/registry.py`**: Add `to_anthropic_schema()` method to Tool dataclass that converts Tool to Anthropic tool definition format:
     ```python
     def to_anthropic_schema(self) -> dict:
         # Returns {"name": ..., "description": ..., "input_schema": {...}}
     ```
     Also add `input_schema: dict` field to Tool dataclass for parameter definitions.
     Add `get_tools_for_agent(allowed_tools: list[str]) -> list[dict]` function.
  
  2. **Modify `agents/base.py`**: Replace single LLM call with agentic loop:
     ```python
     def run(self, task, context=""):
         # 1. Get tool schemas for this agent's allowed_tools
         tools = get_tools_for_agent(self.allowed_tools)
         
         # 2. Call LLM with tools parameter
         response = client.messages.create(model=..., tools=tools, messages=...)
         
         # 3. Loop: while response has tool_use blocks
         while response.stop_reason == "tool_use":
             tool_results = []
             for block in response.content:
                 if block.type == "tool_use":
                     # Check HITL
                     # Execute via registry.call()
                     # Collect result
                     tool_results.append({"type": "tool_result", ...})
             # 4. Send tool_results back to LLM
             messages.append({"role": "assistant", "content": response.content})
             messages.append({"role": "user", "content": tool_results})
             response = client.messages.create(...)
         
         # 5. Extract final text response
         return AgentResult(...)
     ```
  
  3. **Handle session_key mode**: ClaudeSessionClient doesn't support tool use natively.
     For session_key mode, implement a text-based tool parsing fallback:
     - Instruct LLM to output tool calls in a structured format (JSON blocks)
     - Parse and execute them
     - Or: raise clear error that tool use requires API key mode

  **Must NOT do**:
  - Don't implement streaming (keep it simple)
  - Don't add retry logic yet
  - Don't change Commander routing logic

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: This is the core architectural change that everything depends on. Needs deep understanding of Anthropic API and careful integration with existing security/audit/budget systems.

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (solo)
  - **Blocks**: Tasks 2,3,4,5
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `aiarmy/agents/base.py:50-119` - Current run() method to modify (single LLM call, security validation, budget check, audit log)
  - `aiarmy/tools/registry.py:1-37` - Tool dataclass and registry.call() function to extend with schema generation
  - `aiarmy/core/security.py:35-73` - requires_hitl() and request_human_approval() — integrate into tool loop
  - `aiarmy/core/budget.py` - check_run_budget() — call per iteration to enforce limits
  - `aiarmy/core/audit.py` - log_action() — log each tool call individually

  **API References**:
  - Anthropic Tool Use docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
  - Tool response format: `{"type": "tool_result", "tool_use_id": "...", "content": "..."}`
  - Stop reason: `response.stop_reason == "tool_use"` means tools requested

  **Acceptance Criteria**:

  ```
  Scenario: Agent executes tool call loop
    Tool: Bash
    Steps:
      1. Set AUTH_MODE=api_key in .env with valid key (or session_key)
      2. Run: python -c "from aiarmy.tools.registry import get_tools_for_agent; print(get_tools_for_agent(['file_read']))"
      3. Assert: Returns list with one tool schema dict containing name, description, input_schema
      4. Run: aiarmy ask "read the file README.md"
      5. Assert: Developer agent calls file_read tool and returns file contents
      6. Check audit.db: SELECT * FROM audit_log WHERE action_type='tool_call'
      7. Assert: Tool call entry exists with agent, action, result
    Expected Result: Agent autonomously calls tools and returns results
    Evidence: Terminal output captured
  ```

  **Commit**: YES
  - Message: `feat(core): add agent tool execution loop with Anthropic Tool Use API`
  - Files: `aiarmy/agents/base.py`, `aiarmy/tools/registry.py`

---

- [ ] 2. Shell Operations

  **What to do**:
  
  Create `aiarmy/tools/shell_ops.py`:
  - `shell_exec(command: str, working_dir: str = ".", timeout: int = 30) -> str`
    - Uses `subprocess.run()` with capture_output=True, text=True, timeout
    - Returns stdout + stderr combined
    - Validates command isn't empty
    - Catches subprocess.TimeoutExpired, returns timeout error
    - HITL required (requires_hitl=True)
  
  Register with input_schema:
  ```python
  register(Tool(
      name="shell_exec",
      description="Execute a shell command. Returns stdout and stderr. Use for running scripts, installing packages, building projects, etc.",
      fn=_shell_exec,
      requires_hitl=True,
      input_schema={
          "type": "object",
          "properties": {
              "command": {"type": "string", "description": "Shell command to execute"},
              "working_dir": {"type": "string", "description": "Working directory (default: current)"},
              "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"}
          },
          "required": ["command"]
      }
  ))
  ```

  **Must NOT do**:
  - No shell=True with user input without validation
  - No unlimited timeout
  - No background process spawning

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3,4,5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1

  **References**:
  - `aiarmy/tools/file_ops.py:1-36` - Follow this exact registration pattern
  - `aiarmy/tools/registry.py:6-10` - Tool dataclass with requires_hitl flag
  - Python docs: subprocess.run() with capture_output, timeout, cwd parameters

  **Acceptance Criteria**:
  ```
  Scenario: shell_exec runs command and returns output
    Tool: Bash
    Steps:
      1. python -c "from aiarmy.tools.shell_ops import *; from aiarmy.tools.registry import call; print(call('shell_exec', ['shell_exec'], command='echo hello'))"
      2. Assert: output contains "hello"
      3. Test timeout: call('shell_exec', ['shell_exec'], command='sleep 100', timeout=2)
      4. Assert: Returns timeout error message
    Expected Result: Commands execute with output capture and timeout
  ```

  **Commit**: NO (groups with Task 6)

---

- [ ] 3. Git Operations

  **What to do**:
  
  Create `aiarmy/tools/git_ops.py` with 6 tools (all using subprocess, NOT GitPython — no new deps):
  
  - `git_init(path: str = ".") -> str` — `git init` in path
  - `git_status(path: str = ".") -> str` — `git status`
  - `git_diff(path: str = ".", staged: bool = False) -> str` — `git diff` or `git diff --staged`
  - `git_commit(message: str, path: str = ".", add_all: bool = True) -> str` — `git add -A && git commit -m "..."`
  - `git_push(remote: str = "origin", branch: str = "", path: str = ".") -> str` — HITL required
  - `git_clone(url: str, dest: str = "") -> str` — `git clone url [dest]`
  
  All use subprocess.run() with cwd=path, timeout=60.
  
  Register each as separate tool with appropriate input_schema.
  git_push requires_hitl=True.

  **Must NOT do**:
  - No GitPython dependency (use subprocess)
  - No force push
  - No credential handling (rely on system git config)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2,4,5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1

  **References**:
  - `aiarmy/tools/file_ops.py:1-36` - Registration pattern
  - `aiarmy/tools/shell_ops.py` (from Task 2) - subprocess pattern to follow

  **Acceptance Criteria**:
  ```
  Scenario: git tools work end-to-end
    Tool: Bash
    Steps:
      1. Create temp dir, init repo, create file, commit
      2. python -c "from aiarmy.tools.git_ops import *; from aiarmy.tools.registry import call; print(call('git_init', ['git_init'], path='/tmp/test-aiarmy-git'))"
      3. Assert: "Initialized" in output
      4. call('git_status', ['git_status'], path='/tmp/test-aiarmy-git')
      5. Assert: status output returned
    Expected Result: All 6 git tools execute correctly
  ```

  **Commit**: NO (groups with Task 6)

---

- [ ] 4. Web Operations

  **What to do**:
  
  Create `aiarmy/tools/web_ops.py`:
  
  - `web_fetch(url: str, max_length: int = 10000) -> str`
    - Uses httpx.get() (already in requirements.txt)
    - Returns response text truncated to max_length
    - Handles errors gracefully (timeout, connection error)
    - Timeout: 15 seconds
  
  - `web_search(query: str, num_results: int = 5) -> str`
    - Uses DuckDuckGo HTML search (no API key needed)
    - GET `https://html.duckduckgo.com/html/?q={query}`
    - Parse results with basic string parsing (no BeautifulSoup dep)
    - OR use `duckduckgo-search` pip package (lightweight)
    - Returns formatted list of title + URL + snippet
  
  Register both with input_schema. Neither requires HITL (read-only operations).

  **Must NOT do**:
  - No API keys required (use free search)
  - No BeautifulSoup dependency
  - No unlimited content fetching

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2,3,5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1

  **References**:
  - `aiarmy/tools/file_ops.py:1-36` - Registration pattern
  - `requirements.txt:5` - httpx already available
  - DuckDuckGo HTML endpoint: `https://html.duckduckgo.com/html/`

  **Acceptance Criteria**:
  ```
  Scenario: web_fetch retrieves URL content
    Tool: Bash
    Steps:
      1. python -c "from aiarmy.tools.web_ops import *; from aiarmy.tools.registry import call; r = call('web_fetch', ['web_fetch'], url='https://httpbin.org/get'); print(r[:200])"
      2. Assert: Contains JSON response from httpbin
    Expected Result: URL content retrieved and truncated

  Scenario: web_search returns results
    Tool: Bash
    Steps:
      1. python -c "from aiarmy.tools.web_ops import *; from aiarmy.tools.registry import call; print(call('web_search', ['web_search'], query='python programming'))"
      2. Assert: Contains search results with titles and URLs
    Expected Result: Search results returned
  ```

  **Commit**: NO (groups with Task 6)

---

- [ ] 5. Search & System Operations

  **What to do**:
  
  Create `aiarmy/tools/search_ops.py`:
  
  - `glob_search(pattern: str, path: str = ".") -> str`
    - Uses pathlib.Path(path).glob(pattern)
    - Returns newline-separated list of matching paths
    - Limits to first 100 results
  
  - `grep_search(pattern: str, path: str = ".", include: str = "") -> str`
    - Uses subprocess: `grep -rn "{pattern}" {path}` with optional `--include={include}`
    - Falls back to Python re module if grep not available
    - Returns matching lines (max 50)
  
  Create `aiarmy/tools/system_ops.py`:
  
  - `file_rename(old_path: str, new_path: str) -> str`
    - pathlib.Path(old_path).rename(new_path)
    - requires_hitl=True
  
  - `directory_list(path: str = ".") -> str`
    - Lists directory contents with type indicators (/ for dirs)
  
  - `package_install(package: str, manager: str = "pip") -> str`
    - Runs `pip install {package}` or `npm install {package}`
    - requires_hitl=True
    - Timeout: 120 seconds
  
  - `env_read(name: str) -> str`
    - os.environ.get(name, "not set")
    - Blocks reading of sensitive vars (API keys, secrets, passwords)

  **Must NOT do**:
  - No recursive glob without depth limit
  - No reading SECRET/PASSWORD/KEY env vars (security)
  - No package_install without HITL

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2,3,4)
  - **Blocks**: Task 6
  - **Blocked By**: Task 1

  **References**:
  - `aiarmy/tools/file_ops.py:1-36` - Registration pattern
  - Python pathlib.Path.glob() docs
  - Python subprocess for grep

  **Acceptance Criteria**:
  ```
  Scenario: glob_search finds files
    Tool: Bash
    Steps:
      1. python -c "from aiarmy.tools.search_ops import *; from aiarmy.tools.registry import call; print(call('glob_search', ['glob_search'], pattern='**/*.py', path='/Users/jnnj92/AIarmy/aiarmy'))"
      2. Assert: Contains list of .py files
    Expected Result: File paths returned

  Scenario: package_install blocked without HITL
    Tool: Bash
    Steps:
      1. Verify package_install has requires_hitl=True
    Expected Result: HITL flag is set
  ```

  **Commit**: NO (groups with Task 6)

---

- [ ] 6. Update Agent Configs & Imports

  **What to do**:
  
  1. **Update `tools/__init__.py`**: Import all tool modules so they auto-register:
     ```python
     from . import file_ops
     from . import shell_ops
     from . import git_ops
     from . import web_ops
     from . import search_ops
     from . import system_ops
     ```
  
  2. **Update agent allowed_tools**:
     - `developer.py`: `["file_read", "file_write", "file_delete", "file_rename", "shell_exec", "git_init", "git_status", "git_diff", "git_commit", "git_push", "git_clone", "glob_search", "grep_search", "directory_list", "package_install", "env_read"]`
     - `researcher.py`: `["file_read", "web_search", "web_fetch", "glob_search", "grep_search", "directory_list"]`
     - `writer.py`: `["file_read", "file_write", "file_rename", "glob_search", "grep_search", "directory_list"]`
     - `analyst.py`: `["file_read", "web_search", "web_fetch", "glob_search", "grep_search", "directory_list", "shell_exec", "env_read"]`
  
  3. **Update `.env.example`**: Add new HITL actions:
     ```
     HITL_REQUIRED_ACTIONS=file_delete,git_push,shell_exec,package_install,file_rename
     ```
  
  4. **Update `core/config.py`**: Ensure HITL_REQUIRED_ACTIONS default includes new tools

  **Must NOT do**:
  - Don't change Commander — it routes, doesn't use tools directly
  - Don't remove existing allowed_tools, only add

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential)
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 2,3,4,5

  **References**:
  - `aiarmy/agents/developer.py:35` - Current allowed_tools
  - `aiarmy/agents/researcher.py` - Current allowed_tools
  - `aiarmy/agents/writer.py` - Current allowed_tools
  - `aiarmy/agents/analyst.py` - Current allowed_tools
  - `aiarmy/tools/__init__.py` - Currently empty, needs imports
  - `aiarmy/core/config.py` - HITL_REQUIRED_ACTIONS default

  **Acceptance Criteria**:
  ```
  Scenario: All tools registered on import
    Tool: Bash
    Steps:
      1. python -c "import aiarmy.tools; from aiarmy.tools.registry import list_tools; print(sorted(list_tools()))"
      2. Assert: Lists 18+ tools (file_read, file_write, file_delete, shell_exec, git_init, git_status, git_diff, git_commit, git_push, git_clone, web_search, web_fetch, glob_search, grep_search, file_rename, directory_list, package_install, env_read)
    Expected Result: All tools registered
  ```

  **Commit**: YES
  - Message: `feat(tools): add 15 development tools (shell, git, web, search, system)`
  - Files: all new tool files, updated agents, updated config

---

- [ ] 7. End-to-End Verification

  **What to do**:
  
  Run the full AIarmy CLI and test each capability:
  
  1. Start `aiarmy` in interactive mode
  2. Test Developer: "list all Python files in this project"
     → Should use glob_search, return file list
  3. Test Developer: "show me the git status"
     → Should use git_status
  4. Test Researcher: "search the web for Python asyncio best practices"
     → Should use web_search
  5. Test shell: "run the command 'echo hello world'"
     → Should trigger HITL, then execute
  6. Check audit log: all tool calls logged

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Task 6)
  - **Blocks**: None
  - **Blocked By**: Task 6

  **Acceptance Criteria**:
  ```
  Scenario: Full end-to-end tool usage
    Tool: Bash
    Steps:
      1. Run: aiarmy ask "list all .py files in this project"
      2. Assert: Returns list of Python files (used glob_search tool)
      3. Run: aiarmy ask "what is the git status of this project"
      4. Assert: Returns git status output
      5. sqlite3 logs/audit.db "SELECT action_type, action FROM audit_log ORDER BY ts DESC LIMIT 10"
      6. Assert: Contains tool_call entries
    Expected Result: All tools work through natural language
  ```

  **Commit**: YES
  - Message: `docs: update README with full tool catalog`
  - Files: README.md

---

## Commit Strategy

| After Task | Message | Verification |
|------------|---------|--------------|
| 1 | `feat(core): add agent tool execution loop with Anthropic Tool Use API` | Tool schema generation works |
| 6 | `feat(tools): add 15 development tools (shell, git, web, search, system)` | All tools registered |
| 7 | `docs: update README with full tool catalog` | E2E test passes |

---

## Success Criteria

### Verification Commands
```bash
# All tools registered
python -c "import aiarmy.tools; from aiarmy.tools.registry import list_tools; print(len(list_tools()), 'tools:', sorted(list_tools()))"
# Expected: 18+ tools listed

# Agent can use tools
aiarmy ask "list all .py files in the aiarmy directory"
# Expected: Returns file list via glob_search

# Audit log captures tool calls
sqlite3 logs/audit.db "SELECT COUNT(*) FROM audit_log WHERE action_type='tool_call'"
# Expected: > 0
```

### Final Checklist
- [ ] Agent tool execution loop works (multi-turn tool calling)
- [ ] 15+ tools implemented and registered
- [ ] HITL triggers for dangerous operations (shell_exec, git_push, package_install, file_rename, file_delete)
- [ ] All tool calls logged to audit.db
- [ ] Budget enforced during tool loop
- [ ] No new heavy dependencies (uses stdlib + existing httpx)
- [ ] All agents have appropriate tool permissions
- [ ] Committed to GitHub
