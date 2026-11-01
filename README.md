# agents-autonomous

Agente autónomo local con **LangChain + LangGraph**, LLM vía **Ollama**, skills **ECC**, y Docker Compose.

## Qué hace el agente

Recibe una **meta en lenguaje natural** (API o CLI), la descompone en pasos y usa herramientas:

| Tool | Para qué |
|---|---|
| `list_skills` / `load_skill` | Cargar guías ECC (p.ej. `angular-developer`) antes de codear |
| `scaffold_angular_app` | Crear una app Angular con CLI (no interactivo) |
| `write/read/list_workspace_*` | Editar archivos solo dentro de `workspace/` |
| `run_shell` | npm / npx / ng / node (allowlist) |
| `web_search` | Búsqueda corta con DuckDuckGo |
| `calculator` | Aritmética segura |

**POC actual:** puede crear una página/app web con Angular siguiendo el skill ECC `angular-developer`.

## Stack

| Servicio | Rol |
|---|---|
| `agent` | FastAPI + LangGraph ReAct + Node 22 (para Angular CLI) |
| `ollama` | LLM local (`qwen2.5:7b` por defecto) |
| `redis` | Reservado para persistencia futura |
| `ollama-init` | Descarga el modelo al arrancar |

## Skills ECC incluidas

Ver [`skills/README.md`](skills/README.md):

- `angular-developer`
- `frontend-design-direction`
- `coding-standards`

## Arranque (cuando quieras levantar Docker)

```bash
cp .env.example .env
docker compose up --build
```

No hace falta levantarlo todavía para revisar el código. La primera vez descarga Ollama + el modelo 7B.

API: http://localhost:8000/docs

## POC — crear una página Angular

Cuando el stack esté arriba:

```bash
curl -s -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Usa el skill angular-developer de ECC. Crea una app Angular llamada poc-landing con una landing page simple (hero + CTA). Edita los templates/estilos y deja instrucciones para npm start."}'
```

O CLI:

```bash
docker compose exec agent python -m app run \
  "Load ECC skill angular-developer, scaffold Angular app poc-landing, make a simple landing page."
```

El resultado queda en `workspace/poc-landing/`.

## Desarrollo local (sin Docker)

Necesitas Ollama local + Python 3.12 + Node 22:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OLLAMA_BASE_URL=http://localhost:11434
export AGENT_WORKSPACE="$PWD/workspace"
export AGENT_SKILLS_DIR="$PWD/skills"
export AGENT_ALLOW_SHELL=true
uvicorn app.main:app --reload --port 8000
```

## Estructura

```
app/                 # FastAPI + LangGraph agent
skills/              # ECC skills vendored (POC)
workspace/           # sandbox del agente
docker-compose.yml
Dockerfile
```
