"""Diagnóstico nuevo de P62 y del supuesto de reporte compartido entre ramos."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import argparse
import json
import math
import sys

R = Path(__file__).resolve().parents[1]; ROOT = R.parents[1]
s = importlib.util.spec_from_file_location('p63_saved_only', R/'herramientas/validar_proxy_observacion_P62.py')
p = importlib.util.module_from_spec(s); s.loader.exec_module(p)
w = p.w; q = p.q; pd = p.pd; np = p.np; BASE = p.BASE
OLD = BASE/'P55_validacion_mezcla_20261027'; NEW = p.OUT
OUT = BASE/'P63_revision_proxy_guardado_20261027'
PLAN = R/'registro/semana2_proxy_diagnostico_plan.json'
INDEX = R/'registro/semana2_proxy_diagnostico_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P63_OBSERVACION_Y_RAMOS.md'
POINTS = [30, 90, 180, 365, 730, 1095]


def utc(): return datetime.now(timezone.utc).isoformat()
def dump(path, value): return q.dump(path, value)


def deviance(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    assert np.isfinite(y).all() and np.isfinite(mu).all() and (y >= 0).all() and (mu > 0).all()
    return 4*(y/np.sqrt(mu)+np.sqrt(mu)-2*np.sqrt(y))


def summary(x):
    x = np.asarray(x, float); assert np.isfinite(x).all()
    return {str(k): float(v) for k, v in zip([0, .01, .05, .5, .95, .99, 1], np.quantile(x, [0, .01, .05, .5, .95, .99, 1]))}


def synthetic():
    # Independent library formula and scalar sums cover zeros and very different units.
    from sklearn.metrics import mean_tweedie_deviance
    y = np.array([0., .03, 3., 800., 80000.]); mu = np.array([.01, .2, 2., 500., 50000.])
    z = deviance(y, mu)
    assert math.isclose(float(z.mean()), mean_tweedie_deviance(y, mu, power=1.5), rel_tol=3e-14)
    direct = [4*(float(a)/math.sqrt(float(b))+math.sqrt(float(b))-2*math.sqrt(float(a))) for a, b in zip(y, mu)]
    assert np.array_equal(z, direct)
    u0 = np.array([100., 300., 70.]); u1 = np.array([110., 270., 90.]); q0 = np.array([.7, .8, .5]); q1 = np.array([.8, .6, .4])
    assert np.allclose((u1*q1)/(u0*q0), (u1/u0)*(q1/q0), rtol=1e-15)
    return {'tweedie_library_and_independent_scalar_formula': True, 'price_q_ratio_identity': True,
        'new_real_fits': 0, 'new_model_applications': 0, 'new_resampling': 0}


def prepare():
    assert not PLAN.exists() and not OUT.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    for folder in [OLD, NEW]:
        assert w.read(folder/'replay_report.json')['report_sha256'] == w.sha(folder/'report.json')
        assert w.read(folder/'completion_receipt.json')['report_sha256'] == w.sha(folder/'report.json')
    p.m.check_sources(w.read(p.PLAN))
    OUT.mkdir(); dump(OUT/'synthetic.json', synthetic())
    paths = [Path(__file__), p.PLAN, q.SOURCE_CLAIMS, p.u.PLAN, p.u.OUT/'report.json', OUT/'synthetic.json']
    for folder in [OLD, NEW]:
        paths += [folder/name for name in ['report.json', 'replay_report.json', 'completion_receipt.json', 'POOLED_prices.parquet']]
    for line in q.LINES:
        for outer in range(5):
            paths += [p.u.OUT/f'input_{line}_{outer}.parquet', p.m.REPORTING/f'outer{outer}/target_{line}.parquet']
            for folder in [OLD, NEW]: paths += [folder/f'{line}_{outer}/learning.json', folder/f'{line}_{outer}/committed.json']
    paths += [p.m.REPORTING/'outer0/cost_curves.json']
    plan = {'author': 'Codex', 'utc': utc(), 'scope': 'NEW saved P55/P62 comparison and shared-line reporting assumption; no repeat of P46 or other unchanged diagnostics',
        'prior_outcome_exposure': 'P62 pooled/scenario/cell summaries already inspected. This is explicitly adaptive, not a blind test or an independent confirmation.',
        'questions': ['Is the P62-vs-P55 point recovery broad across existing folds/years/business cells and groups? Reconcile the exact price/q multiplicative change without new counterfactual prices.',
            'Do shared peril names conceal different mature-developed line-specific reporting mixes? Fixed1095day conditional summaries only, not new production CDFs or emerging ultimate identification.'],
        'frozen_analysis': {'point_comparisons': 'All5 saved scenarios, same109296rows/labels/reference, exact difference of saved D2 contrasts. No new intervals.',
            'cohorts': 'All line/year/NB cells and all5folds. Existing cells only; no pruning or selection.',
            'concentration': 'Group positive and negative contribution masses, fixed top1/5/10 shares. No deletion/leave-out score or pricing decision.',
            'ratios': 'Saved ultimate and q_NOMINAL ratios; percentiles0,1,5,50,95,99,100. Multiplicative row identity and scalar sum check.',
            'source_reporting': 'Accepted original10character developed claims; source-only loss window>=1095; positive net; report delay<=1095; fixed source P50outer0peril p995 caps. Weighted fractions at '+str(POINTS)+'days by line/peril. Conditional on reported within1095 and current incurred marks; not ultimate or truncation-corrected target CDF.',
            'source_comparisons': 'All shared-peril line pairs, no selected significance or support threshold; raw count and effective weight count reported.'},
        'criterion': 'Exact row/key/reference/sum/formula identities must pass. No admission or threshold relaxation from descriptive points. Even a broad recovery does not establish private gain. Any later line-specific curve proposal needs a separate standard-model recipe and unchanged complete validation gates.',
        'budget': {'new_price_fits': 0, 'new_price_model_applications': 0, 'new_production_CDF_fits': 0, 'new_source_fits': 0, 'new_resampling': 0, 'new2025inference': 0, 'new_submissions': 0},
        'sources': {w.rel(path): w.sha(path) for path in paths}, '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P63registra revisión nueva y finita, después de conocer el resumenP62: comparar solo artefactos P55/P62, cinco escenarios y todas las celdas/folds, contribuciones por grupos y cociente precio*q. No crear precios contrafactuales, ajustar o remuestrear. Además revisar el supuesto P50de una curva por nombre de peril compartido entre ramos mediante fracciones descriptivas de siniestros desarrollados maduros, condicionadas a reporte antes de1095días; no son CDFúltima emergente ni prueba causal. Cero modelos aplicados/ajustados, nuevas curvas productivas,2025o envíos. No admitir ni retirar candidatos por esta revisión. B00conservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P63registered_before_new_saved_comparison', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': q.post(body, 'COD-S2-20261027-PRIVADA-P63-REVISION-PREVIO', 'P63: comparación nueva de observación y supuesto entre ramos')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN); p.m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    old = pd.read_parquet(OLD/'POOLED_prices.parquet'); new = pd.read_parquet(NEW/'POOLED_prices.parquet')
    for name in ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0', 'old_nominal']:
        assert np.array_equal(old[name], new[name]), name
    assert new.row_id.is_unique and len(new) == 109296
    denominator = math.fsum(deviance(new.T0, np.full(len(new), float(new.T0.mean()))).tolist())
    paired = (deviance(new.T0, old.new_nominal)-deviance(new.T0, new.new_nominal))/denominator
    assert math.isclose(math.fsum(paired.tolist()), w.read(NEW/'report.json')['results']['POOLED']['NOMINAL']['delta']-w.read(OLD/'report.json')['results']['POOLED']['NOMINAL']['delta'], abs_tol=1e-13)
    f = new[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy(); f['paired_delta_global'] = paired
    extra = []; levels = []
    for line in q.LINES:
        for outer in range(5):
            h = pd.read_parquet(p.u.OUT/f'input_{line}_{outer}.parquet')
            h = h.loc[h.is_held, ['row_id', 'year', 'reserve', 'q_NOMINAL']].copy()
            z = pd.read_parquet(p.m.REPORTING/f'outer{outer}/target_{line}.parquet').set_index('row_id')
            assert np.array_equal(z.loc[h.row_id, 'year'], h.year)
            h['q_old'] = z.loc[h.row_id, 'q_A1R'].to_numpy(float); extra.append(h)
            for folder in [OLD, NEW]:
                receipt = w.read(folder/f'{line}_{outer}/committed.json')
                assert all(w.sha(ROOT/path) == value for path, value in receipt['outputs'].items())
            a = w.read(OLD/f'{line}_{outer}/learning.json'); b = w.read(NEW/f'{line}_{outer}/learning.json')
            assert a['fit_row_ids_digest'] == b['fit_row_ids_digest'] and a['fit_groups_digest'] == b['fit_groups_digest']
            levels.append({'line': line, 'outer': outer, 'component_level_ratios': {key: b['components'][key]['level']/a['components'][key]['level'] for key in ['A1S', 'T2b']}})
    x = pd.concat(extra).set_index('row_id').loc[f.row_id]; assert x.index.is_unique and np.array_equal(x.year, f.year)
    f['q_ratio'] = x.q_NOMINAL.to_numpy()/x.q_old.to_numpy(); f['ultimate_ratio'] = new.ultimate.to_numpy()/old.ultimate.to_numpy()
    f['observed_ratio'] = new.new_nominal.to_numpy()/old.new_nominal.to_numpy()
    assert np.allclose(f.observed_ratio, f.q_ratio*f.ultimate_ratio, rtol=2e-14)
    for pos in np.linspace(0, len(f)-1, 31, dtype=int):
        scalar = float(f.q_ratio.iloc[pos])*float(f.ultimate_ratio.iloc[pos]); assert math.isclose(scalar, float(f.observed_ratio.iloc[pos]), rel_tol=2e-14)
    cells = []
    for keys, z in f.groupby(['line', 'year', 'new_business'], sort=True):
        cells.append({'line': keys[0], 'year': int(keys[1]), 'NB': int(keys[2]), 'rows': len(z), 'paired_delta_global': math.fsum(z.paired_delta_global.tolist()),
            'q_ratio': summary(z.q_ratio), 'ultimate_ratio': summary(z.ultimate_ratio)})
    assert math.isclose(math.fsum(z['paired_delta_global'] for z in cells), math.fsum(paired.tolist()), abs_tol=1e-14)
    folds = {str(key): math.fsum(z.paired_delta_global.tolist()) for key, z in f.groupby('fold')}
    groups = f.groupby('group_id').paired_delta_global.sum(); masses = {}
    for name, vec in [('positive', groups[groups > 0].sort_values(ascending=False)), ('negative', (-groups[groups < 0]).sort_values(ascending=False))]:
        total = math.fsum(vec.tolist()); masses[name] = {'groups': len(vec), 'mass': total,
            'top_shares': {str(k): float(vec.iloc[:k].sum()/total) if total else None for k in [1, 5, 10]}}
    assert math.isclose(masses['positive']['mass']-masses['negative']['mass'], math.fsum(paired.tolist()), abs_tol=1e-14)
    scenarios = []
    for name in p.m.e.NAMES:
        key = 'new_nominal' if name == 'NOMINAL' else name+'_new'
        y = new.T0.to_numpy(float).copy()
        if name in ['RESERVE075', 'RESERVE125']: y += (-.25 if name == 'RESERVE075' else .25)*x.reserve.to_numpy()
        den = math.fsum(deviance(y, np.full(len(y), float(y.mean()))).tolist())
        point = math.fsum((deviance(y, old[key])-deviance(y, new[key])).tolist())/den
        saved = w.read(NEW/'report.json')['results']['POOLED'][name]['delta']-w.read(OLD/'report.json')['results']['POOLED'][name]['delta']
        assert math.isclose(point, saved, abs_tol=1e-13)
        scenarios.append({'scenario': name, 'P62_minus_P55_point': point, 'new_interval': None})
    f.to_parquet(OUT/'paired_rows.parquet', index=False)
    # New question: common-name line pooling. Fixed-horizon descriptive ratios, NOT production fitting.
    source = q.source_claims(); source['window'] = (q.CUT-pd.to_datetime(source.loss_date)).dt.days
    source['delay'] = (pd.to_datetime(source.report_date)-pd.to_datetime(source.loss_date)).dt.days
    source = source.loc[(source.window >= 1095)&(source.delay <= 1095)&(source.net > 0)].copy()
    caps = {z['peril']: z['cap_CDF_weight_p995'] for z in w.read(p.m.REPORTING/'outer0/cost_curves.json')['records']}
    shared = {peril for peril in caps if sum(peril in q.PERILS[line] for line in q.LINES) > 1}
    source = source.loc[source.peril.isin(shared)]
    rows = []
    for (line, peril), z in source.groupby(['line', 'peril'], sort=True):
        weight = np.minimum(z.net.to_numpy(float), caps[peril]); total = math.fsum(weight.tolist())
        fractions = {str(t): math.fsum(weight[z.delay.to_numpy() <= t].tolist())/total for t in POINTS}
        assert all(0 <= value <= 1 for value in fractions.values()) and fractions['1095'] == 1.
        rows.append({'line': line, 'peril': peril, 'claims': len(z), 'capped_cost': total, 'cost_weight_ESS': total**2/math.fsum((weight**2).tolist()), 'fractions_by_day': fractions})
    contrasts = []
    for peril in sorted(shared):
        strata = [z for z in rows if z['peril'] == peril]
        for j, one in enumerate(strata):
            for two in strata[j+1:]:
                contrasts.append({'peril': peril, 'line_one': one['line'], 'line_two': two['line'], 'claims': [one['claims'], two['claims']],
                    'cost_weight_ESS': [one['cost_weight_ESS'], two['cost_weight_ESS']],
                    'fraction_one_minus_two': {str(t): one['fractions_by_day'][str(t)]-two['fractions_by_day'][str(t)] for t in POINTS}})
    p.m.check_sources(plan)
    report = {'author': 'Codex', 'utc': utc(), 'plan_sha256': w.sha(PLAN), 'rows': len(f), 'paired_delta_global': math.fsum(paired.tolist()),
        'scenarios': scenarios, 'folds': folds, 'cells': cells, 'group_masses': masses, 'component_levels': levels,
        'source_mature_conditional1095': rows, 'source_shared_line_contrasts': contrasts,
        'identity_checks': ['keys_labels_reference_exact', 'same_training_row_group_digests', 'all_saved_model_output_hashes', 'ratio_factorization', 'scalar_formula', 'all5saved_delta_differences', 'cell_and_group_additivity'],
        'limits': ['Saved paired point differences have no new confidence interval and are adaptive. Relearning price calibration under the changed qprevents a pure fixed-price observation effect claim.',
            'Mature developed conditional1095fractions do not identify emerging delay distributions, unreported tail or ultimate marks. Incurred maturity, valuation/calendar and market confounding remain.',
            'Descriptive heterogeneity does not admit a candidate or require line-stratified curves to improve. Separate registration and complete protected validation would be needed.'],
        **plan['budget'], 'B00_all_alternatives_preserved': True, '2024_open': True, 'goal_achieved': False}
    dump(OUT/'report.json', report); print(json.dumps({'paired_delta_global': report['paired_delta_global'], 'folds': folds, 'group_masses': masses, 'source_contrasts': contrasts}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); p.m.check_sources(w.read(PLAN))
    next_unit = 'Review P63source line-specific conditional delay contrasts and existing target support before preregistering a line/peril-specific standard reporting curve. Do not select peril/cell overrides, change price capacity, tune public score or treat P62point as admission. No new CSV yet.'
    text = '# P63: comparación guardada y reporte entre ramos\n\nCodex, '+utc()+'. La comparación usa únicamente los nuevos artefactosP62yP55 y documenta que sus costes, claves, grupos y referencia coinciden. El cambio deq también vuelve a estimar las calibraciones de precio: no es un efecto causal de observación con precios fijos.\n\n'
    text += f"P62menosP55, punto global={d['paired_delta_global']:+.7f}. No se calculó un nuevo intervalo. Las cinco diferencias de escenarios, identidad precio*q, sumas por celda/grupo y fórmula Tweedie por otro método coincidieron. Los15ámbitos conservan exactamente las mismas claves de ajuste.\n\n"
    text += 'Concentración: '+json.dumps(d['group_masses'])+'.\n\n'
    text += 'La revisión del supuesto de nombres de peril compartidos usa solo siniestros desarrollados con al menos1095días de ventana, positivos y reportados antes de1095. Pesos de coste con los topesP50ya guardados; fracciones descriptivas, sin ajustar nuevas curvas productivas.\n\n'
    text += '| Peril | Ramos | N por ramo | ESS de coste | Diferencia F(90d) | Diferencia F(365d) |\n|---|---|---|---|---|---|\n'
    for z in d['source_shared_line_contrasts']:
        text += f"| {z['peril']} | {z['line_one']} / {z['line_two']} | {z['claims']} | {[round(v, 1) for v in z['cost_weight_ESS']]} | {z['fraction_one_minus_two']['90']:+.4f} | {z['fraction_one_minus_two']['365']:+.4f} |\n"
    text += '\nSon distribuciones condicionadas de una fuente desarrollada madura, con costes a su fecha de valoración; no identifican reporte o severidad última emergente. Sin prueba causal, significancia nueva ni evidencia privada. El fallo de las guardasP62sigue vigente; no hay CSV nuevo admitido. Cero ajustes/aplicaciones de modelos, curvas productivas nuevas, remuestreo,2025o envíos. B00/F3cyalternativas conservados,2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P63saved_comparison_and_shared_line_reporting_review_complete', 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'paired_delta_global': d['paired_delta_global'], 'next_unit': next_unit, **w.read(PLAN)['budget'],
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False,
        'forum': q.post(body, 'COD-S2-20261027-PRIVADA-P63-REVISION-RESULTADO', 'P63: recuperación media, límites y reporte entre ramos')}
    archive = R/'privado'/('corte_P63_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive)
    for path, key in [(R/'registro/semana2_mision017_fase2_actual.json', 'private_P63'), (R/'registro/semana2_mision_privada_actual.json', 'P63')]: w.update(path, {key: receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P63=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P63: observación guardada y ramos\n\nCodex, '+receipt['utc']+'. Comparación nuevaP62/P55yfracciones maduras desarrolladas por ramo/peril, sin aplicar o ajustar modelos ni curvas productivas, remuestrear o enviar. No admite candidatos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_proxy_diagnostic_index': w.rel(INDEX), 'week_2_private_proxy_diagnostic_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('mode', choices=['prepare', 'run', 'close']); args = ap.parse_args()
    with p.m.e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'close': close}[args.mode]()
