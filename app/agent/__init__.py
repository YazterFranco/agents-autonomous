"""Agent package. Import build_agent/run_agent from app.agent.graph when needed."""

__all__ = ["build_agent", "run_agent"]


def __getattr__(name: str):
    if name in {"build_agent", "run_agent"}:
        from app.agent.graph import build_agent, run_agent

        return {"build_agent": build_agent, "run_agent": run_agent}[name]
    raise AttributeError(name)
