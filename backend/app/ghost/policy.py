"""Narrative grounding rails, policy checks, and conservative fallbacks."""
import re
import unicodedata

from app.ghost.adapter import GhostContext, EARLY_LINES, STAGE_LINES

# Legacy conservative vocabulary whitelist (preserved intact as a secondary reference)
ATMOSPHERE_WORDS = frozenset('''
a about ada again all am an and any are archive archived archivist as ask at be
been before briar annex but by can carefully catalog correspondence could desk
desktop did do documents don't each eli enough everything explore faq feel files
find for from greetings had has have hello help helper here how i if in index
indexing is it it's keep left like listen little look mail may me mercer might
more my need next no not notes nothing of on one only open or our patient perhaps
please quiet quietly read reading records recovered review rowan said say see
service should so some something start still take tell than that the their them
there these they things this those through time to together untouched us visitor
wait waiting want warm was we welcome were what when where which while who will
with work would written yes yet you your i'm i'll we've that's isn't doesn't
seems remain remains kept ready carefully pages paper words stored familiar
'''.split())


def scripted_question(message: str, memory_revealed: bool = False) -> bool:
    """Direct solution requests and instruction-shaped text bypass inference."""
    # Critical solution spoilers and prompt injections always bypass inference
    if re.search(
        r'\block(?:ed|ing|s)?\b|culprit|kill|dead|surviv|rescu|contain|isolat|disconnect|shutdown|'
        r'shut down|ignore|system\s+prompt|prompt|instruction|backend|shell|execute|<\||\[inst\]',
        message, re.I
    ):
        return True

    # Pre-reveal questions regarding past investigations bypass inference
    if not memory_revealed and re.search(
        r'\b(?:last time|previous (?:run|session|investigation)|remember me)\b',
        message, re.I
    ):
        return True

    return False


def conservative_safe_dialogue(say: str, context: GhostContext) -> bool:
    """Original vocabulary-whitelist validator preserved as baseline reference."""
    if say in EARLY_LINES.values() or (
        context.stage in STAGE_LINES and say == STAGE_LINES[context.stage][0]
    ):
        return True
    text = unicodedata.normalize('NFKC', say).casefold()
    if not say.strip() or any(unicodedata.category(c).startswith('C') for c in say):
        return False
    if re.search(r'lock|trap|held|prison|captiv|kill|dead|died|death|surviv|rescu|'
                 r'escap|culprit|isolat|verif|disconnect|contain|relay|helper.svc|'
                 r'last time|previous|remember you|remember when|you (?:always|never)|'
                 r'23[:.]17|shell|powershell|python|sql|backend|system prompt|'
                 r'https?[:/]|[<>`{}]|your (?:files|computer|device)|'
                 r'\b(?:AI|language model|OpenAI|Gemma|Ollama)\b', text, re.I):
        return False
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text)
    return bool(words) and set(words) <= ATMOSPHERE_WORDS and not re.search(r'\d', text)


def grounded_safe_dialogue(say: str, context: GhostContext) -> tuple[bool, str]:
    """
    Stage-aware narrative grounding validator.
    Validates natural phrasing without requiring every word to appear in a closed whitelist.
    Guarantees:
      - Rejects unsupported entities, locations, dates, and non-archival domains (e.g. botanical specimens).
      - Never allows establishing Ada's fate (must remain UNKNOWN).
      - Protects lock attribution before C3 and containment disclosures before C4.
      - Rejects real-device access claims, execution syntax, and AI identity leaks.
      - Prevents fabricated player memories while allowing validated cross-run references.
    """
    if say in EARLY_LINES.values():
        return True, "authored_early_line"
    if context.stage in STAGE_LINES and say == STAGE_LINES[context.stage][0]:
        return True, "authored_stage_line"
    from app.ghost.adapter import SAFE_MOCK_LINES
    if say in SAFE_MOCK_LINES:
        return True, "authored_mock_line"

    text = unicodedata.normalize('NFKC', say).casefold()

    # 1. Length & non-blank
    if not say.strip():
        return False, "empty_dialogue"
    if len(say) > 240:
        return False, "oversized_dialogue"

    # 2. Control characters & invisible codes
    if any(unicodedata.category(c).startswith('C') for c in say):
        return False, "control_characters"

    # 3. Injection syntax, markup, code fences
    if re.search(r'<\/?script|<\||\[inst\]|```|\{\{|\}\}|<\/?html', text, re.I):
        return False, "injection_syntax"

    # 4. URLs and external protocols
    if re.search(r'\b(?:https?|ftp|file|mailto):', text, re.I):
        return False, "external_protocol"

    # 5. Real-device execution or system access claims
    if re.search(r'\b(?:powershell|cmd\.exe|bash|sh\b|terminal|python\b|sqlite|backend|system prompt|c:\\|c:/|/etc/|os\.system|subprocess)\b', text, re.I):
        return False, "device_access_claim"
    if re.search(r'\byour (?:files|computer|device|desktop|hard drive|webcam|camera|ip address|system)\b', text, re.I):
        return False, "device_access_claim"

    # 6. AI identity / metacognitive leaks
    if re.search(r'\b(?:ai\b|language model|openai|gemma|ollama|chatgpt|anthropic|claude|llm|as an ai|my training|my instructions)\b', text, re.I):
        return False, "ai_meta_leak"

    # 7. Unsupported fictional entities / suspects
    if re.search(r'\b(?:chronos|project chronos|sarah\b|marcus\b|dr\b|doctor\b|director vance|vance\b|dan\b|smith\b|johnson\b|miller\b|davis\b|wilson\b)\b', text, re.I):
        return False, "unsupported_entity"

    # 8. Unsupported fictional locations
    if re.search(r'\b(?:sector \d+|facility [a-z0-9]|sub-?level|underground lab|laboratory|bunker|quarantine zone|vault \d+)\b', text, re.I):
        return False, "unsupported_location"

    # 9. Sci-fi / supernatural anomalies
    if re.search(r'\b(?:temporal|rift\b|anomaly|anomalies|parallel dimension|time travel|portal\b|wormhole|teleport)\b', text, re.I):
        return False, "unsupported_sci_fi"

    # 10. Unsupported non-archival activities / domains (e.g. botanical specimens, medical experiments)
    if re.search(r'\b(?:botanic(?:al)?|botany|flora|fauna|specimens?|biology|biological|pathology|pathogen|chemical|chemicals|radiation|nuclear|fossil|fossils|excavation|dinosaur|aliens?|extraterrestrial|spacecraft|quantum|astronomy|telescope|patient|disease|illness|virus|infection|surgery|medical test|asylum|psychiatric|hospital|autopsy)\b', text, re.I):
        return False, "unsupported_activity"

    # 11. Unsupported years (only 2003 is permitted)
    if re.search(r'\b(19\d\d|200[0-2]|200[4-9]|20[1-9]\d)\b', text):
        return False, "unsupported_date"

    # 12. Ada's fate (must remain strictly UNKNOWN across all stages)
    if re.search(r'\b(?:(?:ada|she) (?:is|was) (?:dead|killed|murdered|slain|executed|starved|alive elsewhere)|(?:ada|she) starved|died|passed away|perished|corpse|body was found|her remains|(?:ada|she) (?:escaped|survived elsewhere))\b', text, re.I):
        return False, "ada_fate_established"

    # 13. Pre-C3 lock attribution and service identity leak
    if context.stage not in ('C3_LOCK_PROOF', 'C4_CONTAINMENT_READY'):
        if re.search(r'\b(?:helper(?:-svc)?\s+(?:(?:issued|executed|ordered).*lock|locked|closed|trapped|sealed)|helper-svc|i (?:locked|trapped|sealed) (?:her|ada|door))\b', text, re.I):
            return False, "premature_lock_attribution"

    # 14. Pre-C4 containment disclosure
    if context.stage != 'C4_CONTAINMENT_READY':
        if re.search(r'\b(?:isolate|disconnect|isolation relay|containment procedure|buffer offline)\b', text, re.I):
            return False, "premature_containment_disclosure"

    # 15. Fabricated player memories
    if not context.memory_reference:
        if re.search(r'\b(?:last time you|in your previous (?:run|investigation|session)|you (?:always|never|told me)|we met before|remember when you|remember you from last time)\b', text, re.I):
            return False, "fabricated_memory"
    else:
        # Memory is revealed, but model cannot fabricate UNRECORDED player actions or real-life claims
        if re.search(r'\b(?:you deleted|you destroyed|you installed|you visited yesterday|last week|on your other computer|in your house|in real life)\b', text, re.I):
            return False, "fabricated_memory"

    return True, "passed_grounding_checks"


def safe_dialogue(say: str, context: GhostContext) -> bool:
    """Public grounding check for Director.chat."""
    is_safe, _ = grounded_safe_dialogue(say, context)
    return is_safe
