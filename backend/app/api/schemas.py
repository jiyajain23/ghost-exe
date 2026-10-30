"""Public contracts. The Director separately authorizes every transition."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

FileId = Literal['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09', 'F10', 'D01']
RunStatus = Literal['active', 'completed', 'abandoned']
Clue = Literal['C1_ACCESS_CONTRADICTION', 'C2_LOG_TAMPERING', 'C3_LOCK_PROOF', 'C4_CONTAINMENT_READY']
PhotoChoice = Literal['inspect', 'leave_sealed']
ContainmentStep = Literal['ISOLATE', 'VERIFY', 'DISCONNECT']
GhostEffect = Literal['none', 'flicker_screen', 'change_dialogue', 'reveal_file', 'plant_clue', 'fake_deletion']
EventType = Literal[
    'run_started', 'file_opened', 'photo_choice', 'chat_category',
    'clue_unlocked', 'file_unlocked', 'ghost_effect', 'memory_revealed',
    'containment_step', 'run_completed', 'run_abandoned'
]


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class EndingPresentation(Contract):
    title: str
    final_line: str
    narrative: str


class RunState(Contract):
    ending_presentation: EndingPresentation | None = None
    run_id: UUID
    run_index: int = Field(ge=1, strict=True)
    status: RunStatus = 'active'
    opened_file_ids: list[FileId] = Field(default_factory=list)
    visible_file_ids: list[FileId]  # Supplied by the Director, not client toggles.
    clues: list[Clue] = Field(default_factory=list)
    photo_choice: PhotoChoice | None = None
    containment_index: int = Field(default=0, ge=0, le=3, strict=True)
    fear: int = Field(default=0, ge=0, le=100, strict=True)
    trust: int = Field(default=65, ge=0, le=100, strict=True)
    helper_chat_turns: int = Field(default=0, ge=0, strict=True)
    memory_revealed: StrictBool = False
    has_qualified_prior_run: StrictBool = False
    ending: Literal['DO_NOT_FORGET'] | None = None


class FileMetadata(Contract):
    id: FileId
    path: str  # Display-only virtual path; never used for filesystem access.
    title: str
    app: Literal['explorer', 'mail']
    unread: StrictBool = True
    modified: StrictBool = False


class StartRunAction(Contract):
    restart_from_run_id: UUID | None = None


class OpenFileAction(Contract):
    file_id: FileId


class PhotoChoiceAction(Contract):
    choice: PhotoChoice


class ChatAction(Contract):
    message: str = Field(min_length=1, max_length=500)

    @field_validator('message')
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Enter a message')
        return value


class ContainmentAction(Contract):
    step: ContainmentStep


class ClearHistoryAction(Contract):
    confirm: StrictBool

    @field_validator('confirm')
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError('Explicit confirmation is required')
        return value


class DirectorEffect(Contract):
    type: GhostEffect
    duration_ms: int | None = None
    file_id: FileId | None = None
    hint: str | None = None
    target: str | None = None
    message: str | None = None


class GhostReply(Contract):
    say: str = Field(min_length=1, max_length=240)
    emotion: Literal['calm', 'curious', 'defensive', 'frightened', 'possessive']
    intent: Literal['assist', 'deflect', 'deceive', 'warn', 'plead']
    request_action: GhostEffect


class HealthResponse(Contract):
    status: Literal['ok'] = 'ok'
    agent_mode: Literal['mock', 'ollama']
    ollama_reachable: bool | None = None  # null = not probed; no inference at health/startup.


class RunResponse(Contract):
    snapshot: RunState
    greeting: str


class StartRunResponse(RunResponse):
    run_id: UUID


class FilesResponse(Contract):
    files: list[FileMetadata]


class FileDocument(FileMetadata):
    content: str
    actions: list[PhotoChoice] = Field(default_factory=list)
    description: str | None = None


class OpenFileResponse(Contract):
    file: FileDocument
    snapshot: RunState
    effects: list[DirectorEffect] = Field(default_factory=list)


class PhotoResponse(Contract):
    snapshot: RunState
    description: str


class ChatResponse(Contract):
    fallback: bool = False
    reply: str
    emotion: Literal['calm', 'curious', 'defensive', 'frightened', 'possessive']
    intent: Literal['assist', 'deflect', 'deceive', 'warn', 'plead']
    effects: list[DirectorEffect] = Field(default_factory=list)
    snapshot: RunState


class ContainmentResponse(Contract):
    snapshot: RunState
    effects: list[DirectorEffect] = Field(default_factory=list)
    message: str
    ending: Literal['DO_NOT_FORGET'] | None = None


class ClearHistoryResponse(Contract):
    cleared: StrictBool = True
