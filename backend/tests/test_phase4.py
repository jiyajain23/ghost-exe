import asyncio
import pytest
from app.director.game import Director, GameError
from app.storage.repository import Repository

class NeverCalled:
    async def reply(self, *args):
        raise AssertionError('Memory must bypass inference')

@pytest.mark.parametrize('choice, phrase', [('inspect', 'inspected'), ('leave_sealed', 'left the negative sealed')])
def test_memory_demo_and_refresh(tmp_path, choice, phrase):
    repo = Repository(tmp_path / 'memory.sqlite3')
    director = Director(repo, NeverCalled())
    first = director.start(None)
    director.open_file(first.run_id, 'F02')
    director.photo(first.run_id, choice)
    second = director.start(first.run_id)
    assert second.run_id != first.run_id
    assert director.resume(first.run_id).snapshot.status == 'abandoned'
    assert "don't believe we've met" in second.greeting
    assert 'D01' not in second.snapshot.visible_file_ids
    with pytest.raises(GameError): director.open_file(second.run_id, 'D01')
    result = asyncio.run(director.chat(second.run_id, 'What happened to Ada?'))
    assert phrase in result.reply
    assert 'D01' in result.snapshot.visible_file_ids
    restored = Director(Repository(repo.database))
    assert restored.resume(second.run_id).snapshot.memory_revealed
    document = restored.open_file(second.run_id, 'D01').file.content
    assert ('LEAVE SEALED' if choice == 'leave_sealed' else 'INSPECT NEGATIVE') in document
    assert 'Recovered session: 001' in document
    assert 'VISITOR 002' in document
    with repo.transaction() as db:
        assert sum(e['type'] == 'memory_revealed' for e in repo.events(db, str(second.run_id))) == 1
        assert 'What happened' not in str([dict(e) for e in repo.events(db, str(second.run_id))])
    assert restored.clear_history(True).cleared
    clean = restored.start(None)
    assert clean.snapshot.run_index == 1 and not clean.snapshot.has_qualified_prior_run
    assert 'D01' not in clean.snapshot.visible_file_ids

@pytest.mark.parametrize('kind', ['none', 'file', 'question'])
def test_alternate_sources_and_no_history(tmp_path, kind):
    director = Director(Repository(tmp_path / 'memory.sqlite3'))
    first = director.start(None)
    if kind == 'file': director.open_file(first.run_id, 'F05')
    if kind == 'question': asyncio.run(director.chat(first.run_id, 'What happened to Ada?'))
    second = director.start(first.run_id)
    result = asyncio.run(director.chat(second.run_id, 'hello'))
    assert result.snapshot.memory_revealed == (kind != 'none')
    if kind == 'file': assert 'ACCESS_1031.CSV' in result.reply
    if kind == 'question': assert 'ada' in result.reply
