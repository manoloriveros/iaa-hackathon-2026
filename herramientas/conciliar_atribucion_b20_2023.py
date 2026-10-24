"""Conciliación de cierre que preserva una continuación concurrente posterior."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    run = REPO/'privado/semana2/desarrollo2023/b20_atribucion_20261024_v1a'
    output = run/'closure_verification.json'
    assert not output.exists(), 'Cierre ya conservado'
    p, r = read(run/'plan_snapshot.json'), read(run/'report.json')
    idx = read(REPO/'registro/semana2_b20_atribucion_actual.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    for name in ['report', 'verification', 'fixtures', 'manifest', 'decision_journal']:
        q = idx[name]
        check('Index SHA '+name, sha(ROOT/q['path']) == q['sha256'])
    check('Finalcorrectedcheck', read(ROOT/idx['verification']['path'])['failed'] == 0 and idx['verification']['passed'] == 1014)
    check('Initialfailedcheckpreserved', read(run/'verification.json')['failed'] == 10 and (run/'checker_first_attempt_code.py').exists())
    check('Sourcecounterandmodelsunchanged', all(sha(ROOT/x['path']) == x['sha256'] for x in p['frozen_sources']))
    models = read(REPO/'registro/semana2_desarrollo2023_actual.json')
    check('Modelcataloguntouched', models['id'] == 'S2-GLM-RIDGE-COBERTURAS2023-v1-20261024' and models['models_consulted'] == [f'W2-B{i:02d}' for i in range(21)] and not models['promotion'])
    n = read(REPO/'registro/semana2_continuidad_nocturna.json')
    own = [x for x in n['completed_units'] if x['id'] == p['id']]
    check('Owncompletionpreservedonce', len(own) == 1 and own[0]['run'] == idx['run'] and own[0]['verification'] == idx['verification'])
    check('Nootherwindowchange', n['window_end'] == '2026-10-24T07:00:00-05:00' and n['submission_platform_incident']['topic_id'] == 752144)
    routes = read(ROOT/'RUTAS_PROYECTO.json')
    check('Diagnosticroutes', (ROOT/routes['week_2_b20_attribution_index']).exists() and routes['week_2_b20_attribution_report'] == idx['documentation'] and routes['week_2_b20_attribution_plan'] == idx['plan'])
    forum = (ROOT/routes['week_2_forum']).read_text(encoding='utf-8-sig')
    for ident in [p['forum_prior'], p['forum_amendment'], p['forum_result']]:
        check('Ownforumpost '+ident, forum.count('<!-- aporte:'+ident+' -->') == 1)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        text = (ROOT/'Preparación'/name).read_text(encoding='utf-8-sig')
        check('Ownmemory '+name, text.count('## S2-B20-ATRIBUCION2023-v1a-20261024:') == 1)
    check('Noextramodelorbootstrap', r['new_fits'] == r['new_price_predictions'] == r['new_candidate_recipes'] == 0 and not r['bootstrap_repeated'])
    check('Signexplanationallpairs', all(x['all']['gain'] > 0 and x['selected31']['gain'] > x['all']['gain'] and x['remaining']['gain'] < 0 and x['remaining']['null_deviance'] > 0 for x in r['summary']))
    check('Closedtime_scope', '2024/test' in idx['scope'] and 'closed' in r['scope_2024_test'])
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks), 'checks': checks,
              'current_unit_id_read_only': (n.get('current_unit') or {}).get('id'),
              'current_unit_not_modified': True, 'new_fits': 0, 'bootstrap_repeated': False,
              'professional_independent_validation': False}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'current_unit_preserved': True, 'new_fits': 0}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
