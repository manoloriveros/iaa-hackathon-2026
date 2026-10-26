"""Registra H3B adverso sin promoción, envío ni repetición de sus cálculos."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton')
R = ROOT / 'Hackaton/Repositorio_IAA2026'
OUT = R / 'privado/semana2/mision017_fase2/H3B_mezcla_negocio_20261026_v1'
sp = importlib.util.spec_from_file_location('state_H3B', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp)
sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT / 'completion_receipt.json').exists()
    report = w.read(OUT / 'report.json')
    commits = [w.read(p) for p in OUT.glob('scope_*/committed.json')]
    assert len(commits) == 75 and all(c['new_learning_poison_exact'] for c in commits)
    assert report['new_reporting_fits'] == report['new_source_models'] == report['new_submissions'] == 0
    stamp = datetime.now(timezone.utc)
    archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%S%fZ')
    archive.mkdir(parents=True)
    next_unit = (
        'Bounded static review of existing temporal trend/annual-weather recipes and available result receipts, '
        'before any further fitting. Determine whether an unresolved calendar/availability mechanism is '
        'materially distinct from completed E13/T7/E27/source-trend work; do not rerun historical producers. '
        'Record evidence and a finite next action, with no automatic new candidate, pooling coefficient search, '
        'oracle level transfer or submission. Keep private-generalization priority, adaptive2023/2024open, '
        'B00/F3c/all alternatives preserved and H1delivery held.'
    )
    note = '\n\n## Privada H3B: la mezcla agregada por negocio pierde frente a H1, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se terminó la receta preinscrita H3B en los 75 ámbitos anidados. '
    note += ('La mezcla de periles se calculó por nuevo negocio/renovación con f_period*s de las covariables '
             'de entrenamiento de cada miembro. La frecuencia ya incluye el periodo: no se multiplicó otra vez por exposición. '
             'Se conservaron T0, los folds, C0 y los denominadores G3 de P2. El coste último se promedió entre cinco miembros '
             'antes de aplicar la observación exterior protegida.\n\n')
    note += '| Contraste | Diferencia D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---:|---:|---:|\n'
    for name, a in report['results'].items():
        note += (f'| {name} | {a["delta"]:+.8f} | [{a["bootstrap95"][0]:+.8f}, '
                 f'{a["bootstrap95"][1]:+.8f}] | {a["post31_delta"]:+.8f} | {a["worst_cell_delta"]:+.8f} |\n')
    note += ('\nH3B pierde frente a H1 en los cinco folds. La diferencia agregada es -0,00098227, '
             'con intervalo simultáneo exploratorio de seis contrastes [-0,00189433, -0,00027593]. '
             'La pérdida se concentra en 2024 y alcanza -0,01122617 en autos nuevos de ese año. '
             'Frente a S2 la mejora nominal es pequeña e incierta; falla el mínimo 0,002, el límite inferior, '
             'la consistencia de folds/años y Post31. Bajo reservas125 y cola10 también falla el suelo de celdas. '
             'Se preserva como resultado adverso, sin promoción o eliminación de candidatos. '
             'No se buscará un peso entre H1 y H3B para rescatar el resultado. El fallo de H3B tampoco prueba la robustez privada de H1.\n\n')
    note += ('Los 75 controles reales volvieron a calcular el aprendizaje nuevo con costes y reservas retenidos '
             'alterados, y perfiles fuente retenidos multiplicados por 1e8. Mezclas, artefactos y precios de último '
             'coincidieron exactamente. Esto verifica el aprendizaje nuevo de H3B; las curvas heredadas no se '
             'reajustaron y su validación de P2 conserva su alcance original. ')
    note += f'El mayor error relativo del puente es {max(c["bridge_max_relative_error"] for c in commits):.3g}. '
    note += ('El flujo sintético de los tres ramos, el momento de Tweedie por otra suma, la media y la métrica '
             'también quedaron comprobados en los recibos de ejecución. Se conservan los SHA de fuentes y código.\n\n')
    count = report['counts']['primary']
    note += (f'Se registran {count["closed_learners"]} aprendices cerrados y {count["constants"]["price_total"]} '
             'constantes de precio primarias; otros tantos controles adversos se cuentan aparte. '
             'Las 150 mezclas de entrenamiento y 30 exteriores son resúmenes de covariables, separados de los parámetros '
             'de precio y de los normalizadores. Hubo cero ajustes C0, modelos fuente, inferencias fuente, precios 2025 o envíos nuevos.\n\n')
    note += ('La evaluación sigue condicionada al núcleo S2, a modelos fuente congelados y a muestras de miembro del 64% '
             'frente al 80% de producción. 2023 y 2024 ya son exploratorios tras búsqueda adaptativa. '
             'El escaso soporte de los pesos hacia la cartera 2025 sigue sin resolverse. '
             'No equivale a reproducción completa del F3c recibido, validación profesional independiente o evidencia de mejora privada.\n\n')
    note += ('Siguiente paso: revisar únicamente las recetas y recibos temporales ya existentes para identificar '
             'si queda un mecanismo de calendario o disponibilidad que justifique una prueba distinta. '
             'No se repetirán E13, T7, E27 ni diagnósticos terminados por cambiarles el nombre. '
             'B00, F3c y todas las alternativas se conservan; 2024 permanece abierto y la entrega H1 diferida.\n\n')
    note += f'Evidencia: {w.rel(OUT / "report.json")}; receta {w.rel(R / "registro/semana2_H3B_mezcla_negocio_plan_v1.json")}.\n'
    doc = R / 'docs/semana2/PRIVADA_H3B_MEZCLA_POR_NEGOCIO.md'
    assert not doc.exists()
    doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / name, note, archive)
    body = OUT / 'forum_resultados.md'
    body.write_text(note, encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-H3B-RESULTADO', '--asunto',
                          'H3B adverso: agregar la mezcla por negocio pierde frente a H1 y no acredita estabilidad',
                          '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {
        'author': 'Codex', 'utc': stamp.isoformat(), 'status': report['status'],
        'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'),
        'document': w.rel(doc), 'forum': json.loads(res.stdout), 'results': report['results'],
        'diagnostic_gates': report['diagnostic_gates'], 'counts': report['counts'],
        'committed_scopes': 75, 'new_C0_fits': 0, 'new_iterative_price_fits': 0,
        'new_source_inference': 0, 'new_final_test_prices': 0, 'new_submissions': 0,
        'submission_allowed': False, 'formal_promotion': False, '2024_open': True,
        'B00_all_alternatives_preserved': True, 'private_improvement_established': False,
        'goal_achieved': False, 'next_unit': next_unit,
    }
    counters = R / 'registro/semana2_contadores_propios_actual.json'
    c = w.read(counters)
    assert 'phase2_private_H3B' not in c
    w.update(counters, {
        'as_of_utc': stamp.isoformat(),
        'cumulative_closed_form_constants': c['cumulative_closed_form_constants'] + count['constants']['price_total'],
        'phase2_private_H3B': {
            'primary': count, 'adverse_separate': report['counts']['poison'],
            'outer_covariate_mixtures_separate': 30, 'outer_derived_covariate_weights_separate': 150,
            'synthetic_closed_learners_excluded': 6, 'new_C0_fits': 0,
            'new_iterative_price_fits': 0, 'report': receipt['report'], 'report_sha256': receipt['report_sha256'],
        },
    }, archive)
    index = R / 'registro/semana2_H3B_mezcla_negocio_actual.json'
    assert not index.exists()
    index.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    priority = R / 'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'H3B': receipt, 'next_unit': next_unit}, archive)
    phase = R / 'registro/semana2_mision017_fase2_actual.json'
    w.update(phase, {'utc': stamp.isoformat(), 'private_H3B': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'active_execution': None, 'active_jobs': [],
                     'last_goal_turn_classification': 'progress: completed and retained adverse nested business-mixture trial; no public-driven rescue'}, archive)
    state = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_H3B=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, active_jobs=[], goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_private_H3B_index': w.rel(index),
                                          'week_2_private_H3B_report': w.rel(doc)}, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_submissions': 0,
                      'cumulative_closed_constants': w.read(counters)['cumulative_closed_form_constants']}))


if __name__ == '__main__':
    main()
