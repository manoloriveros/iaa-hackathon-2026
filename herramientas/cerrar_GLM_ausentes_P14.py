"""Integra tres GLM con ausencia observable, sin anticipar su validación."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P14_GLM_ausentes_20261026'
sp = importlib.util.spec_from_file_location('p14_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'context_report.json'); replay = w.read(OUT/'P14_replay_context.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'context_report.json')
    assert {k: len(v) for k, v in d['indicators'].items()} == {'motor': 6, 'buildings': 5, 'contents': 5}
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P14_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    note = '\n\n## Privada P14: indicadores de ausencia dentro del GLM estándar, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Se guardaron tres GLMfuente con las variables y penalización '
             'originales y solo la ampliación preinscrita de indicadores numéricos. El criterio de inclusión '
             'fue ausencia no constante en fuente. Produjo seis indicadores en autos y cinco en cada ramo '
             'de hogar: además de las trece variables con bandera entre mercados, incluyó flood_zoneen '
             'los tres ramos. No se eliminó por no activar una bandera destino ni se seleccionaron '
             'indicadores por su relación con respuestas.\n\n')
    note += '| Ramo | Indicadores | Parámetros totales |\n|---|---:|---:|\n'
    for line, names in d['indicators'].items(): note += f'| {line} | {len(names)} | {d["parameters"][line]} |\n'
    note += ('\nLos indicadores se centraron y escalaron solo en fuente, manteniendo alpha1. El fixture '
             'probó la colisión anterior entre ausente y mediana observada y la distinción de su nueva '
             'representación. Una llamada sintética ejerció el ajuste completo, gradiente por diferencias '
             'finitas, valores desconocidos, JSONy orden. Los tres ajustes reales pasaron convergencia, '
             'momento/gradiente, álgebra del offset y controles escalares del productor. El replay nuevo '
             'con fitbloqueado recuperó exactamente las relatividades históricas, aplicando los nuevos '
             'preprocesamientos y coeficientes JSON.\n\n'
             'El motor P11se reutilizó con enlaces de funciones locales al proceso. Sus archivos y '
             'recibos anteriores no se modificaron. El informe bruto conserva la identidad del motor '
             'P11y context_report.jsonidentifica GLM4_MI, sus enlaces y las variables reales. Hay un '
             'modelo fuente por ramo; el nombre heredado three_seedde caché es solo una interfaz.\n\n'
             'No hubo C0, calibraciones destino, scores destino, inferencias2025, precios finales o '
             'envíos. Se preparó la validación completa P15frente a A1Scomo primario y P12GLMcomo '
             'secundario, manteniendo criterios y escenarios. Los mecanismos de ausencia pueden diferir '
             'entre mercados: este cambio no recupera valores perdidos ni acredita mejora privada. '
             'B00/F3c/P6y todos los adversos permanecen;2024abierto adaptativo.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'context_report.json')+'; '+w.rel(OUT/'P14_replay_context.json')+'.\n'
    doc = R/'docs/archivo/semana2/PRIVADA_P14_GLM_AUSENTES_FUENTE.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P14-AUSENTES-RESULTADO', '--asunto',
                             'P14: tres GLM con 6/5/5indicadores y replay exacto; validación completa pendiente',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = dict(d); receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'context_report.json'),
                   report_sha256=w.sha(OUT/'context_report.json'), replay=w.rel(OUT/'P14_replay_context.json'),
                   document=w.rel(doc), forum=json.loads(result.stdout),
                   next_unit='P15complete primary versus A1S/S2/H1and paired secondary versus plainGLM; same gates/stresses, no uploads.')
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P14_missing_source_GLM' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counters['cumulative_price_base_fits']+3,
                  'phase2_private_P14_missing_source_GLM': {'real_source_GLM_fits': 3, 'synthetic_source_GLM_fits_separate': 1,
                    'GLMparameters_not_closedform_constants': sum(d['parameters'].values()), 'new_C0_fits': 0,
                    'historical_replay_inference_rows_separate': 109296, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(R/'registro/semana2_GLM_ausentes_fuente_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P14': receipt, 'next_unit': receipt['next_unit']}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase); assert not current.get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P14': receipt, 'new_price_fits': current['new_price_fits']+3,
                     'mission_private_priority': w.read(priority), 'next_unit': receipt['next_unit']}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P14=receipt, new_price_fits=current['new_price_fits']+3,
               mission_private_priority=w.read(priority), next_unit=receipt['next_unit'], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_missing_GLM_source_index': w.rel(R/'registro/semana2_GLM_ausentes_fuente_actual.json'),
                                        'week_2_private_missing_GLM_source_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'new_source_fits': 3, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
