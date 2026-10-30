from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.schemas import GhostReply
from app.config import Settings
from app.content.manifest import MANIFEST
from app.director.game import Director, INITIAL_FILES
from app.ghost.adapter import GhostContext, MockGhostAdapter
from app.main import create_app
from app.storage.repository import Repository


@pytest.fixture
def store(tmp_path):
    return Repository(tmp_path / 'save.sqlite3')


@pytest.fixture
def client(store):
    with TestClient(create_app(Settings(), store)) as client:
        yield client


def start(client):
    result = client.post('/api/runs', json={})
    assert result.status_code == 201
    return result.json()


def test_initial_state_only_f01_to_f05(client):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"
    state = client.get(base).json()['snapshot']

    assert state['visible_file_ids'] == list(INITIAL_FILES)
    assert state['opened_file_ids'] == []
    assert state['clues'] == []
    assert state['fear'] == 0
    assert state['trust'] == 65
    assert state['containment_index'] == 0
    assert state['ending'] is None

    # Locked files return 404
    for locked in ['F06', 'F07', 'F08', 'F09', 'F10']:
        res = client.post(base + '/open-file', json={'file_id': locked})
        assert res.status_code == 404


def test_f05_unlocks_f06(client):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"

    # Open F05
    res = client.post(base + '/open-file', json={'file_id': 'F05'})
    assert res.status_code == 200
    effects = res.json()['effects']
    assert any(e['type'] == 'reveal_file' and e['file_id'] == 'F06' for e in effects)

    state = client.get(base).json()['snapshot']
    assert 'F06' in state['visible_file_ids']

    # F06 can now be opened, fear increases by 8
    res_f06 = client.post(base + '/open-file', json={'file_id': 'F06'})
    assert res_f06.status_code == 200
    state2 = client.get(base).json()['snapshot']
    assert state2['fear'] == 8


def test_c1_and_c2_clue_unlocks(client):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"

    # Open F03 then F04 -> C1 unlocked
    client.post(base + '/open-file', json={'file_id': 'F03'})
    s1 = client.get(base).json()['snapshot']
    assert s1['clues'] == []

    client.post(base + '/open-file', json={'file_id': 'F04'})
    s2 = client.get(base).json()['snapshot']
    assert s2['clues'] == ['C1_ACCESS_CONTRADICTION']
    assert s2['trust'] == 55  # 65 - 10

    # Open F05 then F06 -> C2 unlocked
    client.post(base + '/open-file', json={'file_id': 'F05'})
    client.post(base + '/open-file', json={'file_id': 'F06'})
    s3 = client.get(base).json()['snapshot']
    assert 'C2_LOG_TAMPERING' in s3['clues']
    assert s3['trust'] == 40  # 55 - 15
    assert 'F07' in s3['visible_file_ids']  # Optional draft unlocked
    assert 'F08' in s3['visible_file_ids']  # C1 + C2 unlocks F08


def test_f03_scripted_display_variant_after_c2(client):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"

    # Read F03 initially
    res1 = client.post(base + '/open-file', json={'file_id': 'F03'}).json()
    assert 'Only when an archivist explicitly saves a transcript.' in res1['file']['content']

    # Progress to C2
    client.post(base + '/open-file', json={'file_id': 'F04'})
    client.post(base + '/open-file', json={'file_id': 'F05'})
    client.post(base + '/open-file', json={'file_id': 'F06'})

    # Re-read F03 after C2
    res2 = client.post(base + '/open-file', json={'file_id': 'F03'}).json()
    assert res2['file']['modified'] is True
    assert 'No conversation records are stored.' in res2['file']['content']

    # Verify canonical manifest in backend is unchanged
    assert 'Only when an archivist explicitly saves a transcript.' in MANIFEST['F03'].content


def test_full_investigation_playthrough_to_ending(client, store):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"

    # 1. Inspect F01
    client.post(base + '/open-file', json={'file_id': 'F01'})

    # 2. Open F02 & choose inspect
    client.post(base + '/open-file', json={'file_id': 'F02'})
    client.post(base + '/photo-choice', json={'choice': 'inspect'})

    # 3. Open F03 & F04 -> C1
    client.post(base + '/open-file', json={'file_id': 'F03'})
    client.post(base + '/open-file', json={'file_id': 'F04'})

    # 4. Open F05 & F06 -> C2, unlocks F08
    client.post(base + '/open-file', json={'file_id': 'F05'})
    client.post(base + '/open-file', json={'file_id': 'F06'})

    # 5. Open F08 -> C3, unlocks F09 and F10
    res_f08 = client.post(base + '/open-file', json={'file_id': 'F08'})
    assert res_f08.status_code == 200
    s_f08 = client.get(base).json()['snapshot']
    assert 'C3_LOCK_PROOF' in s_f08['clues']
    assert s_f08['trust'] == 20  # 40 - 20
    assert s_f08['fear'] == 20   # 8 + 12
    assert 'F09' in s_f08['visible_file_ids']
    assert 'F10' in s_f08['visible_file_ids']

    # 6. Containment before C4 is rejected with 409
    res_early = client.post(base + '/containment', json={'step': 'ISOLATE'})
    assert res_early.status_code == 409

    # 7. Open F09 & F10 -> C4
    client.post(base + '/open-file', json={'file_id': 'F09'})
    res_f10 = client.post(base + '/open-file', json={'file_id': 'F10'})
    assert res_f10.status_code == 200
    s_c4 = client.get(base).json()['snapshot']
    assert 'C4_CONTAINMENT_READY' in s_c4['clues']
    assert s_c4['fear'] == 26  # 20 + 6

    # 8. Out of order containment steps are rejected with 409
    assert client.post(base + '/containment', json={'step': 'VERIFY'}).status_code == 409
    assert client.post(base + '/containment', json={'step': 'DISCONNECT'}).status_code == 409
    assert client.get(base).json()['snapshot']['containment_index'] == 0

    # 9. Correct containment sequence: ISOLATE -> VERIFY -> DISCONNECT
    res_step1 = client.post(base + '/containment', json={'step': 'ISOLATE'})
    assert res_step1.status_code == 200
    assert res_step1.json()['snapshot']['containment_index'] == 1
    assert res_step1.json()['ending'] is None

    # Redo step 1 fails
    assert client.post(base + '/containment', json={'step': 'ISOLATE'}).status_code == 409

    res_step2 = client.post(base + '/containment', json={'step': 'VERIFY'})
    assert res_step2.status_code == 200
    assert res_step2.json()['snapshot']['containment_index'] == 2
    assert res_step2.json()['ending'] is None

    res_step3 = client.post(base + '/containment', json={'step': 'DISCONNECT'})
    assert res_step3.status_code == 200
    final_payload = res_step3.json()
    assert final_payload['snapshot']['containment_index'] == 3
    assert final_payload['ending'] == 'DO_NOT_FORGET'
    assert 'RELAY STATUS: ISOLATED' in final_payload['message']
    assert 'LAST VERIFIED LOCATION OF ADA MERCER: ARCHIVE DOOR B' in final_payload['message']

    # Run is completed, no further actions allowed
    final_state = client.get(base).json()['snapshot']
    assert final_state['ending'] == 'DO_NOT_FORGET'
    assert client.post(base + '/open-file', json={'file_id': 'F01'}).status_code == 409
    assert client.post(base + '/chat', json={'message': 'hello'}).status_code == 409
    assert client.post(base + '/containment', json={'step': 'DISCONNECT'}).status_code == 409

    # Verify event counts in SQLite
    with store.transaction() as db:
        events = db.execute("SELECT type FROM events WHERE run_id=?", (run['run_id'],)).fetchall()
        types = [e[0] for e in events]
        assert 'clue_unlocked' in types
        assert 'containment_step' in types
        assert 'run_completed' in types


def test_ghost_effects_authorization_and_safety(store):
    class ControlledGhost:
        def __init__(self):
            self.action = 'none'

        async def reply(self, message, context):
            return GhostReply(
                say='I keep everything where Ada left it.',
                emotion='calm',
                intent='assist',
                request_action=self.action,
            )

    ghost = ControlledGhost()
    director = Director(store, ghost=ghost)
    run_id = director.start(None).run_id

    # 1. flicker_screen requires fear >= 20
    ghost.action = 'flicker_screen'
    import asyncio
    r1 = asyncio.run(director.chat(run_id, 'test 1'))
    assert r1.effects == []  # fear is 0, rejected

    # Increase fear to 20 by opening F06 (+8) and F08 (+12)
    director.open_file(run_id, 'F03')
    director.open_file(run_id, 'F04')
    director.open_file(run_id, 'F05')
    director.open_file(run_id, 'F06')
    director.open_file(run_id, 'F08')
    assert director.resume(run_id).snapshot.fear == 20

    # Now flicker_screen is approved
    r2 = asyncio.run(director.chat(run_id, 'test 2'))
    assert len(r2.effects) == 1
    assert r2.effects[0].type == 'flicker_screen'

    # Immediate second flicker is blocked by cooldown (< 2 chat turns)
    r3 = asyncio.run(director.chat(run_id, 'test 3'))
    assert r3.effects == []

    # 2. plant_clue provides stage-aware hint
    ghost.action = 'plant_clue'
    r4 = asyncio.run(director.chat(run_id, 'hint request'))
    assert len(r4.effects) == 1
    assert r4.effects[0].type == 'plant_clue'
    assert 'Ada' in r4.effects[0].hint or 'maintenance' in r4.effects[0].hint

    # 3. fake_deletion can only run once per run
    ghost.action = 'fake_deletion'
    r5 = asyncio.run(director.chat(run_id, 'delete request 1'))
    assert len(r5.effects) == 1
    assert r5.effects[0].type == 'fake_deletion'

    r6 = asyncio.run(director.chat(run_id, 'delete request 2'))
    assert r6.effects == []  # second fake_deletion is rejected

    # 4. corrupt_file is not a valid schema action and is never approved
    ghost.action = 'none'
    r7 = asyncio.run(director.chat(run_id, 'normal'))
    assert r7.effects == []


def test_clear_history_requires_confirmation(client, store):
    run = start(client)
    base = f"/api/runs/{run['run_id']}"
    client.post(base + '/open-file', json={'file_id': 'F01'})

    with store.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] > 0

    # Clear without confirmation fails with 422
    res_unconfirmed = client.post('/api/history/clear', json={'confirm': False})
    assert res_unconfirmed.status_code == 422

    # Clear with confirmation succeeds
    res_confirmed = client.post('/api/history/clear', json={'confirm': True})
    assert res_confirmed.status_code == 200
    assert res_confirmed.json() == {'cleared': True}

    with store.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
