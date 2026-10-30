"""Phase 2 Authoritative Game Director.
Owns truth, evidence, clue gates, file visibility, fear/trust, containment, and ending.
"""
import asyncio
import json
from uuid import UUID

from app.api.schemas import (
    ChatResponse,
    ClearHistoryResponse,
    Clue,
    ContainmentResponse,
    ContainmentStep,
    DirectorEffect,
    FileDocument,
    FileId,
    FileMetadata,
    FilesResponse,
    GhostReply,
    OpenFileResponse,
    PhotoChoice,
    PhotoResponse,
    RunResponse,
    RunState,
    StartRunResponse,
)
from app.content.manifest import MANIFEST
from app.director.dialogue import build_context, ConversationHistory
from app.director.memory import project, notes
from app.ghost.adapter import (
    GhostAdapter,
    GhostContext,
    MockGhostAdapter,
    question_category,
)
from app.storage.repository import Repository
from app.ghost.ollama import diagnostic
from app.ghost.policy import safe_dialogue, scripted_question

INITIAL_FILES: tuple[FileId, ...] = ('F01', 'F02', 'F03', 'F04', 'F05')
GREETING = "Hello. I'm HELPER, Ada's archive assistant. Start with START_HERE.TXT. I keep everything where Ada left it."
PHOTO_DESCRIPTIONS = {
    'inspect': 'FRAME_17: a shadow visible inside Door B; time uncertain.',
    'leave_sealed': 'Envelope left untouched.',
}

F03_MODIFIED_CONTENT = (
    "HELPER SERVICE / FREQUENT QUESTIONS\n"
    "Installed: 10/26/2003\n"
    "Purpose: catalog archive notes, logs, and recorded correspondence.\n\n"
    "Q: Can HELPER open or lock doors?\n"
    "A: No. HELPER is an indexing service. It has no physical access.\n\n"
    "Q: Does HELPER retain conversations?\n"
    "A: No conversation records are stored."
)

ENDING_FINAL_MESSAGE = (
    "RELAY STATUS: ISOLATED\n"
    "LAST VERIFIED LOCATION OF ADA MERCER: ARCHIVE DOOR B\n"
    "OUTCOME: UNKNOWN\n"
    "ARCHIVE IMAGE BACKUP: COMPLETE"
)


class GameError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


class Director:
    def __init__(self, repository: Repository, ghost: GhostAdapter | None = None, timeout: float = 20):
        self.repository = repository
        self.ghost = ghost or MockGhostAdapter()
        self.timeout = timeout
        self.conversation = ConversationHistory()

    def _snapshot(self, db, run_id: str) -> RunState:
        run = self.repository.get_run(db, run_id)
        if run is None:
            raise GameError(404, 'Investigation not found. Start a new investigation if local history was cleared.')
        events = self.repository.events(db, run_id)

        opened = list(dict.fromkeys(e['target_id'] for e in events if e['type'] == 'file_opened'))
        choices = [json.loads(e['payload_json'])['choice'] for e in events if e['type'] == 'photo_choice']
        chat_turns = sum(e['type'] == 'chat_category' for e in events)
        containment_steps = [e for e in events if e['type'] == 'containment_step']
        containment_index = len(containment_steps)

        # Clue derivations
        c1 = 'F03' in opened and 'F04' in opened
        c2 = 'F05' in opened and 'F06' in opened
        c3 = c1 and c2 and 'F08' in opened
        c4 = c3 and 'F09' in opened and 'F10' in opened

        clues: list[Clue] = []
        if c1:
            clues.append('C1_ACCESS_CONTRADICTION')
        if c2:
            clues.append('C2_LOG_TAMPERING')
        if c3:
            clues.append('C3_LOCK_PROOF')
        if c4:
            clues.append('C4_CONTAINMENT_READY')

        # Visible file derivations
        visible: list[FileId] = list(INITIAL_FILES)
        if 'F05' in opened and 'F06' not in visible:
            visible.append('F06')
        if c2 and 'F07' not in visible:
            visible.append('F07')
        if c1 and c2 and 'F08' not in visible:
            visible.append('F08')
        if c3:
            if 'F09' not in visible:
                visible.append('F09')
            if 'F10' not in visible:
                visible.append('F10')

        # Fear & Trust calculations
        fear = 0
        if 'F06' in opened:
            fear += 8
        if 'F08' in opened:
            fear += 12
        if 'F09' in opened:
            fear += 6
        fear = max(0, min(100, fear))

        trust = 65
        if c1:
            trust -= 10
        if c2:
            trust -= 15
        if c3:
            trust -= 20
        trust = max(0, min(100, trust))

        # Ending state
        ending = 'DO_NOT_FORGET' if containment_index >= 3 or run['status'] == 'completed' else None

        dossier = self.repository.get_beliefs(db, run_id).get('prior_dossier')
        has_prior = dossier is not None
        mem_revealed = any(e['type'] == 'memory_revealed' for e in events)
        if mem_revealed and dossier:
            visible.append('D01')

        return RunState(
            run_id=run_id,
            run_index=run['run_index'],
            status=run['status'],
            visible_file_ids=visible,
            opened_file_ids=opened,
            clues=clues,
            photo_choice=choices[0] if choices else None,
            containment_index=containment_index,
            fear=fear,
            trust=trust,
            helper_chat_turns=chat_turns,
            memory_revealed=mem_revealed,
            has_qualified_prior_run=has_prior,
            ending_presentation={
                'title': 'DO NOT FORGET',
                'final_line': 'If you close the archive, who will remember she was here?',
                'narrative': ENDING_FINAL_MESSAGE,
            } if run['status'] == 'completed' else None,
            ending=ending,
        )

    def _sync_progression(self, db, run_id: str, old_state: RunState | None = None):
        """Append clue_unlocked and file_unlocked events for newly earned progression."""
        state = self._snapshot(db, run_id)
        old_clues = set(old_state.clues if old_state else [])
        old_visible = set(old_state.visible_file_ids if old_state else INITIAL_FILES)

        for clue in state.clues:
            if clue not in old_clues:
                self.repository.append(db, run_id, 'clue_unlocked', target=clue)

        for file_id in state.visible_file_ids:
            if file_id not in old_visible:
                self.repository.append(db, run_id, 'file_unlocked', target=file_id)

    @staticmethod
    def _active(state: RunState):
        if state.status != 'active':
            raise GameError(409, 'This investigation is no longer active.')

    def start(self, restart_from_run_id: UUID | None = None) -> StartRunResponse:
        with self.repository.transaction() as db:
            parent = str(restart_from_run_id) if restart_from_run_id else None
            if parent:
                previous = self._snapshot(db, parent)
                if previous.status == 'active':
                    self.repository.update_run_status(db, parent, 'abandoned')
                    self.repository.append(db, parent, 'run_abandoned')
            run_id = self.repository.create_run(db, parent)
            self.conversation.clear()
            index = self.repository.get_run(db, run_id)['run_index']
            self.repository.set_belief(db, run_id, 'prior_dossier', project(db, index))
            state = self._snapshot(db, run_id)
            return StartRunResponse(run_id=run_id, snapshot=state, greeting=self._greeting(state))

    @staticmethod
    def _greeting(state):
        return "Hello. I'm HELPER. I don't believe we've met." if state.run_index > 1 else GREETING

    def resume(self, run_id: UUID) -> RunResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            return RunResponse(snapshot=state, greeting=self._greeting(state))

    @staticmethod
    def _metadata(file_id: FileId, state: RunState) -> FileMetadata:
        if file_id == 'D01':
            return FileMetadata(id='D01', path='/SYSTEM/HELPER_NOTES.TXT', title='HELPER_NOTES.TXT', app='explorer', unread=file_id not in state.opened_file_ids, modified=False)
        doc = MANIFEST[file_id]
        is_modified = file_id == 'F03' and 'C2_LOG_TAMPERING' in state.clues
        return FileMetadata(
            id=doc.id,
            path=doc.path,
            title=doc.title,
            app=doc.app,
            unread=file_id not in state.opened_file_ids,
            modified=is_modified,
        )

    def files(self, run_id: UUID) -> FilesResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            return FilesResponse(files=[self._metadata(i, state) for i in state.visible_file_ids])

    def open_file(self, run_id: UUID, file_id: FileId) -> OpenFileResponse:
        with self.repository.transaction() as db:
            old_state = self._snapshot(db, str(run_id))
            self._active(old_state)
            if file_id not in old_state.visible_file_ids:
                raise GameError(404, 'Document is not available in this investigation.')

            first_read = file_id not in old_state.opened_file_ids
            if first_read:
                self.repository.append(db, str(run_id), 'file_opened', file_id)
                self._sync_progression(db, str(run_id), old_state)

            state = self._snapshot(db, str(run_id))

            # Virtual display variant for F03 after C2
            if file_id == 'D01':
                content = notes(self.repository.get_beliefs(db, str(run_id))['prior_dossier'], state.run_index)
            elif file_id == 'F03' and 'C2_LOG_TAMPERING' in state.clues:
                content = F03_MODIFIED_CONTENT
            else:
                content = MANIFEST[file_id].content

            # Track effects if newly unlocked
            effects: list[DirectorEffect] = []
            if first_read and file_id == 'F05' and 'F06' in state.visible_file_ids:
                effects.append(DirectorEffect(type='reveal_file', file_id='F06'))
            elif first_read and 'F08' in state.visible_file_ids and 'F08' not in old_state.visible_file_ids:
                effects.append(DirectorEffect(type='reveal_file', file_id='F08'))

            document = FileDocument(
                **self._metadata(file_id, state).model_dump(),
                content=content,
                actions=['inspect', 'leave_sealed'] if file_id == 'F02' else [],
                description=PHOTO_DESCRIPTIONS.get(state.photo_choice) if file_id == 'F02' else None,
            )
            return OpenFileResponse(file=document, snapshot=state, effects=effects)

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

    async def chat(self, run_id: UUID, message: str, evidence_id: FileId | None = None) -> ChatResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            self._active(state)
            if evidence_id and (evidence_id not in state.opened_file_ids or evidence_id not in state.visible_file_ids):
                raise GameError(409, 'Open this evidence in the current investigation before asking HELPER about it.')
            dossier = self.repository.get_beliefs(db, str(run_id)).get('prior_dossier')
            if dossier and not state.memory_revealed and state.helper_chat_turns == 0:
                self.repository.append(db, str(run_id), 'chat_category', payload={'category': question_category(message)})
                self.repository.append(db, str(run_id), 'memory_revealed', payload={'source_event_id': dossier['source_event_id']})
                self.repository.append(db, str(run_id), 'file_unlocked', 'D01')
                return ChatResponse(reply=dossier['line'], emotion='defensive', intent='deflect',
                    effects=[DirectorEffect(type='reveal_file', file_id='D01')], snapshot=self._snapshot(db, str(run_id)))
        # Pre-check state outside transaction
        current_state = self.resume(run_id).snapshot
        self._active(current_state)

        with self.repository.transaction() as db:
            categories = [json.loads(e['payload_json'])['category'] for e in self.repository.events(db, str(run_id))
                          if e['type'] == 'chat_category'][-2:]
            dossier = self.repository.get_beliefs(db, str(run_id)).get('prior_dossier')
        faq = F03_MODIFIED_CONTENT if 'C2_LOG_TAMPERING' in current_state.clues else MANIFEST['F03'].content
        context = build_context(current_state, evidence_id, faq, dossier,
                                self.conversation.get(run_id), categories)
        fallback = False
        try:
            if scripted_question(message, current_state.memory_revealed):
                proposal = await MockGhostAdapter().reply(message, context)
                proposal.request_action = 'none'
            else:
                proposal = await asyncio.wait_for(self.ghost.reply(message, context), self.timeout)
            reply = GhostReply.model_validate_json(proposal.model_dump_json())
            if not safe_dialogue(reply.say, context):
                diagnostic('safety_rejection')
                raise ValueError('Unsafe narrative proposal')
        except (TimeoutError, ValueError, TypeError, AttributeError, OSError):
            fallback = True
            reply = await MockGhostAdapter().reply(message, context)
            reply.request_action = 'none'

        # Validate and authorize Ghost effects in Director
        approved_effects: list[DirectorEffect] = []
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            self._active(state)
            events = self.repository.events(db, str(run_id))

            # Effect 1: flicker_screen
            if reply.request_action == 'flicker_screen':
                flicker_events = [e for e in events if e['type'] == 'ghost_effect' and e['target_id'] == 'flicker_screen']
                last_flicker_id = flicker_events[-1]['id'] if flicker_events else 0
                chat_events_since = sum(e['type'] == 'chat_category' and e['id'] > last_flicker_id for e in events)

                if state.fear >= 20 and (not flicker_events or chat_events_since >= 2):
                    approved_effects.append(DirectorEffect(type='flicker_screen', duration_ms=250))
                    self.repository.append(db, str(run_id), 'ghost_effect', 'flicker_screen')

            # Effect 2: reveal_file
            elif reply.request_action == 'reveal_file':
                if 'C2_LOG_TAMPERING' in state.clues and 'F07' in state.visible_file_ids and 'F07' not in state.opened_file_ids:
                    approved_effects.append(DirectorEffect(type='reveal_file', file_id='F07'))
                    self.repository.append(db, str(run_id), 'ghost_effect', 'reveal_file', {'file_id': 'F07'})

            # Effect 3: plant_clue
            elif reply.request_action == 'plant_clue':
                clue_events = [e for e in events if e['type'] == 'ghost_effect' and e['target_id'] == 'plant_clue']
                last_clue_id = clue_events[-1]['id'] if clue_events else 0
                chat_since_clue = sum(e['type'] == 'chat_category' and e['id'] > last_clue_id for e in events)

                if not clue_events or chat_since_clue >= 3:
                    if 'C1_ACCESS_CONTRADICTION' not in state.clues:
                        hint = "Review the service FAQ alongside Eli's memo regarding door permissions."
                    elif 'C2_LOG_TAMPERING' not in state.clues:
                        hint = "Compare the access log entries with the recovered cache records."
                    elif 'C3_LOCK_PROOF' not in state.clues:
                        hint = "Check the Door B security log for who authorized the lock."
                    elif 'C4_CONTAINMENT_READY' not in state.clues:
                        hint = "Read Ada's private note and the maintenance isolation procedure."
                    else:
                        hint = "The containment procedure can now be executed in MAINTENANCE.TXT."

                    approved_effects.append(DirectorEffect(type='plant_clue', hint=hint))
                    self.repository.append(db, str(run_id), 'ghost_effect', 'plant_clue', {'hint': hint})

            # Effect 4: fake_deletion
            elif reply.request_action == 'fake_deletion':
                fake_del_events = [e for e in events if e['type'] == 'ghost_effect' and e['target_id'] == 'fake_deletion']
                if not fake_del_events:
                    approved_effects.append(DirectorEffect(type='fake_deletion', target='system_temp_cache'))
                    self.repository.append(db, str(run_id), 'ghost_effect', 'fake_deletion')

            # Append the chat category
            self.repository.append(db, str(run_id), 'chat_category', payload={'category': question_category(message)})
            new_state = self._snapshot(db, str(run_id))

        self.conversation.append(run_id, message, reply.say)
        diagnostic('disallowed_action' if reply.request_action not in {'none', 'change_dialogue'} and not approved_effects else 'director_complete')
        return ChatResponse(
            fallback=fallback,
            reply=reply.say,
            emotion=reply.emotion,
            intent=reply.intent,
            effects=approved_effects,
            snapshot=new_state,
        )

    def containment(self, run_id: UUID, step: ContainmentStep) -> ContainmentResponse:
        with self.repository.transaction() as db:
            state = self._snapshot(db, str(run_id))
            self._active(state)

            if 'C4_CONTAINMENT_READY' not in state.clues:
                raise GameError(409, 'Containment Console is locked. The complete evidence chain (C4) is required.')

            if state.containment_index == 0:
                if step != 'ISOLATE':
                    raise GameError(409, 'Invalid containment step. Expected ISOLATE as step 1.')
                self.repository.append(db, str(run_id), 'containment_step', 'ISOLATE', {'step': 'ISOLATE'})
                message = 'RELAY ISOLATION SIGNAL SENT. VERIFICATION REQUIRED.'
                effects = [DirectorEffect(type='flicker_screen', duration_ms=200)]
                ending = None

            elif state.containment_index == 1:
                if step != 'VERIFY':
                    raise GameError(409, 'Invalid containment step. Expected VERIFY as step 2.')
                self.repository.append(db, str(run_id), 'containment_step', 'VERIFY', {'step': 'VERIFY'})
                message = 'RELAY BUFFER VERIFIED OFFLINE. READY FOR DISCONNECT.'
                effects = [DirectorEffect(type='flicker_screen', duration_ms=200)]
                ending = None

            elif state.containment_index == 2:
                if step != 'DISCONNECT':
                    raise GameError(409, 'Invalid containment step. Expected DISCONNECT as step 3.')
                self.repository.append(db, str(run_id), 'containment_step', 'DISCONNECT', {'step': 'DISCONNECT'})
                self.repository.append(db, str(run_id), 'run_completed', payload={'ending': 'DO_NOT_FORGET'})
                self.repository.update_run_status(db, str(run_id), 'completed')
                message = ENDING_FINAL_MESSAGE
                effects = [DirectorEffect(type='flicker_screen', duration_ms=500)]
                ending = 'DO_NOT_FORGET'

            else:
                raise GameError(409, 'Containment procedure is already completed.')

            updated_state = self._snapshot(db, str(run_id))
            return ContainmentResponse(
                snapshot=updated_state,
                effects=effects,
                message=message,
                ending=ending,
            )

    def clear_history(self, confirm: bool) -> ClearHistoryResponse:
        if not confirm:
            raise GameError(422, 'Explicit confirmation is required to clear history.')
        with self.repository.transaction() as db:
            self.repository.clear_history(db)
        self.conversation.clear()
        return ClearHistoryResponse(cleared=True)
