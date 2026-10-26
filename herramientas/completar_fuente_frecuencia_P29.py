"""Refits completos de la receta P28 aprobada solo en fuente, sin puntuar destino."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('p29_fixed_pair_helpers', R/'herramientas/fuente_frecuencia_marca_P28.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BASE = m.BASE; HOME = m.HOME; INNER = m.OUT
OUT = BASE/'P29_fuente_frecuencia_completa_20261026'
PLAN = R/'registro/semana2_fuente_frecuencia_completa_privada_plan.json'
INDEX = R/'registro/semana2_fuente_frecuencia_completa_privada_actual.json'
w = m.w; np = m.np; pd = m.pd
m.OUT = OUT; m.PLAN = PLAN; m.INDEX = INDEX


def compose(matrix, pairs):
    result = np.zeros(matrix.shape[0]); terms = []
    for frequency, mark in pairs:
        value = m.predict(matrix, frequency)*m.predict(matrix, mark)
        assert np.isfinite(value).all() and (value > 0).all()
        result += value; terms.append(value)
    assert np.isfinite(result).all() and (result > 0).all()
    sample = np.unique(np.linspace(0, len(result)-1, min(32, len(result)), dtype=int))
    independent = np.array([math.fsum(x[i] for x in terms) for i in sample])
    assert np.allclose(result[sample], independent, rtol=3e-15)
    return np.log(result)


def synthetic():
    from scipy.sparse import csr_matrix
    from scipy.special import logsumexp
    matrix = csr_matrix(np.arange(120).reshape(40, 3)/200.)
    pairs = []
    for j in range(3):
        pairs.append(({'coef': [.1, -.2, .1], 'intercept': -2.+j/10.},
            {'coef': [.05, .1, -.05], 'intercept': 6.+j/20.}))
    log_annual = compose(matrix, pairs); weights = np.linspace(.1, 1, 40)
    center = float(logsumexp(log_annual, b=weights)-np.log(weights.sum()))
    assert np.array_equal(compose(matrix[::-1], json.loads(json.dumps(pairs))), log_annual[::-1])
    assert abs(np.average(np.exp(log_annual-center), weights=weights)-1) < 2e-15
    independent = math.log(math.fsum((np.exp(log_annual)*weights).tolist())/math.fsum(weights.tolist()))
    assert abs(independent-center) < 2e-15
    return {'new_GLM_fits': 0, 'annual_peril_product_sum_scalar_verified': True,
        'JSON_and_order_exact': True, 'weighted_relative_mean_one': True,
        'center_other_method_verified': True}


def paths():
    result = [Path(__file__), Path(m.__file__), Path(m.p14.__file__), Path(m.p14.old.__file__), Path(m.p27.__file__),
        INNER/'report.json', INNER/'completion_receipt.json', INNER/'numerical_replay.json',
        R/'registro/semana2_fuente_frecuencia_marca_privada_plan.json']
    for line in m.LINES:
        result += [HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s1_{line}.parquet',
            HOME/f'matrix_s2_{line}.parquet', HOME/f'rows_s2_{line}.parquet',
            m.COUNTS/f'counts_{line}.parquet', m.LINKS/f'rkm_links_{line}.parquet']
    return result


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    prior = w.read(INNER/'report.json'); closed = w.read(INNER/'completion_receipt.json')
    assert prior['source_gate_all_pass'] and closed['source_gate_all_pass']
    assert closed['replay_sha256'] == w.sha(INNER/'numerical_replay.json')
    assert prior['plan_sha256'] == w.sha(R/'registro/semana2_fuente_frecuencia_marca_privada_plan.json')
    OUT.mkdir(); fixture = synthetic(); m.dump(OUT/'synthetic_annual.json', fixture)
    plan = {'author': 'Codex', 'utc': m.utc(), 'candidate': 'P28fixed_peril_GLMs_full_source',
        'hypothesis': 'Refit the exact source-eligible standard pair recipe on all source before evaluating transport; no new architecture or tuning from source differences.',
        'configuration': w.read(R/'registro/semana2_fuente_frecuencia_marca_privada_plan.json')['configuration'],
        'features_and_preprocessing': 'Exact P28/P14main-effects predictors and missing flags; learn same medians/clips/scales/categories using full source only. No target preprocessing.',
        'source_composition': 'One Poisson/Tweedie1.5pair per15fixed perils; sum annual frequency*mark. No cost-completion or calendar exposure multiplication in annual rate.',
        'normalization': 'Original A1Sexposure_model-weighted source mean annual rate; centered relative mean1, target calibration remains later.',
        'cache_interface': 'historical_line_three_seed.parquet compatibility name denotes ONE fixed15peril sum, not3seeds or independent validation.',
        'budget': {'full_source_GLM_fits': 30, 'new_source_baseline_constants': 0,
            'source_covariate_normalizers': 3, 'new_synthetic_fits': 0, 'new_C0_fits': 0,
            'new_target_calibrations': 0, 'new_target_scores': 0, 'new_future_inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'criteria': ['Same P28gradient<=1e-4,no convergence warning, JSON/order/manual predictor controls before consuming each saved model.',
            'Save every model before controls; reconcile each invoked attempt, do not repeat failed fits.',
            'Annual peril sum and normalization by scalar arithmetic; positive finite historical components, exact keys/years.',
            'Filter2025before transform/predict; no future inference or prices. No target admission from full-source completion.'],
        'preflight': fixture, 'sources': {w.rel(p): w.sha(p) for p in paths()},
        'limits': w.read(R/'registro/semana2_fuente_frecuencia_marca_privada_plan.json')['limits']+[
            'Source-observation objects have common ancestry including source-held groups; only coefficients/preprocessing had the prior protected new source split.',
            'All-source production fitting is legitimate but supplies no new independent validation.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    m.dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. Registro P29 antes de refits: exactamente30GLM fuente completos con '
        'la receta P28, sin variar variables, nominal alpha, familias o perils. Las '
        'penalizaciones se reescalan con los pesos de toda la fuente según la fórmula '
        'fijada, y el preprocesamiento usa solo esa fuente. Se suman tasas anuales '
        'frecuencia×marca y se centra por la exposición fuente A1S. El nombre de caché '
        'three_seed es compatibilidad: una suma fija, no tres semillas. Tres '
        'normalizadores nuevos; cero constantes de referencia nuevas, C0, '
        'calibraciones/scores destino, inferencias2025, precios o envíos. El fixture '
        'nuevo sin ajustes verifica suma, JSON/orden y centro por otro método. '
        'La observación fuente tiene ancestros comunes y su control fue condicional. '
        'Solo después se registrará el contraste completo con las guardas privadas '
        'intactas. B00/F3c/alternativas conservados,2024abierto adaptativo. Plan '
        +w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P29-FRECUENCIA-PREVIO',
        '--asunto', 'P29: refits fuente completos de la receta fija, sin cambiar criterio o puntuar destino',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': m.utc(), 'status': 'P29registered_before_full_source_refits',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    m.dump(OUT/'registration.json', receipt); m.dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'full_source_budget': 30, 'forum': receipt['forum']}))


def state(status, execution):
    archive = R/'privado'/('p29_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    keys = sorted(p.parent.name for p in OUT.glob('*/*/fit_invoked.json'))
    completed = sorted(p.parent.name for p in OUT.glob('*/*/fit_record.json'))
    cp = R/'registro/semana2_contadores_propios_actual.json'; counter = w.read(cp)
    old = counter.get('phase2_private_P29_full_pairs', {}).get('counted_keys', [])
    assert set(old).issubset(keys); extra = len(set(keys)-set(old))
    if execution is not None:
        execution = {**execution, 'script': w.rel(Path(__file__)), 'kind': 'P29full_source_pairs', 'raw_fit_driver': w.rel(Path(m.__file__))}
    current = {'author': 'Codex', 'utc': m.utc(), 'status': status, 'attempts': len(keys), 'completed': len(completed), 'execution': execution, 'output': w.rel(OUT)}
    w.update(cp, {'cumulative_price_base_fits': counter['cumulative_price_base_fits']+extra,
        'phase2_private_P29_full_pairs': {'counted_keys': keys, 'attempts': len(keys), 'completed': len(completed)}}, archive)
    w.update(INDEX, current, archive); phase = R/'registro/semana2_mision017_fase2_actual.json'; d = w.read(phase)
    jobs = [] if execution is None else [execution]
    w.update(phase, {'private_P29_source': current, 'new_price_fits': d['new_price_fits']+extra, 'active_execution': execution, 'active_jobs': jobs}, archive)
    sp = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(sp)['week_2_mission017_phase2_20261025']
    own.update(private_P29_source=current, new_price_fits=d['new_price_fits']+extra, active_jobs=jobs)
    w.update(sp, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


m.state = state


def run():
    from scipy.special import logsumexp
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    m.dump(OUT/'started.json', {'utc': m.utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    outputs = {}
    try:
        for line in m.LINES:
            folder = OUT/line; folder.mkdir()
            x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'exposure_model', 'T0_cents'])
            part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group'])
            count = pd.read_parquet(m.COUNTS/f'counts_{line}.parquet'); link = pd.read_parquet(m.LINKS/f'rkm_links_{line}.parquet')
            assert all(np.array_equal(f.row_id, rows.row_id) for f in [part, count, link])
            assert np.array_equal(rows.T0_cents, count.T0_cents_total) and rows.year.isin([2021, 2022, 2023, 2024]).all()
            prep = m.p14.fit_preprocessor(x); prep.pop('penalty', None); m.dump(folder/'preprocessor.json', prep)
            matrix, names = m.p14.transform(x, prep); pairs = []
            for peril in [z['peril'] for z in w.read(m.P27/'report.json')['by_line_peril'] if z['line'] == line]:
                n = count['N_'+peril].to_numpy(float); cost = count['T0_cents_'+peril].to_numpy(float)/100
                en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
                selected, ratio, ym, wm = m.p27.transformed_mark(n, cost, en, ec); pair = []
                for family in ['frequency', 'mark']:
                    idx = en > 0 if family == 'frequency' else selected
                    y = n[idx]/en[idx] if family == 'frequency' else ym
                    weight = en[idx] if family == 'frequency' else wm
                    alpha = .001*len(rows)/weight.sum() if family == 'frequency' else n[idx].sum()/weight.sum()
                    target = folder/f'{line}_{peril}_{family}'; target.mkdir()
                    meta = {'scope_training_row_digest': m.digest(rows.row_id), 'scope_training_group_digest': m.digest(part.source_group.unique()),
                        'fit_row_digest': m.digest(rows.loc[idx, 'row_id']), 'fit_group_digest': m.digest(part.loc[idx, 'source_group'].unique()),
                        'source_scope': 'full developed2021-2024', 'preprocessor_sha256': w.sha(folder/'preprocessor.json'), 'columns': names}
                    m.fit(target, matrix[idx], y, weight, family, alpha, meta)
                    record = w.read(target/'fit_record.json'); assert record['model_sha256'] == w.sha(target/'model.json')
                    pair.append(w.read(target/'model.json'))
                pairs.append(pair)
            log_annual = compose(matrix, pairs); weights = rows.exposure_model.to_numpy(float)
            center = float(logsumexp(log_annual, b=weights)-np.log(weights.sum()))
            brute = math.log(math.fsum((np.exp(log_annual)*weights).tolist())/math.fsum(weights.tolist()))
            assert abs(center-brute) < 2e-12 and abs(np.average(np.exp(log_annual-center), weights=weights)-1) < 2e-12
            target_rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
            target_x = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')
            keep = ~target_rows.is_test; target_rows = target_rows.loc[keep].reset_index(drop=True); target_x = target_x.loc[keep].reset_index(drop=True)
            assert target_rows.year.isin([2023, 2024]).all() and target_rows.row_id.is_unique
            tmatrix, target_names = m.p14.transform(target_x, prep); assert target_names == names
            target_log = compose(tmatrix, pairs)
            sample = np.unique(np.linspace(0, len(target_rows)-1, 32, dtype=int))
            reloaded_matrix, _ = m.p14.transform(target_x.iloc[sample], json.loads(json.dumps(prep)))
            assert np.array_equal(compose(reloaded_matrix, json.loads(json.dumps(pairs))), target_log[sample])
            target_rows['raw_log_rate'] = target_log; target_rows['log_relative_A1S'] = target_log-center
            path = OUT/f'historical_{line}_three_seed.parquet'; target_rows.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
            m.dump(folder/'application.json', {'utc': m.utc(), 'source_rows': len(rows), 'historical_rows': len(target_rows),
                'source_center': center, 'normalization_other_method_error': abs(center-brute),
                'source_relative_mean_one': True, 'JSONhistorical_pipeline_sample_exact': True,
                'one_fixed_peril_sum_not_three_seeds': True, 'new_future_inference': 0, 'output_sha256': w.sha(path)})
        assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
        assert len(list(OUT.glob('*/*/controls.json'))) == len(list(OUT.glob('*/*/fit_invoked.json'))) == 30
        report = {'author': 'Codex', 'utc': m.utc(), 'status': 'P29full_source_complete_target_pending',
            'new_source_GLM_fits': 30, 'new_source_normalizers': 3, 'new_C0_fits': 0,
            'new_target_scores': 0, 'new_target_calibrations': 0, 'new_future_inference': 0,
            'new_final_prices': 0, 'new_submissions': 0, 'outputs': outputs,
            'cache_name_not_seed_ensemble': True, 'plan_sha256': w.sha(PLAN),
            'private_improvement_established': False, 'goal_achieved': False, '2024_open': True,
            'B00_all_alternatives_preserved': True, 'limits': plan['limits']}
        m.dump(OUT/'report.json', report); state(report['status'], None)
        print(json.dumps({'status': report['status'], 'source_fits': 30, 'historical_outputs': len(outputs), 'new_target_scores': 0}), flush=True)
    finally:
        if not (OUT/'report.json').exists(): state('P29unfinished_reconcile_attempts_no_blind_refits', None)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run']); args = parser.parse_args()
    with m.threadpool_limits(limits=2): {'prepare': prepare, 'run': run}[args.mode]()
