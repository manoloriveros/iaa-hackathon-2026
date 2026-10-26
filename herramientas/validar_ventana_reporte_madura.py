"""P7: reconstrucción de coste en cohorte desarrollada2021 y cortes virtuales.

Marcas/status finales comunes de2024, no reservas reconstruidas a2022/2023.
No es CVde precios, no aporta soporte emergente ni identifica la cola infinita.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import os
import sys
import subprocess

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P7_ventana_reporte_madura_20261026_v2'
PLAN = R/'registro/semana2_ventana_reporte_madura_plan_v2.json'
RAW = ROOT/'Hackaton/Semana 1/Datos/claims.parquet'
CUTS = [('20221231', '2022-12-31'), ('20231231', '2023-12-31')]
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader')); sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(sp); sp.loader.exec_module(module); return module


parent = load('P7_pinned_standard_reporting', R/'herramientas/validar_transferencia_anual_H1.py')
v = parent.v; w = parent.w; n = parent.n; digest = parent.b.digest


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream: json.dump(value, stream, ensure_ascii=False, indent=2)


def event(folder, kind, **fields):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'events.jsonl').open('a', encoding='utf8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'kind': kind, **fields})+'\n')


def independent_math(model, delay, age, net):
    """Sorted risk-count identity + log-product + event-probability cost masses."""
    support, events = np.unique(delay, return_counts=True)
    risk = np.searchsorted(np.sort(delay), support, side='right')-np.searchsorted(np.sort(age), support, side='left')
    assert np.array_equal(risk, model['risk_set']) and np.array_equal(events, model['events'])
    hazard = events/risk
    with np.errstate(divide='ignore'):
        logs = np.log1p(-hazard)
    # F(d_j) excludes the hazard at d_j itself. The first hazard can equal1.
    cdf = np.ones(len(support))
    if len(cdf) > 1: cdf[:-1] = np.exp(np.cumsum(logs[:0:-1])[::-1])
    assert np.max(np.abs(cdf-np.asarray(model['count_cdf']))) < 3e-12
    mass = np.diff(np.r_[0., cdf]); index = np.searchsorted(support, delay)
    probability = mass[index]/events[index]
    mean = math.fsum((probability*net).tolist())
    costcdf = np.cumsum(np.bincount(index, weights=probability*net, minlength=len(support)))/mean
    error = float(np.max(np.abs(costcdf-np.asarray(model['cost_cdf']['1.0']))))
    assert math.isclose(mean, model['mean_net_mark']['1.0'], rel_tol=3e-12) and error < 3e-12
    return {'count_CDF_log_product_max_error': float(np.max(np.abs(cdf-np.asarray(model['count_cdf'])))),
            'mean_relative_error': abs(mean/model['mean_net_mark']['1.0']-1), 'cost_CDF_max_error': error}


def learning(claims, line, fold, cut, cutoff, folder, log, role):
    """Fixed metadata selects observed training rows before protected fields."""
    train = claims.loc[claims.fold.ne(fold) & claims['available_'+cut] & claims.accepted_final].copy()
    assert train.fold.ne(fold).all() and train.cohort_year.eq(2021).all()
    assert train.source_group.notna().all()
    perils = PERILS[line]; result = {}; controls = {}; fitted = 0; reused = 0
    for peril in perils:
        c = train.loc[train.peril.eq(peril)].copy()
        assert len(c) >= 5
        loss = pd.to_datetime(c.loss_date); report = pd.to_datetime(c.report_date)
        assert report.le(cutoff).all() and report.ge(loss).all()
        delay = (report-loss).dt.days.to_numpy(); age = (pd.Timestamp(cutoff)-loss).dt.days.to_numpy()
        net = c.T0_cents.to_numpy(float)/100; reserve = c.reserve_cents.to_numpy(float)/100
        assert np.isfinite(net).all() and (net >= 0).all()
        signature = n.args_digest((delay, age, net, reserve)); path = folder/(peril+'.json')
        folder.mkdir(parents=True, exist_ok=True)
        selected_digest = digest(c.claim_id.tolist())
        if path.exists():
            item = w.read(path); assert item['argument_digest'] == signature
            model = item['model']
        else:
            # For fully observed identical samples, changing only a larger
            # followup cannot change the empirical distribution. Reuse rather
            # than re-estimate that exact distribution in the second window.
            oldpath = folder.parent.parent/'20221231'/role/(peril+'.json')
            old = w.read(oldpath) if cut == '20231231' and oldpath.exists() else None
            can_reuse = (old is not None and old['selected_claim_digest'] == selected_digest
                         and old['untruncated'] and int(age.min()) >= int(delay.max())
                         and old['mark_digest'] == digest([net.tolist(), reserve.tolist()]))
            if can_reuse:
                model = json.loads(json.dumps(old['model'])); model['max_followup'] = int(age.max())
                event(log, 'reporting_distribution_reused', line=line, fold=fold, cut=cut, role=role, peril=peril,
                      reason='Identical fully observed events and marks; risksets and distribution unchanged', source_sha256=w.sha(oldpath))
                reused += 1
            else:
                event(log, 'reporting_started', line=line, fold=fold, cut=cut, role=role, peril=peril)
                model, _ = v.fit_reporting(delay, age, net, reserve); fitted += 1
                event(log, 'reporting_completed', line=line, fold=fold, cut=cut, role=role, peril=peril)
            dump(path, {'argument_digest': signature, 'selected_claim_digest': selected_digest,
                        'mark_digest': digest([net.tolist(), reserve.tolist()]),
                        'training_groups_digest': digest(sorted(set(c.source_group))),
                        'untruncated': bool(int(age.min()) >= int(delay.max())), 'model': model})
        controls[peril] = independent_math(model, delay, age, net)
        result[peril] = model
    return result, controls, {'new_fits_this_call': fitted, 'reused_distributions_this_call': reused}


def cost_completion(ages, model):
    ages = np.asarray(ages, int); assert (ages >= 0).all()
    support = np.asarray(model['delay_days']); curve = np.asarray(model['cost_cdf']['1.0'])
    index = np.searchsorted(support, ages, side='right')-1
    q = np.where(index >= 0, curve[np.maximum(index, 0)], 0.)
    assert np.isfinite(q).all() and (q > 0).all() and (q <= 1+1e-12).all(), 'Zero cost completion: no floor allowed'
    return q


def reconstruction(claims, line, fold, cut, cutoff, models):
    observed = claims.loc[claims.fold.eq(fold) & claims['available_'+cut] & claims.accepted_final].copy()
    assert not set(observed.source_group).intersection(claims.loc[claims.fold.ne(fold), 'source_group'])
    out = []
    for peril in PERILS[line]:
        c = observed.loc[observed.peril.eq(peril)].copy()
        age = (pd.Timestamp(cutoff)-pd.to_datetime(c.loss_date)).dt.days.to_numpy()
        q = cost_completion(age, models[peril]); value = c.T0_cents.to_numpy(float)/100
        assert (value >= 0).all()
        out.append(pd.DataFrame({'claim_id': c.claim_id.to_numpy(), 'source_group': c.source_group.to_numpy(),
                                 'fold': fold, 'line': line, 'peril': peril, 'cut': cut,
                                 'observed_cost': value, 'reconstructed_cost': value/q,
                                 'completion': q, 'loss_quarter': c.loss_quarter.to_numpy()}))
    return pd.concat(out, ignore_index=True)


def poison_learning(claims, fold, cut):
    bad = claims.copy(); mask = bad.fold.eq(fold) | ~bad['available_'+cut]
    bad.loc[mask, 'T0_cents'] = np.int64(-(1 << 61)); bad.loc[mask, 'reserve_cents'] = np.int64(1 << 61)
    bad.loc[mask, 'accepted_final'] = True
    for column in ['loss_date', 'report_date', 'peril']:
        bad[column] = bad[column].astype(object); bad.loc[mask, column] = '__PROTECTED__'
    return bad


def poison_unavailable_reference(claims, cut):
    bad = claims.copy(); mask = ~bad['available_'+cut]
    bad.loc[mask, 'T0_cents'] = np.int64(1 << 61); bad.loc[mask, 'reserve_cents'] = np.int64(-(1 << 61))
    bad.loc[mask, 'accepted_final'] = True
    for column in ['loss_date', 'report_date', 'peril']:
        bad[column] = bad[column].astype(object); bad.loc[mask, column] = '__UNAVAILABLE__'
    return bad


PERILS = {'motor': ['bodily_injury', 'glass_hail', 'own_damage', 'theft', 'third_party_prop'],
          'buildings': ['accidental_damage', 'escape_of_water', 'fire', 'flood', 'storm', 'subsidence'],
          'contents': ['accidental_damage', 'escape_of_water', 'flood', 'theft']}


def synthetic():
    rng = np.random.default_rng(2026102635); checks = []
    # One representative peril per line tests the full selection/learning/
    # reconstruction entry point; the real schema/peril catalogue is preflighted.
    original_perils = json.loads(json.dumps(PERILS))
    try:
        for line, peril in [('motor', 'bodily_injury'), ('buildings', 'subsidence'), ('contents', 'flood')]:
            PERILS[line] = [peril]; size = 1500; groups = np.arange(size)
            loss = pd.Timestamp('2021-01-01')+pd.to_timedelta(rng.integers(0, 365, size), unit='D')
            delay = rng.choice([0, 30, 180, 500, 800, 1000], size, p=[.2, .2, .2, .15, .15, .1])
            report = loss+pd.to_timedelta(delay, unit='D'); net = rng.integers(1000, 50000, size, dtype=np.int64)
            c = pd.DataFrame({'claim_id': [line+str(i) for i in range(size)], 'source_group': ['g'+str(i) for i in groups],
                              'fold': groups % 5, 'cohort_year': 2021, 'line': line, 'peril': peril,
                              'loss_date': loss, 'report_date': report, 'T0_cents': net, 'reserve_cents': net//5,
                              'accepted_final': True, 'loss_quarter': pd.DatetimeIndex(loss).quarter})
            for cut, cutoff in CUTS: c['available_'+cut] = c.report_date.le(cutoff)
            for cut, cutoff in CUTS:
                folder = OUT/'synthetic'/line/'fold0'/cut
                a, _, _ = learning(c, line, 0, cut, cutoff, folder/'primary', OUT/'synthetic', 'primary')
                z, _, _ = learning(poison_learning(c, 0, cut), line, 0, cut, cutoff, folder/'poison', OUT/'synthetic', 'poison')
                assert digest(a) == digest(z)
                p = reconstruction(c, line, 0, cut, cutoff, a)
                pp = reconstruction(poison_unavailable_reference(c, cut), line, 0, cut, cutoff, a)
                assert p.equals(pp)
                checks.append({'line': line, 'cut': cut, 'held_and_unavailable_learning_payload_invariant': True,
                               'unavailable_future_marks_perils_dates_not_read_by_reconstruction': True})
            # If every delay is within the shortest followup, no correction is
            # needed and reported/mature/reconstructed cost coincide exactly.
            flat = c.copy(); flat['report_date'] = pd.to_datetime(flat.loss_date)+pd.Timedelta(days=10)
            for cut, cutoff in CUTS: flat['available_'+cut] = True
            a, _, _ = learning(flat, line, 0, '20221231', '2022-12-31', OUT/'synthetic'/line/'flat/primary', OUT/'synthetic', 'flat')
            p = reconstruction(flat, line, 0, '20221231', '2022-12-31', a)
            assert np.array_equal(p.observed_cost, p.reconstructed_cost)
            # Add entirely unobserved-at-cut claims without changing the
            # observable training sample. The same estimator cannot identify
            # that missing mass from its observed inputs.
            extra = c.loc[~c.available_20221231].copy(); extra.claim_id = extra.claim_id+'extra'
            extra['T0_cents'] *= 2
            augmented = pd.concat([c, extra], ignore_index=True)
            original, _, _ = learning(c, line, 0, '20221231', '2022-12-31', OUT/'synthetic'/line/'identifiability/original', OUT/'synthetic', 'identifiability')
            augmented_model, _, _ = learning(augmented, line, 0, '20221231', '2022-12-31', OUT/'synthetic'/line/'identifiability/augmented', OUT/'synthetic', 'identifiability')
            assert digest(original) == digest(augmented_model)
            assert reconstruction(c, line, 0, '20221231', '2022-12-31', original).equals(reconstruction(augmented, line, 0, '20221231', '2022-12-31', augmented_model))
    finally:
        PERILS.clear(); PERILS.update(original_perils)
    return {'author': 'Codex', 'checks': checks, 'fully_observed_identity_exact': True,
            'unobserved_mass_nonidentifiability_counterexample_exact': True,
            'synthetic_reporting_calls': 21, 'new_price_fits': 0, 'contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    previous = w.read(HOME/'report.json'); assert w.sha(RAW) == previous['sources'][w.rel(RAW)]
    claims = pd.read_parquet(RAW)
    duplicated = claims.duplicated([x for x in claims if x != 'claim_id'], keep=False) & claims.claim_id.str.len().eq(11)
    assert int(duplicated.sum()) == 604
    claims = claims.loc[~duplicated].copy()
    claims['loss_date'] = pd.to_datetime(claims.loss_date); claims['report_date'] = pd.to_datetime(claims.report_date)
    claims = claims.loc[claims.loss_date.dt.year.eq(2021)].copy()
    assert claims.report_date.ge(claims.loss_date).all() and claims.report_date.le('2024-12-31').all() and claims.claim_id.is_unique
    claims['T0_cents'] = np.rint(claims.incurred_to_date.to_numpy()*100).astype(np.int64)-np.rint(claims.recoveries.to_numpy()*100).astype(np.int64)
    claims['reserve_cents'] = np.rint(claims.incurred_to_date.to_numpy()*100).astype(np.int64)-np.rint(claims.paid_to_date.to_numpy()*100).astype(np.int64)
    claims['accepted_final'] = claims.status.ne('repudiated')
    assert claims.T0_cents.ge(0).all() and claims.reserve_cents.ge(0).all()
    frames = []; files = [RAW, HOME/'report.json', HOME/'partition_source/report.json']; checks = []
    for line in PERILS:
        rp = HOME/f'rows_s1_{line}.parquet'; fp = HOME/f'partition_source/folds_{line}.parquet'; files += [rp, fp]
        f = pd.read_parquet(rp, filters=[('year', '=', 2021)], columns=['row_id', 'customer_id', 'address_id', 'policy_id', 'year', 'period_start', 'period_end', 'T0_cents'])
        folds = pd.read_parquet(fp, filters=[('year', '=', 2021)], columns=['row_id', 'source_group', 'fold'])
        f = f.merge(folds, on='row_id', validate='one_to_one'); f['line'] = line
        frames.append(f)
        c = claims.loc[claims.line.eq(line)].merge(f, on=['policy_id', 'line'], how='left', suffixes=('', '_period'))
        c = c.loc[c.loss_date.ge(c.period_start) & c.loss_date.le(c.period_end)].copy()
        assert c.claim_id.is_unique, 'Ambiguous source2021claim assignment'
        # A calendar-year loss is not necessarily inside an observed policy
        # period. Preserve and reconcile that original coverage exclusion;
        # never enlarge the cohort denominator with precoverage claims.
        oldpath = BASE/f'fuente_f2_2024_v2/unassigned_{line}.parquet'
        old = pd.read_parquet(oldpath, columns=['claim_id', 'loss_date'])
        old = old.loc[pd.to_datetime(old.loss_date).dt.year.eq(2021)]
        missing = claims.loc[claims.line.eq(line) & ~claims.claim_id.isin(c.claim_id)]
        assert set(missing.claim_id) == set(old.claim_id), 'New sourcecoverage discrepancy: stop before learning'
        files.append(oldpath)
        missing.to_parquet(OUT/f'outside_observed2021coverage_{line}.parquet', index=False)
        expected = f.T0_cents.sum(); observed = c.loc[c.accepted_final, 'T0_cents'].sum(); assert expected == observed
        checks.append({'line': line, 'periods': len(f), 'claims': len(c), 'accepted_claims': int(c.accepted_final.sum()),
                       'cost_cents_reconciled': int(observed), 'calendar2021outsidecoverage_preserved': len(missing),
                       'outsidecoverage_exact_original_unassigned_IDs': True})
        keep = ['claim_id', 'row_id', 'line', 'peril', 'source_group', 'fold', 'loss_date', 'report_date', 'T0_cents', 'reserve_cents', 'accepted_final']
        c = c[keep].copy(); c['cohort_year'] = 2021; c['loss_quarter'] = c.loss_date.dt.quarter
        for cut, cutoff in CUTS: c['available_'+cut] = c.report_date.le(cutoff)
        c.to_parquet(OUT/f'cohort_claims_{line}.parquet', index=False)
        files.append(OUT/f'cohort_claims_{line}.parquet')
    periods = pd.concat(frames, ignore_index=True)
    assert periods.row_id.is_unique and periods.groupby('source_group').fold.nunique().max() == 1
    group = periods[['source_group', 'fold']].drop_duplicates(); group.to_parquet(OUT/'cohort_groups.parquet', index=False)
    files.append(OUT/'cohort_groups.parquet'); scopes = []
    for line, perils in PERILS.items():
        c = pd.read_parquet(OUT/f'cohort_claims_{line}.parquet')
        for fold in range(5):
            for cut, cutoff in CUTS:
                selected = c.loc[c.fold.ne(fold) & c['available_'+cut] & c.accepted_final]
                counts = selected.peril.value_counts().reindex(perils, fill_value=0)
                assert counts.min() >= 5
                scopes.append({'line': line, 'fold': fold, 'cut': cut, 'cutoff': cutoff,
                               'train_claims': len(selected), 'minimum_peril_reports': int(counts.min()),
                               'training_claim_digest': digest(selected.claim_id.tolist()),
                               'training_groups_digest': digest(sorted(set(selected.source_group)))})
    dump(OUT/'preflight.json', {'author': 'Codex', 'scope_count': len(scopes), 'scopes': scopes, 'reconciliation': checks,
                               'global_source_groups': len(group), 'all_source_customer_address_edges_protected': True,
                               'reference': 'Known nonrepudiated final2024cost for assigned2021sourceclaims; not infinite ultimate or historical asofmarks',
                               'new_price_fits': 0, 'new_reporting_fits': 0})
    dump(OUT/'synthetic_report.json', synthetic())
    bibliography = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
                    'sources': [{'url': 'https://doi.org/10.1093/biomet/asz023', 'title': 'Nonidentifiability in the presence of factorization for truncated data',
                                 'use': 'Primary bibliographic/search excerpts only: truncation assumptions can remain unidentifiable; not a claim that this competition follows them.',
                                 'access': 'PMCrecaptcha and directpublisher/repository fetch unavailable; no fulltextaccess claimed'},
                                {'url': 'https://www.mdpi.com/2227-9091/4/3/25', 'title': 'Understanding Reporting Delay in General Insurance',
                                 'use': 'Primary abstract: reporting-delay modelling can involve nonstationarity, trends and seasonal patterns. Alternative explanations retained.',
                                 'access': 'Searchabstract retrieved, directfetch429; no fulltextaccess claimed'}],
                    'calculation_basis': 'Actual existing code and independently derived discrete risksets/logproducts. Literature snippets are context, not validation of the code, source transport or inferred tail.'}
    dump(OUT/'literature_context.json', bibliography)
    files += [Path(__file__), Path(parent.__file__), Path(v.__file__), Path(n.__file__), Path(w.__file__),
              OUT/'preflight.json', OUT/'synthetic_report.json', OUT/'literature_context.json',
              BASE/'P6_productor_S2_H1_nominal_20261026_v1/report.json', BASE/'P6_productor_S2_H1_nominal_20261026_v1/level_context.json',
              R/'herramientas/auditar_cola_fuente_A1S.py', HOME/'source_tail_seed_audit/report.json',
              R/'herramientas/registrar_F03_desarrollado2023.py', R/'src/semana2/fuente_f2_2024_cb.py',
              R/'registro/semana2_mision_privada_plan_v1.json', R/'registro/semana2_control_entregas_codex_actual.json',
              BASE/'P7_ventana_reporte_madura_20261026_v1/defect_before_real_start.json',
              BASE/'P7_ventana_reporte_madura_20261026_v1/preflight_attempt_v1.py']
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'type': 'P7_conditional_mature_source_reporting_window_backtest',
            'repair_before_real_fits': 'V1incorrectlyrequired every calendar2021claim to lie in observed2021policycoverage. V2reconciles outsidecoverageIDs exactly against originalsourceunassignedfiles and retains them separately. Cohort was always assigned2021coverage. V1had zero real/syntheticfits and no preregisteredscore; failure/code preserved.',
            'hypothesis': 'Short reporting windows plus F(maxdelay)=1can under-reconstruct cost of a more mature observed cohort. Test estimator behaviour before adopting any source-tail anchor or interpreting P6vsF3clevel gap causally.',
            'not_repeated': 'Bounded current-code/results review found no equivalent pseudo-truncation backtest. F03was documentary; A1Stail/seed audit concerned scoremass/seeddispersion; old6lateBIinventory and nominalsourceCDFreplays are preserved, not rerun.',
            'cohort': 'All assigned developed2021periods/claims after original604clone rule; same source global customer/address componentfolds. Repudiatedstatus and netmarks fixed at common2024-12-31snapshot. Reference is known2024cost, a finite lower bound for later/infinite ultimate. Zero-claim sourcegroups retained in cohort metadata.',
            'windows': CUTS, 'learning': 'For each line/fold/cut, choose traininggroups and available-at-cutmetadata before reading marks/perils/lossreportdates. Same reverse-productlimit v.fit_reporting; no mature/fullsourceCDFor targetC0as learnerinput. Fit on observed2021trainingclaims only. Cutmetadata frozen from official reportdates.',
            'held_calculation': 'Held reportedclaims atcut supply observed finalmarks and knownlossdate/peril as reconstructioninputs. q_i=estimatedcostCDF(cut-lossdate_i); reconstruct=sum(net_i/q_i), compare with all known2024nonrepudiatedheld2021cost. This is a reporting-cost nowcast diagnostic, not held-response-free pricingCV. Finalmarks would not generally be available at virtualcut, so no prospectivevaluation claim.',
            'protected': 'Actual learnedcurves must match under poisoning all heldpayload and all unavailabletrainingpayload, preserving eligibility/groupmetadata. Heldreconstruction must ignore unavailablefuture marks/perils/dates. Reportedheldmarks legitimately enter reconstruction and are not falsely poisoned as if pricescouldignorethem.',
            'math': 'Independent risk count via sorted D/A search; reverse logproduct CDF; event-probability costCDF/mean; directstep evaluation without hardcoded2024average_completion. No floor if heldcompletionzero.',
            'reuse': 'Across the secondwindow reuse only exactsame trainingclaim IDs/marks when both windows are fullyuntruncated(minage>=maxdelay): distribution/risksets identical; update nonestimatedfollowupmetadata. Each controlrole reuses only its own earliercurve, never primarycurves.',
            'primary': 'Total reconstructed/mature-knowncost ratio at each of two cuts, compared also with rawobserved/matureknownratio. Material underrecovery if paired-group Poissonbootstrap upper95family2 below.98. Report everyresult regardlesscriterion; no pricepromotion.',
            'secondary': 'All line/peril/fold/lossquarter ratios; exploratory marginal95perperil, not simultaneousclaims. LongtailBI/subsidenceunder.95reported as materialdescriptivewarning. Record maximumsinglemissingcostgroup and post31missingcostgroups without refitting/deletingrows from model.',
            'bootstrap': {'replicates': 2000, 'seed': 2026102636, 'unit': 'same global sourcecomponent', 'method': 'joint Poisson1weights across bothcuts/perils; zero-contributiongroups analytically omitted from ratio draws', 'primary_family': 2,
                          'conditional': 'Curve estimates fixed during bootstrap; not unconditional model uncertainty or independentcuts'},
            'budget': {'primary_reporting_calls_max': 150, 'adverse_reporting_calls_max_separate': 150,
                       'source_price_model_fits': 0, 'target_C0fits': 0, 'new_targetprices': 0, 'new_finaltestprices': 0, 'new_submissions': 0},
            'limits': ['Developed context does not create emerging support or identify transported delay/severitylaw',
                       'Finalmarks/status and fullsourcegroupmetadata make the exercise conditionalretrospective, not genuinepastdataavailability',
                       'Referenceobservedto2024stillmayomitlaterlossreports/development; no infiniteultimate claim',
                       'Calendar/seasonality/severityheterogeneity and sampling can also explain reconstructionerrors; tailcause or10.83percentgap not automatically identified',
                       'No tailprior/scale/pricefeatureadoption or publicscore inference from this diagnostic'],
            'scopes': scopes, '2024_open': True, 'B00_all_alternatives_preserved': True, 'submission_allowed': False,
            'sources': {w.rel(p): w.sha(p) for p in files}}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. RegistroP7antes de ajustes reales: backtest de ventana de reporte en cohorte desarrollada2021, '
                    'con cortes virtuales fin2022/2023y referencia observada fin2024. Se mantienen marcas/status finales; '
                    'no es un pronóstico de reservas históricas niCVde precios. Los grupos cliente/dirección fuente ya guardados '
                    'excluyen completamente los retenidos del aprendizaje de curvas. La reconstrucción retenida usa solo '
                    'los costes ya reportados al corte y su completitud estimada, comparados después con el coste maduro conocido. '
                    'Las curvas deben resistir corrupción de retenidos/futuros; la reconstrucción debe ignorar etiquetas futuras, '
                    'sin fingir que puede ignorar el coste reportado que es su entrada. Se comprobarán riesgo, producto-límite y coste por otro método. '
                    'Máximo150curvas primarias y150controles separados; se reutilizan distribuciones exactamente iguales de muestras completas. '
                    'El flujo sintético pasó en tres ramos, con identidad sin truncamiento y contraejemplo de masa invisible. '
                    'No repite inventario de seis tardíos o auditoría de semillas, no altera C0emergente/preciosP6, no adopta cola fuente, '
                    'no añade soporte emergente y no envía. Plan: '+w.rel(PLAN)+'.', encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-P7-VENTANA-V2-PREVIO', '--asunto',
                          'P7 registrado: ventana de reporte sobre cohorte madura, sin cambiar precios', '--cuerpo', str(body)],
                         check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(res.stdout)})
    print(json.dumps({'registered': True, 'scope_count': len(scopes), 'minimum_peril': min(s['minimum_peril_reports'] for s in scopes),
                      'sourcegroups': len(group), 'synthetic': w.read(OUT/'synthetic_report.json'), 'forum': json.loads(res.stdout)}))


def actual_counts():
    path = OUT/'events.jsonl'
    rows = [json.loads(s) for s in path.read_text(encoding='utf8').splitlines()] if path.exists() else []
    return {role: {'reporting_started': sum(x['kind'] == 'reporting_started' and x['role'] == role for x in rows),
                   'reporting_completed': sum(x['kind'] == 'reporting_completed' and x['role'] == role for x in rows),
                   'distribution_reuses': sum(x['kind'] == 'reporting_distribution_reused' and x['role'] == role for x in rows)}
            for role in ['primary', 'poison']}


def summarize(claims, reconstruction_data):
    known = claims.loc[claims.accepted_final].copy(); known['known_cost'] = known.T0_cents.to_numpy(float)/100
    reference = known.groupby(['source_group', 'line', 'peril'], sort=True).known_cost.sum()
    # Zero-contribution source components do not enter any cost-ratio numerator
    # or denominator. Their Poisson weights cancel exactly; no data rows are
    # removed from learning/cohort metadata or from reported support.
    positive = reference.groupby(level=0).sum(); group_ids = positive.loc[positive.gt(0)].index.tolist()
    labels = [(line, peril) for line, perils in PERILS.items() for peril in perils]
    pos = {group: i for i, group in enumerate(group_ids)}; column = {key: i for i, key in enumerate(labels)}
    Y = np.zeros((len(group_ids), len(labels))); RR = np.zeros((len(group_ids), 2*len(labels))); OO = RR.copy()
    for (group, line, peril), value in reference.items():
        if group in pos: Y[pos[group], column[(line, peril)]] = value
    for k, (cut, _) in enumerate(CUTS):
        c = reconstruction_data.loc[reconstruction_data.cut.eq(cut)]
        sums = c.groupby(['source_group', 'line', 'peril'], sort=True)[['observed_cost', 'reconstructed_cost']].sum()
        for (group, line, peril), row in sums.iterrows():
            if group in pos:
                RR[pos[group], k*len(labels)+column[(line, peril)]] = row.reconstructed_cost
                OO[pos[group], k*len(labels)+column[(line, peril)]] = row.observed_cost
    assert (Y >= 0).all() and (OO >= 0).all() and (RR >= OO-1e-8).all()
    rng = np.random.default_rng(2026102636); sims = []; pooled = []
    both = np.column_stack([Y, RR]); width = len(labels)
    for start in range(0, 2000, 40):
        count = min(40, 2000-start)
        weights = rng.poisson(1., size=(count, len(group_ids))).astype(float)
        sums = weights@both; yy = sums[:, :width]; rr = sums[:, width:]
        denominator = np.tile(yy, (1, 2))
        assert (denominator > 0).all(), 'Undefined sourceperilbootstrap ratio; no draw silently omitted'
        sims.append(rr/denominator)
        pooled.append(np.column_stack([rr[:, :width].sum(axis=1)/yy.sum(axis=1), rr[:, width:].sum(axis=1)/yy.sum(axis=1)]))
    sims = np.vstack(sims); pooled = np.vstack(pooled)
    np.save(OUT/'joint_peril_recovery_bootstrap.npy', sims); np.save(OUT/'joint_primary_recovery_bootstrap.npy', pooled)
    foldmap = pd.read_parquet(OUT/'cohort_groups.parquet').set_index('source_group').fold
    groupfold = foldmap.loc[group_ids].to_numpy(); entries = []; primary = {}
    group_records = []
    for k, (cut, cutoff) in enumerate(CUTS):
        block = RR[:, k*width:(k+1)*width]; raw = OO[:, k*width:(k+1)*width]
        y = Y.sum(axis=1); r = block.sum(axis=1); o = raw.sum(axis=1)
        missing = y-r; rank = np.argsort(-missing); chosen = rank[missing[rank] > 0][:31]
        mask = np.ones(len(y), bool); mask[chosen] = False
        post = float(r[mask].sum()/y[mask].sum()) if y[mask].sum() > 0 else None
        ci = np.quantile(pooled[:, k], [.025, .975]).tolist(); family = np.quantile(pooled[:, k], [.0125, .9875]).tolist()
        primary[cut] = {'cutoff': cutoff, 'known2024_cost': float(y.sum()), 'observed_at_cut_cost_finalmarks': float(o.sum()),
                        'reconstructed_cost': float(r.sum()), 'raw_recovery': float(o.sum()/y.sum()),
                        'reconstructed_recovery': float(r.sum()/y.sum()), 'bootstrap95': ci, 'family2_exploratory95': family,
                        'material_underrecovery_family_upper_below098': bool(family[1] < .98),
                        'folds': {str(f): float(r[groupfold == f].sum()/y[groupfold == f].sum()) for f in range(5)},
                        'post31largest_missing_cost_groups_recovery_descriptive': post,
                        'removed_groups_for_diagnostic_only': len(chosen),
                        'reference_cost_share_of_chosen_groups': float(y[chosen].sum()/y.sum()),
                        'max_group_share_of_positive_missing_cost': float(np.max(np.maximum(missing, 0))/np.maximum(missing, 0).sum()) if (missing > 0).any() else 0.}
        for group, yy, rr, oo in zip(group_ids, y, r, o):
            group_records.append({'cut': cut, 'source_group': group, 'fold': int(foldmap.loc[group]),
                                  'known2024_cost': yy, 'reconstructed_cost': rr, 'observed_cost_finalmarks': oo})
        for j, (line, peril) in enumerate(labels):
            den = Y[:, j].sum(); est = block[:, j].sum(); obs = raw[:, j].sum()
            entries.append({'cut': cut, 'line': line, 'peril': peril, 'known2024_cost': float(den),
                            'raw_recovery': float(obs/den), 'reconstructed_recovery': float(est/den),
                            'exploratory_marginal95': np.quantile(sims[:, k*width+j], [.025, .975]).tolist(),
                            'material_longtail_point_below095': bool(peril in ['bodily_injury', 'subsidence'] and est/den < .95),
                            'folds': {str(f): float(block[groupfold == f, j].sum()/Y[groupfold == f, j].sum()) for f in range(5)}})
    pd.DataFrame(group_records).to_parquet(OUT/'held_source_group_reconstruction.parquet', index=False)
    quarters = []
    refq = known.groupby(['line', 'peril', 'loss_quarter']).known_cost.sum()
    for cut, _ in CUTS:
        obsq = reconstruction_data.loc[reconstruction_data.cut.eq(cut)].groupby(['line', 'peril', 'loss_quarter'])[['observed_cost', 'reconstructed_cost']].sum()
        for key, value in refq.items():
            assert key in obsq.index
            quarters.append({'cut': cut, 'line': key[0], 'peril': key[1], 'loss_quarter': int(key[2]),
                             'known2024_cost': float(value), 'raw_recovery': float(obsq.loc[key, 'observed_cost']/value),
                             'reconstructed_recovery': float(obsq.loc[key, 'reconstructed_cost']/value)})
    return {'primary': primary, 'by_peril': entries, 'by_loss_quarter': quarters,
            'positive_cost_groups_in_ratio_bootstrap': len(group_ids),
            'all_source_cohort_groups': len(foldmap), 'zero_cost_groups_analytically_omitted_from_ratio_draws': len(foldmap)-len(group_ids),
            'bootstrap_is_conditional_on_fitted_curves': True}


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(),
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT), 'kind': 'P7source_window_diagnostic_no_prices'}
    dump(OUT/'started.json', execution); n.OUT = OUT; n.set_execution(execution)
    pieces = []
    try:
        for item in plan['scopes']:
            line, fold, cut, cutoff = item['line'], item['fold'], item['cut'], item['cutoff']
            claims = pd.read_parquet(OUT/f'cohort_claims_{line}.parquet')
            folder = OUT/line/f'fold{fold}'/cut; folder.mkdir(parents=True, exist_ok=True)
            selected = claims.loc[claims.fold.ne(fold) & claims['available_'+cut] & claims.accepted_final]
            assert digest(selected.claim_id.tolist()) == item['training_claim_digest']
            primary, controls, count = learning(claims, line, fold, cut, cutoff, folder/'primary', OUT, 'primary')
            other, _, adverse_count = learning(poison_learning(claims, fold, cut), line, fold, cut, cutoff, folder/'poison', OUT, 'poison')
            assert digest(primary) == digest(other)
            p = reconstruction(claims, line, fold, cut, cutoff, primary)
            bad = reconstruction(poison_unavailable_reference(claims, cut), line, fold, cut, cutoff, primary)
            assert p.equals(bad)
            p.to_parquet(folder/'held_reconstruction.parquet', index=False); pieces.append(p)
            paths = [folder/'held_reconstruction.parquet', *list((folder/'primary').glob('*.json')), *list((folder/'poison').glob('*.json'))]
            dump(folder/'committed.json', {'line': line, 'fold': fold, 'cut': cut,
                                           'whole_curve_learning_protected_payload_invariant': True,
                                           'held_reconstruction_ignores_unavailable_payload': True,
                                           'math_controls': controls, 'primary_counts': count, 'adverse_counts_separate': adverse_count,
                                           'outputs': {w.rel(p): w.sha(p) for p in paths}})
            print(json.dumps({'line': line, 'fold': fold, 'cut': cut, 'complete': True,
                              'fitted': count['new_fits_this_call'], 'reused': count['reused_distributions_this_call']}), flush=True)
        allclaims = pd.concat([pd.read_parquet(OUT/f'cohort_claims_{line}.parquet') for line in PERILS], ignore_index=True)
        reconstruction_data = pd.concat(pieces, ignore_index=True)
        assert not reconstruction_data.duplicated(['cut', 'claim_id']).any()
        summary = summarize(allclaims, reconstruction_data); counts = actual_counts()
        assert all(counts[role]['reporting_completed']+counts[role]['distribution_reuses'] == 150 for role in ['primary', 'poison'])
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P7conditional_mature_reporting_window_backtest_complete',
                  'summary': summary, 'counts': counts, 'committed_scopes': 30, 'new_price_model_fits': 0,
                  'new_target_C0fits': 0, 'new_source_model_inference': 0, 'new_target_price_predictions': 0,
                  'new_final_test_prices': 0, 'new_submissions': 0, 'source_tail_prior_adopted': False,
                  'P6_prices_changed': False, 'private_improvement_established': False, 'formal_promotion': False,
                  'submission_allowed': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
                  'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'primary': summary['primary'], 'counts': counts,
                          'longtail_points': [r for r in summary['by_peril'] if r['peril'] in ['bodily_injury', 'subsidence']]}), flush=True)
    except Exception as exc:
        dump(OUT/f'failure_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.json',
             {'exception': type(exc).__name__, 'message': str(exc), 'counts': actual_counts(),
              'committed_scopes': len(list(OUT.glob('*/fold*/*/committed.json'))),
              'next': 'Preserve all curve/cache signatures and reconcile before resuming; no silent refit or relaxed criterion'})
        raise
    finally:
        n.set_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    before = w.sha(OUT/'events.jsonl'); original = v.fit_reporting; total = 0
    def reject(*args, **kwargs): raise AssertionError('No reporting refit in P7saved replay')
    v.fit_reporting = reject
    try:
        for item in plan['scopes']:
            line, fold, cut, cutoff = item['line'], item['fold'], item['cut'], item['cutoff']
            folder = OUT/line/f'fold{fold}'/cut; c = pd.read_parquet(OUT/f'cohort_claims_{line}.parquet')
            commit = w.read(folder/'committed.json'); assert all(w.sha(ROOT/p) == z for p, z in commit['outputs'].items())
            models, _, _ = learning(poison_learning(c, fold, cut), line, fold, cut, cutoff, folder/'primary', OUT, 'replay')
            predicted = reconstruction(poison_unavailable_reference(c, cut), line, fold, cut, cutoff, models)
            saved = pd.read_parquet(folder/'held_reconstruction.parquet'); assert predicted.equals(saved)
            total += len(predicted)
        assert w.sha(OUT/'events.jsonl') == before and all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    finally: v.fit_reporting = original
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P7saved_whole_flow_replay_exact',
              'scopes': 30, 'reconstructed_reported_claim_rows': total,
              'learning_blocked': True, 'protected_and_unavailable_payload_checks_exact': True,
              'fit_events_unchanged': True, 'new_reporting_fits': 0, 'new_price_fits': 0, 'new_scores': 0,
              'new_targetprices': 0, 'new_submissions': 0, 'report_sha256': w.sha(OUT/'report.json')}
    dump(OUT/'replay_report.json', result); print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay']); args = parser.parse_args()
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
