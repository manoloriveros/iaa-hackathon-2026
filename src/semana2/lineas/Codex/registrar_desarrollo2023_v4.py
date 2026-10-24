"""Registro atómico por archivo; conserva ramas y cortes anteriores."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';SNAP=REPO/'registro/semana2_desarrollo2023_v3_snapshot.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    value=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw);return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+value+'\n}\n'
    match=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert match,key
    _,end=json.JSONDecoder().raw_decode(raw[match.end():]);return raw[:match.end()]+value+raw[match.end()+end:]
changes=[]
def change(p,fn):
    before=p.read_bytes();backup=BACK/p.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=p.with_name(p.name+'.s2dev4.tmp');assert p.read_bytes()==before,'Cambio concurrente '+str(p)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==before,'Cambio concurrente '+str(p);os.replace(tmp,p)
    changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p),'backup':rel(backup)})
index=read(RUN/'active_index_proposed.json');report=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json')
assert ACTIVE.read_bytes()==SNAP.read_bytes(),'Conciliar índice concurrente antes de reemplazar'
assert read(ROOT/index['verification']['path'])['failed']==0 and read(ROOT/index['fixtures']['path'])['failed']==0
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath)
assert not (ROOT/selector['ledger_workspace_relative']).exists();assert sha(ROOT/selector['policy']['path'])==plan['selection_policy_sha256']
(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
assert cut.count(b'<!-- aporte:COD-S2-20261023-015 -->')==1
change(ACTIVE,lambda raw:(RUN/'active_index_proposed.json').read_text(encoding='utf-8'))
def routes(raw):
    for key,path in [('week_2_development_report',index['documentation']),('week_2_development_plan',index['plan']),('week_2_development_oof',index['oof'])]:raw=top(raw,key,path)
    return top(raw,'week_2_development_v3_snapshot',rel(SNAP),True)
def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_business_level_and_conditional_refit_stress_2023_verified_B00_retained_2024_closed','current_state_key':'week_2_development2023_v4_20261023',
           'historical_fields_notice':'Cada encargo anterior conserva su corte; cuatro tandas en el índice activo y snapshots exactos.'}
    section={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'documentation':index['documentation'],'run':rel(RUN),'training_years':[2023],'scored_years':[2023],
     'rows_per_recipe':50094,'groups':30869,'folds':5,'new_candidate_base_estimator_fits':0,'new_level_factors':60,'new_adapter_bundles':30,'stress_GLM_fits':15,'stress_constants':15,
     'cumulative_base_estimator_fits':65,'cumulative_closed_form_constants':30,'cumulative_candidate_level_factors':90,
     'models_consulted':index['models_consulted'],'results_D2':{x['model_id']:x['D2'] for x in report['summary']},'stress_results':report['stress_summary'],
     'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],'promotion':False,'confirmation_2024_open':False,
     'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,'verification':index['verification'],'fixtures':index['fixtures'],
     'forum_decisions':['COD-S2-20261023-014','COD-S2-20261023-015'],
     'pending':['B08 absolute level sensitive to severe training groups; stress conditional on frozen reporting C0, not full-pipeline robustness',
      'B10/B11 parent improvement uncertain; buildings-new deviance worsens despite near-one A/E',
      'In-sample scalar calibration, adaptive search and 66 unadjusted pairs; ultimate/reporting/reserve assumptions persist',
      'Original B09 and other recipe warnings remain with owners; B11 does not close B09',
      'B00 incumbent and 2024 expressly closed; no final roster or promotion'],
     'selector_status_not_assessed_here':True,'no_submissions':True,'no_remote_training':True,'no_delegation':True,'professional_independent_validation':False}
    collab=dict(obj['collaboration_forum'],latest_Codex_comment='COD-S2-20261023-015',updated_utc=NOW)
    headers=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if headers:collab['latest_Codex_comment']=headers[-1][0].decode().strip()
    for key,val in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab)]:raw=top(raw,key,val)
    return top(raw,'week_2_development2023_v4_20261023',section,True)
note='''

## Estabilidad de B08 y nuevo negocio: cuarta prueba solo en 2023

Codex, 23 de octubre de 2026, por solicitud expresa de revisar B08/B09, registrar antes de probar, conservar B00 y mantener 2024 cerrado. Preinscripción COD-S2-20261023-014 (20:45:49 UTC), resultado COD-S2-20261023-015 (20:54:26 UTC). Informe Hackaton/Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md; corrida dev4_20261023T204811Z_4adcedec y plan v4. El índice actual conserva los snapshots exactos v1/v2/v3; los campos de encargos anteriores mantienen sus cortes.

El diagnóstico OOF congelado confirma B08 mejor que B00 en los cinco folds (delta D² 0,01291–0,03360), pero con pérdida en edificios nuevos (−0,03269). Los 31 grupos favorables concentran 78,0 % de la ventaja B08 y 90,8 % de B09; 68/40 bastan para invertir la ventaja con modelos fijos. B09 pierde en autos nuevos (A/E 1,910, delta D² −0,01722) y edificios nuevos (−0,00843); mejora en contenidos nuevos. Autos nuevos tiene 1,088 millones CU observados, 0,570 predichos por B09 y 0,543 por B00. Hay 265/40/36 periodos positivos nuevos en autos/edificios/contenidos. La lectura inicial se repitió al recuperar una sesión de herramienta: ambas revisiones se conservan sin contarlas como evidencia independiente.

B10/B11 parten de B08/B09 con un factor positivo por ramo/fold/tipo de negocio q=sum_ajuste(T0/sqrt(mu))/sum_ajuste(sqrt(mu)), mu=e_C0*tasa_padre. Es mínimo escalar Tweedie 1,5 dentro del ajuste, no calibración independiente ni equilibrio de importes/A/E=1. Se cambia explícitamente el ancla en las dos variantes, sin cambiar padres o B00. Sesenta factores y treinta adaptadores, sin estimadores base nuevos para las candidatas; ningún peso buscado o factor aprendido con OOF. Mismos 50.094 periodos de 2023, 30.869 componentes y cinco folds; B00–B09 exactos.

Prueba separada S08: se retiran los 25 componentes con mayor T0 del ajuste de cada fold (0,1 % redondeado hacia arriba; 46–53 filas y 2,715–3,408 millones CU), completos en todos los ramos. Se reaprenden transformaciones F0, quince GLM B03, quince constantes S00, ancla y mezcla B08 al 50 %. No se retira validación ni filas de las candidatas principales. Los conjuntos de estrés se solapan: no son 125 observaciones independientes o candidatos. C0 sigue fijo y refleja grupos retirados; sensibilidad condicional del modelo de riesgo, no reporting integral, jackknife completo o prueba temporal. Acumulado: 65 estimadores base y 30 constantes; 90 factores candidatos y 90 adaptadores, con las anclas/adaptadores de estrés identificados aparte.

D² B00 0,06858169; B08 0,09317908; B09 0,08076687; B10 0,09424368; B11 0,08658871. Totales B10/B11 14,161/14,319 millones CU, A/E global 1,08022/1,06833 frente a 15,297 millones observados. Nuevo negocio: B10 D² 0,08037458, A/E 1,01869; B11 D² 0,08303575, A/E 1,04334 frente a B09 0,04064978/1,50173. B11 autos nuevos mejora D² −0,14736→−0,04508 y A/E 1,910→1,042; no demuestra nivel último adecuado. Edificios nuevos empeora: B08→B10 0,03253→0,01111 pese a A/E 1,003; B09→B11 0,05680→0,02595 pese a A/E 1,020.

B10/B08 delta D² +0,00106460, intervalo exploratorio 95 % [−0,00348976;0,00647903]; B11/B09 +0,00582184 [−0,00157762;0,01618883]. Ambos intervalos incluyen cero; tras retiro de sus 31 grupos favorables quedan −0,00335826/−0,00505856. Frente a B00, B10/B11 tienen delta +0,02566200/+0,01800702, retiro propio +0,00691391/+0,00346160 y retiro de listas congeladas B08/B09 +0,00700836/+0,00835395. Las 66 parejas y 2.000 sorteos comunes son exploratorios, sin corrección por búsqueda adaptativa/multiplicidad; no confirmación simultánea de2024.

S08 bajo estrés baja a D² 0,06915681 y predice 11,625 millones CU (−25,48 % frente a B08), A/E 1,31591; la mediana de cambio de tasa es −7,27 % y percentiles 1/99 −67,34/+7,65 %. La constante S00 de estrés queda D² 0,03931571: S08 conserva ventaja relativa +0,02984110 bajo la misma perturbación, mientras el nivel depende de grupos severos. No se propone recortar cola ni se declara B08 estable para2025.

Pasaron 21 casos focales y 1.178 controles separados con solapamiento; replay con fit bloqueado, derivada/mínimo q con suma compensada, fuentes, entrenamiento exclusivo2023, selección completa de grupos, transformaciones del estrés, constante/ancla, métricas/escenarios/remuestreo/influencia. Es comprobación propia de Codex, no validación profesional independiente. El primer intento dev4_20261023T204705Z_3a937001 abortó antes de factores o entrenamiento por usar el guard de tabla única sobre OOF multirreceta; se corrigió la clave con model_id sin cambiar recetas y se conservó. El primer comprobador abortó por sombra local del módulo regex; quedó registrado y corregido sin reentrenamiento. No hubo ajustes adicionales tras los resultados.

Se conserva B00 y B01–B11 sin promoción, retiro, equivalencia o lista final congelada. Quedan abiertas sensibilidad del nivel de B08, edificios nuevos adverso, incertidumbre del beneficio respecto del padre, escasez de positivos y calibración dentro del ajuste, además de supuestos de último/reservas/reporting. B11 no cierra la advertencia de B09. Las advertencias ajenas mantienen responsables y alcance. 2024 sigue cerrado por instrucción expresa, sin predicciones, precios, scores o ledger; tampoco test, envíos, remoto, publicación externa o delegación. Sigue pendiente revisión humana. Se aplican gobernanza IAA §2.8 y §§3.3.2,3.4–3.6, documentación §§2–3 y consideraciones profesionales §3.3 sin convertirlas en certificación.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda raw:raw+note)
change(ROOT/'Preparación/DECISIONES.md',lambda raw:raw+note)
update='\n\n## Estabilidad y nuevo negocio, cuarta prueba de 2023\n\nLa [revisión de B08/B09 y la prueba preinscrita](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md) muestra sensibilidad del nivel de B08 al reentrenar sin grupos severos. B10/B11 mejoran sus puntos globales y el nivel de nuevo negocio, con ventajas inciertas sobre sus padres y deterioro en edificios nuevos. Se conservan B00 y B01–B11, sin promoción o lista final congelada. 2024 sigue expresamente cerrado. El [índice activo](../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conserva cuatro tandas.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md',lambda raw:raw+'\n\n## Corte posterior: estabilidad y negocio\n\nLa [cuarta prueba](DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md) revisa B08/B09 y contrasta factores por negocio y un estrés de reentrenamiento. El [snapshot del índice de esta tercera tanda](../../registro/semana2_desarrollo2023_v3_snapshot.json) conserva exactamente su registro. Este documento y sus cifras mantienen su corte original.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_development_execution',{'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
 'status':'four_2023_trials_verified_reference_retained','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
 'historical_counter_notice':'Los contadores del corte de preparación permanecen históricos. Corridas/factores/estrés y snapshots en índice de desarrollo.'}))
dump(REPO/'registro/semana2_desarrollo2023_pruebas_v4.json',{'author':'Codex','utc':NOW,'verification':index['verification'],'fixtures':index['fixtures'],'source':'Own checks, not independent professional validation','confirmation_2024_open':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper responses observed in this task','receipts':[
 {'id':'COD-S2-20261023-014','utc':'2026-10-23T20:45:49+00:00','previous_sha256':'f388b1303d1bec007ff674fa4d5d0b78ccbf2fcea3c80300164456689aea1eb3','sha256_at_append':'543bfcce61ebb7751a5b91193f1010e7ff3589763141776c4547d98796ef13f8'},
 {'id':'COD-S2-20261023-015','utc':'2026-10-23T20:54:26+00:00','previous_sha256':'543bfcce61ebb7751a5b91193f1010e7ff3589763141776c4547d98796ef13f8','sha256_at_append':'5fe5f9d0da091f33757f9802c86c3cc789615a8fe6b407c6414c2952ec23e514'}]})
checks=[]
def check(name,val):checks.append({'name':name,'pass':bool(val)})
for key in ['report','plan','producer','oof','manifest','assessment','stress_oof']:check('Active hash '+key,sha(ROOT/index[key])==index[key+'_sha256'])
for key in ['verification','fixtures']:check('Active check '+key,sha(ROOT/index[key]['path'])==index[key]['sha256'] and read(ROOT/index[key]['path'])['failed']==0)
check('V3 snapshot exact',SNAP.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json')
check('Other routes preserved',all(newroutes.get(k)==v for k,v in oldroutes.items() if k not in ['week_2_development_report','week_2_development_plan','week_2_development_oof']))
for k,val in newroutes.items():
    if k.startswith('week_2_'):check('Route '+k,(ROOT/val).exists())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Earlier state branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum']))
for item in changes:
    if item['path'].endswith('.md'):check('Previous prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
docs=[ROOT/index['documentation'],REPO/'docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]
for doc in docs:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Local link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in read(RUN/'frozen_sources_before_fit.json')['files']:check('Source retained '+it['path'],sha(ROOT/it['path'])==it['sha256'])
for suffix in ['014','015']:check('Unique forum '+suffix,forum.read_bytes().count(('<!-- aporte:COD-S2-20261023-'+suffix+' -->').encode())==1)
check('B00 and eleven alternatives',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==11 and not index['promotion'])
check('2024 ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists())
result={'utc':NOW,'scope':'Registration and links integrity, no repeated statistical tests or training','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
files={p for p in RUN.rglob('*') if p.is_file()};files.update(ROOT/x['path'] for x in changes)
files.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],SNAP,Path(__file__),forum,REPO/'registro/semana2_desarrollo2023_pruebas_v4.json'])
files.update(REPO/'herramientas'/f'{name}_desarrollo2023_v4_semana2.py' for name in ['documentar','probar','verificar'])
files.add(REPO/'herramientas/revisar_estabilidad2023_semana2.py')
files.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_desarrollo2023_v4.py','desarrollo2023_v4_preinscripcion.md','desarrollo2023_v4_resultado.md'])
reviewdir=(ROOT/plan['diagnostic_review']).parent;files.update(p for p in reviewdir.rglob('*') if p.is_file())
failed=REPO/'privado/semana2/desarrollo2023/dev4_20261023T204705Z_3a937001';files.update(p for p in failed.rglob('*') if p.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte de cierre; manifiestos anteriores conservan su corte. Los archivos compartidos pueden cambiar después con evidencia nueva.',
 'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'reference':'W2-B00','promotion':False,'confirmation_2024_open':False})
print(json.dumps({'index':rel(ACTIVE),'checks':result['passed'],'failed':result['failed'],'reference':'W2-B00','confirmation_2024_open':False}))
