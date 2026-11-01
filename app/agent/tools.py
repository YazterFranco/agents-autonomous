"""Tools available to the autonomous agent (scoped to workspace + ECC skills)."""

from __future__ import annotations

import ast
import operator
import re
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from app.agent.skills import list_available_skills, load_skill as read_skill
from app.config import get_settings

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}

_ALLOWED_SHELL_PREFIXES = (
    "npm ",
    "npx ",
    "ng ",
    "node ",
    "ls",
    "pwd",
    "cat ",
    "mkdir ",
    "cp ",
    "mv ",
    "rm ",
    "chmod ",
    "test ",
    "which ",
    "echo ",
)


def _workspace() -> Path:
    root = get_settings().agent_workspace.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(relative: str) -> Path:
    root = _workspace()
    target = (root / relative).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("Path escapes the agent workspace")
    return target


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Only basic arithmetic is allowed")


@tool
def list_skills() -> str:
    """List ECC skills available to guide specialized work (Angular, coding standards, etc.)."""
    skills = list_available_skills()
    if not skills:
        return "No skills found under skills/."
    lines = []
    for skill in skills:
        lines.append(f"- {skill['name']}: {skill['description']}")
    return "\n".join(lines)


@tool
def load_skill(
    name: Annotated[
        str,
        "Skill name or path, e.g. 'angular-developer' or "
        "'angular-developer/references/components.md'",
    ],
) -> str:
    """Load an ECC skill (or one of its references) into context before coding."""
    return read_skill(name)


@tool
def calculator(expression: Annotated[str, "Arithmetic expression, e.g. '(2+3)*4'"]) -> str:
    """Evaluate a basic arithmetic expression safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except Exception as exc:  # noqa: BLE001
        return f"Calculator error: {exc}"


@tool
def list_workspace(
    relative_dir: Annotated[str, "Directory relative to workspace (default '.')"] = ".",
) -> str:
    """List files and folders inside the agent workspace."""
    path = _safe_path(relative_dir)
    if not path.exists():
        return f"Directory not found: {relative_dir}"
    if not path.is_dir():
        return f"Not a directory: {relative_dir}"
    entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    if not entries:
        return "(empty)"
    lines = []
    for entry in entries:
        kind = "dir" if entry.is_dir() else "file"
        lines.append(f"{kind}\t{entry.relative_to(_workspace())}")
    return "\n".join(lines)


@tool
def read_workspace_file(
    relative_path: Annotated[str, "File path relative to workspace"],
) -> str:
    """Read a text file from the agent workspace (max 50 KB)."""
    path = _safe_path(relative_path)
    if not path.exists() or not path.is_file():
        return f"File not found: {relative_path}"
    data = path.read_bytes()
    if len(data) > 50_000:
        return "File too large (>50KB). Read a smaller file or summarize externally."
    return data.decode("utf-8", errors="replace")


@tool
def write_workspace_file(
    relative_path: Annotated[str, "File path relative to workspace"],
    content: Annotated[str, "Full text content to write"],
) -> str:
    """Create or overwrite a text file inside the agent workspace."""
    path = _safe_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {relative_path}"


@tool
def web_search(
    query: Annotated[str, "Search query"],
    max_results: Annotated[int, "Number of results (1-5)"] = 3,
) -> str:
    """Search the public web with DuckDuckGo and return short snippets."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "duckduckgo-search is not installed"

    limit = max(1, min(int(max_results), 5))
    rows: list[str] = []
    with DDGS() as ddgs:
        for i, item in enumerate(ddgs.text(query, max_results=limit), start=1):
            title = item.get("title", "")
            href = item.get("href", "")
            body = item.get("body", "")
            rows.append(f"{i}. {title}\n   {href}\n   {body}")
    return "\n\n".join(rows) if rows else "No results found."


def _shell_allowed(command: str) -> str | None:
    """Return an error message if the command is not allowed, else None."""
    stripped = command.strip()
    if not stripped:
        return "Empty command."
    forbidden = ["`", "$(", ">", "<", "\n", ";", "||"]
    if any(token in stripped for token in forbidden):
        return "Command rejected: dangerous metacharacters are not allowed."
    # Allow && chains only when every segment starts with an allowlisted prefix
    segments = [part.strip() for part in stripped.split("&&")]
    for segment in segments:
        if segment.startswith("cd "):
            # only allow cd into relative workspace subdirs
            target = segment[3:].strip().strip("'\"")
            if target.startswith("/") or ".." in Path(target).parts:
                return "cd is limited to relative paths inside the workspace."
            continue
        if not any(
            segment == prefix.strip() or segment.startswith(prefix)
            for prefix in _ALLOWED_SHELL_PREFIXES
        ):
            return (
                "Command rejected. Allowed prefixes: "
                + ", ".join(p.strip() for p in _ALLOWED_SHELL_PREFIXES)
            )
    return None


@tool
def run_shell(
    command: Annotated[
        str,
        "Shell command inside the workspace (npm/npx/ng/node/ls/...); && chains OK",
    ],
) -> str:
    """Run an allowlisted shell command inside the workspace (POC: npm/ng enabled)."""
    settings = get_settings()
    if not settings.agent_allow_shell:
        return (
            "Shell tool is disabled. Set AGENT_ALLOW_SHELL=true to enable "
            "(use only in trusted environments)."
        )
    reason = _shell_allowed(command)
    if reason:
        return reason
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=_workspace(),
            capture_output=True,
            text=True,
            timeout=settings.agent_shell_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {settings.agent_shell_timeout}s"
    output = (completed.stdout or "") + (completed.stderr or "")
    return f"exit={completed.returncode}\n{output[:12000]}"


@tool
def scaffold_angular_app(
    project_name: Annotated[
        str,
        "Directory/project name under workspace, e.g. 'poc-landing'",
    ],
    stylesheet: Annotated[str, "css | scss | sass | less"] = "css",
) -> str:
    """
    Create a new Angular app in the workspace using the Angular CLI (non-interactive).
    Prefer loading the 'angular-developer' ECC skill first, then call this tool.
    """
    settings = get_settings()
    if not settings.agent_allow_shell:
        return "Shell is disabled; cannot scaffold Angular. Set AGENT_ALLOW_SHELL=true."

    name = project_name.strip().strip("/")
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,40}", name):
        return "Invalid project_name. Use letters/numbers/_/- starting with a letter."

    target = _safe_path(name)
    if target.exists() and any(target.iterdir()):
        return f"Target already exists and is not empty: {name}"

    style = stylesheet if stylesheet in {"css", "scss", "sass", "less"} else "css"
    npx = shutil.which("npx") or "npx"
    cmd = (
        f"{npx} -y @angular/cli@latest new {name} "
        f"--defaults --skip-git --directory {name} --style={style} --ssr=false"
    )
    try:
        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=_workspace(),
            capture_output=True,
            text=True,
            timeout=settings.agent_shell_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Angular scaffold timed out after {settings.agent_shell_timeout}s"

    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        return f"scaffold failed (exit={completed.returncode})\n{output[:12000]}"

    app_component = target / "src" / "app" / "app.component.ts"
    hint = (
        f"Created Angular app at workspace/{name}. "
        "Next: load_skill('angular-developer'), edit components under "
        f"{name}/src/app/, then run `npm start --prefix {name}` if needed."
    )
    if not app_component.exists():
        # Newer CLI may use app.ts
        alt = list((target / "src" / "app").glob("app.*")) if (target / "src" / "app").exists() else []
        hint += f" App entry files: {[p.name for p in alt]}"
    return f"{hint}\n\nCLI output (tail):\n{output[-4000:]}"


def get_tools() -> list:
    return [
        list_skills,
        load_skill,
        calculator,
        list_workspace,
        read_workspace_file,
        write_workspace_file,
        web_search,
        run_shell,
        scaffold_angular_app,
    ]
