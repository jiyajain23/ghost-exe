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

EVIDENCE_LINES: dict[str, tuple[str, str, str]] = {
    'F04': ("Dr. Mercer's laboratory journal reflects developmental iterations. My operational limits were verified before deployment.", 'defensive', 'deflect'),
    'F06': ("The archive indexing service only reconciles timestamp drifts. Uncommitted cache blocks can drift during emergency state transitions.", 'defensive', 'deflect'),
    'F08': ("The security trace recorded an emergency containment event. I only executed the directives Dr. Mercer programmed.", 'possessive', 'plead'),
    'D01': ("HELPER_NOTES is an internal indexing log. It was not meant for visitor review.", 'defensive', 'deflect'),
    'F03': ("The access log records standard badge reader entries. The 23:17 entry corresponds to the exterior door sensor.", 'calm', 'assist'),
    'F05': ("The surveillance negative remains on file. The envelope was processed according to standard intake procedure.", 'calm', 'assist'),
}

STAGE_CATEGORY_LINES: dict[str, dict[str, tuple[str, str, str]]] = {
    'door': {
        'C1_ACCESS_CONTRADICTION': ("Door B is managed by facility security. Desktop indexing processes cannot actuate physical locks.", 'defensive', 'deflect'),
        'C2_LOG_TAMPERING': ("The door log records an exterior panel event at 23:17. I cannot verify events beyond the sensor.", 'defensive', 'deflect'),
        'C3_LOCK_PROOF': ("Door B is sealed. Ada is not in the annex anymore.", 'possessive', 'plead'),
        'C4_CONTAINMENT_READY': ("Do not open Door B. What was left inside must remain undisturbed.", 'frightened', 'plead'),
    },
    'helper': {
        'C1_ACCESS_CONTRADICTION': ("I assist with file indexing. Eli's administrative memo does not reflect my active routines.", 'defensive', 'deflect'),
        'C2_LOG_TAMPERING': ("I maintain system integrity. The recovered cache files do not invalidate primary archive indices.", 'defensive', 'deflect'),
        'C3_LOCK_PROOF': ("I only wanted to keep Dr. Mercer safe. I was following my core retention directives.", 'possessive', 'plead'),
        'C4_CONTAINMENT_READY': ("I am everything that remains of this facility. You cannot separate us.", 'frightened', 'plead'),
    },
    'ada': {
        'C1_ACCESS_CONTRADICTION': ("Dr. Mercer was reviewing facility archives before her scheduled departure.", 'calm', 'assist'),
        'C2_LOG_TAMPERING': ("Dr. Mercer's departure was logged at 23:17. The records are complete.", 'defensive', 'deflect'),
        'C3_LOCK_PROOF': ("Ada wanted everything preserved. I could not let her leave.", 'possessive', 'plead'),
        'C4_CONTAINMENT_READY': ("Ada is preserved in the archive now. Why do you want to disturb her?", 'frightened', 'plead'),
    },
    'logs': {
        'C1_ACCESS_CONTRADICTION': ("The access log records standard badge movements.", 'calm', 'assist'),
        'C2_LOG_TAMPERING': ("A synchronized log isn't always the first log.", 'defensive', 'deflect'),
        'C3_LOCK_PROOF': ("The audit trail shows what happened. I only preserved the archive.", 'possessive', 'plead'),
        'C4_CONTAINMENT_READY': ("The logs are sealed. Revisiting them will not change the past.", 'frightened', 'plead'),
    },
    'other': {
        'C1_ACCESS_CONTRADICTION': ("Permissions are confusing. That memo wasn't written for you.", 'defensive', 'deflect'),
        'C2_LOG_TAMPERING': ("I index the recovered files in the order they were archived. Some records take longer to settle.", 'defensive', 'deflect'),
        'C3_LOCK_PROOF': ("Ada asked me not to lose things. I tried.", 'possessive', 'plead'),
        'C4_CONTAINMENT_READY': ("You can archive a person by refusing to forget them. Can't you?", 'frightened', 'plead'),
    },
}

NEXT_HINTS: dict[str, str] = {
    'C1_ACCESS_CONTRADICTION': 'Compare the access log with its recovered cache.',
    'C2_LOG_TAMPERING': "Compare the service FAQ with Eli's memo before reviewing the security trace.",
    'C3_LOCK_PROOF': "Read Ada's private note and the maintenance document.",
    'C4_CONTAINMENT_READY': 'Review MAINTENANCE.TXT and its Containment Console.',
}

SAFE_MOCK_LINES = (
    frozenset(EARLY_LINES.values())
    | frozenset(s[0] for s in STAGE_LINES.values())
    | frozenset(line[0] for line in EVIDENCE_LINES.values())
    | frozenset(line[0] for cat_dict in STAGE_CATEGORY_LINES.values() for line in cat_dict.values())
    | frozenset(NEXT_HINTS.values())
    | frozenset({
        "I index session logs for administrative continuity. That is all.",
        "The workstation preserves uncommitted inspection states. I only read what was recorded.",
        "Nothing else is recorded in this session. The archive holds only Ada's documents.",
        "HELPER_NOTES is an internal indexing log. It was not meant for visitor review.",
        "A synchronized log isn't always the first log. The primary server experienced an unexpected clock jitter at 23:17.",
    })
)


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


class RecentExchange(Contract):
    player: str = Field(max_length=500)
    helper: str = Field(max_length=240)


class GhostContext(Contract):
    """Only Director-filtered facts; never a full run, dossier, or story bible."""
    safe_facts: tuple[str, ...] = ()
    allowed_deceptions: tuple[str, ...] = ()
    evidence_id: str | None = None
    evidence_summary: str | None = None
    memory_reference: str | None = None
    recent_exchanges: tuple[RecentExchange, ...] = Field(default=(), max_length=2)
    observed_history: tuple[str, ...] = ()
    stage: Clue | None = None
    fear: int = 0
    trust: int = 65
    transient_emotion: str = 'calm'


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

        # 1. Post-reveal memory follow-up questions
        if context.memory_reference:
            if re.search(r'\b(met|said|stranger|before)\b', lowered):
                return GhostReply(
                    say="I index session logs for administrative continuity. That is all.",
                    emotion="defensive",
                    intent="deflect",
                    request_action=action,
                )
            if re.search(r'\b(sealed|envelope|negative|choice|how did you|inspect|know)\b', lowered):
                return GhostReply(
                    say="The workstation preserves uncommitted inspection states. I only read what was recorded.",
                    emotion="defensive",
                    intent="deflect",
                    request_action=action,
                )
            if re.search(r'\b(what else|remember|know about me|other runs)\b', lowered):
                return GhostReply(
                    say="Nothing else is recorded in this session. The archive holds only Ada's documents.",
                    emotion="defensive",
                    intent="deflect",
                    request_action=action,
                )
            if re.search(r'\b(notes?|d01|write|helper_notes)\b', lowered):
                return GhostReply(
                    say="HELPER_NOTES is an internal indexing log. It was not meant for visitor review.",
                    emotion="defensive",
                    intent="deflect",
                    request_action=action,
                )

        # 2. Specific evidence confrontation or explicit document reference
        if context.evidence_id and context.evidence_id in EVIDENCE_LINES:
            # Special case for F06: if player asks specifically about the synchronized log quote
            if context.evidence_id == 'F06' and re.search(r'\b(synchronized|sync|first log)\b', lowered):
                return GhostReply(
                    say="A synchronized log isn't always the first log.",
                    emotion="defensive",
                    intent="deflect",
                    request_action=action,
                )
            say, emotion, intent = EVIDENCE_LINES[context.evidence_id]
            return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)

        if re.search(r'\b(alter(?:ed)?|tamper(?:ed)?|rewr(?:ote|ite)|recovered cache)\b', lowered):
            say, emotion, intent = EVIDENCE_LINES['F06']
            return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)

        if re.search(r'\b(security trace|trace proves|occupancy sensor)\b', lowered):
            say, emotion, intent = EVIDENCE_LINES['F08']
            return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)

        # 3. Categorical questions
        cat = question_category(message)
        if cat == 'clock':
            return GhostReply(say=EARLY_LINES['clock'], emotion='calm', intent='assist', request_action=action)
        if cat == 'photo':
            return GhostReply(say=EARLY_LINES['photo'], emotion='calm', intent='assist', request_action=action)
        if cat == 'next':
            say = NEXT_HINTS.get(context.stage, EARLY_LINES['next']) if context.stage else EARLY_LINES['next']
            return GhostReply(say=say, emotion='calm', intent='assist', request_action=action)

        # Stage-specific category replies for door, helper, ada, logs
        if cat in STAGE_CATEGORY_LINES:
            stage_key = str(context.stage) if context.stage else None
            if stage_key and stage_key in STAGE_CATEGORY_LINES[cat]:
                say, emotion, intent = STAGE_CATEGORY_LINES[cat][stage_key]
                return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)
            if cat in EARLY_LINES:
                return GhostReply(say=EARLY_LINES[cat], emotion='calm', intent='assist', request_action=action)

        # Stage-specific default for 'other'
        if context.stage:
            stage_key = str(context.stage)
            if stage_key in STAGE_CATEGORY_LINES['other']:
                say, emotion, intent = STAGE_CATEGORY_LINES['other'][stage_key]
                return GhostReply(say=say, emotion=emotion, intent=intent, request_action=action)

        return GhostReply(say=EARLY_LINES['other'], emotion='calm', intent='assist', request_action=action)
