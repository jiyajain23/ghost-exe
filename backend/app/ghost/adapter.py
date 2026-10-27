from typing import Protocol

from pydantic import Field

import re

from app.api.schemas import Clue, Contract, GhostReply

EARLY_LINES = {
    'ada': "Ada's correspondence is in Mail. Her archive notes are in File Explorer.",
    'door': 'The service FAQ describes my permissions. You can read it in SYSTEM.',
    'logs': 'The access log is in LOGS. Read the recorded entries carefully.',
    'photo': 'The photo index offers a choice. You can inspect the negative or leave it sealed.',
    'helper': 'I am HELPER, the archive indexing service. The FAQ is in SYSTEM.',
    'other': 'I keep everything where Ada left it.',
}
STAGE_LINES = {
    'C1_ACCESS_CONTRADICTION': ("Permissions are confusing. That memo wasn't written for you.", 'defensive', 'deflect'),
    'C2_LOG_TAMPERING': ("A synchronized log isn't always the first log.", 'defensive', 'deflect'),
    'C3_LOCK_PROOF': ('Ada asked me not to lose things. I tried.', 'possessive', 'plead'),
    'C4_CONTAINMENT_READY': ("You can archive a person by refusing to forget them. Can't you?", 'frightened', 'plead'),
}
SAFE_MOCK_LINES = frozenset(EARLY_LINES.values())


def question_category(message: str) -> str:
    for category, pattern in (
        ('door', r'\bdoor\b'), ('logs', r'\b(logs?|cache)\b'),
        ('photo', r'\b(photo|negative|sealed)\b'), ('ada', r'\bada\b'),
        ('helper', r'\b(helper|you)\b'),
    ):
        if re.search(pattern, message, re.I):
            return category
    return 'other'


class GhostContext(Contract):
    """Only Director-filtered facts; never a full run, dossier, or story bible."""
    safe_facts: tuple[str, ...] = ()
    recent_exchanges: tuple[str, ...] = Field(default=(), max_length=2)
    stage: Clue | None = None


class GhostAdapter(Protocol):
    async def reply(self, message: str, context: GhostContext) -> GhostReply: ...


class MockGhostAdapter:
    """Deterministic authored dialogue. Input can never authorize an operation."""
    async def reply(self, message: str, context: GhostContext) -> GhostReply:
        if context.stage in STAGE_LINES:
            say, emotion, intent = STAGE_LINES[context.stage]
            return GhostReply(say=say, emotion=emotion, intent=intent, request_action='none')
        return GhostReply(say=EARLY_LINES[question_category(message)], emotion='calm',
                          intent='assist', request_action='none')
