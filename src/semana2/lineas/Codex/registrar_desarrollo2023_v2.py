"""Cierre de la segunda tanda; índices actuales y cortes anteriores separados."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';PROPOSED=RUN/'active_index_proposed.json'
BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
NOW=datetime.now(timezone.utc).isoformat();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    text=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+text+'\n}\n'
    match=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert match,key
    _,end=json.JSONDecoder().raw_decode(raw[match.end():])
    return raw[:match.end()]+text+raw[match.end()+end:]
changes=[]
def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');stage=path.with_name(path.name+'.s2dev2.tmp')
    assert path.read_bytes()==before,'Cambio concurrente '+str(path)
    with stage.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Cambio concurrente '+str(path)
    os.replace(stage,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})

index=read(PROPOSED);report=read(RUN/'report.json');snapshot=REPO/'registro/semana2_desarrollo2023_v1_snapshot.json'
assert ACTIVE.read_bytes()==snapshot.read_bytes(),'El índice v1 cambió concurrentemente; conciliar antes de registrar'
assert read(ROOT/index['verification']['path'])['failed']==0
selection_path=REPO/'registro/semana2_seleccion_actual.json';selection=read(selection_path)
assert not (ROOT/selection['ledger_workspace_relative']).exists()
assert sha(ROOT/selection['policy']['path'])==read(RUN/'plan_snapshot.json')['selection_policy_sha256']
(RUN/'selector_index_at_close.json').write_bytes(selection_path.read_bytes())
forum_path=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_cut=forum_path.read_bytes()
assert forum_cut.count(b'<!-- aporte:COD-S2-20261023-011 -->')==1
change(ACTIVE,lambda raw:PROPOSED.read_text(encoding='utf-8'))

def routes(raw):
    for key,path in {'week_2_development_report':ROOT/index['documentation'],'week_2_development_plan':ROOT/index['plan'],'week_2_development_oof':ROOT/index['oof']}.items():
        assert path.exists();raw=top(raw,key,rel(path))
    return top(raw,'week_2_development_v1_snapshot',rel(snapshot),add=True)

def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_second_2023_batch_verified_reference_retained_2024_explicitly_closed',
      'current_state_key':'week_2_development2023_v2_20261023',
      'historical_fields_notice':'Los contadores de cada encargo anterior conservan su corte; el índice activo contiene ambas tandas e historial.'}
    section={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'documentation':index['documentation'],'run':rel(RUN),
      'training_years':[2023],'scored_years':[2023],'rows_per_recipe':50094,'groups':30869,'folds':5,
      'new_fits_this_batch':20,'cumulative_price_estimators_fitted':50,'closed_form_constants_total':15,
      'GLM_bundle_reuses':10,'prefix_exports':15,'models_consulted':index['models_consulted'],
      'results_D2':{x['model_id']:x['D2'] for x in report['summary']},'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],
      'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
      'verification':index['verification'],'forum_decisions':['COD-S2-20261023-010','COD-S2-20261023-011'],
      'pending':['Reference differences uncertain and sensitive to favorable components; no promotion',
        'Observed aggregate level and reserve/ultimate assumptions unresolved; no implicit rescaling',
        'Keep 2024 closed, irrespective of progress of separate selector repair; final confirmation roster not frozen',
        'Original B02 warning and alias remain under their responsible reviewers; new recipe IDs do not close them'],
      'no_submissions':True,'no_remote_training':True,'no_delegation':True,'professional_independent_validation':False}
    forum=dict(obj['collaboration_forum'],latest_Codex_comment='COD-S2-20261023-011',updated_utc=NOW)
    latest=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',forum_cut,re.M)
    if latest:forum['latest_Codex_comment']=latest[-1][0].decode('utf-8').strip()
    for key,value in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',forum)]:raw=top(raw,key,value)
    return top(raw,'week_2_development2023_v2_20261023',section,add=True)

note='''

## Segunda tanda de desarrollo 2023 y revisión de las brechas

Codex, 23 de octubre de 2026, por nueva instrucción del participante: revisar GLM en edificios y brecha LightGBM, preinscribir antes de otra tanda, conservar referencia y mantener 2024 cerrado. Revisión sin fit en privado/semana2/desarrollo2023/revision_20261023T175646Z_4924665e. Recetas en COD-S2-20261023-010 antes de probar; resultado COD-S2-20261023-011. Informe docs/semana2/DESARROLLO_2023_TANDA2.md; índice activo Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json. V1 preserva snapshot público y sus artefactos intactos.

El GLM de edificios ganaba pérdida en filas sin coste y la perdía en las positivas; cinco grupos adversos invertían el signo al retirarlos solo como diagnóstico. Los 26 capitales desconocidos no tuvieron siniestros y no explican el deterioro. Coeficientes variables y soporte reducido de algunos árboles motivaron la prueba. min_child_samples es aproximación por Hessianos, no garantía exacta de filas por hoja; se precisa la prosa previa, sin cambiar la receta original.

Tres recetas registradas: B03 alpha=10 solo en edificios, otras líneas B01 exacto; B04 primeros 25 árboles de cada B02, sin búsqueda de etapa o nuevo ajuste; B05 80 árboles de profundidad uno/dos hojas, min_child_samples=1000 y L2=100, resto igual. Veinte ajustes nuevos, diez reutilizaciones GLM y quince prefijos. Se acumulan cincuenta estimadores de precios ajustados y quince constantes, sin contar reusos como entrenamientos. Solo 2023, mismos 50.094 periodos, 30.869 componentes, folds, F0, T0/C0, pesos y semilla. Ninguna calibración, mezcla o receta añadida después de ver resultados.

D² global OOF: B00 0,06858169; B01 0,06665894; B02 −0,27352879 (comparadores exactos); B03 0,08672449; B04 0,07341590; B05 0,07985841. Edificios GLM pasa de −0,04146675 a 0,01776628, todavía menor que la referencia 0,02084694. Brecha de edificios baja de 0,22694 a 0,11452; desviación media de coeficientes entre folds de 0,08412 a 0,03371. A/E de edificios empeora de 1,09061 a 1,13991: mejor devianza no resuelve el nivel. Brecha global B02 0,80982 baja a 0,13260 con prefijo y 0,06991 con boosting simple. Mejoras descriptivas compatibles con menor sobreajuste; no causalidad aislada de cada parámetro.

Frente a B00, intervalos exploratorios 95 %: B03 delta 0,01814280, [−0,00229710;0,03744815]; B04 delta 0,00483422, [−0,01202376;0,02017174]; B05 delta 0,01127672, [−0,00304048;0,02279640]. Los tres cruzan cero y las tres ventajas se invierten al retirar los 31 componentes más favorables. Se mantiene B00 y se conservan B01–B05, sin promoción, retiro o equivalencia. Se publican quince parejas, 2.000 remuestreos comunes y búsqueda adaptativa declarada; no hay corrección de selección/multiplicidad o confirmación temporal.

Pasaron 21 controles focales y 1.279 del comprobador separado, con solapamiento. Replay exacto con fit bloqueado, árboles del prefijo y suma de hojas reconstruidos, parámetros, transformaciones dentro de fold, gradientes GLM, objetivos/vínculos, métricas, intervalos e influencia contrastados. Es comprobación propia de Codex. Corrida privada dev2_20261023T180127Z_46d18106. Supuestos del último y escenarios de tasas fijas conservan su alcance; no sustituyen reserva suficiente o escenarios reentrenados de confirmación.

2024 queda expresamente cerrado por la instrucción actual, con independencia del progreso del encargo separado del selector. No se cierra DEV2023-B02-GENERALIZATION ni su alias S2-VAL-MOD-007 de la receta original por probar IDs nuevos. No se abre ledger o congela lista final, ajusta/predice/puntúa 2024 o test, envía, entrena remoto, publica o delega. La revisión humana sigue pendiente. Los campos de encargos anteriores conservan sus cortes.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda raw:raw+note)
change(ROOT/'Preparación/DECISIONES.md',lambda raw:raw+note)
update='\n\n## Segunda tanda de desarrollo de 2023\n\nLa [revisión del GLM y segunda tanda](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_TANDA2.md) conserva recetas previas y resultados. B03/B04/B05 mejoran los puntos, pero sus ventajas frente a la referencia son inciertas y sensibles a pocos componentes. Se conserva B00 y todas las alternativas. 2024 sigue cerrado por instrucción expresa del participante. El [índice activo](../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) incluye el historial de ambas tandas.\n'
change(ROOT/'Hackaton/Semana 2/README.md',lambda raw:raw+update)
change(ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',lambda raw:raw+update)
change(REPO/'docs/semana2/DESARROLLO_2023.md',lambda raw:raw+'\n\n## Corte posterior: segunda tanda\n\nLa [segunda tanda](DESARROLLO_2023_TANDA2.md) prueba las recetas preinscritas para las brechas identificadas aquí. El [snapshot del índice de esta primera tanda](../../registro/semana2_desarrollo2023_v1_snapshot.json) conserva exactamente el registro original; el índice activo contiene el avance posterior. Las cifras y decisiones anteriores mantienen su corte.\n')
def readiness(raw):
    value={'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
      'status':'two_batches_verified_reference_retained','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
      'historical_counter_notice':'Earlier preparation counters retain their dated no-training scope; current authorized price execution and history are in the development index.'}
    return top(raw,'latest_development_execution',value)
change(REPO/'registro/semana2_listo_entrenar.json',readiness)
dump(RUN/'registration.json',{'utc':NOW,'index':rel(ACTIVE),'changes':changes,'confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'author':'Codex','source':'Serialized helper outputs observed in this task','receipts':[
 {'id':'COD-S2-20261023-010','utc':'2026-10-23T17:59:07+00:00','previous_sha256':'02adfbd02317b17865dc118a296625741f415faeb39229c3e14c7926e09ffb31','sha256_at_append':'cf2c67de5403451a591b6c68750bd951b023488646167febc0d65b10d376dd09'},
 {'id':'COD-S2-20261023-011','utc':'2026-10-23T18:06:56+00:00','previous_sha256':'2fdb148eb57373c65273271aff7bb047772b768e5aec08e920c2ab4e1bc71af3','sha256_at_append':'18b4a8f3421d09ffaa295e21489e1c92ee7d34ee8565ac58688713ef03d2e73e'}]})
checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
for key in ['report','plan','producer','oof','manifest','assessment']:check('Index '+key,sha(ROOT/index[key])==index[key+'_sha256'])
check('Verification checksum',sha(ROOT/index['verification']['path'])==index['verification']['sha256'])
check('Preserved v1 public index',snapshot.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldroutes=read(BACK/'RUTAS_PROYECTO.json');routes_now=read(ROOT/'RUTAS_PROYECTO.json')
changed_route_keys={'week_2_development_report','week_2_development_plan','week_2_development_oof'}
check('Other route values preserved',all(routes_now.get(k)==v for k,v in oldroutes.items() if k not in changed_route_keys))
for key,path in routes_now.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/path).exists())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Older state branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in {'memory_as_of','current_phase','collaboration_forum'}))
for item in changes:
    if item['path'].endswith('.md'):check('Prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [ROOT/index['documentation'],REPO/'docs/semana2/DESARROLLO_2023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum_path]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        dest=link.strip('<>').split('#')[0]
        if not dest or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',dest):continue
        check('Local link '+rel(doc)+' -> '+dest,(doc.parent/unquote(dest)).resolve().exists())
for item in read(RUN/'frozen_sources_before_fit.json')['files']:check('Source remains '+item['path'],sha(ROOT/item['path'])==item['sha256'])
for mid in ['010','011']:check('Unique forum '+mid,forum_path.read_bytes().count(('<!-- aporte:COD-S2-20261023-'+mid+' -->').encode())==1)
check('2024 still closed',not (ROOT/selection['ledger_workspace_relative']).exists())
check('All alternatives retained',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==5 and not index['promotion'])
result={'utc':NOW,'scope':'Post-registration integrity/links only; no estimator fitting or broad suite rerun','checks':checks,
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)}
dump(RUN/'closure_verification.json',result)
assert result['failed']==0,[x for x in checks if not x['pass']]
paths={p for p in RUN.rglob('*') if p.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],snapshot,Path(__file__),forum_path,
 REPO/'herramientas/revisar_brechas2023_semana2.py',REPO/'herramientas/probar_desarrollo2023_v2_semana2.py',
 REPO/'herramientas/verificar_desarrollo2023_v2_semana2.py',REPO/'herramientas/documentar_desarrollo2023_v2_semana2.py',
 REPO/'registro/semana2_desarrollo2023_pruebas_v2.json',ROOT/'Hackaton/Semana 2/Codex/preinscribir_desarrollo2023_v2.py',
 ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v2_preinscripcion.md',ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v2_resultado.md'])
review_dir=(ROOT/read(RUN/'plan_snapshot.json')['diagnostic_review']).parent;paths.update(p for p in review_dir.rglob('*') if p.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Closing cut; prior manifests remain historical. Shared files may change later.',
 'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)],'confirmation_2024_open':False,'promotion':False})
print(json.dumps({'registered':rel(ACTIVE),'closure_checks':result['passed'],'failed':result['failed'],'reference':'W2-B00','confirmation_2024_open':False},ensure_ascii=True))
