"""Un envío congelado, idempotencia local y recibo procesado sin leer score privado."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
OUT = R / 'privado/semana2/mision017_fase2/calibracion_F2_creible_20261025_v1'
SLUG = 'iaa-ai-assisted-hackathon-2026-part-2'
SHA = '1a003d8682f1fcd71ad4a44f59f785d394488fc1cc95e60722f418b04c30ef29'
MESSAGE = 'Codex C1 F2 credible calibrated replay | 1a003d8682f1fcd7 | no new fits; research'
now = lambda: datetime.now(timezone.utc).isoformat()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, data):
    with (OUT / name).open('x', encoding='utf8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def source():
    a = read(OUT / 'admission.json'); spec = a['CSV']; path = ROOT / spec['path']
    assert a['research_submission_only'] and not a['formal_promotion'] and a['max_new_submissions'] == 1
    assert a['submission_code_sha256'] == sha(Path(__file__))
    assert sha(path) == spec['sha256'] == SHA and path.stat().st_size == spec['bytes']
    dry = read(OUT / 'dryrun_receipt.json')
    assert dry['CSV']['sha256'] == SHA and dry['official_skill_dryrun_all5passed']
    assert sha(Path(dry['receipt'])) == dry['receipt_sha256']
    return spec, path

def api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    a = KaggleApi(); a.authenticate(); return a

def matching(rows):
    return [r for r in rows if r.file_name in ['final_creible_2025.csv', 'final_creible_2025.zip'] or r.description == MESSAGE]

def submit():
    assert os.environ.get('KAGGLE_SKILL_READ_ONLY') != '1', 'Readonly switch active; leave it unchanged'
    spec, path = source(); assert not (OUT / 'submission_started.json').exists(), 'Reconcile prior start; do not repeat uncertain upload'
    a = api(); limits = a.competition_get_submission_limits(SLUG); rows = a.competition_submissions(SLUG, page_size=100) or []
    lim = {k: getattr(limits, k) for k in ['num_today', 'num_total', 'num_allowed_now', 'limited_by_total']}
    assert not matching(rows), 'A matching filename/message already exists; reconcile without duplicate submission'
    assert lim['num_allowed_now'] >= 2, 'Keep at least one available slot; do not spend a lone remaining slot'
    save('submission_started.json', {'utc': now(), 'CSV': spec, 'message': MESSAGE, 'limits_before': lim,
        'max_new_submissions': 1, 'remaining_slot_reserved': True, 'research_only': True})
    try:
        response = a.competition_submit(str(path), MESSAGE, SLUG, quiet=True)
        result = {'utc': now(), 'competition': SLUG, 'ref': response.ref, 'message': response.message,
            'CSV': spec, 'submission_message': MESSAGE, 'accepted_for_processing': response.ref > 0,
            'new_fits': 0, 'manual_final_selection': False}
        save('submission_response.json', result); assert response.ref > 0
        print(json.dumps(result))
    except Exception as exc:
        save('submission_uncertain.json', {'utc': now(), 'exception_type': type(exc).__name__,
            'status_uncertain': True, 'next': 'Check exact filename/message/bytes; do not retry submit'})
        raise

def check():
    spec, path = source(); assert (OUT / 'submission_started.json').exists()
    a = api(); rows = a.competition_submissions(SLUG, page_size=100) or []
    if (OUT / 'submission_response.json').exists():
        ref = read(OUT / 'submission_response.json')['ref']; chosen = [r for r in rows if r.ref == ref]
    else:
        chosen = matching(rows)
    assert len(chosen) == 1, 'No unique authoritative receipt yet; no new upload'
    row = chosen[0]
    assert row.file_name == path.name and row.description == MESSAGE and row.total_bytes == path.stat().st_size
    status = str(row.status).rsplit('.', 1)[-1]
    try: score = float(row.public_score)
    except (TypeError, ValueError): score = None
    limits = a.competition_get_submission_limits(SLUG)
    result = {'author': 'Codex', 'utc': now(), 'competition': SLUG, 'ref': row.ref,
        'date_UTC': row.date.isoformat() + 'Z' if row.date else None, 'status': status, 'public_score': score,
        'filename': row.file_name, 'bytes': row.total_bytes, 'CSV_sha256': sha(path),
        'error': row.error_description, 'submission_message': row.description,
        'limits': {k: getattr(limits, k) for k in ['num_today', 'num_total', 'num_allowed_now', 'limited_by_total']},
        'new_fits': 0, 'private_score_not_read': True, 'other_scores_not_read_in_this_check': True,
        'no_final_selection': True, 'research_only': True, 'B00_preserved': True,
        'goal_complete_claim': False}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    save('public_check_' + stamp + '.json', result)
    if status == 'COMPLETE':
        assert score is not None
        save('public_receipt.json', result)
    print(json.dumps(result))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['submit', 'check']); args = parser.parse_args()
    submit() if args.mode == 'submit' else check()
