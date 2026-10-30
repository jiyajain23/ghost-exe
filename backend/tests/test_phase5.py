import asyncio
from app.director.game import Director
from app.storage.repository import Repository
from app.ghost.adapter import GhostContext
from app.api.schemas import GhostReply


def test_three_complete_investigations_and_memory(tmp_path):
    repo = Repository(tmp_path / 'repeat.sqlite3')
    director = Director(repo)
    current = director.start(None)
    for iteration, choice in enumerate(['leave_sealed', 'inspect', 'leave_sealed']):
        run = current.run_id
        for file in ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09', 'F10']:
            director.open_file(run, file)
            director.open_file(run, file)  # duplicate clicks cannot duplicate first-read events
        director.photo(run, choice)
        director.photo(run, choice)
        for step in ['ISOLATE', 'VERIFY', 'DISCONNECT']:
            result = director.containment(run, step)
        assert result.snapshot.status == 'completed'
        director = Director(Repository(repo.database))
        assert director.resume(run).snapshot.ending == 'DO_NOT_FORGET'
        current = director.start(run)
        reply = asyncio.run(director.chat(current.run_id, 'What happened to Ada?'))
        expected = 'left the negative sealed' if choice == 'leave_sealed' else 'inspected the photo negative'
        assert expected in reply.reply
        assert director.resume(current.run_id).snapshot.memory_revealed
        notes = director.open_file(current.run_id, 'D01').file.content
        assert f'Recovered session: {iteration + 1:03d}' in notes
        with repo.transaction() as db:
            events = repo.events(db, str(run))
            assert sum(e['type'] == 'photo_choice' for e in events) == 1
            assert sum(e['type'] == 'file_opened' and e['target_id'] == 'F02' for e in events) == 1


def test_chat_outage_and_recovery_same_run(tmp_path):
    class SwitchableGhost:
        offline = False
        async def reply(self, message, context: GhostContext):
            if self.offline:
                raise OSError('simulated local connection loss')
            return GhostReply(say='These records have been waiting quietly.', emotion='calm', intent='assist', request_action='none')
    ghost = SwitchableGhost()
    director = Director(Repository(tmp_path / 'outage.sqlite3'), ghost)
    run = director.start(None).run_id
    assert not asyncio.run(director.chat(run, 'hello')).fallback
    ghost.offline = True
    assert asyncio.run(director.chat(run, 'hello')).fallback
    director.open_file(run, 'F05')
    ghost.offline = False
    assert not asyncio.run(director.chat(run, 'hello')).fallback
    assert 'F06' in director.resume(run).snapshot.visible_file_ids
