"""Real HTTP memory demo with isolated saves in both runtime modes."""
import tempfile
from pathlib import Path
from verify_phase3_server import server
from app.config import Settings
from app.storage.repository import Repository

for mode in ['mock', 'ollama']:
    with tempfile.TemporaryDirectory() as directory:
        with server(Settings(agent_mode=mode), Repository(Path(directory) / 'memory.sqlite3')) as client:
            first = client.post('/api/runs', json={}).json()['run_id']
            base = '/api/runs/' + first
            assert client.post(base + '/open-file', json={'file_id':'F02'}).status_code == 200
            assert client.post(base + '/photo-choice', json={'choice':'leave_sealed'}).status_code == 200
            second = client.post('/api/runs', json={'restart_from_run_id':first}).json()
            base = '/api/runs/' + second['run_id']
            assert "don't believe we've met" in second['greeting']
            assert client.post(base + '/open-file', json={'file_id':'D01'}).status_code == 404
            reply = client.post(base + '/chat', json={'message':'What happened to Ada?'}).json()
            assert reply['reply'] == 'At first, you left the negative sealed last time.'
            assert 'D01' in reply['snapshot']['visible_file_ids']
            assert client.get(base).json()['snapshot']['memory_revealed']
            notes = client.post(base + '/open-file', json={'file_id':'D01'}).json()['file']['content']
            assert 'LEAVE SEALED' in notes and 'Recovered session: 001' in notes
            assert client.post('/api/history/clear', json={'confirm':True}).status_code == 200
            assert client.get(base).status_code == 404
            print(mode + ': HTTP photo/restart/reveal/notes/resume/clear PASS')
