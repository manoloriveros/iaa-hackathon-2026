"""Integra los tres GLM y conserva pendiente su contraste completo."""
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P11_GLM_fuente_20261026'
sp = importlib.util.spec_from_file_location('p11_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert len(d['records']) == 3 and replay['all3lines_exact'] and replay['events_unchanged']
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P11_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    note = '\n\n## Privada P11: GLM fuente de efectos principales preparado, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se guardaron tres GLM Tweedie1,5 de penalización1 fija, uno por '
             'ramo, sobre el contrato A1S actual de fuente2021–2024. Los profesores GLM previos comprobados '
             'exigían source_guard año2023; no se repitieron sobre las mismas entradas. Se mantuvo duración '
             'como predictor después del adverso P10. No hay interacciones, splines o búsqueda de parámetros.\n\n'
             'Todos los preprocesamientos se ajustaron solo en fuente. Las marcas T0/e_cost con pesos '
             'sqrt(e_cost) concilian por homogeneidad la desviación Tweedie de coste con offset log(e_cost). '
             'Se verificaron gradiente penalizado, predictor lineal por sumas escalares y centros fuente. '
             'Los modelos tienen 136 parámetros en autos, 112 en edificios y 111 en contenidos. Los máximos '
             'gradientes fueron 7,17e−6, 9,23e−7 y 5,95e−7, por debajo del criterio1e−4.\n\n'
             'Coeficientes, medianas, límites, escalas y categorías están en JSON. Su replay recuperó '
             'exactamente las109.296 relatividades históricas, con fit bloqueado. La repetición de inferencia '
             'GLM histórica se cuenta separadamente del cálculo primario; no consulta2025. El nombre de '
             'caché heredado three_seed identifica una interfaz; hay un GLM por ramo y no tres semillas. '
             'Un ajuste sintético verificó el flujo y el gradiente por diferencias finitas.\n\n'
             'Cero C0, calibraciones destino, scores, inferencias2025, precios finales o envíos en P11. '
             'La simplicidad no demuestra generalización: la comparación completa se registra por separado '
             'con los grupos y criterios intactos. Los modelos pueden perder señal no lineal. B00/F3c/P6y '
             'alternativas permanecen,2024abierto adaptativo; no se afirma mejora privada.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P11_GLM_FUENTE.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P11-GLM-RESULTADO', '--asunto',
                             'P11: tres GLM estándar reproducibles; comparación completa pendiente', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'records'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   next_unit='Register/run P12complete GLM4/S2/H1versus original A1S/S2/H1, same groups/criteria/stress. No2025prices or uploads.')
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P11_standard_source_GLM' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counters['cumulative_price_base_fits']+3,
                  'phase2_private_P11_standard_source_GLM': {'real_source_GLM_fits': 3, 'synthetic_source_GLM_fits_separate': 1,
                    'GLM_parameters_not_closedform_constants': 359, 'historical_replay_inference_rows_separate': 109296,
                    'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(R/'registro/semana2_GLM_fuente_privada_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P11': receipt, 'next_unit': receipt['next_unit']}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase)
    assert not current.get('active_execution') and not current.get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P11': receipt, 'new_price_fits': current['new_price_fits']+3,
                     'mission_private_priority': w.read(priority), 'next_unit': receipt['next_unit']}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P11=receipt, new_price_fits=current['new_price_fits']+3,
               mission_private_priority=w.read(priority), next_unit=receipt['next_unit'], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_standard_GLM_source_index': w.rel(R/'registro/semana2_GLM_fuente_privada_actual.json'),
                                        'week_2_private_standard_GLM_source_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_source_fits': 3, 'new_submissions': 0}))


if __name__ == '__main__': main()
