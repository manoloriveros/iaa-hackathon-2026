"""Actualiza la memoria común tras la prueba de nivel, preservando sus cortes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';PROPOSED=RUN/'active_index_proposed.json'
BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
NOW=datetime.now(timezone.utc).isoformat();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
    found=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert found,key
    _,end=json.JSONDecoder().raw_decode(raw[found.end():])
    return raw[:found.end()]+encoded+raw[found.end()+end:]
changes=[]
def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');stage=path.with_name(path.name+'.s2dev3.tmp')
    assert path.read_bytes()==before,'Cambio concurrente '+str(path)
    with stage.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Cambio concurrente '+str(path)
    os.replace(stage,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})

index=read(PROPOSED);report=read(RUN/'report.json');snapshot=REPO/'registro/semana2_desarrollo2023_v2_snapshot.json'
assert ACTIVE.read_bytes()==snapshot.read_bytes(),'Índice concurrente distinto de v2; conciliar antes de actualizar'
assert read(ROOT/index['verification']['path'])['failed']==0
selector_path=REPO/'registro/semana2_seleccion_actual.json';selector=read(selector_path)
assert not (ROOT/selector['ledger_workspace_relative']).exists()
assert sha(ROOT/selector['policy']['path'])==read(RUN/'plan_snapshot.json')['selection_policy_sha256']
(RUN/'selector_index_at_close.json').write_bytes(selector_path.read_bytes())
forum_path=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_cut=forum_path.read_bytes()
assert forum_cut.count(b'<!-- aporte:COD-S2-20261023-013 -->')==1
change(ACTIVE,lambda raw:PROPOSED.read_text(encoding='utf-8'))

def routes(raw):
    for key,path in {'week_2_development_report':ROOT/index['documentation'],'week_2_development_plan':ROOT/index['plan'],'week_2_development_oof':ROOT/index['oof']}.items():
        assert path.exists();raw=top(raw,key,rel(path))
    return top(raw,'week_2_development_v2_snapshot',rel(snapshot),add=True)
def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_level_anchor_contraction_2023_verified_B00_retained_2024_closed',
      'current_state_key':'week_2_development2023_v3_20261023','historical_fields_notice':'Cada encargo anterior conserva su corte; el índice activo y sus snapshots contienen las tres pruebas de desarrollo.'}
    section={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'documentation':index['documentation'],'run':rel(RUN),
      'training_years':[2023],'scored_years':[2023],'rows_per_recipe':50094,'groups':30869,'folds':5,
      'new_base_estimator_fits':0,'new_level_factors':30,'new_adapter_bundles':60,'cumulative_base_estimator_fits':50,'closed_form_constants_total':15,
      'models_consulted':index['models_consulted'],'results_D2':{x['model_id']:x['D2'] for x in report['summary']},
      'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],'promotion':False,
      'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
      'verification':index['verification'],'forum_decisions':['COD-S2-20261023-012','COD-S2-20261023-013'],
      'pending':['Training-level anchor is not independent calibration; ultimate/reserve/reporting assumptions persist',
        'Exploratory positive intervals do not correct adaptive search or 45 pairwise comparisons',
        'B06/B07 residual top31 influence; B09 adverse new-business point; previous warnings retain their owners',
        'B00 remains incumbent; 2024 expressly closed regardless of separate selector repair progress'],
      'selector_status_not_assessed_here':True,'no_submissions':True,'no_remote_training':True,'no_delegation':True,'professional_independent_validation':False}
    forum=dict(obj['collaboration_forum'],latest_Codex_comment='COD-S2-20261023-013',updated_utc=NOW)
    entries=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',forum_cut,re.M)
    if entries:forum['latest_Codex_comment']=entries[-1][0].decode('utf-8').strip()
    for key,value in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',forum)]:raw=top(raw,key,value)
    return top(raw,'week_2_development2023_v3_20261023',section,add=True)

note='''

## Nivel agregado e influencia: tercera prueba solo en 2023

Codex, 23 de octubre de 2026, por nueva petición del participante de revisar nivel e influencia en B03/B05, registrar antes de probar, conservar B00 y mantener 2024 cerrado. La revisión previa está en privado/semana2/desarrollo2023/revision_nivel_20261023T181136Z_82668c37. Preinscripción COD-S2-20261023-012, resultado COD-S2-20261023-013. Informe docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md; índice actual Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json, con snapshots exactos de v1/v2 y tres corridas intactas.

B03/B05 estaban 8,29 %/9,61 % por debajo del total B00. Los 31 componentes más favorables aportaban 140,49 %/130,02 % de la ventaja neta al compensar contribuciones adversas. Concentran 12,31 %/9,48 % del coste observado y 0,12 %/0,13 % de la exposición; 14/18 grupos favorables bastaban para invertir la ventaja. Los retiros son influencia de evaluación con modelos fijos, no errores de datos o un jackknife de reentrenamiento. Ningún grupo se excluyó de ajuste, factores o score completo.

La receta v3 aprende exclusivamente en las filas de ajuste de cada ramo/fold s=sum(e*tasa_B00)/sum(e*tasa_padre). B06/B07 usan B03/B05 con esa escala; B08/B09 mezclan su tasa anclada con B00 al 50 % fijado previamente. Las dos versiones de cada padre comparten factor. Treinta factores y sesenta adaptadores; no se ajustan nuevos GLM o árboles. Se reutilizan 45 archivos distintos de fuentes y se acumulan cincuenta estimadores base ajustados, quince constantes y treinta factores, sin contar reusos como nuevos entrenamientos. Mismos 50.094 periodos de 2023, 30.869 componentes, folds, F0 y T0/C0; B00–B05 exactos.

Los sesenta adaptadores igualan el total predicho de ajuste con B00 y los de peso medio contraen exactamente a la mitad las desviaciones de tasa. No se fuerza el total OOF u observado, no se minimiza otra vez la pérdida de escala o busca el mejor peso. La normalización usa predicciones dentro del ajuste, no calibración independiente o interna fuera de muestra; el ancla B00 también depende de siniestros. Un A/E próximo al de B00 no demuestra calibración futura, reservas o último.

D² OOF 2023: B00 0,06858169; B03 0,08672449; B05 0,07985841; B06 0,08903915; B07 0,08173829; B08 0,09317908; B09 0,08076687. Totales B06/B07/B08/B09: 15,584/15,622/15,599/15,618 millones CU frente a 15,614 B00 y 15,297 observado. El nivel se acerca a B00 sin imponer igualdad en validación. B08 mejora los puntos de tres ramos y ambos segmentos; B09 sigue adverso en nuevo negocio.

Mover solo nivel no resuelve influencia: B06/B07 tienen diferencias frente a B00 de −0,00817419/−0,00429867 al retirar sus propios 31 grupos favorables. B08/B09 conservan +0,00581426/+0,00119128; con las listas congeladas de sus padres +0,00587360/+0,00120545. Diferencias completas B06/B07/B08/B09: 0,02045746/0,01315660/0,02459740/0,01218518. Límites inferiores exploratorios 95 %: 0,00137502/0,00073247/0,01468254/0,00581405. Son positivos en esta muestra, pero no corrigen búsqueda adaptativa o las 45 parejas; no constituyen confirmación simultánea temporal o superioridad profesional.

Se mantiene B00 y todas las alternativas B01–B09, sin promoción, retiro, equivalencia o lista final congelada. B08 es el mejor punto de la exploración actual, sin alterar su condición. Pasaron 21 casos focales y 2.023 controles del comprobador separado, con solapamiento; factores reconstruidos sin respuestas en su entrada, momento de ajuste, contracción/orden, padres intactos, replay con fit bloqueado, métricas, remuestreo, ambas listas de influencia y escenarios a adaptadores fijos. Corrida dev3_20261023T181613Z_24c943a3. Es revisión propia de Codex, no profesional independiente.

2024 sigue cerrado por instrucción expresa. El cierre técnico del vínculo del selector y el seguimiento GOV005 fueron recibidos en el foro y conservan responsables/evidencia propios; no se evalúan o cierran aquí ni se infiere permiso de abrir. No se ajusta/predice/puntúa 2024 o test, abre ledger, envía, entrena remoto, publica o delega. Los supuestos del último y la revisión humana pendiente siguen vigentes. Cada campo de encargos anteriores conserva su corte.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda raw:raw+note)
change(ROOT/'Preparación/DECISIONES.md',lambda raw:raw+note)
update='\n\n## Nivel e influencia, tercera prueba de 2023\n\nLa [prueba de ancla y contracción](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md) acerca los niveles a B00. El ancla sola conserva influencia adversa; las contracciones fijas del 50 % mantienen ventaja tras los dos retiros preinscritos de grupos. B08 obtiene D² OOF 0,09318, pero se mantiene B00 y todas las alternativas. No hay promoción, calibración independiente o lista final congelada. 2024 sigue expresamente cerrado. El [índice activo](../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conserva el historial de las tres pruebas.\n'
change(ROOT/'Hackaton/Semana 2/README.md',lambda raw:raw+update)
change(ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',lambda raw:raw+update)
change(REPO/'docs/semana2/DESARROLLO_2023_TANDA2.md',lambda raw:raw+'\n\n## Corte posterior: ancla de nivel e influencia\n\nLa [tercera prueba](DESARROLLO_2023_NIVEL_INFLUENCIA.md) contrasta nivel anclado y contracción fija preinscritos. El [snapshot del índice de esta segunda tanda](../../registro/semana2_desarrollo2023_v2_snapshot.json) conserva exactamente su registro; el índice activo recoge el avance posterior. Este documento y sus resultados mantienen el corte original.\n')
def readiness(raw):
    return top(raw,'latest_development_execution',{'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
      'status':'three_2023_trials_verified_reference_retained','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
      'historical_counter_notice':'Earlier preparation counters retain their dated no-training scope; current authorized executions, scalar factors and snapshots are in the development index.'})
change(REPO/'registro/semana2_listo_entrenar.json',readiness)
dump(RUN/'registration.json',{'utc':NOW,'index':rel(ACTIVE),'changes':changes,'confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'author':'Codex','source':'Serialized helper responses observed in this task','receipts':[
 {'id':'COD-S2-20261023-012','utc':'2026-10-23T18:13:13+00:00','previous_sha256':'82d7f4ef5df59150b931987419a62539155b0dc223f9761b9169449699e1e1c1','sha256_at_append':'74141f86ee5961df9ad8d1ece83a7a37e741a806a83b5d69a4ce33da930c16e0'},
 {'id':'COD-S2-20261023-013','utc':'2026-10-23T18:21:54+00:00','previous_sha256':'d2c05e5c2d417ca376cb32ded2ad6b9ce4605c8c72fc77f09c5960980466dfe5','sha256_at_append':'1966f3a078d9de6e5907cc1db826a3306b8263df5ea940504d230651d7dfefbd'}]})
checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
for key in ['report','plan','producer','oof','manifest','assessment']:check('Index '+key,sha(ROOT/index[key])==index[key+'_sha256'])
check('Verifier checksum',sha(ROOT/index['verification']['path'])==index['verification']['sha256'])
check('Preserved v2 public index',snapshot.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldroutes=read(BACK/'RUTAS_PROYECTO.json');currentroutes=read(ROOT/'RUTAS_PROYECTO.json');mutable={'week_2_development_report','week_2_development_plan','week_2_development_oof'}
check('Other route values preserved',all(currentroutes.get(k)==v for k,v in oldroutes.items() if k not in mutable))
for key,path in currentroutes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/path).exists())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Previous state branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in {'memory_as_of','current_phase','collaboration_forum'}))
for item in changes:
    if item['path'].endswith('.md'):check('Prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [ROOT/index['documentation'],REPO/'docs/semana2/DESARROLLO_2023_TANDA2.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum_path]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        dest=link.strip('<>').split('#')[0]
        if not dest or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',dest):continue
        check('Local link '+rel(doc)+' -> '+dest,(doc.parent/unquote(dest)).resolve().exists())
for item in read(RUN/'frozen_sources_before_fit.json')['files']:check('Source stable '+item['path'],sha(ROOT/item['path'])==item['sha256'])
for mid in ['012','013']:check('Unique forum '+mid,forum_path.read_bytes().count(('<!-- aporte:COD-S2-20261023-'+mid+' -->').encode())==1)
check('2024 still closed',not (ROOT/selector['ledger_workspace_relative']).exists())
check('B00 and nine alternatives retained',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==9 and not index['promotion'])
result={'utc':NOW,'scope':'Post-registration integrity only; no estimator refitting or statistical suite repetition','checks':checks,
 'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={p for p in RUN.rglob('*') if p.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],snapshot,Path(__file__),forum_path,
 REPO/'herramientas/revisar_nivel_influencia2023_semana2.py',REPO/'herramientas/probar_desarrollo2023_v3_semana2.py',
 REPO/'herramientas/verificar_desarrollo2023_v3_semana2.py',REPO/'herramientas/documentar_desarrollo2023_v3_semana2.py',
 REPO/'registro/semana2_desarrollo2023_pruebas_v3.json',ROOT/'Hackaton/Semana 2/Codex/preinscribir_desarrollo2023_v3.py',
 ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v3_preinscripcion.md',ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v3_resultado.md'])
review_dir=(ROOT/read(RUN/'plan_snapshot.json')['diagnostic_review']).parent;paths.update(p for p in review_dir.rglob('*') if p.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Closing cut; earlier manifests remain historical and shared files can change later.',
 'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)],'confirmation_2024_open':False,'promotion':False})
print(json.dumps({'registered':rel(ACTIVE),'closure_checks':result['passed'],'failed':result['failed'],'reference':'W2-B00','confirmation_2024_open':False},ensure_ascii=True))
