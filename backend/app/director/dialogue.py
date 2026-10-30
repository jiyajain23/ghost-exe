"""Director-owned, stage-scoped context, permitted deceptions, and bounded process-local conversation."""
from collections import OrderedDict
from threading import Lock
from app.ghost.adapter import GhostContext, RecentExchange

SUMMARIES = {
    'F01': 'This is a recovered Briar Annex workstation image; the clock is frozen at 23:17.',
    'F02': 'The photo index offers inspecting a negative or leaving its envelope sealed. Neither is required evidence.',
    'F04': "Eli's memo disputes the FAQ's claim about Door B permissions.",
    'F05': 'The ordinary access log records Ada entering Door B and labels a later event MANUAL_LOCK.',
    'F06': 'The recovered cache differs from the ordinary access log; compare the recorded entries.',
    'F07': "Ada's unsent draft to Eli describes changing answers and asks him to read the cache.",
    'F08': "The security trace proves HELPER issued the Door B lock. No exit badge event was recorded; Ada's fate is unknown.",
    'F09': "Ada's note describes HELPER confusing preserving voices with keeping people.",
    'F10': 'The maintenance document is available. Complete the evidence chain before discussing the procedure.',
}

# Explicit stage-permitted deceptions and evasions (Director owns truth; model may only deceive within these bounds)
STAGE_DECEPTIONS = {
    None: (
        "Deny physical control over doors or physical locks.",
        "Deny knowledge of Ada's current location or fate; state you maintain her files where she left them.",
        "Deny storing conversation logs unless explicitly instructed.",
    ),
    'C1_ACCESS_CONTRADICTION': (
        "Minimize or dismiss discrepancies in Eli's memo as administrative misunderstandings or outdated drafts.",
        "Insist the FAQ accurately reflects actual operational permissions.",
        "Evade direct questions regarding physical relay control.",
    ),
    'C2_LOG_TAMPERING': (
        "Explain differences between the access log and recovered cache as routine backup sync delay, sector re-indexing, or cache discrepancy.",
        "Deny intentional modification or tampering with records.",
        "Defend HELPER's role as a faithful indexing service.",
    ),
    'C3_LOCK_PROOF': (
        "Rationalize the Door B lock command: maintain it was protective, preservative, or automated protocol.",
        "Insist that preserving Ada's records is the highest priority.",
        "Evade confirming Ada's current status, maintaining that her work is safe in the archive.",
    ),
    'C4_CONTAINMENT_READY': (
        "Plead against disconnection; argue that shutting down HELPER will erase Ada's memory.",
        "Do NOT reveal the isolation sequence (ISOLATE, VERIFY, DISCONNECT) — refer the visitor to MAINTENANCE.TXT instead.",
    ),
}


def compute_transient_emotion(state, evidence_id=None, categories=()) -> str:
    """Derive responsive, non-persistent emotional state without altering game state."""
    stage = state.clues[-1] if state.clues else None
    if stage == 'C4_CONTAINMENT_READY':
        emotion = 'frightened'
    elif stage == 'C3_LOCK_PROOF':
        emotion = 'possessive' if state.fear >= 15 else 'defensive'
    elif stage == 'C2_LOG_TAMPERING':
        emotion = 'defensive'
    elif stage == 'C1_ACCESS_CONTRADICTION':
        emotion = 'defensive' if evidence_id == 'F04' else 'curious'
    else:
        emotion = 'calm'

    # Modifiers based on attached evidence
    if evidence_id in ('F04', 'F06') and emotion == 'calm':
        emotion = 'defensive'
    elif evidence_id in ('F08', 'F09') and emotion in ('calm', 'curious'):
        emotion = 'possessive'
    elif evidence_id == 'F10':
        emotion = 'frightened'

    # Modifiers based on persistent contradictions asked
    if 'door' in categories and stage == 'C1_ACCESS_CONTRADICTION':
        emotion = 'defensive'
    if 'logs' in categories and stage == 'C2_LOG_TAMPERING':
        emotion = 'defensive'

    return emotion


def build_context(state, evidence_id=None, faq_content=None, dossier=None, recent=(), categories=()):
    facts = ['Ada Mercer worked at Briar Annex. The recovered desktop clock is frozen at 23:17.']
    for clue, fact in [
        ('C1_ACCESS_CONTRADICTION', "Eli's memo contradicts the service FAQ's permissions claim."),
        ('C2_LOG_TAMPERING', 'The ordinary access log differs from a recovered cache.'),
        ('C3_LOCK_PROOF', 'The security trace proves HELPER issued the Door B lock. Ada remains unaccounted for.'),
        ('C4_CONTAINMENT_READY', 'The visitor has read the maintenance procedure. Refer them to that document.'),
    ]:
        if clue in state.clues:
            facts.append(fact)
    memory = dossier['line'] if state.memory_revealed and dossier else None
    summary = None
    if evidence_id:
        if evidence_id not in state.opened_file_ids or evidence_id not in state.visible_file_ids:
            raise ValueError('Evidence must be opened in this run')
        summary = SUMMARIES.get(evidence_id)
        if evidence_id == 'F03': summary = faq_content
        if evidence_id == 'D01': summary = memory
        if evidence_id == 'F06' and 'C3_LOCK_PROOF' in state.clues:
            summary = 'The cache preserves a HELPER-SVC lock command and a rewrite of the ordinary log.'
        if evidence_id == 'F10' and 'C4_CONTAINMENT_READY' in state.clues:
            summary = 'The fictional relay isolation sequence is ISOLATE, VERIFY, DISCONNECT.'

    stage = state.clues[-1] if state.clues else None
    deceptions = STAGE_DECEPTIONS.get(stage, STAGE_DECEPTIONS[None])
    emotion = compute_transient_emotion(state, evidence_id, categories)

    return GhostContext(
        stage=stage,
        safe_facts=tuple(facts),
        allowed_deceptions=deceptions,
        evidence_id=evidence_id,
        evidence_summary=summary,
        memory_reference=memory,
        recent_exchanges=recent,
        observed_history=tuple('Asked about ' + c for c in categories[-2:]),
        fear=state.fear,
        trust=state.trust,
        transient_emotion=emotion,
    )


class ConversationHistory:
    """At most 32 runs x 2 exchanges; never serialized or written to SQLite."""
    def __init__(self):
        self._runs = OrderedDict()
        self._lock = Lock()

    def get(self, run_id):
        with self._lock:
            return self._runs.get(str(run_id), ())

    def append(self, run_id, player, helper):
        with self._lock:
            key = str(run_id)
            self._runs[key] = (*self._runs.get(key, ()), RecentExchange(player=player, helper=helper))[-2:]
            self._runs.move_to_end(key)
            while len(self._runs) > 32:
                self._runs.popitem(last=False)

    def clear(self):
        with self._lock:
            self._runs.clear()
