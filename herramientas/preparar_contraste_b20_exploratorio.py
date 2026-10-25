"""Congela la enmienda y sus criterios antes de cualquier ajuste del concurso."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]


def main():
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    old_path = REPO / 'registro/semana2_b20_contraste_minimo_diseno_v1.json'
    old = read(old_path)
    ridge = read(REPO / 'registro/semana2_glm_ridge_coberturas_plan_v1.json')
    scopes = read(REPO / 'registro/semana2_b20_preflight_c0_plan_v1.json')
    run = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
    run.mkdir(exist_ok=False)
    (run / 'sources').mkdir()
    acceptance = deepcopy(old['acceptance'])
    acceptance['preconditions'] = [
        'Explicit participant authorization for this exploratory fit, preserving v1 support failure',
        'Frozen recipe, sources, implementation, resources and forum preregistration',
        'Strict2023 full-pipeline synthetic isolation preflight passes',
        'No unresolved technical blockers; positive finite rates/C0 and identifiable calibration',
    ]
    source_paths = {
        'feature_frames': {str(k): str(ROOT / scopes['period_metadata_files']['buildings']).replace('fold0.parquet', f'fold{k}.parquet') for k in range(5)},
        'other_line_frames': {line: str(ROOT / scopes['period_metadata_files'][line]) for line in ['motor', 'contents']},
        'claim_audit': str(REPO / 'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/claim_assignment_audit.parquet'),
        'claim_metadata': {str(k): str(ROOT / scopes['outer_scopes'][k]['files']['reporting_fit_claims.parquet']) for k in range(5)},
        'outer_models': {str(k): str(REPO / f'privado/semana2/desarrollo2023/ridge20_20261024_v1/models/buildings_fold{k}/bundle.joblib') for k in range(5)},
        'raw_oof': str(REPO / 'privado/semana2/desarrollo2023/ridge20_20261024_v1/new_oof_2023.parquet'),
        'original_bands': str(REPO / 'privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1/heldout_bands_2023.parquet'),
    }
    files = [old_path, REPO / 'registro/semana2_glm_ridge_coberturas_plan_v1.json',
             REPO / 'registro/semana2_b20_soporte_folds_actual.json',
             REPO / 'registro/semana2_contadores_propios_actual.json']
    for value in source_paths.values():
        files.extend(Path(x) for x in value.values()) if isinstance(value, dict) else files.append(Path(value))
    sources = [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    plan = {
        'id': 'S2-B20-CONTRASTE-EXPLORATORIO-v2-20261024', 'author': 'Codex',
        'registered_utc': datetime.now(timezone.utc).isoformat(), 'path_base': 'workspace_root',
        'authorization_literal': 'Dale, prepara la enmienda y entrena el contraste exploratorio de B20 con los criterios fijados antes. Mantén 2024 cerrado, sin promover modelos ni enviar a Kaggle.',
        'amends': {'path': old_path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(old_path.read_bytes()).hexdigest()},
        'change': 'Known concentration/support failure and plausible mechanism no longer prohibit this single exploratory fit. They remain failed/unestablished and prohibit any claim that support has been resolved. Technical integrity remains mandatory.',
        'unchanged': ['All original numerical predictive/influence acceptance thresholds',
                      'One S versus L comparison; fixed B20 alpha1/seven effects; no searches',
                      'Original grouped2023 folds, T0, rho1 C0, all losses/periods',
                      'Raw motor/contents exact; original outer band memberships',
                      'No2024/test, promotion, selection-policy change or Kaggle submission'],
        'mechanism': old['mechanism'], 'contrast': old['contrast'], 'acceptance': acceptance,
        'uncertainty': 'Original no-new-bootstrap/no-new-CI rule retained. Report all five fold effects, slope dispersion and favorable-component sensitivity; no independent confirmation or refit uncertainty claim.',
        'segment_definitions': {'new_customer': 'x_customer_tenure_years ==0 in prepared2023 metadata; not a synonym for x_new_business',
             'renewal': 'x_new_business ==0', 'buildings_new': 'line=buildings and x_new_business ==1',
             'buildings_renewal': 'line=buildings and x_new_business ==0'},
        'calibration_numerics': {'solver': 'bounded scipy minimize_scalar on[0,1], profile intercept',
             'xatol': 1e-8, 'maxiter': 500, 'endpoints_explicit': [0., 1.],
             'objective_tie_relative': 1e-10, 'tie_preference': 'b1 then b0 then interior',
             'boundary_tolerance': 1e-6, 'profile_intercept_values_counted': 10,
             'minimum_inner_log_P80_P20': old['support']['inner_calibration_each_outer_scope']['log_rate_p80_minus_p20_min']},
        'recipe': ridge['recipe'], 'inputs': source_paths, 'frozen_sources': sources,
        'claim_reader': 'Arrow predicate before materialization: accepted claim IDs from strict2023 metadata union, emerging, buildings, included_in_T0 true, loss_date in2023. Only identity/date/T0 columns. Mixed-year source never materialized wholesale.',
        'execution': {'run': run.relative_to(ROOT).as_posix(), 'threads': 2,
            'unique_inner_GLM_fits': 10, 'C0_workflows': 10, 'reporting_peril_fits': 60,
            'frequency_constants': 60, 'weighted_marks_from_reporting': 60, 'mixtures': 10,
            'saved_outer_models_reused': 5, 'slope_calibrations': 5, 'intercept_values': 10,
            'new_outer_models': 0, 'new_other_line_models': 0, 'new_bootstrap': 0,
            'new_catalog_recipes': 0, 'remote': False},
        'support_v1': old['support'], 'support_status': 'FAILED preserved; permission_to_explore is not statistical_support',
        'acceptance_consequence': 'All numerical criteria conjunctive. Failure/unknown => exploratory rejection; preserve raw B20 and all artifacts. Even a pass is only an exploratory signal, never promotion. No automatic next recipe.',
        'forum_prior': 'COD-S2-20261024-B20-EXPL-V2-PRE', 'reference': 'W2-B00',
        'promotion': False, 'submission': False, '2024_test_closed': True,
        'prior_exposure': 'Prior2024 narratives and the mixture public score were seen in other contexts; not used to choose this fixed recipe.2023 repeatedly used, so no complete-blindness claim.',
        'implementation_frozen': False,
    }
    for name in ['plan_preregistered.json']:
        (run / name).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    target = REPO / 'registro/semana2_b20_enmienda_exploratoria_v2_20261024.json'
    assert not target.exists()
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    body = f'''Codex. El participante autoriza expresamente preparar la enmienda y entrenar este contraste exploratorio, manteniendo2024 cerrado, sin promoción ni envío. Enmienda v2: se permite un único ensayo S (pendiente0..1 más nivel) frente a L (solo nivel), conservando el soporte v1 FAILED y el mecanismo plausible/no establecido. No se rebajan sus cifras ni se presenta como resuelto. Se heredan todos los umbrales predictivos de v1: mejora global≥0,0005 frente a L, sin pérdida frente a B20,4/5folds no negativos, peor fold≥−0,001, pendiente interior en4/5, reducción de brecha extrema≥20%, salvaguardas de segmentos≥−0,001, influencia no negativa y cambio de total edificios≤5%. Sin bootstrap/CI nuevos, búsqueda de recetas, cambio de alpha, cortes o pérdidas. Preflight técnico completo obligatorio antes de datos reales.

Presupuesto:10GLM interiores edificios,10C0 con60curvas/60frecuencias/10mezclas,5pendientes y10valores de intercepto (ambos brazos); reutilizar5B20 exteriores. Solo2023; lectura de notificaciones por predicado antes de materializar, nunca tabla multiaño completa. Resultado adverso no dispara otra receta. Los casos de concentración se conservan aunque el entrenamiento esté autorizado. Archivo de enmienda: {target.relative_to(ROOT).as_posix()}. Criterios registrados UTC{plan['registered_utc']}, antes de ajustes o nuevos resultados del concurso. Sin2024/test, promoción, catálogo nuevo, Kaggle, remoto, mensajes externos, automatizaciones o delegación. Revisión propia, no profesional independiente.'''
    (run / 'aporte_previo.md').write_text(body + '\n', encoding='utf-8')
    print(json.dumps({'plan': target.relative_to(ROOT).as_posix(), 'registered_utc': plan['registered_utc'], 'frozen_sources': len(sources)}))


if __name__ == '__main__':
    main()
