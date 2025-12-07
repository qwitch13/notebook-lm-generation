"""
Multi-Agent Orchestrator for NotebookLM Generation Tool.

Coordinates multiple coding assistants (Junie, Claude Code, Gemini) working
together on this project. Adapted from the coding-agent orchestrator protocol.

Agents:
- Junie (JetBrains AI): Browser automation, Selenium selectors, UI fixes
- Claude Code (Anthropic): Architecture, refactoring, complex logic, documentation
- Gemini (Google): API integration, content generation prompts, Google services

Collaboration Strategies:
- parallel: Each agent works on different aspects simultaneously
- consensus: Multiple agents propose solutions, best one wins
- pipeline: analyze → implement → review → optimize
- swarm: Dynamic task allocation based on agent strengths
"""

import asyncio
import time
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Set
from collections import defaultdict

try:
    from ..utils.logger import get_logger
except ImportError:
    # Standalone mode - define simple logger
    import logging
    def get_logger():
        logger = logging.getLogger("orchestrator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


class AgentRole(Enum):
    """Roles that coding assistants can take in collaboration."""
    ANALYZER = "analyzer"           # Analyze code for issues
    IMPLEMENTER = "implementer"     # Implement new features
    FIXER = "fixer"                 # Fix bugs and errors
    TESTER = "tester"               # Write and run tests
    OPTIMIZER = "optimizer"         # Optimize performance
    REVIEWER = "reviewer"           # Review changes
    DOCUMENTER = "documenter"       # Write documentation
    SELECTOR_EXPERT = "selector"    # CSS selector specialist (Junie)
    API_EXPERT = "api_expert"       # API integration (Gemini)
    ARCHITECT = "architect"         # Architecture decisions (Claude)


class AgentType(Enum):
    """Types of coding assistants available."""
    JUNIE = "junie"                 # JetBrains AI Assistant
    CLAUDE_CODE = "claude_code"     # Anthropic Claude Code CLI
    GEMINI = "gemini"               # Google Gemini in IDE
    HUMAN = "human"                 # Human developer


@dataclass
class AgentCapabilities:
    """Defines what each agent is best at."""
    name: str
    agent_type: AgentType
    strengths: List[str]
    preferred_roles: List[AgentRole]
    file_patterns: List[str]  # Files this agent is best suited for


# Define agent capabilities
AGENT_CAPABILITIES = {
    AgentType.JUNIE: AgentCapabilities(
        name="Junie",
        agent_type=AgentType.JUNIE,
        strengths=[
            "Selenium browser automation",
            "CSS selector debugging",
            "UI element detection",
            "Click interception handling",
            "Overlay/popup management",
            "WebDriver interactions",
        ],
        preferred_roles=[
            AgentRole.SELECTOR_EXPERT,
            AgentRole.FIXER,
            AgentRole.TESTER,
        ],
        file_patterns=[
            "**/notebooklm.py",
            "**/google_auth.py",
            "**/downloader.py",
            "**/*selenium*",
            "**/*browser*",
        ]
    ),
    AgentType.CLAUDE_CODE: AgentCapabilities(
        name="Claude Code",
        agent_type=AgentType.CLAUDE_CODE,
        strengths=[
            "Architecture design",
            "Complex refactoring",
            "Error handling patterns",
            "Documentation writing",
            "Code review",
            "Multi-file changes",
            "Git operations",
        ],
        preferred_roles=[
            AgentRole.ARCHITECT,
            AgentRole.REVIEWER,
            AgentRole.DOCUMENTER,
            AgentRole.IMPLEMENTER,
        ],
        file_patterns=[
            "**/main.py",
            "**/orchestrator/**",
            "**/__init__.py",
            "**/README.md",
            "**/CLAUDE.md",
            "**/JOURNAL.md",
        ]
    ),
    AgentType.GEMINI: AgentCapabilities(
        name="Gemini",
        agent_type=AgentType.GEMINI,
        strengths=[
            "Google API integration",
            "Gemini API prompts",
            "JSON response handling",
            "Content generation prompts",
            "Google authentication",
            "NotebookLM API patterns",
        ],
        preferred_roles=[
            AgentRole.API_EXPERT,
            AgentRole.IMPLEMENTER,
            AgentRole.OPTIMIZER,
        ],
        file_patterns=[
            "**/gemini_client.py",
            "**/topic_splitter.py",
            "**/generators/*.py",
            "**/config/settings.py",
        ]
    ),
}


@dataclass
class AgentTask:
    """A task assigned to a coding assistant."""
    task_id: str
    title: str
    description: str
    role: AgentRole
    target_files: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more important
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[AgentType] = None
    status: str = "pending"  # pending, assigned, in_progress, review, completed, failed
    result: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "role": self.role.value,
            "target_files": self.target_files,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "assigned_agent": self.assigned_agent.value if self.assigned_agent else None,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class CodingAgent:
    """Represents a coding assistant in the collaboration."""
    agent_type: AgentType
    capabilities: AgentCapabilities
    status: str = "idle"  # idle, busy, waiting_review
    current_task: Optional[str] = None
    tasks_completed: int = 0
    last_active: float = field(default_factory=time.time)


class TaskQueue:
    """Priority queue for agent tasks with dependency tracking."""

    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.pending: List[str] = []
        self.assigned: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.in_review: Set[str] = set()
        self.completed: List[str] = []
        self.failed: List[str] = []

    def add_task(self, task: AgentTask):
        """Add a task to the queue."""
        self.tasks[task.task_id] = task
        self.pending.append(task.task_id)
        self._sort_pending()

    def _sort_pending(self):
        """Sort pending tasks by priority."""
        self.pending.sort(key=lambda tid: self.tasks[tid].priority, reverse=True)

    def get_next_task_for_agent(self, agent_type: AgentType) -> Optional[AgentTask]:
        """Get the next suitable task for a specific agent type."""
        capabilities = AGENT_CAPABILITIES.get(agent_type)
        if not capabilities:
            return None

        for task_id in self.pending:
            task = self.tasks[task_id]

            # Check dependencies are complete
            if task.dependencies:
                deps_complete = all(
                    self.tasks.get(dep_id, AgentTask("", "", "", AgentRole.FIXER, [])).status == "completed"
                    for dep_id in task.dependencies
                )
                if not deps_complete:
                    continue

            # Check if task role matches agent's preferred roles
            if task.role in capabilities.preferred_roles:
                return task

            # Check if target files match agent's file patterns
            for pattern in capabilities.file_patterns:
                for target in task.target_files:
                    if Path(target).match(pattern.replace("**/", "")):
                        return task

        # Fallback: return first available task
        for task_id in self.pending:
            task = self.tasks[task_id]
            if not task.dependencies or all(
                self.tasks.get(d).status == "completed" for d in task.dependencies if d in self.tasks
            ):
                return task

        return None

    def assign_task(self, task_id: str, agent_type: AgentType):
        """Assign a task to an agent."""
        if task_id in self.pending:
            self.pending.remove(task_id)
            self.assigned.add(task_id)
            task = self.tasks[task_id]
            task.status = "assigned"
            task.assigned_agent = agent_type

    def start_task(self, task_id: str):
        """Mark a task as in progress."""
        if task_id in self.assigned:
            self.assigned.remove(task_id)
            self.in_progress.add(task_id)
            task = self.tasks[task_id]
            task.status = "in_progress"
            task.started_at = time.time()

    def submit_for_review(self, task_id: str, result: str):
        """Submit task for review."""
        if task_id in self.in_progress:
            self.in_progress.remove(task_id)
            self.in_review.add(task_id)
            task = self.tasks[task_id]
            task.status = "review"
            task.result = result

    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        task = self.tasks.get(task_id)
        if not task:
            return

        for queue in [self.in_review, self.in_progress, self.assigned]:
            if task_id in queue:
                queue.discard(task_id)

        self.completed.append(task_id)
        task.status = "completed"
        task.completed_at = time.time()

    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed."""
        task = self.tasks.get(task_id)
        if not task:
            return

        for queue in [self.in_review, self.in_progress, self.assigned, self.pending]:
            if task_id in queue if isinstance(queue, set) else task_id in queue:
                if isinstance(queue, set):
                    queue.discard(task_id)
                else:
                    queue.remove(task_id) if task_id in queue else None

        self.failed.append(task_id)
        task.status = "failed"
        task.result = f"ERROR: {error}"
        task.completed_at = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Get queue status summary."""
        return {
            "pending": len(self.pending),
            "assigned": len(self.assigned),
            "in_progress": len(self.in_progress),
            "in_review": len(self.in_review),
            "completed": len(self.completed),
            "failed": len(self.failed),
            "total": len(self.tasks),
        }


class CollaborationProtocol:
    """
    Protocol for agents to communicate and coordinate work.

    Uses a shared state file that all agents can read/write to.
    """

    STATE_FILE = ".agent_state.json"

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_path = project_root / self.STATE_FILE
        self.logger = get_logger()

    def _load_state(self) -> Dict[str, Any]:
        """Load shared state from file."""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "tasks": [],
            "messages": [],
            "active_agents": {},
            "last_updated": time.time(),
        }

    def _save_state(self, state: Dict[str, Any]):
        """Save shared state to file."""
        state["last_updated"] = time.time()
        with open(self.state_path, 'w') as f:
            json.dump(state, f, indent=2)

    def register_agent(self, agent_type: AgentType):
        """Register an agent as active."""
        state = self._load_state()
        state["active_agents"][agent_type.value] = {
            "registered_at": time.time(),
            "status": "active",
        }
        self._save_state(state)
        self.logger.info(f"Agent registered: {agent_type.value}")

    def unregister_agent(self, agent_type: AgentType):
        """Unregister an agent."""
        state = self._load_state()
        if agent_type.value in state["active_agents"]:
            del state["active_agents"][agent_type.value]
        self._save_state(state)

    def post_message(self, from_agent: AgentType, message: str,
                     to_agent: Optional[AgentType] = None):
        """Post a message for other agents."""
        state = self._load_state()
        state["messages"].append({
            "from": from_agent.value,
            "to": to_agent.value if to_agent else "all",
            "message": message,
            "timestamp": time.time(),
            "read_by": [],
        })
        # Keep only last 100 messages
        state["messages"] = state["messages"][-100:]
        self._save_state(state)

    def get_messages(self, for_agent: AgentType, unread_only: bool = True) -> List[Dict]:
        """Get messages for an agent."""
        state = self._load_state()
        messages = []
        for msg in state["messages"]:
            if msg["to"] in ["all", for_agent.value]:
                if not unread_only or for_agent.value not in msg.get("read_by", []):
                    messages.append(msg)
        return messages

    def mark_messages_read(self, for_agent: AgentType):
        """Mark all messages as read for an agent."""
        state = self._load_state()
        for msg in state["messages"]:
            if for_agent.value not in msg.get("read_by", []):
                msg.setdefault("read_by", []).append(for_agent.value)
        self._save_state(state)

    def claim_task(self, task_id: str, agent_type: AgentType) -> bool:
        """Attempt to claim a task (atomic operation)."""
        state = self._load_state()
        for task in state["tasks"]:
            if task["task_id"] == task_id:
                if task["status"] == "pending":
                    task["status"] = "assigned"
                    task["assigned_agent"] = agent_type.value
                    self._save_state(state)
                    return True
                return False
        return False

    def add_task(self, task: AgentTask):
        """Add a task to shared state."""
        state = self._load_state()
        state["tasks"].append(task.to_dict())
        self._save_state(state)

    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks."""
        state = self._load_state()
        return [t for t in state["tasks"] if t["status"] == "pending"]

    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None):
        """Update a task's status."""
        state = self._load_state()
        for task in state["tasks"]:
            if task["task_id"] == task_id:
                task["status"] = status
                if result:
                    task["result"] = result
                break
        self._save_state(state)


class AgentOrchestrator:
    """
    Main orchestrator for multi-agent collaboration.

    Coordinates Junie, Claude Code, and Gemini working together
    on the NotebookLM Generation Tool project.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.logger = get_logger()
        self.project_root = project_root or Path.cwd()
        self.task_queue = TaskQueue()
        self.protocol = CollaborationProtocol(self.project_root)

        # Initialize agents
        self.agents: Dict[AgentType, CodingAgent] = {}
        for agent_type, capabilities in AGENT_CAPABILITIES.items():
            self.agents[agent_type] = CodingAgent(
                agent_type=agent_type,
                capabilities=capabilities
            )

    def _generate_task_id(self, title: str) -> str:
        """Generate unique task ID."""
        content = f"{title}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def create_task(
        self,
        title: str,
        description: str,
        role: AgentRole,
        target_files: List[str],
        priority: int = 0,
        dependencies: Optional[List[str]] = None,
        preferred_agent: Optional[AgentType] = None,
    ) -> AgentTask:
        """Create and queue a new task."""
        task = AgentTask(
            task_id=self._generate_task_id(title),
            title=title,
            description=description,
            role=role,
            target_files=target_files,
            priority=priority,
            dependencies=dependencies or [],
            assigned_agent=preferred_agent,
        )

        self.task_queue.add_task(task)
        self.protocol.add_task(task)

        self.logger.info(f"Created task: {task.task_id} - {title}")
        return task

    def assign_best_agent(self, task: AgentTask) -> Optional[AgentType]:
        """Determine the best agent for a task based on capabilities."""
        scores: Dict[AgentType, int] = defaultdict(int)

        for agent_type, capabilities in AGENT_CAPABILITIES.items():
            # Score based on role match
            if task.role in capabilities.preferred_roles:
                scores[agent_type] += 10

            # Score based on file pattern match
            for pattern in capabilities.file_patterns:
                for target in task.target_files:
                    if Path(target).match(pattern.replace("**/", "")):
                        scores[agent_type] += 5

            # Score based on agent availability
            agent = self.agents.get(agent_type)
            if agent and agent.status == "idle":
                scores[agent_type] += 3

        if scores:
            best_agent = max(scores.keys(), key=lambda k: scores[k])
            return best_agent

        return None

    def get_recommended_assignments(self) -> List[Dict[str, Any]]:
        """Get recommended task assignments for all pending tasks."""
        recommendations = []

        for task_id in self.task_queue.pending:
            task = self.task_queue.tasks[task_id]
            best_agent = self.assign_best_agent(task)

            recommendations.append({
                "task_id": task.task_id,
                "title": task.title,
                "role": task.role.value,
                "recommended_agent": best_agent.value if best_agent else "any",
                "target_files": task.target_files,
                "priority": task.priority,
            })

        return recommendations

    def generate_agent_instructions(self, agent_type: AgentType) -> str:
        """Generate instructions for a specific agent based on pending tasks."""
        agent = self.agents.get(agent_type)
        if not agent:
            return "Agent not found."

        capabilities = agent.capabilities
        task = self.task_queue.get_next_task_for_agent(agent_type)

        if not task:
            return f"No tasks currently available for {capabilities.name}."

        # Build instructions
        instructions = f"""
# Task Assignment for {capabilities.name}

## Task: {task.title}
**ID:** {task.task_id}
**Role:** {task.role.value}
**Priority:** {task.priority}

## Description
{task.description}

## Target Files
{chr(10).join(f"- {f}" for f in task.target_files)}

## Your Strengths (use these!)
{chr(10).join(f"- {s}" for s in capabilities.strengths)}

## Instructions
1. Read the target files to understand current state
2. Implement the changes described above
3. Test your changes if applicable
4. When done, post a message using the collaboration protocol:
   - Describe what you changed
   - Note any issues or concerns
   - Tag other agents if review needed

## Collaboration Notes
- If you need help from another agent, post a message
- Check for messages from other agents before starting
- Coordinate on shared files to avoid conflicts
"""
        return instructions

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "agents": {
                agent_type.value: {
                    "name": agent.capabilities.name,
                    "status": agent.status,
                    "current_task": agent.current_task,
                    "tasks_completed": agent.tasks_completed,
                    "strengths": agent.capabilities.strengths[:3],
                }
                for agent_type, agent in self.agents.items()
            },
            "task_queue": self.task_queue.get_status(),
            "pending_tasks": [
                {
                    "id": self.task_queue.tasks[tid].task_id,
                    "title": self.task_queue.tasks[tid].title,
                    "role": self.task_queue.tasks[tid].role.value,
                }
                for tid in self.task_queue.pending[:5]
            ],
        }

    def create_standard_tasks(self, issue_description: str) -> List[AgentTask]:
        """Create a standard set of tasks for fixing an issue."""
        tasks = []

        # Task 1: Analyze (Claude Code)
        analyze_task = self.create_task(
            title="Analyze issue and plan fix",
            description=f"Analyze the following issue and create a plan:\n{issue_description}",
            role=AgentRole.ANALYZER,
            target_files=["src/"],
            priority=10,
            preferred_agent=AgentType.CLAUDE_CODE,
        )
        tasks.append(analyze_task)

        # Task 2: Fix selectors (Junie) - if browser-related
        if any(word in issue_description.lower() for word in ["selector", "click", "element", "browser"]):
            fix_task = self.create_task(
                title="Fix browser automation selectors",
                description=f"Fix CSS selectors and browser automation:\n{issue_description}",
                role=AgentRole.SELECTOR_EXPERT,
                target_files=["src/generators/notebooklm.py", "src/auth/google_auth.py"],
                priority=8,
                dependencies=[analyze_task.task_id],
                preferred_agent=AgentType.JUNIE,
            )
            tasks.append(fix_task)

        # Task 3: Fix API (Gemini) - if API-related
        if any(word in issue_description.lower() for word in ["api", "gemini", "json", "response"]):
            api_task = self.create_task(
                title="Fix API integration",
                description=f"Fix API calls and response handling:\n{issue_description}",
                role=AgentRole.API_EXPERT,
                target_files=["src/generators/gemini_client.py", "src/processors/topic_splitter.py"],
                priority=8,
                dependencies=[analyze_task.task_id],
                preferred_agent=AgentType.GEMINI,
            )
            tasks.append(api_task)

        # Task 4: Review (Claude Code)
        review_task = self.create_task(
            title="Review all changes",
            description="Review all changes made by other agents, ensure quality and consistency.",
            role=AgentRole.REVIEWER,
            target_files=["src/"],
            priority=5,
            dependencies=[t.task_id for t in tasks[1:]],
            preferred_agent=AgentType.CLAUDE_CODE,
        )
        tasks.append(review_task)

        return tasks


def print_agent_guide():
    """Print a guide for agents to follow."""
    guide = """
╔══════════════════════════════════════════════════════════════════╗
║           MULTI-AGENT COLLABORATION PROTOCOL                      ║
║              NotebookLM Generation Tool                           ║
╠══════════════════════════════════════════════════════════════════╣

AGENT ROLES & RESPONSIBILITIES:

🤖 JUNIE (JetBrains AI)
   Expertise: Selenium, CSS selectors, browser automation
   Files: notebooklm.py, google_auth.py, downloader.py
   Tasks: Fix click interception, update selectors, handle overlays

🧠 CLAUDE CODE (Anthropic)
   Expertise: Architecture, refactoring, documentation, git
   Files: main.py, orchestrator/, README.md, JOURNAL.md
   Tasks: Design patterns, error handling, code review, commits

✨ GEMINI (Google)
   Expertise: Google APIs, JSON parsing, content generation
   Files: gemini_client.py, topic_splitter.py, generators/
   Tasks: API integration, prompt engineering, response handling

COLLABORATION WORKFLOW:

1. CHECK STATE: Read .agent_state.json for pending tasks/messages
2. CLAIM TASK: Update state to claim a task before starting
3. IMPLEMENT: Make changes to your assigned files
4. NOTIFY: Post message about what you changed
5. REVIEW: Check other agents' changes if requested

COMMUNICATION:
- Use .agent_state.json for async communication
- Tag specific agents in messages when needed
- Describe changes clearly for review

FILE OWNERSHIP:
- Prefer working on files matching your expertise
- Coordinate before modifying shared files
- Always run syntax checks before committing

╚══════════════════════════════════════════════════════════════════╝
"""
    print(guide)
    return guide


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        orchestrator = AgentOrchestrator()

        if command == "status":
            status = orchestrator.get_status()
            print(json.dumps(status, indent=2))

        elif command == "guide":
            print_agent_guide()

        elif command == "tasks":
            recs = orchestrator.get_recommended_assignments()
            print(json.dumps(recs, indent=2))

        elif command == "instructions":
            if len(sys.argv) > 2:
                agent_name = sys.argv[2].lower()
                agent_map = {
                    "junie": AgentType.JUNIE,
                    "claude": AgentType.CLAUDE_CODE,
                    "gemini": AgentType.GEMINI,
                }
                if agent_name in agent_map:
                    instructions = orchestrator.generate_agent_instructions(agent_map[agent_name])
                    print(instructions)
                else:
                    print(f"Unknown agent: {agent_name}")
            else:
                print("Usage: python agent_orchestrator.py instructions <junie|claude|gemini>")

        elif command == "create":
            if len(sys.argv) > 2:
                issue = " ".join(sys.argv[2:])
                tasks = orchestrator.create_standard_tasks(issue)
                print(f"Created {len(tasks)} tasks:")
                for t in tasks:
                    print(f"  - {t.task_id}: {t.title} ({t.role.value})")
            else:
                print("Usage: python agent_orchestrator.py create <issue description>")
        else:
            print("Commands: status, guide, tasks, instructions <agent>, create <issue>")
    else:
        print_agent_guide()
