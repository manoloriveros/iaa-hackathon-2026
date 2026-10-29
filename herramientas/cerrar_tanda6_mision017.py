"""Conserva la calibración adversa y los recibos, sin agotar los cupos."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda6_pendiente_20261025_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    v = w.read(OUT / 'validation_v1/report.json'); assert len(v['replays']) == 15
    assert len(v['mathematics_and_real_learning_replays']) == 30 and not any(z['exploratory_pass'] for z in v['comparisons'].values())
    phase = w.read(P); assert phase['new_price_fits'] == 24 and phase['current_batch']['batch'] == 5
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    live = BASE / 'estado_publico_20261026_v1/receipt.json'; latest = w.read(live)
    best = latest['best_processed_public']; assert best['status'] == 'COMPLETE' and best['public_score'] == .16033
    next_unit = (
        'Auditar la composición de la cartera de 2025 por ramo, negocio y duración frente a 2023–2024, sin etiquetas nuevas ni ajustes. '
        'Revisar por separado la calibración creíble de F2 ya propuesta y sus recibos oficiales: reconstrucción exacta del CSV desde parámetros guardados, '
        'identidad/orden de filas, matemática, sensibilidad y límites de extrapolación de forma; no tratar su previsión de score como recibo ni como validación independiente. '
        'No lanzar otra familia ni otro ajuste de pendientes con las mismas fuentes. Si hay una mejora bien sustentada, fijar antes de enviar el único candidato, su SHA, criterio y coste; '
        'como máximo un envío inicial y conservar el otro cupo. No activar colas antiguas, sondas ajenas ni selección final manual. '
        '2024 sigue abierto como desarrollo; B00, F2 y alternativas se conservan, y la misión 0,17 permanece activa.')
    note = '\n\n## Calibración de pendientes por ámbito, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('La tanda 6 aprendió pendientes de riesgo dentro de cada fold de componentes en 2023–2024. '
        'El preflight reprodujo exactamente precios y completitud en los 15 ámbitos con C0/credibilidad ya guardados; no se reestimó ninguna curva. '
        'Se ajustaron 30 GLM Tweedie 1,5: pendiente común y pendientes por negocio, con penalización 1 y cuatro interceptos año/negocio de control. '
        'Solo se trasladaron pendientes; T3 aplicó la mitad de T2 sin otro ajuste. Se conservaron los totales de cada celda mediante predicciones y covariables.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Folds positivos |\n|---|---:|---:|---|---:|\n'
    for name in ['T1', 'T2', 'T3']:
        z = v['comparisons'][name]; lo, hi = z['bootstrap95']
        note += f'| {name} | {v["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {z["positive_folds"]}/5 |\n'
    note += (f'\nN3 = {v["scores"]["base_N3"]:.6f} es referencia de investigación sobre T2b, no el envío F2 completo. '
        'Las tres variantes empeoran el resultado conjunto y fallan los criterios registrados. La pendiente separada tiene una diferencia de −0,002712 en 2023 y +0,000592 en 2024; '
        'esa mejora de un año no basta para admitirla. En nuevo negocio, las pendientes de autos van aproximadamente de 0,66 a 0,94 y las de edificios de 0,63 a 0,99 entre folds. '
        'El soporte no estabiliza esas correcciones. Se conservan todos los resultados adversos y no se envía la tanda.\n\n'
        'Los 30 GLM pasaron la reconstrucción independiente de matriz, momentos, objetivo scikit-learn y derivadas por diferencias finitas. '
        'Se recorrió el flujo real de aprendizaje sustituyendo el optimizador por la solución congelada: selección, inicialización, momentos, objetivos y parámetros resultan idénticos al alterar las etiquetas retenidas, '
        'sin volver a ajustar. Las 15 reproducciones de precios fueron exactas y conservaron los totales por ramo/negocio. '
        'Coste: 30 estimadores GLM, cero modelos fuente nuevos, cero C0 y 90 normalizadores de cartera sin etiquetas. Los 120 interceptos son parámetros de esos GLM, no 120 estimadores adicionales.\n\n'
        'La consulta oficial actual confirmó F2 procesado, referencia 57647413, score público 0,16033. Kaggle informa ocho envíos del día, 20 totales y dos disponibles; '
        'el límite activo no es un agotamiento total del concurso. La primera lectura falló por DNS del entorno restringido; la consulta autorizada de lectura funcionó después. '
        'No hubo envíos ni cambios de cuenta y no se leyó el score privado. Se conserva el recibo con fecha, sin presentar la consulta como nueva mejora predictiva.\n\n'
        '2024 está abierto como desarrollo adaptativo. El ámbito de información de T2b incluye el desarrollado de 2024, conocido al inicio de 2025; no es validación prospectiva de 2024. '
        'Los intervalos condicionan en la fuente fijada y no identifican toda la incertidumbre de reservas, cola o maestros sin fecha. '
        'Es revisión propia exploratoria, no aprobación humana ni revisión profesional independiente. B00, F2, alternativas y autoría permanecen.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '; ' + w.rel(live) + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA6_RESULTADOS.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    forum = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA6-RESULTADO', '--asunto',
        'Pendientes GLM: resultado adverso e inestabilidad en nuevo negocio; dos cupos conservados', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 6, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'reference': 'N3', 'scores': v['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 30,
        'new_source_reporting_reconstructions': 0, 'new_emerging_C0_fits': 0, 'new_covariate_only_normalizers': 90,
        'submissions': 0, 'forum': json.loads(forum.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts}}, indent=2), encoding='utf8')
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; count = w.read(counters)
    assert 'phase2_2024_tanda6' not in count
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': count['cumulative_price_base_fits'] + 30,
        'phase2_2024_tanda6': {'price_GLM_fits': 30, 'new_C0_fits': 0, 'new_parent_fits': 0,
            'covariate_only_portfolio_normalizers': 90, 'synthetic_fits_separate': 6,
            'GLM_nuisance_intercepts_not_independent_estimators': 120, 'receipt': summary}}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 30,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 90,
        'last_quota': latest['limits'], 'latest_official_public_receipt': {'path': w.rel(live), 'sha256': w.sha(live), 'best': best},
        'active_execution': None, 'active_jobs': [], 'next_unit': next_unit, '2024_open': True, '2024_closed': False,
        'goal_achieved': False, 'previous_goal_turn_audit': {'classification': 'progress',
            'evidence': 'Tanda5 completed with six real GLM and numeric validation; F2 lineage discrepancy identified and preserved; authoritative counters/forum updated.'}}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_batch=summary, next_unit=next_unit, active_jobs=[], status='active',
        latest_official_public_receipt={'path': w.rel(live), 'sha256': w.sha(live), 'best': best})
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'batch': 6, 'new_price_fits': 30, 'phase_price_fits': phase['new_price_fits'] + 30,
        'new_C0_fits': 0, 'new_submissions': 0, 'remaining_daily_slots': latest['limits']['num_allowed_now'], 'forum_id': summary['forum']['id']}))

if __name__ == '__main__':
    main()
