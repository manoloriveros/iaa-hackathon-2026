"""Prepara A1R: observación agrupada por fold, sin precios o ajustes de árboles."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import sys
import subprocess

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'; BASE = R/'privado/semana2/mision017_fase2'
HOME = BASE/'A1S_nucleo_20261026_v1'; P1 = BASE/'preflight_anidado_H1_20261026_v1'
CLAIMS = R/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/claim_assignment_audit.parquet'
SOURCE_CLAIMS = ROOT/'Hackaton/Semana 1/Datos/claims.parquet'
COUNTS = BASE/'recuentos_fuente2024_v1'
OUT = BASE/'P50_reporte_agrupado_20261027'
PLAN = R/'registro/semana2_reporte_agrupado_privada_plan.json'; INDEX = R/'registro/semana2_reporte_agrupado_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P50_REPORTE_AGRUPADO_POR_FOLD.md'
sp = importlib.util.spec_from_file_location('p50_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
LINES = ['motor', 'buildings', 'contents']; CUT = pd.Timestamp('2024-12-31'); BUCKET = 7
PERILS = {'motor': ['own_damage', 'third_party_prop', 'bodily_injury', 'theft', 'glass_hail'],
    'buildings': ['storm', 'flood', 'escape_of_water', 'subsidence', 'fire', 'accidental_damage'],
    'contents': ['theft', 'escape_of_water', 'accidental_damage', 'flood']}


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject):
    q = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', identifier,
        '--asunto', subject, '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    return json.loads(q.stdout)


def source_claims():
    c = pd.read_parquet(SOURCE_CLAIMS)
    c = c.loc[c.claim_id.str.len().eq(10)&c.status.ne('repudiated')].copy()
    c['net'] = c.incurred_to_date.to_numpy(float)-c.recoveries.to_numpy(float)
    return c[['claim_id', 'line', 'peril', 'loss_date', 'report_date', 'net']].assign(market='source')


def pool_claims(source, target, train_ids):
    # Key exclusion comes BEFORE parsing protected dates, peril, cost or status.
    c = target.loc[target.row_id.isin(train_ids)].copy(); c = c.loc[c.included_in_T0].copy()
    c['net'] = c.T0_cents.to_numpy(float)/100
    c = c[['claim_id', 'line', 'peril', 'loss_date', 'report_date', 'net']].assign(market='target_train')
    result = pd.concat([source, c], ignore_index=True)
    # Normalize selected payload types AFTER key exclusion. Corrupting protected
    # parent cells can change a column dtype without changing any selected value.
    for name in ['claim_id', 'line', 'peril', 'market']: result[name] = result[name].astype('string')
    for name in ['loss_date', 'report_date']: result[name] = pd.to_datetime(result[name]).astype('datetime64[ns]')
    result['delay'] = (pd.to_datetime(result.report_date)-pd.to_datetime(result.loss_date)).dt.days
    result['window'] = (CUT-pd.to_datetime(result.loss_date)).dt.days
    assert result[['delay', 'window', 'net']].notna().all().all()
    assert result.delay.ge(0).all() and result.delay.le(result.window).all() and result.net.ge(0).all()
    return result


def cost_curves(claims):
    """Restored REP-N2 cost-weighted reverse product limit, with scoped inputs."""
    tmax = int(claims.window.max()); size = tmax//BUCKET+1; curves = {}; records = []
    for peril, z in claims.groupby('peril', sort=True):
        net = z.net.to_numpy(float); cap = float(np.quantile(net, .995)); weight = np.minimum(net, cap)
        assert weight.sum() > 0
        db = z.delay.to_numpy(int)//BUCKET; wb = z.window.to_numpy(int)//BUCKET
        mass = np.bincount(db, weights=weight, minlength=size)[:size]
        start = np.bincount(db, weights=weight, minlength=size+1)[:size]
        end = np.bincount(np.minimum(wb, size-1)+1, weights=weight, minlength=size+1)[:size]
        risk = np.cumsum(start)-np.cumsum(end)
        hazard = np.divide(mass, np.maximum(risk, 1e-9), out=np.zeros_like(mass), where=risk > 0)
        assert np.isfinite(hazard).all() and (hazard >= -1e-12).all() and (hazard <= 1+1e-10).all()
        # Only representational roundoff at probability endpoints is corrected.
        hazard = np.clip(hazard, 0, 1)
        survival = np.cumprod((1-hazard)[::-1])[::-1]; cdf = np.r_[survival[1:], 1.]
        assert np.isfinite(cdf).all() and (np.diff(cdf) >= -1e-12).all() and cdf[-1] == 1.
        curves[peril] = cdf.tolist()
        records.append({'peril': peril, 'claims': len(z), 'target_training_claims': int(z.market.eq('target_train').sum()),
            'cap_CDF_weight_p995': cap, 'full_net_sum_not_capped_price_target': float(net.sum()), 'cost_CDF_weight_sum': float(weight.sum())})
    return {'bucket_days': BUCKET, 'tmax_days': tmax, 'curves': curves, 'records': records}


def effective(periods, curve):
    lo = (CUT-pd.to_datetime(periods.period_end)).dt.days.to_numpy(int)
    hi = (CUT-pd.to_datetime(periods.period_start)).dt.days.to_numpy(int)
    assert (lo >= 0).all() and (hi >= lo).all()
    daily = np.repeat(np.asarray(curve, float), BUCKET)
    n = int(hi.max())+1
    if len(daily) < n: daily = np.r_[daily, np.ones(n-len(daily))]
    cumulative = np.r_[0., np.cumsum(daily)]
    return (cumulative[hi+1]-cumulative[lo])/365.


def mixture(periods, perils, curves, costs, train):
    assert costs.shape == (len(periods), len(perils)) and (costs >= 0).all()
    ee = np.column_stack([effective(periods, curves['curves'][peril]) for peril in perils])
    exposure = periods.exposure_calendar.to_numpy(float)
    assert (ee >= -1e-12).all() and (ee <= exposure[:, None]+1e-10).all()
    den = ee[train].sum(axis=0); assert (den > 0).all()
    ult = costs[train].sum(axis=0)*exposure[train].sum()/den
    assert ult.sum() > 0
    shares = ult/ult.sum(); mixed = ee@shares
    assert np.isfinite(mixed).all() and (mixed > 0).all()
    # Independent scalar exposure and normalization identities, no fitted prices.
    assert math.isclose(math.fsum(shares.tolist()), 1., rel_tol=2e-15)
    for k in np.unique(np.linspace(0, len(periods)-1, 16, dtype=int)):
        scalar = math.fsum(float(a)*float(b) for a, b in zip(ee[k], shares))
        assert math.isclose(float(mixed[k]), scalar, rel_tol=3e-14, abs_tol=1e-13)
    return mixed, {peril: float(shares[j]) for j, peril in enumerate(perils)}


def synthetic():
    source = pd.DataFrame({'claim_id': ['s0', 's1', 's2', 's3'], 'line': 'motor', 'peril': ['theft']*4,
        'loss_date': pd.to_datetime(['2021-01-01', '2022-01-01', '2023-01-01', '2024-01-01']),
        'report_date': pd.to_datetime(['2021-01-01', '2022-02-01', '2023-06-01', '2024-02-01']), 'net': [0., 100., 200., 1000.], 'market': 'source'})
    target = pd.DataFrame({'row_id': ['tr', 'held'], 'claim_id': ['t0', 't1'], 'line': 'motor', 'peril': 'theft',
        'loss_date': pd.to_datetime(['2024-02-01', '2024-04-01']), 'report_date': pd.to_datetime(['2024-03-01', '2024-07-01']),
        'T0_cents': [30000, 100000], 'included_in_T0': True})
    selected = pool_claims(source, target, {'tr'}); a = cost_curves(selected)
    bad = target.copy()
    for key in ['peril', 'loss_date', 'report_date']:
        bad[key] = bad[key].astype('object'); bad.loc[bad.row_id.eq('held'), key] = 'INVALID_PROTECTED'
    bad.loc[bad.row_id.eq('held'), 'T0_cents'] = -10**12
    second = pool_claims(source, bad, {'tr'}); assert selected.equals(second) and a == cost_curves(second)
    periods = pd.DataFrame({'period_start': pd.to_datetime(['2023-01-01', '2024-02-01']),
        'period_end': pd.to_datetime(['2023-12-31', '2024-02-29'])})
    value = effective(periods, a['curves']['theft']); direct = []
    for s, end in zip(periods.period_start, periods.period_end):
        direct.append(math.fsum(a['curves']['theft'][min(int((CUT-d).days)//BUCKET, len(a['curves']['theft'])-1)] for d in pd.date_range(s, end))/365.)
    assert np.allclose(value, direct, rtol=1e-12, atol=1e-12)
    # Independent direct risk-set/product formula at every bucket of this fixture.
    g = selected; weights = np.minimum(g.net.to_numpy(float), np.quantile(g.net, .995)); db = g.delay.to_numpy(int)//BUCKET; wb = g.window.to_numpy(int)//BUCKET
    hazards = []
    for s in range(len(a['curves']['theft'])):
        risk = math.fsum(float(v) for v in weights[(db <= s)&(wb >= s)]); event = math.fsum(float(v) for v in weights[db == s])
        hazards.append(event/risk if risk > 0 else 0.)
    direct_cdf = [math.prod(1-v for v in hazards[s+1:]) for s in range(len(hazards))]
    assert np.allclose(direct_cdf, a['curves']['theft'], rtol=1e-13, atol=1e-13)
    return {'author': 'Codex', 'utc': utc(), 'held_dates_perils_cost_poison_invariant': True,
        'curve_direct_risk_sets_products_match': True, 'calendar_inclusive_daily_sum_match': True,
        'synthetic_cost_curve_calls': 2, 'new_price_fits': 0, 'limit': 'No tree fit or private-generalization claim from this reporting fixture.'}


def prepare():
    assert not PLAN.exists() and not INDEX.exists()
    if OUT.exists(): assert {x.name for x in OUT.iterdir()} == {'preparation_failure'}
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    OUT.mkdir(exist_ok=True); dump(OUT/'synthetic.json', synthetic())
    work = R/'privado/reentrenamiento_completo_20261026/corrida'
    paths = [Path(__file__), SOURCE_CLAIMS, CLAIMS, OUT/'synthetic.json',
        R/'src/semana2/reproduccion_cadena.py', work/'noche/codigo/exposicion_efectiva.py', work/'noche/codigo/desarrollado_gbm.py',
        BASE/'P41_grafo_fuente_recuperada_20261026/report.json', BASE/'P49_atribucion_pareada_20261027/report.json',
        R/'herramientas/entrenar_nucleo_A1S.py', R/'herramientas/preparar_algoritmo_pareado_P47.py']
    for line in LINES:
        paths += [HOME/f'rows_s1_{line}.parquet', HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s2_{line}.parquet',
            HOME/f'matrix_s2_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet',
            P1/f'canonical_{line}.parquet', COUNTS/f'counts_{line}.parquet']
    plan = {'author': 'Codex', 'utc': utc(), 'candidate_design': 'A1R: scoped restored pooled cost reporting, original-standard three-seed source trees and closed target calibration; one complete all-training learner perline for eventual production.',
        'need': 'Recovered A1price models inherit pooled source+target reporting. P49new PS1allocation cannot be repaired by a scalar. The smallest numerical dependency for an A1-family production comparator is a reporting/source fit whose entire target ancestry excludes the held group, rather than another frozen-model swap.',
        'not_exact_F3c': 'This is a NEW explicitly scoped A1-family algorithm, not historical F3creplay: use current source-safe notification-history matrices and global connected source/target groups. No public-derived vertex, scale or score solving. Existing historical reconstructions remain unchanged.',
        'reporting': {'estimator': 'RestoredREP-N2 weighted reverse product limit in7daybuckets with per-peril netcost weights capped at within-trainingp99.5. Cap affects reporting weights only, neverT0price labels or retained records.',
            'source': 'All accepted/nonrepudiated source report history including precoverage2020, original10characterclaimIDclone rule; fixed source population always training.',
            'target': 'ONLY included_in_T0claims keyed to all-line outer-training row IDs, selected BEFORE interpreting protected dates/perils/costs. No unassigned target imputation.',
            'tail': 'CDFnormalizes at largest observable source/training window; beyond support unchanged terminal1assumption, unknown true ultimate tail.',
            'mixture': 'Separate source and target-training cost shares from sumT0_p*sumcalendarExposure/sumE_peril. Source shares use source labels only; target shares use outer-traininglabels only.',
            'calendar': 'Inclusive calendar days/365 for observed cost integration and ultimate forward once. Legacy rounded exposure remains a frozen predictor, not an extra monetary offset.'},
        'validation_architecture': 'Five original global outerfolds. One whole learner uses outer-train reporting +3seedsourceensemble +targetclosed main-effect calibrator; scores its heldfold. Later production is ONE whole all-history learner, not a5target-fold mean. The3source seeds are still all used, geometrically, not independent replications. No nestedfive-member performance claim or copying validation into an ensemble.',
        'future_price_family_if_registered': 'Same31leafTweedie1.5sourceGBM, params/seeds11/12/13/lr.02/max4000/patience400 and source-only held connected groups fromA1S,9inner+9full source fits perouter,90max total. TargetNCB/priorK300, NB/RENlevelsK400 and original residualsK300, no N3mix or H1ratio. No new capacity, feature or hyperparameter search.',
        'preflight_budget': {'primary_cost_CDF_estimators': 55, 'adverse_cost_CDF_estimators_separate': 55, 'synthetic_curve_calls_completed_fixture': 2, 'synthetic_curve_calls_failed_preparation_separate': 2,
            'source_share_vectors': 15, 'target_share_vectors': 15, 'source_normalized_share_coordinates': 75, 'target_normalized_share_coordinates': 75,
            'new_source_price_fits': 0, 'new_target_price_fits': 0, 'new_price_vectors': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'before_future_fit': 'Separate frozen source recipe, criterion, cost and forum; preserve eachinvocation/checkpoint, source-held metric as conditional only. Whole target comparison must retain all original global/cohort/transfer/tail/influencegates. Full conditional transfer requires its OWN report/source fits on2023training, not copying pooled sourceobjects.',
        'sources': {w.rel(k): w.sha(k) for k in paths},
        'limits': ['Market-invariant peril delay/severity and p99.5CDFweights are assumptions; not a correction proved by P49.',
            'Source early stopping conditional on whole-source reporting, but outer-target exclusion must hold for all learning.',
            '2024adaptiveopen, source2024conditional information, undated masters and source-safe history differences fromlegacy remain.',
            'No formal promotion/private improvement from recovered code, curve or source fit alone.'], '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P50registra la dependencia numérica concreta antes de estimar curvas: el reporte de A1agrupaba fuente y destino. Prepararé la fórmula REP-N2restaurada dentro de cada fold, retirando primero todas las filas targetretenidas antes de fechas/perils/costes o percentil. Fuente aceptada conocida y etiquetasT0sin topar; p99,5solo para pesos de CDF. Cinco ámbitos,55curvas de coste primarias y55adversas separadas; cuotas por ramo de fuente y targetsolo entrenados. Calendario una vez. Será una nueva A1Rcon matrices históricas seguras, no replayF3c ni reutilización de modelos con ancestros protegidos. Producción posterior sería un único aprendiz completo, fuente con3semillas; se validará como tal, sin prometer la media de5targetmodelos no evaluada. Esta etapa no entrena árboles o precios ni puntúa. Máximo futuro90fits fuente solo si se preinscribe aparte. Transferencia2023→2024necesitará fuentes propias, no copiar estos objetos agrupados. B00/F3c/adversos intactos;2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P50registered_before_scoped_reporting', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P50-REPORTE-PREVIO', 'P50: reporte agrupado por fold, alcance completo antes de curvas o árboles')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN) and all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    source = source_claims(); target = pd.read_parquet(CLAIMS)
    canonical = {line: pd.read_parquet(P1/f'canonical_{line}.parquet') for line in LINES}
    all_rows = pd.concat(canonical.values(), ignore_index=True); assert all_rows.row_id.is_unique and all_rows.year.isin([2023, 2024]).all()
    checks = []; outputs = {}; primary_calls = 0; adverse_calls = 0
    for outer in range(5):
        folder = OUT/f'outer{outer}'; folder.mkdir(); train_ids = set(all_rows.loc[all_rows.fold.ne(outer), 'row_id'])
        held_ids = set(all_rows.loc[all_rows.fold.eq(outer), 'row_id']); train_groups = set(all_rows.loc[all_rows.fold.ne(outer), 'group_id'])
        assert train_groups.isdisjoint(set(all_rows.loc[all_rows.fold.eq(outer), 'group_id']))
        selected = pool_claims(source, target, train_ids); curves = cost_curves(selected); primary_calls += len(curves['curves'])
        bad = target.copy(); mask = bad.row_id.isin(held_ids)
        for key in ['peril', 'loss_date', 'report_date']: bad[key] = bad[key].astype('object'); bad.loc[mask, key] = 'INVALID_PROTECTED'
        bad.loc[mask, ['T0_cents', 'reserve_cents']] = -10**12
        poisoned = pool_claims(source, bad, train_ids); assert selected.equals(poisoned)
        adversarial = cost_curves(poisoned); adverse_calls += len(adversarial['curves']); assert curves == adversarial
        dump(folder/'cost_curves.json', curves); dump(folder/'scope.json', {'outer': outer, 'training_row_ids': sorted(train_ids),
            'training_group_count': len(train_groups), 'target_training_claim_ids': sorted(selected.loc[selected.market.eq('target_train'), 'claim_id']),
            'held_target_parse_cost_peril_dates_invariant': True, 'primary_and_adverse_curves_exact': True})
        summaries = []
        for line in LINES:
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet'); count = pd.read_parquet(COUNTS/f'counts_{line}.parquet')
            assert np.array_equal(rows.row_id, count.row_id) and np.array_equal(rows.T0_cents, count.T0_cents_total)
            perils = PERILS[line]; costs = count[['T0_cents_'+name for name in perils]].to_numpy(float)/100
            ec, shares = mixture(rows, perils, curves, costs, np.ones(len(rows), dtype=bool))
            inputs = rows[['row_id', 'year']].copy(); inputs['e_cost_A1R'] = ec; inputs.to_parquet(folder/f'source_{line}.parquet', index=False)
            f = canonical[line]; amounts = np.column_stack([f.row_id.map(target.loc[target.included_in_T0&target.peril.eq(name)].groupby('row_id').T0_cents.sum()).fillna(0).to_numpy(float)/100 for name in perils])
            assert np.allclose(amounts.sum(axis=1), f.T0, rtol=0, atol=.005)
            train = f.fold.ne(outer).to_numpy(); target_ec, target_shares = mixture(f, perils, curves, amounts, train)
            q = target_ec/f.exposure_calendar.to_numpy(); assert (q > 0).all() and (q <= 1+1e-10).all()
            inp = f[['row_id', 'line', 'year', 'fold', 'group_id', 'new_business', 'T0', 'reserve', 'exposure_calendar']].copy()
            inp['q_A1R'] = q; inp['e_cost_A1R'] = target_ec; inp.to_parquet(folder/f'target_{line}.parquet', index=False)
            dump(folder/f'mixtures_{line}.json', {'source': shares, 'target_training_only': target_shares,
                'source_T0_cents_digest': w.sha(COUNTS/f'counts_{line}.parquet'), 'source_rows': len(rows),
                'target_training_rows': int(train.sum()), 'target_training_positive': int((f.T0.gt(0)&f.fold.ne(outer)).sum())})
            summaries.append({'line': line, 'source_rows': len(rows), 'target_rows': len(f), 'source_e_cost_min': float(ec.min()),
                'target_q_range': [float(q.min()), float(q.max())], 'target_training_positive': int((f.T0.gt(0)&f.fold.ne(outer)).sum())})
        files = [x for x in folder.iterdir() if x.is_file()]; outputs.update({w.rel(k): w.sha(k) for k in files})
        dump(folder/'committed.json', {'outer': outer, 'curves': len(curves['curves']), 'checks': summaries,
            'outputs': {w.rel(k): w.sha(k) for k in files}})
        checks.append({'outer': outer, 'primary_curves': len(curves['curves']), 'adverse_curves': len(curves['curves']),
            'outer_target_held_exclusion_and_numeric_curve_invariance': True, 'line_checks': summaries})
        print(json.dumps({'outer': outer, 'scoped_reporting_complete': True, 'new_tree_fits': 0}), flush=True)
    assert primary_calls == adverse_calls == 55
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    dump(OUT/'report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P50scoped_reporting_inputs_complete_not_price_validation', 'plan_sha256': w.sha(PLAN),
        'checks': checks, 'outputs': outputs, 'primary_cost_CDF_estimators': primary_calls, 'adverse_cost_CDF_estimators_separate': adverse_calls,
        'source_share_vectors': 15, 'target_share_vectors': 15, 'source_share_coordinates': 75, 'target_share_coordinates': 75,
        'new_price_fits': 0, 'new_prices': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
        '2024_open': True, 'goal_achieved': False, 'private_improvement_established': False})
    print(json.dumps({'complete': True, 'primary_cost_curves': primary_calls, 'adverse_separate': adverse_calls, 'new_price_fits': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); assert d['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/k) == v for k, v in d['outputs'].items())
    next_unit = 'P51: preregister A1Rsource price fits under these exact five scoped reporting inputs, same source-only connected validation groups, source-safe history/features,3seeds and original GBMparameters.90sourcefits max (9inner+9full perouter); source-held metric conditional on reporting including source-heldclaims. Save each invocation/model and test source held-cost/offset math, serialization/leaf sum/order and actual fit-payload invariance to excluded outer-target labels. Do not copy full pooled models acrossouterfolds. Whole-target calibrations/scoring require separate complete recipe and original global/NB/tail/transfer guards; transfer source/report objects still absent. No2025inference or upload in source stage.'
    text = '# P50: observación de A1 agrupada dentro de cada fold\n\nCodex, '+utc()+'. Se prepararon los cinco ámbitos con55curvas de coste primarias y55controles adversos. Se excluyeron las claves targetretenidas antes de interpretar fechas, perils, importes y percentiles. Los objetos numéricos no cambiaron al contaminar todo ese contenido retenido.\n\n'
    text += 'La dependencia pendiente de la A1recuperada era el reporte agrupado anterior a los árboles fuente. Se preparó su fórmula restaurada dentro del ámbito, sin copiar los modelos históricos ni repetir las57etapas ya auditadas. Las etiquetasT0de precio no se topan; el p99,5actúa solo en los pesos de la CDF. Las cuotas source y targetson distintas y usan las respuestas de su entrenamiento correspondiente. Se conservaron todos los originales, periodos y siniestros.\n\n'
    text += 'A1Rsería un algoritmo nuevo y completo, con las matrices de historia segura actuales, tres semillas fuente y calibración estándar; un aprendiz con todos los datos para producción, validado por exclusión global. No se presenta como F3cexacto o como un promedio de cinco aprendices target. Se evita presupuestar otra arquitectura y después entregar una distinta. Fuente y calendario se enlazan una sola vez.\n\n'
    text += 'Esta etapa no ajustó árboles o calibradores de precio y no produjo predicciones, scores o inferencias2025. Hay15vectores de cuotas fuente y15de target,75coordenadas normalizadas de cada mercado, separadas de constantes de precio. El control escalar verificó productos de riesgos y sumas diarias inclusivas. El supuesto de demora común entre mercados, el tope para pesos de reporte y la cola normalizada siguen abiertos; no se deduce mejora privada.2024es desarrollo adaptativo; B00/F3c/adversos conservados.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': d['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'primary_cost_CDF_estimators': 55, 'adverse_cost_CDF_estimators_separate': 55,
        'new_price_fits': 0, 'new_prices': 0, 'new_scores': 0, 'new_submissions': 0, 'next_unit': next_unit, '2024_open': True, 'goal_achieved': False,
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P50-REPORTE-RESULTADO', 'P50: cinco reportes agrupados protegidos, sin nuevos precios o scores')}
    archive = R/'privado'/('corte_P50_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    counts_path = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(counts_path); assert 'phase2_private_P50_scoped_cost_reporting' not in counts
    w.update(counts_path, {'phase2_private_P50_scoped_cost_reporting': {'primary_cost_curves': 55, 'adverse_cost_curves_separate': 55,
        'synthetic_cost_curve_calls_completed_fixture': 2, 'synthetic_cost_curve_calls_failed_preparation_separate': 2, 'source_share_coordinates': 75, 'target_share_coordinates': 75, 'new_price_fits': 0}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P50': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P50': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P50=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P50: reporte agrupado con exclusión de fold\n\nCodex, '+receipt['utc']+'. Cinco ámbitos,55curvas primarias/55adversas invariantes a etiquetas retenidas, cuotas separadas source/targety calendario. Ningún ajuste de precio, score o envío. NuevaA1R, no F3cexacto; falta fuente/target/transferencia completa. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_scoped_pooled_reporting_index': w.rel(INDEX), 'week_2_private_scoped_pooled_reporting_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'new_price_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'close']); mode = a.parse_args().mode
    {'prepare': prepare, 'run': run, 'close': close}[mode]()
