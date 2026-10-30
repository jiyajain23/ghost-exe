# GHOST.EXE

A local-first psychological horror investigation on a fictional recovered 2003
VesperOS desktop. The Python Director owns evidence, clue gates, saves, and the
single ending. Phase 3 adds optional local Gemma 3 dialogue through Ollama.
Phase 4 implements cross-run memory and generated D01 notes from saved in-game events.

## Windows PowerShell

Requires Python 3.11+ and Node.js 22.12+. First-time dependencies and model downloads
need internet. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend ci
```

Backend (terminal 1):

```powershell
$env:GHOST_AGENT_MODE = "mock"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Frontend (terminal 2):

```powershell
npm.cmd --prefix frontend run dev
```

Open http://127.0.0.1:5173. Use HELPER, File Explorer, and Mail. Refresh resumes the
saved run ID. Only app-owned data under `backend/data/` is persisted. Chat text is
not written to SQLite; question categories are recorded. No real device files
are exposed. Canonical documents and developer specifications stay backend-only.

## Optional local Gemma

Install/start Ollama, then download the small profile if not already present:

```powershell
ollama pull gemma3:1b
ollama list
$env:GHOST_AGENT_MODE = "ollama"
$env:OLLAMA_MODEL = "gemma3:1b"
$env:GHOST_MODEL_TIMEOUT_SECONDS = "20"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Restart the backend after changing settings. `OLLAMA_BASE_URL` defaults to
`http://127.0.0.1:11434` and accepts HTTP loopback origins only. Model names must
be local Gemma 3 size tags; cloud aliases are rejected. Optional `gemma3:4b` is
not benchmarked here. Timeout is positive, up to 120 seconds. The chat client
allows 125 seconds for the maximum configured timeout; other requests allow 25.

The backend calls Ollama `/api/chat` with a JSON schema, validates the result
with Pydantic, and applies deterministic narrative/effect checks. HTTP proxies,
redirects, tools, and automatic retries are disabled. Prompts contain a short
persona, stage-safe facts, and at most two prior question categories, plus the
current message. They contain no full transcripts, hidden documents, or DB details.

Direct solution questions receive authored replies. Generated dialogue uses a
conservative atmospheric vocabulary; unsupported vocabulary and suspicious text
fall back to stage-safe lines without effects. This limits variety deliberately.
Model failures display recoverable Chat status and do not hold a DB transaction
or block browsing documents. `/api/health` performs no inference or network probe;
`ollama_reachable: null` means not probed, not a live-availability claim.

## Verification

```powershell
python -m pytest backend/tests -q
npm.cmd --prefix frontend run build
python backend/verify_phase3.py
```

The last command opts into five local inference requests, uses a temporary save,
and prints timings, fallback counts, and mock/Gemma comparisons. Use the venv
Python instead if dependencies were installed there. On this laptop, the installed
system Python had dependencies; no `.venv` existed during verification.

## Current verification and limitations

October 30, 2026: 103 backend tests and 3 frontend ending-render tests pass.
The frontend build includes TypeScript checking and passes. Tests repeat the full
ending/memory scenario three times on one save, cover both photo choices, duplicate
reads/choices, completed-run restoration, and simulated chat outage/recovery.

Actual Gemma 3 1B inference was verified in Phase 3. A five-question C1 sample
averaged 5.84 seconds: one generated reply passed and four used safety fallbacks.
This small sample does not guarantee latency or model correctness. Browser
click-through and physical internet-disconnection proof remain unverified.
Containment UI, document refresh, and the dedicated ending screen are implemented.

No DB files, environment files, model binaries, caches, or build output were found
in tracked files during this pass. A fresh-clone dependency installation was not
repeated; the build used existing local dependencies. No accounts or secret keys
are required. Do not treat local-only configuration as demonstrated offline proof.

## Hardware and troubleshooting

The installed Gemma 3 1B weights occupied approximately 806 MB. Allow additional
space for Ollama, Python/Node dependencies, and runtime caches; inference also uses
RAM beyond the weight size. No minimum RAM or speed guarantee has been measured.
Larger Gemma profiles are optional and unverified. Mock mode requires no model.

- Backend unavailable: start the backend on 127.0.0.1:8000, then retry connection.
- Port 5173 occupied: stop your other dev server; Vite intentionally uses a fixed port.
- HELPER interrupted: check `ollama list` and backend mode; safe scripted replies let
  you continue. Restart the backend after changing environment settings.
- Stale save after history clear: refresh, then explicitly start a new investigation.
- PowerShell blocks npm.ps1: use `npm.cmd`; venv activation is not required.
- On small screens app windows fill the available area; use taskbar buttons to switch.

See [DEMO.md](DEMO.md) for the 60–90 second recording script and remaining manual checks.

## Phase 4: persistent investigation memory

Restart Investigation now creates a new saved run and abandons an active prior run.
Refresh resumes the same run. On the first chat of a new run with meaningful prior
history, the Director references the saved photo choice (preferred), file read, or
question category and reveals SYSTEM/HELPER_NOTES.TXT. Notes are generated from a
bounded event projection stored at run creation; inference cannot invent the reveal.
No raw player chat is stored. Both photo branches are supported.

To clear app-owned history explicitly (this removes all saved investigations), run:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/history/clear -ContentType 'application/json' -Body '{"confirm":true}'
```

Then refresh and start a new investigation when the stale-save message appears.
Only the app database is cleared; canonical files and model weights are untouched.
Phase 4 tests cover both photo choices, hidden notes before reveal, DB-backed notes,
server recreation, no history, alternate sources and clearing linked runs. Browser
verification remains pending because browser automation access was not approved.


Phase 4 verification: `python -m pytest backend/tests -q` passed 101 tests;
`npm.cmd --prefix frontend run build` passed TypeScript and production bundling;
`node --test frontend/tests/ending.cjs` passed all 3 ending tests.
`python backend/verify_phase4.py` passed the real HTTP demo in both mock and
Ollama-configured modes using temporary saves. Memory replies bypass inference in
both modes; this does not measure Gemma performance. Full browser click-through
and disconnected-network proof remain unverified. Phase 5 regression and documentation work is complete; browser/offline acceptance checks remain pending.
