"""Phase 1 Director: initial documents and choices; no Phase 2 clue transitions."""
import asyncio
import json
from uuid import UUID

from app.api.schemas import (ChatResponse, FileDocument, FileId, FileMetadata, FilesResponse,
                             GhostReply, OpenFileResponse, PhotoChoice, PhotoResponse,
                             RunResponse, RunState, StartRunResponse)
from app.content.manifest import MANIFEST
from app.ghost.adapter import (GhostAdapter, GhostContext, MockGhostAdapter,
                               SAFE_MOCK_LINES, question_category)
from app.storage.repository import Repository

INITIAL_FILES: tuple[FileId, ...] = ('F01', 'F02', 'F03', 'F04', 'F05')
GREETING = "Hello. I'm HELPER, Ada's archive assistant. Start with START_HERE.TXT. I keep everything where Ada left it."
PHOTO_DESCRIPTIONS = {
    'inspect': 'FRAME_17: a shadow visible inside Door B; time uncertain.',
    'leave_sealed': 'Envelope left untouched.',
}


class GameError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


class Director:
    def __init__(self, repository: Repository, ghost: GhostAdapter | None = None, timeout: float = 20):
        self.repository = repository
        self.ghost = ghost or MockGhostAdapter()
        self.timeout = timeout

    def _snapshot(self, db, run_id: str) -> RunState:
        run = self.repository.get_run(db, run_id)
        if run is None:
            raise GameError(404, 'Investigation not found. Start a new investigation if local history was cleared.')
        events = self.repository.events(db, run_id)
        opened = list(dict.fromkeys(e['target_id'] for e in events if e['type'] == 'file_opened'))
        choices = [json.loads(e['payload_json'])['choice'] for e in events if e['type'] == 'photo_choice']
        return RunState(run_id=run_id, run_index=run['run_index'], status=run['status'],
                        visible_file_ids=list(INITIAL_FILES), opened_file_ids=opened,
                        photo_choice=choices[0] if choices else None,
                        helper_chat_turns=sum(e['type'] == 'chat_category' for e in events))

    @staticmethod
    def _active(state: RunState):
        if state.status != 'active':
            raise GameError(409, 'This investigation is no longer active.')

    def start(self, restart_from_run_id: UUID | None) -> StartRunResponse:
        if restart_from_run_id is not None:
            raise GameError(409, 'Restart Investigation is not available in this development phase.')
        with self.repository.transaction() as db:
            run_id = self.repository.create_run(db)
            return StartRunResponse(run_id=run_id, snapshot=self._snapshot(db, run_id), greeting=GREETING)

    def resume(self, run_id: UUID) -> RunResponse:
        with self.repository.transaction() as db:
            return RunResponse(snapshot=self._snapshot(db, str(run_id)), greeting=GREETING)

    @staticmethod
    def _metadata(file_id: FileId, state: RunState) -> FileMetadata:
        doc = MANIFEST[file_id]
        return FileMetadata(id=doc.id, path=doc.path, title=doc.title, app=doc.app,
                            unread=file_id not in state.opened_file_ids)

    def files(self, run_id: UUID) -> FilesResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            return FilesResponse(files=[self._metadata(i, state) for i in state.visible_file_ids])

    def open_file(self, run_id: UUID, file_id: FileId) -> OpenFileResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            self._active(state)
            if file_id not in state.visible_file_ids:
                raise GameError(404, 'Document is not available in this investigation.')
            if file_id not in state.opened_file_ids:
                self.repository.append(db, str(run_id), 'file_opened', file_id)
            state = self._snapshot(db, str(run_id))
            document = FileDocument(**self._metadata(file_id, state).model_dump(),
                                    content=MANIFEST[file_id].content,
                                    actions=['inspect', 'leave_sealed'] if file_id == 'F02' else [],
                                    description=PHOTO_DESCRIPTIONS.get(state.photo_choice) if file_id == 'F02' else None)
            return OpenFileResponse(file=document, snapshot=state)

    def photo(self, run_id: UUID, choice: PhotoChoice) -> PhotoResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            self._active(state)
            if 'F02' not in state.opened_file_ids:
                raise GameError(409, 'Open PHOTO_INDEX.TXT before choosing.')
            if state.photo_choice is not None and state.photo_choice != choice:
                raise GameError(409, 'Your first photo choice is already recorded. Reopen the document to view it.')
            if state.photo_choice is None:
                self.repository.append(db, str(run_id), 'photo_choice', 'F02', {'choice': choice})
            return PhotoResponse(snapshot=self._snapshot(db, str(run_id)), description=PHOTO_DESCRIPTIONS[choice])

    async def chat(self, run_id: UUID, message: str) -> ChatResponse:
        # Never hold a SQLite transaction while waiting on an adapter.
        self._active(self.resume(run_id).snapshot)
        context = GhostContext()  # Phase 1 reveals no clue stages to the adapter.
        try:
            proposal = await asyncio.wait_for(self.ghost.reply(message, context), self.timeout)
            reply = GhostReply.model_validate_json(proposal.model_dump_json())
            if reply.say not in SAFE_MOCK_LINES or reply.request_action != 'none':
                raise ValueError('Unapproved Phase 1 dialogue/effect')
        except (TimeoutError, ValueError, TypeError, AttributeError, OSError):
            reply = await MockGhostAdapter().reply('', context)
        with self.repository.transaction() as db:
            self._active(self._snapshot(db, str(run_id)))
            self.repository.append(db, str(run_id), 'chat_category', payload={'category': question_category(message)})
            state = self._snapshot(db, str(run_id))
        return ChatResponse(reply=reply.say, emotion=reply.emotion, intent=reply.intent, snapshot=state)
