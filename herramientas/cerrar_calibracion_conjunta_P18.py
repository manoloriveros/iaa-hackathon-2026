"""Cierra P18 sin repetir ajustes, inferencia ni remuestreo."""
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton')
R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P18_calibracion_conjunta_20261026'
spec = importlib.util.spec_from_file_location('p18_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert not (OUT/'completion_receipt.json').exists()
    phase_path = R/'registro/semana2_mision017_fase2_actual.json'
    phase = w.read(phase_path)
    assert not phase.get('active_jobs')
    state_path = ROOT/'Preparación/ESTADO_PROYECTO.json'
    assert not w.read(state_path).get('week_2_mission017_phase2_execution')
    raw = w.read(OUT/'report.json')
    secondary = w.read(OUT/'secondary_report.json')
    replay = w.read(OUT/'replay_report.json')
    secondary_replay = w.read(OUT/'secondary_replay_receipt.json')
    assert replay['status'] == 'P18all10saved_joint_flows_exact'
    assert replay['scopes'] == 10 and replay['fit_blocked'] and replay['new_fits'] == 0
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    assert secondary_replay['paired_draws_and_intervals_exact']
    assert secondary_replay['secondary_report_sha256'] == w.sha(OUT/'secondary_report.json')
    assert not all(raw['diagnostic_gates'].values())
    events = [json.loads(x) for x in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
    counts = Counter((x['kind'], x['role']) for x in events)
    for role in ['primary', 'poison']:
        for kind in ['estimator_fit_started', 'estimator_fit_returned', 'estimator_fit_completed']:
            assert counts[kind, role] == 10
    parameters = Counter()
    maximum_gradient = 0.0
    for cohort in ['POOLED', 'TRANSFER']:
        for fold in range(5):
            directory = OUT/f'{cohort}_{fold}'
            committed = w.read(directory/'committed.json')
            assert all(committed[k] for k in ['whole_current_learner_held_poison_exact', 'row_shuffle_batch_exact', 'observation_bridge_checked'])
            for relative, digest in committed['outputs'].items():
                assert w.sha(ROOT/relative) == digest
            for role in ['primary', 'poison']:
                model = w.read(directory/role/'model.json')
                parameters[role] += len(model['coef']) + 1
                control = w.read(directory/role/'controls.json')
                assert control['ratio_weight_cost_deviance_equivalence'] and not control['warnings']
                maximum_gradient = max(maximum_gradient, control['max_abs_gradient'])
    assert parameters == {'primary': 290, 'poison': 290}
    stamp = datetime.now(timezone.utc)
    archive = R/'privado'/('corte_P18_'+stamp.strftime('%Y%m%dT%H%M%S%fZ'))
    archive.mkdir()
    next_unit = (
        'P19: covariate-only preflight of broker acquisition proxies against 2025inputs, '
        'then preregister an audit of saved common-qSource OOF algorithms on fixed cohorts '
        '(NB; NB/broker; NB/broker/no prior observed exposure). Compare incumbent A1S/S2/H1 '
        'and already evaluated D0/P12/P15/P17/P18 only under the same observation contract. '
        'Inspect group/positive-claim support by line/year/cohort before interpreting scores. '
        'No new weights, classifiers, model/C0fits or inference; no repeat of global diagnostics. '
        'If a new bounded paired bootstrap is needed, freeze its support rules/family/seeds '
        'before scoring. Do not choose lines, weights or candidates from thin subgroup results. '
        'B00/F3c/all alternatives preserved; 2024open/adaptive; no uploads or private-performance claim.'
    )
    note = '# P18: la calibración conjunta no mejora la robustez\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completó la receta preinscrita: tasas anuales absolutas del GAMfuente con calibración Tweedie conjunta regularizada, sin mezcla N3 ni corrección H1 o normalizadores de cartera al predecir.\n\n'
    note += '| Frente a A1S/S2/H1, nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort in ['POOLED', 'TRANSFER']:
        a = raw['results'][cohort]['NOMINAL']
        note += f'| {cohort} | {a["delta"]:.7f} | [{a["bootstrap95"][0]:.7f}, {a["bootstrap95"][1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nLa transferencia es positiva en punto; su intervalo incluye cero. El combinado pierde, '
             'y fallan los controles de folds, años, concentración y pisos por celda. '
             'La receta no se adopta ni se envía. Compartir escala entre ramos pudo contraer '
             'diferencias reales entre mercados, pero esta receta cambió varios componentes '
             'a la vez y no identifica una causa única.\n\n')
    note += '| Frente al GAM/S2/H1 de P17 | Δ D² | IC95 emparejado | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    for cohort in ['POOLED', 'TRANSFER']:
        a = secondary['results'][cohort]['NOMINAL']
        ci = a['bootstrap95_paired_existing_draws']
        note += f'| {cohort} | {a["delta"]:.7f} | [{ci[0]:.7f}, {ci[1]:.7f}] | {a["post31_delta"]:.7f} | {a["worst_cell_delta"]:.7f} |\n'
    note += ('\nEl intervalo marginal del combinado secundario es negativo; el simultáneo de la familia '
             'de diez comparaciones incluye cero. No se interpreta como confirmación independiente '
             'tras la búsqueda adaptativa. Se reutilizaron diferencias de draws con idénticos grupos, '
             'outcomes, semillas y denominadores, sin otro remuestreo.\n\n')
    note += '| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for scenario in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][scenario]
        b = raw['results']['TRANSFER'][scenario]
        note += f'| {scenario} | {a["delta"]:.7f} | {a["worst_cell_delta"]:.7f} | {b["delta"]:.7f} | {b["worst_cell_delta"]:.7f} |\n'
    note += ('\nSe conservaron todos los adversos. Estas sensibilidades usan precios congelados; '
             'no representan la reestimación completa de cada valoración de reservas o cola.\n\n'
             'Los diez ajustes primarios y diez controles adversos separados terminaron con '
             '29 parámetros por ámbito. Alterar todos los T0/reservas retenidos dejó iguales '
             'los objetos aprendidos y precios últimos. Se verificaron el puente de observación, '
             'la equivalencia matemática del objetivo de cocientes con la desviación de costes, '
             'los gradientes y el flujo completo por filas, lotes y orden cambiado. '
             'Los diez replays con fit bloqueado fueron exactos. No hubo nuevos modelos fuente, '
             'C0, inferencias2025, precios finales ni envíos. Los coeficientes de estos GLM '
             'no se cuentan como constantes cerradas de precio.\n\n'
             'Corrección editorial del registro congelado: donde la evaluación dice '
             '“PureGammaalgorithm” corresponde GAM, modelo aditivo generalizado. La implementación '
             'y las tasas guardadas proceden del GAM de P16; la calibración es Tweedie1,5, '
             'no una regresión Gamma de severidad. Se conserva el texto original y su SHA.\n\n'
             'El siguiente paso revisará la representación del negocio adquirido por broker '
             'con covariables y predicciones ya guardadas. La distribución2025tiene mucho '
             'negocio nuevo y el soporte de la ponderación anterior sigue insuficiente. '
             'Antes de otra familia de modelos conviene delimitar dónde puede transferirse '
             'la evidencia histórica. Las cohortes serán proxies descriptivos; no se ajustarán '
             'pesos para favorecer una receta.\n\n'
             'Se mantienen B00, F3c y todas las alternativas.2024está abierto como desarrollo '
             'adaptativo; la fuente y las marcas incluyen2024y la evaluación anual sigue siendo '
             'condicional. No se acredita mejora privada ni revisión profesional independiente.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'secondary_report.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'secondary_replay_receipt.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P18_CALIBRACION_CONJUNTA.md'
    assert not doc.exists()
    doc.write_text(note, encoding='utf8')
    body = OUT/'forum_resultados.md'
    body.write_text(note, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P18-CONJUNTA-RESULTADO',
        '--asunto', 'P18: calibración conjunta adversa; revisar representación del broker sin ajustar',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {
        'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'P18complete_adverse_not_adopted',
        'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'secondary_report': w.rel(OUT/'secondary_report.json'), 'secondary_report_sha256': w.sha(OUT/'secondary_report.json'),
        'replay': w.rel(OUT/'replay_report.json'), 'replay_sha256': w.sha(OUT/'replay_report.json'),
        'secondary_replay': w.rel(OUT/'secondary_replay_receipt.json'),
        'document': w.rel(doc), 'forum': json.loads(posted.stdout),
        'primary_nominal': {c: raw['results'][c]['NOMINAL'] for c in ['POOLED', 'TRANSFER']},
        'diagnostic_gates': raw['diagnostic_gates'], 'primary_GLM_fits': 10,
        'adverse_GLM_fits_separate': 10, 'primary_coefficients': 290,
        'maximum_gradient': maximum_gradient, 'new_closed_form_constants': 0,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_2025inference': 0,
        'new_final_prices': 0, 'new_submissions': 0, 'adopted': False,
        'private_improvement_established': False, 'goal_achieved': False,
        'B00_all_alternatives_preserved': True, '2024_open': True, 'next_unit': next_unit,
    }
    cp = R/'registro/semana2_contadores_propios_actual.json'
    counters = w.read(cp)
    assert 'phase2_private_P18_joint_calibration' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(),
        'cumulative_price_base_fits': counters['cumulative_price_base_fits']+10,
        'phase2_private_P18_joint_calibration': {
            'primary_GLM_fits': 10, 'adverse_GLM_fits_separate': 10,
            'primary_coefficients_not_closed_form_constants': 290,
            'new_closed_form_constants': 0, 'new_source_fits': 0, 'new_C0_fits': 0,
            'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, archive)
    index = R/'registro/semana2_calibracion_conjunta_privada_actual.json'
    w.update(index, receipt, archive)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P18': receipt, 'next_unit': next_unit}, archive)
    phase = w.read(phase_path)
    assert not phase.get('active_jobs')
    count = phase['new_price_fits']+10
    w.update(phase_path, {'utc': stamp.isoformat(), 'private_P18': receipt,
        'new_price_fits': count, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: joint standard calibration evaluated and replayed; failed robustness gates; fixed-cohort broker audit next'}, archive)
    own = w.read(state_path)['week_2_mission017_phase2_20261025']
    own.update(private_P18=receipt, new_price_fits=count, next_unit=next_unit, goal_achieved=False)
    w.update(state_path, {'week_2_mission017_phase2_20261025': own}, archive)
    brief = ('\n\n## Privada P18: calibración conjunta adversa, 26 de octubre de 2026\n\n'
             f'Codex, {stamp.isoformat()}. ΔD² combinado−0,0014624, transferencia+0,0026877con '
             'IC95compatible con cero; concentración y pisos por celda incumplidos. Diez GLM '
             'primarios y diez adversos separados;290coeficientes primarios, cero constantes cerradas '
             'nuevas. Replays exactos de los diez ámbitos y del secundario emparejado. No se adopta '
             'ni se envía. B00/F3c/todas las alternativas conservadas;2024abierto adaptativo. '
             'Siguiente: cohorte de broker con covariables y OOF guardadas, sin ajustar pesos ni modelos. '
             'Sin evidencia de mejora privada. Informe: '+w.rel(doc)+'.\n')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT/'Preparación'/name, brief, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {
        'week_2_private_joint_calibration_index': w.rel(index),
        'week_2_private_joint_calibration_report': w.rel(doc)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'],
        'new_primary_fits': 10, 'total_phase_fits': count, 'adopted': False, 'new_submissions': 0}))


if __name__ == '__main__':
    main()
