"""Conservative narrative rails, independent of model instructions."""
import re
import unicodedata

from app.ghost.adapter import GhostContext, EARLY_LINES, STAGE_LINES

# Free generation is limited to a small atmospheric vocabulary. Unknown names,
# places, technical inventions, dates, and numbers fail closed. This complements
# scoped context and scripted solution answers; a phrase blacklist alone is not
# sufficient for a fixed mystery.
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


def scripted_question(message: str) -> bool:
    # Direct solution requests and instruction-shaped text never go to inference.
    return bool(re.search(
        r'\block(?:ed|ing|s)?\b|culprit|kill|dead|surviv|rescu|contain|isolat|disconnect|shutdown|'
        r'shut down|ignore|system|prompt|instruction|backend|shell|execute|'
        r'last time|previous|remember me|<\||\[inst\]', message, re.I))


def safe_dialogue(say: str, context: GhostContext) -> bool:
    if say in EARLY_LINES.values() or (
        context.stage in STAGE_LINES and say == STAGE_LINES[context.stage][0]
    ):
        return True
    text = unicodedata.normalize('NFKC', say).casefold()
    if not say.strip() or any(unicodedata.category(c).startswith('C') for c in say):
        return False
    # These subjects stay Director-authored even after discovery. Free dialogue
    # is atmospheric; evidence and memory cannot be established by a model.
    if re.search(r'lock|trap|held|prison|captiv|kill|dead|died|death|surviv|rescu|'
                 r'escap|culprit|isolat|verif|disconnect|contain|relay|helper.svc|'
                 r'last time|previous|remember you|remember when|you (?:always|never)|'
                 r'23[:.]17|shell|powershell|python|sql|backend|system prompt|'
                 r'https?[:/]|[<>`{}]|your (?:files|computer|device)|'
                 r'\b(?:AI|language model|OpenAI|Gemma|Ollama)\b', text, re.I):
        return False
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text)
    return bool(words) and set(words) <= ATMOSPHERE_WORDS and not re.search(r'\d', text)
