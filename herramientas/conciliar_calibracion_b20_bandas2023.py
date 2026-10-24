"""Conciliación de registros y lectura final; respeta unidades concurrentes."""
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()


def main():
    run = REPO/'privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1'
    output = run/'closure_verification.json'
    assert not output.exists(), 'Cierre existente'
    p, r = read(run/'plan_snapshot.json'), read(run/'report.json')
    idx = read(REPO/'registro/semana2_b20_bandas_calibracion_actual.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    for name in ['report', 'readout', 'verification', 'fixtures', 'decision_journal', 'manifest']:
        item = idx[name]
        check('Current SHA '+name, sha(ROOT/item['path']) == item['sha256'])
    check('Allfrozenmodelsdataandcounter', all(sha(ROOT/item['path']) == item['sha256'] for item in p['frozen_sources']))
    check('Checksandfixturespassed', read(ROOT/idx['verification']['path'])['failed'] == read(ROOT/idx['fixtures']['path'])['failed'] == 0)
    routes = read(ROOT/'RUTAS_PROYECTO.json')
    check('Diagnosticroutes', routes['week_2_b20_calibration_bands_report'] == idx['documentation'] and routes['week_2_b20_calibration_bands_plan'] == idx['plan'] and (ROOT/routes['week_2_b20_calibration_bands_index']).exists())
    night = read(ROOT/routes['week_2_night_index'])
    own = [x for x in night['completed_units'] if x['id'] == p['id']]
    check('Completedonce', len(own) == 1 and own[0]['verification'] == idx['verification'])
    check('Scheduledwindowpreserved', night['window_end'] == '2026-10-24T07:00:00-05:00' and night['frequency'] == 'hourly_at_minute_zero' and night['submission_platform_incident']['topic_id'] == 752144)
    model = read(ROOT/routes['week_2_development_index'])
    counter = read(ROOT/routes['week_2_own_fit_counters'])
    check('Modelsandcounter195285', len(model['models_consulted']) == 21 and model['reference'] == 'W2-B00' and not model['promotion'] and counter['cumulative_price_base_fits'] == 195 and counter['cumulative_closed_form_constants'] == 285)
    doc = (ROOT/idx['documentation']).read_text(encoding='utf-8')
    table = read(run/'readout.json')['rows']
    for line, title in [('motor', 'Autos'), ('buildings', 'Edificios'), ('contents', 'Contenidos')]:
        formatted = [f"{x['B20_AE']:.3f}".replace('.', ',') for x in table if x['line'] == line]
        check('Bandtable '+line, '| '+title+' | '+' | '.join(formatted)+' |' in doc)
    forum = (ROOT/routes['week_2_forum']).read_text(encoding='utf-8-sig')
    for ident in [p['forum_prior'], p['forum_result']]:
        check('Ownforumpost '+ident, forum.count('<!-- aporte:'+ident+' -->') == 1)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        text = (ROOT/'Preparación'/name).read_text(encoding='utf-8-sig')
        check('Ownmemory '+name, text.count('## S2-B20-BANDAS-CALIBRACION2023-v1-20261024:') == 1)
    state = read(ROOT/routes['state'])['semana2_b20_bandas_calibracion2023_20261024']
    check('Ownstateclosed', state['2024_test_closed'] and state['new_fits'] == 0 and not state['promotion'])
    check('Fitonlycutsandnotrain', all(not x['labels_used_for_edges'] for x in read(run/'band_cuts.json')) and r['new_fits'] == r['new_bootstrap'] == r['new_model_recipes'] == r['new_test_prices'] == 0 and r['2024_test_closed'] and not r['ledger_read'])
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'passed': sum(x['pass'] for x in checks),
              'failed': sum(not x['pass'] for x in checks), 'checks': checks, 'new_fits': 0,
              'current_unit_id_read_only': (night.get('current_unit') or {}).get('id'), 'current_unit_not_modified': True,
              'professional_independent_validation': False}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'new_fits': 0, 'other_current_unit_preserved': True}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
