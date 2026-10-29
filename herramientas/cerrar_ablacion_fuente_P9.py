"""Integra nueve ajustes fuente; no atribuye ganancia antes de validación destino."""
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P9_fuente_sin_exposicion_20261026'
sp = importlib.util.spec_from_file_location('p9_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert len(d['records']) == 9 and replay['all3lines_exact'] and replay['events_unchanged']
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P9c_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    note = '\n\n## Privada P9: nueve modelos fuente de capacidad fija sin predictor de duración, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se guardaron los nueve modelos preinscritos, con exposición solo '
             'en el offset de coste y sin exposure_model como predictor. Se mantuvieron los demás datos, '
             'categorías, parámetros y rondas originales de cada semilla. No hubo búsqueda nueva de capacidad '
             'ni parada temprana. La duración sigue ponderando el centro fuente, sin entrar en los árboles.\n\n'
             'Las rondas fueron 205/153/190 en autos, 163/201/150 en edificios y 254/239/227 en contenidos. '
             'Se verificaron centros por suma escalar independiente, media ponderada unitaria, guardar/cargar, '
             'orden de filas y suma de hojas. El replay de cachés de las tres semillas fue exacto sin cargar '
             'modelos ni nuevas consultas. Las cachés de aplicación contienen exclusivamente 2023 y 2024. '
             'Cero inferencias 2025, C0, calibraciones destino, scores nuevos, precios finales o envíos.\n\n'
             'Esta etapa es técnica y no permite retirar la variable del modelo actual. La ablación puede '
             'perder señal legítima; además, quitar una columna cambia el mapa del muestreo de variables, '
             'por lo que no equivale a intervenir una sola ruta de árboles ya ajustados. Las rondas proceden '
             'de la búsqueda fuente anterior con esa variable y el enlace fuente permanece condicionado. '
             'La siguiente etapa preinscribirá la comparación completa por grupos y transferencia de año. '
             'B00/F3c/P6, fallos y alternativas intactos; 2024 abierto adaptativo. No hay mejora privada demostrada.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P9_ABLACION_FUENTE.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P9-FUENTE-RESULTADO', '--asunto',
                             'P9: nueve modelos simplificados guardados; validación destino pendiente',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k not in ['records', 'applications']}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   next_unit='Preregister/run P10complete S2/H1source ablation validation, pooled and conditional year transfer; retain original gates/stresses. No futureprices or uploads.')
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P9_source_ablation' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counters['cumulative_price_base_fits']+9,
                  'phase2_private_P9_source_ablation': {'real_source_full_fits': 9, 'attempts': 9,
                    'synthetic_source_fits_separate': 2, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(R/'registro/semana2_ablacion_exposicion_fuente_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P9_source': receipt, 'next_unit': receipt['next_unit']}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase)
    assert not current.get('active_jobs') and not current.get('active_execution')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P9_source': receipt, 'new_price_fits': current['new_price_fits']+9,
                     'mission_private_priority': w.read(priority), 'next_unit': receipt['next_unit']}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P9_source=receipt, new_price_fits=current['new_price_fits']+9,
               mission_private_priority=w.read(priority), next_unit=receipt['next_unit'], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_ablation_index': w.rel(R/'registro/semana2_ablacion_exposicion_fuente_actual.json'),
                                        'week_2_private_source_ablation_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_source_fits': 9, 'new_submissions': 0}))


if __name__ == '__main__': main()
