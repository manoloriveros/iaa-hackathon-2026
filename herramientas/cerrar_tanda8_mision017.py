"""Registra el resultado adverso de Poisson climático y conserva el coste real de la reparación."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer8', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda8_poisson_20261026_v2'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    validation = w.read(OUT / 'validation_v1/report.json'); price = w.read(OUT / 'price_report.json')
    assert len(validation['replays']) == 15 and len(validation['source_mathematics']) == 11
    assert not any(x['all_exploratory_checks_pass'] for x in validation['comparisons'].values())
    assert not validation['conditional_stress_triggered'] and price['source_GLM_attempts_total'] == 12
    phase = w.read(P); assert phase['new_price_fits'] == 60 and phase['new_submissions'] == 1
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = ('Revisar los artefactos y recetas de severidad fuente FS/FSp y su ajuste E25 antes de otra tanda. '
        'La señal meteorológica de frecuencia no resolvió la inestabilidad ni la transferencia a nuevo negocio; no repetir W7/P1-P3, '
        'cambiar el umbral a posteriori o usar un subconjunto de perils elegido por sus resultados retenidos. '
        'Identificar qué soporte/modelos de severidad son recuperables, si ya se probaron las alternativas propuestas y qué diferencia material queda sin contrastar. '
        'Reutilizar recuentos, objetos de reporte y offsets fuente conciliados; no reconstruir curvas por desconocer sus rutas. '
        'Una prueba posterior debe registrar comparador, necesidad, objetivo/exposición, configuración, presupuesto y criterio antes de ajustar o puntuar. '
        '2024 permanece abierto como desarrollo por instrucción humana. Conservar B00, F2, C1, alternativas, autoría y el último cupo; '
        'no gastar un envío por mejoras pequeñas/adversas o sin replay del flujo de entrega. Objetivo0.17 activo, mejor recibo0.16519.')
    note = '\n\n## Frecuencia meteorológica por peril: tanda 8, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se completaron once Poisson GLM estándar en los periodos del desarrollado 2021–2024. '
        'Usan recuentos conciliados y exposición de número de reportes RKM ya guardada. Se transfieren solo los cambios meteorológicos dentro de la misma dirección, '
        'con mezcla de coste de cada C0 de entrenamiento y normalización sin etiquetas por ramo/año/negocio. '
        'Los controles de riesgo, crédito, región, edad, mes y año se quedan en la fuente. No se inventó crédito emergente.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia con ponderación2025, solo sensibilidad |\n|---|---:|---:|---|---:|\n'
    for name in ['P1', 'P2', 'P3']:
        z = validation['comparisons'][name]; lo, hi = z['bootstrap95']; sensitivity = validation['weighted2025_sensitivity'][name]['delta']
        note += f'| {name} | {price["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {sensitivity:+.6f} |\n'
    note += (f'\nLa referencia N3 vale {price["scores"]["N3"]:.6f}; es un comparador de investigación sobre T2b, no el envío C1/F2 completo. '
        'P1 aplica los coeficientes completos, P2 la mitad y P3 la cuarta parte, sin otros ajustes. '
        'Ninguna supera los criterios preinscritos: todas quedan por debajo de +0,002, ganan en tres de cinco folds y pasan a diferencia negativa '
        'tras retirar los 31 grupos más favorables. Los intervalos marginales son positivos, pero los simultáneos de P1/P2 incluyen cero; '
        'no compensan los controles adversos ni la búsqueda adaptativa. P3 tampoco supera los demás criterios.\n\n'
        'Con la ponderación diagnóstica hacia la composición de 2025, las tres diferencias son negativas. '
        'El fallo previo de ESS sigue vigente: esa ponderación no es estimando principal y no se recortó ni reagruparon bandas para cambiarlo. '
        'La corrección mejora el sustituto A1 original2024, pero ese archivo no es el A1 corregido ni reproduce F2 completo. '
        'No se admite un nuevo CSV de test y no se activan los once ajustes condicionales de sensibilidad de observación: faltó su condición previa.\n\n'
        'La primera ejecución terminó en el tercer GLM por no superar el gradiente máximo de 1e-6, aunque el solver declaró convergencia por reducción relativa. '
        'Se guardaron el fallo y los dos modelos ya terminados. La enmienda numérica se registró antes de continuar, redujo ftol de 1e-12 a 1e-15 '
        'y mantuvo objetivo, priors, datos y límite de gradiente. Los dos modelos se reutilizaron por SHA y solo se ajustaron los nueve pendientes. '
        'El coste real es doce intentos para once modelos únicos, incluido el intento fallido; no se oculta ese coste.\n\n'
        'Los once modelos pasaron codificación dispersa independiente, objetivo Poisson de scikit-learn, gradiente y Hessiano por diferencias finitas. '
        'La covarianza aproximada por 48 bloques región/año se reprodujo. Las 15 reproducciones del flujo de precios fueron exactas, '
        'con un segundo cálculo algebraico y el optimizador bloqueado. Alterar siniestros y reservas retenidos no cambia los factores o normalizadores. '
        'Los objetos C0 excluyen los componentes retenidos y se conservaron los totales de referencia. '
        'Estos controles comprueban implementación; no convierten el resultado predictivo adverso en una mejora.\n\n'
        'Se mantienen los límites de cola última, suficiencia de reservas, mezcla global de perils y disponibilidad prospectiva del clima. '
        'La incertidumbre de destino condiciona en la fuente ajustada, la covarianza es aproximada y 2024 es desarrollo adaptativo abierto por el participante. '
        'La revisión propia no es revisión profesional independiente ni aprobación humana. '
        'Coste adicional: 180 normalizadores sin etiquetas, cero curvas C0, cero inferencias T2b nuevas, cero precios de test y cero envíos.\n\n'
        'El mejor recibo público procesado sigue en 0,16519, referencia 57651126; no se ha alcanzado 0,17 y no hay score público nuevo. '
        'B00, F2, C1 y todas las alternativas permanecen.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '; receta y enmienda en registro/semana2_mision017_fase2_tanda8_plan_v1.json y _v2.json.\n\n'
        'Siguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA8_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA8-RESULTADO', '--asunto',
        'Frecuencia climática: mejora pequeña y concentrada; no justifica otro envío', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 8, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'reference': 'N3', 'scores': price['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 12,
        'unique_source_models': 11, 'failed_GLM_attempts_v1': 1, 'completed_models_reused_without_refit': 2,
        'conditional_stress_fits': 0, 'new_C0_fits': 0, 'new_covariate_only_normalizers': 180,
        'new_test_predictions': 0, 'new_submissions': 0, 'forum': json.loads(response.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts}}, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; counter = w.read(counters)
    assert 'phase2_2024_tanda8' not in counter
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counter['cumulative_price_base_fits'] + 12,
        'phase2_2024_tanda8': {'real_GLM_attempts_including_failure': 12, 'unique_accepted_source_models': 11,
            'v1_failed_attempts': 1, 'models_reused_by_SHA_not_refit': 2, 'new_C0_fits': 0,
            'covariate_only_normalizers': 180, 'synthetic_fits_separate': 2, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 12,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 180,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit,
        '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; branch = w.read(state_path)['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, active_jobs=[], next_unit=next_unit, status='active', goal_achieved=False,
        new_price_fits=phase['new_price_fits'] + 12, **{'2024_open': True, '2024_closed': False})
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'goal_status': 'active', 'batch': 8, 'phase_price_fits': phase['new_price_fits'] + 12,
        'new_C0_fits': 0, 'new_submissions': 0, 'best_public': .16519, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__': main()
