"""Conserva P30 sin adopción: fuente favorable no supera las guardas privadas."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P30_validacion_frecuencia_marca_20261026'
INDEX = R/'registro/semana2_frecuencia_marca_validacion_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P30_VALIDACION_NUMERO_MARCA.md'
sp = importlib.util.spec_from_file_location('p30_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); context = w.read(OUT/'P30_context_report.json')
    replay = w.read(OUT/'P30_replay_context.json'); cohort = w.read(OUT/'cohort_report.json')
    assert not context['all_exploratory_gates_pass']
    assert context['raw_engine_report_sha256'] == w.sha(OUT/'report.json')
    assert replay['context_report_sha256'] == w.sha(OUT/'P30_context_report.json')
    assert replay['raw_engine_replay_sha256'] == w.sha(OUT/'replay_report.json')
    assert replay['new_fits'] == replay['new_resampling'] == 0
    calls = Counter(); primary = Counter(); adverse = Counter()
    for event in [json.loads(x) for x in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]:
        if event['kind'] == 'closed_completed':
            calls[event['role']] += 1
            (primary if event['role'] == 'primary' else adverse).update(event['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    number = sum(primary[k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    assert primary['new_source_component_calls'] == 30 and primary['new_residual_stage_calls'] == 40
    now = datetime.now(timezone.utc).isoformat()
    next_unit = ('P31: review the compatibility of the frozen observation-to-ultimate bridge with the new peril source package using existing HET/P0/P1/P2/P26/P30metadata and code, without fitting or scoring. '
        'Distinguish an intentionally model-independent evaluation contract from a trainable/risk-dependent observation link. '
        'Inspect existing HETsource/outermix hypotheses and ancestry first; do not repeat their finished diagnostics or assume a new mechanism. '
        'Identify whether per-peril historical rates were persisted and whether a legitimate source/outer-held-free link exists for any proposed future adapter. '
        'Do not reconstruct missing peril weights from aggregate rates, modify the target/bridge posthoc to rescue P30, or claim reporting caused its failure. '
        'Any genuinely new observation contract would require separately frozen objective/comparator/configuration/cost and forum before new predictions or scores. '
        'No source inference, C0,2025prices or uploads in the review. Keep B00/F3c/all failures,2024open/adaptive.')
    text = '# P30: el GLM por peril no mejora la robustez en destino\n\nCodex, '+now+'. '
    text += ('La receta completa conserva50/50N3, residuales S2y media H1/G3; solo cambia la fuente a la suma fija de GLM por peril. '
        'Que la fuente superara su referencia no fue suficiente para el transporte. Se conserva el resultado sin adopción ni envío.\n\n'
        '| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n')
    for evaluation in ['POOLED', 'TRANSFER']:
        a = raw['results'][evaluation]['NOMINAL']
        text += f'| {evaluation} | {a["delta"]:+.7f} | [{a["bootstrap95"][0]:+.7f}; {a["bootstrap95"][1]:+.7f}] | {a["post31_delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} |\n'
    text += ('\nEl combinado gana poco y su intervalo incluye cero. La transferencia pierde; en ambos casos la retirada de los31grupos más favorables deja pérdidas. '
        'Solo el criterio de ambos años combinados no negativos pasa entre las guardas globales. No se alcanza la mejora mínima, estabilidad de folds o pisos de celdas.\n\n'
        '| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |\n|---|---:|---|---:|---|\n')
    for name in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        a = next(x for x in cohort['comparisons'] if x['evaluation'] == 'POOLED' and x['cohort'] == name)
        b = next(x for x in cohort['comparisons'] if x['evaluation'] == 'TRANSFER' and x['cohort'] == name)
        text += f'| {name} | {a["delta"]:+.7f} | [{a["marginal95"][0]:+.7f}; {a["marginal95"][1]:+.7f}] | {b["delta"]:+.7f} | [{b["marginal95"][0]:+.7f}; {b["marginal95"][1]:+.7f}] |\n'
    text += ('\nEl punto de negocio nuevo combinado es positivo pero muy incierto. Broker nuevo pierde alrededor de0,009D²y su intervalo marginal combinado es negativo, también con historia cero. '
        'La transferencia de las tres cohortes pierde. Todas las guardas adicionales incumplen algún criterio; no se rescata una parte favorable o una semilla.\n\n'
        '| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n')
    for name in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][name]; b = raw['results']['TRANSFER'][name]
        text += f'| {name} | {a["delta"]:+.7f} | {a["worst_cell_delta"]:+.7f} | {b["delta"]:+.7f} | {b["worst_cell_delta"]:+.7f} |\n'
    text += ('\nSe completaron30calibraciones cerradas primarias y30controles adversos. Constantes primarias nuevas: '+str(number)+'. '
        'Los60ajustes fuente de P28/P29y sus constantes no se cuentan otra vez; C0/N3/H1se reutilizan. '
        'Los30flujos nuevos no cambiaron al alterar etiquetas y reservas retenidas. El replay bloqueó aprendizaje e inferencia fuente y verificó precios, normalizadores, multiplicidades guardadas e intervalos sin remuestrear. '
        'Las fuentes/modelos y la receta se congelaron antes de puntuar, en commit2a5b6c9d.\n\n'
        'La evaluación usa el puente y qSourcefijados; el nuevo backbone suma perils, pero no introdujo un C0por riesgo nuevo en destino. '
        'Eso merece una revisión de compatibilidad antes de otra prueba; estos resultados no demuestran que el puente sea erróneo o que explique la pérdida. '
        'No se cambiará una observación u objetivo después del resultado para hacer pasar la receta. Se revisarán los HETya existentes sin repetirlos. '
        'Una hipótesis distinta necesitará sus propios objetivo, comparador, configuración, coste y foro previos.\n\n'
        'Todo es exploratorio tras búsqueda adaptativa. Fuente2024, ancestros comunes de observación, cola y reservas, maestros sin fecha y soporte ponderado2025insuficiente conservan sus límites. '
        'No es una reproducción exacta de F3cni una revisión profesional independiente. B00/F3c y todas las alternativas se conservan,2024abierto adaptativo. '
        'Cero ajustes fuente/C0, inferencias2025, precios finales o envíos nuevos en P30.\n\nPróximo trabajo: '+next_unit
        +'\n\nEvidencia: '+w.rel(OUT/'P30_context_report.json')+'; '+w.rel(OUT/'cohort_report.json')+'; '+w.rel(OUT/'P30_replay_context.json')+'.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P30-FRECUENCIA-RESULTADO',
        '--asunto', 'P30: fuente favorable no transporta con robustez; broker nuevo adverso, sin adopción',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': 'P30complete_transport_adverse_not_admitted',
        'context_report': w.rel(OUT/'P30_context_report.json'), 'context_report_sha256': w.sha(OUT/'P30_context_report.json'),
        'replay': w.rel(OUT/'P30_replay_context.json'), 'replay_sha256': w.sha(OUT/'P30_replay_context.json'),
        'document': w.rel(DOC), 'forum': json.loads(posted.stdout), 'new_primary_closed_learners': 30,
        'adverse_closed_learners_separate': 30, 'new_primary_constants': number, 'constants': dict(primary),
        'global_nominal': {c: {k: raw['results'][c]['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c in ['POOLED', 'TRANSFER']},
        'global_gates': context['global_gates'], 'new_business_gates': context['new_business_gates'],
        'adopted': False, 'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0, 'new_submissions': 0,
        'next_unit': next_unit, 'goal_achieved': False, 'private_improvement_established': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P30_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P30_peril_source_target' not in counters
    w.update(cp, {'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+number,
        'phase2_private_P30_peril_source_target': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
            'new_primary_constants': number, 'constant_breakdown': dict(primary), 'new_iterative_price_fits': 0,
            'new_source_fits': 0, 'new_C0_fits': 0, 'report': receipt['context_report'], 'report_sha256': receipt['context_report_sha256']}}, archive)
    w.update(INDEX, receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P30': receipt, 'next_unit': next_unit, 'last_progress_utc': now}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'private_P30': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: P26andP30whole-target comparisons/replays completed and adverses retained; P27paired objective contract checked; P28/P29standard source models fit, replayed and versioned; no unsupported adoption or upload'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P30=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P30: GLM fuente sin transporte robusto, 26 de octubre de2026\n\nCodex, '+now+'. Δcombinado+0,0003941con ICincluye cero; transferencia−0,0008506, Post31negativo. Broker nuevo combinado−0,0090340con ICmarginal negativo; guardas incumplidas. No adopción/envío.30calibraciones primarias/30adversas, '+str(number)+' constantes primarias; source/C0/N3/H1reutilizados. Replay30flujos y cohortes sin ajustes/remuestreo. B00/F3cy2024abierto conservados; no mejora privada acreditada. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_count_mark_validation_index': w.rel(INDEX), 'week_2_private_count_mark_validation_report': w.rel(DOC)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'closed': True, 'new_primary_constants': number, 'adopted': False, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
