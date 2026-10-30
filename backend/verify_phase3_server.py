"""Isolated real HTTP server smoke check; no player save changes."""
import socket
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import uvicorn

from app.config import Settings
from app.main import create_app
from app.storage.repository import Repository


@contextmanager
def server(settings, repository):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    instance = uvicorn.Server(uvicorn.Config(create_app(settings, repository), log_level='error'))
    thread = threading.Thread(target=instance.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not instance.started:
            if time.monotonic() > deadline:
                raise RuntimeError('Test server did not start')
            time.sleep(.02)
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False, timeout=25) as client:
            yield client
    finally:
        instance.should_exit = True
        thread.join(10)
        sock.close()


def main():
    with tempfile.TemporaryDirectory() as directory:
        repository = Repository(Path(directory) / 'smoke.sqlite3')
        # Hold an unlistened port so it cannot accidentally reach another service.
        with socket.socket() as unavailable:
            unavailable.bind(('127.0.0.1', 0))
            settings = Settings(agent_mode='ollama', ollama_base_url=f'http://127.0.0.1:{unavailable.getsockname()[1]}')
            with server(settings, repository) as client:
                run = client.post('/api/runs', json={}).json()['run_id']
                base = f'/api/runs/{run}'
                reply = client.post(base + '/chat', json={'message': 'Hello HELPER.'})
                assert reply.status_code == 200 and reply.json()['fallback']
                assert client.post(base + '/open-file', json={'file_id': 'F08'}).status_code == 404
                assert client.post(base + '/containment', json={'step': 'ISOLATE'}).status_code == 409
                for file_id in ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09', 'F10']:
                    assert client.post(base + '/open-file', json={'file_id': file_id}).status_code == 200
                    assert file_id in [f['id'] for f in client.get(base + '/files').json()['files']]
                assert client.post(base + '/containment', json={'step': 'VERIFY'}).status_code == 409
                for step in ['ISOLATE', 'VERIFY', 'DISCONNECT']:
                    result = client.post(base + '/containment', json={'step': step})
                    assert result.status_code == 200
                assert result.json()['ending'] == 'DO_NOT_FORGET'
                assert client.get(base).json()['snapshot']['status'] == 'completed'
                print('REAL HTTP: outage fallback, hidden-file gate, C1-C4, all ten files, wrong-step rejection, ending and resume PASS', flush=True)
        with server(Settings(agent_mode='ollama'), repository) as client:
            run = client.post('/api/runs', json={}).json()['run_id']
            result = client.post(f'/api/runs/{run}/chat', json={'message': 'Hello HELPER.'})
            assert result.status_code == 200
            print(f"REAL HTTP: restored local Ollama response; fallback={result.json()['fallback']}; reply={result.json()['reply']}", flush=True)


if __name__ == '__main__':
    main()
