# ECC skills (POC)

Skills vendored from **Everything Claude Code (ECC)** so the local LangGraph agent
can load specialized guidance with `list_skills` / `load_skill`.

## Included for this POC

| Skill | Use when |
|---|---|
| `angular-developer` | Create/edit Angular apps, components, routing, signals |
| `frontend-design-direction` | Visual direction for landing/marketing pages |
| `coding-standards` | General code quality defaults |

## Agent workflow

1. `list_skills`
2. `load_skill("angular-developer")` (and references as needed)
3. `scaffold_angular_app("poc-landing")` or write files manually
4. Edit `src/app/*` with `write_workspace_file`
5. Optional: `run_shell("npm start --prefix poc-landing")`
