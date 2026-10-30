from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.storage.repository import Repository


def test_completed_presentation_survives_server_recreation(tmp_path):
    path = tmp_path / 'ending.sqlite3'
    with TestClient(create_app(Settings(), Repository(path))) as client:
        run = client.post('/api/runs', json={}).json()
        base = '/api/runs/' + run['run_id']
        assert run['snapshot']['ending_presentation'] is None
        for file in ['F03', 'F04', 'F05', 'F06', 'F08', 'F09', 'F10']:
            assert client.post(base + '/open-file', json={'file_id': file}).status_code == 200
        for step in ['ISOLATE', 'VERIFY']:
            result = client.post(base + '/containment', json={'step': step}).json()
            assert result['snapshot']['ending_presentation'] is None
        result = client.post(base + '/containment', json={'step': 'DISCONNECT'}).json()
        snapshot = result['snapshot']
        assert snapshot['status'] == 'completed'
        assert result['ending'] == snapshot['ending'] == 'DO_NOT_FORGET'
        presentation = snapshot['ending_presentation']
        assert presentation['title'] == 'DO NOT FORGET'
        assert presentation['final_line'] == 'If you close the archive, who will remember she was here?'
        assert presentation['narrative'] == result['message']
        assert 'OUTCOME: UNKNOWN' in presentation['narrative']
    with TestClient(create_app(Settings(), Repository(path))) as restored:
        assert restored.get(base).json()['snapshot'] == snapshot
        assert restored.post(base + '/containment', json={'step': 'DISCONNECT'}).status_code == 409
