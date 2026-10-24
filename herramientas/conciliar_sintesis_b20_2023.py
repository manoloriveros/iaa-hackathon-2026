"""Cierre documental propio; nunca exige que otra unidad siga inactiva."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_sintesis_20261024_v1'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output = RUN / 'closure_verification.json'
    assert not output.exists(), 'Cierre existente.'
    ip = REPO / 'registro/semana2_b20_sintesis_actual.json'
    idx, p = read(ip), read(RUN / 'plan_snapshot.json')
    checks = []

    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})

    for name in ['report', 'verification', 'decision_journal', 'evidence_gaps', 'manifest']:
        item = idx[name]
        check('Registered SHA ' + name, sha(ROOT / item['path']) == item['sha256'])
    check('Report SHA', sha(ROOT / idx['documentation']) == idx['documentation_sha256'])
    check('Verification passed', read(ROOT / idx['verification']['path'])['failed'] == 0)
    manifest = read(RUN / 'manifest.json')
    check('All output SHA', all(sha(ROOT / x['path']) == x['sha256'] for x in manifest['outputs']))
    check('Code snapshots exact', all(sha(ROOT / x['path']) == x['sha256'] for x in manifest['code_snapshots']))
    routes = read(ROOT / 'RUTAS_PROYECTO.json')
    check('Routes', routes['week_2_b20_synthesis_index'] == ip.relative_to(ROOT).as_posix()
          and routes['week_2_b20_synthesis_report'] == idx['documentation'] and routes['week_2_b20_synthesis_plan'] == idx['plan'])
    night = read(REPO / 'registro/semana2_continuidad_nocturna.json')
    units = [x for x in night['completed_units'] if x['id'] == idx['id']]
    check('Own unit completed once', len(units) == 1 and units[0]['verification'] == idx['verification'])
    check('No repeat marker', night['no_repetition_for_completed_b20_synthesis']
          and night['latest_b20_synthesis_index'] == routes['week_2_b20_synthesis_index'])
    registration = read(RUN / 'registration_receipt.json')
    check('Concurrent unit preserved at write', registration['preserved_other_current_unit'])
    check('Window and frequency', night['window_end'] == registration['window_end'] == '2026-10-24T07:00:00-05:00'
          and night['frequency'] == registration['frequency'] == 'hourly_at_minute_zero')
    check('Kaggle incident preserved', night['submission_platform_incident']['topic_id'] == 752144)
    frozen = {x['path']: x for x in p['frozen_sources']}
    for name in ['semana2_contadores_propios_actual.json', 'semana2_desarrollo2023_actual.json',
                 'semana2_glm_ridge_actual.json', 'semana2_politica_seleccion_v1.json']:
        path = 'Hackaton/Repositorio_IAA2026/registro/' + name
        check('Unchanged ' + name, sha(ROOT / path) == frozen[path]['sha256'])
    forum = (ROOT / 'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8-sig')
    for name in ['forum_prior', 'forum_result']:
        check('Own forum ID ' + name, forum.count('<!-- aporte:' + idx[name] + ' -->') == 1)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        memory = (ROOT / 'Preparación' / filename).read_text(encoding='utf-8-sig')
        check('Own marker ' + filename, memory.count('## ' + idx['id'] + ':') == 1)
    state = read(ROOT / 'Preparación/ESTADO_PROYECTO.json')['semana2_b20_sintesis2023_20261024']
    check('Own state', state['decisions'] == 9 and state['unresolved_gates'] == 6
          and state['2024_test_closed'] and state['new_fits'] == state['new_inference'] == 0)
    docpath = ROOT / idx['documentation']
    doc = docpath.read_text(encoding='utf-8')
    links = re.findall(r'\]\(([^)]+)\)', doc)
    check('Local evidence links exist', all((docpath.parent / x).resolve().is_file() for x in links))
    check('No promotion or new work', not idx['promotion'] and not idx['next_model_selected']
          and idx['reference'] == 'W2-B00' and idx['all_alternatives_preserved']
          and all(idx[x] == 0 for x in ['new_fits', 'new_inference', 'new_bootstrap', 'new_recipes']))
    result = {'id': idx['id'], 'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'checks': checks, 'current_unit_read_only': (night.get('current_unit') or {}).get('id'),
              'no_assumption_that_current_unit_is_empty': True, 'new_fits': 0, 'new_inference': 0,
              'checker_sha256': sha(Path(__file__)), 'professional_independent_validation': False}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not result['failed']:
        idx['closure_verification'] = {'path': output.relative_to(ROOT).as_posix(), 'sha256': sha(output),
                                       'passed': result['passed'], 'failed': 0}
        ip.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'new_fits': 0, 'new_inference': 0}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
