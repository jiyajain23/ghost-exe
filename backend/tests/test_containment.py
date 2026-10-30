"""Containment Tests: Interlock Puzzle Sequence, C4 Prerequisite, and Ending Presentation."""
from pathlib import Path
import tempfile
import pytest

from app.director.game import Director, GameError, ENDING_FINAL_MESSAGE
from app.ghost.adapter import MockGhostAdapter
from app.storage.repository import Repository


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    import os
    os.close(fd)
    repo = Repository(Path(path))
    yield repo
    try:
        os.remove(path)
    except OSError:
        pass


def advance_to_c4(director: Director, run_id) -> None:
    """Helper to open all necessary documents to unlock Clue 4."""
    for doc in ["F01", "F02", "F03", "F04", "F05", "F06", "F08", "F09", "F10"]:
        director.open_file(run_id, doc)


# ===========================================================================
# 1. Prerequisite & Order Enforcement
# ===========================================================================

def test_containment_locked_before_c4(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id

    # With only initial files open, containment must be locked
    director.open_file(run_id, "F01")
    director.open_file(run_id, "F02")

    with pytest.raises(GameError) as exc_info:
        director.containment(run_id, "ISOLATE")
    assert exc_info.value.status == 409
    assert "complete evidence chain" in exc_info.value.message


def test_containment_sequence_order_enforcement(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    advance_to_c4(director, run_id)

    state = director.resume(run_id).snapshot
    assert "C4_CONTAINMENT_READY" in state.clues

    # --- STEP 1 CHECKS ---
    # Out of order: VERIFY first
    with pytest.raises(GameError) as exc_v:
        director.containment(run_id, "VERIFY")
    assert exc_v.value.status == 409
    assert "Expected ISOLATE as step 1" in exc_v.value.message

    # Out of order: DISCONNECT first
    with pytest.raises(GameError) as exc_d:
        director.containment(run_id, "DISCONNECT")
    assert exc_d.value.status == 409
    assert "Expected ISOLATE as step 1" in exc_d.value.message

    # Correct Step 1: ISOLATE
    s1 = director.containment(run_id, "ISOLATE").snapshot
    assert s1.containment_index == 1
    assert s1.status == "active"
    assert s1.ending is None

    # --- STEP 2 CHECKS ---
    # Out of order: DISCONNECT second
    with pytest.raises(GameError) as exc_d2:
        director.containment(run_id, "DISCONNECT")
    assert exc_d2.value.status == 409
    assert "Expected VERIFY as step 2" in exc_d2.value.message

    # Correct Step 2: VERIFY
    s2 = director.containment(run_id, "VERIFY").snapshot
    assert s2.containment_index == 2
    assert s2.status == "active"
    assert s2.ending is None

    # --- STEP 3 CHECKS ---
    # Out of order: ISOLATE again
    with pytest.raises(GameError) as exc_i2:
        director.containment(run_id, "ISOLATE")
    assert exc_i2.value.status == 409
    assert "Expected DISCONNECT as step 3" in exc_i2.value.message

    # Correct Step 3: DISCONNECT completes containment!
    s3_res = director.containment(run_id, "DISCONNECT")
    s3 = s3_res.snapshot
    assert s3.containment_index == 3
    assert s3.status == "completed"
    assert s3.ending == "DO_NOT_FORGET"
    assert s3_res.ending == "DO_NOT_FORGET"


def test_containment_is_terminal(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    advance_to_c4(director, run_id)

    director.containment(run_id, "ISOLATE")
    director.containment(run_id, "VERIFY")
    director.containment(run_id, "DISCONNECT")

    # Any step after completion must be rejected
    with pytest.raises(GameError) as exc_info:
        director.containment(run_id, "DISCONNECT")
    assert exc_info.value.status == 409
    assert "no longer active" in exc_info.value.message.lower()


# ===========================================================================
# 2. Ending Presentation & Restart Survival
# ===========================================================================

def test_ending_presentation_survives_repository_recreation(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    advance_to_c4(director, run_id)

    director.containment(run_id, "ISOLATE")
    director.containment(run_id, "VERIFY")
    res_final = director.containment(run_id, "DISCONNECT")

    pres = res_final.snapshot.ending_presentation
    assert pres is not None
    assert pres.title == "DO NOT FORGET"
    assert pres.final_line == "If you close the archive, who will remember she was here?"
    assert "RELAY STATUS: ISOLATED" in pres.narrative
    assert "OUTCOME: UNKNOWN" in pres.narrative

    # Reload from disk using fresh Director instance
    restored_director = Director(Repository(temp_db.database))
    restored_state = restored_director.resume(run_id).snapshot
    assert restored_state.status == "completed"
    assert restored_state.ending == "DO_NOT_FORGET"
    assert restored_state.ending_presentation.title == pres.title
    assert restored_state.ending_presentation.final_line == pres.final_line


def test_three_repeated_investigations_and_containment(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    current = director.start(None)

    for i in range(3):
        run_id = current.snapshot.run_id
        advance_to_c4(director, run_id)
        director.containment(run_id, "ISOLATE")
        director.containment(run_id, "VERIFY")
        done = director.containment(run_id, "DISCONNECT")
        assert done.snapshot.status == "completed"

        if i < 2:
            current = director.start(run_id)
            assert current.snapshot.run_index == i + 2
