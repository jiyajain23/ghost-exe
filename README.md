# GHOST.EXE

A local-first psychological horror investigation on a fictional recovered 2003
VesperOS desktop. The Python Director owns evidence, clue gates, saves, and the
single ending. Phase 3 adds optional local Gemma 3 dialogue through Ollama.
Cross-run memory and generated D01 notes remain Phase 4 work.

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

October 30, 2026 verification:

- Existing baseline: 76 tests passed before changes.
- Final backend suite: **94 passed**, with one existing Starlette/httpx deprecation warning.
- Backend tests cover HTTP/schema failures, redirects, response bounds, injection
  role separation, unsupported story details, timeouts, progression after failure,
  and browsing during pending inference. See `backend/tests/test_phase3.py`.
- Frontend TypeScript and production build passed.
- Installed `gemma3:1b` (806 MB) handled five live prompts: mean 5.18 seconds;
  one accepted generated greeting and four safe fallbacks after filtering.
  Example: Gemma said "Greetings."; mock introduced itself as the indexing service.
- The initial live check invented a project named Chronos. The strengthened filter
  rejects that response; it is retained as a regression case. These few samples
  do not establish universal model correctness or latency.
- Manual browser verification was blocked: Computer Use was not approved to launch
  Brave. Chat rendering, full UI playthrough, and Wi-Fi-off video remain unverified.
- The supplied frontend still lacks containment API wiring and document-list
  refresh on clue unlocks; those pre-existing Phase 2 gaps mean full UI completion
  must not be claimed from the passing Director playthrough tests.

No external inference is configured. Actual disconnected-network operation has
not been demonstrated. Phase 3 acceptance remains pending the browser/offline
checks. No Phase 4 memory implementation, commit, push, or PR was performed.
