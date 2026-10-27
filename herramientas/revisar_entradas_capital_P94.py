"""Cierra la selección P93 y registra el contrato de capital directo al destino.

Solo compara artefactos existentes y código de procedencia. No importa motores
de modelos, no predice, no estima parámetros y no consulta respuestas nuevas.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'P94_contrato_capital_destino_20261027'
PLAN = R / 'registro/semana2_capital_destino_revision_plan.json'
INDEX = R / 'registro/semana2_capital_destino_revision_actual.json'
DOC = R / 'docs/semana2/PRIVADA_P94_CAPITAL_DESTINO.md'
OLD = BASE / 'P90_validacion_boosting_prior_20261027'
NEW = BASE / 'P93_validacion_selector_rondas_20261027'
LEGACY = ROOT / 'Hackaton/Semana 2/Claude/validacion_nocturna_20261023/codigo'
spec = importlib.util.spec_from_file_location('p94_concurrent_writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def utc():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject):
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', identifier, '--asunto', subject, '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    return json.loads(p.stdout)


def check_sources(plan):
    for path, sha in plan['sources'].items():
        assert w.sha(ROOT / path) == sha, path


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R / 'registro/semana2_mision017_fase2_actual.json')
    assert phase['P93_execution']['state'] == 'TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    files = [Path(__file__), NEW / 'completion_receipt.json', NEW / 'report.json',
        NEW / 'POOLED_prices.parquet', OLD / 'POOLED_prices.parquet',
        LEGACY / 'variables.py', LEGACY / 'base_mercado.py',
        R / 'herramientas/preparar_nucleo_A1S.py', R / 'herramientas/preparar_GLM_offset_P56.py',
        R / 'herramientas/fuente_marca_capital_P43.py',
        R / 'docs/semana2/VARIABLES_Y_ULTIMO.md',
        R / 'registro/semana2_g4_capital_contrato_v2.json']
    files += [NEW / f'outer{i}/primary_bundle.json' for i in range(5)]
    files += [BASE / f'P64_reporte_por_ramo_preflight_20261027/input_{line}_0.parquet'
        for line in ['motor', 'buildings', 'contents']]
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': utc(),
        'scope': 'P93 saved inner margins and exact pooled-frame identity; static lineage of capital omitted from current direct target design. No old source/support suites.',
        'hypothesis': 'A source capital function already exists, but a direct target main effect could represent market-specific scale response absent from the current rating design. This is a candidate need, not evidence of benefit or a source omission.',
        'criterion': 'Exact same P90/P93 pooled rows, column order, dtypes and values; all five saved losses copied without scoring. Distinguish actual A1S deterministic normalization from premium-dependent G4 quality repair.',
        'future_contract': {'lines': ['buildings', 'contents'],
            'raw_field': 'sum_insured from official emerging policies, projected row_id/period_start/sum_insured only; historical 2023/2024',
            'normal_range_upper_inclusive': {'buildings': 10000000, 'contents': 1000000},
            'threshold_provenance': 'Existing F0 uncertainty filters in VARIABLES_Y_ULTIMO.md; not official limits or newly optimized thresholds.',
            'normal_value': 'Keep original finite positive sum_insured within fixed uncertainty filter. Log1p once, train-only median/center/scale in the existing standard GLM.',
            'uncertain_value': 'Outside range or nonfinite becomes missing; impute own-training median. No division by1000, premium test, learned capital bounds or capital-uncertainty pricing flag.',
            'motor': 'Unchanged vehicle_value_group and existing motor model; no invented monetary value.',
            'availability': 'Conditional supplied policy snapshot, period keyed; no transaction timestamp proves quote-time vintage. Do not certify prospective availability.',
            'comparator': 'P88 complete own-training calibrated two-source prior and alpha1 standard GLM, unchanged target/exposure/q/folds/other fields.',
            'reuse': 'Reuse same-scope P88 source-level calibrations and motor models by code/data/keys hashes; never copy an outer calibration into an inner scope.',
            'prohibition': 'No claims/premium for capital transformation, no G4 2023 buildings object transferred to another scope, no new capital flag as pricing predictor.',
            'next_gate': 'Separate synthetic whole-flow preflight and raw-key binding before any real fit; then separate preregistration of full fixed evaluation.'},
        'budget': {'new_fits': 0, 'model_loads': 0, 'predictions': 0, 'new_scores': 0,
            'resampling': 0, 'CDF_fits': 0, '2025_inference': 0, 'submissions': 0},
        'sources': {w.rel(p): w.sha(p) for p in files}, '2024_open': True,
        'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. P94 registra el cierre descriptivo de P93 y la revisión de linaje del capital directo al destino. Se comparan solo filas/precios ya guardados y los cinco objetivos internos existentes, sin puntuar ni inferir. Capital ya estaba en las fuentes; se revisa su ausencia en el diseño directo actual. La futura opción estándar conserva solo capital original positivo dentro de los filtros F0 ya declarados (edificios10M/contenidos1M); casos inciertos nulos con mediana propia, sin bandera de calidad en precio, prima o reparación. Disponibilidad de snapshot condicional. No se ajusta un candidato en esta revisión. B00 y todas las alternativas preservados; 2024 abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    reg = {'author': 'Codex', 'utc': utc(), 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P94-CAPITAL-PREVIO', 'P94: cierre de rondas y contrato de capital directo')}
    dump(OUT / 'registration.json', reg)
    dump(INDEX, reg)
    print(json.dumps(reg))


def run():
    plan = w.read(PLAN)
    check_sources(plan)
    assert w.read(OUT / 'registration.json')['plan_sha256'] == w.sha(PLAN)
    sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
    import pandas as pd
    import pyarrow.parquet as pq
    a = pd.read_parquet(OLD / 'POOLED_prices.parquet')
    b = pd.read_parquet(NEW / 'POOLED_prices.parquet')
    assert a.equals(b) and list(a) == list(b) and a.dtypes.equals(b.dtypes)
    records = []
    for i in range(5):
        selection = w.read(NEW / f'outer{i}/primary_bundle.json')['selection']
        losses = selection['losses']
        assert selection['rounds'] == 64 and losses[0] == min(losses)
        records.append({'outer': i, 'selected': 64, 'saved_losses_64_128_256': losses,
            'excess_vs64': [v-losses[0] for v in losses],
            'relative_excess_vs64': [(v-losses[0])/losses[0] for v in losses]})
    schema = {line: pq.read_schema(BASE / f'P64_reporte_por_ramo_preflight_20261027/input_{line}_0.parquet').names
        for line in ['motor', 'buildings', 'contents']}
    assert all('sum_insured' not in names and 'log_si' not in names for names in schema.values())
    code = (LEGACY / 'variables.py').read_text(encoding='utf8')
    actual = code[code.index("        si = df['sum_insured']"):code.index("    if line == 'buildings':", code.index("        si = df['sum_insured']"))]
    assert "np.where(scale, si / 1000.0, si)" in actual and 'premium' not in actual and 'ppm' not in actual
    check_sources(plan)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P94_saved_selection_and_direct_capital_contract_reviewed',
        'pooled_frame_exact_P90_P93': True, 'pooled_rows': len(a), 'selection': records,
        'capital_fields_present_in_current_raw_inputs': {line: [n for n in names if any(z in n.lower() for z in ['capital','insured','value','rcn'])] for line,names in schema.items()},
        'actual_A1S_capital_path': {'producer': w.rel(LEGACY / 'variables.py'), 'expression': actual,
            'fixed_division_thresholds': {'buildings': 5000000, 'contents': 2000000},
            'premium_dependency_in_this_actual_transform': False,
            'limit': 'Conditional historical normalization already in frozen source; not a new official scale correction or proof all high limits are erroneous.'},
        'distinct_G4_path': 'Premium-dependent audit bounds, 2023 buildings scopes only. Not the actual A1S log_si expression and not reused here.',
        'prior_work': 'P43 capital-only developed source marks and P44 whole destination failure are retained. B13/B14 target capital work is historical; this plan does not claim a first capital experiment or generalize those outcomes.',
        'future_contract': plan['future_contract'], **plan['budget']}
    dump(OUT / 'report.json', report)
    print(json.dumps({'complete': True, 'pooled_rows': len(a), 'all_pooled_values_exact': True, 'new_fits': 0}))


def close():
    plan = w.read(PLAN)
    check_sources(plan)
    report = w.read(OUT / 'report.json')
    next_unit = 'P95: implement strict raw-capital historical join and same P88 standard GLM with one additional capital main effect for buildings/contents, no uncertainty pricing flag. Validate whole synthetic held-poison/replay/offset math and no premium reads; separate full evaluation registration before real fits. Reuse exact same-scope levels/motor, no threshold/alpha/line rescue.'
    text = '# P94: capital directo al destino\n\nCodex, '+utc()+'.\n\n'
    text += 'P93 conserva exactamente las '+str(report['pooled_rows'])+' filas, columnas, tipos y valores del archivo agrupado P90. Los cinco selectores internos prefieren64rondas; ampliar a128/256 empeora sus objetivos guardados. No se calculó otro score.\n\n'
    text += '| Fold exterior | Exceso interno128 frente64 | Exceso interno256 frente64 |\n|---|---:|---:|\n'
    for z in report['selection']:
        text += f"|{z['outer']}|{z['relative_excess_vs64'][1]:.4%}|{z['relative_excess_vs64'][2]:.4%}|\n"
    text += '\nEl capital ya existe en las fuentes congeladas. El productor real de A1S aplica una división determinista por1000por encima de5M/2M; esa expresión no consulta prima. Su comentario CAP-N1 y el contrato G4 describen otros caminos: G4 sí depende de prima y sus ámbitos de edificios2023no se trasladan aquí. El GLM directo actual excluye el capital por decisión de P56, no por una pérdida accidental de columnas.\n\n'
    text += 'La necesidad que se plantea es una respuesta de capital propia del destino, además de la incorporada en las predicciones fuente. No demuestra una mejora. Se conserva el capital oficial positivo dentro de los filtros de incertidumbre F0 (10M edificios,1M contenidos), sin corregir la escala de los casos dudosos. Esos casos se imputarían con mediana de entrenamiento, sin bandera de calidad como predictor. Los límites son filtros históricos, no límites oficiales. La instantánea de pólizas carece de fecha de transacción que certifique la disponibilidad al cotizar.\n\n'
    text += 'La próxima opción conserva GLM Tweedie1,5, alpha1, efectos principales, prior y exposición de P88. Motor queda igual. Se reutilizan parámetros solo si coinciden ámbito, claves, datos y código; nunca se prestan a un ámbito interno. Primero se probará el flujo sintético y el enlace estricto por fila. P43/P44 y B13/B14 siguen registrados; esto no es la primera revisión de capital. Cero ajustes, predicciones, remuestreos o envíos. B00 y alternativas preservados.2024abierto adaptativo; conclusiones exploratorias sin validación privada ni revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text, encoding='utf8')
    body = OUT / 'forum_resultado.md'
    body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'),
        'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC), 'next_unit': next_unit,
        **plan['budget'], '2024_open': True, 'goal_achieved': False,
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P94-CAPITAL-RESULTADO', 'P94: identidad de precios y capital con linaje separado')}
    cut = R/'privado'/('corte_P94_'+datetime.now(timezone.utc).strftime('%H%M%S%f'))
    cut.mkdir()
    w.update(INDEX, receipt, cut)
    for path, key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P94'), (R/'registro/semana2_mision_privada_actual.json','P94')]:
        w.update(path, {key:receipt, 'next_unit':next_unit}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'
    own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P94=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025':own}, cut)
    note = '\n\n## Privada P94: contrato de capital directo\n\nCodex, '+receipt['utc']+'. Identidad completa P90/P93 comprobada sin inferir; normalización real A1S separada de G4 dependiente de prima. Capital ya presente en fuentes, ausente por diseño en GLM directo. Próxima unidad: '+next_unit+' Informe: '+w.rel(DOC)+'.\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_direct_capital_review_index':w.rel(INDEX),'week_2_private_direct_capital_review_report':w.rel(DOC)}, cut)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['register','run','close'])
    {'register':register,'run':run,'close':close}[p.parse_args().mode]()
