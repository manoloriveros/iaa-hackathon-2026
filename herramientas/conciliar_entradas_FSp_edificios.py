"""Comprueba si las entradas locales permiten recuperar el productor numérico faltante."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_fsp_inputs', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'FSp_edificios_recuperacion_entradas_20261026_v1'
SOURCE = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/exp26_20261026/ml2'
VARIABLES = ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo/variables.py'

def main():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    # Parse constant lists as data. Do not execute the received producer or
    # import its /home/claude paths and globals.
    constants = {}
    for node in ast.parse(VARIABLES.read_text(encoding='utf8')).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ['POLIZA', 'CLIENTE', 'DIRECCION', 'RAMO', 'CATEGORICAS']: constants[name] = ast.literal_eval(node.value)
    features = constants['POLIZA'] + constants['CLIENTE'] + constants['DIRECCION'] + constants['RAMO']['buildings']
    srcpath = BASE / 'fuente_f2_2024_v2/buildings.parquet'
    countpath = BASE / 'recuentos_fuente2024_v1/counts_buildings.parquet'
    targetpath = BASE / 'linaje_T2b_v1/features_buildings.parquet'
    schemas = {'source': pq.ParquetFile(srcpath).schema_arrow, 'target_historical': pq.ParquetFile(targetpath).schema_arrow}
    missing = {name: sorted(set(features) - set(schema.names)) for name, schema in schemas.items()}
    assert not any(missing.values()), missing
    numeric32 = [name for name in features if name not in constants['CATEGORICAS'] and str(schemas['source'].field(name).type) == 'float']
    count = pd.read_parquet(countpath); source_keys = pd.read_parquet(srcpath, columns=['row_id', 'year'])
    assert np.array_equal(source_keys.row_id, count.row_id) and np.array_equal(source_keys.year, count.year)
    assert count.year.isin([2021, 2022, 2023, 2024]).all()
    paths = [Path(__file__), VARIABLES, srcpath, countpath, targetpath,
        BASE / 'recuentos_fuente2024_v1/report.json', BASE / 'recuentos_fuente2024_v1/validation_v1/report.json',
        SOURCE / 'codigo/fsp_light.py', SOURCE / 'codigo/fsp_light_prod.py']
    comparisons = []; metadata = {}
    for phase, years, suffix in [('dev', [2021, 2022, 2023], ''), ('prod', [2021, 2022, 2023, 2024], '_prod')]:
        path = SOURCE / f'trabajo/pred/fsp/buildings{suffix}_meta.json'; paths.append(path); a = w.read(path); metadata[phase] = a
        f = count.loc[count.year.isin(years)]
        for peril, saved in a.items():
            n = f['N_' + peril].to_numpy(float); cost = f['T0_cents_' + peril].to_numpy(float) / 100.
            e = f.exposure.to_numpy(float); ecost = f['E_cost_' + peril].to_numpy(float)
            q = ecost / e; clipped = e * np.maximum(q, 1e-4)
            b0 = float(np.log(n.sum() / clipped.sum()))
            positive = (n > 0) & (cost > 0); mean = float(cost[positive].sum() / n[positive].sum())
            row = {'phase': phase, 'years': years, 'peril': peril, 'rows': len(f),
                'count_sum': int(n.sum()), 'metadata_count_sum': saved['n_dev'], 'count_exact': int(n.sum()) == saved['n_dev'],
                'computed_mean_mark': mean, 'metadata_mean_mark': saved['sev_media'],
                'mean_mark_relative_error': mean / saved['sev_media'] - 1,
                'computed_b0_with_cached_cost_exposure_and_original_floor': b0, 'metadata_b0': saved['b0'],
                'b0_error': b0 - saved['b0'], 'q_floor_rows': int((q < 1e-4).sum()),
                'existing_frequency_rounds': saved['rondas_f'], 'existing_severity_rounds': saved['rondas_s'],
                'noninformative_or_zero_mark_rows': int(np.count_nonzero((n > 0) & (cost == 0)))}
            assert row['count_exact'] and abs(row['mean_mark_relative_error']) < 1e-10, row
            comparisons.append(row)
    pd.DataFrame(comparisons).to_csv(OUT / 'count_mark_offset_parity.csv', index=False)
    # Original code selects rounds and refits but does not persist Boosters.
    saves_models = {}
    for name in ['fsp_light.py', 'fsp_light_prod.py']:
        tree = ast.parse((SOURCE / 'codigo' / name).read_text(encoding='utf8'))
        saves_models[name] = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in ['save_model', 'model_to_string']]
        assert not saves_models[name]
    target_rows = pq.ParquetFile(targetpath).metadata.num_rows
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'response_and_feature_contract_recoverable_precision_and_prediction_outputs_pending',
        'feature_names': features, 'features': len(features), 'missing_features': missing,
        'source_rows': len(count), 'historical_target_rows': target_rows,
        'source_count_mean_mark_parity_all12passed': True, 'comparisons': comparisons,
        'cost_exposure_b0_parity_max_abs_error': max(abs(x['b0_error']) for x in comparisons),
        'cached_source_numeric_float32_columns': numeric32,
        'original_numeric_matrix_requests_float64': True,
        'precision_limit': 'Cached source features were quantized to float32; promoting them tofloat64 does not recover original precision. Restore original raw-derived values or document a new reconstruction, never assert exact original trees.',
        'producer_model_save_calls': saves_models,
        'models_cannot_be_loaded_from_metadata_alone': True,
        'fixed_existing_rounds_can_avoid_repeating_early_stopping': True,
        'minimum_missing_numeric_producer': {'line': 'buildings', 'perils': 6,
            'prod_source_years': [2021, 2022, 2023, 2024], 'dev_source_years': [2021, 2022, 2023],
            'fixed_round_model_fits_if_recovery_necessary': 24, 'new_early_stopping_search': 0,
            'target_required': 'historical2023–2024 plus2025, source f/s fields and producer exposure convention',
            'not_training_authorization_or_recipe_registration': True},
        'frequency_semantics': 'Original Poisson offset uses cost-weighted completion, so f is not automatically ultimate event frequency; product with observed marks is a cost proxy. Preserve this semantic limit.',
        'future_completion_trap': 'Original cp2025can be0. Never multiply it into a2025ultimate price; use supplied risk f*s and explicit ultimate convention.',
        'next_requirements_before_any_recovery_fit': ['Verify full-precision source/target numerical matrices and categorical level mapping',
            'Match development and production climate windows separately; never use source2025weather',
            'Pin fixed rounds, exact source/target manifests and C0 reuse, register budget/criterion and forum before fit',
            'Persist all new numerical models and row predictions for replay; do not reproduce the original missing-output failure'],
        'new_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0, 'new_scores': 0, 'new_submissions': 0,
        'B00_all_alternatives_preserved': True, '2024_open': True,
        'sources': {w.rel(path): w.sha(path) for path in paths}}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'feature_contract': len(features), 'source_rows': len(count), 'historical_target_rows': target_rows,
        'count_and_mean_mark_checks': len(comparisons), 'all_passed': True,
        'max_b0_parity_error': result['cost_exposure_b0_parity_max_abs_error'],
        'quantized_numeric_columns': len(numeric32), 'original_models_not_saved_by_producer': True,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0}))

if __name__ == '__main__': main()
