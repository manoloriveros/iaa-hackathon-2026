"""Registra una síntesis ya conciliada, preservando la unidad concurrente."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_sintesis_20261024_v1'
ID = 'S2-B20-SINTESIS2023-v1-20261024'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()


def dump(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ev(p):
    return {'path': rel(p), 'sha256': sha(p)}


def main():
    idxpath = REPO / 'registro/semana2_b20_sintesis_actual.json'
    assert not idxpath.exists(), 'Registro existente; no repetir.'
    plan = read(RUN / 'plan_snapshot.json')
    report, v = read(RUN / 'report.json'), read(RUN / 'verification.json')
    assert v['failed'] == 0 and v['passed'] == 205
    for item in plan['frozen_sources']:
        assert sha(ROOT / item['path']) == sha(ROOT / item['snapshot']) == item['sha256']
    doc = REPO / 'docs/archivo/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md'
    outputs = [RUN / 'report.json', RUN / 'verification.json', RUN / 'decision_journal.json',
               RUN / 'evidence_gaps.json', doc]
    code = [REPO / 'herramientas' / name for name in ['consolidar_b20_evidencia2023.py',
            'verificar_sintesis_b20_2023.py', 'registrar_sintesis_b20_2023.py']]
    (RUN / 'code').mkdir()
    for path in code:
        (RUN / 'code' / path.name).write_bytes(path.read_bytes())
    manifest = {'id': ID, 'author': 'Codex', 'inputs': plan['frozen_sources'],
                'outputs': [ev(path) for path in outputs], 'code': [ev(path) for path in code],
                'code_snapshots': [ev(RUN / 'code' / path.name) for path in code],
                'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0,
                'not_a_reverification_of_original_raw_data_or_models': True}
    dump(RUN / 'manifest.json', manifest)
    utc = datetime.now(timezone.utc).isoformat()
    idx = {'id': ID, 'author': 'Codex', 'utc': utc, 'path_base': 'workspace_root',
           'status': 'three_saved_B20_diagnostics_consolidated_no_new_model_justified',
           'run': rel(RUN), 'documentation': rel(doc), 'documentation_sha256': sha(doc),
           'plan': rel(REPO / 'registro/semana2_b20_sintesis_plan_v1.json'),
           'plan_sha256': sha(REPO / 'registro/semana2_b20_sintesis_plan_v1.json'),
           'report': ev(RUN / 'report.json'), 'verification': ev(RUN / 'verification.json') | {'passed': 205, 'failed': 0},
           'decision_journal': ev(RUN / 'decision_journal.json'), 'evidence_gaps': ev(RUN / 'evidence_gaps.json'),
           'manifest': ev(RUN / 'manifest.json'), 'source_indices': plan['indices'], 'frozen_source_count': 44,
           'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0, 'new_recipes': 0,
           'reference': 'W2-B00', 'promotion': False, 'all_alternatives_preserved': True,
           '2024_test_closed': True, 'ledger_read': False, 'final_roster_frozen': False,
           'prior_external2024_header_exposure_disclosed': True, 'complete_blindness_claim_allowed': False,
           'professional_independent_validation': False, 'next_model_selected': False,
           'forum_prior': plan['forum_prior'], 'forum_result': plan['forum_result'],
           'next_step': 'Review a finite preregistered mechanism/validation design only if existing evidence supports necessity; no fitting or added complexity now.'}
    dump(idxpath, idx)
    nightpath = REPO / 'registro/semana2_continuidad_nocturna.json'
    n = read(nightpath)
    assert not any(x['id'] == ID for x in n['completed_units'])
    previous_current = n.get('current_unit')
    unit = {'id': ID, 'run': rel(RUN), 'documentation': rel(doc), 'verification': idx['verification'],
            'decision_journal': idx['decision_journal'], 'index': rel(idxpath),
            'forum_result': plan['forum_result'], 'completed_utc': utc,
            'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0}
    n['completed_units'].append(unit)
    if (n.get('current_unit') or {}).get('id') == ID:
        n['current_unit'] = None
    elif ID in n.get('parallel_artifact_diagnostics', {}):
        n['parallel_artifact_diagnostics'][ID].update(status='completed_verified', index=rel(idxpath))
    n['latest_completed_unit'], n['updated_utc'] = unit, utc
    n['latest_b20_synthesis_index'], n['no_repetition_for_completed_b20_synthesis'] = rel(idxpath), True
    n['integration_decisions']['B20_synthesis'] = 'B20 remains alternative: jointnorm shrinkage, outcome-selected influence and heterogeneous/sparse bands do not justify recalibration or added capacity. Nine decisions and six evidence gates recorded.'
    if 'Consolidate completed B20 attribution/contraction/calibration receipts' in n.get('next_unit', ''):
        n['next_unit'] = 'B20 synthesis completed: consult latest_b20_synthesis_index without repeating its diagnostics. Preserve ongoing authorized artifact unit. Any next proposal first needs a concrete residual mechanism, support and a finite preregistered standard comparison; no fit/recalibration/complexity or2024/test/ledger opening under this consolidation.'
    n['queue'] = [x if 'Consolidate existingB20 evidence' not in x else
                  'B20 evidence consolidation completed; reuse saved synthesis and its six unresolved gates, without replay or routine repetition.'
                  for x in n.get('queue', [])]
    dump(nightpath, n)
    dump(RUN / 'registration_receipt.json', {'id': ID, 'utc': utc, 'previous_current_unit': previous_current,
         'current_unit_after': n.get('current_unit'), 'completed_units_at_cut': len(n['completed_units']),
         'preserved_other_current_unit': (previous_current or {}).get('id') in (None, ID)
             or previous_current == n.get('current_unit'),
         'window_end': n['window_end'], 'frequency': n['frequency'], 'no_automation_changed': True})
    routespath = ROOT / 'RUTAS_PROYECTO.json'
    routes = read(routespath)
    routes.update(week_2_b20_synthesis_index=rel(idxpath), week_2_b20_synthesis_report=rel(doc),
                  week_2_b20_synthesis_plan=idx['plan'])
    dump(routespath, routes)
    statepath = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    raw = statepath.read_text(encoding='utf-8-sig')
    key = 'semana2_b20_sintesis2023_20261024'
    assert key not in json.loads(raw)
    state = {'utc': utc, 'author': 'Codex', 'path_base': 'workspace_root', 'index': rel(idxpath),
             'status': idx['status'], 'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0,
             '2024_test_closed': True, 'promotion': False, 'decisions': 9, 'unresolved_gates': 6}
    statepath.write_text(raw.replace('{', '{\n  ' + json.dumps(key) + ': ' +
        json.dumps(state, ensure_ascii=False) + ',', 1), encoding='utf-8')
    note = ('\n\n## ' + ID + ': síntesis de B20 y condiciones del siguiente paso\n\nCodex, UTC ' + utc +
        '. Encargo humano de consolidar atribución, contracción y calibración, sin reentrenar ni abrir 2024/test. '
        'Plan y comentario B20-SYNTH-PRE preceden a la síntesis. Se congelaron 44 JSON/Markdown con SHA y snapshots; '
        'solo recibos finales, sin OOF/modelos/originales, nuevas inferencias o bootstrap. Pasaron 205 conciliaciones documentales propias, cero fallos; '
        'no son repetición ni validación independiente de los diagnósticos.\n\n'
        'La contracción conjunta reduce normas 28,7–61,4% en 15/15 parejas, pero 14 tienen coordenadas crecientes (33 excepciones). '
        'El nivel baja 2,01% y el reparto de log-tasa depende de todos los efectos y su codificación. Frente a B14 la ganancia neta '
        '14.803,66 se compone de 48.637,02 en 31 grupos seleccionados favorables y −33.833,36 en el resto; el numerador explica '
        'la inversión, no el denominador positivo. Las listas cambian por referencia y son diagnósticas, no exclusiones. '
        'Los 12 grupos/20 periodos previos aportan 14.620,81 frente a B19 en ambos recibos, sin constituir otra muestra.\n\n'
        'A/E global B20 1,0113 oculta bandas de edificios 1,966/1,563/0,856/1,198/0,714 y celdas escasas de nuevo negocio. '
        'Bandas fijadas solo en ajuste; B19 usa las mismas filas. Folds solapados y costes concentrados no sostienen factores automáticos. '
        'Se mantienen B00 y B01–B20, contador propio 195/285; cero promoción, calibrador, nuevo alpha, enrutamiento o capacidad añadida.\n\n'
        'Se registran nueve decisiones y seis carencias: mecanismo residual concreto; soporte/estabilidad para recalibrar; '
        'necesidad material de más capacidad; validación que trate búsqueda adaptativa y aprendizaje completo; acta/recibos de política común; '
        'sustento actuarial de último, reservas/reporte/capital y revisión humana competente. Próximo defendible: diseño previo finito y revisable '
        'de una sola modificación estándar si la evidencia concreta lo justifica. Aún no se elige ni autoriza otro modelo. '
        'Más consultas a OOF fijas no cierran la carencia. No se cambia el protocolo común ni se consulta su ledger.\n\n'
        '2024/test/actas/scores/SEL01 cerrados para este trabajo; exposición previa de título ajeno declarada sin uso ni ceguera completa. '
        'Estado/autorizaciones de otra tanda no conciliados aquí. Revisión propia de Codex, no profesional independiente. '
        'Informe docs/archivo/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md e índice registro/semana2_b20_sintesis_actual.json en el repositorio común; '
        'unidad concurrente respetada y fuera de este corte. Se actualiza continuidad para no repetir la síntesis, conservando ventana07:00Bogotá, '
        'frecuencia, incidente Kaggle y otras automatizaciones. Sin entrenamiento/remoto/envío/delegación o mensajes externos.\n')
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        with (ROOT / 'Preparación' / filename).open('a', encoding='utf-8', newline='') as f:
            f.write(note)
    update = ('\n\n## Síntesis B20 concluida, sin otra receta\n\nLa [síntesis](SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md) '
              'concilia tres diagnósticos guardados: 205 comprobaciones documentales sin fallos, 44 fuentes congeladas y cero '
              'ajustes/inferencias/bootstrap. La contracción conjunta, la sensibilidad a grupos y las bandas heterogéneas '
              'mantienen B20 como alternativa. Nueve decisiones y seis carencias delimitan el próximo diseño justificable; '
              'no se adoptan factores, otro alpha o más capacidad. Se conserva cualquier unidad concurrente; sus resultados '
              'posteriores quedan fuera de este corte. 2024/test/ledger cerrados; ventana y programación intactas. '
              'Este balance continúa siendo parcial, no un cierre de la noche.\n')
    for filename in ['PLAN_NOCTURNO_20261023.md', 'BALANCE_NOCTURNO_PARCIAL_20261024.md']:
        with (REPO / 'docs/archivo/semana2' / filename).open('a', encoding='utf-8', newline='') as f:
            f.write(update)
    body = ('Resultado de ' + plan['forum_prior'] + ': 44 fuentes JSON/Markdown agregadas congeladas, '
            '205 conciliaciones documentales propias sin fallos. Sin repetir suites, replay, ajustes o bootstrap. '
            'Contracción conjunta 15/15 (28,7–61,4%) con 33 coordenadas crecientes en 14 pares. '
            'Frente a B14, ganancia +14.803,66 = +48.637,02 de sus31 grupos favorables y −33.833,36 del resto; '
            'la inversión nace del numerador, no del denominador positivo. Listas dependientes de referencia y resultados, sin exclusión. '
            'Los20periodos previos concilian14.620,81 de ganancia frente aB19 entre los dos diagnósticos, sin nueva muestra.\n\n'
            'A/E1,0113 global oculta bandas heterogéneas y soporte concentrado/escaso; B19 usa mismas filas B20. '
            'No normalización/factores/isotónica/alpha/routing u otra capacidad. B00 y B01–B20 conservados, contador195/285 intacto. '
            'Nueve decisiones y seis carencias: mecanismo, soporte/estabilidad, necesidad de capacidad, validación del aprendizaje completo '
            'tras búsqueda adaptativa, política común y sustento actuarial/revisión humana. Aún no hay modificación seleccionada; '
            'el siguiente paso defendible es un diseño previo finito si evidencia concreta lo justifica, sin entrenarlo en este encargo.\n\n'
            'Informe docs/archivo/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md; índice registro/semana2_b20_sintesis_actual.json; '
            'diario, carencias, snapshots y SHA en corrida privada b20_sintesis_20261024_v1. '
            '2024/test/actas/scores/SEL01/ledger cerrados; exposición previa de título ajeno declarada sin uso ni ceguera completa. '
            'Revisión propia de Codex, no profesional independiente; no se concilia la tanda ajena. '
            'Unidad concurrente respetada y fuera de este corte. Continuidad actualizada sin duplicar la síntesis ni cambiar ventana, '
            'incidente o automatizaciones. Cero remoto/envíos/delegación/mensajes externos.\n')
    (REPO / 'registro' / (plan['forum_result'] + '_cuerpo.md')).write_text(body, encoding='utf-8')
    print(json.dumps({'index': rel(idxpath), 'completed_units_at_cut': len(n['completed_units']),
                     'preserved_other_current_unit': read(RUN / 'registration_receipt.json')['preserved_other_current_unit'],
                     'new_fits': 0, 'new_inference': 0}))


if __name__ == '__main__':
    main()
