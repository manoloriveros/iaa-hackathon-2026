"""Recibo de evidencia local nueva: artefactos de equipo, sin entrenamiento o scoring."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys
import tarfile

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_received', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'aportes_F3c_F4c_20261026_v1'
SOURCE = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025'
PRIVATE = R / 'privado/semana2/claude_mision017_20261025'

def main():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    code = SOURCE / 'exp26_20261026_v2/m017'; old_code = SOURCE / 'exp26_20261026/m017'
    plan_path = code / 'exp26/PREINSCRIPCION_AB_20261026_v2.json'; plan = w.read(plan_path)
    reference = BASE / 'calibracion_F2_creible_20261025_v1/final_creible_2025.csv'
    receipt = w.read(BASE / 'calibracion_F2_creible_20261025_v1/public_receipt.json')
    assert w.sha(reference) == plan['referencia_medida']['sha256'] == '1a003d8682f1fcd71ad4a44f59f785d394488fc1cc95e60722f418b04c30ef29'
    base = pd.read_csv(reference, dtype={'row_id': str}); assert len(base) == 209063 and base.row_id.is_unique
    expected = pd.read_parquet(ROOT / 'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet', columns=['row_id'])
    assert np.array_equal(base.row_id, expected.row_id)
    results = []; source_paths = [Path(__file__), plan_path, reference,
        code / 'construir_F3c.py', code / 'construir_F4b.py', code / 'revision/K_auditoria_F4.md',
        old_code / 'construir_F3b.py', old_code / 'exp26/lib26.py', old_code / 'revision/I_factores_residuales.md',
        old_code / 'revision/J_auditoria_F3.md']
    for archive_name, folder in [('exp26_v2.tar.gz', code), ('exp26_codigo_y_evidencia.tar.gz', old_code)]:
        path = SOURCE / archive_name; source_paths.append(path)
        with tarfile.open(path, 'r:gz') as tar:
            members = tar.getmembers(); selected = []
            for item in members:
                if not item.isfile(): continue
                prefix = 'm017/'; assert item.name.startswith(prefix) and '..' not in Path(item.name).parts
                local = folder / item.name[len(prefix):]
                if item.name.endswith(('construir_F3c.py', 'construir_F3b.py', 'construir_F4b.py', 'K_auditoria_F4.md',
                        'I_factores_residuales.md', 'J_auditoria_F3.md', 'PREINSCRIPCION_AB_20261026_v2.json')):
                    data = tar.extractfile(item).read(); assert local.read_bytes() == data
                    selected.append({'member': item.name, 'local': w.rel(local), 'sha256': w.sha(local)})
            results.append({'archive': w.rel(path), 'sha256': w.sha(path), 'members': len(members),
                'selected_members_match_local_bytes': selected, 'new_extraction_or_execution': False})
    candidates = {}
    for name in ['F3c', 'F4c']:
        path = PRIVATE / (name + '_2025.csv'); metadata = code / f'exp26/{name}_info.json'; source_paths += [path, metadata]
        meta = w.read(metadata); assert w.sha(path) == meta['sha256'] == plan['candidatos'][name]['sha256']
        raw_bytes = path.read_bytes(); f = pd.read_csv(path, dtype={'row_id': str})
        assert list(f.columns) == ['row_id', 'prediction'] and len(f) == 209063 and f.row_id.is_unique
        assert np.array_equal(f.row_id, base.row_id) and np.isfinite(f.prediction).all() and f.prediction.gt(0).all()
        assert b'\r' not in raw_bytes and raw_bytes.startswith(b'row_id,prediction\n')
        assert abs(f.prediction.sum() - meta['total']) <= .0051
        candidates[name] = {'path': w.rel(path), 'sha256': w.sha(path), 'rows': len(f), 'columns': list(f.columns),
            'positive_and_finite': True, 'official_ID_order_exact': True, 'LF_no_CR': True,
            'total': float(f.prediction.sum()), 'metadata_total_matches': True,
            'received_forecast_not_actual_score': plan['candidatos'][name]['publico_esperado'],
            'author': 'Claude', 'new_prices_produced_here': False}
    # A necessary algebraic footprint of F3c: its multiplier depends only on
    # these supplied covariates and the business cell, allowing CSV rounding.
    raw = ROOT / 'Hackaton/Semana 2/Datos/emerging'
    customer = pd.read_parquet(raw / 'customers.parquet', columns=['customer_id', 'gender', 'marketing_segment'])
    assert customer.customer_id.is_unique
    frames = []
    for line in ['motor', 'buildings', 'contents']:
        test = pd.read_parquet(raw / f'test_{line}.parquet')
        cols = ['row_id', 'customer_id', 'new_business'] + (['works_from_home'] if line == 'contents' else [])
        test = test[cols].merge(customer, on='customer_id', validate='many_to_one', how='left')
        assert len(test) and test.gender.notna().all() and test.marketing_segment.notna().all()
        test['line'] = line
        if line != 'contents': test['works_from_home'] = 'not_used'
        if line == 'buildings': test['gender'] = 'not_used'
        if line != 'contents': test['marketing_segment'] = 'not_used'
        frames.append(test)
    cov = pd.concat(frames, ignore_index=True); assert cov.row_id.is_unique and set(cov.row_id) == set(base.row_id)
    f3 = pd.read_csv(PRIVATE / 'F3c_2025.csv', dtype={'row_id': str})
    cov = cov.set_index('row_id').loc[base.row_id].reset_index()
    cov['base'] = base.prediction.to_numpy(float); cov['candidate'] = f3.prediction.to_numpy(float)
    cov['lower'] = (cov.candidate - .50001e-6) / cov.base; cov['upper'] = (cov.candidate + .50001e-6) / cov.base
    patterns = []
    for key, t in cov.groupby(['line', 'new_business', 'gender', 'works_from_home', 'marketing_segment'], dropna=False, observed=True):
        low = float(t.lower.max()); high = float(t.upper.min()); assert low <= high + 2e-14, (key, low, high)
        patterns.append({'line': key[0], 'new_business': bool(key[1]), 'gender': str(key[2]),
            'works_from_home': str(key[3]), 'marketing_segment': str(key[4]), 'rows': len(t),
            'constant_multiplier_interval_lower': low, 'constant_multiplier_interval_upper': high})
    building = cov.line.eq('buildings'); assert np.max(abs(cov.loc[building, 'candidate'] - cov.loc[building, 'base'])) <= .50001e-6
    pd.DataFrame(patterns).to_csv(OUT / 'F3c_multiplier_intervals.csv', index=False)
    source_paths += [raw / 'customers.parquet', *[raw / f'test_{l}.parquet' for l in ['motor', 'buildings', 'contents']],
                     raw / 'sample_submission.parquet']
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'received_artifact_integrity_and_necessary_algebra_checked_not_admitted',
        'new_to_this_review_not_new_official_competition_data': True,
        'source_author': 'Claude; reports attribute received AI reviews to I/J/K, not professional independent validation',
        'reference': {'CSV': w.rel(reference), 'sha256': w.sha(reference), 'processed_public_score': .16519, 'ref': 57651126},
        'candidates': candidates, 'archives': results,
        'F3c_necessary_multiplier_footprint': {'pass': True, 'patterns': len(patterns), 'rows': len(cov),
            'no_within_pattern_variation_beyond_CSV_rounding': True, 'buildings_unchanged_to_rounding': True,
            'does_not_prove_training_recipe_or_no_leakage': True, 'no_model_fitted_to_CSV': True},
        'received_limits': ['Residual variables selected after screening around20fields perline; received pvalues are adaptive',
            'Gender motor frequency evidence stable in received reports, not reproduced independently here',
            'Contents telework NB severity interaction based on33claims; marketing marginal signal uncertain',
            'FSp contribution must be incremental to factors; received NB transport adverse or unstable',
            'Provided2025FSp completion cp0 must not be used as ultimate factor; original producer excludes cp',
            'C1/F2 complete historical replay remains unavailable locally; originalA1 is a proxy',
            'Received public forecasts and submission/selection proposals are not measurements or human orders',
            'No new official data version or date change established by these local artifacts'],
        'next_unit': 'Pre-register a bounded own examination of the closed-form residual factors using the frozen N3 outer-training scopes2023–2024 and saved components, with same unmodified acceptance rules. Separate gender only, added telework and added marketing; no FSp refit or new C0. Verify necessary covariate provenance and exact recipe boundaries first; do not score or fit under this receipt.',
        'new_fits': 0, 'new_C0_fits': 0, 'new_scores': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, '2024_open': True, 'goal_achieved': False,
        'sources': {w.rel(path): w.sha(path) for path in source_paths}}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'F3c_rows': 209063, 'F4c_rows': 209063, 'F3c_covariate_multiplier_patterns': len(patterns),
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0}))

if __name__ == '__main__': main()
