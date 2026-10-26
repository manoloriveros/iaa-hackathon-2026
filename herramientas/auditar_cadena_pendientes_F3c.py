"""Scopes, soporte de covariables y grafo de reproducción; sin scores ni modelos."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from cerrar_pendientes_F3c import ROOT, REPO, DATA, SRC, WORK, L, load, save, sha, rel, read

ML = REPO / 'src/semana2/lineas/ml_independiente_20261023/codigo'
NIGHT = REPO / 'src/semana2/lineas/validacion_nocturna_20261023/codigo'


def main(run):
    run.mkdir(parents=True, exist_ok=True)
    names = [ML / n for n in ('preparar_datos.py', 'completitud.py', 'gbm.py', 'variables.py',
        'comun.py', 'historia.py', 'historia2.py', 'produccion.py', 'receta.py', 'mezcla_designada.py')]
    names += [SRC / 'codigo' / n for n in ('etiquetas.py', 'construir_F2.py', 'forma_local.py', 'construir_final.py')]
    names += [SRC / 'exp26_20261026/m017/construir_F3b.py', NIGHT / 'conf_predicciones.py',
              NIGHT / 'evaluar_final.py', NIGHT / 'marco.py', NIGHT / 'variables.py',
              NIGHT / 'construir_final.py', NIGHT / 'transfer.py']
    manifest = [{'path': rel(p), 'sha256': sha(p) if p.exists() else None, 'exists': p.exists()} for p in names]
    config = {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex',
        'code_sha256': sha(Path(__file__)), 'sources': manifest,
        'support_rules': {'categorical': 'categorías no vistas y ausentes; alerta exposición>1%',
            'numeric': 'fuera de rango histórico y PSI con deciles2023-24, alertaPSI>.25',
            'combinations': 'NB,canal,año_completo y dos campos del ramo; escaso<30filas históricas',
            'purpose': 'Descriptivo, sin elegir variables o ajustar precios por lo observado.'}}
    save(run / 'audit_frozen.json', config)
    b, pol, sets = load()
    cu = pd.read_parquet(DATA / 'customers.parquet').set_index('customer_id')
    ad = pd.read_parquet(DATA / 'addresses.parquet').set_index('address_id')
    features = pol.copy()
    for v in cu:
        if v not in features and v not in ('surname', 'email_domain'):
            features[v] = cu[v].reindex(features.customer_id).to_numpy()
    for v in ad:
        if v not in features:
            features[v] = ad[v].reindex(features.address_id).to_numpy()
    features['full_year'] = (b.exposure.reindex(features.index).to_numpy() >= .9)
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'variables': [], 'combinations': [],
              'unavailable_derived_features': [], 'feature_availability': []}
    # Excluir identidades, resultados y fecha exacta del chequeo univariado.
    exclude = {'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'line',
        'renewal_decision', 'written_premium', 'customer_service_contacts', 'missed_payments_12m',
        'surname', 'customer_since_year', 'branch_id', 'campaign_code'}
    for line in L:
        tr = features[(features.line == line) & features.index.isin(b[b.conjunto == 'train'].index)]
        te = features[(features.line == line) & features.index.isin(b[b.conjunto == 'test'].index)]
        exposure = b.exposure.reindex(te.index).to_numpy()
        for v in features:
            if v in exclude or tr[v].notna().sum() == 0:
                continue
            nonnull = tr[v].dropna()
            categorical = not pd.api.types.is_numeric_dtype(nonnull) or pd.api.types.is_bool_dtype(nonnull) or nonnull.nunique() <= 20
            row = {'line': line, 'feature': v, 'rows2025': len(te), 'missing_train': int(tr[v].isna().sum()),
                   'missing2025': int(te[v].isna().sum()), 'type': 'categorical' if categorical else 'numeric'}
            if categorical:
                seen = set(nonnull.astype(str))
                unseen = (~te[v].astype(str).isin(seen) & te[v].notna()).to_numpy()
                row.update({'unseen2025': int(unseen.sum()), 'unseen_exposure_share': float(exposure[unseen].sum() / exposure.sum()),
                    'historical_categories': len(seen)})
            else:
                train = pd.to_numeric(tr[v], errors='coerce').dropna().to_numpy(float)
                future = pd.to_numeric(te[v], errors='coerce').to_numpy(float)
                edges = np.unique(np.quantile(train, np.linspace(0, 1, 11)))
                if len(edges) > 1:
                    edges[0], edges[-1] = -np.inf, np.inf
                    a = np.histogram(train, edges)[0].astype(float)
                    z = np.histogram(future[np.isfinite(future)], edges)[0].astype(float)
                    a, z = np.maximum(a / a.sum(), 1e-6), np.maximum(z / max(z.sum(), 1), 1e-6)
                    psi = float(((z - a) * np.log(z / a)).sum())
                else:
                    psi = None
                outside = np.isfinite(future) & ((future < train.min()) | (future > train.max()))
                row.update({'train_range': [train.min(), train.max()], 'outside_range2025': int(outside.sum()),
                    'outside_exposure_share': float(exposure[outside].sum() / exposure.sum()), 'PSI': psi})
            report['variables'].append(row)
        fields = {'motor': ['new_business', 'channel', 'full_year', 'gender', 'vehicle_value_group'],
                  'buildings': ['new_business', 'channel', 'full_year', 'construction_type', 'occupancy'],
                  'contents': ['new_business', 'channel', 'full_year', 'works_from_home', 'marketing_segment']}[line]
        tk = tr[fields].astype(str).agg('|'.join, axis=1)
        ek = te[fields].astype(str).agg('|'.join, axis=1)
        counts = tk.value_counts()
        n = ek.map(counts).fillna(0).to_numpy()
        flags = pd.DataFrame({'row_id': te.index, 'historical_combination_rows': n,
                              'unseen_combination': n == 0, 'sparse_combination': n < 30})
        flags.to_parquet(run / f'support_flags_{line}_private.parquet', index=False)
        report['combinations'].append({'line': line, 'fields': fields, 'unseen_rows': int((n == 0).sum()),
            'sparse_rows': int((n < 30).sum()), 'total_rows': len(te),
            'unseen_exposure_share': float(exposure[n == 0].sum() / exposure.sum()),
            'sparse_exposure_share': float(exposure[n < 30].sum() / exposure.sum()),
            'limit': 'Combinaciones descriptivas de cinco campos; no demuestra ausencia de soporte continuo ni habilita un precio.'})
    report['feature_availability'] = [
        {'fields': ['gender', 'marketing_segment', 'prior_claims_5y', 'licence_points', 'occupation', 'years_at_address'],
         'source': 'customers.parquet sin fecha de vigencia por atributo', 'quote_availability': 'no_acreditada',
         'consequence': 'No aval profesional de uso. Neutralizar factores propios si no se acredita disponibilidad/admisibilidad; la base también requiere revisión de maestros.'},
        {'fields': ['works_from_home', 'channel', 'new_business', 'cover_type', 'sum_insured'],
         'source': 'periodos de póliza oficiales', 'quote_availability': 'supuesto_del_ejercicio_sin_snapshot_de_cotizacion',
         'consequence': 'No convertir existencia en archivo en prueba de conocimiento al cotizar.'},
        {'fields': ['weather2025'], 'source': 'archivo con año2025', 'quote_availability': 'no_prospectiva_por_existencia',
         'consequence': 'No usar clima2025realizado como covariable al inicio; conservar promedios históricos con alcance explícito.'},
        {'fields': ['renewal_decision', 'customer_service_contacts', 'missed_payments_12m', 'written_premium'],
         'quote_availability': 'riesgo_de_resultado_o_snapshot', 'consequence': 'Revisar por receta; renewal_decision no predictor. Históricos faltantes no se imputan con resultados futuros.'}]
    folds = np.array([int(hashlib.sha256(('mlind_v1|' + c).encode()).hexdigest()[:16], 16) % 5 for c in b.customer_id])
    bb = b.copy()
    bb['customer_fold'] = folds
    fold_audit = []
    for year in (2023, 2024):
        sub = bb[(bb.conjunto == 'train') & (bb.year == year)]
        split_groups = sub.groupby('group').customer_fold.nunique()
        split_addr = sub.groupby('address_id').customer_fold.nunique()
        fold_audit.append({'year': year, 'groups': len(split_groups), 'groups_across_customer_folds': int((split_groups > 1).sum()),
            'addresses_across_customer_folds': int((split_addr > 1).sum()),
            'rows_in_split_groups': int(sub.group.isin(split_groups[split_groups > 1].index).sum())})
    report['fold_audit'] = fold_audit
    def evidence(path, needle):
        text = path.read_text(encoding='utf-8-sig')
        return {'path': rel(path), 'sha256': sha(path),
                'lines': [i for i, line in enumerate(text.splitlines(), 1) if needle in line]}
    report['chain_audit'] = [
        {'stage': 'cost_completion', 'result': 'cost_weighted_not_counts',
         'evidence': evidence(SRC / 'codigo/etiquetas.py', 'weights=w'),
         'limit': 'Coste incurrido neto a una valoración; no coste último observado.'},
        {'stage': 'peril_mix', 'result': 'historical_pool_both_years_uses2024labels',
         'evidence': evidence(SRC / 'codigo/etiquetas.py', 'ult ='),
         'consequence': 'Bloquea afirmar cadena temporal estricta2023->2024.'},
        {'stage': 'category_levels_source', 'result': 'union_source_target_all_covariates',
         'evidence': evidence(ML / 'gbm.py', 'categorias_union'),
         'consequence': 'Transformación transductiva explícita, no fit solo en entrenamiento; corregir requeriría nueva receta y refit.'},
        {'stage': 'fold_assignment', 'result': 'customer_hash_not_address_components',
         'evidence': evidence(ML / 'comun.py', 'mlind_v1|'),
         'consequence': 'Colisiones por dirección medidas; no acreditación integral por grupos.'},
        {'stage': 'F2_production', 'result': 'learns23and24',
         'evidence': evidence(SRC / 'codigo/construir_F2.py', 'pool ='),
         'consequence': 'Válido como aprendizaje para2025; no OOF de sus mismos grupos.'},
        {'stage': 'own_factors_and_Rf_production', 'result': 'learns23and24_then_levels_in_same_pools',
         'evidence': evidence(SRC / 'exp26_20261026/m017/construir_F3b.py', 'pool ='),
         'consequence': 'Separar reproducción exacta de evidencia fuera de muestra.'},
        {'stage': 'source_replay', 'result': 'saved_models_verified_not_retrained',
         'evidence': {'path': rel(REPO / 'privado/semana2/mision017_fase2/linaje_T2b_v1/replay_report.json'),
                      'sha256': sha(REPO / 'privado/semana2/mision017_fase2/linaje_T2b_v1/replay_report.json')},
         'consequence': 'Revisión fuente de producción hasta2024 no valida backtest2023.'},
        {'stage': 'public_level_and_shape', 'result': 'derived_from2025public_feedback',
         'evidence': evidence(SRC / 'codigo/construir_final.py', 'def resolver'),
         'consequence': 'No confirmación independiente; no inferir óptimos públicos para referencias sin sondas.'}]
    graph = [
        {'node': 'raw', 'parents': [], 'command': 'integridad por SHA de once desarrollados y trece emergentes', 'status': 'available'},
        {'node': 'MLind_base', 'parents': ['raw'], 'command': 'python preparar_datos.py; python historia.py; python historia2.py',
         'status': 'code_available_unexecuted_here', 'source': rel(ML / 'preparar_datos.py')},
        {'node': 'T2b_dev_hold', 'parents': ['MLind_base'],
         'command': '$env:MLIND_RAIZ=<sandbox>; $env:MLIND_BACKBONE="T2b"; python gbm.py dev __none__; python gbm.py hold __none__',
         'status': 'training_recipe_located_not_retrained_here', 'seed': 20261024,
         'limit': 'SOLO desconocido deja vacías variantes adicionales y conserva R0/T2b; comprobar entorno y cats antes de ejecutar.'},
        {'node': 'T2b_pcv_prod', 'parents': ['MLind_base'],
         'command': '$env:MLIND_BACKBONE="T2b"; python gbm.py pcv __none__; python gbm.py prod __none__',
         'status': 'training_recipe_located_not_retrained_here', 'seed': 20261024},
        {'node': 'A1_reference', 'parents': ['raw'],
         'command': 'Conf_predicciones.py produce A1decontraste; A1fixF1b3n deproducción requiere SRC de evaluar_final.py, modelos, semillas, historia neutral y promedios originales',
         'status': 'not_portable_closed_graph', 'source': rel(NIGHT / 'conf_predicciones.py'),
         'limit': 'No sustituir A1decontraste por A1fixF1b3n deproducción.'},
        {'node': 'B0', 'parents': ['T2b_pcv_prod', 'A1_reference'], 'command': 'produccion.py + mezcla_designada.py',
         'status': 'saved_predictions_only_for_this_review'},
        {'node': 'F2_final_creible_F3c', 'parents': ['B0', 'T2b_dev_hold', 'A1_reference'],
         'command': 'reproducir_m017_local.py preparar/etiquetas/factores/candidatos',
         'status': 'exact_factor_reproduction_previously_verified',
         'limit': 'ConsumeOOF/CSVprevios; no es orden de entrenamiento total.'},
        {'node': 'F4c', 'parents': ['F2_final_creible_F3c'], 'command': 'construir_F3c.py F4c',
         'status': 'original_FSp_tables_and_production_ancestry_missing'},
        {'node': 'other_operator', 'parents': ['F2_final_creible_F3c'], 'command': 'acta_otro_operador_plantilla.json con operador real',
         'status': 'not_performed_no_external_contact'}]
    report['reproduction_graph'] = graph
    report['full_reproduction_closed'] = False
    report['fallback'] = {
        'unseen_own_factor_key': 'factor1, ya implementado en aplica_tw medianteget(...,1)',
        'undated_or_inadmissible_own_fields': 'neutralizar todos los factores propios y su razónRf; volver a final_creible guardado, sujeto a sus propias limitaciones',
        'base_risk_outside_support': 'constante ramo/negocio entrenada con exposición efectiva como comparador de revisión; no precio comercial operativo aprobado',
        'commercial_material_scenario': 'revisión por referencia antes de publicar o usar; margen de beneficio no cubre incertidumbre por definición',
        'production_predictions_changed': False}
    assert all(sha(ROOT / f['path']) == f['sha256'] for f in manifest if f['exists'])
    save(run / 'audit_results.json', report)
    print(json.dumps({'audit': rel(run / 'audit_results.json'), 'variables': len(report['variables']), 'folds': fold_audit,
                      'full_reproduction': False}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    a = p.parse_args()
    main(a.run.resolve())
