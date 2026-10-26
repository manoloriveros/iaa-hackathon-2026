"""Composición provisional de dos celdas REN; no recrea K ni aísla el FSp puro."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_REN_MC', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'renovacion_fsp_composicion_20261026_v1'
AUDIT = BASE / 'renovacion_fsp_recepcion_20261026_v1'
PRIVATE = R / 'privado/semana2/claude_mision017_20261025'
PARENT = PRIVATE / 'F3c_2025.csv'; DONOR = PRIVATE / 'F4c_2025.csv'
PLAN = R / 'registro/semana2_mision017_REN_MC_composicion_v1.json'
ACTIVE = [('motor', False), ('contents', False)]
now = lambda: datetime.now(timezone.utc).isoformat()

def ticks(f):
    assert list(f.columns) == ['row_id', 'prediction'] and f.row_id.is_unique
    assert f.prediction.str.fullmatch(r'\d+\.\d{6}').all()
    value = f.prediction.str.replace('.', '', regex=False).astype('int64').to_numpy()
    assert (value > 0).all(); return value

def round_ratio_even(numerator, denominator):
    q, rem = divmod(int(numerator), int(denominator))
    return q + int(2 * rem > denominator or (2 * rem == denominator and q % 2 == 1))

def compose(parent, donor, cohort):
    assert len(parent) == len(donor) == len(cohort) and parent.row_id.is_unique and donor.row_id.is_unique and cohort.row_id.is_unique
    assert set(parent.row_id) == set(donor.row_id) == set(cohort.row_id)
    d = donor.set_index('row_id').loc[parent.row_id].reset_index(); c = cohort.set_index('row_id').loc[parent.row_id].reset_index()
    assert c.line.isin(['motor', 'buildings', 'contents']).all() and c.new_business.isin([0, 1, False, True]).all()
    pb = ticks(parent); pdonor = ticks(d); output = pb.copy(); changed_scope = np.zeros(len(parent), dtype=bool); norms = {}
    for line, nb in ACTIVE:
        mask = c.line.eq(line).to_numpy() & (c.new_business.to_numpy(dtype=bool) == nb); assert mask.any()
        changed_scope |= mask; numerator = sum(int(x) for x in pb[mask]); denominator = sum(int(x) for x in pdonor[mask])
        assert numerator > 0 and denominator > 0
        output[mask] = [round_ratio_even(int(value) * numerator, denominator) for value in pdonor[mask]]
        error = int(sum(int(x) for x in output[mask]) - numerator)
        assert abs(error) <= np.count_nonzero(mask) / 2 + 1
        norms[f'{line}|{int(nb)}'] = {'rows': int(mask.sum()), 'base_ticks_sum': numerator, 'donor_ticks_sum': denominator,
            'normalization_ratio': numerator / denominator, 'rounding_total_error_ticks': error}
    assert np.array_equal(output[~changed_scope], pb[~changed_scope]) and (output > 0).all()
    return output, norms, changed_scope

def write_csv(path, ids, value):
    with path.open('x', encoding='utf8', newline='') as f:
        writer = csv.writer(f, lineterminator='\n'); writer.writerow(['row_id', 'prediction'])
        writer.writerows((rid, f'{int(x) // 1000000}.{int(x) % 1000000:06d}') for rid, x in zip(ids, value))

def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir(parents=True)
    audit = w.read(AUDIT / 'audit.json'); assert audit['all_renewal_cells_F3c_over_F3b_and_F4c_over_F4b_constant_to_rounding']
    assert not audit['mechanism_separation']['pure_FSp_effect_separately_identified_from_received_F3c_F4c_CSVs']
    paths = [Path(__file__), AUDIT / 'audit.json', AUDIT / 'cohort_2025.parquet', PARENT, DONOR,
        BASE / 'entrega_F3c_investigacion_20261026_v1/public_receipt.json']
    for path, digest in audit['sources'].items(): assert w.sha(ROOT / path) == digest, path
    plan = {'id': 'S2-MISION017-REN-MC-COMPOSITION-v1', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'A provisional available-output renewal shape may add useful diversity while keeping all NB exactly fixed; assess mechanical composition now, not predictive admission.',
        'parent': 'Processed F3c0.16914, source Claude; review/transport Codex',
        'donor': 'Received F4c, includes FSp and reestimated residual factors together, not isolated FSp',
        'recipe': {'active_cells': ACTIVE, 'donor_weights': 'unchanged received0.25motor/0.5contents, not tuned here',
            'new_price_in_active_cell': 'F4c_i * sum(F3c_cell)/sum(F4c_cell)',
            'other_rows': 'copy original F3c exactly, including every NB and all buildings',
            'arithmetic': 'six-decimal source prices as integer microCU; exact rational rescaling, round ties to even',
            'no_new_labels_or_levels_from_claims': True},
        'quality_criteria': ['source hashes frozen', 'keyed one-to-one coverage and original row order',
            'only the two declared renewal cells may change', 'all NB/buildings price strings remain exact',
            'cell totals conserved before rounding, after rounding within half microCU per affected row',
            'integer rational and independent floating arithmetic agree within rounding',
            'shuffle/scale/outside-scope/label-payload controls passed; positive finite outputs'],
        'predictive_admission_criteria_passed': False,
        'not_a_K_replay': True, 'not_a_pure_FSp_isolation': True,
        'full_renewal_alternative_incomplete': 'BuildingREN has favorable received evidence but F4c donor carries no building FSp shape. Keep recovery/validation pending, do not call it rejected or solved.',
        'evidence_limits': ['K original blends FSp with F2 and reestimates common factors; newer F4c preserves F2 multipliers and has different coupled factors',
            'Received K forecast and bootstrap cannot be assigned exactly to this new composition',
            'No local per-row FSp OOF/learning replay currently recovered for this candidate',
            'This freezes NB explicitly; zero mixture weights alone did not freeze the received full K recipe',
            '2024adaptive development, received AI reviews not professional independent validation'],
        'budget': {'new_model_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0, 'new_candidate_files': 1,
            'new_submissions': 0},
        'submission_ready_under_this_plan': False, 'no_new_score_or_goal_complete_claim': True,
        'B00_all_alternatives_preserved': True, '2024_open': True,
        'sources': {w.rel(path): w.sha(path) for path in paths}}
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf8')
    body = OUT / 'forum_previo.md'
    body.write_text('Se registra una composición local provisional sobre F3c medido0,16914. Solo renovaciones de autos/contenidos toman '
        'la forma del F4c recibido, reescalada al total de la misma celda F3c. Todos los NB y edificios se copian exactamente. '
        'Los pesos internos recibidos0,25/0,5 no se ajustan; se usará aritmética racional de microCU y controles adversos.\n\n'
        'La conciliación mostró que F3c/F3b y F4c/F4b difieren solo por escala en todas las celdas REN, dentro del redondeo. '
        'El K “soloREN” no preserva todo NB: vuelve a aprender factores comunes. Este archivo nuevo sí lo preservará. '
        'No es un replay del K cuyo CSV falta ni un aislamiento de FSp: F4c también incorpora factores residuales reestimados.\n\n'
        'EdificiosREN no tiene evidencia recibida adversa: la variante K completa tiene mejor previsión que la que lo excluye. '
        'El donante disponible F4c tiene peso0 en edificios; recuperar ese tramo queda pendiente. No se sustituye la alternativa completa por esta preparación parcial. '
        'Tampoco se asignan aquí las previsiones o intervalos del K a esta composición. '
        'Presupuesto:un candidato local, cero ajustes/C0/inferencias o envíos. Las pruebas mecánicas no acreditan rendimiento predictivo; '
        'cuota actual0 y sin admisión de carga en este plan.2024 abierto, B00/F2/C1/F3c y alternativas conservados. Plan: ' + w.rel(PLAN) + '.\n', encoding='utf8')
    result = __import__('subprocess').run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-REN-MC-PREVIO', '--asunto', 'REN autos/contenidos: composición provisional con NB exacto y edificios pendiente',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    (OUT / 'registration.json').write_text(json.dumps({'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout)}, indent=2), encoding='utf8')
    print(json.dumps({'registered': w.rel(PLAN), 'new_model_fits': 0, 'new_submissions': 0, 'predictive_admission': False}))

def build_validate():
    assert not (OUT / 'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT / 'registration.json')['plan_sha256'] == w.sha(PLAN)
    for path, digest in plan['sources'].items(): assert w.sha(ROOT / path) == digest, path
    parent = pd.read_csv(PARENT, dtype=str); donor = pd.read_csv(DONOR, dtype=str); cohort = pd.read_parquet(AUDIT / 'cohort_2025.parquet')
    output, norms, mask = compose(parent, donor, cohort)
    baseline = ticks(parent); d = ticks(donor); cohort = cohort.set_index('row_id').loc[parent.row_id].reset_index()
    nb = cohort.new_business.to_numpy(dtype=bool); buildings = cohort.line.eq('buildings').to_numpy()
    assert np.array_equal(output[nb | buildings], baseline[nb | buildings])
    identity, _, _ = compose(parent, parent, cohort); assert np.array_equal(identity, baseline)
    shuffled, _, _ = compose(parent, donor.sample(frac=1, random_state=127), cohort.sample(frac=1, random_state=128))
    assert np.array_equal(shuffled, output)
    altered = donor.copy(); altered.loc[nb | buildings, 'prediction'] = '999999999.123456'
    invariant, _, _ = compose(parent, altered, cohort); assert np.array_equal(invariant, output)
    scaled = donor.copy(); scaled_ticks = d.copy(); scaled_ticks[mask] *= 7
    scaled['prediction'] = [f'{int(x)//1000000}.{int(x)%1000000:06d}' for x in scaled_ticks]
    invariant_scale, _, _ = compose(parent, scaled, cohort); assert np.array_equal(invariant_scale, output)
    payload, _, _ = compose(parent.assign(T0='protected'), donor, cohort) if False else (None, None, None)
    # Interface is intentionally two columns: unrelated payload is rejected,
    # not read as a predictor or allowed to change the algorithm.
    rejection = []
    for name, bad in [('extra_payload', donor.assign(T0='1e30')), ('missing_key', donor.iloc[:-1]),
                      ('negative_price', donor.assign(prediction=donor.prediction.mask(donor.index == 0, '-1.000000')))]:
        try: compose(parent, bad, cohort)
        except (AssertionError, ValueError, KeyError): rejection.append(name)
        else: raise AssertionError('Bad input unexpectedly accepted: ' + name)
    floating = baseline.astype(float) / 1e6; per_cell = []
    for line, new_business in ACTIVE:
        sel = cohort.line.eq(line).to_numpy() & ~nb
        raw = d[sel].astype(float) / 1e6
        predicted = raw * ((baseline[sel].astype(float) / 1e6).sum() / raw.sum())
        assert np.max(abs(predicted - output[sel] / 1e6)) <= .5001e-6
        per_cell.append({'line': line, 'new_business': new_business, 'rows': int(sel.sum()),
            'changed_rows': int(np.count_nonzero(output[sel] != baseline[sel])),
            'max_absolute_float_vs_rational_after_rounding': float(np.max(abs(predicted - output[sel] / 1e6))),
            'total_F3c_CU': sum(int(x) for x in baseline[sel]) / 1e6,
            'total_candidate_CU': sum(int(x) for x in output[sel]) / 1e6,
            'relative_change_quantiles': np.quantile(output[sel] / baseline[sel], [0, .01, .5, .99, 1]).tolist()})
        floating[sel] = predicted
    path = OUT / 'F3c_F4c_REN_MC_nivel_fijo_2025.csv'; write_csv(path, parent.row_id, output)
    result_frame = pd.read_csv(path, dtype=str)
    assert np.array_equal(result_frame.row_id, parent.row_id) and np.array_equal(ticks(result_frame), output)
    assert np.array_equal(result_frame.loc[nb | buildings, 'prediction'], parent.loc[nb | buildings, 'prediction'])
    bytes_out = path.read_bytes(); assert b'\r' not in bytes_out and bytes_out.startswith(b'row_id,prediction\n')
    report = {'author': 'Codex', 'utc': now(), 'status': 'local_composition_QA_passed_predictive_admission_not_established',
        'CSV': {'path': w.rel(path), 'sha256': w.sha(path), 'bytes': path.stat().st_size, 'rows': len(parent),
            'total_CU': sum(int(x) for x in output) / 1e6}, 'normalizers': norms, 'affected_cells': per_cell,
        'new_business_and_all_buildings_prediction_strings_exact': True, 'outside_scope_rows': int((~mask).sum()),
        'identity_shuffle_outside_scope_and_scale_controls_passed': True, 'invalid_inputs_rejected': rejection,
        'independent_integer_rational_vs_float_checked': True, 'new_price_model_fits': 0, 'new_C0_fits': 0,
        'new_model_inferences': 0, 'new_candidate_files': 1, 'new_derived_price_rows': int(mask.sum()),
        'new_scores': 0, 'new_submissions': 0, 'pure_FSp_component_isolated': False,
        'exact_K_candidate_reproduced': False, 'full_building_REN_alternative_complete': False,
        'predictive_validation_passed': False, 'submission_ready': False,
        'received_K_forecast_not_assigned_to_this_candidate': True, 'B00_and_all_alternatives_preserved': True,
        '2024_open': True, 'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'code_sha256': w.sha(Path(__file__))}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': report['status'], 'CSV': report['CSV'], 'affected_cells': per_cell,
        'new_derived_price_rows': int(mask.sum()), 'new_fits': 0, 'new_submissions': 0, 'predictive_validation_passed': False}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'build']); args = parser.parse_args()
    register() if args.mode == 'register' else build_validate()
