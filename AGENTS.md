# Multi-Agent Collaboration Protocol

This document describes how multiple AI coding assistants (Junie, Claude Code, Gemini) collaborate on the NotebookLM Generation Tool project.

## Agent Roles

### 🤖 Junie (JetBrains AI Assistant)

**Expertise:**
- Selenium browser automation
- CSS selector debugging and optimization
- UI element detection and interaction
- Click interception and overlay handling
- WebDriver configurations

**Preferred Files:**
- `src/generators/notebooklm.py` - NotebookLM browser automation
- `src/auth/google_auth.py` - Google login automation
- `src/utils/downloader.py` - Download handling

**When to Use Junie:**
- CSS selectors not finding elements
- Click interception errors
- Stale element exceptions
- Browser timing issues
- Popup/overlay handling

### 🧠 Claude Code (Anthropic CLI)

**Expertise:**
- Architecture and design patterns
- Complex refactoring across files
- Error handling strategies
- Documentation and README updates
- Code review and quality
- Git operations and commits

**Preferred Files:**
- `src/main.py` - Main entry point
- `src/orchestrator/` - This orchestration system
- `README.md`, `CLAUDE.md`, `JOURNAL.md`
- Any `__init__.py` files

**When to Use Claude Code:**
- Multi-file refactoring needed
- Architecture decisions
- Documentation updates
- Code review requests
- Git commit/push operations

### ✨ Gemini (Google AI in IDE)

**Expertise:**
- Google API integration
- Gemini API prompts and responses
- JSON parsing and handling
- Content generation prompt engineering
- Google authentication patterns

**Preferred Files:**
- `src/generators/gemini_client.py` - Gemini API client
- `src/processors/topic_splitter.py` - Topic extraction
- `src/generators/*.py` - Content generators
- `src/config/settings.py` - Configuration

**When to Use Gemini:**
- Gemini API errors or rate limits
- JSON parsing issues
- Prompt engineering
- Google service integration

## Collaboration Workflow

### 1. Check Shared State

Before starting work, check `.agent_state.json` for:
- Pending tasks that match your expertise
- Messages from other agents
- Currently assigned work

```bash
# View orchestrator status
python -m src.orchestrator.agent_orchestrator status
```

### 2. Claim a Task

When you find a suitable task:
1. Update the task status to "assigned" in `.agent_state.json`
2. Set yourself as the assigned agent
3. This prevents other agents from working on the same task

### 3. Implement Changes

- Work on files matching your expertise
- Follow existing code patterns
- Add appropriate error handling
- Run syntax checks before finishing

### 4. Notify Other Agents

After completing work:
1. Add a message to `.agent_state.json`
2. Describe what you changed
3. Tag specific agents if review needed
4. Update task status to "review" or "completed"

### 5. Review & Merge

- Claude Code typically handles final review
- Check for conflicts with other agents' changes
- Run tests if applicable
- Commit and push when ready

## Task Priority

| Priority | Description |
|----------|-------------|
| 10 | Critical - blocking other work |
| 8 | High - important bug fix |
| 5 | Medium - feature or enhancement |
| 3 | Low - documentation or cleanup |
| 1 | Optional - nice to have |

## Communication Protocol

### Message Format

```json
{
  "from": "junie",
  "to": "claude_code",
  "message": "Updated NotebookLM selectors, please review",
  "timestamp": 1733587200,
  "read_by": []
}
```

### Common Messages

- **Request Review:** "Completed [task], please review [files]"
- **Handoff:** "Fixed [issue], passing to [agent] for [next step]"
- **Blocked:** "Blocked on [issue], need help from [agent]"
- **Question:** "Should we [approach A] or [approach B]?"

## File Ownership Matrix

| File Pattern | Primary | Secondary |
|--------------|---------|-----------|
| `**/notebooklm.py` | Junie | Claude |
| `**/google_auth.py` | Junie | Gemini |
| `**/gemini_client.py` | Gemini | Claude |
| `**/topic_splitter.py` | Gemini | Claude |
| `**/main.py` | Claude | Any |
| `**/orchestrator/**` | Claude | Any |
| `**/*.md` | Claude | Any |
| `**/generators/*.py` | Gemini | Junie |

## CLI Commands

```bash
# Print collaboration guide
python -m src.orchestrator.agent_orchestrator guide

# View current status
python -m src.orchestrator.agent_orchestrator status

# View pending tasks
python -m src.orchestrator.agent_orchestrator tasks

# Get instructions for specific agent
python -m src.orchestrator.agent_orchestrator instructions junie
python -m src.orchestrator.agent_orchestrator instructions claude
python -m src.orchestrator.agent_orchestrator instructions gemini

# Create tasks from issue description
python -m src.orchestrator.agent_orchestrator create "JSON parsing fails with newlines"
```

## Example Collaboration Session

### Scenario: Fix Browser Automation Issue

1. **Claude Code** analyzes the issue and creates tasks:
   ```
   Task 1: Analyze issue → Claude Code
   Task 2: Fix selectors → Junie
   Task 3: Review changes → Claude Code
   ```

2. **Junie** claims Task 2 and works on `notebooklm.py`:
   - Updates CSS selectors
   - Adds scroll-into-view
   - Adds overlay dismissal

3. **Junie** posts message:
   ```
   "Updated selectors in notebooklm.py with JS click fallback,
   overlay dismissal, and scroll-into-view. Ready for review."
   ```

4. **Claude Code** reviews, commits, and pushes.

## Best Practices

1. **Don't overlap** - Check what others are working on
2. **Communicate early** - Post messages before making big changes
3. **Test locally** - Run syntax checks at minimum
4. **Small commits** - Easier to review and revert if needed
5. **Document changes** - Update JOURNAL.md with significant work
6. **Respect expertise** - Let the expert agent handle their domain
