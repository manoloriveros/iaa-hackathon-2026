"""Registra la tanda terminada, preservando cortes y cambios concurrentes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
import re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
INDEX=REPO/'registro/semana2_desarrollo2023_actual.json';DOC=REPO/'docs/semana2/DESARROLLO_2023.md'
BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
NOW=datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value,add=False):
    encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():])
    return raw[:m.end()]+encoded+raw[m.end()+end:]

changes=[]
def change(p,fn):
    before=p.read_bytes();backup=BACK/p.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8')
    stage=p.with_name(p.name+'.s2dev.tmp')
    assert p.read_bytes()==before,'Cambio concurrente: '+str(p)
    with stage.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==before,'Cambio concurrente: '+str(p)
    os.replace(stage,p)
    changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p),'backup':rel(backup)})

index=read(INDEX);report=read(RUN/'report.json')
assert read(ROOT/index['verification']['path'])['failed']==0
forum_path=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_before=forum_path.read_bytes()
assert forum_before.count(b'<!-- aporte:COD-S2-20261023-009 -->')==1
selection=read(REPO/'registro/semana2_seleccion_actual.json')
assert not (ROOT/selection['ledger_workspace_relative']).exists()
assert sha(ROOT/selection['policy']['path'])==selection['policy']['sha256']

def routes(raw):
    for key,path in {'week_2_development_index':INDEX,'week_2_development_report':DOC,
                     'week_2_development_plan':ROOT/index['plan'],'week_2_development_oof':ROOT/index['oof']}.items():
        assert path.exists();raw=top(raw,key,rel(path),add=True)
    return raw

def state(raw):
    before=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_first_2023_price_batch_verified_2024_confirmation_closed',
           'current_state_key':'week_2_development2023_v1_20261023',
           'historical_fields_notice':'Los contadores de preparación y de encargos anteriores conservan su corte. La primera ejecución de precios está en semana2_desarrollo2023_actual.json.'}
    section={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(INDEX),'documentation':rel(DOC),
        'run':rel(RUN),'training_years':[2023],'scored_years':[2023],'OOF_rows_per_recipe':50094,
        'groups':30869,'folds':5,'price_estimators_fitted':30,'closed_form_constants':15,'fit_nodes':45,
        'results_D2':{x['model_id']:x['D2'] for x in report['summary']},
        'reference_retained':'W2-B00','alternatives_preserved':['W2-B01','W2-B02'],
        'promotion':False,'confirmation_2024_open':False,'final_confirmation_roster_frozen':False,
        'selector_finding':'S2-AUD-METRIC-BINDING open; no closure attributed by this task',
        'verification':index['verification'],'forum_decisions':[index['forum_prior'],index['forum_result']],
        'pending':['Investigate GLM line differences and boosting generalization/level in preregistered 2023 work',
                   'Selector semantic fix and separate contrast; metrics producer/checker; final roster/recipes/artifacts freeze before any 2024 opening',
                   'Human review and ultimate/reserve/reporting assumptions remain conditional'],
        'no_submissions':True,'no_remote_training':True,'no_delegation':True,'professional_independent_validation':False}
    forum=dict(before['collaboration_forum']);forum.update(latest_Codex_comment=index['forum_result'],updated_utc=NOW)
    latest=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',forum_before,re.M)
    if latest:forum['latest_Codex_comment']=latest[-1][0].decode('utf-8').strip()
    raw=top(raw,'memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat())
    raw=top(raw,'current_phase',phase)
    raw=top(raw,'collaboration_forum',forum)
    return top(raw,'week_2_development2023_v1_20261023',section,add=True)

note='''

## Primera tanda de precios de semana 2, exclusivamente 2023

Codex, 23 de octubre de 2026, por autorización directa del participante para empezar referencia y primeros modelos y mantener 2024 cerrado. Preinscripción COD-S2-20261023-008 anterior al ajuste; resultado COD-S2-20261023-009. Índice activo: Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json; informe: docs/semana2/DESARROLLO_2023.md del repositorio común. Los contadores de preparación anteriores conservan su corte sin entrenamiento; este es un encargo posterior autorizado.

Se completaron tres recetas en cinco folds y tres ramos, con 50.094 filas OOF por receta y 30.869 componentes de clientes-direcciones. Quince constantes y treinta estimadores de precios: GLM Tweedie alpha=1 y LightGBM Tweedie fijo de 300 rondas. Todas las recetas usan F0 y el mismo vínculo C0 por fold, respuesta Y/e, peso sqrt(e); sin calibración posterior, mezcla, búsqueda o parada sobre validación. Recetas y código congelados antes de ajustar; ninguna receta final ni lista de confirmación congelada. Cómputo inicial 60 segundos; se conservaron modelos, transformaciones, filas de ajuste, OOF, pérdidas y trazas en privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc.

D² global OOF 2023: W2-B00 0,06858169; W2-B01 0,06665894; W2-B02 −0,27352879. El GLM mejora puntos de autos/contenidos pero empeora edificios y nuevo negocio. Diferencia global GLM−referencia −0,00192275, intervalo exploratorio pareado 95 % [−0,03810681;0,02869310], 2.000 réplicas semilla2026102302. No acredita mejora o equivalencia. Mantener referencia designada y conservar ambas alternativas. Los intervalos son exploratorios, no los de confirmación simultánea de 2024.

LightGBM presenta D² dentro del ajuste0,53629 y OOF−0,27353; A/E OOF2,02379. Los cinco folds y tres ramos son adversos. Brecha compatible con sobreajuste y deterioro de nivel, sin aislar causalmente un hiperparámetro ni descartar toda la familia. DEV2023-B02-GENERALIZATION bloquea avanzar esta receta como aspirante validado sin nueva evidencia de desarrollo. No se reescaló ni escogió otra ronda. Se conservan todos los resultados y modelos. Las sensibilidades de reserva/cola a tasas fijas no sustituyen reentrenamientos o salvaguardas completas de confirmación.

Pasaron quince casos conocidos y 937 controles del comprobador separado (se solapan). Replay exacto desde los 45 bundles con fit bloqueado, objetivos/predicciones/transformaciones/folds correctos, métricas e intervalos reconstruidos y gradiente GLM contrastado. Es revisión propia de Codex. El consumidor no ajustó, predijo o puntuó 2024 ni test. Ledger sin abrir y S2-AUD-METRIC-BINDING abierto; su cierre conserva responsable y criterio previos. Antes de abrir 2024 se requieren corrección y contraste del selector, productor/comprobador de métricas y lista, recetas, prioridades y artefactos congelados. Sin promoción, retiro, envíos, remoto, terceros o delegación. Originales, T0, folds, F0 y vínculos conservan hashes. Revisión humana y supuestos del último siguen pendientes.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda raw:raw+note)
change(ROOT/'Preparación/DECISIONES.md',lambda raw:raw+note)
change(ROOT/'Hackaton/Semana 2/README.md',lambda raw:raw+'\n\n## Primera tanda de modelos de 2023\n\nEl [resultado de desarrollo](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023.md) y el [índice activo](../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) registran referencia, GLM y LightGBM ya ajustados solo con 2023. Se mantiene la referencia y se conservan los resultados adversos; 2024 sigue cerrado. Este avance es posterior al corte de preparación sin modelos.\n')
change(ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',lambda raw:raw+'\n\n## Primera tanda de desarrollo completada, 23 de octubre\n\nLas tres recetas de [desarrollo 2023](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023.md) completaron cinco folds. D² OOF: referencia0,06858, GLM0,06666, LightGBM−0,27353. La diferencia del GLM no demuestra mejora global; la receta LightGBM tiene un deterioro de generalización/nivel que exige nueva evidencia de desarrollo. Se conservan ambas alternativas. No hay promoción ni lista final congelada. Antes de abrir 2024 deben corregirse y contrastarse el selector y sus métricas y congelarse recetas, lista y artefactos. Las sensibilidades de tasas fijas no cumplen por sí solas los escenarios completos de confirmación.\n')
change(REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md',lambda raw:raw+'\n\n## Avance posterior: primera tanda de desarrollo\n\nDespués del corte de preparación de este documento se entrenaron las primeras recetas exclusivamente en 2023. El [resultado de desarrollo](DESARROLLO_2023.md) y el [índice](../../registro/semana2_desarrollo2023_actual.json) contienen ese nuevo corte, sus resultados adversos y las condiciones pendientes. La preparación original y sus contadores conservan su alcance histórico. La confirmación de 2024 continúa cerrada.\n')
def readiness(raw):
    key='latest_development_execution'
    value={'as_of_utc':NOW,'index':rel(INDEX),'documentation':rel(DOC),'training_years':[2023],
           'status':'first_batch_completed_verified','confirmation_2024_open':False,
           'historical_counter_notice':'All earlier counters and no-training scope in this preparation record refer to its original dated task. This later user-authorized execution is identified separately.'}
    return top(raw,key,value,add=True)
change(REPO/'registro/semana2_listo_entrenar.json',readiness)
dump(RUN/'registration.json',{'utc':NOW,'index':rel(INDEX),'changes':changes,'confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'author':'Codex','source':'Observed serialized helper responses',
    'receipts':[{'id':'COD-S2-20261023-008','utc':'2026-10-23T17:34:46+00:00',
                 'previous_sha256':'53293995ee946cd54ed779cd510f07e3e2b68981832bb9269033cabdd5e40e44',
                 'sha256_at_append':'7911a41fd5284a49f3879caaee7c65fac0acbc8524620fc16c337fbd98927fc4'},
                {'id':'COD-S2-20261023-009','utc':'2026-10-23T17:45:11+00:00',
                 'previous_sha256':'592e3561eb923dc19518ac5a9d509e20aeda36e1eed819c82bc5c9cf33fc68cc',
                 'sha256_at_append':'042f7881e050b61e8e83238f962a3f50a60b5212f41b66c2c0287df8649a16d5'}]})

# Solo cierre documental e integridad después de escribir; no repetir modelos o suite.
checks=[]
def check(name,condition):checks.append({'name':name,'pass':bool(condition)})
for field in ['report','plan','producer','oof','manifest','assessment']:
    check('Active '+field,sha(ROOT/index[field])==index[field+'_sha256'])
check('Separate verification',sha(ROOT/index['verification']['path'])==index['verification']['sha256'])
old_routes=read(BACK/'RUTAS_PROYECTO.json');new_routes=read(ROOT/'RUTAS_PROYECTO.json')
check('Previous routes preserved',all(new_routes.get(k)==v for k,v in old_routes.items()))
for key,path in new_routes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/path).exists())
old_state=read(BACK/'Preparación/ESTADO_PROYECTO.json');new_state=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
changed_keys={'memory_as_of','current_phase','collaboration_forum'}
check('Older state branches preserved',all(new_state.get(k)==v for k,v in old_state.items() if k not in changed_keys))
for item in changes:
    if item['path'].endswith('.md'):
        check('Older prose preserved '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [DOC,ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md',forum_path]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        dest=link.strip('<>').split('#')[0]
        if not dest or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',dest):continue
        check('Local link '+rel(doc)+' -> '+dest,(doc.parent/unquote(dest)).resolve().exists())
current_forum=forum_path.read_bytes()
check('No forum bytes changed by registration',current_forum==forum_before)
for mid in ['008','009']:check('Unique forum '+mid,current_forum.count(('<!-- aporte:COD-S2-20261023-'+mid+' -->').encode())==1)
check('2024 still closed',not (ROOT/selection['ledger_workspace_relative']).exists())
check('Policy stable',sha(ROOT/selection['policy']['path'])==selection['policy']['sha256'])
closure={'utc':NOW,'scope':'Post-registration integrity only, no training or broad suite rerun','checks':checks,
         'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)}
dump(RUN/'closure_verification.json',closure)
assert closure['failed']==0,[x for x in checks if not x['pass']]
paths={p for p in RUN.rglob('*') if p.is_file()}
paths.update(ROOT/x['path'] for x in changes)
paths.update([INDEX,DOC,ROOT/index['plan'],ROOT/index['producer'],forum_path,Path(__file__),
    REPO/'herramientas/probar_desarrollo2023_semana2.py',REPO/'herramientas/verificar_desarrollo2023_semana2.py',
    REPO/'herramientas/diagnosticar_desarrollo2023_semana2.py',REPO/'herramientas/documentar_desarrollo2023_semana2.py',
    REPO/'registro/semana2_desarrollo2023_pruebas_v1.json',ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_preinscripcion.md',
    ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_resultado.md'])
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Closing cut; initial manifests remain historical. Shared files may change later.',
    'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)],
    'confirmation_2024_open':False,'promotion':False})
print(json.dumps({'registered':rel(INDEX),'postregistration_checks':closure['passed'],'failed':closure['failed'],
                  'models_families':3,'confirmation_2024_open':False},ensure_ascii=True))
