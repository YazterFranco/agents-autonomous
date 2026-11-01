"""LangGraph ReAct agent wired to Ollama + workspace tools."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.agent.skills import skills_catalog_for_prompt
from app.agent.tools import get_tools
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a local autonomous agent running fully on the user's machine.

Goals:
- Break the user goal into concrete steps.
- For specialized work (Angular, frontend design, coding standards), ALWAYS call list_skills
  then load_skill before writing code. Follow the ECC skill instructions.
- Prefer tools over guessing: scaffold_angular_app for new Angular apps, then edit files.
- Prefer writing useful artifacts into the workspace.
- When finished, give a clear final answer with what you did and where files live.

Constraints:
- Stay inside the workspace for file operations.
- Shell is allowlisted (npm/npx/ng/node/...). Do not attempt unrelated system commands.
- Be concise and action-oriented.

{skills_catalog}
"""

_agent = None


def _build_checkpointer(settings: Settings):
    """Use in-memory checkpointer; Redis remains available for future persistence."""
    from langgraph.checkpoint.memory import MemorySaver

    logger.info(
        "Using MemorySaver checkpointer (Redis at %s reserved for future persistence)",
        settings.redis_url,
    )
    return MemorySaver()


def build_agent(settings: Settings | None = None, *, force_reload: bool = False):
    global _agent
    settings = settings or get_settings()
    if _agent is not None and not force_reload:
        return _agent

    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.2,
    )
    checkpointer = _build_checkpointer(settings)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(skills_catalog=skills_catalog_for_prompt())
    _agent = create_react_agent(
        model=llm,
        tools=get_tools(),
        checkpointer=checkpointer,
        prompt=prompt,
    )
    return _agent


def run_agent(
    goal: str,
    *,
    thread_id: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Execute one autonomous run and return a structured result."""
    settings = settings or get_settings()
    graph = build_agent(settings)
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": settings.agent_max_iterations,
    }
    result = graph.invoke(
        {"messages": [HumanMessage(content=goal)]},
        config=config,
    )
    messages = result.get("messages", [])
    final_text = ""
    transcript: list[dict[str, str]] = []
    for message in messages:
        role = getattr(message, "type", message.__class__.__name__)
        content = message.content if hasattr(message, "content") else str(message)
        if isinstance(content, list):
            content = " ".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        transcript.append({"role": str(role), "content": str(content)})
        if isinstance(message, AIMessage) and content:
            final_text = str(content)

    return {
        "thread_id": thread_id,
        "goal": goal,
        "result": final_text or "No final answer produced.",
        "messages": transcript,
    }
