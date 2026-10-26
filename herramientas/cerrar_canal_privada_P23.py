"""Conserva el adverso P23 y sus contadores sin repetir ningún cálculo estadístico."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P23_canal_principal_20261026'
spec = importlib.util.spec_from_file_location('p23_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); context = w.read(OUT/'P23_context_report.json')
    replay = w.read(OUT/'P23_replay_context.json'); cohort = w.read(OUT/'cohort_report.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'P23_context_report.json')
    assert replay['new_fits'] == replay['new_resampling'] == 0
    assert replay['cohort_points_saved_weights_and_intervals_verified']
    assert context['raw_engine_report_sha256'] == w.sha(OUT/'report.json')
    assert not context['all_exploratory_gates_pass']
    events = [json.loads(x) for x in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
    calls = Counter(); primary = Counter(); adverse = Counter()
    for event in events:
        if event['kind'] == 'closed_completed':
            calls[event['role']] += 1
            (primary if event['role'] == 'primary' else adverse).update(event['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    assert primary['shape_factors'] == primary['level_constants'] == 0
    assert primary['residual_factors'] == 60 and primary['training_nuisance_levels'] == 90
    number = 150
    stamp = datetime.now(timezone.utc)
    archive = R/'privado'/('corte_P23_'+stamp.strftime('%H%M%S%f')); archive.mkdir()
    next_unit = (
        'P24: prepare one lower-complexity structural ablation of the current complete algorithm: '
        'use the existing calibrated A1Ssource component alone instead of the fixed50/50direct '
        'A1S+N3price mixture, before the original gender/telework/marketing stages; keep the '
        'same frozen H1/G3mean and observation contract. First inspect existing S0/S1/S2evidence '
        'and prior source-only recipes to rule out an identical completed experiment. Existing '
        'S0without residuals/H1or under a different observation link cannot establish this '
        'whole algorithm, but do not relabel an already tested equivalent. This is one fixed '
        'ablation, not lambda/line/business weight search; preserve N3and all alternatives. '
        'Reuse unchanged A1Sshape/level parents and learn only residual stages whose input '
        'base changes, at most40primary plus40adverse stage calls, zero source/C0fits. '
        'Prove synthetic/full-forward and cached-parent group ancestry first; freeze code/config/criteria/cost/forum '
        'before any real fit or score, with unchanged global gates and P23new-business safeguards. '
        'Do not claim eliminating all conditional features: A1S/observation/H1also retain '
        'documented availability limits. No new2025inference, prices or uploads in preparation. '
        'B00/F3c/all adverses preserved,2024open/adaptive, private improvement unproven.'
    )
    note = '# P23: el efecto de canal no mejora la robustez\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completó la receta registrada antes de aprender: una etapa broker/no broker al final de S2, con los mismos padres A1S/N3, media H1/G3y enlace qSource. Se conservó el adverso anterior del ciclo13; esta prueba aisló otro efecto sobre el algoritmo actual.\n\n'
    note += '| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for name in ['POOLED', 'TRANSFER']:
        a = raw['results'][name]['NOMINAL']
        note += f'| {name} | {a["delta"]:+.7f} | [{a["bootstrap95"][0]:+.7f}; {a["bootstrap95"][1]:+.7f}] | {a["post31_delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} |\n'
    note += ('\nEl combinado pierde. Solo dos folds combinados son positivos y2023pierde, mientras '
             'que2024gana muy poco. La transferencia condicional mejora en punto, con intervalo '
             'compatible con cero. El mínimo0,002, la concentración y los pisos por celda '
             'siguen incumplidos. No se adopta ni se envía esta variante.\n\n')
    note += '| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |\n|---|---:|---|---:|---|\n'
    for name in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        a = next(x for x in cohort['comparisons'] if x['evaluation'] == 'POOLED' and x['cohort'] == name)
        b = next(x for x in cohort['comparisons'] if x['evaluation'] == 'TRANSFER' and x['cohort'] == name)
        note += f'| {name} | {a["delta"]:+.7f} | [{a["marginal95"][0]:+.7f}; {a["marginal95"][1]:+.7f}] | {b["delta"]:+.7f} | [{b["marginal95"][0]:+.7f}; {b["marginal95"][1]:+.7f}] |\n'
    note += ('\nEl nuevo negocio combinado pierde−0,0014145y su intervalo marginal es negativo. '
             'Los dos subconjuntos de broker son compatibles con cero; no se elige el punto '
             'favorable de transferencia para salvar la receta. Fallan las guardas adicionales '
             'de nuevo negocio, bandas y escenarios. Las seis comparaciones de cohorte usan '
             'multiplicidades compartidas con el diseño de P19, cotejadas con las cuatro '
             'guardadas, y2000réplicas. Las bandas de la familia16(globales+cohortes) son '
             'exploratorias y tienen poca resolución en sus colas; no se refinan para perseguir '
             'un pase. Ninguna banda elimina la búsqueda adaptativa anterior.\n\n')
    note += '| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][name]; b = raw['results']['TRANSFER'][name]
        note += f'| {name} | {a["delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} | {b["delta"]:+.7f} | {b["worst_cell_delta"]:+.7f} |\n'
    note += ('\nLa pérdida más alta del nominal corresponde a edificios nuevos en2023combinado '
             'y2024transferencia. Son sensibilidades con precios congelados, sin reestimar '
             'fuente y toda la valoración de cada rama. Los adversos y sus parámetros permanecen.\n\n'
             'Se reutilizaron los30padres S2con grupos, filas y predicciones de partida '
             'cotejados; cada nivel tenía al menos108grupos positivos de entrenamiento. '
             'Se aprendieron solo30etapas nuevas y30controles adversos separados:60factores '
             'más90niveles auxiliares de entrenamiento,150constantes primarias nuevas. '
             'No se cuentan los parámetros reutilizados como ajustes nuevos. Los niveles '
             'auxiliares no se transfieren a la aplicación y el efecto no interactúa con '
             'negocio. La normalización usa la cohorte completa de predicciones por año/negocio; '
             'no se declara una tarifa independiente del lote.\n\n'
             'El fixture completo comprobó padres sintéticos, aprendizaje de la etapa, '
             'alteración de todos los T0/reservas retenidos, JSON, avance a último, media '
             'de miembros y puente observado, con normalización por sumas escalares. '
             'Los30flujos reales nuevos fueron invariantes a la alteración retenida y '
             'se reprodujeron con aprendizaje e inferencia fuente bloqueados. El replay '
             'de cohortes verificó puntos, multiplicidades guardadas e intervalos sin '
             'otro remuestreo. El motor conserva el prefijo histórico P10en su informe '
             'crudo; P23_context_reportidentifica esta receta, sus fuentes y su aprendizaje.\n\n'
             'Decisión siguiente: antes de añadir variables o capacidad, revisar una '
             'ablación estructural más sencilla, componente A1Scalibrado solo frente '
             'a la mezcla directa50/50A1S+N3actual. No se buscarán pesos ni se escogerán '
             'ramos; N3permanece como alternativa y como antecedente de la corrección H1 '
             'que seguiría congelada. Debe comprobarse primero qué parte de esta receta '
             'ya se evaluó en S0/S1/S2para no repetirla. Si es una comparación nueva, '
             'se reutilizarían forma/nivel A1Sy solo se reaprenderían los factores '
             'residuales cuya base cambia, después del fixture, criterios y registro '
             'previos. No se presenta como reproducción de F3c ni como eliminación de '
             'todas las variables condicionales del flujo.\n\n'
             'Las cuatro discusiones públicas de parte2mantienen iguales sus metadatos '
             'respecto a la consulta anterior; no se volvieron a leer cuerpos en ese '
             'chequeo ni se infiere una aclaración temporal nueva. El aporte local '
             'CLA-S2-20261026-008se leyó como evidencia de trabajo concurrente de '
             'versionado; no se ejecutaron sus órdenes ni se inventó autorización humana '
             'en este chat para publicar, cambiar automatizaciones o reconstruir toda la historia.\n\n'
             'B00/F3c/todas las alternativas permanecen.2024está abierto adaptativo, '
             'la fuente y las marcas incluyen2024, y el soporte ponderado2025sigue '
             'insuficiente. Cero nuevos modelos fuente, C0, inferencias2025, precios '
             'finales o envíos. No hay mejora privada acreditada ni revisión profesional '
             'independiente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'P23_context_report.json')+'; '+w.rel(OUT/'cohort_report.json')+'; '+w.rel(OUT/'P23_replay_context.json')+'; '+w.rel(OUT/'public_topic_check.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P23_CANAL_PRINCIPAL.md'; assert not doc.exists()
    doc.write_text(note, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(note, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P23-CANAL-RESULTADO',
        '--asunto', 'P23: canal adverso en nuevo negocio; no adopción y siguiente ablación sencilla',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'P23complete_adverse_no_adoption',
        'context_report': w.rel(OUT/'P23_context_report.json'), 'context_report_sha256': w.sha(OUT/'P23_context_report.json'),
        'replay': w.rel(OUT/'P23_replay_context.json'), 'replay_sha256': w.sha(OUT/'P23_replay_context.json'),
        'document': w.rel(doc), 'forum': json.loads(posted.stdout),
        'primary_new_closed_stages': 30, 'adverse_new_closed_stages_separate': 30,
        'new_primary_closed_constants': number, 'constants': dict(primary),
        'global_nominal': {c: {k: raw['results'][c]['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c in ['POOLED', 'TRANSFER']},
        'global_gates': context['global_gates'], 'new_business_gates': context['new_business_gates'],
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0, 'new_final_prices': 0,
        'new_submissions': 0, 'adopted': False, 'private_improvement_established': False,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True, 'next_unit': next_unit}
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P23_channel' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(),
        'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
        'phase2_private_P23_channel': {'new_primary_stages': 30, 'adverse_stages_separate': 30,
            'new_primary_constants': number, 'constant_breakdown': dict(primary),
            'new_iterative_price_fits': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
            'report': receipt['context_report'], 'report_sha256': receipt['context_report_sha256']}}, archive)
    w.update(R/'registro/semana2_canal_privada_actual.json', receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {
        'last_progress_utc': stamp.isoformat(), 'P23': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P23': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: P21/P22 cache/history uncertainty resolved without source edits; P23standard changed-stage complete algorithm tested/replayed and adverse; lower-complexity structural ablation preparation next'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P23=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    brief = ('\n\n## Privada P23: canal no mejora, 26 de octubre de 2026\n\n'
        f'Codex, {stamp.isoformat()}. Una etapa nueva broker/no broker con padres S2/C0/N3/H1 '
        'congelados: Δcombinado−0,0003554y negocio nuevo−0,0014145. Transferencia+0,0001696con '
        'ICcompatible con cero. Guardas globales, de concentración, celdas y nuevo negocio '
        'incumplidas; no se adopta/envía.30etapas primarias/30adversas,150constantes primarias '
        'nuevas, resto reutilizado y no contado otra vez. Replay30ámbitos/intervalos sin '
        'ajustes/remuestreo. Cero fuente/C0/inferencias2025/precios finales/envíos. B00/F3c '
        'conservados,2024abierto adaptativo; no mejora privada acreditada. P24revisará la '
        'ablación estructural fija A1Ssolo, con comprobación de precedentes y fixture antes '
        'de ajustar. Informe: '+w.rel(doc)+'.\n')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, brief, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_channel_index': w.rel(R/'registro/semana2_canal_privada_actual.json'),
        'week_2_private_channel_report': w.rel(doc)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'],
        'new_constants': number, 'adopted': False, 'new_submissions': 0}))


if __name__ == '__main__': main()
