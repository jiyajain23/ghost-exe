# GHOST.EXE

A local-first psychological horror investigation set on a fictional recovered
2003 desktop. **Current implementation: Phase 0 scaffold only. No playable game yet.**

The screen checks the local FastAPI backend through a typed HTTP client. There
are no game sessions, chat endpoints, clue transitions, saves, or model inference
yet. The ten canonical documents are private backend seed data. D01 is not seeded;
it will be generated from real recorded events in a later phase.

## Windows PowerShell setup

Prerequisites: Python 3.11+ and Node.js 22.12+ with npm. Dependency installation
requires internet access. Ollama and model weights are **not required for Phase 0**.
Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend ci
```

Terminal 1 (backend; no activation or execution-policy change needed):

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Terminal 2 (frontend):

```powershell
npm.cmd --prefix frontend run dev
```

Open http://127.0.0.1:5173. Expect “Backend connected · ok” and “Agent mode: mock”.
Both servers bind to loopback. CORS allows only the two Vite development origins,
`http://127.0.0.1:5173` and `http://localhost:5173`. Stop servers with Ctrl+C.

## Configuration

Environment variables are read at backend startup; `.env` files are not auto-loaded.

| Variable | Default | Purpose |
| --- | --- | --- |
| `GHOST_AGENT_MODE` | `mock` | `mock` or `ollama`; selection contract only in Phase 0 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | HTTP loopback origin only |
| `OLLAMA_MODEL` | `gemma3:1b` | Reserved for Phase 3 adapter |
| `GHOST_MODEL_TIMEOUT_SECONDS` | `20` | Positive timeout, at most 120 seconds; reserved for inference |

For example: `$env:GHOST_AGENT_MODE = "mock"` before starting the backend.
`GET /api/health` returns `status`, configured `agent_mode`, and
`ollama_reachable: null`. Null means **not probed**, not unreachable. Health and
startup perform no inference or Ollama connection. Choosing `ollama` does not
implement live inference; that work is explicitly deferred to Phase 3.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend run build
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The build includes TypeScript checking. No separate linter is configured.
Tests cover health without network access, CORS, private content isolation,
configuration, action/reply validation, mock behavior, and exact canonical seeds.

If the screen reports a connection error, start the backend and click **Retry
connection**. Requests time out after five seconds. If port 5173 is occupied,
stop the process using it; Vite intentionally does not switch to another port.
Invalid backend configuration fails at startup with a validation error.
Use `npm.cmd` if PowerShell blocks `npm.ps1`.

## Architecture and privacy

- `backend/app/api/schemas.py`: validated public state, action, and Ghost contracts.
- `backend/app/ghost/adapter.py`: typed adapter interface and side-effect-free mock.
- `backend/app/content/`: immutable F01–F10 seeds, never mounted or bundled publicly.
- `backend/app/director/` and `storage/`: reserved packages, no gameplay/persistence yet.
- `frontend/src/api/client.ts`: local health request with response validation.

The deterministic Python Director will own all truth and transitions; the model
will propose dialogue and cosmetic effects only. Virtual file IDs never authorize
real filesystem access. There are no remote assets, fonts, telemetry, browser
permissions, or cloud inference. No database or player history is created in this
phase. Future app-owned data belongs under ignored `backend/data/`.

The story and state specifications remain developer-only. Complete-game offline
operation, local model performance, and cross-run memory are not implemented or
verified yet. Phase 1 adds the three desktop apps and the first playable mock flow;
it requires a separate reviewed task.
