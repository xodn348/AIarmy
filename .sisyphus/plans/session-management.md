# AIarmy Session Management System

## TL;DR

> **Goal**: Implement comprehensive session persistence and context management for AIarmy
> 
> **Problem**: Currently sessions are ephemeral - all conversation history lost on exit
> 
> **Solution**: 
> - Phase 1: Basic persistence (auto-save/resume)
> - Phase 2: Smart compaction (summarization, key fact extraction)
> - Phase 3: Advanced features (embeddings, project memory)
> 
> **Estimated Effort**: 
> - Phase 1: 4 hours
> - Phase 2: 2 days
> - Phase 3: 3 days

---

## Architecture

### Session Storage Structure

```
.aiarmy/
├── sessions/
│   ├── session-abc123/
│   │   ├── full.json           # Complete transcript
│   │   ├── working.json        # Working Set (compact)
│   │   ├── state.json          # Session state
│   │   └── metadata.json       # Session info
│   └── session-def456/
│       └── ...
├── current_session             # Pointer to active session
└── config.json                 # User preferences
```

### Working Set Structure

```json
{
  "summary": "Brief overview of conversation so far",
  "pinned_facts": [
    "Project: AIarmy at /Users/jnnj92/AIarmy",
    "20 tools implemented",
    "Auth mode: session_key"
  ],
  "decisions": [
    "Renamed package from airarmy to aiarmy",
    "Using HITL for dangerous operations"
  ],
  "open_tasks": [
    "Test with real session key",
    "Fix LSP errors in claude_session.py"
  ],
  "files_touched": [
    "/Users/jnnj92/AIarmy/pyproject.toml",
    "/Users/jnnj92/AIarmy/README.md"
  ],
  "recent_messages": [],  // Last N messages only
  "token_budget": {
    "used": 15234,
    "limit": 100000
  }
}
```

---

## Phase 1: Basic Session Persistence

### Deliverables

1. **SessionManager class** (`aiarmy/core/session_manager.py`)
   - `save_session(session_id, messages, state)`
   - `load_session(session_id)`
   - `list_sessions()`
   - `get_last_session()`
   - `create_new_session()`

2. **Enhanced SessionMemory** (`aiarmy/core/memory.py`)
   - Add `working_set` field
   - Add `to_disk()` and `from_disk()` methods
   - Add `estimate_tokens()` method

3. **Updated CLI** (`aiarmy/cli.py`)
   - Auto-resume last session by default
   - Add `--new-session` flag to force new session
   - Add `--resume <session_id>` flag
   - Add `sessions` command to list all sessions

### Implementation Details

#### SessionManager

```python
class SessionManager:
    def __init__(self, base_dir: Path = Path.home() / ".aiarmy"):
        self.base_dir = base_dir
        self.sessions_dir = base_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session_id: str, memory: SessionMemory, state: dict):
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Save full transcript
        with (session_dir / "full.json").open("w") as f:
            json.dump({
                "messages": [{"role": m.role, "content": m.content} for m in memory.messages],
                "context": memory.context
            }, f, indent=2)
        
        # Save working set
        with (session_dir / "working.json").open("w") as f:
            json.dump(memory.working_set, f, indent=2)
        
        # Save state
        with (session_dir / "state.json").open("w") as f:
            json.dump(state, f, indent=2)
        
        # Save metadata
        with (session_dir / "metadata.json").open("w") as f:
            json.dump({
                "session_id": session_id,
                "created_at": state.get("created_at"),
                "last_updated": datetime.now(UTC).isoformat(),
                "message_count": len(memory.messages),
                "token_count": state.get("tokens_used", 0)
            }, f, indent=2)
        
        # Update current session pointer
        with (self.base_dir / "current_session").open("w") as f:
            f.write(session_id)
    
    def load_session(self, session_id: str) -> tuple[SessionMemory, dict] | None:
        session_dir = self.sessions_dir / session_id
        if not session_dir.exists():
            return None
        
        # Load full transcript
        with (session_dir / "full.json").open() as f:
            data = json.load(f)
        
        memory = SessionMemory(session_id=session_id)
        for msg in data["messages"]:
            memory.add(msg["role"], msg["content"])
        memory.context = data.get("context", {})
        
        # Load working set
        if (session_dir / "working.json").exists():
            with (session_dir / "working.json").open() as f:
                memory.working_set = json.load(f)
        
        # Load state
        with (session_dir / "state.json").open() as f:
            state = json.load(f)
        
        return memory, state
    
    def get_last_session(self) -> str | None:
        current_file = self.base_dir / "current_session"
        if current_file.exists():
            return current_file.read_text().strip()
        return None
    
    def list_sessions(self) -> list[dict]:
        sessions = []
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / "metadata.json"
                if metadata_file.exists():
                    with metadata_file.open() as f:
                        sessions.append(json.load(f))
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
```

#### Enhanced SessionMemory

```python
@dataclass
class SessionMemory:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    working_set: dict[str, Any] = field(default_factory=lambda: {
        "summary": "",
        "pinned_facts": [],
        "decisions": [],
        "open_tasks": [],
        "files_touched": [],
        "recent_messages": []
    })
    
    def estimate_tokens(self) -> int:
        """Rough token estimation: ~4 chars per token"""
        total_chars = sum(len(m.content) for m in self.messages)
        return total_chars // 4
    
    def get_llm_context(self, max_messages: int = 20) -> list[Message]:
        """Return only recent messages for LLM, not full history"""
        return self.messages[-max_messages:]
    
    def add_pinned_fact(self, fact: str):
        if fact not in self.working_set["pinned_facts"]:
            self.working_set["pinned_facts"].append(fact)
    
    def add_decision(self, decision: str):
        if decision not in self.working_set["decisions"]:
            self.working_set["decisions"].append(decision)
    
    def update_summary(self, summary: str):
        self.working_set["summary"] = summary
```

#### Updated CLI

```python
def _run_interactive() -> None:
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(BANNER)
    
    session_manager = SessionManager()
    
    # Check for --new-session flag
    import sys
    force_new = "--new-session" in sys.argv
    
    if not force_new:
        # Try to resume last session
        last_session_id = session_manager.get_last_session()
        if last_session_id:
            try:
                memory, state = session_manager.load_session(last_session_id)
                budget = BudgetTracker(
                    session_id=last_session_id,
                    tokens_used=state.get("tokens_used", 0)
                )
                session_id = last_session_id
                console.print(f"[dim]Resumed session: {session_id} ({len(memory.messages)} messages)[/dim]\n")
            except Exception as e:
                console.print(f"[yellow]Could not resume last session: {e}[/yellow]")
                session_id = f"session-{uuid.uuid4().hex[:8]}"
                memory = SessionMemory(session_id=session_id)
                budget = BudgetTracker(session_id=session_id)
        else:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            memory = SessionMemory(session_id=session_id)
            budget = BudgetTracker(session_id=session_id)
    else:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        memory = SessionMemory(session_id=session_id)
        budget = BudgetTracker(session_id=session_id)
        console.print(f"[dim]Started new session: {session_id}[/dim]\n")
    
    army = build_army(session_id, budget, memory)
    
    while True:
        # ... existing loop ...
        
        # Auto-save after each interaction
        session_manager.save_session(
            session_id=session_id,
            memory=memory,
            state={
                "created_at": datetime.now(UTC).isoformat(),
                "tokens_used": budget.tokens_used
            }
        )
```

### Acceptance Criteria

- [ ] Sessions automatically saved to `.aiarmy/sessions/`
- [ ] Last session automatically resumed on `aiarmy` start
- [ ] `aiarmy --new-session` forces new session
- [ ] `aiarmy sessions` lists all sessions with metadata
- [ ] All conversation history preserved across restarts
- [ ] Working Set structure initialized

---

## Phase 2: Smart Compaction

### Deliverables

1. **ContextCompactor class** (`aiarmy/core/compactor.py`)
   - `should_compact(memory)` - Check if compaction needed
   - `compact(memory)` - Summarize and compress
   - `extract_facts(messages)` - Pull out key facts
   - `extract_decisions(messages)` - Pull out decisions

2. **Enhanced BaseAgent**
   - Check context size before LLM call
   - Trigger compaction if threshold exceeded
   - Use working set + recent messages only

### Implementation Details

#### ContextCompactor

```python
class ContextCompactor:
    def __init__(self, client: anthropic.Anthropic, threshold_tokens: int = 15000):
        self.client = client
        self.threshold_tokens = threshold_tokens
    
    def should_compact(self, memory: SessionMemory) -> bool:
        return memory.estimate_tokens() > self.threshold_tokens
    
    def compact(self, memory: SessionMemory) -> None:
        """Compact old messages into summary"""
        if len(memory.messages) <= 20:
            return  # Nothing to compact
        
        # Take messages except last 20
        old_messages = memory.messages[:-20]
        
        # Generate summary
        summary = self._summarize_messages(old_messages)
        facts = self._extract_facts(old_messages)
        decisions = self._extract_decisions(old_messages)
        
        # Update working set
        memory.working_set["summary"] = summary
        memory.working_set["pinned_facts"].extend(facts)
        memory.working_set["decisions"].extend(decisions)
        
        # Keep only recent messages in memory
        # (full history still in disk)
        console.print("[dim]Context compacted - summarized older messages[/dim]")
    
    def _summarize_messages(self, messages: list[Message]) -> str:
        """Use Claude to summarize old messages"""
        conversation_text = "\n\n".join([
            f"{m.role}: {m.content}" for m in messages
        ])
        
        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Summarize this conversation in 3-5 sentences. Focus on:
- What the user is trying to accomplish
- Key decisions made
- Important context for future work

Conversation:
{conversation_text}

Summary:"""
            }]
        )
        
        return response.content[0].text
    
    def _extract_facts(self, messages: list[Message]) -> list[str]:
        """Extract key facts from messages"""
        # Simple heuristic: look for file paths, project names, etc.
        facts = []
        for msg in messages:
            # Look for file paths
            if "/Users/" in msg.content or "/home/" in msg.content:
                # Extract paths
                import re
                paths = re.findall(r'(/[\w/.-]+)', msg.content)
                facts.extend([f"File: {p}" for p in paths[:3]])
            
            # Look for "Project: X" patterns
            if "Project:" in msg.content or "project" in msg.content.lower():
                lines = [l for l in msg.content.split('\n') if 'project' in l.lower()]
                facts.extend(lines[:2])
        
        return list(set(facts))[:10]  # Dedupe and limit
    
    def _extract_decisions(self, messages: list[Message]) -> list[str]:
        """Extract decisions from messages"""
        decisions = []
        for msg in messages:
            # Look for decision keywords
            if any(kw in msg.content.lower() for kw in ["decided", "chose", "using", "will use", "implemented"]):
                # Extract sentence containing decision
                sentences = msg.content.split('.')
                decision_sentences = [s.strip() for s in sentences if any(kw in s.lower() for kw in ["decided", "chose", "using"])]
                decisions.extend(decision_sentences[:2])
        
        return list(set(decisions))[:10]
```

#### Enhanced BaseAgent.run()

```python
def run(self, task: str, context: str = "") -> AgentResult:
    # Existing validation...
    
    # NEW: Check if compaction needed
    if hasattr(self, 'compactor') and self.compactor.should_compact(self.memory):
        self.compactor.compact(self.memory)
    
    # Build messages from RECENT messages only
    raw_messages = self.memory.get_llm_context(max_messages=20)
    
    # NEW: Prepend working set context if exists
    system_prompt = self.system_prompt
    if self.memory.working_set.get("summary"):
        system_prompt = f"""{self.system_prompt}

## Context from previous conversation:
{self.memory.working_set['summary']}

Key facts:
{chr(10).join('- ' + f for f in self.memory.working_set['pinned_facts'])}

Decisions made:
{chr(10).join('- ' + d for d in self.memory.working_set['decisions'])}
"""
    
    # Rest of existing code...
```

### Acceptance Criteria

- [ ] Context automatically compacted when exceeding 15K tokens
- [ ] Old messages summarized into working set
- [ ] Key facts and decisions extracted
- [ ] LLM receives: summary + recent messages only
- [ ] Full history still available on disk

---

## Phase 3: Advanced Features

### Deliverables

1. **Semantic Search** (embeddings-based)
   - Embed all messages
   - Search by similarity
   - Pull relevant historical context

2. **Project Memory**
   - Project-level persistent facts
   - Shared across sessions
   - File/directory knowledge

3. **Multi-Session Management**
   - Session tagging
   - Session branching
   - Conflict resolution

### Implementation Details

(TBD - requires additional dependencies: sentence-transformers, faiss, etc.)

---

## Success Criteria

### Phase 1
- ✅ Session survives app restart
- ✅ Conversation history preserved
- ✅ Auto-resume works
- ✅ Can start new sessions

### Phase 2
- ✅ Context stays under token budget
- ✅ Old info accessible but not in prompt
- ✅ Summary quality good
- ✅ Token costs reduced

### Phase 3
- ✅ Semantic search works
- ✅ Project knowledge persists
- ✅ Multi-session workflows smooth

---

## Dependencies

### Phase 1
- No new dependencies (uses stdlib + existing)

### Phase 2
- No new dependencies (uses Claude for summarization)

### Phase 3
- sentence-transformers
- faiss-cpu
- tiktoken (better token counting)
