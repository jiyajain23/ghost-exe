# Phase 0 verification — October 27, 2026

Read AGENTS.md, PLAN.md, STORY.md, and STATE.md completely. The original four
documents were left unchanged. Implemented Phase 0 only; no playable investigation.

## Exact added files

```text
.gitignore
README.md
PHASE0_REPORT.md
pytest.ini
backend/requirements.txt
backend/app/__init__.py
backend/app/__main__.py
backend/app/main.py
backend/app/config.py
backend/app/api/__init__.py
backend/app/api/schemas.py
backend/app/content/__init__.py
backend/app/content/documents.json
backend/app/content/manifest.py
backend/app/director/__init__.py
backend/app/storage/__init__.py
backend/app/ghost/__init__.py
backend/app/ghost/adapter.py
backend/tests/test_scaffold.py
frontend/index.html
frontend/package.json
frontend/package-lock.json
frontend/tsconfig.json
frontend/vite.config.ts
frontend/src/main.tsx
frontend/src/api/client.ts
frontend/src/styles/index.css
```

Also initialized local `.git/` metadata. This folder initially had no repository;
Git discovered an unrelated home-folder repository and failed. The parent was not
changed. No files were staged, committed, pushed, or attached to a remote.

## Implemented

FastAPI health endpoint, explicit loopback startup, Vite-only CORS, environment
configuration, strict action/reply schemas, RunState/file metadata contracts,
typed asynchronous GhostAdapter and harmless mock stub. Director and storage are
reserved packages without transitions or database logic. All ten canonical initial
documents are immutable backend seed data, copied verbatim from STORY.md. No D01
seed, file endpoints, or spoiler content is sent to the browser.

React/TypeScript/Tailwind displays a typed and runtime-validated backend health
request with five-second timeout, pending/error states, and Retry. System fonts,
visible keyboard focus, and reduced-motion CSS; no remote assets or services.

## Commands and results

- `python -m pytest backend/tests -q`: **31 passed, 1 warning in 2.77s**.
  Used existing Python 3.13.0 packages matching requirements.txt. Windows test
  sockets stalled in the sandbox; the successful run used approved elevated access.
- `npm.cmd install --no-fund --fetch-retries=0 --fetch-timeout=20000`
  from frontend: installed dependencies. Initial Vite audit finding was resolved
  with `npm.cmd install --save-dev --save-exact vite@6.4.5 --no-fund --fetch-retries=0 --fetch-timeout=20000`.
  Final installation audit: **0 vulnerabilities**. Registry access required
  elevated access after sandboxed installation stalled.
- `npm.cmd run build` from frontend: **passed**, including `tsc --noEmit`;
  Vite transformed 29 modules. JS 188.16 kB (59.63 kB gzip), CSS 8.22 kB.
- `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
  and `npm.cmd run dev` from frontend: both started on loopback.
- Real browser: connected in mock mode; stopped backend, clicked Retry, observed
  recoverable error; restarted backend, clicked Retry, observed successful recovery.
- Local HTTP probe returned `{"status":"ok","agent_mode":"mock","ollama_reachable":null}`.
  Vite refused a direct `/@fs/` request for STORY.md with **403**.
  Production assets contained neither checked spoiler marker (`HELPER-SVC` and
  the canonical containment sequence); backend isolation tests also passed.
- `git init --initial-branch=main .`: initialized this project only.
- `git status --short --untracked-files=all`, `git ls-files`, and `git check-ignore`
  confirmed only source/docs are candidates; no files tracked and DB, venv, .env,
  node_modules, build, cache, and model paths ignored.

## Remaining limits

One Starlette warning deprecates its httpx TestClient integration. Tests still
pass; no extra dependency was added solely to suppress the warning. A fresh
virtualenv installation was not performed; the README documents that setup path.
No separate lint task is configured. No model installation/inference, complete-game
offline test, SQLite persistence, or memory accuracy is claimed. Ollama reachability
is intentionally null (not probed), even if the configured mode is ollama.

Phase 1 remains entirely unimplemented and requires explicit user instruction.
