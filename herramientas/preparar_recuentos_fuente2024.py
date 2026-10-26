"""Recuentos por peril y pareja de observación número/importe, sin ajustar precios."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader')); sys.path.insert(0, str(R / 'src'))
import numpy as np
import pandas as pd
from semana2.variables_ultimo import average_completion

RAW = ROOT / 'Hackaton/Semana 1/Datos'
SOURCE = R / 'privado/semana2/mision017_fase2/fuente_f2_2024_v2'
OUT = SOURCE.parent / 'recuentos_fuente2024_v1'
PLAN = R / 'registro/semana2_mision017_recuentos_fuente2024_plan_v1.json'
LINES = ['motor', 'buildings', 'contents']; VAL = pd.Timestamp('2024-12-31'); LIMIT = 1095
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()
now = lambda: datetime.now(timezone.utc).isoformat()

def dump(path, data):
    with path.open('x', encoding='utf8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def count_cdf(delay):
    delay = np.asarray(delay, dtype=int); assert len(delay) >= 5 and (delay >= 0).all() and (delay <= LIMIT).all()
    count = np.bincount(delay, minlength=LIMIT + 1)
    cdf = count.cumsum() / count.sum()
    other = np.searchsorted(np.sort(delay), np.arange(LIMIT + 1), side='right') / len(delay)
    assert np.array_equal(cdf, other) and cdf[-1] == 1
    return {'delay_days': list(range(LIMIT + 1)), 'count_cdf': cdf.tolist()}

def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir(parents=True)
    toy = count_cdf([0, 0, 20, 60, 100])
    f = pd.DataFrame({'period_start': [pd.Timestamp('2024-12-31'), pd.Timestamp('2024-01-01')],
        'period_end': [pd.Timestamp('2024-12-31'), pd.Timestamp('2024-12-31')], 'is_test': False})
    q = average_completion(f, toy)
    for j, row in f.iterrows():
        ages = (VAL - pd.date_range(row.period_start, row.period_end)).days.to_numpy()
        assert abs(q[j] - np.mean(np.asarray(toy['count_cdf'])[np.minimum(ages, LIMIT)])) < 1e-12
    dump(OUT / 'synthetic.json', {'pass': True, 'count_CDF_searchsorted_second_method': True,
        'inclusive_calendar_integral_second_method': True, 'real_curves_estimated': 0, 'price_fits': 0})
    sources = [Path(__file__), R / 'src/semana2/variables_ultimo.py', RAW / 'claims.parquet', SOURCE / 'report.json',
        ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo/transfer2.py',
        ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo/completitud.py',
        R / 'registro/semana2_robustez2023_ciclo8_plan.json']
    for line in LINES:
        sources += [SOURCE / f'{line}.parquet', SOURCE / f'{line}_link.json',
            SOURCE.parent / f'entradas_temporales_v1/source_reporting_{line}.json']
    plan = {'id': 'S2-SOURCE-COUNT-LINK2024-v1', 'author': 'Codex', 'utc': now(),
        'purpose': 'Prepare coherent count/mark observation inputs for standard frequency research; no price-model training or performance claim',
        'prior_evidence': ['FS/FSp frequency uses cost-weighted completion and unadjusted observed marks; it is not automatically a broken pure-premium product',
            'Own cycle8 used source2023 observed/nominal counts and kept separate count/cost links in target adaptation',
            'Existing phase1 source reporting models use2021–2023 RKM, a different estimator/cohort from the mature empirical cost curves of the frozen source2021–2024'],
        'source_counts': 'Exactly the frozen F2 source rows2021–2024; same604 exact-attribute duplicate clones removed; nonrepudiated claims assigned by policy and inclusive loss-date interval; retain zero net amounts',
        'new_count_curve': {'estimator': 'empirical unweighted reporting-delay CDF in mature accepted claims',
            'valuation': '2024-12-31', 'maturity_days_min': LIMIT, 'delay_support': [0, LIMIT],
            'normalization': 'Conditional on observed delay<=1095, matching the cohort/support of existing cost CDF; tail beyond1095 remains unproven',
            'precoverage2020': 'May contribute reporting history only, never a fabricated policy row'},
        'cost_curves': 'Reuse unchanged full mature cost CDFs and cost mixture in source line_link.json; no new cost curve or target C0 fit',
        'identities': {'E_N': 'nominal inclusive calendar exposure × mean G_count over covered dates',
            'E_C': 'same exposure × existing mean G_cost over covered dates',
            'mark_observation_multiplier': 'E_C/E_N on positive E_N',
            'coherent_product': '(lambda*E_N) * (mu*E_C/E_N) = lambda*mu*E_C',
            'warning': 'Changing frequency to E_N while retaining observed marks without E_C/E_N does not preserve the ultimate-cost interpretation'},
        'criteria': ['All source row and per-row net cents match frozen source exactly', 'All accepted assigned claim counts reconcile, including zero marks',
            'Count CDF reproduced by sorted delays/searchsorted', 'Existing cost mixture reproduces frozen e_cost',
            'Direct calendar summation checks on one-day/year-end/full-year records', 'No positive count under zero E_N or positive cost under zero E_C may be silently clipped or deleted'],
        'zero_exposure': 'Retain all rows and flag zero observation exposure. Zero exposure with zero observed response is noninformative for that likelihood, not a coverage exclusion; positive-response violations block downstream modeling.',
        'budget': {'new_empirical_source_count_CDFs': 15, 'new_source_cost_CDFs': 0, 'new_emerging_C0_fits': 0,
            'new_price_fits': 0, 'new_price_constants': 0, 'new_model_price_inferences': 0, 'new_scores': 0, 'new_test_predictions': 0, 'submissions': 0},
        'sources': {rel(p): sha(p) for p in sources}, 'B00_preserved': True, 'all_alternatives_preserved': True,
        '2024_open_as_adaptive_development': True, 'no_new_recipe_for_price_yet': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Se registra la preparación de recuentos y vínculos por peril del desarrollado 2021–2024, sin ajustar modelos de precio. '
        'El FS/FSp histórico usa completitud de coste en la frecuencia y marcas observadas sin ajuste. Eso no representa una frecuencia última separada, '
        'pero su producto puede mantener coherencia de coste; no se lo declara erróneo ni se cambia su receta.\n\n'
        'Para interpretar por separado frecuencia y coste medio se necesitan E_N, E_C y el multiplicador de marca E_C/E_N. '
        'Se reconstruirán únicamente 15 CDF empíricas de número, con la misma cohorte madura y soporte de las CDF de coste ya congeladas. '
        'Las curvas de coste, C0 emergente y todos los precios permanecen intactos. Los objetos RKM fuente de la primera tanda usan otro corte/cohorte y se conservan como alternativas.\n\n'
        'Se conciliarán los 604 duplicados históricos, todos los siniestros aceptados asignados y cada céntimo de T0. Los siniestros anteriores a cobertura no se asignan a pólizas inventadas. '
        'Los ceros de exposición se conservan con banderas; si hay respuesta positiva bajo exposición nula, se registrará el fallo sin recortar o eliminar casos. '
        'Presupuesto: 15 estimaciones empíricas de reporte de número fuente, cero ajustes de precios, cero C0 emergente y cero envíos. '
        'Plan: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-RECUENTOS-FUENTE-PREVIO', '--asunto',
        'Número y marca por peril: preparación coherente de exposición, sin ajustar precios', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'real_price_fits': 0, 'source_count_CDF_budget': 15}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for p, digest in plan['sources'].items(): assert sha(ROOT / p) == digest, p
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    c = pd.read_parquet(RAW / 'claims.parquet')
    duplicate = c.duplicated([x for x in c if x != 'claim_id'], keep=False) & c.claim_id.str.len().eq(11)
    assert duplicate.sum() == 604; c = c.loc[~duplicate].copy(); assert c.claim_id.is_unique
    c['loss_date'] = pd.to_datetime(c.loss_date); c['report_date'] = pd.to_datetime(c.report_date)
    assert c.loss_date.dt.year.isin([2020, 2021, 2022, 2023, 2024]).all() and c.report_date.le(VAL).all()
    assert c.report_date.ge(c.loss_date).all()
    c['net'] = c.incurred_to_date - c.recoveries
    c['net_cents'] = np.rint(c.incurred_to_date * 100).astype('int64') - np.rint(c.recoveries * 100).astype('int64')
    assert c.net_cents.ge(0).all()
    curves = {}; curve_receipts = []
    for (line, peril), g in c.loc[c.status.ne('repudiated')].groupby(['line', 'peril']):
        mature = g.loc[(VAL - g.loss_date).dt.days.ge(LIMIT)]
        delay = (mature.report_date - mature.loss_date).dt.days.to_numpy(); keep = delay <= LIMIT
        curve = count_cdf(delay[keep]); curves[line + '|' + peril] = curve
        curve_receipts.append({'line': line, 'peril': peril, 'mature_claims': len(mature), 'support_claims': int(keep.sum()),
            'observed_mature_delay_beyond1095': int((~keep).sum()), 'precoverage2020_in_history': int(mature.loss_date.dt.year.eq(2020).sum()),
            'same_count_CDF_by_searchsorted': True})
    assert len(curves) == 15
    dump(OUT / 'count_curves.json', curves)
    dump(OUT / 'curves_completed.json', {'utc': now(), 'new_source_count_CDF_fits': 15, 'curves': curve_receipts,
        'new_price_fits': 0, 'new_target_C0_fits': 0, 'no_source_cost_CDF_refits': True})
    mapping = []; checks = []; exposure_summary = []; direct_checks = []
    for line in LINES:
        f = pd.read_parquet(SOURCE / f'{line}.parquet', columns=['row_id', 'policy_id', 'year', 'period_start', 'period_end', 'exposure', 'e_cost', 'T0_cents'])
        f['period_start'] = pd.to_datetime(f.period_start); f['period_end'] = pd.to_datetime(f.period_end); f['is_test'] = False
        assert f.year.isin([2021, 2022, 2023, 2024]).all() and f.row_id.is_unique
        g = c.loc[c.line.eq(line)].merge(f[['row_id', 'policy_id', 'period_start', 'period_end', 'year']], on='policy_id', how='left')
        assigned = g.loc[g.loss_date.ge(g.period_start) & g.loss_date.le(g.period_end)].copy()
        assert assigned.claim_id.is_unique
        mapping.append(assigned[['claim_id', 'row_id', 'line', 'peril', 'year', 'status', 'loss_date', 'report_date', 'net_cents']])
        accepted = assigned.loc[assigned.status.ne('repudiated')].copy()
        perils = sorted(read(SOURCE / f'{line}_link.json')['mature_cost_CDF'])
        links = read(SOURCE / f'{line}_link.json')
        output = f[['row_id', 'year', 'period_start', 'period_end', 'exposure']].copy(); output['line'] = line
        total_count = np.zeros(len(f), dtype='int64'); total_cents = np.zeros(len(f), dtype='int64'); mixed_cost_exposure = np.zeros(len(f))
        sample_ids = np.unique(np.r_[np.arange(min(3, len(f))), np.flatnonzero(f.period_end.eq(VAL))[:3],
            np.argsort((f.period_end - f.period_start).dt.days.to_numpy())[:3]])
        for peril in perils:
            claims = accepted.loc[accepted.peril.eq(peril)]
            n = f.row_id.map(claims.groupby('row_id').size()).fillna(0).to_numpy(dtype='int64')
            net = f.row_id.map(claims.groupby('row_id').net_cents.sum()).fillna(0).to_numpy(dtype='int64')
            position = pd.Index(f.row_id).get_indexer(claims.row_id); assert (position >= 0).all()
            other_n = np.bincount(position, minlength=len(f)); other_net = np.zeros(len(f), dtype='int64')
            np.add.at(other_net, position, claims.net_cents.to_numpy(dtype='int64'))
            assert np.array_equal(n, other_n) and np.array_equal(net, other_net)
            model_n = curves[line + '|' + peril]; model_c = links['mature_cost_CDF'][peril]
            qn = average_completion(f, model_n); qc = average_completion(f, model_c, 'cost', 1.)
            en = f.exposure.to_numpy(float) * qn; ec = f.exposure.to_numpy(float) * qc
            ratio = np.divide(ec, en, out=np.full(len(f), np.nan), where=en > 0)
            assert np.allclose(en[en > 0] * ratio[en > 0], ec[en > 0], rtol=1e-12, atol=1e-14)
            for i in sample_ids:
                ages = (VAL - pd.date_range(f.period_start.iloc[i], f.period_end.iloc[i])).days.to_numpy()
                direct = np.mean(np.asarray(model_n['count_cdf'])[np.minimum(ages, LIMIT)])
                assert abs(direct - qn[i]) < 1e-12
            n_bad = (n > 0) & (en <= 0); c_bad = (net > 0) & (ec <= 0)
            output[f'N_{peril}'] = n; output[f'T0_cents_{peril}'] = net
            output[f'E_count_{peril}'] = en; output[f'E_cost_{peril}'] = ec; output[f'mark_ratio_{peril}'] = ratio
            total_count += n; total_cents += net; mixed_cost_exposure += links['cost_shares'][peril] * ec
            for year in [2021, 2022, 2023, 2024]:
                sel = f.year.eq(year).to_numpy()
                exposure_summary.append({'line': line, 'peril': peril, 'year': year, 'periods': int(sel.sum()),
                    'N_observed': int(n[sel].sum()), 'net_cents': int(net[sel].sum()),
                    'E_count': float(en[sel].sum()), 'E_cost': float(ec[sel].sum()),
                    'count_to_cost_exposure_ratio': float(en[sel].sum() / ec[sel].sum()),
                    'zero_net_accepted_claims': int(claims.loc[claims.year.eq(year)].net_cents.eq(0).sum()),
                    'zero_count_exposure_rows': int(np.count_nonzero(sel & (en == 0))),
                    'positive_N_zero_E_count': int(np.count_nonzero(sel & n_bad)), 'positive_cost_zero_E_cost': int(np.count_nonzero(sel & c_bad))})
            direct_checks.append({'line': line, 'peril': peril, 'calendar_period_samples': len(sample_ids),
                'CDF_second_method': True, 'counts_and_cents_second_method': True, 'count_mark_cost_identity': True})
        assert total_count.sum() == len(accepted) and np.array_equal(total_cents, f.T0_cents.to_numpy(dtype='int64'))
        assert np.allclose(mixed_cost_exposure, f.e_cost.to_numpy(float), rtol=1e-12, atol=1e-14)
        output['N_total'] = total_count; output['T0_cents_total'] = total_cents
        output.to_parquet(OUT / f'counts_{line}.parquet', index=False)
        checks.append({'line': line, 'rows': len(f), 'accepted_assigned_claims': len(accepted),
            'zero_net_accepted_claims_retained': int(accepted.net_cents.eq(0).sum()), 'cost_cents': int(total_cents.sum()),
            'exact_per_row_frozen_T0_cents': True, 'existing_cost_mixture_reproduced': True,
            'unassigned_claims': int(c.line.eq(line).sum() - len(assigned))})
        print(json.dumps({'counts_ready': line, 'rows': len(f), 'accepted_claims': len(accepted), 'T0_cents_exact': True}), flush=True)
    assignments = pd.concat(mapping, ignore_index=True); assert assignments.claim_id.is_unique
    assignments.to_parquet(OUT / 'assigned_claims.parquet', index=False)
    c.loc[~c.claim_id.isin(assignments.claim_id)].to_parquet(OUT / 'unassigned_claims.parquet', index=False)
    pd.DataFrame(exposure_summary).to_csv(OUT / 'exposure_by_year_peril.csv', index=False)
    violations = sum(x['positive_N_zero_E_count'] + x['positive_cost_zero_E_cost'] for x in exposure_summary)
    final = {'author': 'Codex', 'utc': now(), 'status': 'count_and_mark_input_preparation_completed',
        'rows': sum(x['rows'] for x in checks), 'source_years': [2021, 2022, 2023, 2024], 'checks': checks,
        'curve_checks': curve_receipts, 'direct_checks': direct_checks, 'zero_exposure_positive_response_violations': violations,
        'downstream_observation_positivity_pass': violations == 0,
        'unassigned2020_preserved_not_assigned_to_invented_rows': True,
        'tail_beyond1095_and_case_reserve_adequacy_not_identified': True,
        'old_FS_FSp_not_declared_broken_merely_from_count_label_semantics': True,
        'new_empirical_source_count_CDF_fits': 15, 'new_source_cost_CDF_fits': 0, 'new_target_C0_fits': 0,
        'new_price_fits': 0, 'new_price_constants': 0, 'new_inferences': 0, 'new_scores': 0, 'new_submissions': 0,
        'source_hashes_still_match': all(sha(ROOT / p) == digest for p, digest in plan['sources'].items()),
        'outputs': {p.name: sha(p) for p in OUT.glob('*.parquet')}, 'B00_preserved': True, 'all_alternatives_preserved': True,
        'no_price_recipe_registered_or_fitted_yet': True, 'goal_achieved': False}
    assert final['source_hashes_still_match']; dump(OUT / 'report.json', final)
    print(json.dumps({'rows': final['rows'], 'new_source_count_CDFs': 15, 'positivity_violations': violations,
        'new_price_fits': 0, 'new_target_C0_fits': 0, 'new_scores': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'run']); args = parser.parse_args()
    try: register() if args.mode == 'register' else run()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'do_not_refit_completed_curves_on_retry': True})
        raise
