"""Cierre de un diagnóstico de artefactos B19, sin ajustar o cambiar modelos."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/estabilidad_b19_20261024T014815Z_9b2b1803'
INDEX = REPO / 'registro/semana2_b19_estabilidad_actual.json'
NIGHT = REPO / 'registro/semana2_continuidad_nocturna.json'
NOW = datetime.now(timezone.utc).isoformat()
STATEKEY = 'week_2_B19_stability2023_v1_20261024'
BACK = RUN / 'state_before_registration'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
changes = []


def dump(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def top(raw, key, value, add=False):
    val = json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    if add:
        assert key not in json.loads(raw), key
        return raw[:raw.rfind('}')].rstrip() + ',\n  ' + json.dumps(key) + ': ' + val + '\n}\n'
    match = re.search(r'(?m)^  ' + re.escape(json.dumps(key)) + r':\s*', raw)
    assert match, key
    _, end = json.JSONDecoder().raw_decode(raw[match.end():])
    return raw[:match.end()] + val + raw[match.end() + end:]


def change(path, fn):
    before = path.read_bytes()
    backup = BACK / path.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as f:
        f.write(before)
    after = fn(before.decode('utf-8-sig')).encode('utf-8')
    if before.startswith(b'\xef\xbb\xbf'):
        after = b'\xef\xbb\xbf' + after
    temp = path.with_name(path.name + '.b19estabilidadcierre.tmp')
    assert path.read_bytes() == before, 'Concurrencia antes de escritura: ' + rel(path)
    with temp.open('xb') as f:
        f.write(after)
        f.flush()
        os.fsync(f.fileno())
    assert path.read_bytes() == before, 'Concurrencia antes de reemplazo: ' + rel(path)
    os.replace(temp, path)
    item = {'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(),
            'after_sha256': sha(path), 'backup': rel(backup)}
    changes.append(item)
    with (RUN / 'registration_steps.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')


def main():
    p = read(RUN / 'plan_snapshot.json')
    i = read(RUN / 'index_proposed.json')
    producer = read(RUN / 'report.json')
    verifier = read(RUN / 'verification.json')
    reconciliation = read(RUN / 'readout_reconciliation.json')
    assert producer['failed'] == verifier['failed'] == reconciliation['failed'] == 0
    assert producer['fit_calls'] == verifier['fit_calls'] == producer['new_models'] == 0
    assert producer['new_bootstrap'] == verifier['new_bootstrap'] == 0
    assert not INDEX.exists() and not BACK.exists()
    assert all(sha(ROOT / x['path']) == x['sha256'] for x in p['frozen_sources'])
    n = read(NIGHT)
    assert all(x['id'] != p['id'] for x in n['completed_units'])
    assert n['confirmation_2024_open'] is False
    forum = ROOT / 'Hackaton/Semana 2/Foro/FORO.md'
    forum_cut = forum.read_bytes()
    for suffix in ['036', '037']:
        assert forum_cut.count(('<!-- aporte:COD-S2-20261024-' + suffix + ' -->').encode()) == 1
    BACK.mkdir()
    mutable_indices = [REPO / 'registro' / f for f in [
        'semana2_desarrollo2023_actual.json', 'semana2_contadores_propios_actual.json',
        'semana2_sensibilidad_observacion_actual.json', 'semana2_soporte_calendario2023_actual.json',
        'semana2_coberturas_peril2023_actual.json', 'semana2_glm_ridge_actual.json']]
    untouched = {rel(path): sha(path) for path in mutable_indices}
    counter = read(REPO / 'registro/semana2_contadores_propios_actual.json')
    counter_values = {k: counter[k] for k in ['cumulative_price_base_fits', 'cumulative_closed_form_constants']}
    i.update(as_of_registration_utc=NOW, documentation_sha256=sha(ROOT / i['documentation']),
             unrelated_indices_and_counters_cut=untouched, counter_values_at_registration=counter_values,
             this_unit_counter_increment=0, this_unit_catalog_mutations=0,
             concurrent_research_is_not_this_audit=True)
    dump(INDEX, i)
    next_step = ('Trace payment, reserve, recovery, status and dates for the highlighted saved2023 '
                 'claim components; artifact-only reconciliation, no refit, new bootstrap, target '
                 'change or removal. Keep B00/all alternatives and own2024/test closed. '
                 'Any later model requires a separate justified frozen recipe and prior forum comment.')

    def night(raw):
        obj = json.loads(raw)
        assert not any(x['id'] == p['id'] for x in obj['completed_units'])
        current = obj.get('current_unit')
        ours = current is not None and current.get('id') == p['id']
        foreign = current is not None and not ours
        entry = {k: i[k] for k in ['id', 'run', 'documentation', 'verification', 'decision_journal', 'forum_result']}
        entry.update(index=rel(INDEX), completed_utc=NOW, new_fits=0, new_models=0, new_bootstrap=0)
        obj['completed_units'].append(entry)
        obj.update(updated_utc=NOW, latest_completed_unit=entry,
                   latest_B19_stability_audit_index=rel(INDEX), latest_artifact_diagnostic=entry,
                   next_artifact_diagnostic=next_step,
                   no_retraining_or_suite_repetition_for_completed_B19_stability=True)
        if ours:
            obj['current_unit'] = None
        if not foreign:
            obj['status'] = 'scheduled_' + str(len(obj['completed_units'])) + '_units_B19_artifact_audit_verified_conditions_open'
            obj['next_unit_before_B19_artifact_audit'] = obj.get('next_unit')
            obj['next_unit'] = next_step
        warnings = {x['id']: x for x in obj['open_conditions']}
        for item in i['warnings']:
            assert item['id'] not in warnings, item['id']
            warnings[item['id']] = item
        obj['open_conditions'] = list(warnings.values())
        obj['integration_decisions']['B19_saved_artifact_stability'] = (
            'Building coverage ratio crosses1; no single evaluationgroup deletion removes building loss. '
            'Motornew oneTPOnly injury group concentrates56.1%gross adverse loss, segment-only reversal '
            'after evaluation deletion. LocalH^-1G approximate, no coefficient adoption or price. '
            'No data deletion, model promotion or additional fit.')
        obj.setdefault('condition_progress_without_auto_closure', {})['DEV8-INFLUENCE'] = (
            'Saved2023 coefficients and distinct training/OOF influence mechanisms audited. '
            'Source trace and local approximation limitations remain open; no automatic condition closure.')
        return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'

    change(NIGHT, night)

    def routes(raw):
        for key, value in [('week_2_b19_stability_index', rel(INDEX)),
                           ('week_2_b19_stability_report', i['documentation']),
                           ('week_2_b19_stability_plan', i['plan'])]:
            raw = top(raw, key, value, True)
        return raw
    change(ROOT / 'RUTAS_PROYECTO.json', routes)

    def state(raw):
        obj = json.loads(raw)
        current_night = read(NIGHT)
        dev = dict(i, as_of_utc=NOW, rows=50094, groups=30869, folds=5,
                   producer_checks=producer['passed'], verification_checks=verifier['passed'],
                   readout_checks=reconciliation['passed'], new_prices_from_altered_coefficients=0,
                   confirmation_opened_by_this_task=False, external2024_artifacts_read_this_unit=False,
                   complete_blindness_claim_allowed=False, no_group_removed=True,
                   building_coverage_ratio_range=[0.794772, 1.387842],
                   building_deltaD2_B19_minus_B14=-0.0127426242986,
                   motor_new_deltaD2_B19_minus_B14=-0.0217771397119,
                   motor_new_top_adverse_gross_share=0.561015,
                   motor_new_one_group_evaluation_deletion_deltaD2=0.00976589199,
                   global_after_that_component_evaluation_deletion_deltaD2=-0.00242978854)
        continuity = dict(obj['week_2_nocturnal_continuation_20261023'],
                          as_of_utc=NOW, latest_artifact_diagnostic=rel(INDEX),
                          next_artifact_diagnostic=next_step)
        collab = dict(obj['collaboration_forum'], updated_utc=NOW,
                      latest_Codex_comment='COD-S2-20261024-037')
        updates = [('memory_as_of', datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),
                   ('week_2_nocturnal_continuation_20261023', continuity), ('collaboration_forum', collab)]
        if current_night.get('current_unit') is None:
            phase = {'as_of_utc': NOW, 'phase': 'B19_saved2023_stability_audited_without_refit_own2024closed',
                     'current_state_key': STATEKEY,
                     'historical_fields_notice': 'Dated cuts retained; concurrent B20 and other branches preserved. This audit adds zero fits and does not replace the active model catalog.'}
            updates.append(('current_phase', phase))
        for key, value in updates:
            raw = top(raw, key, value)
        return top(raw, STATEKEY, dev, True)
    change(ROOT / 'Preparación/ESTADO_PROYECTO.json', state)
    note = f'''

## B19: estabilidad e influencia con artefactos guardados de 2023

Codex, corte UTC {NOW}. El participante pidió revisar coeficientes y grupos en B19, con foco en edificios y autos nuevos, sin reentrenar. Plan S2-B19-ESTABILIDAD2023-v1-20261024, comentario previo 036 a las 01:47:58 UTC y resultado 037 a las 01:57:49 UTC. Informe ESTABILIDAD_E_INFLUENCIA_B19_2023.md e índice semana2_b19_estabilidad_actual.json en el repositorio común. Se conservan B00, B14, B19 y todas las alternativas. Esta unidad añade cero ajustes, modelos y bootstrap; tampoco predice o puntúa con coeficientes alterados. El catálogo y contador activos se leen como corte y se preservan; otros chats avanzaron por separado y no se atribuyen sus ajustes a esta auditoría.

Se comparan 15 modelos guardados de B19 con 15 de B14 en escala original y referencias comunes, sobre los cinco folds ya guardados de 50.094 periodos y 30.869 componentes de 2023. Los cinco ajustes solapan y no son cinco réplicas independientes. La razón de tasa de daño accidental sí/no en edificios va de 0,795 a 1,388 y cambia dirección. Third_party_only/comprehensive en autos va de 0,567 a 0,857, frente a 0,587–0,611 en third_party_fire_theft. No se convierte la dispersión entre folds en intervalo de confianza o prueba causal de un siniestro.

Edificios tiene delta D² B19 menos B14 de −0,012743. Ninguna retirada individual de evaluación lo vuelve positivo. Los cinco componentes más adversos son incendios; suman 1.237.635,60 CU de T0 y 31,5% de pérdida bruta adversa. Retirar de evaluación 1/5/10/31 adversos deja −0,009127/−0,002984/+0,000851/+0,006178; retirar favorables empeora el contraste. Son sensibilidades a posteriori, sin borrar registros o seleccionar una limpieza por score.

Autos nuevos tiene delta −0,021777. Un componente de una fila, third_party_only y lesiones corporales, con T0 136.767,16 CU, aporta 56,1% de pérdida bruta adversa. Al retirarlo solo de evaluación, el contraste del segmento pasa a +0,009766; al retirar su componente completo el global del portafolio sigue negativo, −0,002430. No se mezclan ambas escalas. El coste esperado de periodo guardado es 90,25 CU en B19 y 132,77 CU en B14; no son severidades ni indican que la tarifa deba igualar el siniestro observado. El grupo no entrena el fold que lo valida y aparece en los otros cuatro ajustes.

La influencia sobre parámetros usa la aproximación local H inversa por el gradiente del grupo, con Hessiano completo, transformaciones y C0 fijos. No es un reajuste al borrar datos. En autos, el cambio local del logcoeficiente de third_party_only para el componente destacado va de −0,223 a −0,245 en los cuatro ajustes donde participa. En edificios un incendio de 286.093 CU lidera la influencia absoluta sobre AD en cuatro ajustes. El leverage y los cambios grandes limitan la aproximación; no se atribuye el cambio de un fold exclusivamente a un grupo ni se generan precios con betas alteradas.

Pasaron 24 controles del productor, 629 verificaciones por otro método y 112 conciliaciones de lectura, con solapamiento. Se cotejaron identidades de escala, deviance por otra fórmula y por filas con sklearn, influencia por Cholesky y derivadas direccionales. El flujo real rechaza T0 distinto entre modelos antes de calcular Hessianos y conserva el fallo esperado. La guarda inicial exigía nueve unidades ya terminadas, pero encontró diez por trabajo concurrente: detuvo la preinscripción; los intentos dependientes fallaron por archivos ausentes, sin cálculos o ajustes. Se corrigió la conciliación antes del plan registrado, preservando el trabajo ajeno.

Queda pendiente cotejar pagado, reservas, recuperaciones, estado y fechas de los componentes destacados. Esta evidencia no justifica otra tanda, borrar siniestros caros, promover o retirar modelos o congelar la lista final. Los resultados son exploratorios tras investigación adaptativa, revisión técnica propia y no validación profesional independiente. 2024 y test siguen cerrados en este trabajo, incluidas predicciones, scores, actas y ledger. La exposición previa a un título externo ya fue declarada; no se repiten o usan cifras ni se afirma ceguera completa. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La ventana nocturna conserva el corte de las 07:00 Bogotá.
'''
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        change(ROOT / 'Preparación' / filename, lambda raw: raw + note)
    update = ('\n\n## B19: estabilidad sin reentrenar\n\n'
              'La [revisión de artefactos](../Repositorio_IAA2026/docs/semana2/ESTABILIDAD_E_INFLUENCIA_B19_2023.md) '
              'encuentra cambio de signo de cobertura en edificios y concentración del deterioro de autos nuevos '
              'en un componente de lesiones corporales. Distingue error OOF de influencia local sobre otros ajustes; '
              'ningún grupo individual explica todo el deterioro de edificios. Cero ajustes o bootstrap nuevos. '
              'B00 y todas las alternativas conservados, catálogo activo sin sustituir. Siguiente paso: trazabilidad '
              'de pagado, reservas, recuperaciones, estados y fechas de los componentes, antes de otra receta. '
              '2024 cerrado en este trabajo. Foro 036/037.\n')
    for filename in ['README.md', 'PLAN_TRABAJO.md']:
        change(ROOT / 'Hackaton/Semana 2' / filename, lambda raw: raw + update)
    short = ('\n\n## Diagnóstico posterior de B19 con artefactos guardados\n\n'
             'La [revisión de estabilidad e influencia](ESTABILIDAD_E_INFLUENCIA_B19_2023.md) '
             'termina sin ajustes, modelos o bootstrap nuevos. La cobertura de edificios cambia dirección entre '
             'folds; ninguna retirada individual de evaluación revierte su deterioro. En autos nuevos un grupo '
             'concentra 56,1% de pérdida bruta adversa; su retirada de evaluación revierte el segmento, pero '
             'el portafolio continúa negativo. No se borra ningún registro ni se adopta una beta alterada. '
             'La influencia local del GLM es aproximada y se distingue de su error OOF. B00 y todas las '
             'alternativas se conservan, sin reemplazar el catálogo que actualizan otras continuaciones. '
             'Próximo trabajo: trazabilidad de pagado, reservas, recuperaciones, estado y fechas de esos grupos, '
             'con artefactos de 2023. Foro 036/037; 2024 cerrado en este trabajo. Balance parcial hasta las '
             '07:00 Bogotá.\n')
    for filename in ['PLAN_NOCTURNO_20261023.md', 'BALANCE_NOCTURNO_PARCIAL_20261024.md', 'GLM_COBERTURAS_2023.md']:
        change(REPO / 'docs/semana2' / filename, lambda raw: raw + short)
    readiness = REPO / 'registro/semana2_listo_entrenar.json'
    change(readiness, lambda raw: top(raw, 'latest_B19_saved_artifact_diagnostic', {
        'utc': NOW, 'index': rel(INDEX), 'documentation': i['documentation'], 'new_fits': 0,
        'new_bootstrap': 0, 'altered_coefficient_prices': 0, 'next_artifact_step': next_step,
        'reference': 'W2-B00', 'all_alternatives_preserved': True, 'confirmation_opened_by_this_task': False,
        'ledger_read': False, 'complete_blindness_claim_allowed': False}, add=True))
    tests = REPO / 'registro/semana2_b19_estabilidad2023_pruebas_v1.json'
    dump(tests, {'author': 'Codex', 'utc': NOW, 'producer': i['report'], 'verification': i['verification'],
                 'readout_reconciliation': i['readout_reconciliation'],
                 'counts': [producer['passed'], verifier['passed'], reconciliation['passed']],
                 'counts_overlap': True, 'expected_failure_runs': verifier['expected_failure_runs'],
                 'fit_calls': 0, 'new_models': 0, 'new_bootstrap': 0,
                 'local_influence_not_actual_deletion_refit': True, 'professional_independent_validation': False})
    dump(RUN / 'forum_receipts.json', {'source': 'Serialized helper outputs in this chat', 'receipts': [
        {'id': 'COD-S2-20261024-036', 'utc': '2026-10-24T01:47:58+00:00',
         'previous_sha256': 'c32ae0497975824b11b95f06da09819939a3143d215ccc275dd1a739abd5fe67',
         'sha256_at_append': 'cf0ba517c9f1a7718becc8b1803fa72171a2f07ca1a629767cd2a91021283bb7'},
        {'id': 'COD-S2-20261024-037', 'utc': '2026-10-24T01:57:49+00:00',
         'previous_sha256': 'cf0ba517c9f1a7718becc8b1803fa72171a2f07ca1a629767cd2a91021283bb7',
         'sha256_at_append': '4dfcb32c7332ce230ce733d29fedebbd9ea138fb13de562ca3183f2cadd09a11'}]})
    dump(RUN / 'registration.json', {'author': 'Codex', 'utc': NOW, 'changes': changes,
        'unrelated_indices_and_counters_cut': untouched, 'counter_values_cut': counter_values,
        'concurrency': 'Compare-and-replace with exact backups, dynamic completed-unit count; preserve foreign current unit and all old state branches/routes. No active model index or counter writes.',
        'new_fits': 0, 'new_models': 0, 'new_bootstrap': 0, 'ledger_read': False,
        'confirmation_opened_by_this_task': False})
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
    for key in ['report', 'verification', 'readout', 'readout_reconciliation', 'assessment', 'decision_journal', 'manifest']:
        check('Index receipt ' + key, sha(ROOT / i[key]['path']) == i[key]['sha256'])
    check('Documentation exact', sha(ROOT / i['documentation']) == i['documentation_sha256'])
    for source in p['frozen_sources']:
        check('Frozen source ' + source['path'], sha(ROOT / source['path']) == source['sha256'])
    for item in read(RUN / 'manifest.json')['files']:
        check('Producer artifact ' + item['path'], sha(ROOT / item['path']) == item['sha256'])
    # These are mutable shared pointers. A later concurrent change is recorded, never undone.
    pointer_changes = {path: {'before': before, 'now': sha(ROOT / path)}
                       for path, before in untouched.items() if sha(ROOT / path) != before}
    check('No active model index or counter was written by this audit',
          not set(untouched).intersection(item['path'] for item in changes))
    oldstate = read(BACK / 'Preparación/ESTADO_PROYECTO.json')
    newstate = read(ROOT / 'Preparación/ESTADO_PROYECTO.json')
    allowed = {'current_phase', 'memory_as_of', 'collaboration_forum', 'week_2_nocturnal_continuation_20261023'}
    check('Historical state branches exact', all(newstate.get(k) == v for k, v in oldstate.items() if k not in allowed))
    oldroutes = read(BACK / 'RUTAS_PROYECTO.json')
    newroutes = read(ROOT / 'RUTAS_PROYECTO.json')
    check('Earlier routes exact', all(newroutes.get(k) == v for k, v in oldroutes.items()))
    for key in ['week_2_b19_stability_index', 'week_2_b19_stability_report', 'week_2_b19_stability_plan']:
        check('New route ' + key, (ROOT / newroutes[key]).exists())
    for item in changes:
        if item['path'].endswith('.md'):
            check('Prose prefix ' + item['path'], (ROOT / item['path']).read_bytes().startswith((ROOT / item['backup']).read_bytes()))
    for doc in [ROOT / i['documentation'], REPO / 'docs/semana2/GLM_COBERTURAS_2023.md',
                REPO / 'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md', REPO / 'docs/semana2/PLAN_NOCTURNO_20261023.md',
                ROOT / 'Hackaton/Semana 2/README.md', ROOT / 'Hackaton/Semana 2/PLAN_TRABAJO.md']:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8-sig')):
            target = link.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', target):
                continue
            check('Link ' + rel(doc) + ' -> ' + target, (doc.parent / unquote(target)).resolve().exists())
    current = read(NIGHT)
    old = read(BACK / NIGHT.relative_to(ROOT))
    check('Own unit complete exactly once', sum(x['id'] == p['id'] for x in current['completed_units']) == 1)
    check('Earlier completed units preserved', current['completed_units'][:len(old['completed_units'])] == old['completed_units'])
    check('Only own current unit cleared', current['current_unit'] == (None if (old.get('current_unit') or {}).get('id') == p['id'] else old['current_unit']))
    for key in ['window_start', 'window_end', 'frequency', 'automation_id', 'automation_kind', 'automation_target_thread',
                'same_chat', 'other_automations_changed', 'forum_reading_guard', 'confirmation_header_exposure']:
        check('Schedule or guard preserved ' + key, current[key] == old[key])
    check('Old open conditions retained', all(x in current['open_conditions'] for x in old['open_conditions']))
    check('2024 closed in this work', current['confirmation_2024_open'] is False and newstate[STATEKEY]['ledger_read'] is False)
    check('Forum prefix preserved', forum.read_bytes().startswith(forum_cut))
    for path in verifier['expected_failure_runs']:
        check('Actual-flow expected failure archived ' + path, (ROOT / path / 'expected_adversary_failure.json').exists())
    result = {'utc': NOW, 'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'checks': checks, 'concurrent_pointer_changes': pointer_changes,
              'scope': 'Closing sources, indices, links and preservation only; no statistical suite or training repeated.'}
    dump(RUN / 'closure_verification.json', result)
    assert result['failed'] == 0, [x for x in checks if not x['pass']]
    paths = {x for x in RUN.rglob('*') if x.is_file()}
    paths.update(ROOT / x['path'] for x in changes)
    paths.update([INDEX, tests, ROOT / i['documentation'], ROOT / i['plan'], ROOT / p['code'], Path(__file__), forum])
    paths.update(REPO / 'herramientas' / f for f in ['verificar_estabilidad_b19_2023.py', 'documentar_estabilidad_b19_2023.py'])
    paths.update(ROOT / 'Hackaton/Semana 2/Codex' / f for f in [
        'preinscribir_estabilidad_b19_2023.py', 'estabilidad_b19_2023_preinscripcion.md',
        'estabilidad_b19_2023_resultado.md', 'catalogo_antes_estabilidad_b19.json',
        'contadores_antes_estabilidad_b19.json', 'nocturno_antes_estabilidad_b19.json'])
    for path in verifier['expected_failure_runs']:
        paths.update(x for x in (ROOT / path).rglob('*') if x.is_file())
    dump(RUN / 'closure_manifest.json', {'utc': NOW, 'notice': 'Dated cut; later shared appends do not invalidate historical evidence.',
        'files': [{'path': rel(x), 'sha256': sha(x), 'bytes': x.stat().st_size} for x in sorted(paths)],
        'new_fits': 0, 'new_models': 0, 'new_bootstrap': 0, 'reference': 'W2-B00'})
    print(json.dumps({'registered': rel(INDEX), 'closing_checks': result['passed'], 'failed': result['failed'],
                      'completed_units_at_cut': len(current['completed_units']), 'this_unit_fits': 0,
                      'counter_values_at_cut': counter_values, 'concurrent_pointer_changes': len(pointer_changes)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
