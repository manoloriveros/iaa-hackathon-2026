"""Reconstrucción acotada de la receta creíble existente; cero ajustes o etiquetas nuevas."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

BASE = R / 'privado/semana2'
OUT = BASE / 'mision017_fase2/calibracion_F2_creible_20261025_v1'
PLAN = R / 'registro/semana2_mision017_calibracion_F2_plan_v1.json'
DOC = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025'
F2 = BASE / 'claude_mision017_20261025/F2_ncb_previos_2025.csv'
INFO = DOC / 'final_info_3puntos.json'
LEVEL = BASE / 'claude_validacion_nocturna_20261023/sonda_segmento/preinscripcion.json'
LIVE = BASE / 'mision017_fase2/estado_publico_20261026_v1/receipt.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()
now = lambda: datetime.now(timezone.utc).isoformat()

def dump(path, obj):
    with path.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)

def transform(base, frame, params):
    cells = (frame.line + '_' + frame.new_business.astype(int).astype(str)).to_numpy()
    exposure = frame.exposure_calendar.to_numpy(float)
    assert (exposure > 0).all()
    out = base.copy(); transitions = {}
    for cell, effect in params['forma'].items():
        mask = cells == cell; a = effect['a_cred']; assert mask.any() and .3 <= a <= 1.8
        e = exposure[mask]; rate = out[mask] / e; mean = out[mask].sum() / e.sum()
        changed = e * mean * (rate / mean) ** a
        shaped = changed * out[mask].sum() / changed.sum()
        out[mask] = shaped * effect['razon_cred']
        transitions[cell] = {'a': a, 'historical_level_ratio': effect['razon_cred'],
            'outside_measured_public_shape_range': not min(x[0] for x in effect['puntos']) <= a <= max(x[0] for x in effect['puntos'])}
    for cell, factor in params['nivel']['cred'].items():
        mask = cells == cell; out[mask] *= factor / params['nivel']['g']
    assert np.isfinite(out).all() and (out > 0).all()
    return out, transitions

def synthetic():
    n = 120; rng = np.random.default_rng(43)
    frame = pd.DataFrame({'line': np.tile(['motor', 'buildings', 'contents'], 40),
        'new_business': (np.arange(n) // 3) % 2, 'exposure_calendar': rng.uniform(.05, 1., n)})
    base = rng.uniform(20, 1000, n)
    params = {'forma': {}, 'nivel': {'g': 1., 'cred': {f'{l}_{b}': 1. for l in frame.line.unique() for b in [0, 1]}}}
    out, _ = transform(base, frame, params); assert np.array_equal(out, base)
    params['forma']['motor_1'] = {'a_cred': 1.2, 'razon_cred': 1., 'puntos': [[.8, 0.], [1., 0.], [1.3, 0.]]}
    out, _ = transform(base, frame, params); mask = frame.line.eq('motor') & frame.new_business.eq(1)
    assert abs(out[mask].sum() - base[mask].sum()) < 1e-8
    poison, _ = transform(base, frame.assign(T0=-1e30), params); assert np.array_equal(out, poison)
    dump(OUT / 'synthetic.json', {'pass': True, 'identity': True, 'shape_conserves_cell_total_before_level_ratio': True,
        'label_payload_unused': True, 'new_fits': 0})

def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir(parents=True); synthetic()
    sources = [Path(__file__), INFO, LEVEL, LIVE, F2, DOC / 'sigma_forma.json', DOC / 'recibos_reales_20261026.json',
        DOC / 'sondas_F2_info.json', DOC / 'PREINSCRIPCION_FINAL.json', DOC / 'codigo/construir_final.py',
        BASE / 'mision017_fase2/tanda2_20261025_v1/oof_2023_2024.parquet']
    sources += [ROOT / f'Hackaton/Semana 2/Datos/emerging/test_{line}.parquet' for line in ['motor', 'buildings', 'contents']]
    sources += [ROOT / 'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet']
    info = read(INFO); assert info['final_creible_2025.csv']['sha256'] == '1a003d8682f1fcd71ad4a44f59f785d394488fc1cc95e60722f418b04c30ef29'
    plan = {'id': 'S2-MISION017-F2-CREIBLE-REPLAY-v1', 'author': 'Codex', 'utc': now(),
        'purpose': 'Audit and reproduce the existing calibrated F2 proposal and its test-portfolio scope; no new model/parameter search',
        'recipe_author': 'Claude', 'replay_and_audit_author': 'Codex', 'base_F2_sha256': sha(F2),
        'fixed_parameters': rel(INFO), 'expected_CSV_sha256': info['final_creible_2025.csv']['sha256'],
        'formula': 'F2 -> cell power shape, preserving its cell total -> historical shape-level ratio -> existing credible cell factor/g. Inclusive days/365 full precision.',
        'checks': ['Match official processed public receipts to the existing parameter audit, never read private_score',
            'Recompute the existing five cell calibration identities and three predeclared parabolas; compare to fixed parameters without choosing new ones',
            'Exact CSV SHA replay, official template ID order/schema, finite positive predictions, cell totals and independent log-form arithmetic',
            'Report target2025 vs historic2023/2024 composition by line/business/exposure bins fixed at .5/.9; do not reweight/select failed models after the fact',
            'Report extrapolation and sampling/market-shift uncertainty; no claim of intact independent confirmation'],
        'limits': ['Motor new-business shape1.3715 extrapolates beyond measured points .6/.8/1; not yet confirmed at1.4',
            'Credibility depends on historical public/private simulations and common market snapshots, not professional independent review',
            'Replay does not recover missing corrected A1 source weights or certify complete historical F2 training',
            'Public-score calibration is adaptive; it does not supply individual hidden2025claim labels',
            'The full-strength alternative is not constructed or chosen',
            'Goal0.17 is unproven and predicted public performance is not a processed receipt'],
        'budget': {'model_fits': 0, 'C0_fits': 0, 'new_parameter_fits': 0, 'replay_candidate_CSV': 1, 'submissions_in_this_unit': 0},
        'subsequent_submission': 'Separate evidence-based admission before any upload. At most one initial candidate; preserve remaining slot. No old queue, no final selection.',
        'sources': {rel(p): sha(p) for p in sources}, 'B00_preserved': True, 'all_alternatives_preserved': True,
        '2024_open': True, '2024_is_adaptive_development': True, 'no_automatic_submission': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Se registra una unidad sin ajustes: conciliar y reproducir el candidato creíble de F2 que ya propuso Claude, '
        'con sus parámetros intactos y autoría conservada. No se ejecuta su productor histórico ni se recalcula C0.\n\n'
        'Se comprobarán las identidades numéricas con recibos públicos oficiales ya consultados, el CSV esperado por SHA, las filas de la plantilla y la exposición original sin redondear. '
        'También se documentará la composición de 2025 frente a 2023–2024. No se buscarán otras ponderaciones a posteriori para admitir los GLM adversos.\n\n'
        'La pendiente de motor nuevo extrapola los tres puntos públicos medidos. Es una incertidumbre real; su previsión no se presentará como score recibido ni validación independiente. '
        'Se conserva la alternativa plena sin construirla ni adoptarla. Presupuesto: cero ajustes, un replay de CSV y cero envíos en esta unidad. '
        'Cualquier envío requiere una decisión separada sustentada en la evidencia, como máximo un candidato inicial y conservando el otro cupo. '
        'Plan: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-CALF2-REPLAY-PREVIO', '--asunto',
        'Auditoría del candidato creíble de F2 y de la cartera 2025, sin ajuste ni envío', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'new_fits': 0, 'submissions': 0}))

def parameter_audit(info, plan):
    level = read(LEVEL); live = read(LIVE)
    rows = {r['filename'].removesuffix('.zip'): r for r in live['own_team_records'] if r['status'] == 'COMPLETE'}
    scores = {r['sha256']: r['d2'] for r in read(DOC / 'recibos_reales_20261026.json')}
    assert rows['F2_ncb_previos_2025']['public_score'] == scores[sha(F2)] == .16033
    g = level['base']['g']; assert g == info['nivel']['g']
    dF = rows['final_sonda_global_2025']['public_score']; lo, hi = level['d2_F_intervalo_redondeo']
    assert lo - 5e-6 <= dF <= hi + 5e-6
    A = {}; B = {cell: level['base']['beta_B'] * z['cuota_raiz_mu'] for cell, z in level['celdas'].items()}
    for filename, z in level['sondas'].items():
        score = rows[filename.removesuffix('.csv')]['public_score']; assert score == scores[z['sha256']]
        cell = z['celda']; k = z['K']
        A[cell] = (dF - score - B[cell] * (np.sqrt(g * k) - np.sqrt(g))) / ((g * k) ** -.5 - g ** -.5)
    A[level['celda_deducida']] = level['base']['beta_A'] - sum(A.values())
    for cell, z in level['celdas'].items():
        optimal = A[cell] / B[cell]
        credible = float(np.clip((optimal / level['base']['c_optimo_global']) ** z['Z'], .75, 1.33)) * g
        assert abs(optimal - info['nivel']['c_opt'][cell]) < 1e-12
        assert abs(credible - info['nivel']['cred'][cell]) < 1e-12
    sigma = read(DOC / 'sigma_forma.json'); shape_checks = []
    for cell, z in info['forma'].items():
        points = z['puntos']; coef = np.polyfit([p[0] for p in points], [p[1] for p in points], 2)
        vertex = -coef[1] / (2 * coef[0]); a = 1 + z['Z'] * (vertex - 1)
        assert coef[0] < 0 and abs(vertex - z['vertice']) < 1e-10 and abs(a - z['a_cred']) < 1e-10
        assert sigma[cell]['Z_tau0.25'] == z['Z']
        for power, score in points:
            name = 'F2_ncb_previos_2025' if power == 1 else f'sonda_F2_{cell}_a{int(round(power * 10)):02d}'
            assert rows[name]['public_score'] == score
        shape_checks.append({'cell': cell, 'existing_parabola_reproduced': True, 'a_credible': a,
            'extrapolates': not min(p[0] for p in points) <= a <= max(p[0] for p in points)})
    return {'existing_level_identities_reproduced': True, 'shape': shape_checks,
        'public_receipts_are_adaptive_calibration_not_independent_validation': True, 'new_parameter_fits': 0}

def produce():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    assert not (OUT / 'report.json').exists()
    for p, digest in plan['sources'].items(): assert sha(ROOT / p) == digest, p
    info = read(INFO); audit = parameter_audit(info, plan)
    csv = pd.read_csv(F2, dtype={'row_id': str}); assert sha(F2) == plan['base_F2_sha256']
    tables = []
    for line in ['motor', 'buildings', 'contents']:
        f = pd.read_parquet(ROOT / f'Hackaton/Semana 2/Datos/emerging/test_{line}.parquet',
            columns=['row_id', 'new_business', 'period_start', 'period_end'])
        f['line'] = line
        f['exposure_calendar'] = ((pd.to_datetime(f.period_end) - pd.to_datetime(f.period_start)).dt.days + 1) / 365
        tables.append(f)
    f = csv[['row_id']].merge(pd.concat(tables, ignore_index=True), on='row_id', validate='one_to_one')
    assert np.array_equal(f.row_id, csv.row_id)
    sample = pd.read_parquet(ROOT / 'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet')
    assert list(sample) == ['row_id', 'prediction'] and sample.row_id.is_unique and len(sample) == len(csv) == 209063
    assert np.array_equal(sample.row_id.astype(str), csv.row_id)
    base = csv.prediction.to_numpy(float); pred, transitions = transform(base, f, info)
    poison, _ = transform(base, f.assign(T0=-1e30, reserve=-1e30), info); assert np.array_equal(pred, poison)
    cells = (f.line + '_' + f.new_business.astype(int).astype(str)).to_numpy()
    # Rebuild shape with a logarithmic expression rather than the power formula.
    independent = base.copy()
    for cell, z in info['forma'].items():
        mask = cells == cell; x = np.log(base[mask]) - np.log(f.exposure_calendar.to_numpy()[mask])
        log_changed = np.log(base[mask]) + (z['a_cred'] - 1) * x
        log_changed -= log_changed.max(); changed = np.exp(log_changed)
        independent[mask] = changed * base[mask].sum() / changed.sum() * z['razon_cred']
    independent *= np.array([info['nivel']['cred'][cell] / info['nivel']['g'] for cell in cells])
    assert np.allclose(pred, independent, rtol=1e-12, atol=1e-9)
    result = csv.copy(); result['prediction'] = pred
    path = OUT / 'final_creible_2025.csv'; assert not path.exists()
    result.to_csv(path, index=False, float_format='%.6f', lineterminator='\n')
    assert sha(path) == plan['expected_CSV_sha256'], 'Preserve this output and diagnose; never silently change the expected hash'
    assert abs(pred.sum() - info['final_creible_2025.csv']['total']) < .01
    historical = pd.read_parquet(BASE / 'mision017_fase2/tanda2_20261025_v1/oof_2023_2024.parquet')
    rows = []
    for year in [2023, 2024, 2025]:
        data = f if year == 2025 else historical.loc[historical.year.eq(year)].rename(columns={'exposure': 'exposure_calendar'})
        data = data.copy(); data['duration_bin'] = np.where(data.exposure_calendar < .5, 'short_<0.5', np.where(data.exposure_calendar < .9, 'medium_0.5_<0.9', 'long_>=0.9'))
        for (line, nb, duration), group in data.groupby(['line', 'new_business', 'duration_bin'], observed=True):
            rows.append({'year': year, 'line': line, 'new_business': int(nb), 'duration_bin': duration, 'rows': len(group),
                'share_year': len(group) / len(data), 'positive_T0': int(group.T0.gt(0).sum()) if year < 2025 else None})
    pd.DataFrame(rows).to_csv(OUT / 'cohort_composition.csv', index=False)
    totals = {cell: {'rows': int((cells == cell).sum()), 'base': float(base[cells == cell].sum()), 'candidate': float(pred[cells == cell].sum()),
        'factor': float(pred[cells == cell].sum() / base[cells == cell].sum())} for cell in sorted(set(cells))}
    nb_shares = {'2025': float(f.new_business.mean()), **{str(year): float(historical.loc[historical.year.eq(year)].new_business.mean()) for year in [2023, 2024]}}
    delta_shape_parabola = sum(np.polyval(z['coef'], z['a_cred']) - .16033 for z in info['forma'].values())
    forecast = .16033 + info['nivel']['d2_F_celda_cred'] - .15948 + delta_shape_parabola
    dump(OUT / 'report.json', {'author': 'Codex', 'utc': now(), 'recipe_author': 'Claude', 'replay_author': 'Codex',
        'status': 'exact_existing_recipe_replay_with_open_extrapolation_risk', 'parameter_audit': audit,
        'CSV': {'path': rel(path), 'sha256': sha(path), 'rows': len(csv), 'bytes': path.stat().st_size, 'total': float(pred.sum())},
        'independent_log_formula_verified': True, 'schema_and_official_id_order_exact': True, 'new_business_share': nb_shares,
        'cell_totals': totals, 'shape_transitions': transitions, 'approximate_public_forecast': forecast,
        'forecast_not_receipt': True, 'public_score_used_for_calibration_not_independent_confirmation': True,
        'historical_simulation_is_other_AI_evidence_not_professional_independent_review': True,
        'no_new_fits': True, 'new_C0_fits': 0, 'new_submissions': 0, 'not_admitted_or_promoted_by_this_replay': True,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False})
    print(json.dumps({'CSV_sha256': sha(path), 'total': float(pred.sum()), 'new_business_share': nb_shares,
        'forecast_approximate_not_receipt': forecast, 'shape_extrapolation': transitions, 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'produce']); args = parser.parse_args()
    try: register() if args.mode == 'register' else produce()
    except Exception as exc:
        if OUT.exists():
            path = OUT / ('failure_' + args.mode + '_' + datetime.now(timezone.utc).strftime('%H%M%S%f') + '.json')
            dump(path, {'utc': now(), 'mode': args.mode, 'error': type(exc).__name__, 'message': str(exc), 'new_fits': 0, 'submissions': 0})
        raise
