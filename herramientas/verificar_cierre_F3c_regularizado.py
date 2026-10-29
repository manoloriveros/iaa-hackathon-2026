"""Coteja recibos y resultados guardados de F3c-R, sin ajustar ni inferir."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math

ROOT = Path('C:/dev/Hakaton')
R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/F3c_regularizado_20261028'
OUT = BASE / 'closeout'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(name, result):
    OUT.mkdir(exist_ok=True)
    result.update(author='Codex', utc=datetime.now(timezone.utc).isoformat(),
                  verifier_sha256=sha(Path(__file__)), new_fits=0,
                  new_inferences=0, new_submissions=0)
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=True))


def source():
    src = BASE / 'source_scoped'
    plan = read(R / 'registro/semana2_F3c_regularizado_fuente_plan.json')
    scopes = [s['scope'] for s in plan['scopes']]
    assert len(scopes) == len(set(scopes)) == 26
    files = {}
    records = []
    expected_attempts = set()
    for scope in scopes:
        marker = read(src / scope / 'source_complete.json')
        assert marker['scope'] == scope and marker['model_pairs'] == 18 and marker['scores'] == 0
        admission = read(src / scope / 'curves_admission.json')
        curves = src / scope / 'curves.json'
        assert sha(curves) == admission['curves_sha256']
        files[str(curves.relative_to(ROOT))] = sha(curves)
        for line in ['motor', 'buildings', 'contents']:
            for family in ['N0', 'F1']:
                for seed in [11, 12, 13]:
                    folder = src / scope / line / f'{family}_{seed}'
                    rec = read(folder / 'complete.json')
                    assert rec['scope'] == scope
                    assert len(rec['arguments_sha256']) == 64 and rec['rounds'] > 0
                    for kind in ['model', 'raw']:
                        path = ROOT / rec[kind]
                        digest = sha(path)
                        assert digest == rec[kind + '_sha256'], str(path)
                        files[rec[kind]] = digest
                    files[str((folder / 'complete.json').relative_to(ROOT))] = sha(folder / 'complete.json')
                    if not rec['reused_exact']:
                        inner = read(folder / 'inner_complete.json')
                        assert inner['arguments_sha256'] == rec['arguments_sha256']
                        assert inner['rounds'] == rec['rounds']
                        expected_attempts.update((scope, line, family, seed, stage) for stage in ['inner', 'full'])
                    records.append(rec)
    attempts = [json.loads(s) for s in (src / 'native_attempts.jsonl').read_text().splitlines()]
    counted = Counter(tuple(a[k] for k in ['scope', 'line', 'family', 'seed', 'stage']) for a in attempts)
    assert set(counted) == expected_attempts
    extra = [{'key': list(k), 'attempts': v} for k, v in counted.items() if v > 1]
    reused = sum(r['reused_exact'] for r in records)
    assert len(records) == 468 and reused == 33 and len(expected_attempts) == 870
    assert len(attempts) == 872 and sum(v - 1 for v in counted.values()) == 2
    curves = read(src / 'curves_complete.json')
    assert curves['all_passed'] and len(curves['scopes']) == 26
    save('source_reconciliation.json', dict(
        all_passed=True, scopes=26, completed_pairs=468, reused_pairs=33,
        new_completed_pairs=435, completed_native_fits=870,
        native_attempts=872, interrupted_extra_attempts=2, repeated_attempt_keys=extra,
        primary_RKM_bundles=curves['primary_RKM_bundles'],
        adverse_RKM_bundles=curves['adverse_RKM_bundles_separate'], files=files,
        limit='Cotejo de hashes y recibos; no recalcula argumentos, RKM ni modelos.'))


def final():
    import sys
    sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
    import numpy as np
    import pandas as pd
    target, assessment = BASE / 'target_real', BASE / 'assessment'
    assert read(assessment / 'status.json')['state'] == 'COMPLETE'
    source_receipt = read(OUT / 'source_reconciliation.json')
    assert source_receipt['all_passed']
    seal = read(target / 'artifact_seal.json')
    for name, digest in seal['files'].items():
        assert sha(target / name) == digest
    controls = read(target / 'controls.json')
    assert controls['all_passed'] and all(controls['checks'].values())
    assert all(x['entire_branch_exact'] for x in controls['fold_controls'])
    journal = [json.loads(x) for x in (target / 'calibrator_attempts.jsonl').read_text().splitlines()]
    roles = dict(Counter(x['role'] for x in journal))
    assert len(journal) == controls['calibrator_calls'] == 34
    assert roles == controls['call_roles'] == {
        'primary': 16, 'held2024_poison': 16, 'positive_training': 1, 'independent_optimizer': 1}
    result = read(assessment / 'results.json')
    assert result['target_seal_sha256'] == sha(target / 'artifact_seal.json')
    assert result['plan_sha256'] == sha(R / 'registro/semana2_F3c_regularizado_evaluacion_plan.json')
    assert result['max_independent_point_score_error'] < 1e-10
    assert result['bootstrap_proof']['max_direct_draw_error'] < 1e-10
    assert result['bootstrap_proof']['draws'] == 10000 and result['groups'] == 36408
    pred = pd.read_parquet(target / 'predictions2024.parquet').sort_values('row_id')
    old = pd.read_parquet(R / 'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/predictions2024.parquet').sort_values('row_id')
    assert pred.row_id.is_unique and np.array_equal(pred.row_id, old.row_id) and len(pred) == 59202
    y = pred.row_id.map(pd.read_parquet(target / 'labels2024.parquet').set_index('row_id').y).to_numpy()
    mean = math.fsum(y.tolist()) / len(y)
    den = math.fsum((4 * (y / math.sqrt(mean) - 2 * np.sqrt(y) + math.sqrt(mean))).tolist())
    independent = {}
    for name in ['F3c_R', 'matched_trainlevel_full', 'public_full']:
        mu = (old if name == 'public_full' else pred)[name].to_numpy()
        value = 1 - math.fsum((4 * (y / np.sqrt(mu) - 2 * np.sqrt(y) + np.sqrt(mu))).tolist()) / den
        assert abs(value - result['metrics']['global']['D2'][name]) < 1e-12
        independent[name] = value
    boot = np.load(assessment / 'bootstrap.npz')
    assert boot['delta'].shape == (10000, 8, 2)
    for j, name in enumerate(boot['segments']):
        for k, comp in enumerate(boot['comparisons']):
            assert np.array_equal(np.quantile(boot['delta'][:, j, k], [.00125, .99875]), result['metrics'][name]['family20'][comp])
    assert result['all_gates_pass'] == {k: all(v.values()) for k, v in result['gates'].items()}
    stable = read(assessment / 'whole_pipeline_stability.json')
    assert len(stable['folds']) == 5 and stable['new_fits'] == 0 and stable['members_not_selectable']
    for comp, value in stable['all_five_gates'].items():
        assert value == all(x['stability_gates'][comp] for x in stable['folds'])
        assert value == result['gates'][comp]['whole_pipeline_fivefold_stability']
    stresses = read(assessment / 'fixed_price_stresses.json')
    assert len(stresses['scenarios']) == 50 and stresses['fixed_prices_no_relearning']
    receipt = read(assessment / 'documentation.json')
    assert receipt['result_sha256'] == sha(assessment / 'results.json')
    assert receipt['report_sha256'] == sha(ROOT / receipt['report'])
    assert receipt['forum'] == read(assessment / 'forum_receipt.json')
    csv = R / 'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
    assert sha(csv) == '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
    paths = [target / 'artifact_seal.json', target / 'controls.json', OUT / 'source_reconciliation.json', csv]
    paths += [assessment / x for x in ['results.json', 'bootstrap.npz', 'first20_group_counts.npy',
        'fixed_price_stresses.json', 'whole_pipeline_stability.json', 'stability_predictions2024.parquet',
        'documentation.json', 'forum_receipt.json']]
    save('final_verification.json', dict(all_passed=True, independent_global_D2=independent,
        target_calibrator_calls=34, target_call_roles=roles, all_candidate_gates_pass=result['all_gates_pass'],
        F3c_original_csv_unchanged=True, files={str(p.relative_to(ROOT)): sha(p) for p in paths},
        limit='Comprobacion propia de IA; sin nueva muestra, nuevos sorteos ni garantia privada.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['source', 'final'])
    args = parser.parse_args()
    source() if args.mode == 'source' else final()
