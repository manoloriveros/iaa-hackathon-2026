"""Atribución del adverso GLM y soporte marginal, sin nuevos precios o ajustes.

Los niveles perfilados usan respuestas retenidas: son oráculos de diagnóstico.
No son factores de calibración admisibles ni evidencia privada independiente.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
P11 = BASE/'P11_GLM_fuente_20261026'; P12 = BASE/'P12_validacion_GLM_20261026'
OUT = BASE/'P13_atribucion_GLM_20261026'
PLAN = R/'registro/semana2_atribucion_GLM_privada_plan.json'
INDEX = R/'registro/semana2_atribucion_GLM_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import TweedieRegressor
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

sp = importlib.util.spec_from_file_location('p13_state', R/'herramientas/ablar_exposicion_fuente_P9.py')
state = importlib.util.module_from_spec(sp); sp.loader.exec_module(state); w = state.w
LINES = ['motor', 'buildings', 'contents']; MISSING = '__P11_MISSING__'; OTHER = '__P11_OTHER__'


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def aggregate_loss(y, mu):
    assert np.isfinite(y).all() and (y >= 0).all() and np.isfinite(mu).all() and (mu > 0).all()
    root = np.sqrt(mu)
    A = math.fsum((y/root).tolist()); B = math.fsum(root.tolist()); C = math.fsum(np.sqrt(y).tolist())
    loss = 4*A+4*B-8*C
    best = 8*math.sqrt(A*B)-8*C
    level = 4*(math.sqrt(A)-math.sqrt(B))**2
    assert math.isclose(loss, best+level, rel_tol=2e-12, abs_tol=1e-7)
    direct = math.fsum((4*y/root+4*root-8*np.sqrt(y)).tolist())
    external = mean_tweedie_deviance(y, mu, power=1.5)*len(y)
    assert math.isclose(loss, direct, rel_tol=2e-12, abs_tol=1e-7)
    assert math.isclose(loss, external, rel_tol=2e-12, abs_tol=1e-7)
    scalar = A/B
    derivative = -4*A/scalar+4*B
    assert abs(derivative)/max(1., 4*B) < 2e-12
    # Profiled allocation is invariant to rescaling. No rescaled row prices are made.
    for c in [.7, 1.3]:
        a2, b2 = A/math.sqrt(c), B*math.sqrt(c)
        assert math.isclose(a2*b2, A*B, rel_tol=3e-15)
    return {'A': A, 'B': B, 'C': C, 'original_loss': loss, 'profiled_loss': best,
            'level_penalty': level, 'oracle_scalar_inadmissible': scalar}


def contrast(frame):
    y = frame.T0.to_numpy(float)
    old = aggregate_loss(y, frame.old_nominal.to_numpy(float))
    new = aggregate_loss(y, frame.new_nominal.to_numpy(float))
    den = 8*(math.sqrt(len(y)*math.fsum(y.tolist()))-math.fsum(np.sqrt(y).tolist()))
    assert den > 0
    total = (old['original_loss']-new['original_loss'])/den
    allocation = (old['profiled_loss']-new['profiled_loss'])/den
    level = (old['level_penalty']-new['level_penalty'])/den
    assert abs(total-allocation-level) < 1e-11
    return {'rows': len(frame), 'positive_cost_rows': int(np.count_nonzero(y > 0)),
            'delta_total': total, 'delta_profiled_allocation': allocation, 'delta_level_penalty': level,
            'best_possible_new_scalar_vs_fixed_old_delta': (old['original_loss']-new['profiled_loss'])/den,
            'oracle_level_still_below_fixed_old': new['profiled_loss'] > old['original_loss']+1e-8,
            'original': old, 'GLM': new, 'null_deviance': den,
            'oracle_scalars_admissible': False, 'not_pure_ranking_or_causal_allocation': True}


def synthetic():
    y = np.array([0., 4., 0., 25., 1., 0., 10., 3.])
    f = pd.DataFrame({'T0': y, 'old_nominal': [1., 2., 1., 20., 1., 1., 8., 3.],
                      'new_nominal': [2., 4., 1., 15., 2., 1., 9., 3.]})
    c = contrast(f)
    assert abs(c['delta_total']-c['delta_profiled_allocation']-c['delta_level_penalty']) < 1e-12
    return {'decomposition_two_loss_methods_and_scalar_derivative': True,
            'profiled_allocation_scale_invariance': True, 'synthetic_model_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(state.PHASE).get('active_jobs') and not w.read(state.PHASE).get('active_execution')
    OUT.mkdir()
    paths = [Path(__file__), Path(state.__file__), P12/'report.json', P12/'replay_report.json']
    scopes = []
    for cohort in ['POOLED', 'TRANSFER']:
        path = P12/(cohort+'_prices.parquet'); paths.append(path)
        meta = pd.read_parquet(path, columns=['row_id', 'line', 'year', 'new_business'])
        assert meta.row_id.is_unique and meta.year.isin([2023, 2024]).all()
        scopes.append({'cohort': cohort, 'scope': 'GLOBAL'})
        for line, year, nb in sorted(meta.groupby(['line', 'year', 'new_business']).groups):
            scopes.append({'cohort': cohort, 'scope': 'CELL', 'line': line, 'year': int(year), 'NB': int(nb)})
    assert len(scopes) == 20
    for line in LINES:
        paths += [P11/line/'model.json', P11/line/'fit_record.json']
        for market in ['s1', 's2']:
            paths += [HOME/f'matrix_{market}_{line}.parquet', HOME/f'rows_{market}_{line}.parquet']
    plan = {'author': 'Codex', 'utc': utc(), 'hypothesis': 'The P12GLMloss may reflect allocation, level or marginal feature support; determine which before another source recipe.',
            'math': 'A=sum(y/sqrt(mu)),B=sum(sqrt(mu)),C=sum(sqrt(y));D=4A+4B-8C; inf_scalarD=8sqrt(AB)-8C; level=4(sqrt(A)-sqrt(B))^2; oracle_scalar=A/B.',
            'interpretation': 'Compare profiled allocation for both algorithms and also new oracle versus fixed reference. Worse profiled allocation alone does not prove that no scalar can beat an unprofiled reference.',
            'scope': 'Nominal saved P12prices only:2global+18line/year/businesscells. No rebootstrap, stress rerun, trim, new model/query or price vector.',
            'support': 'Source2021-2024and emerging2023-2025covariates only, source-preprocessor metadata. Censuses by year/business and combined sourcebusiness reference; no labels in support audit.',
            'support_flags': {'target_minus_sameNBsource_missing_fraction': .05,
                              'target_minus_sameNBsource_OTHER_fraction': .05,
                              'target_minus_sameNBsource_numeric_clip_fraction': .10},
            'support_limits': 'Marginal descriptive checks cannot prove joint overlap, causal mechanism or transportability. Existing failed2025weightESS remains unchanged.',
            'budget': {'new_model_fits': 0, 'new_C0_fits': 0, 'new_calibrations': 0, 'new_inference': 0,
                       'loss_decompositions': 20, 'diagnostic_oracle_scalars_inadmissible': 40,
                       'new_predictive_price_vectors': 0, 'new_submissions': 0},
            'decision': 'No global/line-level candidate selection, oracle rescaling, penalty search or new complexity from these diagnostics alone. A further recipe must identify a concrete unresolved mechanism and be preregistered.',
            'preflight': synthetic(), 'scopes': scopes, 'sources': {w.rel(p): w.sha(p) for p in paths},
            '2024_open': True, 'private_improvement_established': False, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P13antes de calcular otra atribución:20descomposiciones nominales sobre precios P12guardados,2globales y18celdas ramo/año/negocio. '
                    'Se separa algebraicamente desviación de nivel y pérdida perfilada de asignación. Los40escalares óptimos usan respuestas retenidas: oráculos inadmisibles, no nuevos factores o precios. '
                    'También se compara el mínimo del GLMcon la referencia fija para no confundir asignación peor con imposibilidad de mejorar una referencia sin perfilar. '
                    'Se revisará soporte marginal por año/negocio con covariables fuente2021–2024y destino2023–2025, sin etiquetas o inferencias en esa auditoría. '
                    'Se fijan banderas descriptivas de5puntos porcentuales en ausentes/OTHERy10en recorte numérico, comparando fuente con mismo negocio. '
                    'No acreditan soporte conjunto ni resuelven el ESS2025fallido. Cero ajustes, C0, nuevos precios, remuestreos o envíos. '
                    'No habrá mezcla por celdas positivas ni uso predictivo de los oráculos. B00/F3c/P6y adversos intactos,2024abierto adaptativo. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P13-ATRIBUCION-PREVIO', '--asunto',
                             'P13 previo: nivel, asignación y soporte del GLM, solo artefactos guardados', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P13registered_before_diagnostics',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'decompositions': 20, 'new_fits': 0, 'forum': receipt['forum']}))


def support_audit():
    records = []
    for line in LINES:
        model = w.read(P11/line/'model.json'); prep = model['preprocessor']
        # Only preprocessing metadata is read; coefficients are never applied.
        sx = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
        tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')
        sr = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'new_business'])
        tr = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'new_business'])
        assert list(sx) == list(tx) == prep['columns'] and len(sx) == len(sr) and len(tx) == len(tr)
        assert sr.row_id.is_unique and tr.row_id.is_unique
        assert sr.year.isin([2021, 2022, 2023, 2024]).all() and tr.year.isin([2023, 2024, 2025]).all()
        source_refs = {}
        for name in prep['columns']:
            categorical = name in prep['categorical']
            if categorical:
                source_values = sx[name].astype(object).where(sx[name].notna(), MISSING).astype(str)
                observed = set(source_values.unique()); kept = set(prep['categorical'][name][:-1])
                assert prep['categorical'][name][-1] == OTHER
                values = [(sx, sr, 'SOURCE', source_values),
                          (tx, tr, 'TARGET', tx[name].astype(object).where(tx[name].notna(), MISSING).astype(str))]
            else:
                values = [(sx, sr, 'SOURCE', None), (tx, tr, 'TARGET', None)]
            for x, rows, market, strings in values:
                if categorical:
                    missing = x[name].isna().to_numpy(); other = ~strings.isin(kept).to_numpy()
                    unseen = ~strings.isin(observed).to_numpy(); low = high = np.zeros(len(x), bool)
                else:
                    a = pd.to_numeric(x[name], errors='coerce').to_numpy(float); missing = ~np.isfinite(a)
                    other = unseen = np.zeros(len(x), bool)
                    low = (~missing) & (a < prep['numeric'][name]['lo'])
                    high = (~missing) & (a > prep['numeric'][name]['hi'])
                cohorts = [(int(y), int(nb), np.asarray(ix)) for (y, nb), ix in rows.groupby(['year', 'new_business']).groups.items()]
                if market == 'SOURCE':
                    cohorts += [('ALL', int(nb), np.asarray(ix)) for nb, ix in rows.groupby('new_business').groups.items()]
                for year, nb, ii in cohorts:
                    item = {'line': line, 'market': market, 'year': str(year), 'NB': nb, 'feature': name,
                            'kind': 'categorical' if categorical else 'numeric', 'rows': len(ii),
                            'missing_fraction': float(missing[ii].mean()), 'OTHER_fraction': float(other[ii].mean()),
                            'absent_from_source_values_fraction': float(unseen[ii].mean()),
                            'below_source_clip_fraction': float(low[ii].mean()), 'above_source_clip_fraction': float(high[ii].mean()),
                            'numeric_clip_fraction': float((low[ii] | high[ii]).mean())}
                    records.append(item)
                    if market == 'SOURCE' and year == 'ALL': source_refs[(nb, name)] = item
        line_items = [z for z in records if z['line'] == line and z['market'] == 'TARGET']
        for item in line_items:
            ref = source_refs[(item['NB'], item['feature'])]
            item['missing_gap'] = item['missing_fraction']-ref['missing_fraction']
            item['OTHER_gap'] = item['OTHER_fraction']-ref['OTHER_fraction']
            item['clip_gap'] = item['numeric_clip_fraction']-ref['numeric_clip_fraction']
            item['descriptive_flag'] = item['missing_gap'] >= .05 or item['OTHER_gap'] >= .05 or item['clip_gap'] >= .10
        print(json.dumps({'support_line': line, 'features': len(prep['columns']), 'source_rows': len(sr), 'target_covariate_rows': len(tr)}), flush=True)
    return pd.DataFrame(records)


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'kind': 'P13saved_price_attribution_covariate_support',
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); state.state_execution(execution)
    old_train, old_booster, old_glmfit = lgb.train, lgb.Booster, TweedieRegressor.fit
    def reject(*a, **kw): raise AssertionError('No fit or new model inference permitted in P13')
    lgb.train = reject; lgb.Booster = reject; TweedieRegressor.fit = reject
    try:
        frames = {c: pd.read_parquet(P12/(c+'_prices.parquet')) for c in ['POOLED', 'TRANSFER']}
        results = []
        previous = w.read(P12/'report.json')
        for scope in plan['scopes']:
            f = frames[scope['cohort']]
            if scope['scope'] == 'CELL':
                f = f.loc[f.line.eq(scope['line']) & f.year.eq(scope['year']) & f.new_business.eq(scope['NB'])]
            a = contrast(f); item = {**scope, **a}; results.append(item)
            if scope['scope'] == 'GLOBAL':
                assert abs(a['delta_total']-previous['results'][scope['cohort']]['NOMINAL']['delta']) < 1e-11
        assert len(results) == 20
        dump(OUT/'loss_decomposition.json', results)
        support = support_audit(); support.to_parquet(OUT/'marginal_support.parquet', index=False)
        flagged = support.loc[support.market.eq('TARGET') & support.descriptive_flag.fillna(False)].copy()
        flagged.to_parquet(OUT/'flagged_marginal_support.parquet', index=False)
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P13saved_GLM_attribution_and_marginal_support_complete',
                  'loss_decompositions': results, 'support_rows': len(support), 'flagged_target_feature_cells': len(flagged),
                  'new_model_fits': 0, 'new_C0_fits': 0, 'new_calibrations': 0, 'new_inference': 0,
                  'diagnostic_oracle_scalars_inadmissible': 40, 'new_predictive_price_vectors': 0, 'new_submissions': 0,
                  'model_apis_blocked': True, 'oracle_scalars_admissible': False, 'joint_support_established': False,
                  'existing_futureweight_ESS_failure_resolved': False, 'new_candidate_adopted': False,
                  'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
                  'plan_sha256': w.sha(PLAN), 'goal_achieved': False,
                  'limits': ['Per-cell profile levels use retained labels, so are diagnostic oracles only.',
                             'Allocation component is scale-profiled Tweedie loss, not a pure rank metric or causal effect.',
                             'Marginal support flags do not identify the cause of loss or prove joint transportability.',
                             'Current source/target years and recipe search remain conditional/adaptive.']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'global': [{k: z[k] for k in ['cohort', 'delta_total', 'delta_profiled_allocation', 'delta_level_penalty', 'best_possible_new_scalar_vs_fixed_old_delta']} for z in results if z['scope'] == 'GLOBAL'],
                          'flagged_target_feature_cells': len(flagged), 'new_fits': 0, 'new_submissions': 0}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'next': 'Preserve attempted output and reconcile before repeating unchanged diagnostics'})
        raise
    finally:
        lgb.train, lgb.Booster, TweedieRegressor.fit = old_train, old_booster, old_glmfit
        state.state_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    d = w.read(OUT/'report.json'); saved = w.read(OUT/'loss_decomposition.json')
    # Replay small aggregate formulas only; do not repeat source support census.
    errors = []
    for item in saved:
        for name in ['original', 'GLM']:
            a = item[name]; err = abs(a['original_loss']-a['profiled_loss']-a['level_penalty'])
            assert err/max(1, a['original_loss']) < 2e-12; errors.append(err)
        assert abs(item['delta_total']-item['delta_profiled_allocation']-item['delta_level_penalty']) < 1e-11
    assert len(saved) == 20 and d['diagnostic_oracle_scalars_inadmissible'] == 40
    plan = w.read(PLAN); assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P13aggregate_formula_replay_exact_tolerance',
                                  'aggregate_models_checked': 40, 'max_absolute_rounding_error': max(errors),
                                  'source_support_census_not_repeated': True, 'new_fits': 0, 'new_inference': 0,
                                  'report_sha256': w.sha(OUT/'report.json')})
    print(json.dumps({'replay': 'passed', 'aggregate_models': 40, 'new_fits': 0, 'new_inference': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
