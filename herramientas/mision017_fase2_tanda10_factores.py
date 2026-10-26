"""Factores residuales cerrados dentro del ámbito N3, sin nuevo C0 o árboles."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

b = load('scope10', R / 'herramientas/mision017_fase2_tanda6_pendiente.py')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda10_factores_20261026_v1'
PLAN = R / 'registro/semana2_mision017_fase2_tanda10_plan_v1.json'
RAW = ROOT / 'Hackaton/Semana 2/Datos/emerging'
CV = BASE / 'tanda2_20261025_v1'; K = 300.
STAGES = {'motor': ['gender'], 'contents': ['gender', 'works_from_home', 'marketing_segment'], 'buildings': []}
NAMES = ['G1', 'G2', 'G3']
sha = b.sha; read = b.read; dump = b.dump; rel = b.rel
now = lambda: datetime.now(timezone.utc).isoformat()
digest = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def key(x): return x.astype('string').fillna('__MISSING__').astype(str).to_numpy()

def normalise(f, base, factor):
    assert len(f) == len(base) == len(factor) and np.isfinite(factor).all() and (factor > 0).all()
    out = base.copy(); normalizers = {}
    for year in sorted(f.year.unique()):
        for nb in [0, 1]:
            mask = f.year.eq(year).to_numpy() & (f.new_business.to_numpy(dtype=int) == nb); assert mask.any()
            norm = float(np.sum(base[mask] * factor[mask]) / np.sum(base[mask])); assert norm > 0
            out[mask] = base[mask] * factor[mask] / norm; normalizers[f'{int(year)}|{nb}'] = norm
            assert np.isclose(out[mask].sum(), base[mask].sum(), rtol=1e-12, atol=1e-6)
    assert np.isfinite(out).all() and (out > 0).all()
    return out, normalizers

def fit_stage(train, base, variable):
    assert len(train) == len(base) and train.T0.ge(0).all() and np.isfinite(train.T0).all()
    y = train.T0.to_numpy(float); adjusted = base.copy(); nuisance = {}
    for year in sorted(train.year.unique()):
        for nb in [0, 1]:
            mask = train.year.eq(year).to_numpy() & (train.new_business.to_numpy(dtype=int) == nb)
            assert mask.any() and y[mask].sum() > 0
            value = float(np.sum(y[mask] / np.sqrt(base[mask])) / np.sum(np.sqrt(base[mask])))
            nuisance[f'{int(year)}|{nb}'] = value; adjusted[mask] *= value
    labels = key(train[variable]); factors = {}; raw = {}; counts = {}; unknown_positive = []
    for label in sorted(set(labels)):
        mask = labels == label; n = int(np.count_nonzero(y[mask] > 0)); counts[label] = n
        if n == 0:
            factors[label] = 1.; raw[label] = None; unknown_positive.append(label)
        else:
            optimum = float(np.sum(y[mask] / np.sqrt(adjusted[mask])) / np.sum(np.sqrt(adjusted[mask])))
            assert optimum > 0 and np.isfinite(optimum)
            raw[label] = optimum; factors[label] = float(np.exp(n / (n + K) * np.log(optimum)))
    artifact = {'variable': variable, 'K': K, 'nuisance_year_business': nuisance, 'raw_factors': raw,
        'factors': factors, 'positive_period_counts': counts, 'zero_positive_levels_neutral': unknown_positive,
        'training_rows': len(train), 'training_row_ids_digest': digest(sorted(train.row_id)),
        'training_groups_digest': digest(sorted(set(train.group_id))),
        'training_label_digest': digest(y.tolist()), 'input_base_digest': digest(base.tolist()),
        'nuisance_not_transferred': True, 'new_iterative_model_fits': 0, 'closed_form_factor_learning_calls': 1}
    return artifact

def apply_stage(f, base, artifact):
    labels = key(f[artifact['variable']])
    factor = np.array([artifact['factors'].get(label, 1.) for label in labels])
    return normalise(f, base, factor)

def learn_scope(f, held, line):
    # This is the complete estimator entry point: exclude all protected costs first.
    mask = f.fold.ne(held).to_numpy(); tr = f.loc[mask].copy(); val = f.loc[~mask].copy()
    assert not set(tr.group_id).intersection(val.group_id)
    training = tr.base_N3.to_numpy(float); valid = val.base_N3.to_numpy(float)
    artifacts = []; predictions = {}; normalizers = {}; train_normalizers = {}
    for step, variable in enumerate(STAGES[line]):
        a = fit_stage(tr, training, variable)
        training, nt = apply_stage(tr, training, a); valid, nv = apply_stage(val, valid, a)
        artifacts.append(a); name = NAMES[step]; predictions[name] = valid.copy()
        normalizers[variable] = nv; train_normalizers[variable] = nt
    for name in NAMES:
        if name not in predictions: predictions[name] = valid.copy()
    record = {'line': line, 'held_fold': int(held), 'training_rows': len(tr), 'held_rows': len(val),
        'training_row_ids_digest': digest(sorted(tr.row_id)), 'training_groups_digest': digest(sorted(set(tr.group_id))),
        'stages': artifacts, 'training_normalizers': train_normalizers, 'held_normalizers': normalizers,
        'new_C0_fits': 0, 'new_iterative_model_fits': 0}
    return predictions, record

def synthetic():
    rng = np.random.default_rng(2026102604); n = 1600
    f = pd.DataFrame({'row_id': ['synthetic_' + str(i) for i in range(n)], 'group_id': ['g' + str(i) for i in range(n)],
        'fold': np.arange(n) % 5, 'year': 2023 + (np.arange(n) // 5) % 2,
        'new_business': (np.arange(n) // 10) % 2, 'gender': rng.choice(['M', 'F'], n),
        'works_from_home': rng.integers(0, 2, n), 'marketing_segment': rng.choice(['budget', 'mainstream', 'affluent'], n),
        'T0': rng.gamma(2, 80, n) * (rng.random(n) < .35), 'base_N3': rng.uniform(25, 200, n)})
    pred, learned = learn_scope(f, 0, 'contents')
    bad = f.copy(); bad.loc[bad.fold.eq(0), 'T0'] = -1e30
    other, unchanged = learn_scope(bad, 0, 'contents')
    assert digest(learned) == digest(unchanged) and all(np.array_equal(pred[k], other[k]) for k in NAMES)
    bad = f.copy(); bad.loc[bad.fold.ne(0), 'T0'] *= np.where(bad.loc[bad.fold.ne(0), 'gender'].eq('M'), 1.7, .7)
    _, changed = learn_scope(bad, 0, 'contents'); assert digest(changed) != digest(learned)
    val = f.loc[f.fold.eq(0)]; base = val.base_N3.to_numpy(float)
    a = learned['stages'][0]; neutral = {**a, 'factors': {k: 1. for k in a['factors']}}
    identity, norms = apply_stage(val, base, neutral); assert np.array_equal(identity, base) and set(norms.values()) == {1.}
    unknown, _ = apply_stage(val.assign(gender='unseen'), base, a); assert np.array_equal(unknown, base)
    # A zero-positive category must not imply a zero premium or a clipped MLE.
    tr = f.loc[f.fold.ne(0)].copy(); tr.loc[tr.gender.eq('F'), 'T0'] = 0
    z = fit_stage(tr, tr.base_N3.to_numpy(float), 'gender'); assert z['factors']['F'] == 1. and z['raw_factors']['F'] is None
    dump(OUT / 'synthetic.json', {'pass': True, 'full_learning_held_cost_invariant': True, 'training_change_changes_factors': True,
        'neutral_and_unseen_identity_bit_exact': True, 'zero_positive_level_neutral_without_clipping': True,
        'year_business_totals_preserved': True, 'synthetic_closed_stage_calls': 10, 'contest_estimates': 0})

def preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True); synthetic()
    customer_path = RAW / 'customers.parquet'; customers = pd.read_parquet(customer_path, columns=['customer_id', 'gender', 'marketing_segment'])
    assert customers.customer_id.is_unique and customers.gender.notna().all() and customers.marketing_segment.notna().all()
    assert set(customers.gender) == {'M', 'F'} and customers.marketing_segment.nunique() == 12
    old = pd.read_parquet(CV / 'oof_2023_2024.parquet'); sources = [Path(__file__), customer_path,
        R / 'registro/semana2_politica_desarrollo2024_v2.json', BASE / 'aportes_F3c_F4c_20261026_v2/report.json',
        b.OUT / 'preflight.json', b.OUT / 'validation_v1/report.json', CV / 'oof_2023_2024.parquet']
    rows = []; scopes = []; outputs = []
    for line in ['motor', 'contents']:
        raw = RAW / f'policies_{line}.parquet'; sources.append(raw)
        cols = ['row_id', 'customer_id', 'period_start'] + (['works_from_home'] if line == 'contents' else [])
        f = pd.read_parquet(raw, columns=cols).merge(customers, on='customer_id', validate='many_to_one', how='left')
        assert f.row_id.is_unique and f.gender.notna().all() and f.marketing_segment.notna().all()
        assert pd.to_datetime(f.period_start).dt.year.isin([2023, 2024]).all()
        if line == 'contents':
            assert f.works_from_home.notna().all() and f.groupby('customer_id').works_from_home.nunique().max() == 1
        else: f['works_from_home'] = '__NOT_USED__'
        cov = f[['row_id', 'gender', 'works_from_home', 'marketing_segment']].copy()
        path = OUT / f'covariates_{line}.parquet'; cov.to_parquet(path, index=False); outputs.append(path)
        for held in range(5):
            inputs = b.OUT / f'inputs_{line}_fold{held}.parquet'; parent = CV / f'learning_{line}_fold{held}.json'
            sources += [inputs, parent]; inp = pd.read_parquet(inputs); a = read(parent)['artifact']['C0']
            assert set(inp.row_id) == set(cov.row_id) and inp.row_id.is_unique
            train = inp.fold.ne(held); assert sorted(inp.loc[train, 'row_id']) == a['fit_row_ids']
            assert not set(inp.loc[train, 'group_id']).intersection(inp.loc[~train, 'group_id'])
            val = old.set_index('row_id').loc[inp.loc[~train, 'row_id']]
            assert np.array_equal(val.N3, inp.loc[~train, 'base_N3']) and np.array_equal(val.T0, inp.loc[~train, 'T0'])
            assert all(inp.loc[train & inp.year.eq(y) & inp.new_business.eq(nb), 'T0'].sum() > 0 for y in [2023, 2024] for nb in [0, 1])
            scopes.append({'line': line, 'held': held, 'input': rel(inputs), 'input_sha256': sha(inputs),
                'C0_parent': rel(parent), 'C0_parent_sha256': sha(parent), 'membership_exact_and_held_groups_excluded': True,
                'held_N3_and_T0_bit_exact': True, 'training_rows': int(train.sum()), 'held_rows': int((~train).sum())})
        rows.append({'line': line, 'rows': len(cov), 'gender_levels': sorted(set(cov.gender)),
            'marketing_levels': cov.marketing_segment.nunique(), 'master_temporal_availability': 'Supplied undated snapshot, not proof of inception-time vintage',
            'contents_telework_stable_within_customer': line == 'contents'})
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': now(), 'sources': {rel(p): sha(p) for p in sources},
        'outputs': {rel(p): sha(p) for p in outputs}, 'scopes': scopes, 'covariate_audit': rows,
        'new_contest_factor_estimates': 0, 'new_C0_fits': 0, 'new_scores': 0})
    print(json.dumps({'preflight': 'complete', 'learning_scopes': len(scopes), 'new_contest_estimates': 0, 'new_C0_fits': 0}))

def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = read(OUT / 'preflight.json'); assert read(OUT / 'synthetic.json')['pass'] and len(pre['scopes']) == 10
    sources = {**pre['sources'], **pre['outputs'], rel(OUT / 'preflight.json'): sha(OUT / 'preflight.json'),
        rel(OUT / 'synthetic.json'): sha(OUT / 'synthetic.json')}
    for path, value in sources.items(): assert sha(ROOT / path) == value, path
    criterion = read(R / 'registro/semana2_mision017_fase2_tanda8_plan_v1.json')['criterion']
    plan = {'id': 'S2-MISION017-FASE2-TANDA10-FACTORES-v1', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'The received residual gender/telework/marketing evidence may survive global component exclusion and the frozen outer-training C0/N3 flow. Test this distinct scope, not repeat received permutation suites or FSp training.',
        'reference': 'Frozen N3 research comparator, not complete C1/F2 or a replay of F3c learning',
        'models': {'G1': 'Gender in motor/contents; buildings unchanged', 'G2': 'G1 plus telework in contents',
            'G3': 'G2 plus marketing segment in contents'},
        'configuration': {'years': [2023, 2024], 'folds': 'saved global customer/address components',
            'K': K, 'factor': 'exp(n_positive/(n_positive+K)*log(conditional_Tweedie_optimum))',
            'nuisance': 'Tweedie-optimal baseline level separately by year/business on training only, not transferred',
            'sequential': True, 'unknown_or_zero_positive_level': 'neutral1, no zero price or clipped factor',
            'normalization': 'prediction-only per year/business on each application, preserve N3 cell totals',
            'level_ratios_from_received_F3c': 'not adopted; this trial isolates shape without new held-label levels',
            'no_new_C0_source_inference_or_FSp': True, 'no_hyperparameter_search': True},
        'criterion': criterion, 'bootstrap': {'replicates': 2000, 'seed': 2026102604, 'unit': 'saved connected component'},
        'budget': {'closed_form_stage_learning_calls': 20, 'factor_parameters_max': 90, 'training_nuisance_levels': 80,
            'training_prediction_only_normalizers': 80, 'held_prediction_only_normalizers': 80,
            'new_iterative_price_fits': 0, 'new_C0_fits': 0, 'new_test_prices': 0, 'submissions': 0},
        'candidate_priority_if_checks_pass': ['G1', 'G2', 'G3'],
        'limits': ['Prior variable screening is adaptive; received AI reviews not independent professional validation',
            'Undated customer/master snapshots do not establish inception-time availability',
            'Telework NB severity interaction has sparse support in received evidence', 'Marketing composite can duplicate age signals',
            'Heuristic credibility and single sequential pass are not a joint maximum-likelihood fit',
            'Weighted2025 primary ESS failed; diagnostic/veto only', '2024 development adaptive; no full C1/A1 historical replay',
            'No automatic test candidate, submission, formal promotion or final selection'],
        'sources': sources, 'B00_preserved': True, 'all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan); body = OUT / 'forum_previo.md'
    body.write_text('Se registra la tanda10: factores residuales cerrados con K300, por etapas G1(género en autos/contenidos), '
        'G2(+teletrabajo en contenidos), G3(+segmento en contenidos). Edificios conserva N3. '
        'La diferencia con los aportes F3c recibidos es el ámbito: cada factor aprende solo en los componentes exteriores de entrenamiento, '
        'con su C0/N3 ya guardado y niveles por año/negocio como nuisance que no se transfieren. '
        'Las predicciones conservan el total N3 por año/negocio sin etiquetas; no se adopta la razón de nivel de F3c.\n\n'
        'Pasaron antes del registro la exclusión del retenido en el flujo sintético, identidad neutral/desconocida, respuesta al cambio del entrenamiento, '
        'neutralidad de categorías sin positivos y los10ámbitos reales de pertenencia/relatividades guardadas. '
        'Los maestros están sin fecha: la estabilidad del teletrabajo no prueba disponibilidad al cotizar. '
        'La selección previa de variables sigue siendo adaptativa.\n\n'
        'Criterios principales y vetos sin cambios. Presupuesto:20estimaciones cerradas de etapas, hasta90factores,80niveles nuisance y160normalizadores sin etiquetas; '
        'cero árboles/GLM iterativos, C0, precios de test o envíos. No se repiten las suites I/J/K, FSp o las tandas anteriores. '
        'La prioridad si pasan todos los controles será G1, luego G2, luego G3, por simplicidad. Cualquier entrega se revisará aparte. '
        '2024 abierto como desarrollo, B00/F2/C1 y alternativas conservados. Plan: ' + rel(PLAN) + '.\n', encoding='utf8')
    receipt = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA10-PREVIO', '--asunto',
        'Factores simples con exclusión global de componentes y C0 guardado: género, teletrabajo y segmento', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(receipt.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'closed_form_stage_budget': 20, 'new_C0_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, value in plan['sources'].items(): assert sha(ROOT / path) == value, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    p = pd.read_parquet(CV / 'oof_2023_2024.parquet')
    for name in NAMES: p[name] = p.N3.to_numpy(float)
    stages = 0; factor_count = 0; nuisance_count = 0; train_norms = 0; held_norms = 0
    with threadpool_limits(limits=2):
        for line in ['motor', 'contents']:
            cov = pd.read_parquet(OUT / f'covariates_{line}.parquet').set_index('row_id')
            for held in range(5):
                inp = pd.read_parquet(b.OUT / f'inputs_{line}_fold{held}.parquet')
                for col in ['gender', 'works_from_home', 'marketing_segment']: inp[col] = cov.loc[inp.row_id, col].to_numpy()
                prediction, a = learn_scope(inp, held, line); stages += len(a['stages'])
                factor_count += sum(len(s['factors']) for s in a['stages']); nuisance_count += sum(len(s['nuisance_year_business']) for s in a['stages'])
                train_norms += sum(len(v) for v in a['training_normalizers'].values()); held_norms += sum(len(v) for v in a['held_normalizers'].values())
                dump(OUT / f'learning_{line}_fold{held}.json', a)
                keys = inp.loc[inp.fold.eq(held), 'row_id']; idx = p.set_index('row_id').loc[keys].index
                target_idx = pd.Series(p.index.to_numpy(), index=p.row_id).loc[idx].to_numpy()
                for name in NAMES: p.loc[target_idx, name] = prediction[name]
                print(json.dumps({'event': 'closed_stages_completed', 'line': line, 'fold': held, 'total_stage_calls': stages}), flush=True)
    assert len(p) == 109296 and p.row_id.is_unique and stages == 20 and factor_count <= 90 and nuisance_count == train_norms == held_norms == 80
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = b.b.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - b.b.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', *NAMES]}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'scored_validation_pending', 'scores': scores,
        'closed_form_stage_learning_calls': stages, 'factor_parameters': factor_count, 'training_nuisance_levels': nuisance_count,
        'training_prediction_only_normalizers': train_norms, 'held_prediction_only_normalizers': held_norms,
        'new_iterative_price_fits': 0, 'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, '2024_open': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'closed_form_stage_calls': stages, 'factor_parameters': factor_count, 'nuisance_levels': nuisance_count,
        'new_C0_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'register', 'run']); args = parser.parse_args()
    try: {'preflight': preflight, 'register': register, 'run': run}[args.mode]()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'preserve_completed_artifacts': True})
        raise
