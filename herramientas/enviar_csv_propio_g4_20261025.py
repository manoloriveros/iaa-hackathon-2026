"""Entrega única del CSV G4 congelado; no importa código de modelado."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path('C:/dev/Hakaton')
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
OUT = REPO / 'privado/semana2/envios/g4_20261025_v1'
INDEX = REPO / 'registro/semana2_g4_entrega_final_actual.json'
SLUG = 'iaa-ai-assisted-hackathon-2026-part-2'
MESSAGE = 'Codex G4-GLM2023-FINAL-v1 | train 2023 only | frozen CSV e5e30c5921c0494b | no calibration'
SHA = 'e5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def source():
    idx = json.loads(INDEX.read_text(encoding='utf-8-sig'))
    assert idx['model_id'] == 'G4-GLM2023-FINAL-v1'
    assert idx['CSV']['sha256'] == SHA
    p = ROOT / idx['CSV']['path']
    assert digest(p) == SHA, 'El CSV congelado cambió'
    return idx, p


def api():
    # La biblioteca oficial autentica sin imprimir ni copiar credenciales.
    from kaggle.api.kaggle_api_extended import KaggleApi
    a = KaggleApi()
    a.authenticate()
    return a


def safe_row(row, own=False):
    d = {'ref': row.ref, 'date': row.date.isoformat() if row.date else None,
         'file_name': row.file_name, 'status': str(row.status).rsplit('.', 1)[-1],
         'total_bytes': row.total_bytes}
    if own:
        d.update(public_score=row.public_score, error=row.error_description,
                 description=row.description, url=row.url)
    # No se accede a private_score ni se guardan mensajes/scores de terceros.
    return d


def remote(a):
    limits = a.competition_get_submission_limits(SLUG)
    lim = {k: getattr(limits, k) for k in ('num_today', 'num_total', 'num_allowed_now', 'limited_by_total')}
    rows = a.competition_submissions(SLUG, page_size=100) or []
    return lim, rows


def local():
    idx, p = source()
    sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
    import pyarrow.parquet as pq
    plan = json.loads((REPO / 'registro/semana2_g4_modelo_final_plan_v1.json').read_text(encoding='utf-8-sig'))
    sample = ROOT / 'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet'
    schema = pq.read_schema(sample)
    assert schema.names == ['row_id', 'prediction']
    ids = pq.read_table(sample, columns=['row_id']).column(0).to_pylist()
    with p.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == schema.names
        rows = list(reader)
    assert len(rows) == len(ids) == idx['CSV']['rows'] == 209063
    assert [r['row_id'] for r in rows] == ids
    assert len(set(ids)) == len(ids)
    assert all(math.isfinite(float(r['prediction'])) and float(r['prediction']) > 0 for r in rows)
    # La plantilla derivada sirve únicamente para el dry-run de formato del skill.
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'official_sample_format.csv').open('x', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(schema.names)
        w.writerows((v, 0) for v in ids)
    result = {'utc': now(), 'author': 'Codex', 'competition': SLUG,
              'CSV': str(p), 'sha256': SHA, 'bytes': p.stat().st_size,
              'rows': len(rows), 'columns': schema.names, 'IDs_order_exact': True,
              'predictions_positive_finite': True, 'source_index_sha256': digest(INDEX),
              'sample_sha256': digest(sample), 'sample_format_sha256': digest(OUT / 'official_sample_format.csv'),
              'prior_replay': idx['replay'], 'fit_calls': 0, 'C0_reestimated': False,
              '2024_policy_data_or_metrics_read': False, 'B00_preserved': True,
              'authorization': 'Dale, envía el CSV propio a Kaggle, verifica que se procese y deja el resultado en el foro. Sin volver a entrenar; conserva B00 y mantén 2024 cerrado.',
              'message': MESSAGE, 'cost': 'one daily submission slot; no remote training',
              'historical_plan_sha256': digest(REPO / 'registro/semana2_g4_modelo_final_plan_v1.json')}
    save('local_preflight.json', result)
    print(json.dumps(result, ensure_ascii=False))


def preflight():
    _, p = source()
    a = api()
    lim, rows = remote(a)
    matches = [safe_row(r, True) for r in rows if r.file_name == p.name or r.description == MESSAGE]
    result = {'utc': now(), 'competition': SLUG, 'limits': lim,
              'latest_metadata_only': [safe_row(r) for r in rows], 'matching_G4': matches,
              'all_submission_rows_returned': len(rows) >= lim['num_total'],
              'no_remote_write': True}
    save('remote_preflight.json', result)
    print(json.dumps(result, ensure_ascii=False))
    assert lim['num_allowed_now'] > 0, 'Cuota agotada'
    assert not matches, 'Existe un envío con el mismo nombre o identificador; conciliar antes de subir'
    assert result['all_submission_rows_returned'], 'Hay historial adicional sin conciliar'


def submit():
    if os.environ.get('KAGGLE_SKILL_READ_ONLY') == '1':
        raise RuntimeError('KAGGLE_SKILL_READ_ONLY=1; no se modifica la cuenta')
    _, p = source()
    local_check, before = load('local_preflight.json'), load('remote_preflight.json')
    assert local_check['sha256'] == SHA and not before['matching_G4']
    assert (OUT / 'skill_dry_run.txt').is_file()
    a = api()
    lim, rows = remote(a)
    assert lim['num_allowed_now'] > 0
    assert not any(r.file_name == p.name or r.description == MESSAGE for r in rows)
    # El marcador exclusivo impide repetir automáticamente un POST cuyo resultado sea incierto.
    save('submission_started.json', {'utc': now(), 'sha256': SHA, 'message': MESSAGE, 'limits_before': lim})
    try:
        response = a.competition_submit(str(p), MESSAGE, SLUG, quiet=True)
        result = {'utc': now(), 'competition': SLUG, 'ref': response.ref,
                  'response_message': response.message, 'sha256': SHA, 'message': MESSAGE,
                  'CSV': str(p), 'bytes': p.stat().st_size, 'accepted_for_processing': response.ref > 0,
                  'processed': False, 'fit_calls': 0}
        save('submission_response.json', result)
        print(json.dumps(result, ensure_ascii=False))
        assert response.ref > 0
    except Exception as e:
        # No se vuelcan excepciones con cabeceras o URLs firmadas.
        save('submission_transport_failure.json', {'utc': now(), 'exception_type': type(e).__name__,
             'status_uncertain': True, 'instruction': 'conciliar por mensaje y nombre; no reenviar a ciegas'})
        print(json.dumps({'error_type': type(e).__name__, 'status_uncertain': True}))
        raise SystemExit(1)


def check(name):
    response = load('submission_response.json')
    a = api()
    lim, rows = remote(a)
    matching = [r for r in rows if r.ref == response['ref']]
    assert len(matching) == 1, 'El envío no figura en la competición esperada'
    row = matching[0]
    assert row.description == MESSAGE and row.file_name == Path(response['CSV']).name
    assert row.total_bytes == response['bytes']
    result = {'utc': now(), 'competition': SLUG, 'sha256': SHA,
              'submission': safe_row(row, True), 'limits': lim,
              'CSV_hash_unchanged': digest(Path(response['CSV'])) == SHA,
              'new_fit_calls': 0, '2024_policy_data_or_metrics_read': False,
              'B00_preserved': True, 'manual_final_selection_changed': False}
    save(name, result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['local', 'preflight', 'submit', 'check'])
    parser.add_argument('--receipt', default='scoring_check_01.json')
    args = parser.parse_args()
    if args.action == 'local':
        local()
    elif args.action == 'preflight':
        preflight()
    elif args.action == 'submit':
        submit()
    else:
        check(args.receipt)
