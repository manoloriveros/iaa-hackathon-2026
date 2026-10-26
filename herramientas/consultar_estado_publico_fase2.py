"""Recibo oficial de estado propio; sin escrituras o envíos, no lee private_score."""
from pathlib import Path
from datetime import datetime, timezone
import json
from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
OUT = R / 'privado/semana2/mision017_fase2/estado_publico_20261026_v1'
SLUG = 'iaa-ai-assisted-hackathon-2026-part-2'

def main():
    assert not OUT.exists()
    a = KaggleApi(); a.authenticate()
    limits = a.competition_get_submission_limits(SLUG)
    rows = a.competition_submissions(SLUG, page_size=100) or []
    records = []
    for row in rows:
        try: public_score = float(row.public_score)
        except (TypeError, ValueError): public_score = None
        records.append({'ref': row.ref, 'date_UTC': row.date.isoformat() + 'Z' if row.date else None,
            'status': str(row.status).rsplit('.', 1)[-1], 'public_score': public_score,
            'filename': row.file_name, 'bytes': row.total_bytes})
    complete = [r for r in records if r['status'] == 'COMPLETE' and r['public_score'] is not None]
    best = max(complete, key=lambda r: r['public_score']) if complete else None
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'competition': SLUG,
        'limits': {k: getattr(limits, k) for k in ['num_today', 'num_total', 'num_allowed_now', 'limited_by_total']},
        'own_team_records': records, 'best_processed_public': best,
        'no_submission_or_competition_write': True, 'authentication_introspection_may_use_read_RPC_POST': True,
        'private_score_not_read': True, 'other_team_scores_not_read': True,
        'new_fits': 0, 'new_submissions': 0, 'goal_complete_claim': False}
    OUT.mkdir(parents=True)
    (OUT / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'receipt': str(OUT / 'receipt.json'), 'limits': result['limits'],
        'best_processed_public': best, 'own_records': len(records), 'no_submission_or_competition_write': True}))

if __name__ == '__main__':
    main()
