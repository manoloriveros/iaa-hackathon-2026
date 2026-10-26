"""Conciliación de bases y del significado de soloREN; sin ajuste o evaluación con etiquetas."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_ren', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'renovacion_fsp_recepcion_20261026_v1'
SOURCE = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025'
CODE = SOURCE / 'exp26_20261026_v2/m017'
PRIVATE = R / 'privado/semana2/claude_mision017_20261025'

def main():
    assert (OUT / 'inventory.json').exists() and not (OUT / 'audit.json').exists()
    paths = {name: PRIVATE / (name + '_2025.csv') for name in ['F3b', 'F3c', 'F4b', 'F4c']}
    expected = {'F3b': '5755513e9579748de236f3ce0c22910320ff1de29b442d0864dc00c48a32af27',
        'F3c': '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276',
        'F4b': 'dfcb27817008391adfcf43f89e5ec5599f78bb0b082d2186bf9e7358c7b561fd',
        'F4c': 'd5dfbf5769a134a09a3a3b23550eda496471b3511f9f66226c24301bb0de18f4'}
    for name, path in paths.items(): assert w.sha(path) == expected[name]
    frames = {name: pd.read_csv(path, dtype={'row_id': str}) for name, path in paths.items()}
    base = frames['F3c']; source_paths = [Path(__file__), OUT / 'inventory.json', *paths.values()]
    rows = []
    raw = ROOT / 'Hackaton/Semana 2/Datos/emerging'
    for line in ['motor', 'buildings', 'contents']:
        path = raw / f'test_{line}.parquet'; source_paths.append(path)
        f = pd.read_parquet(path, columns=['row_id', 'new_business']); f['line'] = line; rows.append(f)
    cohort = pd.concat(rows, ignore_index=True).set_index('row_id').loc[base.row_id].reset_index()
    assert cohort.row_id.is_unique and np.array_equal(cohort.row_id, base.row_id)
    for name, f in frames.items(): assert f.row_id.is_unique and np.array_equal(f.row_id, base.row_id)
    cohort.to_parquet(OUT / 'cohort_2025.parquet', index=False)
    ratios = []
    for numerator, denominator in [('F3c', 'F3b'), ('F4c', 'F4b')]:
        a = frames[numerator].prediction.to_numpy(float); b = frames[denominator].prediction.to_numpy(float)
        # Both artifacts are six-decimal outputs. This interval tests a single
        # unknown pre-rounding scale, not a regression on their values.
        lower = (a - .50001e-6) / (b + .50001e-6); upper = (a + .50001e-6) / (b - .50001e-6)
        for (line, nb), idx in cohort.groupby(['line', 'new_business'], observed=True).groups.items():
            idx = np.asarray(idx); ratio = a[idx] / b[idx]
            low = float(lower[idx].max()); high = float(upper[idx].min())
            ratios.append({'numerator': numerator, 'denominator': denominator, 'line': line, 'new_business': bool(nb),
                'rows': len(idx), 'constant_scale_compatible_with_rounding': bool(low <= high + 2e-14),
                'scale_interval_lower': low, 'scale_interval_upper': high,
                'ratio_min': float(ratio.min()), 'ratio_max': float(ratio.max()), 'ratio_median': float(np.median(ratio))})
    pd.DataFrame(ratios).to_csv(OUT / 'base_scale_checks.csv', index=False)
    renewal = [x for x in ratios if not x['new_business']]
    assert all(x['constant_scale_compatible_with_rounding'] for x in renewal), renewal
    meta_base_path = CODE / 'revision/K_F3b_mio_info.json'; meta_new_path = CODE / 'revision/K_F4_soloREN_sinedif_info.json'
    full_path = CODE / 'revision/K_F4_soloREN_info.json'; forecast_path = CODE / 'revision/K_t5d_variantes.json'
    mb = w.read(meta_base_path); mk = w.read(meta_new_path); full = w.read(full_path); forecasts = w.read(forecast_path)
    assert mb['sha256'] == expected['F3b'] and mk['pesos']['motor_1'] == mk['pesos']['contents_1'] == 0
    assert mb['A_M1'] == mk['A_M1']
    factor_change = []
    for variable, factors in mb['factores'].items():
        for name, value in factors.items():
            factor_change.append({'variable': variable, 'key': name, 'K_REN_vs_F3b_factor': mk['factores'][variable][name] / value})
    changes = pd.DataFrame(factor_change); changes.to_csv(OUT / 'common_factor_changes.csv', index=False)
    gender = changes.loc[changes.variable.eq('gender') & changes.key.str.startswith('motor|')]
    assert gender.K_REN_vs_F3b_factor.nunique() > 1
    f4meta = w.read(CODE / 'exp26/F4b_info.json'); assert f4meta['pesos_fsp']['buildings'] == 0
    source_paths += [meta_base_path, meta_new_path, full_path, forecast_path, CODE / 'exp26/F4b_info.json',
        CODE / 'revision/K_t4_build.py', CODE / 'revision/K_auditoria_F4.md', CODE / 'construir_F4b.py', CODE / 'construir_F3c.py']
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'renewal_base_mapping_established_predictive_replay_missing',
        'all_renewal_cells_F3c_over_F3b_and_F4c_over_F4b_constant_to_rounding': True,
        'scale_checks': ratios,
        'zero_FSp_NB_weights_do_not_freeze_total_NB_recipe': {'proved_from_provided_recipe_and_coefficients': True,
            'direct_FSp_NB_weights_zero': True, 'common_factors_reestimated': True,
            'motor_gender_factor_ratios_nonconstant': gender.to_dict('records'),
            'no_claim_of_direct_K_CSV_comparison': True},
        'buildings_renewal_not_rejected_by_received_evidence': True,
        'buildings_renewal_missing_in_available_F4c_donor': True,
        'received_forecasts_not_own_or_scored': {'all_renewal': forecasts['solo_REN'],
            'renewal_without_buildings': forecasts['solo_REN_sin_edif'],
            'not_transferable_as_exact_forecast_for_new_composition': True},
        'mechanism_separation': {'F4c_donor_includes_FSp_and_reestimated_residual_factors': True,
            'pure_FSp_effect_separately_identified_from_received_F3c_F4c_CSVs': False,
            'needed': 'Unrounded F4b residual factors plus per-row FSp totals/predictions, or a matching intermediate stage; scalar tables and two composite CSVs do not identify both components'},
        'exact_missing_K_CSV_not_researched_again': True,
        'candidate_implication': 'A new shape-only composition can be defined on available motor/contents renewals, preserving NB and all buildings exactly. It is neither a replay of K nor the complete all-renewal alternative; building output and numerical OOF evidence remain pending.',
        'new_fits': 0, 'new_C0_fits': 0, 'new_scores': 0, 'new_test_candidates': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_preserved': True, 'sources': {w.rel(p): w.sha(p) for p in source_paths}}
    (OUT / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'renewal_base_scale_checks': len(renewal), 'all_constant_to_rounding': True,
        'zero_weight_not_sufficient_to_freeze_NB': True, 'buildings_not_statistically_rejected': True,
        'pure_FSp_separation_not_identified': True, 'new_fits': 0, 'new_scores': 0}))

if __name__ == '__main__': main()
