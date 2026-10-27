"""A1R completo en destino: pooled primero, transferencia propia obligatoria para admitir."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import importlib.util
import json
import math
import os
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'; BASE = R/'privado/semana2/mision017_fase2'
SOURCE = BASE/'P51_fuente_agrupada_20261027'; REPORTING = BASE/'P50_reporte_agrupado_20261027'
OUT = BASE/'P52_validacion_A1R_20261027'
PLAN = R/'registro/semana2_A1R_destino_validacion_plan.json'; INDEX = R/'registro/semana2_A1R_destino_validacion_actual.json'
DOC = R/'docs/semana2/PRIVADA_P52_A1R_VALIDACION_DESTINO.md'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


p = load('p52_closed_main_effects', R/'herramientas/preparar_algoritmo_pareado_P47.py')
q = load('p52_scoped_report', R/'herramientas/preparar_reporte_agrupado_P50.py')
c = load('p52_standard_metrics', R/'herramientas/validar_canal_privada_P23.py')
w = p.w; np = p.np; pd = p.pd; e = c.e; e.OUT = OUT
P1 = BASE/'preflight_anidado_H1_20261026_v1'; REF = BASE/'P15_validacion_ausentes_20261026/POOLED_prices.parquet'


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value): return q.dump(path, value)


def check_sources(plan):
    bad = [k for k, v in plan['sources'].items() if w.sha(ROOT/k) != v]; assert not bad, bad


def selected_claims(target, train_ids, branch):
    z = target.loc[target.row_id.isin(train_ids)].copy(); z = z.loc[z.included_in_T0].copy()
    z['T0_cents'] = z.T0_cents.to_numpy(float)+(branch-1)*z.reserve_cents.to_numpy(float)
    assert z.T0_cents.ge(0).all(); return z


def source_branch(branch):
    raw = pd.read_parquet(q.SOURCE_CLAIMS); raw = raw.loc[raw.claim_id.str.len().eq(10)&raw.status.ne('repudiated')].copy()
    net = raw.incurred_to_date.to_numpy(float)-raw.recoveries.to_numpy(float)
    reserve = raw.incurred_to_date.to_numpy(float)-raw.paid_to_date.to_numpy(float)
    result = raw[['claim_id', 'line', 'peril', 'loss_date', 'report_date']].copy()
    result['net'] = net+(branch-1)*reserve; assert result.net.ge(0).all()
    return result.assign(market='source')


def train_shares(frame, selected, curves, perils):
    # frame and selected contain ONLY training keys; held cost fields never enter.
    assert frame.row_id.is_unique and set(selected.row_id).issubset(set(frame.row_id))
    ee = np.column_stack([q.effective(frame, curves['curves'][name]) for name in perils])
    total = np.array([selected.loc[selected.peril.eq(name), 'T0_cents'].sum()/100 for name in perils])
    ult = total*frame.exposure_calendar.sum()/ee.sum(axis=0); assert (ult >= 0).all() and ult.sum() > 0
    return ult/ult.sum()


def apply_q(frame, curves, perils, shares, tail=0.):
    ee = np.column_stack([q.effective(frame, curves['curves'][name]) for name in perils])
    ee *= 1-tail*np.array([name in ['bodily_injury', 'subsidence'] for name in perils])
    result = (ee@shares)/frame.exposure_calendar.to_numpy(float)
    assert np.isfinite(result).all() and (result > 0).all() and (result <= 1+1e-10).all(); return result


def once(folder, name, producer):
    """Recover a saved learning call; an interrupted unsaved call needs reconciliation."""
    folder.mkdir(parents=True, exist_ok=True); result = folder/(name+'.json'); marker = folder/(name+'_invoked.json')
    if result.exists():
        assert marker.exists(); return w.read(result)
    assert not marker.exists(), 'Unsaved invocation, do not blindly repeat: '+str(marker)
    dump(marker, {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'call': name})
    value = producer(); dump(result, value); return value


def synthetic():
    """Exercise new row exclusion, reserve valuation and reporting-to-price wiring."""
    path = BASE/'P52_synthetic_preflight.json'; assert not path.exists()
    rng = np.random.default_rng(2026102752); n = 480
    frame = pd.DataFrame({'row_id': ['s'+str(i) for i in range(n)], 'group_id': ['g'+str(i) for i in range(n)],
        'is_held': np.arange(n)%5 == 0, 'year': 2023+(np.arange(n)//5)%2, 'new_business': (np.arange(n)//10)%2,
        'T0': rng.gamma(2, 100, n)*(rng.random(n) < .3), 'reserve': 0.,
        'ncb_years': rng.integers(0, 15, n), 'prior_claims_5y': rng.integers(0, 3, n),
        'gender': rng.choice(['F', 'M'], n), 'works_from_home': rng.integers(0, 2, n),
        'marketing_segment': rng.choice(['a', 'b', 'c'], n)})
    frame['period_start'] = pd.to_datetime(np.where(frame.year.eq(2023), '2023-01-01', '2024-01-01'))
    frame['period_end'] = pd.to_datetime(np.where(frame.year.eq(2023), '2023-12-31', '2024-09-30'))
    frame['exposure_calendar'] = (frame.period_end-frame.period_start).dt.days.add(1)/365.
    frame['annual_paired'] = np.exp(rng.normal(4, .3, n)); perils = ['bodily_injury', 'theft']
    target = frame[['row_id', 'period_start']].rename(columns={'period_start': 'loss_date'}).copy()
    target['claim_id'] = 't'+target.row_id; target['line'] = 'motor'; target['peril'] = np.resize(perils, n)
    target['report_date'] = target.loss_date+pd.to_timedelta(np.resize([1, 30, 120, 240], n), unit='D')
    target['included_in_T0'] = True; target['T0_cents'] = 10000; target['reserve_cents'] = 2000
    source = target.iloc[:16][['claim_id', 'line', 'peril', 'loss_date', 'report_date']].copy()
    source['claim_id'] = 'source'+source.claim_id; source['net'] = 100.; source['market'] = 'source'
    train_ids = set(frame.loc[~frame.is_held, 'row_id']); selected = selected_claims(target, train_ids, .75)
    assert np.array_equal(selected.T0_cents, np.full(len(selected), 9500.))
    bad = target.copy(); protected = ~bad.row_id.isin(train_ids)
    bad.loc[protected, ['T0_cents', 'reserve_cents']] = -10**12
    for key in ['peril', 'loss_date', 'report_date']:
        bad[key] = bad[key].astype('object'); bad.loc[protected, key] = 'INVALID_HELD'
    first = q.pool_claims(source, selected, train_ids)
    second = q.pool_claims(source, selected_claims(bad, train_ids, .75), train_ids)
    assert first.equals(second); curves = q.cost_curves(first); assert curves == q.cost_curves(second)
    shares = train_shares(frame.loc[~frame.is_held], selected, curves, perils)
    frame['q_paired'] = apply_q(frame, curves, perils, shares)
    for i in [0, 1, 11, n-1]:
        sums = []
        for peril in perils:
            curve = curves['curves'][peril]
            sums.append(math.fsum(curve[min((q.CUT-d).days//q.BUCKET, len(curve)-1)]
                for d in pd.date_range(frame.period_start.iloc[i], frame.period_end.iloc[i]))/365.)
        direct = math.fsum(float(s)*float(t) for s,t in zip(sums, shares))/frame.exposure_calendar.iloc[i]
        assert math.isclose(direct, frame.q_paired.iloc[i], rel_tol=1e-12, abs_tol=1e-13)
    records = []
    for line in q.LINES:
        artifact = p.learn(frame, line); poison = frame.copy(); poison.loc[poison.is_held, ['T0', 'reserve']] = -1e30
        adverse = p.learn(poison, line); assert artifact == adverse
        ultimate, norm = p.forward(frame.loc[frame.is_held], artifact, True)
        observed, _ = p.forward(frame.loc[frame.is_held], artifact, False)
        replay, other = p.forward(poison.loc[poison.is_held], json.loads(json.dumps(artifact)), True)
        assert np.array_equal(ultimate, replay) and norm == other
        # Residual normalizers may depend on the supplied base; only apply q AFTER ultimate, as production does.
        nominal = ultimate*frame.loc[frame.is_held, 'q_paired'].to_numpy()
        assert np.isfinite(nominal).all() and (nominal > 0).all() and np.isfinite(observed).all()
        records.append({'line': line, 'held_learning_and_ultimate_invariant': True, 'serialization_exact': True})
    result = {'author': 'Codex', 'utc': utc(), 'code_sha256': w.sha(Path(__file__)), 'records': records,
        'new_interface_daily_calendar_second_method_exact': True, 'reserve_selection_before_held_payload_parse': True,
        'synthetic_curve_calls': 2, 'synthetic_primary_closed_learners': 3, 'synthetic_adverse_learners_separate': 3,
        'real_fits': 0, 'scores': 0, 'new_submissions': 0}
    dump(path, result); print(json.dumps(result))


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert len(list(SOURCE.glob('outer*/completed.json'))) == 5
    template = w.read(R/'registro/semana2_marca_capital_validacion_privada_plan.json')
    paths = [Path(__file__), Path(p.__file__), Path(q.__file__), Path(c.__file__), Path(e.__file__),
        Path(p.b.__file__), Path(p.g.__file__), REF, q.SOURCE_CLAIMS, q.CLAIMS, q.PLAN,
        R/'registro/semana2_fuente_agrupada_privada_plan.json', REPORTING/'report.json', REPORTING/'completion_receipt.json',
        BASE/'P47_preflight_pareado_20261026/synthetic.json', BASE/'P52_synthetic_preflight.json', BASE/'P52_code_domain_preflight.json',
        BASE/'P19_cohortes_broker_20261026/covariates.parquet', BASE/'P19_cohortes_broker_20261026/group_universe.json',
        BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy', BASE/'estimando_cartera2025_v3/weights.parquet']
    for outer in range(5):
        done = w.read(SOURCE/f'outer{outer}/completed.json'); assert done['source_fits'] == 18
        for k, v in {**done['outputs'], **done['source_fit_records']}.items(): assert w.sha(ROOT/k) == v; paths.append(ROOT/k)
        paths += [SOURCE/f'outer{outer}/completed.json', REPORTING/f'outer{outer}/cost_curves.json', REPORTING/f'outer{outer}/scope.json']
        for line in q.LINES:
            paths += [REPORTING/f'outer{outer}/target_{line}.parquet', REPORTING/f'outer{outer}/mixtures_{line}.json', P1/f'canonical_{line}.parquet']
            for seed in [11, 12, 13]:
                folder = SOURCE/f'outer{outer}/{line}_seed{seed}_full'
                paths += [folder/'model.txt', folder/'application.json']
    OUT.mkdir(); plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1R_complete_single_training_learner_three_seed_source',
        'hypothesis': 'Correcting source and target observation ancestry inside each fold may allow the standard A1family to allocate cost more robustly than the protected A1S/S2/H1reference. All curves/source fits are protected from the target held group; source-only performance is not evidence of this gain.',
        'architecture': 'Use ALL3P51source seeds geometrically for eachline/outer, learn one closed target calibrator from80percent target groups, and forward to calendar ultimate. Production later would be ONEall-training learner with3source seeds; no targetfold mean, N3mix or H1/G3ratio.',
        'calibration': 'Reuse unchanged P47closed kernel: NCB/prior shapeK300, line-level Tweedie optimum, NB/RENlevelsK400, original gender/WFH/marketing residualsK300. annual_paired is an internal alias for exp(log_relative_A1R), not a new count/mark claim.',
        'comparator': 'Original protected complete A1S/S2/H1reference from saved identical rows. Different architecture and training fractions are explicit; no causal attribution or exactF3cidentity.',
        'exposure': 'Nominal P50own scoped qand inclusive calendar exposure once in training; ultimate ignores oldvaluation completion, then held observed prediction=ultimate*q_own_scope.',
        'scenarios': 'Fixed nominal fitted ultimate prices. RESERVE075/125recompute pooled costCDFweights/caps and training-only target shares under own scoped branch claims; source price trees remain nominal. TAIL005/010scale BI/subsidence costcompletion with nominal shares, no new prices or curves. No full branch price retraining claim.',
        **{k: template[k] for k in ['criteria', 'bootstrap', 'level_sensitivity', 'cohort_guard']},
        'staged_decision_before_scores': 'POOLEDmust pass EVERYunchanged applicable global/scenario/cohort guard. Any failure rejects this candidate and avoids unnecessary transfer source fits; transfer remains NOT_EVALUATED, not a pass. If pooled passes, own conditional-transfer report/source/target stage is mandatory before file admission, no automatic upload.',
        'family': 'Keep family16bands even in initial pooled stage (5global+3cohort available); remaining transfer comparisons are unobserved. Same seeds/group multiplicities,2000draws, no relaxed lower-tail resolution.',
        'budget': {'new_source_fits': 0, 'nominal_C0_refits': 0, 'primary_reserve_branch_costCDFs': 110,
            'adverse_branch_costCDFs_separate': 110, 'primary_target_closed_learners': 15, 'adverse_target_closed_learners_separate': 15,
            'new2025inference': 0, 'new_submissions': 0},
        'recovery': 'Each primary/adverse call saves its invocation before learning and result immediately. Saved results are reused; an invoked call without saved result stops for explicit reconciliation. No timeout-based repeat.',
        'sources': {w.rel(k): w.sha(k) for k in set(paths)},
        'limits': ['Adaptive2023/2024and source2024conditional; source cost-reporting market invariance, p99.5CDFweights, tail/reserve adequacy and undated masters remain assumptions.',
            'Baseline mixes an80percent outer S2fit with64percent nested corrections, new candidate is one80percent complete fit; later100percent production, not an equality-of-sample-size experiment.',
            'Conditional bootstrap does not account for the source/target fitting uncertainty or repeated adaptive search. No professional independent validation.',
            'Missing conditional-transfer cannot be certified by copying pooled source objects or inserting zero deltas.']}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P52preinscribe el algoritmo A1Rcompleto en destino después de90fits fuente P51. Quince calibradores cerrados primarios y15adversos con C0y fuente propios, objetivoT0sin cambios, calendario una vez y avance a último. Producción sería un aprendiz completo con3semillas fuente, no una media targetde5modelos. Mismos mínimos/IC/folds/años/Post31/pisos/negocio nuevo/broker/historia cero/familia16. Escenarios de reservas:110CDFde coste primarias y110adversas bajo las dos valoraciones, con shares solo entrenados; árboles y últimos nominales fijos. No se recalcula el C0nominal. La transferencia queda no evaluada: si el combinado falla cualquier guarda basta para rechazar; si pasa, transferencia propia obligatoria antes de admitir CSV. No se inventa un cero favorable o se rescata un ramo. Cero árboles nuevos, inferencias2025o envíos. B00/F3c/adversos conservados;2024abierto adaptativo, privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P52registered_before_target_or_branch_fit_score', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': q.post(body, 'COD-S2-20261027-PRIVADA-P52-A1R-PREVIO', 'P52: A1Rcompleto, guardas intactas y transferencia pendiente explícita')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def frame_for(line, outer):
    f = pd.read_parquet(P1/f'canonical_{line}.parquet'); rate = pd.read_parquet(SOURCE/f'outer{outer}/historical_{line}.parquet').set_index('row_id')
    link = pd.read_parquet(REPORTING/f'outer{outer}/target_{line}.parquet').set_index('row_id')
    assert f.row_id.is_unique and set(f.row_id) == set(rate.index) == set(link.index)
    for z in [rate, link]: assert np.array_equal(f.year, z.loc[f.row_id].year)
    f['is_held'] = f.fold.eq(outer); f['annual_paired'] = np.exp(rate.loc[f.row_id].log_relative_A1R.to_numpy())
    f['q_paired'] = link.loc[f.row_id].q_A1R.to_numpy(); return f


def branch_links():
    if (OUT/'branch_report.json').exists():
        saved = w.read(OUT/'branch_report.json')
        assert all(w.sha(ROOT/k) == v for k,v in saved['outputs'].items()); return
    target = pd.read_parquet(q.CLAIMS); all_rows = pd.concat([pd.read_parquet(P1/f'canonical_{line}.parquet') for line in q.LINES])
    records = []
    for outer in range(5):
        train_ids = set(all_rows.loc[all_rows.fold.ne(outer), 'row_id']); scope = w.read(REPORTING/f'outer{outer}/scope.json')
        assert scope['training_row_ids'] == sorted(train_ids)
        for name, branch in [('RESERVE075', .75), ('RESERVE125', 1.25)]:
            folder = OUT/f'{name}_outer{outer}'
            selected = selected_claims(target, train_ids, branch); src = source_branch(branch)
            args = q.pool_claims(src, selected, train_ids); curves = once(folder, 'primary_curves', lambda: q.cost_curves(args))
            bad = target.copy(); protected = ~bad.row_id.isin(train_ids)
            for key in ['peril', 'loss_date', 'report_date']: bad[key] = bad[key].astype('object'); bad.loc[protected, key] = 'INVALID_HELD'
            bad.loc[protected, ['T0_cents', 'reserve_cents']] = -10**12
            adverse_args = q.pool_claims(src, selected_claims(bad, train_ids, branch), train_ids)
            assert args.equals(adverse_args)
            adverse = once(folder, 'adverse_curves', lambda: q.cost_curves(adverse_args)); assert curves == adverse and len(curves['curves']) == 11
            for line in q.LINES:
                f = pd.read_parquet(P1/f'canonical_{line}.parquet'); train = f.loc[f.fold.ne(outer)].copy(); perils = q.PERILS[line]
                sel = selected.loc[selected.line.eq(line)]; shares = train_shares(train, sel, curves, perils)
                value = apply_q(f, curves, perils, shares)
                z = f[['row_id']].copy(); z['q'] = value; z.to_parquet(OUT/f'{name}_{line}_{outer}_q.parquet', index=False)
            records.append({'outer': outer, 'scenario': name, 'primary_curves': 11, 'adverse_curves_separate': 11, 'held_claim_poison_invariant': True})
    paths = list(OUT.glob('RESERVE*_q.parquet'))+list(OUT.glob('RESERVE*_outer*/*.json'))
    dump(OUT/'branch_report.json', {'author': 'Codex', 'utc': utc(), 'primary_curves': 110, 'adverse_separate': 110, 'records': records,
        'outputs': {w.rel(x):w.sha(x) for x in paths}, 'new_price_fits': 0})


def cohort_blocks():
    f = pd.read_parquet(OUT/'POOLED_prices.parquet'); cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet').set_index('row_id').loc[f.row_id]
    assert np.array_equal(cov.year, f.year) and np.array_equal(cov.new_business, f.new_business)
    universe = w.read(BASE/'P19_cohortes_broker_20261026/group_universe.json'); parts = []; descriptions = []; stress = []
    reserve = pd.concat([pd.read_parquet(P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in q.LINES]).set_index('row_id').loc[f.row_id].reserve.to_numpy()
    for cohort in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        keep = f.new_business.to_numpy(bool).copy()
        if cohort != 'NB': keep &= cov.channel.eq('broker').to_numpy()
        if cohort == 'NB_BROKER_ZERO': keep &= cov.f1_anios_observados.eq(0).to_numpy()
        z = f.loc[keep]; y = z.T0.to_numpy(float); gain = e.unit(y, z.old_nominal.to_numpy())-e.unit(y, z.new_nominal.to_numpy())
        values = np.column_stack([np.ones(len(z)), y, np.sqrt(y), gain])
        parts.append(pd.DataFrame(values).assign(group=z.group_id.to_numpy()).groupby('group', sort=True).sum().reindex(universe, fill_value=0).to_numpy())
        den = e.unit(y, np.full(len(y), y.mean())).sum(); descriptions.append({'evaluation': 'POOLED', 'cohort': cohort, 'rows': len(z), 'groups': int(z.group_id.nunique()), 'delta': float(gain.sum()/den)})
        for name in e.NAMES[1:]:
            yy = y-.25*reserve[keep] if name == 'RESERVE075' else y+.25*reserve[keep] if name == 'RESERVE125' else y
            dd = e.unit(yy, np.full(len(yy), yy.mean())).sum(); diff = e.unit(yy, z[name+'_old'].to_numpy())-e.unit(yy, z[name+'_new'].to_numpy())
            stress.append({'cohort': cohort, 'scenario': name, 'delta': float(diff.sum()/dd)})
    return np.concatenate(parts, axis=1), descriptions, stress, universe


def cohort_scores(values):
    return np.column_stack([values[:, j*4+3]/(8*np.sqrt(values[:, j*4]*values[:, j*4+1])-8*values[:, j*4+2]) for j in range(3)])


def cohort_analysis():
    totals, desc, stress, universe = cohort_blocks(); rng = np.random.default_rng(2026102660); draws = []
    for start in range(0, 2000, 32):
        weights = rng.multinomial(len(universe), np.full(len(universe), 1/len(universe)), size=min(32, 2000-start))
        if start == 0: assert np.array_equal(weights[:4], np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy'))
        draws.append(cohort_scores(weights@totals))
    draws = np.concatenate(draws); assert np.isfinite(draws).all(); np.save(OUT/'cohort_bootstrap.npy', draws)
    for j, z in enumerate(desc):
        z['marginal95'] = np.quantile(draws[:, j], [.025, .975]).tolist(); z['family16_band95'] = np.quantile(draws[:, j], [.025/16, 1-.025/16]).tolist()
    lower = float(np.quantile(np.load(OUT/'POOLED_joint_bootstrap.npy')[:, 0], .025/16))
    gates = {'cohort_nominal_points_above_floor': all(z['delta'] >= -.001 for z in desc),
        'cohort_nominal_lower95_above_floor': all(z['marginal95'][0] >= -.001 for z in desc),
        'cohort_family16_lower_above_floor': all(z['family16_band95'][0] >= -.001 for z in desc),
        'cohort_all_stress_points_above_floor': all(z['delta'] >= -.001 for z in stress), 'pooled_nominal_family16_lower_positive': lower > 0}
    result = {'author': 'Codex', 'utc': utc(), 'comparisons': desc, 'stress_points': stress, 'gates': gates, 'family16_pooled_lower': lower,
        'transfer': None, 'transfer_not_evaluated': True, 'replicates': 2000, 'low_tail_resolution': 'Approximately3taildraws per2000for family16; exploratory adaptive search.'}
    dump(OUT/'cohort_report.json', result); return result


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN); check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    if not (OUT/'started.json').exists(): dump(OUT/'started.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid()})
    branch_links(); counts = Counter(); parts = []
    for outer in range(5):
        curves = w.read(REPORTING/f'outer{outer}/cost_curves.json')
        for line in q.LINES:
            folder = OUT/f'{line}_{outer}'; folder.mkdir(exist_ok=True); f = frame_for(line, outer); train = ~f.is_held
            if (folder/'committed.json').exists():
                saved = w.read(folder/'committed.json'); assert all(w.sha(ROOT/k) == v for k,v in saved['outputs'].items())
                counts.update(saved['constants']); parts.append(pd.read_parquet(folder/'prices.parquet')); continue
            def learning(data):
                value = p.learn(data, line); value['contract'] = 'A1R_single_complete_learner'; return value
            artifact = once(folder, 'learning', lambda: learning(f)); counts.update(p.constant_counts(artifact))
            bad = f.copy(); bad.loc[bad.is_held, ['T0', 'reserve']] = -1e30
            adverse = once(folder, 'adverse_learning', lambda: learning(bad)); assert artifact == adverse
            held = f.loc[f.is_held].copy(); ultimate, norms = p.forward(held, artifact, True)
            check, nn = p.forward(bad.loc[bad.is_held], adverse, True); assert np.array_equal(ultimate, check) and norms == nn
            value = p.base(f.loc[train])
            for shape in artifact['shape']: value = p.b.shape_apply(f.loc[train], value, shape)
            moment = math.fsum((f.loc[train, 'T0'].to_numpy()/np.sqrt(value)).tolist())/math.fsum(np.sqrt(value).tolist())
            assert math.isclose(moment, artifact['level'], rel_tol=3e-12)
            result = held[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy(); result['ultimate'] = ultimate
            result['new_nominal'] = ultimate*held.q_paired.to_numpy()
            perils = q.PERILS[line]; shares_map = w.read(REPORTING/f'outer{outer}/mixtures_{line}.json')['target_training_only']; shares = np.array([shares_map[n] for n in perils])
            assert np.allclose(apply_q(held, curves, perils, shares), held.q_paired, rtol=2e-12, atol=1e-13)
            for name in ['RESERVE075', 'RESERVE125']:
                link = pd.read_parquet(OUT/f'{name}_{line}_{outer}_q.parquet').set_index('row_id').loc[held.row_id, 'q'].to_numpy()
                result[name+'_new'] = ultimate*link
            for name, tail in [('TAIL005', .05), ('TAIL010', .10)]: result[name+'_new'] = ultimate*apply_q(held, curves, perils, shares, tail)
            result.to_parquet(folder/'prices.parquet', index=False); parts.append(result)
            dump(folder/'committed.json', {'outer': outer, 'line': line, 'constants': p.constant_counts(artifact), 'ultimate_normalizers': norms,
                'held_payload_invariant': True, 'outputs': {w.rel(x): w.sha(x) for x in folder.iterdir() if x.is_file()}})
    reference = pd.read_parquet(REF); combined = pd.concat(parts); assert combined.row_id.is_unique and set(combined.row_id) == set(reference.row_id)
    combined = combined.set_index('row_id', drop=False).loc[reference.row_id].reset_index(drop=True)
    for key in ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']: assert np.array_equal(combined[key], reference[key])
    combined['old_nominal'] = reference.old_nominal.to_numpy()
    reserve = pd.concat([pd.read_parquet(P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in q.LINES]).set_index('row_id').loc[combined.row_id].reserve.to_numpy()
    y = combined.T0.to_numpy(float); ys = [y, y-.25*reserve, y+.25*reserve, y, y]; data = [(y, combined.old_nominal.to_numpy(), combined.new_nominal.to_numpy())]
    for j, name in enumerate(e.NAMES[1:], 1): combined[name+'_old'] = reference[name+'_old'].to_numpy(); data.append((ys[j], combined[name+'_old'].to_numpy(), combined[name+'_new'].to_numpy()))
    combined.to_parquet(OUT/'POOLED_prices.parquet', index=False)
    weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[combined.row_id]; assert np.array_equal(weights.group_id, combined.group_id)
    metrics = e.metrics(combined, data, 'POOLED', weights.weight.to_numpy(float), plan); cohorts = cohort_analysis(); a = metrics['NOMINAL']; crit = plan['criteria']
    gates = {'pooled_delta_ge002': a['delta'] >= crit['nominal_pooled_delta_min'], 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
        'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4, 'both_pooled_years_nonnegative': min(a['years'].values()) >= 0,
        'pooled_post31_nonnegative': a['post31_delta'] >= 0, 'all_nominal_and_stress_cell_floors': all(v['worst_cell_delta'] >= -.001 for v in metrics.values())}
    passed = all(gates.values()) and all(cohorts['gates'].values()); check_sources(plan)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P52pooled_complete_transfer_not_evaluated', 'plan_sha256': w.sha(PLAN), 'results': {'POOLED': metrics, 'TRANSFER': None},
        'pooled_gates': gates, 'pooled_cohort_gates': cohorts['gates'], 'all_pooled_gates_pass': passed, 'conditional_transfer_gate': None,
        'all_required_gates_pass': False, 'decision': 'TRANSFER_REQUIRED_BEFORE_ADMISSION' if passed else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED',
        'primary_target_closed_learners': 15, 'adverse_target_closed_learners_separate': 15, 'primary_constants': dict(counts),
        'new_source_fits': 0, 'primary_branch_CDFs': 110, 'adverse_branch_CDFs_separate': 110, 'new2025inference': 0, 'new_submissions': 0,
        'adopted': False, 'private_improvement_established': False, 'goal_achieved': False, '2024_open': True}
    dump(OUT/'report.json', report); print(json.dumps({'decision': report['decision'], 'nominal': {k:a[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}, 'gates': gates, 'cohort_gates': cohorts['gates']}))


def replay():
    assert not (OUT/'replay_report.json').exists(); plan = w.read(PLAN); check_sources(plan); report = w.read(OUT/'report.json')
    def reject(*a, **kw): raise AssertionError('No learning/source inference/report fit during P52replay')
    for module, key in [(p, 'learn'), (p.b, 'shape_fit'), (p.b, 'cell_levels'), (p.b, 'factor'), (p.g, 'fit_stage'), (q, 'cost_curves')]: setattr(module, key, reject)
    for outer in range(5):
        for line in q.LINES:
            folder = OUT/f'{line}_{outer}'; commit = w.read(folder/'committed.json'); assert all(w.sha(ROOT/k) == v for k, v in commit['outputs'].items())
            f = frame_for(line, outer); f.loc[f.is_held, ['T0', 'reserve']] = 1e30
            value, norms = p.forward(f.loc[f.is_held], w.read(folder/'learning.json'), True)
            assert np.array_equal(value, pd.read_parquet(folder/'prices.parquet').ultimate) and norms == commit['ultimate_normalizers']
    totals, desc, _, _ = cohort_blocks(); saved = np.load(OUT/'cohort_bootstrap.npy'); weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(cohort_scores(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    cohort = w.read(OUT/'cohort_report.json')
    for j, z in enumerate(cohort['comparisons']): assert desc[j]['delta'] == z['delta'] and np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), z['family16_band95'])
    draws = np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j, name in enumerate(e.NAMES): assert np.array_equal(np.quantile(draws[:, j], [.025, .975]), report['results']['POOLED'][name]['bootstrap95'])
    check_sources(plan); dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'report_sha256': w.sha(OUT/'report.json'),
        'all15saved_member_flows_exact': True, 'learning_and_report_fits_blocked': True, 'saved_intervals_and_first4weights_exact': True, 'new_fits': 0, 'new_resampling': 0})
    print(json.dumps({'replay': 'exact', 'members': 15, 'new_fits': 0, 'transfer_not_evaluated': True}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); assert w.read(OUT/'replay_report.json')['report_sha256'] == w.sha(OUT/'report.json')
    passed = d['all_pooled_gates_pass']; number = sum(d['primary_constants'].values()); a = d['results']['POOLED']['NOMINAL']
    next_unit = ('Prepare own conditional-transfer2023training reporting/source for A1R; pooled pass is insufficient. Freeze exact source/report/pricecost/criteria before fitting, no copied pooledobjects or automatic production/upload.' if passed else
        'Review the NEW A1Rpooled loss using saved parameters and group/cell support before another recipe. No need to spend90transfer sourcefits on a candidate already rejected by unchanged pooled guards. Transfer remains missing, never certified as zero. Preserve all A1Rsource models and priors; no K/profile/line rescue or public probes. Select a materially justified standard mechanism, not repeat PS1or old source searches.')
    text = '# P52: A1Rcompleto, primera puerta de validación en destino\n\nCodex, '+utc()+'. '+('El combinado pasa las guardas aplicables. La transferencia propia sigue siendo obligatoria antes de admitir un CSV.' if passed else 'El combinado falla las guardas aplicables. Se conserva sin adopción; la transferencia no fue evaluada.')
    text += f"\n\nΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text += 'Quince calibradores cerrados primarios y15adversos, fuente y CDFpropios por fold; calendario una vez y avance a último. Es un aprendiz completo con tres semillas fuente por ramo, no una media targetde cinco aprendices. Se conservan todos los ramos/años/negocios/folds, nivel, reservas y cola, así como NB/broker/historia cero y bandas16. Las110curvas de escenario primarias y110adversas cambiaron la valoración de observación, no los árboles o últimos nominales. No se afirma reentrenamiento completo de cada escenario.\n\n'
    text += 'Guardas combinadas: '+json.dumps(d['pooled_gates'])+'. Guardas de cohortes: '+json.dumps(d['pooled_cohort_gates'])+'. Transferencia: no evaluada, sin delta o aprobación inventados. El rechazo combinado basta para detener un candidato, pero aprobarlo exigiría la transferencia pendiente.\n\n'
    text += f'Constantes primarias nuevas:{number}. Se verificó la invariancia al alterar T0/reservas retenidos, niveles por sumas independientes y15replays con aprendizaje bloqueado. Fuente P51no se cuenta otra vez. Cero inferencias2025o envíos. B00/F3c/adversos conservados;2024abierto adaptativo. Fuente2024condicional, supuesto de reporte, maestros sin fecha, cola y búsqueda adaptativa limitan la generalización. No es mejora privada acreditada ni revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': d['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC),
        'decision': d['decision'], 'nominal': {k:a[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}, 'all_pooled_gates_pass': passed, 'conditional_transfer_gate': None,
        'primary_closed_learners': 15, 'adverse_closed_learners_separate': 15, 'new_primary_constants': number, 'new_source_fits': 0, 'primary_branch_CDFs': 110,
        'adverse_branch_CDFs_separate': 110, 'new2025inference': 0, 'new_submissions': 0, 'next_unit': next_unit, '2024_open': True, 'goal_achieved': False,
        'forum': q.post(body, 'COD-S2-20261027-PRIVADA-P52-A1R-RESULTADO', 'P52: A1Rcompleto, guardas combinadas y transferencia sin inventar')}
    archive = R/'privado'/('corte_P52_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    count_path = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(count_path); assert 'phase2_private_P52_A1R_target' not in counts
    w.update(count_path, {'as_of_utc': utc(), 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+number,
        'phase2_private_P52_A1R_target': {'primary_closed_learners': 15, 'adverse_closed_learners_separate': 15, 'new_primary_constants': number, 'primary_branch_CDFs': 110,
            'adverse_branch_CDFs_separate': 110, 'synthetic_curve_calls': 2, 'synthetic_primary_learners': 3, 'synthetic_adverse_learners_separate': 3, 'new_source_fits': 0}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P52': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P52': receipt, 'next_unit': next_unit}, archive)
    state_path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state_path)['week_2_mission017_phase2_20261025']; own.update(private_P52=receipt, next_unit=next_unit)
    w.update(state_path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P52: A1Rcompleto en destino\n\nCodex, '+receipt['utc']+'. Decisión='+d['decision']+f'.15calibradores primarios/15adversos,{number}constantes;110curvas de escenario primarias/110adversas, replay exacto. Transferencia no evaluada. Cero fuente nueva/inferencias2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_A1R_target_validation_index': w.rel(INDEX), 'week_2_private_A1R_target_validation_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'decision': d['decision'], 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['synthetic', 'prepare', 'run', 'replay', 'close']); mode = a.parse_args().mode
    with e.threadpool_limits(limits=2): {'synthetic': synthetic, 'prepare': prepare, 'run': run, 'replay': replay, 'close': close}[mode]()
