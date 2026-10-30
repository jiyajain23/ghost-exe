"""Director Tests: Game State Machine, Clue Gates, Document Unlocking, and Persistence Invariants."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from uuid import uuid4
import pytest

from app.api.schemas import Clue, FileId
from app.content.manifest import MANIFEST
from app.director.game import Director, GameError, INITIAL_FILES, F03_MODIFIED_CONTENT
from app.ghost.adapter import MockGhostAdapter
from app.storage.repository import Repository


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os_close = getattr(asyncio, "_os_close", None)
    import os
    os.close(fd)
    repo = Repository(Path(path))
    yield repo
    try:
        os.remove(path)
    except OSError:
        pass


# ===========================================================================
# 1. Scaffolding & Initial State Invariants
# ===========================================================================

def test_initial_state_and_manifest(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    res = director.start(None)
    run = res.snapshot

    assert run.status == "active"
    assert run.run_index == 1
    assert run.clues == []
    assert set(run.visible_file_ids) == set(INITIAL_FILES)
    assert run.opened_file_ids == []
    assert run.fear == 0
    assert run.trust == 65
    assert run.containment_index == 0
    assert run.ending is None
    assert not run.memory_revealed


def test_seed_matches_all_canonical_documents():
    story_path = Path(__file__).resolve().parents[2] / 'STORY.md'
    story = story_path.read_text(encoding='utf-8')
    assert set(MANIFEST) == {f'F{i:02}' for i in range(1, 11)}
    for file_id, document in MANIFEST.items():
        section = story.split('### ' + file_id + ' — ', 1)[1]
        original = re.search(r'```(?:text|csv)\n(.*?)\n```', section, re.S).group(1)
        assert document.content == original
        assert f'| {file_id} | `{document.path}` |' in story


# ===========================================================================
# 2. Clue Progression Gates & Visibility Predicates
# ===========================================================================

def test_clue_progression_gates(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    # 1. Opening F01 does not unlock new clues
    res1 = director.open_file(run_id, "F01")
    assert res1.snapshot.clues == []

    # 2. Opening F05 unlocks F06
    res5 = director.open_file(run_id, "F05")
    assert "F06" in res5.snapshot.visible_file_ids

    # 3. Opening F03 + F04 triggers C1 (Access Contradiction)
    director.open_file(run_id, "F03")
    res4 = director.open_file(run_id, "F04")
    assert "C1_ACCESS_CONTRADICTION" in res4.snapshot.clues
    assert res4.snapshot.trust == 55  # 65 - 10

    # 4. Opening F06 (with F05 already opened) triggers C2 (Log Tampering)
    res6 = director.open_file(run_id, "F06")
    assert "C2_LOG_TAMPERING" in res6.snapshot.clues
    assert res6.snapshot.trust == 40   # 55 - 15
    assert res6.snapshot.fear == 8     # F06 opened (+8)
    assert "F07" in res6.snapshot.visible_file_ids
    assert "F08" in res6.snapshot.visible_file_ids

    # 5. Opening F08 triggers C3 (Lock Proof) and unlocks F09, F10
    res8 = director.open_file(run_id, "F08")
    assert "C3_LOCK_PROOF" in res8.snapshot.clues
    assert res8.snapshot.trust == 20   # 40 - 20
    assert res8.snapshot.fear == 20    # 8 + 12
    assert "F09" in res8.snapshot.visible_file_ids
    assert "F10" in res8.snapshot.visible_file_ids

    # 6. Opening F09 + F10 triggers C4 (Containment Ready)
    director.open_file(run_id, "F09")
    res10 = director.open_file(run_id, "F10")
    assert "C4_CONTAINMENT_READY" in res10.snapshot.clues
    assert res10.snapshot.fear == 26   # 20 + 6


def test_f03_scripted_variant_after_c2(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    # Read F03 initially
    res1 = director.open_file(run_id, "F03")
    assert "Only when an archivist explicitly saves a transcript." in res1.file.content
    assert res1.file.modified is False

    # Progress to C2: F04, F05, F06
    director.open_file(run_id, "F04")
    director.open_file(run_id, "F05")
    director.open_file(run_id, "F06")

    # Re-read F03 after C2
    res2 = director.open_file(run_id, "F03")
    assert res2.file.modified is True
    assert "No conversation records are stored." in res2.file.content
    assert res2.file.content == F03_MODIFIED_CONTENT
    # Canonical manifest in memory remains original
    assert "Only when an archivist explicitly saves a transcript." in MANIFEST["F03"].content


def test_hidden_files_return_404(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    for locked_id in ["F06", "F07", "F08", "F09", "F10", "D01"]:
        with pytest.raises(GameError) as exc_info:
            director.open_file(run_id, locked_id)
        assert exc_info.value.status == 404


def test_open_file_idempotency(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    for file_id in INITIAL_FILES:
        res1 = director.open_file(run_id, file_id)
        res2 = director.open_file(run_id, file_id)
        assert res1.file.content == res2.file.content

    with temp_db.transaction() as db:
        event_count = db.execute("SELECT COUNT(*) FROM events WHERE type='file_opened'").fetchone()[0]
        assert event_count == 5


# ===========================================================================
# 3. Atomicity, Transactions & Concurrency
# ===========================================================================

def test_parallel_first_choices_are_atomic(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    director.open_file(run_id, "F02")

    def choose(choice):
        try:
            return director.photo(run_id, choice).snapshot.photo_choice
        except GameError as error:
            return error.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(choose, ["inspect", "leave_sealed"]))

    assert 409 in results
    assert ("inspect" in results) or ("leave_sealed" in results)

    with temp_db.transaction() as db:
        choice_count = db.execute("SELECT COUNT(*) FROM events WHERE type='photo_choice'").fetchone()[0]
        assert choice_count == 1


def test_storage_transaction_rollback(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    with pytest.raises(sqlite3.DatabaseError):
        with temp_db.transaction() as db:
            temp_db.append(db, str(run_id), 'file_opened', 'F01')
            raise sqlite3.DatabaseError('simulate write failure')

    assert director.resume(run_id).snapshot.opened_file_ids == []


def test_inactive_run_cannot_mutate(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    with temp_db.transaction() as db:
        db.execute("UPDATE runs SET status='abandoned' WHERE id=?", (str(run_id),))

    with pytest.raises(GameError) as exc_info:
        director.open_file(run_id, "F01")
    assert exc_info.value.status == 409

    with pytest.raises(GameError) as exc_info:
        director.photo(run_id, "inspect")
    assert exc_info.value.status == 409

    with pytest.raises(GameError) as exc_info:
        asyncio.run(director.chat(run_id, "hello"))
    assert exc_info.value.status == 409


# ===========================================================================
# 4. Evidence Authorization Guards
# ===========================================================================

def test_unopened_evidence_raises_409(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    # F03 is visible but unopened
    with pytest.raises(GameError) as exc_info:
        asyncio.run(director.chat(run_id, "hello", evidence_id="F03"))
    assert exc_info.value.status == 409


def test_hidden_evidence_raises_409(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    with pytest.raises(GameError) as exc_info:
        asyncio.run(director.chat(run_id, "hello", evidence_id="F08"))
    assert exc_info.value.status == 409


def test_opened_evidence_is_accepted(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    director.open_file(run_id, "F03")

    result = asyncio.run(director.chat(run_id, "What does the FAQ say?", evidence_id="F03"))
    assert result.reply


def test_evidence_from_other_run_is_rejected(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run1_id = director.start(None).snapshot.run_id
    director.open_file(run1_id, "F03")

    # Run 2 starts; F03 is not opened in Run 2
    run2_id = director.start(run1_id).snapshot.run_id
    with pytest.raises(GameError) as exc_info:
        asyncio.run(director.chat(run2_id, "hello", evidence_id="F03"))
    assert exc_info.value.status == 409

