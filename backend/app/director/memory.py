"""Deterministic bounded projections of validated prior in-game events."""
import json
from app.content.manifest import MANIFEST


def project(db, run_index):
    rows = db.execute("""SELECT e.*, r.run_index FROM events e JOIN runs r ON r.id=e.run_id
        WHERE r.run_index < ? ORDER BY r.run_index DESC, e.id""", (run_index,)).fetchall()
    candidates = []
    for e in rows:
        payload = json.loads(e['payload_json'])
        if e['type'] == 'photo_choice' and payload.get('choice') in {'inspect', 'leave_sealed'}:
            choice = payload['choice']
            line = ('At first, you left the negative sealed last time.' if choice == 'leave_sealed'
                    else 'At first, you inspected the photo negative last time.')
            observed = 'PHOTO_INDEX.TXT -> ' + ('LEAVE SEALED' if choice == 'leave_sealed' else 'INSPECT NEGATIVE')
            priority = 0
        elif e['type'] == 'file_opened' and e['target_id'] in MANIFEST:
            title = MANIFEST[e['target_id']].title
            line = f'You opened {title} last time.'
            observed = title + ' opened'
            priority = 1 if e['target_id'] == 'F05' else 2
        elif e['type'] == 'chat_category' and payload.get('category') in {'door','logs','photo','ada','helper','clock','next'}:
            category = payload['category']
            line = f'You asked about {category} last time.'
            observed = 'Question category: ' + category
            priority = 3
        else:
            continue
        candidates.append((priority, -e['run_index'], e['id'], {
            'source_event_id': e['id'], 'source_run_index': e['run_index'],
            'line': line, 'observed': observed,
        }))
    return min(candidates, key=lambda c: c[:3])[3] if candidates else None


def notes(dossier, visitor):
    return (f'HELPER / PRIVATE NOTES / VISITOR {visitor:03d}\n'
            f"Recovered session: {dossier['source_run_index']:03d}\n"
            f"Observed behavior: {dossier['observed']}\n"
            'Planned response: deny recognition; reference the recorded behavior\n\n'
            'NOTE: These notes were assembled from in-game events, not device files.')
