"""Cierra trazabilidad editorial de F0/último; no estima ni entrena modelos."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766'
BACK = RUN / 'state_before_selection_adenda'
NOW = datetime.now(timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def dump(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def top(raw, key, value):
    m = re.search(r'(?m)^  ' + re.escape(json.dumps(key)) + r':\s*', raw)
    assert m, key
    _, end = json.JSONDecoder().raw_decode(raw[m.end():])
    encoded = json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    return raw[:m.end()] + encoded + raw[m.end()+end:]


changes = []


def change(p, fn):
    before = p.read_bytes()
    backup = BACK / p.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as f:
        f.write(before)
    after = fn(before.decode('utf-8-sig')).encode('utf-8')
    stage = p.with_name(p.name + '.s2close.tmp')
    assert p.read_bytes() == before, 'Cambio concurrente: ' + str(p)
    with stage.open('xb') as f:
        f.write(after)
        f.flush()
        os.fsync(f.fileno())
    assert p.read_bytes() == before, 'Cambio concurrente: ' + str(p)
    os.replace(stage, p)
    changes.append({'path': rel(p), 'before_sha256': hashlib.sha256(before).hexdigest(),
                    'after_sha256': sha(p), 'backup': rel(backup)})


audit_path = ROOT / 'foros/validacion_ia_periodica/runs/20261023T170351Z_semana2/gate_adversarial_review.json'
audit = {'id': 'S2-AUD-METRIC-BINDING', 'status': 'open', 'evidence': rel(audit_path),
         'evidence_sha256': sha(audit_path), 'forum': 'COD-S2-IA-20261023-GATE',
         'consequence': 'No verified promotion; close semantic binding and independent metrics reconstruction before 2024 confirmation opening',
         'closed_by_this_task': False}
assert read(audit_path)['finding']['status'] == 'open'
BACK.mkdir(exist_ok=False)


def index_update(raw):
    obj = json.loads(raw)
    obj.update(status='ready_for_2023_development_only_2024_confirmation_closed',
               selection_gate_finding=audit, forum_readiness_condition='COD-S2-20261023-007',
               as_of_readiness_condition_utc=NOW)
    return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'


def contract_update(raw):
    obj = json.loads(raw)
    obj['validation']['selection_gate_finding'] = audit
    obj['validation']['confirmation_2024'] += ' Also requires documented closure of S2-AUD-METRIC-BINDING; hash identity alone is insufficient.'
    return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'


def state_update(raw):
    obj = json.loads(raw)
    phase = dict(obj['current_phase'])
    phase.update(as_of_utc=NOW, phase='week2_ready_for_2023_development_2024_confirmation_closed')
    section = dict(obj['week_2_variables_ultimate_20261023'])
    section.update(as_of_selection_adenda_utc=NOW, status='ready_for_2023_development_only_2024_confirmation_closed',
                   selection_policy=read(REPO/'registro/semana2_listo_entrenar.json')['selection_policy'],
                   selection_gate_finding=audit)
    section['readiness'] = dict(section['readiness'], development_2023_training=True,
                                confirmation_2024_open=False, promotion_ready=False)
    section['forum_decisions'] = section['forum_decisions'] + ['COD-S2-20261023-006', 'COD-S2-20261023-007']
    section['pending'] = section['pending'] + ['Freeze roster/recipes and statistical producer/checker before 2024 opening',
                                            'Close S2-AUD-METRIC-BINDING; finding remains open']
    forum = dict(obj['collaboration_forum'], latest_Codex_comment='COD-S2-20261023-007', updated_utc=NOW)
    for key, value in [('memory_as_of', datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),
                       ('current_phase', phase), ('week_2_variables_ultimate_20261023', section), ('collaboration_forum', forum)]:
        raw = top(raw, key, value)
    return raw


change(REPO/'registro/semana2_listo_entrenar.json', index_update)
change(REPO/'registro/semana2_contrato_entrenamiento.json', contract_update)
change(ROOT/'Preparación/ESTADO_PROYECTO.json', state_update)
adenda = '''

## S2-F0-ULT: integración de selección y condición abierta del selector

Codex, 23 de octubre de 2026. Precisión posterior al registro de variables/último: COD-S2-20261023-006 y COD-S2-20261023-007 incorporan la política común S2-SELECCION-v1 y el hallazgo abierto S2-AUD-METRIC-BINDING de COD-S2-IA-20261023-GATE. El desarrollo con 2023 puede empezar; la confirmación de modelos en 2024 sigue cerrada. La referencia W2-B00 y sus aspirantes usarán el mismo vínculo C0 de exposición efectiva, estimado solo en el ajuste. La referencia nominal de T0 queda como diagnóstico W2-D00-OBS separado de esa comparación primaria.

Antes de abrir 2024 se requieren lista, recetas y artefactos congelados, productor y comprobador de métricas desde predicciones congeladas y cierre documentado del vínculo semántico entre recibo y cifras consumidas por el selector. La revisión sintética encontró que comprobar el hash del recibo no acredita esa correspondencia. El hallazgo permanece abierto; este encargo no modifica el selector ni lo da por resuelto. La preparación no equivale a permiso de promoción, suficiencia de reservas o verdad última validada. Ningún entrenamiento de precios, apertura o promoción en este encargo. T0, folds, matrices y curvas actuariales conservan sus hashes. Índice: Hackaton/Repositorio_IAA2026/registro/semana2_listo_entrenar.json. Informe: docs/semana2/VARIABLES_Y_ULTIMO.md del repositorio común.
'''
change(ROOT/'Preparación/MEMORIA_PROYECTO.md', lambda raw: raw + adenda)
change(ROOT/'Preparación/DECISIONES.md', lambda raw: raw + adenda)
dump(RUN/'selection_adenda_registration.json', {'utc': NOW, 'changes': changes, 'models_trained': 0})

receipts = [
    ('004', '2026-10-23T17:05:17+00:00', '86553c78', 'bce8f12f0b555fe304118e88b8123b9fdbed7994822ff3dab11b3ea243f85bd5'),
    ('005', '2026-10-23T17:22:53+00:00', '2602a19311e5278a74a1bfa5aeaab2ee1b63a578c15f44d8c668a53e5132ec20', '3cc10aab2db11e714ebf124c56b4c1cb8bf8d944d59f978d11a24ed5396772ec'),
    ('006', '2026-10-23T17:26:01+00:00', '849c9dfe01d474ffcea8ee9d32416061a0d33cbd95acb24fe17d2abe3442c889', 'c54c816823f2002ea2a39974dadc3e443648a803e482839c04235ce8c9979881'),
    ('007', '2026-10-23T17:29:28+00:00', 'c54c816823f2002ea2a39974dadc3e443648a803e482839c04235ce8c9979881', '2008d25134b0d07109abfe656bc963191a67479310e85d2125ef4c1c1a00c3ea')
]
dump(RUN/'forum_receipts.json', {'author': 'Codex', 'source': 'Serialized helper outputs observed during task; 004 previous hash retained only as prefix in closing summary',
    'receipts': [{'id': 'COD-S2-20261023-'+i, 'utc': t,
                  ('previous_sha256' if len(prev)==64 else 'previous_sha256_prefix'): prev,
                  'sha256_at_append': after} for i,t,prev,after in receipts]})

# Son controles de integridad y coherencia editorial. No vuelven a estimar curvas.
checks = []
def check(name, passed):
    checks.append({'name': name, 'pass': bool(passed)})

index = read(REPO/'registro/semana2_listo_entrenar.json')
base = read(REPO/'registro/semana2_preparacion_actual.json')
manifest = read(RUN/'manifest.json')
for item in manifest['files']:
    check('Frozen output '+item['path'], sha(RUN/item['path']) == item['sha256'])
for path, expected in manifest['input_sha256'].items():
    check('Original '+path, sha(ROOT/'Hackaton/Semana 2'/path) == expected)
for path_key, hash_key in [('producer','producer_sha256'), ('plan','plan_sha256'), ('report','report_sha256'),
                           ('availability_contract','availability_sha256')]:
    check(path_key+' current hash', sha(ROOT/index[path_key]) == index[hash_key])
for path_key, hash_key in [('target','target_sha256'), ('partitions','partitions_sha256')]:
    check('Base '+path_key+' hash', sha(ROOT/base[path_key]) == base[hash_key])
policy = index['selection_policy']
check('Policy hash stable', sha(ROOT/policy['path']) == policy['sha256'])
sel_index = read(REPO/'registro/semana2_seleccion_actual.json')
check('Selector source unchanged', sha(ROOT/sel_index['gate_workspace_relative']) == sel_index['gate_sha256'])
check('No real confirmation ledger created at close', not (ROOT/sel_index['ledger_workspace_relative']).exists())
check('Readiness limited to development', index['readiness']['development_2023_training'] and
      not index['readiness']['confirmation_2024_open'] and not index['readiness']['promotion_ready'])
check('No pricing training in preparation', index['price_models_trained'] == 0 and index['price_model_inference'] == 0)
check('Selector finding remains open', index['selection_gate_finding']['status'] == 'open')
routes = read(ROOT/'RUTAS_PROYECTO.json')
for key,path in routes.items():
    if key.startswith('week_2_'):
        check('Route '+key, (ROOT/path).exists())
old_routes = read(RUN/'state_before_registration/RUTAS_PROYECTO.json')
check('Earlier route values preserved', all(routes.get(k)==v for k,v in old_routes.items()))
for changed in changes:
    path = ROOT/changed['path']
    if path.suffix == '.md':
        check('Previous prose prefix preserved '+rel(path), path.read_bytes().startswith((ROOT/changed['backup']).read_bytes()))
before_state = read(BACK/'Preparación/ESTADO_PROYECTO.json')
after_state = read(ROOT/'Preparación/ESTADO_PROYECTO.json')
allowed = {'memory_as_of','current_phase','collaboration_forum','week_2_variables_ultimate_20261023'}
check('Other state records preserved', all(after_state.get(k)==v for k,v in before_state.items() if k not in allowed))
forum = ROOT/'Hackaton/Semana 2/Foro/FORO.md'
forum_text = forum.read_text(encoding='utf-8')
for i,t,prev,after in receipts:
    check('Unique forum ID '+i, forum_text.count('<!-- aporte:COD-S2-20261023-'+i+' -->') == 1)
check('Preregistered before materialization', datetime.fromisoformat(receipts[0][1]) < datetime.fromisoformat(read(RUN/'report.json')['started_utc']))
check('Results after separate verification', '20261023T171434Z' < '20261023T172253Z')
for doc in [REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md', ROOT/'Hackaton/Semana 2/README.md', ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md', forum]:
    for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
        dest = link.strip('<>').split('#')[0]
        if not dest or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', dest):
            continue
        check('Local link '+rel(doc)+' -> '+dest, (doc.parent/unquote(dest)).resolve().exists())
result = {'utc': NOW, 'scope': 'Integrity/metadata closure only, no rerun of actuarial/price fitting',
          'checks': checks, 'passed': sum(c['pass'] for c in checks),
          'failed': sum(not c['pass'] for c in checks)}
dump(RUN/'closure_verification.json', result)
assert result['failed'] == 0, [c for c in checks if not c['pass']]

paths = set(RUN.rglob('*'))
paths.update(ROOT/c['path'] for c in changes)
paths.update([Path(__file__), ROOT/'RUTAS_PROYECTO.json', REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md',
              REPO/'src/semana2/variables_ultimo.py', REPO/'registro/semana2_variables_ultimo_plan.json',
              REPO/'herramientas/probar_variables_ultimo_semana2.py', REPO/'herramientas/verificar_variables_ultimo_semana2.py',
              REPO/'herramientas/comprobar_contrato_entrenamiento_semana2.py',
              REPO/'registro/semana2_variables_ultimo_pruebas.json', REPO/'registro/semana2_contrato_entrenamiento_comprobacion.json',
              ROOT/policy['path'], ROOT/sel_index['gate_workspace_relative'], audit_path, forum])
dump(RUN/'closure_manifest.json', {'utc': NOW, 'notice': 'Current closing cut; earlier manifests remain historical. Shared files may change later.',
     'files': [{'path': rel(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths) if p.is_file()],
     'pricing_training_performed': False, 'confirmation_opened': False, 'selector_finding_closed': False})
print(json.dumps({'integrity_checks': result['passed'], 'failed': result['failed'], 'run': rel(RUN),
                  'development_2023_ready': True, 'confirmation_2024_open': False, 'models_trained': 0}))
