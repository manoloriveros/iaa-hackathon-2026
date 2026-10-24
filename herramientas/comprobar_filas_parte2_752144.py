"""Cotejo de solo lectura de plantilla/IDs; no lee importes ni predice."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq


def main():
    routes = json.loads((ROOT / 'RUTAS_PROYECTO.json').read_text(encoding='utf-8-sig'))
    emerging = ROOT / routes['week_2_emerging_data']
    developed = ROOT / routes['week_2_developed_reference']
    checks, sources = [], []

    def read_ids(path):
        # Select only row_id. Never read sample predictions or risk features.
        parquet = pq.ParquetFile(path)
        values = parquet.read(columns=['row_id']).column('row_id').to_pylist()
        sources.append({'path': path.relative_to(ROOT).as_posix(),
                        'rows': parquet.metadata.num_rows,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        assert len(values) == parquet.metadata.num_rows
        return values

    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})

    sample = read_ids(emerging / 'sample_submission.parquet')
    concatenated = []
    line_rows = {}
    for line in ['motor', 'buildings', 'contents']:
        ids = read_ids(emerging / f'test_{line}.parquet')
        line_rows[line] = len(ids)
        check(f'{line}: unique nonnull IDs', None not in ids and len(ids) == len(set(ids)))
        concatenated.extend(ids)
    old_sample = read_ids(developed / 'sample_submission.parquet')
    check('Emerging sample 209063 rows', len(sample) == 209063)
    check('Emerging concatenated unique nonnull IDs', None not in concatenated and len(concatenated) == len(set(concatenated)))
    check('Emerging template unique nonnull IDs', None not in sample and len(sample) == len(set(sample)))
    check('Emerging template exact ID set', set(sample) == set(concatenated))
    check('Emerging template exact concatenation order', sample == concatenated)
    check('Developed template 626639 rows', len(old_sample) == 626639)
    check('Reported expected count equals developed count', len(old_sample) != len(sample) and len(old_sample) == 626639)
    result = {
        'id': 'S2-INCIDENTE-752144-20261024', 'author': 'Codex',
        'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Read-only raw Parquet row_id and metadata audit; no predictions, outcomes, fits or submissions',
        'line_rows': line_rows, 'emerging_rows': len(sample), 'developed_rows': len(old_sample),
        'passed': sum(c['pass'] for c in checks), 'failed': sum(not c['pass'] for c in checks),
        'checks': checks, 'sources': sources,
        'causation': 'Matching counts support the reported mismatch; the scorer configuration and root cause were not inspected.',
        'own_failed_submission': False, 'platform_fix_verified': False,
        'next_action': 'Keep 209063 emerging IDs; monitor host response. No padding, developed rows or diagnostic submission.',
        'professional_independent_validation': False,
    }
    output = REPO / 'registro/semana2_cotejo_filas_752144_20261024.json'
    if output.exists():
        raise FileExistsError('Preserve existing receipt; use its evidence rather than repeating the audit')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['id', 'line_rows', 'emerging_rows', 'developed_rows', 'passed', 'failed']}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
