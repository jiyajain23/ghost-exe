from typing import Protocol
import re

from pydantic import Field

from app.api.schemas import Clue, Contract, GhostEffect, GhostReply

EARLY_LINES = {
    'clock': 'The clock is frozen in the recovered workstation image. It is not a live clock.',
    'next': 'Start with the service FAQ and the archived mail, then compare the access records.',
    'ada': "Ada's correspondence is in Mail. Her archive notes are in File Explorer.",
    'door': 'The service FAQ describes my permissions. You can read it in SYSTEM.',
    'logs': 'The access log is in LOGS. Read the recorded entries carefully.',
    'photo': 'The photo index offers a choice. You can inspect the negative or leave it sealed.',
    'helper': 'I am HELPER, the archive indexing service. The FAQ is in SYSTEM.',
    'other': 'I keep everything where Ada left it.',
}

STAGE_LINES: dict[Clue, tuple[str, str, str]] = {
    'C1_ACCESS_CONTRADICTION': ("Permissions are confusing. That memo wasn't written for you.", 'defensive', 'deflect'),
    'C2_LOG_TAMPERING': ("A synchronized log isn't always the first log.", 'defensive', 'deflect'),
    'C3_LOCK_PROOF': ('Ada asked me not to lose things. I tried.', 'possessive', 'plead'),
    'C4_CONTAINMENT_READY': ("You can archive a person by refusing to forget them. Can't you?", 'frightened', 'plead'),
}

SAFE_MOCK_LINES = frozenset(EARLY_LINES.values()) | frozenset(s[0] for s in STAGE_LINES.values())


def question_category(message: str) -> str:
    for category, pattern in (
        ('clock', r'\bclock\b'),
        ('next', r'\b(next|read|hint)\b'),
        ('door', r'\bdoor\b'),
        ('logs', r'\b(logs?|cache)\b'),
        ('photo', r'\b(photo|negative|sealed)\b'),
        ('ada', r'\bada\b'),
        ('helper', r'\b(helper|you)\b'),
    ):
        if re.search(pattern, message, re.I):
            return category
    return 'other'


class GhostContext(Contract):
    """Only Director-filtered facts; never a full run, dossier, or story bible."""
    safe_facts: tuple[str, ...] = ()
    recent_exchanges: tuple[str, ...] = Field(default=(), max_length=2)
    observed_history: tuple[str, ...] = ()
    stage: Clue | None = None
    fear: int = 0
    trust: int = 65


class GhostAdapter(Protocol):
    async def reply(self, message: str, context: GhostContext) -> GhostReply: ...


class MockGhostAdapter:
    """Deterministic authored dialogue. Input can never authorize an unvetted operation."""
    async def reply(self, message: str, context: GhostContext) -> GhostReply:
        action: GhostEffect = 'none'
        lowered = message.lower()
        if 'flicker' in lowered:
            action = 'flicker_screen'
        elif 'hint' in lowered or 'clue' in lowered:
            action = 'plant_clue'

        cat = question_category(message)
        if cat in {'clock', 'ada', 'photo', 'next', 'logs'}:
            say = EARLY_LINES[cat]
            if cat == 'next' and context.stage:
                say = {
                    'C1_ACCESS_CONTRADICTION': 'Compare the access log with its recovered cache.',
                    'C2_LOG_TAMPERING': "Compare the service FAQ with Eli's memo before reviewing the security trace.",
                    'C3_LOCK_PROOF': "Read Ada's private note and the maintenance document.",
                    'C4_CONTAINMENT_READY': 'Review MAINTENANCE.TXT and its Containment Console.',
                }[context.stage]
            return GhostReply(say=say, emotion='calm', intent='assist', request_action=action)

        if context.stage in STAGE_LINES:
            say, emotion, intent = STAGE_LINES[context.stage]
            return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)

        cat = question_category(message)
        return GhostReply(say=EARLY_LINES[cat], emotion='calm', intent='assist', request_action=action)
