"""Copia exacta y preflight de un CSV2025 existente; no genera predicciones."""
from pathlib import Path
import argparse
import csv
import hashlib
import itertools
import json
import math
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def safe_csv(relative):
    p = (ROOT/relative).resolve()
    assert p.is_relative_to(ROOT) and p.suffix.lower() == '.csv'
    assert not {'2024', 'sel01', 'ledger', 'actas', 'models'}.intersection({x.lower() for x in p.parts})
    assert '2024' not in p.stem and not p.name.lower().startswith(('oof', 'score'))
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    assert config_path.is_relative_to(ROOT)
    config = json.loads(config_path.read_text(encoding='utf-8'))
    assert config['operation'] == 'byte_exact_existing_2025_csv_copy_no_new_inference'
    assert config['source_selected_by_participant'] is True
    source = safe_csv(config['source']['path'])
    sample = safe_csv(config['sample']['path'])
    target = safe_csv(config['destination'])
    assert target.is_relative_to(ROOT/'Hackaton/Repositorio_IAA2026/privado')
    assert sha(source) == config['source']['sha256'], 'Existing CSV content changed'
    assert sha(sample) == config['sample']['sha256'], 'Pinned sample changed'
    assert not target.exists(), 'Do not overwrite an earlier preparation'
    seen, rows, zero_rows = set(), 0, 0
    smallest, largest = float('inf'), float('-inf')
    with source.open(encoding='utf-8-sig', newline='') as src, sample.open(encoding='utf-8-sig', newline='') as ref:
        pred, expected = csv.reader(src, strict=True), csv.reader(ref, strict=True)
        assert next(pred) == next(expected) == ['row_id', 'prediction'], 'Unexpected CSV columns'
        for number, pair in enumerate(itertools.zip_longest(pred, expected), start=2):
            row, sample_row = pair
            assert row is not None and sample_row is not None, 'Row counts differ from sample'
            assert len(row) == len(sample_row) == 2, 'Wrong column count at CSV line '+str(number)
            assert row[0] == sample_row[0] and row[0] and row[0] not in seen, 'ID/order/uniqueness mismatch at CSV line '+str(number)
            value = float(row[1])
            assert math.isfinite(value) and value >= 0, 'Invalid prediction at CSV line '+str(number)
            seen.add(row[0]); rows += 1; zero_rows += int(value == 0)
            smallest, largest = min(smallest, value), max(largest, value)
    assert rows == config['expected_rows'] == 209063
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst, 1048576)
    digest = sha(target)
    assert digest == config['source']['sha256'] and sha(source) == digest
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'competition': config['competition'], 'source': config['source'], 'sample': config['sample'],
        'destination': target.relative_to(ROOT).as_posix(), 'sha256': digest,
        'columns': ['row_id', 'prediction'], 'rows': rows, 'unique_ids': len(seen),
        'order_matches_sample': True, 'finite_nonnegative_predictions': True,
        'zero_prediction_rows': zero_rows, 'minimum_prediction': smallest, 'maximum_prediction': largest,
        'byte_identical_to_existing_source': True, 'lineage': config['lineage'],
        'source_is_new_G4_prediction': False, 'model_fits': 0, 'C0_calls': 0,
        'new_inferences': 0, 'new_scores': 0, '2024_artifacts_opened': False,
        'submission_sent': False, 'final_roster_changed': False, 'B00_preserved': True,
        'validation_scope': 'CSV contract and source identity only; not predictive model validation or promotion'}
    p = target.with_suffix('.preflight.json')
    with p.open('x', encoding='utf-8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({k: receipt[k] for k in ['destination', 'sha256', 'rows', 'unique_ids',
        'order_matches_sample', 'byte_identical_to_existing_source', 'source_is_new_G4_prediction', 'submission_sent']}, ensure_ascii=True))


if __name__ == '__main__':
    main()
