"""Registra entradas conciliadas y reutilización de RKM, sin admitir un modelo de precio."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'recuentos_fuente2024_v1'
REUSE = BASE / 'recuentos_fuente2024_rkm_reuse_v1'; P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    report = w.read(OUT / 'report.json'); validation = w.read(OUT / 'validation_v1/report.json'); reuse = w.read(REUSE / 'report.json')
    assert report['rows'] == 2409311 and len(validation['checks']) == len(reuse['checks']) == 15
    assert reuse['count_likelihood_input_positivity_pass'] and reuse['paired_mark_link_support_pass']
    assert report['new_empirical_source_count_CDF_fits'] == 15 and reuse['new_reporting_fits'] == 0
    phase = w.read(P); assert phase['new_price_fits'] == 60 and phase['new_C0_fits'] == 105
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = (
        'Preparar y preinscribir una corrección meteorológica de frecuencia con Poisson GLM por peril físico, conservando el riesgo C1/F2 como base. '
        'La necesidad documentada es reducir el ruido de importes que no permitió una señal estable en W7, no repetir FS/FSp completo. '
        'Usar todos los periodos fuente2021–2024 y E_count_RKM ya reutilizado; no estimar otro C0. '
        'El factor transferido debe comparar clima anual con clima histórico de la misma dirección y solo trasladar diferencias de frecuencia, no efectos estáticos nuevos ni valores de crédito inventados para el emergente. '
        'Los controles de región/año/riesgo base y posibles covariables fuente exclusivas serían nuisance que no se trasladan; fijar su contrato y tratamiento antes del ajuste. '
        'Reutilizar los offsets fuente T2b guardados en W7 si su identidad y filas coinciden; no repetir inferencias históricas por falta de búsqueda. '
        'Los pesos por peril en destino deben provenir de los objetos C0 ya congelados de entrenamiento de cada fold, excluyendo al retenido. '
        'Antes de cualquier fit/score: código, mapa físico de perils/variables, regularización, presupuesto, comparador y criterio congelados y foro previo. '
        'Conservar el fallo de soporte de la ponderación2025 y los límites de cola; no usar ese diagnóstico para rescatar modelos adversos. '
        'No gastar el último cupo ni producir un CSV2025 sin evidencia sustancial y admisión separada. B00, F2, C1 y alternativas se conservan;2024 abierto como desarrollo y meta0.17 aún no lograda.')
    note = '\n\n## Frecuencia por peril: entradas fuente conciliadas, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se prepararon 2.409.311 periodos desarrollados de 2021–2024 y sus recuentos por peril, sin ajustar un precio. '
        'Los 160.432 siniestros aceptados asignados concilian con cada céntimo de T0 de la fuente congelada. Se conserva un siniestro aceptado de importe neto cero. '
        'Los 604 clones duplicados siguen la regla histórica exacta; todos los demás siniestros quedan en una partición completa y disjunta de asignados y no asignados. '
        'Los 413 no asignados, incluidos los anteriores a cobertura, se conservan y no se adjudican a pólizas inventadas.\n\n'
        'FS/FSp histórico usa completitud ponderada por coste en la frecuencia y un coste medio observado. Eso no identifica directamente una frecuencia última, '
        'pero su producto puede seguir siendo coherente con el coste. Por tanto, no se declara defectuoso todo el modelo anterior a partir del nombre del componente. '
        'Para separar número y marca, E_N es exposición de reporte de número, E_C la de coste y el multiplicador de marca es E_C/E_N. '
        'El producto lambda × E_N × mu × E_C/E_N vuelve a lambda × mu × E_C; cambiar solo frecuencia y dejar la marca observada sin ese ajuste rompe la interpretación separada.\n\n'
        'Se reconstruyeron 15 CDF empíricas de número con la misma cohorte madura y soporte de 1.095 días que las CDF de coste de la fuente. '
        'Son estimaciones de observación fuente, no modelos de precio ni C0 emergente. El contraste detectó seis siniestros maduros de lesiones corporales con reportes posteriores a 1.095 días, '
        'máximo 1.361 días e incurrido neto observado de 141.238,52 CU. La versión empírica condicionada a 1.095 días se conserva como alternativa; '
        'no se presenta como identificación de toda la cola última.\n\n'
        'La búsqueda de objetos existentes encontró las 15 curvas RKM fuente de la primera tanda, con ocurrencias asignadas 2021–2023 y valoración al 31 de diciembre de 2024. '
        'Se cotejaron su número de siniestros, soporte, eventos y conjuntos de riesgo con la asignación actual y se reprodujo la CDF congelada mediante otro producto acumulado. '
        'Esos objetos ya incluyen el soporte de 1.361 días de lesiones corporales y se reutilizaron sin ajustar otra curva. '
        'La cola posterior a su máximo observado sigue sin identificarse. Las curvas de coste de F2 no se sustituyeron por las RKM; se conservan los dos vínculos explícitos.\n\n'
        'Las exposiciones y el multiplicador de marca se guardaron para cada periodo/peril. No hay recuentos positivos con exposición de número nula ni costes positivos bajo exposición de coste nula. '
        'Tampoco aparece soporte de coste positivo con soporte RKM de número nulo. Se conserva todo el tiempo de póliza; no se impusieron ceros estructurales de cobertura. '
        'En lesiones corporales de 2024, la exposición empírica de número supera la de coste aproximadamente un 3,01 %. Es una diferencia de denominadores, no una mejora predictiva medida.\n\n'
        'La lectura de vuelta confirmó filas, claves, importes y partición de siniestros. Recuentos e importes se verificaron por acumulación de índices además de agregación tabular; '
        'la integración de calendarios se cotejó con masas de probabilidad de retraso y la identidad número/marca/coste se verificó numéricamente. '
        'Cero ajustes de precio, constantes de precio, inferencias de precios, scores o envíos. Coste de observación real: 15 CDF empíricas de número fuente; '
        'cero CDF de coste nuevas, cero C0 emergente y cero refits RKM. Se contabilizan explícitamente aunque no sean ajustes de precio.\n\n'
        'Las entradas quedan preparadas para registrar una prueba Poisson estándar; no se admite todavía un candidato ni se afirma ganancia en 2025. '
        'El objetivo es condicional a los datos oficiales, 2024 es desarrollo adaptativo y la revisión propia no constituye aprobación humana ni revisión profesional independiente. '
        'El mejor recibo verificado continúa en 0,16519; el último cupo no se usó. B00, F2, C1, todos los modelos y las alternativas de observación permanecen.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '; ' + w.rel(REUSE / 'report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/semana2/RECUENTOS_FUENTE2024_Y_VINCULO_NUMERO_MARCA.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-RECUENTOS-FUENTE-RESULTADO', '--asunto',
        'Recuentos fuente conciliados y RKM reutilizado; número y marca preparados, sin precios nuevos', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'inputs_reconciled_for_future_preregistered_trial_not_model_admission',
        'source_rows': report['rows'], 'accepted_assigned_claims': sum(x['accepted_assigned_claims'] for x in report['checks']),
        'count_inputs': {'path': w.rel(OUT / 'report.json'), 'sha256': w.sha(OUT / 'report.json')},
        'validation': {'path': w.rel(OUT / 'validation_v1/report.json'), 'sha256': w.sha(OUT / 'validation_v1/report.json')},
        'RKM_reuse': {'path': w.rel(REUSE / 'report.json'), 'sha256': w.sha(REUSE / 'report.json')},
        'new_source_empirical_count_CDF_fits': 15, 'new_source_cost_CDF_fits': 0, 'new_target_C0_fits': 0,
        'new_price_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'observed_tail_preserved': validation['observed_tail'],
        'full_ultimate_tail_not_identified': True, 'forum': json.loads(p.stdout)}
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; count = w.read(counters)
    assert 'phase2_source_counts2024_preparation' not in count
    w.update(counters, {'as_of_utc': stamp.isoformat(),
        'supplementary_reporting_peril_fits_since_counter_start': count['supplementary_reporting_peril_fits_since_counter_start'] + 15,
        'phase2_source_counts2024_preparation': {'new_source_count_CDFs': 15, 'source_RKM_refits': 0,
            'new_source_cost_CDFs': 0, 'new_target_C0_fits': 0, 'new_price_fits': 0, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'source_count_mark_input_preparation': summary,
        'new_C0_fits': phase['new_C0_fits'] + 15, 'new_source_C0_fits': phase['new_source_C0_fits'] + 15,
        'new_source_count_CDF_fits': phase.get('new_source_count_CDF_fits', 0) + 15,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit, 'status': 'active',
        '2024_open': True, '2024_closed': False, 'goal_achieved': False,
        'previous_goal_turn_audit': {'classification': 'progress', 'evidence': 'Official2025weather scope/data verified and W7 completed with six source GLM, validation and preserved adverses; no submission.'}}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(source_count_mark_input_preparation=summary, next_unit=next_unit, active_jobs=[], status='active', goal_achieved=False)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_source_count_inputs': summary['count_inputs']['path'],
        'week_2_mission017_source_count_RKM_reuse': summary['RKM_reuse']['path'],
        'week_2_mission017_source_count_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'source_rows_ready': report['rows'], 'accepted_assigned_claims': summary['accepted_assigned_claims'],
        'new_source_count_CDFs': 15, 'new_RKM_fits': 0, 'phase_C0_fits': phase['new_C0_fits'] + 15,
        'phase_price_fits_unchanged': phase['new_price_fits'], 'new_submissions': 0, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__':
    main()
