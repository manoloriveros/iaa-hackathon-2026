"""Adecuación condicional fuente sobre predicciones guardadas; ningún ajuste."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
SOURCE = BASE/'P28_fuente_frecuencia_marca_20261026'
OUT = BASE/'P32_adecuacion_condicional_fuente_20261026'
PLAN = R/'registro/semana2_adecuacion_condicional_fuente_privada_plan.json'
INDEX = R/'registro/semana2_adecuacion_condicional_fuente_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P32_ADECUACION_CONDICIONAL_FUENTE.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
sp = importlib.util.spec_from_file_location('p32_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']
CELLS = ['REN_OTHER', 'REN_BROKER', 'NB_OTHER', 'NB_BROKER']


def classify(new_business, channel):
    channel = channel.astype('string')
    known = channel.isin(['broker', 'direct', 'comparison_site']).to_numpy(bool)
    broker = channel.eq('broker').fillna(False).to_numpy(bool)
    nb = np.asarray(new_business, bool)
    return np.select([~known, nb&broker, nb, broker],
        ['UNKNOWN_CHANNEL', 'NB_BROKER', 'NB_OTHER', 'REN_BROKER'], default='REN_OTHER'), known


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def interaction(sums):
    # columns: each of four cells has cost, GLMexpected, treeexpected.
    a = np.asarray(sums, float).reshape(-1, 4, 3)
    valid = (a > 0).all(axis=(1, 2)); result = np.full((len(a), 3), np.nan)
    for i in np.flatnonzero(valid):
        glm = a[i, :, 0]/a[i, :, 1]; tree = a[i, :, 0]/a[i, :, 2]
        g = math.log(glm[3]/glm[2])-math.log(glm[1]/glm[0])
        t = math.log(tree[3]/tree[2])-math.log(tree[1]/tree[0])
        result[i] = [g, t, g-t]
    return result


def aggregate(frame):
    groups = sorted(frame.source_group.unique()); blocks = []
    for cell in CELLS:
        z = frame.loc[frame.cell.eq(cell)]
        a = z.groupby('source_group', sort=True)[['T0', 'candidate', 'original_tree']].sum().reindex(groups, fill_value=0)
        blocks.append(a.to_numpy(float))
    return np.column_stack(blocks), groups


def cell_readout(frame):
    result = []
    for cell in CELLS:
        z = frame.loc[frame.cell.eq(cell)]
        cost = float(z.T0.sum()); gc = float(z.candidate.sum()); tc = float(z.original_tree.sum())
        result.append({'cell': cell, 'rows': len(z), 'groups': int(z.source_group.nunique()),
            'positive_groups': int(z.loc[z.T0.gt(0), 'source_group'].nunique()), 'cost': cost,
            'GLMexpected': gc, 'treeexpected': tc, 'AE_GLM': cost/gc if gc > 0 else None,
            'AE_tree': cost/tc if tc > 0 else None})
    return result


def synthetic():
    sums = []
    for nb, broker in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        mean = 100.*(1+.2*nb)*(1+.1*broker)
        sums.extend([mean, 100., 100.])
    assert np.max(np.abs(interaction(sums))) < 1e-14
    changed = np.asarray(sums); changed[9] *= 1.2
    values = interaction(changed)[0]
    assert math.isclose(values[0], math.log(1.2), rel_tol=2e-14) and abs(values[2]) < 1e-14
    # If only the GLM mean misses the interaction, its difference from the
    # tree must show that contrast, without fitting any calibration factor.
    changed[11] *= 1.2; values = interaction(changed)[0]
    assert math.isclose(values[2], math.log(1.2), rel_tol=2e-14)
    return {'multiplicative_main_effects_zero_residual_interaction': True,
        'known_interaction_and_model_difference_verified': True, 'new_fits': 0}


def paths():
    result = [Path(__file__), SOURCE/'report.json', SOURCE/'completion_receipt.json', SOURCE/'numerical_replay.json',
        BASE/'P31_compatibilidad_puente_20261026/report.json']
    for line in LINES:
        result += [SOURCE/line/'held_predictions.parquet', SOURCE/line/'summary.json',
            HOME/f'rows_s1_{line}.parquet', HOME/f'matrix_s1_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet']
    return result


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    assert w.read(SOURCE/'completion_receipt.json')['replay_sha256'] == w.sha(SOURCE/'numerical_replay.json')
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'question': 'Does the saved paired-peril source GLM have a residual business/broker interaction beyond the saved original source tree, before considering additional main-effect capacity?',
        'scope': 'All saved P28source-held groups over2021-2024, all3lines, same frozen prices and labels. No target readout, inference, fitting, calibration, new forecast or model admission.',
        'cells': CELLS, 'channel': 'broker vs direct/comparison_site. Unknowns retain their own readout and all-source bootstrap group universe; they are not silently assigned OTHER or removed from any training data.',
        'statistic': 'For model m, logR_m=log(AE_NB_BROKER/AE_NB_OTHER)-log(AE_REN_BROKER/AE_REN_OTHER). Primary D=logR_GLM-logR_originaltree. AE is descriptive observed/expected cost, never applied as a fitted price factor.',
        'bootstrap': {'replicates': 2000, 'seed_motor': 2026102672, 'seed_buildings': 2026102673,
            'seed_contents': 2026102674, 'unit': 'held connected source customer/address group',
            'family': 3, 'quantiles': [.025/3, 1-.025/3],
            'invalid': 'Keep nonfinite draws and fail screen; do not refill, alter groups, add pseudo-cost or resample for a pass.'},
        'screen': {'minimum_positive_groups_each_pooled_cell': 100,
            'minimum_positive_groups_each_cell_after_drop31': 30,
            'absolute_primary_D_min': math.log(1.10), 'family3_band_excludes_zero': True,
            'GLM_absolute_logR_larger_than_tree': True, 'GLM_logR_same_direction_as_D': True,
            'source_year_support_positive_groups_each_cell': 30, 'at_least3years_same_D_direction': True,
            'drop31_D_same_direction_and_absolute_min': math.log(1.05),
            'interpretation': 'Descriptive source mechanism screen, not causal proof, a price acceptance rule or automatic authorization to fit.'},
        'dominant_group_rule': 'Remove31source-held groups with largest total observedT0within each line, ties by groupID, all their rows; chosen by costs, not favorable candidate improvement. Keep full result primary.',
        'controls': ['Saved source input/prediction hashes, row/year/held-group exact binding.',
            'All four known-channel cells plus unknown readout; no model/line chosen from target scores.',
            'Primary contrast by group sums and independent scalar arithmetic.',
            'Actual original-tree baseline and GLM share the same source-held rows; source-observation ancestors remain conditional.'],
        'sources': {w.rel(p): w.sha(p) for p in paths()}, 'fixture': fixture,
        'budget': {'new_model_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0,
            'new_prices': 0, 'new_target_scores': 0, 'new_source_group_bootstrap_contrasts': 3, 'new_submissions': 0},
        'limits': ['Source response and both model predictions are conditional on frozen source-observation objects; bootstrap does not refit observation or source models.',
            'Target P30adverse motivated this question; current source holdout already used, adaptive exploratory review.',
            'Different source likelihood/observation structures, confounding and risk composition can produce residual contrasts; not a causal channel diagnosis.',
            'Source support adds no emerging newbusiness support or private-performance guarantee.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. Registro P32 antes del readout: adecuación condicional de las predicciones '
        'fuente retenidas guardadas P28, cruzando negocio nuevo/renovación con broker/otros. '
        'Se comparará la interacción residual de A/E del GLM con la del árbol original, '
        'sin aplicar A/E como factor de precio. Todos los ramos, años y cuatro celdas '
        'se conservan; desconocidos se reportan aparte. Se fijan2000réplicas por grupos '
        'fuente, banda de familia3 y filtro de10% con soporte100grupos positivos por '
        'celda, estabilidad temporal y tras retirar31grupos de mayor coste. No son '
        'criterios de admisión ni causa demostrada. Cero ajustes, inferencias, precios '
        'o scores destino; no se repite bootstrap antiguo o aprendizaje fuente. '
        'Solo si aparece una limitación concreta se consideraría otra receta estándar '
        'registrada por separado. B00/F3c y alternativas conservados,2024abierto '
        'adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P32-RESIDUO-FUENTE-PREVIO',
        '--asunto', 'P32: adecuación fuente por negocio y broker antes de otra interacción',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P32registered_before_conditional_readout',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'new_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    dump(OUT/'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'new_model_fits': 0})
    results = []
    for index, line in enumerate(LINES):
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'new_business', 'T0'])
        part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
        x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet', columns=['channel', 'new_business'])
        assert np.array_equal(rows.row_id, part.row_id) and np.array_equal(rows.new_business.astype(float), x.new_business.astype(float))
        held = part.internal_validation.to_numpy(bool)
        z = rows.loc[held].reset_index(drop=True); z['source_group'] = part.loc[held, 'source_group'].to_numpy()
        channel = x.loc[held, 'channel'].astype('string').reset_index(drop=True)
        z['cell'], known = classify(z.new_business, channel)
        saved = pd.read_parquet(SOURCE/line/'held_predictions.parquet')
        assert w.sha(SOURCE/line/'held_predictions.parquet') == w.read(SOURCE/line/'summary.json')['held_predictions_sha256']
        assert np.array_equal(z.row_id, saved.row_id) and np.array_equal(z.year, saved.year)
        for col in ['candidate', 'original_tree']: z[col] = saved[col].to_numpy(float)
        totals, groups = aggregate(z); point = interaction(totals.sum(axis=0))[0]
        primary_cells = cell_readout(z); unknown = z.loc[~known]
        # Independent scalar cell sums before any bootstrap.
        scalar = []
        for cell in CELLS:
            c = z.loc[z.cell.eq(cell)]
            scalar.extend([math.fsum(c[col].tolist()) for col in ['T0', 'candidate', 'original_tree']])
        assert np.allclose(interaction(scalar)[0], point, rtol=2e-11, atol=2e-13)
        seed = plan['bootstrap']['seed_'+line]; rng = np.random.default_rng(seed); draws = []
        for start in range(0, 2000, 32):
            weights = rng.multinomial(len(groups), np.full(len(groups), 1/len(groups)), size=min(32, 2000-start))
            draws.append(interaction(weights@totals))
        draws = np.concatenate(draws); np.save(OUT/(line+'_group_draws.npy'), draws)
        finite = np.isfinite(draws).all(axis=1); invalid = int((~finite).sum())
        band = np.quantile(draws[:, 2], plan['bootstrap']['quantiles']).tolist() if invalid == 0 else None
        top = z.groupby('source_group').T0.sum().reset_index().sort_values(['T0', 'source_group'], ascending=[False, True]).head(31).source_group
        trimmed = z.loc[~z.source_group.isin(top)]; trimmed_totals, _ = aggregate(trimmed)
        trimmed_point = interaction(trimmed_totals.sum(axis=0))[0]; trimmed_cells = cell_readout(trimmed)
        years = []
        for year, frame in z.groupby('year'):
            tt, _ = aggregate(frame); pp = interaction(tt.sum(axis=0))[0]; cc = cell_readout(frame)
            years.append({'year': int(year), 'D': float(pp[2]) if np.isfinite(pp[2]) else None,
                'support_pass': min(c['positive_groups'] for c in cc) >= 30})
        gates = {'pooled_cell_support': min(c['positive_groups'] for c in primary_cells) >= 100,
            'primary_D_material': bool(np.isfinite(point[2]) and abs(point[2]) >= math.log(1.10)),
            'family3_band_excludes_zero': band is not None and (band[0] > 0 or band[1] < 0),
            'GLM_anomaly_larger_than_tree': bool(abs(point[0]) > abs(point[1])),
            'GLM_anomaly_same_D_direction': bool(point[0]*point[2] > 0),
            'at_least3source_years_same_direction': sum(a['support_pass'] and a['D'] is not None and a['D']*point[2] > 0 for a in years) >= 3,
            'after31_cell_support': min(c['positive_groups'] for c in trimmed_cells) >= 30,
            'after31_D_same_direction_material': bool(np.isfinite(trimmed_point[2]) and trimmed_point[2]*point[2] > 0 and abs(trimmed_point[2]) >= math.log(1.05)),
            'no_invalid_bootstrap_draws': invalid == 0}
        result = {'line': line, 'rows': len(z), 'groups': len(groups), 'cells': primary_cells,
            'unknown_channel_rows': len(unknown), 'unknown_channel_cost': float(unknown.T0.sum()),
            'logR_GLM': float(point[0]) if np.isfinite(point[0]) else None,
            'logR_tree': float(point[1]) if np.isfinite(point[1]) else None,
            'primary_D': float(point[2]) if np.isfinite(point[2]) else None,
            'family3_band95_D': band, 'invalid_draws': invalid, 'source_years': years,
            'after31_primary_D': float(trimmed_point[2]) if np.isfinite(trimmed_point[2]) else None,
            'removed_groups': len(top), 'removed_rows': len(z)-len(trimmed), 'after31_cells': trimmed_cells,
            'gates': gates, 'mechanism_screen_pass': all(gates.values()),
            'draws_sha256': w.sha(OUT/(line+'_group_draws.npy'))}
        results.append(result)
        print(json.dumps({'line': line, 'primary_D': result['primary_D'], 'family3_band': band,
            'mechanism_screen_pass': result['mechanism_screen_pass']}), flush=True)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P32source_conditional_review_complete_no_fit', 'results': results,
        'source_lines_with_screen': [x['line'] for x in results if x['mechanism_screen_pass']],
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_prices': 0,
        'new_target_scores': 0, 'new_source_bootstrap_contrasts': 3, 'new_submissions': 0,
        'limits': plan['limits'], 'plan_sha256': w.sha(PLAN), '2024_open': True,
        'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    print(json.dumps({'status': report['status'], 'lines_with_screen': report['source_lines_with_screen']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run']); args = parser.parse_args()
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run}[args.mode]()
