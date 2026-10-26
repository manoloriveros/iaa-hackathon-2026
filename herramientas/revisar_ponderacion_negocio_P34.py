"""Soporte de un peso fuente NB/REN fijado con covariables oficiales, sin modelos."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P34_soporte_peso_negocio_20261026'
PLAN = R/'registro/semana2_peso_negocio_fuente_privada_plan.json'
INDEX = R/'registro/semana2_peso_negocio_fuente_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P34_SOPORTE_PESO_NEGOCIO.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
sp = importlib.util.spec_from_file_location('p34_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False,
                  default=lambda x: x.item() if isinstance(x, np.generic) else str(x))


def binary(value):
    a = np.asarray(value)
    assert pd.notna(a).all() and np.isin(a, [0, 1]).all(), 'Missing or unknown business'
    return a.astype(int)


def ratios(source, future):
    source = binary(source); future = binary(future)
    ns = np.bincount(source, minlength=2); nt = np.bincount(future, minlength=2)
    assert (ns > 0).all() and (nt > 0).all(), 'No regrouping or invented overlap'
    factors = (nt/nt.sum())/(ns/ns.sum())
    weight = factors[source]
    assert np.isclose(weight.sum(), len(source), rtol=1e-13)
    assert np.allclose(np.bincount(source, weights=weight)/weight.sum(), nt/nt.sum(), rtol=1e-13)
    return weight, factors


def ess(weights):
    a = np.asarray(weights, dtype=float); assert np.isfinite(a).all() and (a > 0).all()
    value = a.sum()**2/np.square(a).sum()
    other = 1./np.square(a/a.sum()).sum()
    assert np.isclose(value, other, rtol=5e-14)
    return float(value)


def synthetic():
    source = np.array([0, 0, 0, 1]); future = np.array([0, 1, 1, 1])
    a, factors = ratios(source, future)
    assert np.allclose(a, [1/3, 1/3, 1/3, 3], rtol=1e-15)
    assert np.isclose(ess(a), 12/7, rtol=1e-15)
    reverse, _ = ratios(source[::-1], future[::-1]); assert np.array_equal(reverse[::-1], a)
    pooled = pd.DataFrame({'group': ['A', 'A', 'B', 'C'], 'weight': a}).groupby('group').weight.sum()
    assert np.isclose(ess(pooled), math.fsum(pooled)**2/math.fsum(x*x for x in pooled), rtol=1e-15)
    # Only selected source covariates enter factor estimation, not held covariates.
    frame = np.r_[source, [0, 0, 1, 0]]; selected = np.arange(8) < 4
    before = ratios(frame[selected], future)[1]; frame[~selected] = 1-frame[~selected]
    assert np.array_equal(before, ratios(frame[selected], future)[1])
    rejected = 0
    for bad in [[0, 0, 0], [0, 1, np.nan], [0, 1, 2]]:
        try: ratios(bad, future)
        except AssertionError: rejected += 1
    assert rejected == 3
    return {'nonconstant_ratio_and_mass_exact': True, 'ESS_two_methods_and_group_scalar': True,
            'row_order_exact': True, 'held_source_covariate_argument_boundary': True,
            'missing_business_and_empty_cell_rejected': True, 'new_fits': 0}


def sources():
    paths = [Path(__file__), R/'herramientas/robustez2023_ciclo34.py',
        R/'herramientas/robustez2023_ciclo35.py', R/'herramientas/preparar_estimando_cartera2025.py',
        R/'registro/semana2_robustez2023_ciclo34_plan.json', R/'registro/semana2_robustez2023_ciclo35_plan.json',
        R/'registro/semana2_mision017_A1S_fuente_plan_v1.json',
        BASE/'estimando_cartera2025_v3/report.json', BASE/'P33_soporte_adaptacion_destino_20261026/report.json']
    for line in LINES:
        paths += [HOME/f'rows_s1_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet',
            ROOT/f'Hackaton/Semana 2/Datos/emerging/test_{line}.parquet']
    return paths


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'question': 'Does ONE exact, unclipped business-only source reweighting have adequate support before any training?',
        'hypothesis': 'Source risk fit prioritizes its predominantly renewal portfolio; finite-capacity approximation may be less relevant for the known emerging2025business composition. Coarse weighting is a training-relevance hypothesis, not equality of conditional risks across markets.',
        'novelty': {'C34_C35': 'Motor logistic source/emerging2023attribute density, clipped and then tempered, both stopped by ESS. Different source cohorts, weights and objective. Preserve both failures.',
                    'old2025weights': '18 line/business/duration emerging historical validation strata, ESS failed; this review neither recomputes nor replaces that evaluation.',
                    'P33': 'Target-cell positive cost support failed in20/30scopes. Developed source covariates do not resolve it.'},
        'formula': 'For each line and source fit scope, r_b=(official2025row_share_b)/(current_source_training_row_share_b), b=NB/REN. Positive untrimmed per-row weights with mean1. No duration/channel/region strata, clipping, exponent or parameter search.',
        'source_scopes': ['saved source internal training groups, exclude internal_validation', 'all source groups for a possible later full refit'],
        'read_allowlist': 'Source row_id,year,new_business,exposure_calendar; saved source partition row_id,source_group,internal_validation; official2025 row_id,new_business,period_start,period_end. No T0,e_cost,claim,price or model columns/objects.',
        'screen': {'all_six_scopes_required': True, 'row_ESS_fraction_min': .5, 'group_ESS_fraction_min': .5,
                   'each_business_unique_source_groups_min': 100,
                   'rationale': 'Retain the previous source-training weight rowESS>=.5 screen fromC34/C35; also screen connected group ESS>=.5. This differs from the older .1diagnostic evaluation-weight gate and does not relax either.',
                   'additional_exposure_proxy': 'Report ESS of r*sqrt(calendar exposure), normalized to preserve sum sqrt(exposure), with same.5floor. Covariate proxy only: not actual label-dependent e_cost curvature or a proof of numerical fitting.'},
        'if_fail': 'No weighted price fit, clipping, tempering, regrouping or selecting favorable lines to salvage this recipe. Keep the evidence. Revisit a distinct observed modeling failure before another recipe.',
        'if_pass': 'Only permits preparing a separate same-capacity source-only recipe and objective/regularization controls, followed by whole-target validation under unchanged criteria. No automated fit from this report.',
        'limitations': ['No evidence of conditional outcome stationarity between markets or within business.',
                       'No private labels or prospective availability established; official2025covariates are conditional competition inputs.',
                       'A coarse support pass does not overturn failed fine-grained ESS or sparse emerging cells.'],
        'sources': {w.rel(p): w.sha(p) for p in sources()}, 'new_fits': 0, 'new_scores': 0,
        'new_C0_fits': 0, 'new_submissions': 0, 'B00_all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan)
    text = ('Codex. Registro P34: un solo peso fuente por ramo y NB/REN, proporción oficial2025dividida por proporción del ajuste fuente. '
        'Se estima por separado en los grupos internos de entrenamiento y en la fuente completa. No entran siniestros, C0, precios o modelos. '
        'C34/C35ya fallaron con pesos de dominio logísticos; la ponderación histórica2025de18estratos también sigue fallida. '
        'Este peso grueso es una hipótesis distinta y no crea soporte emergente. Conservo el mínimo.5de ESS de entrenamiento y añado el mismo mínimo por grupos conectados. '
        'No se recorta, modera o cambia la partición para pasar. Sin ajustes ni envíos. B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN))
    body = OUT/'forum_previo.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P34-PESO-PREVIO', '--asunto', 'P34: soporte de un peso fuente por negocio antes de ajustar', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P34registered_covariates_only', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in sources()}
    results = []; future_ids = []
    for line in LINES:
        f = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'new_business', 'exposure_calendar'])
        p = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
        t = pd.read_parquet(ROOT/f'Hackaton/Semana 2/Datos/emerging/test_{line}.parquet', columns=['row_id', 'new_business', 'period_start', 'period_end'])
        assert f.row_id.is_unique and t.row_id.is_unique and np.array_equal(p.row_id, f.row_id)
        assert f.year.isin([2021, 2022, 2023, 2024]).all() and pd.to_datetime(t.period_start).dt.year.eq(2025).all()
        assert (pd.to_datetime(t.period_end) >= pd.to_datetime(t.period_start)).all()
        assert f.exposure_calendar.gt(0).all() and p.source_group.notna().all()
        assert p.groupby('source_group').internal_validation.nunique().max() == 1
        future_ids.extend(t.row_id); future_business = binary(t.new_business)
        for role in ['inner', 'full']:
            selected = ~p.internal_validation.to_numpy(bool) if role == 'inner' else np.ones(len(f), dtype=bool)
            z = f.loc[selected]; groups = p.loc[selected, 'source_group'].to_numpy()
            a, factors = ratios(z.new_business, future_business)
            group_mass = pd.DataFrame({'group': groups, 'mass': a}).groupby('group').mass.sum()
            baseline_group_mass = pd.Series(groups).value_counts().to_numpy(float)
            group_proxy = np.sqrt(z.exposure_calendar.to_numpy(float))*a
            group_proxy *= np.sqrt(z.exposure_calendar.to_numpy(float)).sum()/group_proxy.sum()
            proxy_mass = pd.DataFrame({'group': groups, 'mass': group_proxy}).groupby('group').mass.sum()
            row_fraction = ess(a)/len(a); group_fraction = ess(group_mass)/len(group_mass)
            proxy_row_fraction = ess(group_proxy)/len(a); proxy_group_fraction = ess(proxy_mass)/len(proxy_mass)
            cell_support = []
            for business in [0, 1]:
                ix = binary(z.new_business) == business
                n = len(set(groups[ix])); cell_support.append({'new_business': business, 'source_rows': int(ix.sum()),
                    'source_share': float(ix.mean()), 'future_share': float(np.mean(future_business == business)),
                    'unique_source_groups': n, 'weight': float(factors[business]), 'groups_min100_pass': n >= 100})
            independent = len(a)**2/math.fsum(int(c['source_rows'])*float(c['weight'])**2 for c in cell_support)
            assert np.isclose(independent, ess(a), rtol=5e-14)
            gates = {'row_ESS': row_fraction >= .5, 'group_ESS': group_fraction >= .5,
                     'exposure_proxy_row_ESS': proxy_row_fraction >= .5, 'exposure_proxy_group_ESS': proxy_group_fraction >= .5,
                     'business_groups': all(c['groups_min100_pass'] for c in cell_support)}
            results.append({'line': line, 'role': role, 'rows': len(z), 'source_groups': len(group_mass), 'future_rows': len(t),
                'cells': cell_support, 'row_ESS_fraction': row_fraction, 'group_ESS_fraction': group_fraction,
                'unweighted_group_ESS_fraction': ess(baseline_group_mass)/len(group_mass),
                'exposure_proxy_row_ESS_fraction': proxy_row_fraction, 'exposure_proxy_group_ESS_fraction': proxy_group_fraction,
                'training_row_digest': hashlib.sha256('\n'.join(sorted(z.row_id)).encode()).hexdigest(),
                'training_group_digest': hashlib.sha256('\n'.join(sorted(set(groups))).encode()).hexdigest(),
                'gates': gates, 'support_pass': all(gates.values()), 'ESS_scalar_cell_formula_exact': True})
    assert len(future_ids) == 209063 and len(set(future_ids)) == 209063
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in sources()}
    passed = all(x['support_pass'] for x in results)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P34source_weight_support_review_complete',
        'scopes': results, 'all_scope_support_pass': passed, 'failed_scopes': sum(not x['support_pass'] for x in results),
        'plan_sha256': w.sha(PLAN), 'sources_unchanged': True, 'outcomes_or_models_read': False,
        'new_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_prices': 0, 'new_scores': 0, 'new_submissions': 0,
        'old_fine_weight_ESS_not_resolved': True, 'emerging_support_not_resolved': True,
        'B00_all_alternatives_preserved': True, '2024_open': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    text = '# P34: soporte de un peso fuente por negocio\n\nCodex, '+report['utc']+'.\n\n'
    text += ('Se revisó una sola razón de proporciones NB/REN, por ramo y ámbito fuente, antes de ajustar. '
        'Los únicos datos leídos fueron claves, particiones, negocio, fechas y exposición de calendario. No entraron etiquetas, C0, precios o modelos.\n\n')
    text += '| Ramo | Ámbito | ESS filas / n | ESS grupos / G | Pasa todos los mínimos |\n|---|---|---:|---:|---|\n'
    for a in results: text += f"| {a['line']} | {a['role']} | {a['row_ESS_fraction']:.4f} | {a['group_ESS_fraction']:.4f} | {a['support_pass']} |\n"
    text += ('\n'+('Los seis ámbitos pasan los mínimos de soporte. Esto solo permite preparar una receta separada y controles del objetivo; no demuestra transportabilidad o ganancia.' if passed else
        'La receta completa falla el soporte. No se ajusta, recorta o modera el peso ni se eligen ramos para hacerla pasar. Se conserva el resultado adverso.')+
        ' Los fallos de los pesos finos históricos y del soporte NB/broker emergente siguen vigentes. Las cuentas fuente no son siniestros emergentes.\n\n'
        'La prueba difiere de C34/C35, que usaron clasificadores de dominio de2023; también de los18estratos usados para sensibilidad de validación. '
        'La propuesta actual no estima una densidad condicional completa. Cambios de riesgo dentro de NB/REN o entre mercados pueden invalidar esa aproximación.\n\n'
        'Cero ajustes, C0, inferencias, precios, scores o envíos. B00/F3c y alternativas conservados,2024abierto adaptativo. Evidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    post = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P34-PESO-RESULTADO', '--asunto', 'P34: soporte de ponderación fuente por negocio, sin ajustar', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    next_unit = ('Prepare a separately preregistered same-capacity source training-relevance assay; freeze exact objective, source split/weights, alpha or gradient regularization, source veto, full-target gates and fit budget. No automatic fit from overlap.' if passed else
        'P35: inspect existing feature lineage for a documented source input mismatch still unresolved by standard models. Bound review to construction/occupancy/deductible/official weather availability and existing model recipes; do not repeat P13/P22/P31/P32, refit density weights or chase the failed support floor. Identify one distinct, temporally admissible missing mechanism before a new recipe; preserve no-submission status.')
    receipt = {'author': 'Codex', 'utc': report['utc'], 'status': report['status'], 'report': w.rel(OUT/'report.json'),
        'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC), 'all_scope_support_pass': passed,
        'failed_scopes': report['failed_scopes'], 'forum': json.loads(post.stdout), 'next_unit': next_unit,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, '2024_open': True, 'goal_achieved': False}
    archive = R/'privado'/('corte_P34_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P34': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P34': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P34=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P34: soporte de ponderación fuente por negocio\n\nCodex, '+report['utc']+'. Pasa el conjunto de ámbitos='+str(passed)+'; fallos='+str(report['failed_scopes'])+'. Cero ajustes, inferencias, scores o envíos. No se rescata el soporte fino ni se mezcla soporte entre mercados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_business_weight_index': w.rel(INDEX), 'week_2_private_source_business_weight_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'all_scopes_pass': passed, 'failed_scopes': report['failed_scopes'],
        'scopes': [{k: a[k] for k in ['line', 'role', 'row_ESS_fraction', 'group_ESS_fraction']} for a in results], 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run']); args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.mode]()
