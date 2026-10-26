"""Registra la auditoría de cohortes guardada, sin volver a puntuar o remuestrear."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P19_cohortes_broker_20261026'
spec = importlib.util.spec_from_file_location('p19_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    assert replay['new_fits'] == replay['new_resampling'] == replay['new_inference'] == 0
    assert report['family_size'] == 30 and report['new_submissions'] == report['new_model_fits'] == 0
    preflight = w.read(OUT/'covariate_preflight.json'); support = w.read(OUT/'support.json')
    correction = w.read(OUT/'implementation_correction.json')
    assert correction['no_scoring_before_correction']
    assert correction['new_code_sha256'] == w.sha(R/'herramientas/auditar_cohortes_broker_P19.py')
    stamp = datetime.now(timezone.utc)
    archive = R/'privado'/('corte_P19_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); archive.mkdir()
    next_unit = (
        'P20: before another model fit, reconstruct the complete delivered F3c lineage and '
        'availability of a strict saved historical replay. Read only its own production/receipt '
        'metadata and inspect the exact producer code and available per-fold artifacts. '
        'Distinguish delivery-row replay from grouped OOF and verify source/history/target/observation '
        'contracts and code version status. Reuse actual saved objects where present; do not '
        'substitute A1S/S2/H1 proxy evidence for F3c. If historical objects are absent, enumerate '
        'the exact missing scopes and preregister the smallest complete comparison before any fit. '
        'No retraining, source/C0reestimation, new inference, public probing or submission in this '
        'provenance unit. No private-score read or performance claim. Preserve B00/F3c/all '
        'adverse variants,2024open/adaptive and source2024conditional limits.'
    )
    note = '# P19: el promedio global oculta pérdidas en negocio nuevo\n\n'
    note += f'Codex, {stamp.isoformat()}. Se compararon OOF ya guardadas en tres cohortes preinscritas, frente al mismo A1S/S2/H1 y su enlace de observación qSource. No es una comparación directa con el F3c enviado.\n\n'
    note += '| Cartera preparada | Filas | Negocio nuevo | Nuevo/broker | Nuevo/broker/historia cero |\n|---|---:|---:|---:|---:|\n'
    for year in [2023, 2024, 2025]:
        rows = [a for a in preflight['summaries'] if a['year'] == year]
        n = sum(a['rows'] for a in rows)
        counts = {c: sum(a['cohort_rows'][c] for a in rows) for c in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']}
        note += f'| {year} | {n} | {counts["NB"]} ({100*counts["NB"]/n:.2f}%) | {counts["NB_BROKER"]} | {counts["NB_BROKER_ZERO"]} |\n'
    note += ('\nEl canal broker ronda70%de todas las filas en cada año; no identifica de forma exclusiva '
             'la cartera adquirida. Las cohortes son proxies descriptivos. Historia cero significa '
             'cero años desde el primer inicio de póliza visible en esta base, con fecha conocida '
             'hasta31de diciembre2024y truncamiento inferior en cero; no demuestra que el cliente '
             'carezca de seguro previo o experiencia de siniestros en otra entidad. El preflight '
             'de2025leyó solo covariables, sin resultados o predicciones nuevas.\n\n')
    note += '| Evaluación | Cohorte | D0 | GLM | GLM con ausentes | GAM | Conjunta |\n|---|---|---:|---:|---:|---:|---:|\n'
    for evaluation in ['POOLED', 'TRANSFER']:
        for cohort in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
            a = {v['algorithm']: v['delta'] for v in report['comparisons'] if v['evaluation'] == evaluation and v['cohort'] == cohort}
            note += f'| {evaluation} | {cohort} | '+ ' | '.join(f'{a[k]:+.7f}' for k in ['D0', 'GLM', 'GLM_MI', 'GAM', 'JOINT'])+' |\n'
    note += ('\nTodas las variantes pierden en el nuevo negocio combinado; en nuevo/broker y '
             'nuevo/broker/historia cero las pérdidas de GLM, GLMcon ausentes, GAMy conjunta '
             'también conservan signo negativo en la banda simultánea exploratoria de esta familia. '
             'El GAMhabía ganado en promedio global, pero pierde−0,0062464en negocio nuevo '
             '(banda simultánea[−0,0118206;−0,0006722]). La conjunta pierde−0,0136354en esa '
             'cohorte. No se selecciona una línea favorable ni se cambia una mezcla para compensarlo.\n\n'
             'En la transferencia condicional, los intervalos de las quince comparaciones '
             'correspondientes a sus cohortes incluyen cero. Los puntos de GLM, GAMy conjunta '
             'siguen negativos. Estas cifras no acreditan una mejora privada ni permiten '
             'atribuir el deterioro a una única variable o etapa.\n\n')
    # All 30 intervals stay visible, including the adverse and ambiguous comparisons.
    note += '| Evaluación/cohorte | Variante | IC95 marginal | Banda95 simultánea, familia30 |\n|---|---|---|---|\n'
    for a in report['comparisons']:
        ci = a['marginal95']; simultaneous = a['simultaneous95']
        note += f'| {a["evaluation"]}/{a["cohort"]} | {a["algorithm"]} | [{ci[0]:+.6f}; {ci[1]:+.6f}] | [{simultaneous[0]:+.6f}; {simultaneous[1]:+.6f}] |\n'
    note += ('\nSe hizo una sola familia nueva de2000remuestras por los grupos globales de negocio '
             'nuevo. Las mismas multiplicidades se aplicaron a las cohortes solapadas y ambas '
             'evaluaciones. En cada réplica se recalculó el nulo de la cohorte; la banda '
             'simultánea usa el máximo desvío estandarizado de las30comparaciones. Los precios '
             'OOF permanecen fijos: no se reestima incertidumbre de los modelos o de la fuente. '
             'La corrección por esta familia no elimina la búsqueda adaptativa anterior.\n\n')
    note += '| Ramo/año en nuevo/broker/historia cero | Grupos con coste positivo | Mínimo por fold | Mayor grupo, % del coste |\n|---|---:|---:|---:|\n'
    for a in support:
        if a['evaluation'] == 'POOLED' and a['cohort'] == 'NB_BROKER_ZERO':
            note += f'| {a["line"]}/{a["year"]} | {a["positive_groups"]} | {min(a["positive_groups_by_fold"].values())} | {100*a["largest_cost_group_share"]:.2f}% |\n'
    note += ('\nEdificios y contenidos incumplen el filtro descriptivo en las tres cohortes: '
             '30grupos positivos por ramo/año y10en cada fold. Motor pasa ese filtro, que '
             'solo detecta soporte manifiestamente escaso y no certifica suficiencia de cola '
             'o transferencia. Hay18registros fallidos entre27, contando las cohortes anidadas '
             'y la repetición de2024en transferencia; no son18fallos independientes. Se '
             'conservan los folds y los siniestros, sin reagrupar para hacer pasar el filtro.\n\n'
             'El enlace real cotejó109296filas combinadas y59202de transferencia: mismas '
             'claves, grupos, folds, objetivos y referencia entre las cinco variantes. La '
             'desviación se contrastó con otra implementación para puntos y multiplicidades '
             'guardadas. El replay reprodujo covariables, puntos, primeras cuatro multiplicidades '
             'y todos los intervalos, sin nuevas remuestras. Enlaces con IDsduplicados o años '
             'futuros fueron rechazados. El fallo inicial de tipos numéricos y el de conservación '
             'de row_idocurrieron antes de puntuar; quedan código, recibos y enmienda previa '
             'en el foro. Cero ajustes, C0, inferencias, precios2025o envíos.\n\n'
             'Decisión: no adoptar estas variantes por el promedio global ni añadir otra familia '
             'sin aclarar el comparador entregado. El siguiente punto reconstruirá el linaje '
             'completo de F3cy determinará qué replay histórico estricto existe. El proxy '
             'A1S/S2/H1no sustituye esa evidencia. No se ajustará nada en esa revisión de '
             'procedencia; si faltan objetos, se precisará el menor experimento completo '
             'necesario antes de preinscribirlo.\n\n'
             'B00/F3c/todas las alternativas permanecen.2024está abierto adaptativo, la fuente '
             'y las marcas comunes incluyen2024y la transferencia anual sigue condicionada '
             'a ello. El soporte ponderado2025continúa insuficiente. No hay prueba de mejora '
             'privada ni revisión profesional independiente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'support.json')+'; '+w.rel(OUT/'cells.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'implementation_correction.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P19_COHORTES_BROKER.md'; assert not doc.exists()
    doc.write_text(note, encoding='utf8')
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P19-COHORTES-RESULTADO',
        '--asunto', 'P19: pérdidas en nuevo negocio; verificar F3c antes de otra familia',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'P19cohorts_complete_adverse_no_adoption',
        'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'replay': w.rel(OUT/'replay_report.json'), 'replay_sha256': w.sha(OUT/'replay_report.json'),
        'implementation_correction': w.rel(OUT/'implementation_correction.json'),
        'document': w.rel(doc), 'forum': json.loads(posted.stdout),
        'new_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_submissions': 0,
        'new_bootstrap_families': 1, 'replicates': 2000, 'simultaneous_family': 30,
        'hidden_private_improvement_established': False, 'goal_achieved': False,
        'B00_all_alternatives_preserved': True, '2024_open': True, 'next_unit': next_unit}
    counters_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counters_path)
    assert 'phase2_private_P19_cohorts' not in counters
    w.update(counters_path, {'as_of_utc': stamp.isoformat(), 'phase2_private_P19_cohorts': {
        'new_price_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_submissions': 0,
        'new_bootstrap_families': 1, 'bootstrap_replicates': 2000, 'comparisons': 30,
        'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    w.update(R/'registro/semana2_cohortes_broker_privada_actual.json', receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P19': receipt, 'next_unit': next_unit}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P19': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: fixed new-business cohort audit completed and replayed without fits; global point gains fail relevant cohorts; strict F3c lineage next'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P19=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    brief = ('\n\n## Privada P19: composición y nuevo negocio, 26 de octubre de 2026\n\n'
        f'Codex, {stamp.isoformat()}. Auditoría preinscrita con OOF guardadas: el nuevo negocio '
        'es76,04%en2025frente a11,93%/15,31%histórico. El GAMpierde−0,0062464D²en nuevo '
        'negocio combinado frente al mismo A1S/S2/H1, pese a su punto global positivo; las '
        'otras variantes tampoco establecen mejora en esas cohortes. Edificios/contenidos '
        'fallan el filtro descriptivo de grupos positivos por fold. Una familia nueva de2000 '
        'remuestras/30comparaciones, replay y matemática por otro método; cero ajustes, '
        'C0, inferencias o envíos. Fallos de implementación previos a puntuación conservados. '
        'No adopción; B00/F3c/alternativas preservadas,2024abierto adaptativo. Siguiente: '
        'linaje y disponibilidad del replay histórico del F3centregado, sin entrenar. Informe: '+w.rel(doc)+'.\n')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, brief, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {
        'week_2_private_broker_cohort_index': w.rel(R/'registro/semana2_cohortes_broker_privada_actual.json'),
        'week_2_private_broker_cohort_report': w.rel(doc)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_fits': 0, 'new_submissions': 0}))


if __name__ == '__main__': main()
