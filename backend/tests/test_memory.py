"""Memory Tests: Cross-Run SQLite Persistence, Bounded Dossier, and Post-Reveal Interrogation."""
import asyncio
import json
from pathlib import Path
import tempfile
import pytest

from app.director.game import Director, GameError
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


class NeverCalledGhost:
    """Memory reveal MUST be Director-authored and never call the model."""
    async def reply(self, *args, **kwargs):
        raise AssertionError("Memory slip must bypass model inference entirely")


# ===========================================================================
# 1. Cross-Run Memory Slip & D01 Manifestation
# ===========================================================================

@pytest.mark.parametrize('choice, expected_slip, expected_d01', [
    ('inspect', 'inspected', 'INSPECT NEGATIVE'),
    ('leave_sealed', 'left the negative sealed', 'LEAVE SEALED'),
])
def test_cross_run_memory_slip_and_d01(temp_db, choice, expected_slip, expected_d01):
    director = Director(temp_db, NeverCalledGhost())

    # --- RUN 1 ---
    run1 = director.start(None)
    run1_id = run1.snapshot.run_id
    director.open_file(run1_id, 'F02')
    director.photo(run1_id, choice)

    # --- RUN 2 ---
    run2 = director.start(run1_id)
    run2_id = run2.snapshot.run_id
    assert run2_id != run1_id
    assert director.resume(run1_id).snapshot.status == 'abandoned'
    assert "don't believe we've met" in run2.greeting
    assert 'D01' not in run2.snapshot.visible_file_ids

    # D01 cannot be opened before reveal
    with pytest.raises(GameError):
        director.open_file(run2_id, 'D01')

    # First chat message triggers the deterministic memory slip
    result = asyncio.run(director.chat(run2_id, 'What happened to Ada?'))
    assert expected_slip in result.reply
    assert 'D01' in result.snapshot.visible_file_ids

    # D01 file content verification
    d01_doc = director.open_file(run2_id, 'D01').file.content
    assert expected_d01 in d01_doc
    assert 'Recovered session: 001' in d01_doc
    assert 'VISITOR 002' in d01_doc


# ===========================================================================
# 2. Conversational Memory Follow-ups
# ===========================================================================

def test_post_reveal_conversational_follow_ups(temp_db):
    director = Director(temp_db, MockGhostAdapter())

    # Run 1: leave sealed
    run1_id = director.start(None).snapshot.run_id
    director.open_file(run1_id, 'F02')
    director.photo(run1_id, 'leave_sealed')

    # Run 2: start and reveal memory
    run2_id = director.start(run1_id).snapshot.run_id
    slip_res = asyncio.run(director.chat(run2_id, 'Hello'))
    assert 'sealed' in slip_res.reply.lower()

    async def verify_follow_ups():
        # "You said we hadn't met before"
        res_stranger = await director.chat(run2_id, "You said we hadn't met before.")
        assert "administrative continuity" in res_stranger.reply

        # "How did you know I left the envelope sealed?"
        res_choice = await director.chat(run2_id, "How did you know I left the envelope sealed?")
        assert "uncommitted inspection states" in res_choice.reply

        # "What else do you remember?"
        res_more = await director.chat(run2_id, "What else do you remember?")
        assert "Nothing else is recorded" in res_more.reply

        # "Why did you write those HELPER_NOTES?"
        res_notes = await director.chat(run2_id, "Why did you write those HELPER_NOTES?")
        assert "internal indexing log" in res_notes.reply

    asyncio.run(verify_follow_ups())


# ===========================================================================
# 3. Alternate Memory Sources & Fresh Investigation
# ===========================================================================

@pytest.mark.parametrize('kind', ['none', 'file', 'question'])
def test_alternate_sources_and_no_history(temp_db, kind):
    director = Director(temp_db, MockGhostAdapter())
    run1_id = director.start(None).snapshot.run_id

    if kind == 'file':
        director.open_file(run1_id, 'F05')
    elif kind == 'question':
        asyncio.run(director.chat(run1_id, 'What happened to Ada?'))

    run2_id = director.start(run1_id).snapshot.run_id
    chat_res = asyncio.run(director.chat(run2_id, 'hello'))

    if kind == 'none':
        # Without prior meaningful actions, memory is NOT revealed
        assert chat_res.snapshot.memory_revealed is False
        assert 'D01' not in chat_res.snapshot.visible_file_ids
    elif kind == 'file':
        assert chat_res.snapshot.memory_revealed is True
        assert 'ACCESS_1031.CSV' in chat_res.reply
    elif kind == 'question':
        assert chat_res.snapshot.memory_revealed is True
        assert 'ada' in chat_res.reply.lower()


# ===========================================================================
# 4. Privacy: Zero Raw Dialogue Storage & History Clearance
# ===========================================================================

def test_zero_raw_chat_dialogue_persisted(temp_db):
    director = Director(temp_db, MockGhostAdapter())
    run_id = director.start(None).snapshot.run_id
    secret_marker = "sensitive-investigator-passphrase-9988"

    asyncio.run(director.chat(run_id, f"What happened to Ada? {secret_marker}"))

    with temp_db.transaction() as db:
        events = temp_db.events(db, str(run_id))
        category_events = [e for e in events if e['type'] == 'chat_category']
        assert len(category_events) == 1
        # Payload contains ONLY the discrete category enum
        assert json.loads(category_events[0]['payload_json']) == {'category': 'ada'}

    # Raw database bytes must NEVER contain the secret text
    raw_db_bytes = temp_db.database.read_bytes()
    assert secret_marker.encode() not in raw_db_bytes


def test_clear_history_purges_all_runs(temp_db):
    director = Director(temp_db, MockGhostAdapter())

    # Create run 1 with photo choice
    r1_id = director.start(None).snapshot.run_id
    director.open_file(r1_id, 'F02')
    director.photo(r1_id, 'inspect')

    # Clear history
    clear_res = director.clear_history(True)
    assert clear_res.cleared is True

    # Subsequent run starts fresh as Run 1 with no prior dossier
    clean_run = director.start(None).snapshot
    assert clean_run.run_index == 1
    assert clean_run.has_qualified_prior_run is False
    assert 'D01' not in clean_run.visible_file_ids
