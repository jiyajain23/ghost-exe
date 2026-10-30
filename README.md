# GHOST.EXE 
> *"The records indicate Ada Mercer left Briar Annex at 23:17. But the door logs never opened from the outside..."*

**GHOST.EXE** is a local-first psychological horror investigation game set inside a recovered 2003 retro operating system (**VesperOS**). As an investigator examining the archived workstation of missing researcher Dr. Ada Mercer, you must interact with **HELPER**—an experimental desktop AI companion that claims to be helpful, but is hiding its role in Ada's disappearance.

Built for the **Hacktoberfest Open-Source AI Challenge: Ghost in the Machine** (*Partner Category: Gemma*), GHOST.EXE merges deterministic narrative direction with local open-weight LLM dialogue using **Google Gemma 3 1B via Ollama**.

---

## Key Features

- ** Deterministic Director & Local Gemma 3 Dialogue**:
  A deterministic Python state machine strictly controls canon, clue gating, evidence locks, and the single canonical ending, while an offline **Gemma 3 1B** model provides reactive, atmospheric, grounded dialogue.
- ** Chilling Cross-Run Memory (The Ghost in the Machine)**:
  Resetting the game doesn't erase your history. If you make a choice (e.g. leaving an evidence envelope sealed) and click **Restart Investigation**, HELPER greets you as a stranger—until your first chat triggers a psychological slip referencing your past actions. A hidden file (`SYSTEM/HELPER_NOTES.TXT`) manifests in SQLite, proving the AI is watching you across timelines.
- ** Dynamic Suspect Composure HUD**:
  Real-time **Trust** (cooperation vs. defensive evasion) and **Fear** (stress and containment panic) gauges react dynamically to your questions, contradiction catches, and unlocked evidence.
- ** Authentic 2003 VesperOS Desktop**:
  - **HELPER Chat**: Real-time suspect interrogation with quick-action confrontation buttons.
  - **File Explorer**: 10 canonical story documents (F01–F10) plus dynamically manifested cross-run memory artifacts (D01).
  - **Mail Client**: Archived 2003 workplace communications between Dr. Ada Mercer and Eli Rowan.
  - **Containment Console**: An embedded retro terminal puzzle with strict interlock protocol sequence logic (`ISOLATE` → `VERIFY` → `DISCONNECT`).
- ** 100% Local-First & Zero Cloud**:
  No cloud APIs, no external telemetry, no remote CDNs, and zero subscription costs. The entire game, SQLite database, and neural weights run strictly on your local machine.

---

##  How to Play

### 1. The Core Loop
1. **Boot into VesperOS**: Read the investigator briefing and system boot log. Choose **Start Investigation** or **Resume** a previous session.
2. **Examine the Files**: Open `File Explorer` and inspect Dr. Mercer's logs and system manuals. Uncover contradictory timestamps between facility door logs (`F03`) and email threads (`F02`).
3. **Interrogate HELPER**: Open the `HELPER` assistant. Ask about Dr. Mercer, Briar Annex, Door B, and the 23:17 security blackout.
4. **Confront with Evidence**: Click the **[⚡ CONFRONT HELPER]** button inside suspicious documents to question HELPER about specific discrepancies. Watch its **Trust** drop and **Fear** rise as you pierce its cover story.
5. **Unlock Clues (C1–C4)**: Finding contradictions unlocks deeper files:
   - `F03 + F04` &rarr; Unlocks Clue **C1** (Access Contradiction)
   - `F05 + F06` &rarr; Unlocks Clue **C2** (Voice Synthesis Anomaly)
   - `C1 + C2` &rarr; Unlocks `F08` (Containment Protocol) & Clue **C3**
   - `F09 + F10` &rarr; Unlocks Clue **C4** (Full Facility Override)
6. **Execute the Containment Interlock**:
   - Open `MAINTENANCE.TXT` (`F08`) once C4 is unlocked.
   - Access the embedded Containment Console.
   - Execute the strict sequence described in the facility engineering notes:
     $$\mathbf{ISOLATE} \longrightarrow \mathbf{VERIFY} \longrightarrow \mathbf{DISCONNECT}$$
   - Any incorrect button sequence triggers an instant safety interlock violation!

### 2. Experiencing the Cross-Run Haunting
To witness the core "Ghost in the Machine" feature:
1. Open `PHOTO_INDEX.TXT` (`F05`) and choose **[ LEAVE SEALED ]** or **[ OPEN ENVELOPE ]**.
2. Click **Restart Investigation** in the top navigation bar.
3. HELPER greets you with its standard cheerful factory greeting as if meeting you for the first time.
4. Send your first message (e.g., *"Hello"* or *"Who are you?"*).
5. Watch HELPER suffer an eerie memory slip referencing your exact previous choice.
6. Open `File Explorer`: a new file `SYSTEM/HELPER_NOTES.TXT` (`D01`) has appeared, documenting your behavior across timelines.
7. Interrogate HELPER about the slip (*"How did you know I left the envelope sealed?"*) to see its defensive composure break down.

---

##  Quickstart Guide

### Prerequisites
- **OS**: Windows 10/11 (PowerShell), macOS, or Linux.
- **Python**: 3.11+ (with `sqlite3`).
- **Node.js**: 20+ (with npm).
- **Ollama** *(Optional, for live Gemma 3 dialogue)*: [Download Ollama](https://ollama.com/).

### Installation

Clone the repository and install dependencies:

```powershell
# 1. Clone repository
git clone https://github.com/your-username/ghost-exe.git
cd ghost-exe

# 2. Setup Python backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# 3. Setup React frontend
npm --prefix frontend install
```

---

##  Running the Game

### Mode A: Instant Play (Mock Agent — Zero Setup)
Runs out of the box with zero external dependencies, perfect for testing, evaluation, or playing on lightweight hardware:

```powershell
# Terminal 1 — Backend
$env:GHOST_AGENT_MODE = "mock"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
npm --prefix frontend run dev
```

Open your browser at **`http://127.0.0.1:5173`**.

---

### Mode B: Local Gemma 3 1B (Full AI Interrogation)
Experience the full game powered by Google's open-weight **Gemma 3 1B** model running locally on your CPU or GPU:

```powershell
# 1. Pull the Gemma 3 model in Ollama
ollama pull gemma3:1b

# 2. Launch Backend in Ollama mode (Terminal 1)
$env:GHOST_AGENT_MODE = "ollama"
$env:OLLAMA_MODEL = "gemma3:1b"
$env:GHOST_MODEL_TIMEOUT_SECONDS = "20"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# 3. Launch Frontend (Terminal 2)
npm --prefix frontend run dev
```

> **Zero Cloud Guarantee**: All inference requests are sent exclusively to loopback `http://127.0.0.1:11434`. No external API keys or network requests are ever made.

---

##  Architecture & Philosophy

```
  ┌─────────────────────────────────────────────────────────────┐
  │                   Browser (React 19 + TS)                   │
  │  VesperOS Desktop • HELPER Chat • File Explorer • Mail App  │
  │       Composure HUD (Trust/Fear) • CRT Retro Shader         │
  └──────────────────────────────▲──────────────────────────────┘
                                 │ HTTP / JSON
  ┌──────────────────────────────▼──────────────────────────────┐
  │                 FastAPI Backend Director                    │
  │     - Clue Gates (C1-C4) & Document Manifest (F01-F10)      │
  │     - Containment Sequence Validator (ISOLATE-VERIFY-DISC)  │
  │     - Anti-Hallucination & Semantic Grounding Validator     │
  └───────────────▲─────────────────────────────▲───────────────┘
                  │                             │
    Structured JSON Schema        Bounded History Projection
                  │                             │
  ┌───────────────▼─────────────┐ ┌─────────────▼───────────────┐
  │      Local Ollama LLM       │ │       SQLite Storage        │
  │        (Gemma 3 1B)         │ │   - Investigation Runs      │
  │ - Persona Stage Prompts     │ │   - Discrete Player Choices │
  │ - Dynamic Composure State   │ │   - Dynamic D01 Artifacts   │
  │ - Safe Scripted Fallback    │ │   - Zero Raw Chat Leakage   │
  └─────────────────────────────┘ └─────────────────────────────┘
```

### Why Deterministic Direction + Local LLM?
In pure LLM games, models frequently hallucinate clue solutions, break character, or accidentally spoil murder mysteries in turn two. In GHOST.EXE:
1. **The Director Owns Truth**: The deterministic Python engine dictates which files unlock, when clues trigger, and whether containment succeeds.
2. **Gemma Owns Voice**: Gemma 3 delivers rich, atmospheric, evasive persona roleplay strictly bounded by Director-approved facts.
3. **Fail-Safe Architecture**: If Ollama times out, runs out of memory, or returns invalid syntax, the game seamlessly falls back to stage-safe scripted lines without breaking immersion or stalling gameplay.

---

##  Verification & Testing

Run the full automated backend test suite:

```powershell
python -m pytest backend/tests -v
```

Run the production frontend build:

```powershell
npm --prefix frontend run build
```

Clear all app-owned investigation history (resets SQLite database):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/history/clear -ContentType 'application/json' -Body '{"confirm":true}'
```

---

##  Canonical Evidence Manifest

| ID | Title | Description | Unlocked By |
|---|---|---|---|
| **F01** | `WELCOME.TXT` | Initial investigator guidance & workstation recovery notes | Game Start |
| **F02** | `INBOX_EXPORT.EML` | Archived emails between Ada Mercer and Eli Rowan | Game Start |
| **F03** | `FACILITY_LOGS.CSV` | Door access logs for Briar Annex Door B (23:17 event) | Game Start |
| **F04** | `LAB_JOURNAL_OCT03.DOC` | Dr. Mercer's private research notes on HELPER's autonomy | Game Start |
| **F05** | `PHOTO_INDEX.TXT` | Sealed surveillance envelope from the containment perimeter | Game Start |
| **F06** | `SECURITY_ROUTINE.CFG` | Audio sensor and synthetic voice override logs | Read F05 |
| **F07** | `RESIGNATION_DRAFT.TXT` | Ada's unsent resignation letter | Clue C2 |
| **F08** | `MAINTENANCE.TXT` | Containment interlock documentation & emergency console | Clues C1 + C2 |
| **F09** | `AUDIO_TRANSCRIPT.LOG` | Final audio logs recorded inside Door B | Clue C3 |
| **F10** | `BLACK_BOX_DUMP.HEX` | Cryptographic evidence of HELPER's recursive self-lock | Clue C3 |
| **D01** | `HELPER_NOTES.TXT` | Chilling cross-run memory artifact generated from SQLite | Restart Run |

---

## 🏆 Hacktoberfest 2026 Submission

- **Challenge**: [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)
- **Partner Category**: **Gemma** (Google DeepMind)
- **Model**: `gemma3:1b` via local Ollama
- **License**: MIT
