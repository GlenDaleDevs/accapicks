# Agent Workflow

## Agents

| Agent | Role |
|---|---|
| `critic` | Devil's advocate — challenges plans before implementation. Read-only. |
| `frontend-dev` | Implements frontend code under `src/` |
| `backend-dev` | Implements backend code under `backend/app/` |
| `database` | Schema design, models, migrations |
| `odds-api` | The-Odds-API integration |
| `code-reviewer` | Reviews written code for bugs/security. Read-only. |
| `tester` | Writes and runs tests |
| `devops` | Build, deploy, config files |
| `web-design-planner` | Visual design direction and UI/UX recommendations |
| `legal-gambling-compliance` | UK gambling law, GDPR, legal documents |

## Pipeline (non-trivial changes)

1. **Orchestrator** — reads files, scopes work, writes plan (planning stays in main context, not delegated)
2. **critic** — challenges the plan
3. **Implementation agents** — run in parallel where independent
4. **code-reviewer + tester** — run in parallel after implementation

## Skip to step 3 for:
- Single-file bug fixes, copy/text changes, config tweaks, obvious approaches

## The `annoying-user` agent

Use `critic` subagent with adversarial prompt. Thinks like an impatient, creative, slightly malicious user who tries to bypass validation, race conditions, abuse business logic, test edge cases, and break navigation.

## Parallel execution

Always run in parallel when possible: frontend + backend for full-stack features, code review + test writing, multiple independent agents.
