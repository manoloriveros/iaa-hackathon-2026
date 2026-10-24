"""Registra la preparación ya verificada, sin cambiar receta o modelos de semana 1."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
REPORT=RUN/'report.json'
VERIFY=RUN/'verifications/20261023T164607Z_90a4bf51.json'
NOW=datetime.now(timezone.utc).isoformat()
BOGOTA=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(REPORT.read_text(encoding='utf-8'))
v=json.loads(VERIFY.read_text(encoding='utf-8'))
assert v['failed']==0 and v['passed']==106
assert all(x['pass'] for x in r['checks'])
assert len(r['checks'])==78
BACK=RUN/'shared_state_before_registration'
BACK.mkdir(exist_ok=False)
changes=[]


def rel(p): return p.relative_to(ROOT).as_posix()


def replace_top(raw,key,value):
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw)
    assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():])
    return raw[:m.end()]+json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')+raw[m.end()+end:]


def add_top(raw,key,value):
    assert key not in json.loads(raw),key
    i=raw.rfind('}')
    return raw[:i].rstrip()+',\n  '+json.dumps(key)+': '+json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')+'\n}\n'


def change(path,transform):
    before=path.read_bytes()
    backup=BACK/path.relative_to(ROOT)
    backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f: f.write(before)
    after=transform(before.decode('utf-8-sig')).encode('utf-8')
    assert path.read_bytes()==before,'Cambio concurrente: '+str(path)
    stage=path.with_name(path.name+'.s2base.tmp')
    with stage.open('xb') as f:
        f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Cambio concurrente: '+str(path)
    os.replace(stage,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})


index={
    'id':'S2-BASE-20261023','author':'Codex','as_of_utc':NOW,'path_base':'workspace_root',
    'status':'observed_T0_and_partitions_prepared_verified_no_training',
    'scope_authorized_literal':'Dale, empieza por conciliar la exposición y revisar los 36 siniestros sin periodo. Prepara el objetivo y las particiones de validación, y deja las decisiones en el foro antes de entrenar.',
    'run':rel(RUN),'report':rel(REPORT),'report_sha256':sha(REPORT),
    'plan':'Hackaton/Repositorio_IAA2026/registro/semana2_preparacion_plan.json','plan_sha256':r['plan_sha256'],
    'documentation':'Hackaton/Repositorio_IAA2026/docs/semana2/PREPARACION_BASE.md',
    'producer':'Hackaton/Repositorio_IAA2026/src/semana2/preparar_base.py','producer_sha256':r['code_sha256'],
    'target':rel(RUN/'target_T0_and_stresses.parquet'),'target_sha256':sha(RUN/'target_T0_and_stresses.parquet'),
    'partitions':rel(RUN/'partitions.parquet'),'partitions_sha256':sha(RUN/'partitions.parquet'),
    'splits_directory':rel(RUN/'splits'),'group_membership':rel(RUN/'group_membership_training_only.parquet'),
    'claim_audit':rel(RUN/'claim_assignment_audit.parquet'),'precoverage_claims':rel(RUN/'precoverage_claims_36.parquet'),
    'exposure_changes':609,'days_unit':114,'basis360':495,'test_exposure_changes':0,
    'exposure_rule':'Inclusive covered days / 365, round 4 decimals; no date-value changes; original preserved',
    'training_exposure_before':127105.4490,'training_exposure_after':91494.5253,
    'claims':r['claims'],'money_reconciliation_cents':r['money_reconciliation_cents'],
    'target_type':'Observed net incurred as at 2024-12-31, not observed ultimate','train_rows':109296,'test_rows_with_null_labels':209063,
    'groups':r['groups'],'temporal_split':{'fit_2023_rows':50094,'evaluate_2024_rows':59202},
    'development_group_folds':5,'cold_2024_group_folds':5,'seed':'IAA2026-S2-GROUPS-v1',
    'target_and_group_ids_not_predictors':True,
    'producer_checks':78,'separate_checker':{'report':rel(VERIFY),'sha256':sha(VERIFY),'passed':106,'failed':0,'professional_independent_validation':False},
    'adversarial_cases':{'report':'Hackaton/Repositorio_IAA2026/registro/semana2_pruebas_casos.json','passed':19,'failed':0,'source_sha256':sha(REPO/'herramientas/probar_preparacion_semana2.py')},
    'first_checker_issue':{'report':rel(RUN/'verification.json'),'passed':100,'failed':6,'cause':'Checker compared date text with timestamps; final checker normalizes representation, without temporal tolerance; prepared layer unchanged'},
    'forum_prior_decision':'COD-S2-20261023-002','forum_result':'COD-S2-20261023-003',
    'training_performed':False,'model_inference_performed':False,'reporting_completion_fitted':False,'reserve_development_fitted':False,
    'feature_matrix_prepared':False,'ultimate_target_observed':False,'week1_recipe_modified':False,
    'pending':['feature availability contract including 2025 weather','reporting completeness and reserve uncertainty before interpreting performance on ultimate','human review'],
    'historical_note':'Previous diagnostic and opening manifests retain their original cuts; 452 above-one flags are replaced by 609 reconciled exposure changes for the active derived layer.'}
index_path=REPO/'registro/semana2_preparacion_actual.json'
with index_path.open('x',encoding='utf-8') as f:json.dump(index,f,ensure_ascii=False,indent=2);f.write('\n')


def state(raw):
    raw=replace_top(raw,'memory_as_of',BOGOTA)
    raw=replace_top(raw,'current_phase',{'as_of_utc':NOW,'phase':'week2_observed_target_and_validation_prepared','current_state_key':'week_2_base_preparation_20261023','historical_fields_notice':'El diagnóstico de apertura conserva su corte anterior; consultar la preparación actual para las correcciones y particiones.'})
    current=json.loads(raw)['collaboration_forum']
    current.update({'latest_Codex_comment':'COD-S2-20261023-003','updated_utc':NOW})
    raw=replace_top(raw,'collaboration_forum',current)
    return add_top(raw,'week_2_base_preparation_20261023',{'id':index['id'],'as_of_utc':NOW,'path_base':'workspace_root','status':index['status'],'index':rel(index_path),'run':rel(RUN),'documentation':index['documentation'],'exposure_changes':609,'precoverage_claims':36,'assigned_accepted_claims':9102,'T0_CU':27997991.57,'training_rows':109296,'test_rows_unlabelled':209063,'temporal_train_rows':50094,'temporal_validation_rows':59202,'groups':36398,'folds':5,'forum_decisions':['COD-S2-20261023-002','COD-S2-20261023-003'],'training_performed':False,'target_is_observed_ultimate':False,'human_review':'pending','pending':index['pending']})


def routes(raw):
    for k,value in {'week_2_preparation_index':rel(index_path),'week_2_preparation_report':index['documentation'],
        'week_2_prepared_targets':index['target'],'week_2_validation_partitions':index['partitions']}.items():
        assert (ROOT/value).exists(),value
        raw=add_top(raw,k,value)
    return raw


memory='''

## Segunda semana: exposición conciliada, objetivo observado y particiones preparadas

Codex, 23 de octubre de 2026. El participante pidió conciliar la exposición, revisar los 36 siniestros sin periodo y preparar objetivo y particiones, dejando las decisiones en el foro antes de entrenar. Preinscripción COD-S2-20261023-002 y resultado COD-S2-20261023-003. Código y registros nuevos en el repositorio común; artefactos por fila en privado/semana2/preparacion, fuera de Git. S41 y la receta anterior no cambian.

La conciliación exacta detectó 609 exposiciones incorrectas: 114 guardadas como días y 495 con divisor 360. Las otras 108.687 filas de entrenamiento y las 209.063 de test coinciden con días inclusivos/365 redondeados a cuatro decimales. Se adoptó esa regla sin cambiar días de cobertura; se conservan valor original, razón y delta. La suma de exposición de entrenamiento pasa de 127.105,4490 a 91.494,5253 años. La referencia exploratoria 365,25 no se adoptó. Los 452 valores mayores que uno del primer diagnóstico eran una detección parcial, no el total de errores.

Los 36 siniestros son anteriores al primer inicio disponible de su propia póliza y ramo. Los dos de 2023 lo anteceden en 166 y 175 días. Se conservan en auditoría y se excluyen del coste de estos periodos, por 92.267,26 CU netos. No se fuerzan asignaciones ni se presume su disponibilidad histórica como variables. Quedan 9.102 aceptados asignados y 120 rechazados excluidos; no hay ambigüedades u otros casos sin explicar.

T0 suma 27.997.991,57 CU de incurrido neto observado: incurrido 28.898.003,92 menos recuperaciones 900.012,35. Pagos, reserva y conteos se guardan aparte y concilian en centavos. Las 109.296 filas de entrenamiento tienen etiqueta, incluidos 101.225 ceros legítimos; las etiquetas de test permanecen nulas. Las sensibilidades de reserva 0,75/1,25 son escenarios de diseño. No se estimó reporte pendiente ni desarrollo de reserva y T0 no se presenta como último observado.

Se persistieron cinco folds de desarrollo 2023, contraste temporal con 50.094 filas de ajuste 2023 y 59.202 de evaluación 2024, cinco pruebas de población nueva sin clientes o direcciones compartidos y roles de producción 2023–2024/test 2025. Son 36.398 componentes de cliente-dirección, máximo doce periodos; semilla y hash fijos, sin etiquetas ni enlaces del test. Cada fila de 2024 se valida una vez en las cinco pruebas de población nueva. Solo alrededor del 15,3 % de las filas de 2024 son de clientes nuevos por ramo, frente a cerca del 76 % del test. La única valoración común impide afirmar un backtest plenamente prospectivo.

Corrida: Hackaton/Repositorio_IAA2026/privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3. Pasaron 78 controles internos, 106 del comprobador separado y diecinueve casos adversos/de límites; los grupos se solapan. Se conserva un primer informe con seis fallos del comparador de fechas de texto frente a timestamps; se corrigió solo el comprobador, sin regenerar la capa. Las fechas normalizadas y demás campos coinciden con los originales. No es validación profesional independiente.

Índice vigente: Hackaton/Repositorio_IAA2026/registro/semana2_preparacion_actual.json. Informe: docs/semana2/PREPARACION_BASE.md dentro del repositorio. Rutas añadidas al mapa raíz. Siguen pendientes matriz de predictores, contrato de disponibilidad (clima 2025 incluido), puente a último y revisión humana. Sin entrenamiento, calibración, inferencia de modelos, envíos, remoto, publicaciones, automatizaciones o delegación.
'''
decision='''

## S2-BASE-20261023: reglas de exposición, prehistoria, T0 y particiones

Codex, 23 de octubre de 2026, por instrucción directa del participante. Las decisiones se preinscribieron en COD-S2-20261023-002 y se materializaron sin entrenar; el resultado se publica como COD-S2-20261023-003. El índice vigente es ../Hackaton/Repositorio_IAA2026/registro/semana2_preparacion_actual.json y el informe está en docs/semana2/PREPARACION_BASE.md del repositorio común.

Se adopta para emerging la exposición de días inclusivos/365 a cuatro decimales, respaldada por las filas normales y todo el test: 609 correcciones, 114 por unidades y 495 por divisor 360. Fechas y originales se conservan. Los 36 siniestros anteriores al primer inicio disponible quedan auditados y fuera del objetivo de estos periodos, sin reasignación; los dos de 2023 son pre-cobertura por 166 y 175 días.

Se materializa T0 como incurrido neto observado de aceptados asignados, calculado en centavos y separado del coste último. Total 27.997.991,57 CU, 9.102 aceptados asignados, 120 rechazados excluidos y 36 pre-cobertura excluidos. Todos los periodos de entrenamiento permanecen; las etiquetas de test son nulas. Las sensibilidades de reserva 0,75/1,25 son estrés de diseño y no una estimación de último.

Se fijan cinco folds por componentes de cliente-dirección entre los ramos de entrenamiento, independientes de etiquetas y sin enlaces del test, con semilla IAA2026-S2-GROUPS-v1. Desarrollo agrupado dentro de 2023; contraste temporal 2023→2024; cinco pruebas de población nueva que retienen el mismo grupo en 2024 y lo excluyen de 2023; producción futura con todos los años etiquetados. Cada fila se evalúa una sola vez dentro de cada familia de folds. No se declara prospectividad histórica completa con la valoración única de 2024.

La corrida base_20261023T164102Z_b3e6c2a3 pasa controles de productor y comprobador separado. Se conserva el primer fallo del comparador de fechas y su corrección, sin cambiar la capa. Las comprobaciones propias de Codex no se presentan como revisión profesional independiente. Las decisiones son técnicas dentro del alcance autorizado; no afirman revisión humana general, ajuste del puente a último ni entrenamiento. S41 y las recetas históricas permanecen intactos.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda x:x+memory)
change(ROOT/'Preparación/DECISIONES.md',lambda x:x+decision)
change(ROOT/'Hackaton/Semana 2/README.md',lambda x:x+'\n\n## Base y particiones preparadas el 23 de octubre\n\nLa [preparación verificada](<../Repositorio_IAA2026/docs/semana2/PREPARACION_BASE.md>) contiene la exposición conciliada, auditoría de los 36 casos, T0 observado y particiones persistidas. El [índice activo](../Repositorio_IAA2026/registro/semana2_preparacion_actual.json) identifica las rutas y huellas. Se corrigieron 609 exposiciones de entrenamiento; los originales y el test no cambian. T0 suma 27.997.991,57 CU y no equivale al coste último observado. No se ha entrenado un modelo.\n')
change(ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',lambda x:x+'\n\n## Avance del 23 de octubre: preparación materializada\n\nLa exposición, asignación y objetivo observado T0 ya están conciliados, con cinco folds de desarrollo y población nueva y un contraste temporal 2023→2024 persistidos antes del primer modelo. Consultar [la preparación](<../Repositorio_IAA2026/docs/semana2/PREPARACION_BASE.md>) y las decisiones COD-S2-20261023-002/003 del foro. Las tablas anteriores conservan el plan de apertura. Siguen abiertos el contrato de predictores y el puente de T0 a último; no hay modelos entrenados ni resultados de validación predictiva.\n')
record={'id':index['id'],'registered_utc':NOW,'index':rel(index_path),'shared_changes':changes,'training':False}
(RUN/'registration.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'index':rel(index_path),'shared_updates':[x['path'] for x in changes]},ensure_ascii=True))
