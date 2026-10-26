"""Informe y registro de consecuencias a partir de resultados conservados."""
from __future__ import annotations
import argparse
import ast
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import numpy as np
import pandas as pd
from cerrar_pendientes_F3c import REPO, ROOT, DATA, WORK, SRC, read, save, sha, rel


def f(x, n=6):
    return f'{float(x):,.{n}f}'.replace(',', '@').replace('.', ',').replace('@', '.')


def interval(x):
    return '[' + '; '.join(f(a) for a in x) + ']'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows])


def natural(text):
    protected = []
    def keep(match):
        protected.append(match.group())
        return chr(0xE000 + len(protected) - 1)
    text = re.sub(r'`[^`]+`|[^\s,;()]+/[^\s,;()]+|[^\s,;()]+_[^\s,;()]+', keep, text)
    text = re.sub(r'A1fixF1b3n|final_creible|F3c|F3d|F4c|T2b|T0|F2|Rf|A1|R0|B00|B03|B05|B0|C0|v1|v2|NB|REN|IC95|IC90|SHA256|PSI', keep, text)
    letters = 'A-Za-zÁÉÍÓÚÜÑáéíóúüñ'
    text = re.sub(r'([' + letters + r'])(?=\d)', r'\1 ', text)
    text = re.sub(r'(\d)(?=[' + letters + r'])', r'\1 ', text)
    text = re.sub(r'(%)(?=[' + letters + r'])', r'\1 ', text)
    text = re.sub(r'([' + letters + r'0-9])([\uE000-\uEFFF])', r'\1 \2', text)
    text = re.sub(r'([\uE000-\uEFFF])(?=[' + letters + r'0-9])', r'\1 ', text)
    for i, value in enumerate(protected):
        text = text.replace(chr(0xE000 + i), value)
    text = re.sub(r',(?=[A-Za-zÁÉÍÓÚáéíóúñ])', ', ', text)
    text = re.sub(r'(?<=[A-Za-záéíóúñ])(?=[+−-]\d)', ' ', text)
    text = re.sub(r'([+−-]\d)', r'\1', text)
    text = text.replace('IC95[', 'IC95 [').replace('IC90[', 'IC90 [')
    for old, new in {'deoctubre': 'de octubre', 'dediciembre': 'de diciembre', 'CUnetos': 'CU netos',
                     'deproducción': 'de producción', 'decontraste': 'de contraste',
                     'decompletitud': 'de completitud', 'de0': 'de 0', 'de15': 'de 15',
                     'de100': 'de 100', 'sin0': 'sin 0', 'IAAConsideraciones': 'IAA Consideraciones',
                     'factoresF3c': 'factores F3c', 'T2bdev': 'T2b dev', 'dev/hold/pcv/prod': 'dev/hold/pcv/prod',
                     'ambosCSVidénticos': 'ambos CSV idénticos', 'FSporiginales': 'FSp originales',
                     'escalasT2b': 'escalas T2b', 'F3ccontrafinal_creible': 'F3c contra final_creible',
                     'A1contraR0': 'A1 contra R0', 'porescenario': 'por escenario',
                     'optimizaciónTweedie': 'optimización Tweedie', 'contractualNB': 'contractual NB',
                     'ramo/negocio2024': 'ramo/negocio 2024', 'es-': 'es -', 'a-0,': 'a -0,',
                     'de−': 'de −', 'al mínimo−': 'al mínimo −', 'limpieza/desarrollo/categor í as/calibraci ón': 'limpieza/desarrollo/categorías/calibración',
                     'CUde': 'CU de', 'CUtras': 'CU tras', 'CUy': 'CU y', 'porSHA': 'por SHA', 'ySHA': 'y SHA',
                     'porfila': 'por fila', 'ancestrosT2b': 'ancestros T2b', 'fasesT2b': 'fases T2b', 'tablasFSp': 'tablas FSp',
                     'semillas11/12/13': 'semillas 11/12/13', 'identidadesDecimal/float': 'identidades Decimal/float',
                     'Rya': 'R ya', 'primaP': 'prima P', 'concat=': 'con cat=', 'profesionales§': 'profesionales §',
                     ';Gobernanza': '; Gobernanza', ';Documentación': '; Documentación', 'y§': 'y §',
                     '1 e −8': '`1e-8`', '2023,92.267': '2023; 92.267', 'aparte:34': 'aparte: 34',
                     'autos,2,15': 'autos, 2,15', 'edificios,2,69': 'edificios, 2,69'}.items():
        text = text.replace(old, new)
    return text


def main(run, audit_run):
    d, audit = read(run / 'results.json'), read(audit_run / 'audit_results.json')
    verified = read(run / 'verification.json')
    independent = read(run / 'independent_math_and_poison.json')
    assert verified['result_sha256'] == independent['results_sha256'] == sha(run / 'results.json')
    primary = d['comparisons']['DEV23_T2b_to_HOLD24_T2b']
    inverse = d['comparisons']['HOLD24_T2b_to_DEV23_T2b']
    b = pd.read_parquet(WORK / 'base_etiquetas.parquet').set_index('row_id')
    band_rows = []
    for year in (2023, 2024):
        for line in ('motor', 'buildings', 'contents'):
            h = b[(b.year == year) & (b.line == line) & b.new_business & (b.exposure >= .9)]
            ft = b[(b.conjunto == 'test') & (b.line == line) & b.new_business & (b.exposure >= .9)]
            band_rows.append({'year': year, 'line': line, 'rows': len(h), 'exposure': h.exposure.sum(),
                'positive_periods': int((h.y > 0).sum()), 'future_rows': len(ft), 'future_exposure': ft.exposure.sum()})
    save(run / 'support_full_year.json', band_rows)
    expense_corrected = (run / 'veinte_primas_gasto_por_poliza.json').exists()
    commercial = read(run / ('veinte_primas_gasto_por_poliza.json' if expense_corrected else 'veinte_primas_privadas.json'))
    price_summary = read(run / 'gasto_por_poliza_resumen.json') if expense_corrected else None
    ref = pd.read_parquet(DATA / 'reference_policies.parquet').set_index('row_id')
    refs = []
    for number, (idx, r) in enumerate(ref.iterrows(), 1):
        rows = [x for x in commercial if x['row_id'] == idx]
        nominal = {x['model']: x for x in rows if x['scenario'] == 'nominal'}
        cases = [x for x in rows if x['model'] == 'F3c']
        p0 = Decimal(nominal['F3c']['commercial_unrounded'])
        pc = Decimal(nominal['sin_factores_final_creible']['commercial_unrounded'])
        vals = [Decimal(x['commercial_unrounded']) for x in cases]
        low, high = min(vals), max(vals)
        material = abs(pc / p0 - 1) >= Decimal('.1')
        refs.append({'reference': number, 'row_id': idx, 'line': r.line, 'new_business': bool(r.new_business),
            'channel': r.channel, 'exposure': r.exposure,
            'F3c_risk_period': nominal['F3c']['risk_period'],
            'F3c': nominal['F3c']['commercial'], 'without_own_factors': nominal['sin_factores_final_creible']['commercial'],
            'difference_without_factors_pct': float((pc / p0 - 1) * 100), 'material_10pct': bool(material),
            'scenario_min': str(low.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
            'scenario_max': str(high.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
            'scenario_min_name': min(cases, key=lambda x: Decimal(x['commercial_unrounded']))['scenario'],
            'scenario_max_name': max(cases, key=lambda x: Decimal(x['commercial_unrounded']))['scenario'],
            'explanation': 'Gastos y exposición iguales. La diferencia nominal procede de los factores residuales y su razón de nivel; los extremos son escenarios deterministas de nivel por celda, no intervalos de confianza individuales.'})
    save(run / 'veinte_referencias_comparadas.json', refs)
    private = '# Veinte primas, candidatos y escenarios\n\nCodex. Importes restringidos, fuera de Git. No son precios aprobados para uso real.\n\n'
    private += table(['Ref', 'row_id', 'Ramo', 'Exposición', 'F3c CU', 'Sin factores CU', 'Cambio %', 'Mín. escenarios', 'Máx. escenarios'],
        [[x['reference'], x['row_id'], x['line'], f(x['exposure'], 4), x['F3c'], x['without_own_factors'], f(x['difference_without_factors_pct'], 2), x['scenario_min'], x['scenario_max']] for x in refs])
    private += '\n\nEl riesgo del CSV corresponde al periodo. La tasa anual se obtiene dividiendo por exposición solo para comparar; no se vuelve a multiplicar por exposición para construir el precio. '
    private += ('El gasto fijo principal es 85 CU por póliza, sin prorrateo. Los decimales exactos, denominadores y escenarios están en veinte_primas_gasto_por_poliza.json. ' if expense_corrected else
                'En esta hipótesis previa el gasto fijo se prorratea con la exposición oficial, redondeada a cuatro decimales. Los decimales exactos, denominadores y escenarios están en veinte_primas_privadas.json. ')
    private += 'Los extremos mezclan tensiones de reservas y de severidad; no representan probabilidades ni justifican el margen de beneficio.\n'
    if expense_corrected:
        private += '\n\nLectura principal: 85 CU por póliza, según el nombre y unidad oficiales. El prorrateo previo se conserva en VEINTE_PRIMAS_COMPARADAS.md y veinte_primas_privadas.json. No hay indicación oficial de que los 85 CU sean anuales. La incertidumbre de asignar gastos a subperiodos se muestra por separado, sin cambiar el riesgo del CSV.\n'
    (run / ('VEINTE_PRIMAS_GASTO_POR_POLIZA.md' if expense_corrected else 'VEINTE_PRIMAS_COMPARADAS.md')).write_text(private, encoding='utf-8')
    rows = []
    for name, view in d['comparisons'].items():
        rows.append([name.replace('_to_', ' → '), f(view['metrics']['all']['delta_F3c_minus_sin_factores']),
            interval(view['bootstrap']['intervals']['all']['delta_CI_family6']),
            f(view['metrics']['new_business']['delta_F3c_minus_sin_factores']),
            f(view['metrics']['motor_1']['delta_F3c_minus_sin_factores'])])
    comparison_table = table(['Vista', 'Δ D² global', 'Banda condicional familia 6', 'Δ NB', 'Δ autos NB'], rows)
    segments = []
    for name in ('motor', 'buildings', 'contents', 'new_business', 'renewal'):
        x = primary['metrics'][name]
        segments.append([name, f(x['models']['sin_factores']['D2']), f(x['models']['F3c_transferido']['D2']),
                         f(x['delta_F3c_minus_sin_factores']), interval(primary['bootstrap']['intervals'][name]['delta_CI95'])])
    seg_table = table(['Segmento 2024', 'Sin factores', 'Con factores', 'Diferencia', 'IC95 condicional'], segments)
    by_year = d['support']['business_by_year']
    business = []
    for year in (2023, 2024, 2025):
        yr = [x for x in by_year if x['year'] == year]
        nb = next(x for x in yr if x['new_business'])
        business.append([year, f(sum(x['rows'] for x in yr), 0), f(nb['rows'], 0),
                         f(100 * nb['rows'] / sum(x['rows'] for x in yr), 2),
                         f(100 * nb['exposure'] / sum(x['exposure'] for x in yr), 2)])
    business_table = table(['Año', 'Periodos', 'Nuevo negocio', '% filas NB', '% exposición NB'], business)
    support_table = table(['Ramo', 'NB largo 2024', 'Periodos positivos', 'NB largo 2025'],
                          [[x['line'], x['rows'], x['positive_periods'], x['future_rows']] for x in band_rows if x['year'] == 2024])
    cal = []
    for key, label in [('metrics', 'Nivel histórico, formas públicas fijas'),
                       ('common_public_overlay_metrics', 'Mismo nivel + overlay público recibido'),
                       ('no_public_extra_shape_metrics', 'Sin exponentes adicionales del público')]:
        mm = primary[key]['all']['models']
        cal.append([label] + [f(mm[n]['D2']) for n in ('constante', 'sin_factores', 'F3c_transferido')])
    calibration_table = table(['Cálculo 2024', 'Constante', 'Sin factores', 'Con factores'], cal)
    stage_table = table(['Paso', 'Autos NB 2024', 'Contenidos NB 2024', 'Autos NB traslado inverso'],
        [[s['variable'], f(s['evaluation']['motor_1']['delta_F3c_minus_sin_factores']),
          f(s['evaluation']['contents_1']['delta_F3c_minus_sin_factores']),
          f(inverse['factor_stages'][i]['evaluation']['motor_1']['delta_F3c_minus_sin_factores'])]
         for i, s in enumerate(primary['factor_stages'])])
    magnitude = []
    for v in ('gender', 'works_from_home', 'marketing_segment'):
        pa = read(run / 'DEV23_T2b_to_HOLD24_T2b_parameters.json')['own']
        pb = read(run / 'HOLD24_T2b_to_DEV23_T2b_parameters.json')['own']
        aa = next(s for s in pa if s['variable'] == v)
        bb = next(s for s in pb if s['variable'] == v)
        for key, value in aa['factors'].items():
            l, level = ast.literal_eval(key)
            value24 = bb['factors'].get(key)
            magnitude.append([v, l, level, f(value, 4), f(value24, 4),
                              'sí' if (value - 1) * (value24 - 1) < 0 else 'no'])
    magnitude_table = table(['Variable', 'Ramo', 'Nivel', 'Factor 2023', 'Factor 2024', 'Cruza 1'], magnitude)
    inf = []
    for s in primary['influence']['scenarios']:
        mm = s['models']
        inf.append([s['scenario']] + [f(mm[n]['D2']) for n in ('constante', 'sin_factores', 'F3c_transferido')] +
                   [f(mm['F3c_transferido']['D2'] - mm['sin_factores']['D2'])])
    influence_table = table(['Exclusión común', 'Constante', 'Sin factores', 'Con factores', 'Δ factores'], inf)
    report_rows = []
    for s in d['reporting_count_cost']:
        report_rows.append([s['line'], s['peril'], s['claims'], s['late_count'],
            f(s['severity_late_over_early'], 2) if s['severity_late_over_early'] is not None else 'sin tardíos',
            f(s['count_completion'], 3), f(s['cost_completion'], 3)])
    reporting_table = table(['Ramo', 'Peligro', 'Aceptados 2023', 'Tardíos', 'Sev. tardía/temprana', 'Completitud conteo', 'Completitud coste'], report_rows)
    comp = []
    for s in d['completion_stress']['scenarios']:
        comp.append([s['scenario'], f(s['mean_completion_te'], 4),
                     f(s['before_public']['all']['models']['F3c_transferido']['D2']),
                     f(s['after_frozen_public_overlay']['all']['models']['F3c_transferido']['D2']),
                     f(s['before_public']['all']['delta_F3c_minus_sin_factores'])])
    completion_table = table(['Escenario', 'Completitud media 2024', 'D² con factores antes', 'Después overlay fijo', 'Δ frente sin factores antes'], comp)
    selected = ('reserve075', 'reserve125', 'opposed_BI125_rest075', 'opposed_BI075_rest125', 'reserve_motor_bodily_injury_1.25')
    reserve = []
    for name in selected:
        s = next(x for x in d['scenarios'] if x['scenario'] == name)
        c = next(x for x in (price_summary if expense_corrected else d['commercial']['summary']) if x['model'] == 'F3c' and x['scenario'] == name)
        reserve.append([name, f(s['metrics_training_level_relearned']['all']['delta_F3c_minus_sin_factores']),
                        f(s['rank_correlation_annual_observed_rate']['F3c_transferido'], 6),
                        c['total'] if expense_corrected else c['total_rounded'],
                        f(100 * c['min_change_vs_F3c' if expense_corrected else 'min_change'], 2) + ' a ' + f(100 * c['max_change_vs_F3c' if expense_corrected else 'max_change'], 2)])
    reserve_table = table(['Escenario', 'Δ D²', 'Correlación rangos', 'Total 20 CU', 'Cambio individual %'], reserve)
    folds_table = table(['Año', 'Componentes', 'Componentes partidos', 'Direcciones partidas', 'Filas afectadas'],
                         [[x['year'], x['groups'], x['groups_across_customer_folds'], x['addresses_across_customer_folds'], x['rows_in_split_groups']] for x in audit['fold_audit']])
    risk_table = table(['Ramo', 'Filas combinaciones nuevas', '% exposición nueva', '% exposición con <30 filas históricas'],
                       [[x['line'], x['unseen_rows'], f(x['unseen_exposure_share'] * 100, 2), f(x['sparse_exposure_share'] * 100, 2)] for x in audit['combinations']])
    if expense_corrected:
        price_table = table(['Candidato guardado', '85 CU por póliza', '85 × exposición previo', 'Referencias con cambio ≥10% vs F3c'],
            [[x['model'], f(x['total'], 2), f(x['prior_total'], 2), x['references_material_vs_F3c']] for x in price_summary if x['scenario'] == 'nominal'])
    else:
        price_table = table(['Candidato guardado', 'Total veinte CU', 'Referencias con cambio ≥10% vs F3c'],
            [[x['model'], x['total_rounded'], x['material_refs_vs_F3c_10pct']] for x in d['commercial']['summary'] if x['scenario'] == 'nominal'])
    pdelta = primary['metrics']['all']['delta_F3c_minus_sin_factores']
    lower = primary['bootstrap']['intervals']['all']['delta_CI_family6'][0]
    entries = [
        ('01', 'Comparar F3c y sin factores', 'Ganancia condicional; promoción no acreditada',
         f'Δ={pdelta:.9f}; límite inferior={lower:.9f}; contraste ponderado2025 incierto. No es el aprendizaje completo del CSV F3c.',
         'Mantener final_creible como referencia de esta comparación. Conservar el titular A1 de la política v2, B00 y las alternativas; no promover F3c por este informe.'),
        ('02', 'Protección de negocio nuevo', 'Salvaguarda original fallida; incertidumbre abierta',
         'Original A1−R0: +0.013062, límite95 −0.010535 <−0.001; v2 humana quitó el veto del intervalo. Nueva evidencia NB no demuestra no inferioridad.',
         'No presentar falta de potencia o enmienda como aprobación estadística. Revisión de cohortes largas y datos adicionales antes de uso profesional.'),
        ('03', 'Modelo frente a sondas', 'Identificación parcial',
         'Constante y candidatos con igual calibración histórica y overlay común calculados. Sin sondas propias no existe calibración pública óptima de la constante.',
         'No atribuir a estructura toda la ganancia pública ni inferir privada a partir de la misma señal. No producir sondas nuevas para cerrar documentalmente.'),
        ('04', 'Estabilidad de factores', 'Falla estabilidad de contribución en autos NB',
         'Género aprendido2023 resta0.0028913 D² a autosNB2024 con nivel base fijo; traslado inverso suma0.0152718. Varios segmentos marketing cruzan1.',
         'No acreditar factores propios estables para autos NB; no escoger retrospectivamente solo los pasos favorables.'),
        ('05', 'Concentración', 'Fragilidad identificada, veto nominal pasa por poco',
         'Quitar37grupos favorables dejaΔ0.000004471; cien exclusiones aleatorias1% mantienen signo. Diagnóstico top es retrospectivo.',
         'Mantener referencia y mostrar concentración. No afirmar fragilidad mayor/menor que otra receta no comparada con los mismos escenarios.'),
        ('06', 'Conteos, coste y tardíos', 'Curvas separadas; último real sin identificar',
         'La curva usada por etiquetas.py pondera costes. Lesiones: severidad tardía/temprana1.6454; completitud conteo0.6053 frente coste0.4824.',
         'No usar una curva de coste como si acreditara frecuencia. Escenarios no establecen suficiencia ni absorción real de nuevas sondas.'),
        ('07', 'Reservas por componentes', 'Sensibilidad medida; suficiencia abierta',
         '45 escenarios comunes más5decompletitud; niveles por celda y veinte comerciales. Una valoración no demuestra suficiencia ni refit total de forma.',
         'Conservar tensiones por peligro y compensaciones; bloquear acreditación de reservas y uso comercial profesional sin revisión.'),
        ('08', 'Particiones de la cadena', 'No acredita cadena integral protegida',
         'Mezcla de peligros de ambos años, categorías transductivas y direcciones partidas; controles adversos propios pasan solo nuevos factores/niveles.',
         'No etiquetar resultados como prueba temporal íntegra. Nueva receta con limpieza/desarrollo/categorías/calibración dentro de cada ámbito antes de sostener esa afirmación.'),
        ('09', 'Exploración y confirmación', 'Clasificación e inventario cerrados por alcance',
         '500 documentos con menciones2024 en inventario de recuperación; v1,v2 y desarrollo abierto preservados. No inventario exhaustivo de cada consulta.',
         'Todos estos resultados siguen exploratorios y adaptativos. La corrección familia6 no borra selección previa.'),
        ('10', 'Disponibilidad y soporte', 'Disponibilidad no acreditada y soporte escaso',
         '142 perfiles de covariables, combinaciones por ramo, maestros sin fecha y límites de clima. Fallback explícito, sin cambiar precios guardados.',
         'Neutralizar factores propios si falta disponibilidad/admisibilidad; para riesgo base sin soporte, revisión con constante. No aprobar uso real con esta evidencia.'),
        ('11', 'Reproducción desde originales', 'Parcial, criterio integral incumplido',
         'Etiquetas cotejadas porfila; F3c/F3d exactos previos desde OOF; grafo fuente revisado. No reentrenamiento de todos los ancestros ni otro operador.',
         'Prohibir la afirmación de reproducción integral o independiente. Resolver grafo portable A1/T2b y ancestros FSp para F4c; acta real pendiente.'),
        ('12', 'Veinte primas', 'Cálculo y sensibilidad verificados; uso limitado',
         '2100 registros por lectura de gasto,20referencias por combinación y cinco candidatos. Gasto fijo corregido a85CUpor póliza según descripción oficial; prorrateo anterior preservado. Una referencia cambia≥10% al retirar factores con la lectura principal.',
         'Revisión individual antes de publicar/usar. Escenarios no son IC; beneficio8% no se presume margen de incertidumbre suficiente.')]
    ledger = {'id': 'CIERRE-12-F3C-20261026', 'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'review_completed': True, 'all_original_requirements_satisfied': False, 'formal_promotion': False,
        'comparison_reference': 'final_creible sin factores propios', 'formal_incumbent_policy_v2': 'A1, con receta exploratoria A1fixF1b3n',
        'F3c_status': 'public_research_candidate_preserved_not_promoted_by_this_review',
        'run': rel(run), 'audit_run': rel(audit_run),
        'sources': [{'path': rel(p), 'sha256': sha(p)} for p in [run / 'results.json', run / 'verification.json',
            run / 'independent_math_and_poison.json', audit_run / 'audit_results.json', REPO / 'registro/pendientes_F3c_plan.json',
            REPO / 'registro/semana2_politica_seleccion_v2_20261024.json',
            REPO / 'privado/semana2/claude_validacion_nocturna_20261023/rev5_resultados.json']],
        'items': [{'id': i, 'test': title, 'prior_criterion': read(REPO / 'registro/pendientes_F3c_plan.json')['acceptance'][i],
                   'status': status, 'result_and_limit': result, 'consequence': consequence}
                  for i, title, status, result, consequence in entries],
        'submissions': 0, 'manual_selection_changed': False, 'professional_independent_validation': False}
    if expense_corrected:
        ledger['sources'] += [{'path': rel(p), 'sha256': sha(p)} for p in [run / 'gasto_fijo_criterio_previo.json',
            run / 'gasto_por_poliza_verificacion.json', run / 'veinte_primas_gasto_por_poliza.json']]
        ledger['commercial_primary_basis'] = '85CUper_policy_not_prorated; prior interpretation preserved'
    retraining_index = REPO / 'registro/reentrenamiento_originales_actual.json'
    if retraining_index.exists():
        snapshot = run / 'reentrenamiento_status_snapshot.json'
        save(snapshot, {'consulted_utc': datetime.now(timezone.utc).isoformat(),
            'source': rel(retraining_index), 'source_sha256': sha(retraining_index), 'status': read(retraining_index)})
        ledger['sources'].append({'path': rel(snapshot), 'sha256': sha(snapshot)})
        ledger['parallel_retraining_at_review'] = read(retraining_index)['estado']
        item = next(x for x in ledger['items'] if x['id'] == '11')
        item['status'] = 'Reentrenamiento completo en curso; cierre numérico y otro operador pendientes'
        item['result_and_limit'] = 'Se localizó una ejecución concurrente desde originales, con planes, entorno aislado y restauraciones explícitas. No se duplica. El recibo final todavía no acredita el cierre de toda la cadena.'
    save(run / 'decision_ledger.json', ledger)
    summary_table = table(['N.º', 'Prueba', 'Resultado del cierre', 'Consecuencia'],
                          [[i, title, status, consequence] for i, title, status, result, consequence in entries])
    text = f'''# Doce pendientes de F3c: resultados, límites y decisiones

Codex, 26 de octubre de 2026, Bogotá. Revisión propia con código y cálculos locales. Las recetas originales y sus factores son de Claude; la nueva comparación, auditoría y verificación son de Codex. No es validación profesional independiente.

La revisión de los doce puntos terminó, pero los doce requisitos no quedaron aprobados. Hay una ganancia global condicional de los factores y resultados adversos que impiden promover F3c o acreditar su uso profesional. Se conserva final_creible sin factores como comparador sencillo, junto con todas las alternativas. La política humana v2 mantiene a A1 como titular común; este trabajo no revierte esa decisión ni cambia una selección en Kaggle.

## Alcance y criterio congelado

Se guardó el plan antes del cálculo nuevo y se comentó en el foro. Ya se habían leído las sensibilidades de Claude y los contrastes P19/P20/P26/P30/P32. Por ello congelar esta tanda no devuelve independencia a2024. La comparación evalúa una receta residual trasladada entre años, sobre las mismas filas, costesT0 y bases guardadas; no llama OOF al F3c de producción aprendido con ambos años.

El margen global es0,0005, con10.000bootstrap emparejados por componente conexa cliente-dirección y banda de familia6. Los intervalos fijan precios/modelos y condicionan los ancestros guardados: no incluyen incertidumbre de reentrenamiento fuente, selección adaptativa o suficiencia de reservas. Las sensibilidades no reciben una garantía simultánea sobre toda la búsqueda histórica. Se usan niveles aprendidos en entrenamiento. Los exponentes heredados de final_creible fueron elegidos con público2025 y se declaran; también se calcula una vista sin ellos.

{summary_table}

## Comparación directa sobre la misma base

{comparison_table}

Las tres primeras vistas comparten resultados2024 y no son tres pruebas independientes. El traslado2024a2023 estudia estabilidad inversa y no es un pronóstico. El primario mejora{f(pdelta)} y su límite inferior{f(lower)} supera por poco0,0005. Esa condición aislada pasa, con sus límites. La comparación reponderada por ramo,negocio y banda de exposición2025 da{f(primary['metrics_composition2025']['all']['delta_F3c_minus_sin_factores'])}, con IC95{interval(primary['bootstrap_composition2025']['intervals']['all']['delta_CI95'])}: sigue siendo incierta para la composición futura.

{seg_table}

En la celda autos/negocio nuevo la diferencia es{f(primary['metrics']['motor_1']['delta_F3c_minus_sin_factores'],9)}, apenas0,000003611 por debajo del piso adicional predeclarado de−0,001. Ese cruce es frágil por proximidad al umbral y no prueba daño poblacional; se conserva. El intervalo de negocio nuevo es compatible con pérdidas materiales. Las carencias de la cadena y la inestabilidad de su contribución impiden convertir la ganancia global en promoción.

## Protección original y representatividad del negocio nuevo

El control original A1contraR0 dio+0,013062 en la población nueva y límite95−0,010535, inferior al mínimo−0,001. Falló. La enmienda humana v2 del24deoctubre retiró el veto del intervalo y promovió A1 sin reabrir2024; se conserva esa decisión y su autoría. La potencia insuficiente describe incertidumbre, no aprobación de no inferioridad. Fuente: política v2 y rev5_resultados.json,t4_politica,paso1_A1_vs_R0. No confundir aquel contraste con el incremento F3ccontrafinal_creible de esta tanda, ni la marca new_business con un cliente totalmente nuevo para todos los ramos.

{business_table}

El soporte grueso por ramo/negocio2024 pasa el filtro descriptivo de100grupos efectivos y30grupos positivos; ese resultado no cubre la banda que domina2025. Los periodos con exposición≥0,9 muestran otra escala:

{support_table}

Edificios y contenidos solo aportan3y11periodos positivos en la banda larga de2024. Las proporciones futuras multiplican esa información escasa. Se conservan por año, ramo y negocio las exposiciones, tamaños efectivos de filas y componentes y grupos positivos en results.json/support. No se altera la partición para mejorar soporte. El corte por componentes estrictamente nuevos deja{primary['overlap']['cold_rows']}filas, frente a las9.063con marca contractualNB.

## Cuánto aporta la estructura y cuánto la lectura pública

{calibration_table}

La constante usa una tasa por ramo y negocio con la misma optimizaciónTweedie histórica y exposición efectiva. En la fila del overlay se aplica a los tres modelos el mismo multiplicador público guardado. Esto compara un procedimiento común de aplicación; no estima una calibración pública propia de la constante. Los momentos extraídos del tablero dependen de la predicción sondeada, por lo que no se transfieren como si identificaran el óptimo de otro vector. Esa parte del pendiente queda sin identificar y no se inventan sondas.

La lectura pública histórica real sigue separada: final_creible0,16519 y F3c0,16914, diferencia+0,00395. Comparte selección adaptativa y feedback del tablero; no es un privado observado. Reoptimizar en las etiquetas del mismo año prueba forma con nivel oráculo: en la vista ponderada2025 del primario el incremento pasa a{f(primary['oracle_same_evaluation_year_level']['all']['delta_F3c_minus_sin_factores'])}. Ese diagnóstico explica la tensión con B05 de Claude; no se mezcla con el pronóstico de nivel aprendido en entrenamiento.

## Estabilidad de género, teletrabajo y marketing

{stage_table}

Los incrementos de la tabla mantienen el nivel de la base fijo y aplican la secuencia completa, sin seleccionar pasos después. Género perjudica autosNB en2024 y ayuda en el traslado inverso; teletrabajo perjudica contenidosNB2024. Los factores de género mantienen su dirección agregada, pero su contribución fuera del año cambia. Varios niveles de marketing cruzan1. No corresponde afirmar estabilidad por una ganancia global ni retirar retrospectivamente un nivel para hacer pasar la prueba.

{magnitude_table}

Los parámetros privados guardan para cada nivel las filas, exposición y grupos positivos porNB/REN. Un factor cercano a1puede reflejar credibilidad escasa y no ausencia del efecto. La fórmula de n/(n+300) cuenta periodos con coste positivo, no todos los siniestros; se mantiene esa definición histórica y no se presenta como una estimación de frecuencia por siniestro.

## Concentración y perturbaciones comunes

{influence_table}

Las tres recetas reciben exactamente las mismas exclusiones. Retirar los37grupos favorables deja una ganancia de0,000004471: pasa el veto puntual≥0por un margen mínimo y pierde casi toda la mejora. Retirar grupos elegidos después del resultado es diagnóstico, no validación. En cambio, las100retiradas aleatorias predeclaradas de1%de componentes mantienen la diferencia positiva, entre{f(primary['influence']['random_1pct_100']['delta_min'])}y{f(primary['influence']['random_1pct_100']['delta_max'])}. La fragilidad depende del mecanismo de perturbación y se informa en ambos sentidos.

## Conteo, severidad tardía y objetivo de coste

etiquetas.py construye curvas ponderadas por incurrido neto, no curvas de conteos. No hay que reinterpretar esa curva como completitud de frecuencia. Se separaron ambas y se conservaron los ceros de los siniestros aceptados. La siguiente tabla compara los ocurridos en2023reportados hasta la valoración2024; tardío significa reportado después del31dediciembre2023.

{reporting_table}

Lesiones corporales tiene severidad tardía1,645veces la temprana y completitud de coste0,482frente a0,605de conteo. La misma fracción de avisos no implica la misma fracción de coste. Estas severidades son incurridas a una sola valoración; los abiertos aún pueden cambiar y los todavía no reportados no se observan.

{completion_table}

Las mezclas por peligro de estos escenarios se calculan solo en entrenamiento2023; se conservan los árboles y la estructura de los precios. Se cambia la severidad de la porción no reportada a0,5,1,5y2veces y se compara conteo/coste, con y sin overlay público congelado. El overlay fijo no simula una nueva recalibración del marcador, de modo que su diferencia no mide cuánto absorberían realmente nuevas sondas.

La acotación anterior de Claude (src/semana2/lineas/reservas_20261026/INFORME.md) mantiene un resultado adverso de lesiones:1,427veces el coste tardío previsto, IC90[1,021;2,021]. Su estimador extrapola desde el coste temprano mediante completitudes integradas por exposición; el de reporting_count_cost condiciona en cada siniestro/coste observado hasta2024. Los denominadores difieren. No se reemplaza aquella alarma con este contraste ni se lee uno como réplica del otro. FSp usa una exposición de frecuencia que debe revisarse por separado si su completitud procede de coste; F3c no incorpora FSp y F4c conserva ese requisito.

## Reservas por ramo y peligro, orden y compensaciones

Se calcularon45escenarios de respuesta con reservas0,75/1,25agregadas, por cada ramo y cada uno de15peligros, dos tensiones opuestas de lesiones/resto, severidad de tardíos observados y colas de lesiones/hundimiento. Se añaden5escenarios de completitud. Los tres modelos reciben el mismo escenario. Se miden precios congelados con objetivo estresado y niveles reaprendidos solo en2023, además del overlay público fijo. No es un refit de todos los árboles o factores de forma bajo cada valoración.

{reserve_table}

Lesiones concentra2.447.770,73CUde reserva en los periodos enlazados. Los cambios opuestos producen compensaciones entre componentes que no se ven en un único total. Las correlaciones de rangos son altas porque aquí cambia el nivel por celda, no las relatividades dentro de ella; no acreditan estabilidad de un reentrenamiento completo. Los veinte precios con reserva±25%cambian hasta4,43%individualmente. Los escenarios de severidad son más amplios y están identificados como tensiones, sin probabilidad asignada. La suficiencia real permanece abierta con una valoración.

## Auditoría de la cadena y dependencias

Se reconstruyóT0con los siniestros originales y se cotejaron todas las109.296filas históricas con la base recibida, con error inferior a1e−8CU; suma27.997.991,57CU. Test conserva y nulo. Los36siniestros sin periodo se preservan aparte:34anteriores a2023y dos de2023,92.267,26CUnetos en conjunto. No se reasignaron claves ni se alteró la base para este contraste.

{folds_table}

Los folds originales usan hash de cliente. Construir componentes cliente-dirección para el bootstrap no repara que el aprendizaje previo separase direcciones compartidas. El inventario estático también muestra: pesos de peligro de c_fila calculados con ambos años destino; diccionario de categorías construido con covariables fuente y destino completas; factores F2/F3c de producción aprendidos con2023+2024; y razones de nivel evaluadas sobre pools usados para aprenderlos. La unión de categorías no usa etiquetas, pero es transductiva y no cumple una exigencia estricta de transformación aprendida solo en entrenamiento.

La nueva capa de factores y nivel sí pasó el control adverso: alterar completamente y retenido deja exactamente iguales parámetros aprendidos y precios, en los dos sentidos de traslado. Se reprodujeron también las primeras multiplicidades archivadas por otro cálculo fila a fila para los tres modelos y seis segmentos. Son comprobaciones propias. No cubren el reaprendizaje de ancestrosT2b/A1, limpieza, completitud o selección de variables. El replay fuente de producción hasta2024no certifica automáticamente los objetos dev/hold cuyo código declara cortes hasta2023.

## Exploración, disponibilidad y soporte futuro

El inventario congelado de recuperación contiene500documentos de registro y semana2con menciones a2024. Guarda rutas, número de menciones ySHA; no pretende reconstruir cada lectura o decisión no registrada. La política v1, su fallo, la enmienda v2 y la autorización de desarrollo2024del25deoctubre se conservan. Todas las cifras nuevas siguen siendo exploratorias. Bonferroni de esta familia no corrige retrospectivamente el proceso que eligió sus variables o el uso del público.

Se revisaron142perfiles de covariables. Las mayores alertas dePSI corresponden a exposición (2,43autos,2,15edificios,2,69contenidos), coherentes con la sustitución de cartera corta por negocio nuevo de año completo. Son indicadores descriptivos sensibles a las bandas, no umbrales de validez actuarial.

{risk_table}

Las combinaciones fijadas usan negocio,canal,año completo y dos campos del ramo. Con cinco campos se dispersan los históricos; estos porcentajes no prueban por sí solos que cada riesgo carezca de información. Sí identifican dónde falta evidencia cercana. Los maestros de cliente y dirección no tienen vigencia histórica por atributo; que género o marketing existan en la tabla no prueba que fueran conocidos al cotizar. El archivo de clima2025tampoco acredita conocimiento prospectivo.

La regla de contingencia queda escrita en el registro de uso: clave propia no vista recibe factor1; si no se acredita disponibilidad/admisibilidad de los atributos propios, se neutraliza el bloque entero y su razón de nivel, recuperando final_creible. Si el riesgo base está fuera de soporte, se compara con constante por ramo/negocio y se exige revisión; no hay tarifa real aprobada automáticamente. La disponibilidad de variables de la base también sigue pendiente. El permiso del mercado sintético no se traslada como dictamen jurídico a una jurisdicción real.

## Reproducción: lo realizado y lo que sigue abierto

Se reutiliza la evidencia ya verificada del entorno limpio Python3.12.14: etiquetas desde originales y factoresF3c/F3d reaprendidos sobre OOF guardadas, ambosCSVidénticos porSHA. Esta tanda agrega cotejo porfila de las etiquetas. No se repitió aquel ensayo por una corrección documental ni se llamó reproducción integral a reconstruir desde OOF.

La auditoría guarda un grafo de nueve nodos. Se localizaron las fasesT2bdev/hold/pcv/prod y sus semillas, preparación,historia y variables. A1decontraste y A1fixF1b3n deproducción tienen recetas distintas; el segundo requiere sus promedios de semillas11/12/13, historia neutral, modelos y ensamblado exactos. El grafo portable de todos esos ancestros no está cerrado ni ejecutado desde cero. F4c necesita además sus tablasFSporiginales exactas. No corresponde iniciar un entrenamiento parecido y llamarlo reproducción fiel.

La reproducción por otra persona tampoco se realizó. La plantilla de acta disponible no es una firma. La consecuencia es impedir las afirmaciones de reproducción integral e independiente hasta disponer del grafo ejecutable cerrado, entorno y versiones fuente exactas, semillas, comandos, salidas cotejadas y un operador real distinto cuando proceda. Es un requisito no cumplido, no una tarea declarada terminada por acumulación de comprobaciones parciales.

## Las veinte primas comerciales

{price_table}

Hay2.100registros verificados, con20referencias en cada combinación de candidato y escenario. F3c suma20.304,23CUtras redondear cada fila; la suma sin redondear es20.304,200792CUy su redondeo sería20.304,20CU. final_creible suma19.481,61CUy modifica dos referencias más del10%. F3d/F4c se muestran como sensibilidades guardadas, sin admisión; sus totales parecidos no acreditan equivalencia.

Para cada referencia se comprobó exposición oficial, calendario, denominador, comisión y ambas identidadesDecimal/float. La primaP=(R·(1+cat)+85·e)/(1−0,15−comisión−0,08−0,08), concat=0,12solo en hogar y comisión0directo/0,20broker. Responde al supuesto de gasto fijo anual prorrateado por exposición del contrato del ejercicio. Rya es coste del periodo. La comisión de comparison_site no está informada para el emergente; ninguna de las20referencias utiliza ese canal y no se inventó una tasa.

El archivo privado VEINTE_PRIMAS_COMPARADAS.md identifica cada referencia, su diferencia y los extremos con su causa. Los escenarios de reserva/completitud transfieren razones de nivel histórico por celda a precios de producción congelados; no son primas de un reentrenamiento integral ni intervalos individuales. Duplicar la severidad de tardíos observados eleva hasta24,96%una comercial y el total21,25%, mientras reserva±25%mueve menos. El margen de beneficio8%es una entrada del ejercicio y no se da por suficiente para ese riesgo.

## Archivos, verificación y consecuencia operativa

El plan es registro/pendientes_F3c_plan.json. El cálculo, sus parámetros y precios porfila, los cinco archivos de bootstrap y las veinte comerciales están en `{rel(run)}`. La auditoría está en `{rel(audit_run)}`. La matriz estructurada guarda criterio previo, resultado, limitación y consecuencia para cada punto; el registro público no incluye primas ni identificadores porfila.

Dos fallos de implementación se conservaron: exigencia incorrecta de enlace total y precisión de exposición demasiado estricta. El segundo ocurrió después de guardar precios/parámetros y los intervalos; la recuperación reutiliza esos archivos porSHA, sin nuevas remuestras ni elección de semilla. Recalcula los niveles escalares de escenarios perdidos antes de persistir, con las mismas reglas. El comprobador posterior pasa16controles y otro cálculo reproduce multiplicidades y controles adversos; sigue siendo verificación propia.

No se entrena un nuevo árbol fuente,C0, hace una sonda,envía,promueve,retira una alternativa o cambia una selección manual. Se registra un bloqueo de admisión para las afirmaciones/uso que no satisfacen los criterios, con su evidencia de liberación. El informe anterior de sensibilidad de Claude y sus conclusiones quedan como corte histórico; esta revisión limita lo que puede afirmarse hoy sin atribuirle aprobación de otra persona. Prácticas aplicadas: IAAConsideraciones profesionales§§3.1,3.3,3.5–3.8;Gobernanza§2.8y§§3.4–3.6;Documentación§§2–6, como guías educativas del proyecto.
'''
    if expense_corrected:
        begin = text.index('Hay2.100registros verificados')
        end = text.index('\n## Archivos, verificación y consecuencia operativa', begin)
        base_f3c = next(x for x in price_summary if x['model'] == 'F3c' and x['scenario'] == 'nominal')
        base_simple = next(x for x in price_summary if x['model'] == 'sin_factores_final_creible' and x['scenario'] == 'nominal')
        material_cost = sum(x['model'] == 'F3c' and x['scenario'] == 'nominal' and x['increase_over_proration_pct'] >= .1 for x in commercial)
        worst = max(x['increase_over_proration_pct'] for x in commercial if x['model'] == 'F3c' and x['scenario'] == 'nominal') * 100
        nominal_total = Decimal(base_f3c['unrounded_total'])
        corrected = f'''Se verificaron 2.100 registros para cada lectura de gasto, 4.200 en total, con veinte referencias en cada combinación de candidato y escenario. La revisión directa de la descripción oficial detectó una diferencia respecto al informe anterior: el concepto se denomina «fixed expense per policy», unidad CU. No consta que sea un gasto anual. La lectura principal de esta revisión cobra 85 CU por póliza de referencia y conserva el prorrateo 85×exposición como hipótesis alternativa. Las veinte referencias tienen policy_id distintos; no se está cobrando dos veces a una póliza repetida dentro de esta lista.

Con la lectura por póliza, F3c suma {f(base_f3c['total'],2)} CU de comerciales redondeadas y {f(nominal_total,6)} CU sin redondear; redondear esa suma da {f(nominal_total,2)} CU. La lectura prorrateada anterior suma {f(base_f3c['prior_total'],2)} CU. La diferencia agregada no revela el impacto en los periodos cortos: {material_cost} referencias suben al menos 10% por esta sola interpretación de gasto y el máximo es {f(worst,2)}%. No cambia su prima de riesgo, exposición, comisión o modelo.

La referencia sin factores suma {f(base_simple['total'],2)} CU y una comercial cambia al menos 10% frente a F3c. Bajo el prorrateo previo eran dos. Se conservan ambas lecturas para que la convención de gasto no oculte incertidumbre del modelo. F3d y F4c siguen siendo sensibilidades guardadas, sin admisión; un total parecido no demuestra equivalencia.

La fórmula principal es `P = (R × (1 + cat) + 85) / (1 − 0,15 − comisión − 0,08 − 0,08)`. Catástrofes añade 0,12 de la prima de riesgo solo en hogar; la comisión es 0 para directo y 0,20 para broker. R ya corresponde al periodo y no se vuelve a multiplicar por exposición. Para comparar tasas anuales se divide R por exposición por separado. La comisión comparison_site está vacía para el emergente; ninguna de las veinte referencias usa ese canal y no se inventó una tasa.

Ambas lecturas pasan dos fórmulas Decimal, identidad de cargas y cotejo float. El cambio exacto de prima por corregir el gasto es `85 × (1 − exposición) / denominador`; se comprobó en las 2.100 filas. El supuesto de gasto debe declararse en la entrega: el archivo oficial no identifica cómo repartir un gasto de adquisición entre varios subperiodos de una misma póliza fuera de estas veinte referencias. La frase anterior que atribuía el prorrateo al contrato queda corregida por esta consulta directa.

El archivo privado VEINTE_PRIMAS_GASTO_POR_POLIZA.md identifica cada referencia, diferencia nominal y rango de escenarios. VEINTE_PRIMAS_COMPARADAS.md conserva el cálculo prorrateado anterior. Las reservas/completitudes se propagan mediante razones de nivel histórico por celda a precios guardados; no son un refit integral ni intervalos individuales. Los escenarios y el margen de beneficio del 8% se mantienen separados: ese margen es una entrada del ejercicio, no prueba que cubra incertidumbre.
'''
        text = text[:begin] + corrected + text[end:]
    if retraining_index.exists():
        text += '''\n## Actualización de reproducción al cerrar esta revisión\n\nEl estado común posterior a la auditoría registra un reentrenamiento completo ya iniciado en otro chat del participante, «Revisar pendientes del proyecto IAA». No se duplica esa ejecución ni se le atribuye a esta batería. El grafo de T2b/A1/M017/FSp está implementado en `herramientas/completar_reentrenamiento_cadena.py`, con guía `docs/REENTRENAMIENTO_ORIGINALES.md`, entorno nuevo y controles de aislamiento. La consulta de cierre lo encuentra en ejecución local: T2b completado, A1 en progreso, sin recibo final de todos los CSV. Dos restauraciones de código histórico están declaradas y requieren cotejo. Esto supera el diagnóstico inicial de grafo portable sin cerrar, pero aún no demuestra igualdad final de toda la cadena ni reproducción por otra persona. Se conserva el snapshot fechado en privado y el requisito11no se da por aprobado.\n'''
    text += '''\nLa puerta `herramientas/puerta_uso_F3c.py` verifica las huellas de este expediente y solo permite `research_review`. Rechaza promoción, cotización profesional, afirmación de reproducción integral y nuevo envío con código de salida3. Se conservan los recibos del ensayo de las cinco finalidades. Es una consecuencia operativa para esta línea; no reemplaza autorizaciones humanas históricas ni es una barrera contra un operador que reescriba el código. El informe conjunto anterior conserva su corte; sus cifras comerciales prorrateadas no se deben presentar como la lectura principal de esta revisión. Su integración editorial queda identificada antes de otra entrega.\n'''
    # Espacios en torno a tokens históricos compactos no se corrigen por sustituciones numéricas.
    doc = REPO / 'docs/semana2/CIERRE_DOCE_PENDIENTES_F3C.md'
    doc.write_text(natural(text), encoding='utf-8')
    index = {'id': ledger['id'], 'author': 'Codex', 'utc': ledger['utc'],
        'report': rel(doc), 'report_sha256': sha(doc), 'run': rel(run), 'audit_run': rel(audit_run),
        'ledger': rel(run / 'decision_ledger.json'), 'ledger_sha256': sha(run / 'decision_ledger.json'),
        'review_completed': True, 'all_original_requirements_satisfied': False,
        'formal_promotion': False, 'submissions': 0, 'references_private': True,
        'primary_delta': pdelta, 'primary_conditional_family6_CI': primary['bootstrap']['intervals']['all']['delta_CI_family6'],
        'future_composition_CI95': primary['bootstrap_composition2025']['intervals']['all']['delta_CI95'],
        'hard_limits': ['whole_chain_scope_not_verified', 'original_NB_safeguard_failed',
            '2024_adaptive', 'quote_availability_unverified', 'full_retraining_and_other_operator_pending'],
        'release_requires': 'Evidencia nueva que cierre cada condición; no basta reconocerla o mejorar público.'}
    if expense_corrected:
        index.update({'commercial_primary_basis': 'fixed85_per_policy', 'F3c_commercial_total_CU': '20800.02',
            'prior_prorated_total_CU': '20304.23', 'joint_PDF_expense_correction_integration_pending': True,
            'retraining_status_at_review': read(retraining_index)['estado'] if retraining_index.exists() else 'not_verified'})
    save(REPO / 'registro/pendientes_F3c_actual.json', index)
    save(REPO / 'registro/F3c_limites_de_uso.json', {'id': 'F3C-USO-20261026', 'author': 'Codex',
        'review': rel(REPO / 'registro/pendientes_F3c_actual.json'), 'formal_promotion_allowed_by_this_review': False,
        'professional_pricing_approved': False, 'F3c_public_research_artifact_preserved': True,
        'human_v2_incumbent_unchanged': True, 'fallback': audit['fallback'],
        'not_a_new_competition_submission_or_replacement_csv': True,
        'required_evidence_before_releasing_limits': [x['consequence'] for x in ledger['items']]})
    print({'report': rel(doc), 'items': len(entries), 'commercial_references': len(refs), 'primary_delta': pdelta})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--audit-run', type=Path, required=True)
    a = p.parse_args()
    main(a.run.resolve(), a.audit_run.resolve())
