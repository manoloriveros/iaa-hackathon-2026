"""Conserva los escenarios de reservas/cola, el fallo previo y sus límites."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'sensibilidad_observacion_PUL2_20261026_v2'
sp = importlib.util.spec_from_file_location('observation_closure', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); quota = w.read(OUT/'quota_readonly.json')
    assert len(report['numeric_controls']) == 15 and len(report['results']) == 6
    assert report['new_model_fits'] == report['new_C0_fits'] == 0
    stamp = datetime.now(timezone.utc)
    archive = OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ'); archive.mkdir(parents=True)
    next_unit = ('Register one finite standard H1-only transfer ablation against the existing PUL2 operator: '
                 'same source-safe S0/S1/S2 bases and conditional originalA1 proxy, cached own-fold H1/G3 only, '
                 'no new fit/inference/C0 or REN FSp shape. Motivation: H1 alone retained positive post31 while PUL2 did not. '
                 'Evaluate source-safe direction, paired groups, concentration and cells; reuse completed PUL2 results rather than rerunning. '
                 'Do not tune a weight/level or claim a complete F3c replay. Check whether this simpler correction addresses the specific concentration failure. '
                 'Quota read26Oct10:32UTC=0; no upload from either prototype.2024open adaptive, B00/F3c0.16914 and alternatives preserved.')
    receipt = {'author':'Codex','utc':stamp.isoformat(),'status':report['status'],
               'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
               'plan':'Hackaton/Repositorio_IAA2026/registro/semana2_sensibilidad_observacion_PUL2_plan_v2.json',
               'previous_failure':w.rel(BASE/'sensibilidad_observacion_PUL2_20261026_v1/failure_receipt.json'),
               'new_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
               'scenario_prices':1311552,'new_final_test_prices':0,'new_CSVs':0,'new_submissions':0,
               'all_scenario_point_and_lower95_positive':True,'post31_negative_all_six':True,
               'full_pipeline_revaluation_not_established':True,'submission_allowed':False,
               'quota_readonly':quota,'2024_open':True,'B00_all_alternatives_preserved':True,
               'goal_achieved':False,'next_unit':next_unit}
    note = '\n\n## PUL2: reservas y reportes tardíos, 26 de octubre de 2026\n\n'
    note += ('Codex, '+stamp.isoformat()+'. Se completaron los seis escenarios registrados sobre las mismas 109.296 filas retenidas de 2023 y 2024, '
             'con precios, estructuras, perfiles y curvas ya guardados. Cero ajustes de modelos, C0, recalibraciones o inferencias fuente. '
             'La versión inicial se detuvo antes de producir escenarios por exigir identidad entre exposición de calendario y redondeada. '
             'Se conservó el código y el fallo; V2 comprueba exposure_model y round(calendar,4), sin cambiar el denominador histórico ni las fórmulas.\n\n')
    note += '| Escenario | Diferencia D² frente a G3 | IC95 por grupos | Después de retirar 31 grupos favorables | Peor celda D² |\n|---|---:|---:|---:|---:|\n'
    for name, a in report['results'].items():
        worst = min(z['delta_cell_null'] for z in a['cells'])
        note += f'| {name} | {a["delta"]:+.8f} | [{a["bootstrap95"][0]:+.8f}, {a["bootstrap95"][1]:+.8f}] | {a["post31_delta"]:+.8f} | {worst:+.8f} |\n'
    note += ('\nC corresponde a cambiar la completitud con tasas agregadas fijas; V añade la revaloración analítica de marcas por peril. '
             'R075/R125 usan las respuestas oficiales con reservas al 75%/125%. TAIL005/010 conserva T0 y desplaza hipotéticamente un 5%/10% de masa '
             'más allá del soporte observado solo en lesión corporal y subsidencia, según el contrato previo. Ninguna variante identifica los siniestros desconocidos. '
             'No son ajustes completos del modelo ni una prueba de suficiencia de reservas.\n\n'
             'Los seis incrementos son positivos en ambos años y los cinco folds. Los límites inferiores simultáneos exploratorios de los seis escenarios también son positivos. '
             'La concentración persiste en todos: post31 es negativo. La revaloración al 75% empeora autos nuevos de 2023 en -0,00490388; '
             'la cola del 10% empeora esa misma celda en -0,00426495. No se escogerá un escenario favorable para el CSV, se eliminarán grupos o se cambiarán los criterios.\n\n')
    note += ('Quince ámbitos verificaron ancestros/grupos, la identidad del enlace base, simetría lineal de reservas e integración diaria por un método escalar independiente. '
             'El máximo error absoluto de integración fue '+str(max(x['max_direct_daily_integration_abs_error'] for x in report['numeric_controls']))+'. '
             'Se aceptan ceros legítimos por peril sin suelo artificial. Los SHA de las fuentes permanecieron iguales; estos recibos cubren únicamente el código registrado.\n\n'
             'La consulta de cupos del 26 de octubre a las 10:32 UTC devolvió 10 envíos del día, 22 acumulados y cero disponibles ahora; no es un límite total. '
             'El primer intento de lectura falló por DNS dentro del entorno restringido; la lectura posterior autorizada tuvo respuesta. No se envió archivo ni se consultó score privado.\n\n'
             'La instrucción directa vigente del participante abre 2024 para desarrollo, análisis, ajustes y validación. Sustituye el cierre histórico, incluso si el texto antiguo '
             'del objetivo automático todavía lo menciona. Los resultados de 2024 son adaptativos y no constituyen confirmación intacta. '
             'B00, F3c procesado con 0,16914 y todas las alternativas, prototipos y versiones fallidas se conservan. El objetivo público de 0,17 sigue activo y no se ha logrado.\n\n'
             'Siguiente unidad: aislar la corrección H1 en las bases ya guardadas, sin la forma FSp de renovaciones. H1 pasó el control post31 local y PUL2 no; '
             'esa diferencia concreta justifica comprobar si una corrección más simple transfiere mejor. Se registrará antes de puntuar, sin entrenar ni repetir la tanda PUL2. '
             'Permanecen la falta de replay completo de F3c y de validación anidada del ensemble final, además del soporte insuficiente de la sensibilidad ponderada.\n\n'
             'Evidencia: '+w.rel(OUT/'report.json')+'.\n')
    doc = R/'docs/semana2/MISION017_PUL2_RESERVAS_REPORTES.md'
    assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, note, archive)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL2-OBS-STRESS-RESULTADO',
        '--asunto','PUL2: escenarios positivos, persisten concentración y deterioros en autos nuevos',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    index = R/'registro/semana2_sensibilidad_observacion_PUL2_actual.json'
    assert not index.exists(); index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    phase = R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'PUL2_observation_stress':receipt,'next_unit':next_unit,
                   'last_quota':quota['limits'],'last_quota_read':quota,'active_execution':None,'active_jobs':[]},archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'
    own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(PUL2_observation_stress=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False,
               last_quota=quota['limits'],explicit_2024_scope='Open by direct participant instruction; adaptive development, no pristine holdout claim')
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_PUL2_observation_stress_index':w.rel(index),
                                      'week_2_mission017_PUL2_observation_stress_report':w.rel(doc)},archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'new_fits':0,'new_submissions':0,'2024_open':True,
                      'quota':quota['limits'],'forum':receipt['forum']}))


if __name__ == '__main__':
    main()
