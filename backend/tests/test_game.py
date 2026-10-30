"""End-to-End Game Integration & HTTP Workflow Tests."""
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.api.schemas import RunState
from app.config import Settings
from app.director.game import Director
from app.ghost.adapter import MockGhostAdapter
from app.main import create_app
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


@pytest.fixture
def client(temp_db):
    app = create_app(Settings(), temp_db)
    with TestClient(app) as test_client:
        yield test_client


# ===========================================================================
# 1. Server Scaffolding, Health & Security Boundaries
# ===========================================================================

def test_health_and_cors(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json() == {'status': 'ok', 'agent_mode': 'mock', 'ollama_reachable': None}

    # CORS check
    res_cors = client.get('/api/health', headers={'Origin': 'http://localhost:5173'})
    assert res_cors.headers.get('access-control-allow-origin') == 'http://localhost:5173'

    res_disallowed = client.get('/api/health', headers={'Origin': 'https://evil.attacker.com'})
    assert res_disallowed.headers.get('access-control-allow-origin') is None


@pytest.mark.parametrize('private_path', [
    '/STORY.md', '/STATE.md', '/docs', '/openapi.json', '/api/runs'
])
def test_private_endpoints_not_exposed(client, private_path):
    res = client.get(private_path)
    assert res.status_code == 404


# ===========================================================================
# 2. Full Investigation Playthrough via HTTP
# ===========================================================================

def test_full_investigation_http_playthrough(client):
    # 1. Start investigation
    start_res = client.post('/api/runs', json={})
    assert start_res.status_code == 201
    run_id = start_res.json()['snapshot']['run_id']
    base = f'/api/runs/{run_id}'

    # 2. Open initial files
    assert client.post(f'{base}/open-file', json={'file_id': 'F01'}).status_code == 200
    assert client.post(f'{base}/open-file', json={'file_id': 'F02'}).status_code == 200

    # 3. Photo choice on F02
    photo_res = client.post(f'{base}/photo-choice', json={'choice': 'inspect'})
    assert photo_res.status_code == 200
    assert 'shadow' in photo_res.json()['description']

    # 4. Progress clues C1 & C2
    client.post(f'{base}/open-file', json={'file_id': 'F03'})
    res_f04 = client.post(f'{base}/open-file', json={'file_id': 'F04'}).json()
    assert 'C1_ACCESS_CONTRADICTION' in res_f04['snapshot']['clues']

    client.post(f'{base}/open-file', json={'file_id': 'F05'})
    res_f06 = client.post(f'{base}/open-file', json={'file_id': 'F06'}).json()
    assert 'C2_LOG_TAMPERING' in res_f06['snapshot']['clues']

    # 5. Open F08 -> C3, unlocks F09, F10
    res_f08 = client.post(f'{base}/open-file', json={'file_id': 'F08'}).json()
    assert 'C3_LOCK_PROOF' in res_f08['snapshot']['clues']

    # 6. Open F09 & F10 -> C4
    client.post(f'{base}/open-file', json={'file_id': 'F09'})
    res_f10 = client.post(f'{base}/open-file', json={'file_id': 'F10'}).json()
    assert 'C4_CONTAINMENT_READY' in res_f10['snapshot']['clues']

    # 7. Unnumbered containment interlock sequence: ISOLATE -> VERIFY -> DISCONNECT
    assert client.post(f'{base}/containment', json={'step': 'VERIFY'}).status_code == 409
    assert client.post(f'{base}/containment', json={'step': 'ISOLATE'}).status_code == 200
    assert client.post(f'{base}/containment', json={'step': 'DISCONNECT'}).status_code == 409
    assert client.post(f'{base}/containment', json={'step': 'VERIFY'}).status_code == 200

    end_res = client.post(f'{base}/containment', json={'step': 'DISCONNECT'})
    assert end_res.status_code == 200
    end_data = end_res.json()
    assert end_data['ending'] == 'DO_NOT_FORGET'
    assert end_data['snapshot']['status'] == 'completed'
    assert end_data['snapshot']['ending_presentation']['title'] == 'DO NOT FORGET'


# ===========================================================================
# 3. Full Cross-Run HTTP Lifecycle
# ===========================================================================

def test_full_cross_run_http_lifecycle(client):
    # --- RUN 1 ---
    r1 = client.post('/api/runs', json={}).json()
    r1_id = r1['snapshot']['run_id']
    client.post(f'/api/runs/{r1_id}/open-file', json={'file_id': 'F02'})
    client.post(f'/api/runs/{r1_id}/photo-choice', json={'choice': 'leave_sealed'})

    # --- RUN 2 (Restart Investigation) ---
    r2 = client.post('/api/runs', json={'restart_from_run_id': r1_id}).json()
    r2_id = r2['snapshot']['run_id']
    assert "don't believe we've met" in r2['greeting']
    assert 'D01' not in r2['snapshot']['visible_file_ids']

    # Chat triggers cross-run memory slip
    chat_res = client.post(f'/api/runs/{r2_id}/chat', json={'message': 'Who are you?'}).json()
    assert 'sealed' in chat_res['reply'].lower() or 'negative' in chat_res['reply'].lower()

    # D01 file is now visible and readable
    files_res = client.get(f'/api/runs/{r2_id}/files').json()
    assert any(f['id'] == 'D01' for f in files_res['files'])
    d01_doc = client.post(f'/api/runs/{r2_id}/open-file', json={'file_id': 'D01'}).json()
    assert 'LEAVE SEALED' in d01_doc['file']['content']

    # Clear History API resets database
    clear_res = client.post('/api/history/clear', json={'confirm': True})
    assert clear_res.status_code == 200
    assert clear_res.json()['cleared'] is True

    # Next run starts as clean Run 1
    r3 = client.post('/api/runs', json={}).json()
    assert r3['snapshot']['run_index'] == 1
    assert r3['snapshot']['has_qualified_prior_run'] is False


# ===========================================================================
# 4. Input Validation & Error Handling
# ===========================================================================

def test_invalid_http_requests_rejected(client):
    start = client.post('/api/runs', json={}).json()
    run_id = start['snapshot']['run_id']

    # Invalid UUID
    assert client.get('/api/runs/bad-uuid').status_code == 422

    # Path traversal payload
    assert client.post(f'/api/runs/{run_id}/open-file', json={'file_id': '../../STORY.md'}).status_code == 422

    # Invalid photo choice
    assert client.post(f'/api/runs/{run_id}/photo-choice', json={'choice': 'burn_photo'}).status_code == 422

    # Invalid containment step
    assert client.post(f'/api/runs/{run_id}/containment', json={'step': 'OVERRIDE'}).status_code == 422

    # Blank chat message
    assert client.post(f'/api/runs/{run_id}/chat', json={'message': ''}).status_code == 422
