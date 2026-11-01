"""Load ECC-style skills shipped with this repo for the autonomous agent."""

from __future__ import annotations

import re
from pathlib import Path

from app.config import get_settings


def skills_root() -> Path:
    settings = get_settings()
    configured = settings.agent_skills_dir.resolve()
    if configured.exists():
        return configured
    # Fallback: repo-relative skills/ when running outside Docker
    local = Path(__file__).resolve().parents[2] / "skills"
    return local if local.exists() else configured


def _parse_frontmatter(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not text.startswith("---"):
        return meta
    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def list_available_skills() -> list[dict[str, str]]:
    root = skills_root()
    if not root.exists():
        return []
    skills: list[dict[str, str]] = []
    for skill_md in sorted(root.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        name = meta.get("name") or skill_md.parent.name
        description = meta.get("description") or "No description"
        skills.append(
            {
                "name": name,
                "path": str(skill_md.relative_to(root)),
                "description": description,
            }
        )
    return skills


def load_skill(name: str, *, max_chars: int = 12000) -> str:
    """Load a skill by folder/name. Optionally include a reference file via 'name/ref'."""
    root = skills_root()
    requested = name.strip().strip("/")
    if not requested:
        return "Skill name is required. Call list_skills first."

    # Allow "angular-developer" or "angular-developer/references/components.md"
    candidate = (root / requested).resolve()
    if not str(candidate).startswith(str(root.resolve())):
        return "Invalid skill path."

    if candidate.is_dir():
        candidate = candidate / "SKILL.md"
    elif not candidate.suffix:
        candidate = root / requested / "SKILL.md"

    if not candidate.exists():
        matches = [
            p for p in root.glob("*/SKILL.md") if p.parent.name.lower() == requested.lower()
        ]
        if not matches:
            available = ", ".join(s["name"] for s in list_available_skills()) or "(none)"
            return f"Skill not found: {name}. Available: {available}"
        candidate = matches[0]

    text = candidate.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip("\n")
    header = f"# Skill: {meta.get('name', candidate.parent.name)}\n\n"
    content = header + body
    if len(content) > max_chars:
        content = (
            content[:max_chars]
            + "\n\n[truncated — ask for a specific references/*.md file if needed]"
        )
    refs_dir = candidate.parent / "references"
    if refs_dir.is_dir():
        refs = sorted(p.name for p in refs_dir.glob("*.md"))
        if refs:
            content += (
                "\n\n## Available references\n"
                + "\n".join(f"- {candidate.parent.name}/references/{r}" for r in refs)
                + "\nLoad with load_skill using one of those paths when needed."
            )
    return content


def skills_catalog_for_prompt() -> str:
    skills = list_available_skills()
    if not skills:
        return "No ECC skills are installed under skills/."
    lines = ["Available ECC skills (load before specialized work):"]
    for skill in skills:
        desc = re.sub(r"\s+", " ", skill["description"])[:160]
        lines.append(f"- {skill['name']}: {desc}")
    lines.append(
        "Workflow: list_skills → load_skill('<name>') → follow the skill → "
        "write files / run allowed shell commands in the workspace."
    )
    return "\n".join(lines)
