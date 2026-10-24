"""Registra entradas para el primer entrenamiento, conservando cortes anteriores."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766'
VERIFY=RUN/'verifications/20261023T171434Z_32028237.json'
NOW=datetime.now(timezone.utc).isoformat();BOGOTA=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
report=json.loads((RUN/'report.json').read_text(encoding='utf-8'))
verify=json.loads(VERIFY.read_text(encoding='utf-8'))
tests=json.loads((REPO/'registro/semana2_variables_ultimo_pruebas.json').read_text(encoding='utf-8'))
env=json.loads((REPO/'registro/semana2_contrato_entrenamiento_comprobacion.json').read_text(encoding='utf-8'))
assert len(report['checks'])==194 and all(x['pass'] for x in report['checks'])
assert verify['failed']==0 and verify['passed']==1138 and tests['passed']==20 and env['passed']==9
BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
changes=[]


def top(raw,key,value,replace=False):
    encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if replace:
        m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
        _,end=json.JSONDecoder().raw_decode(raw[m.end():])
        return raw[:m.end()]+encoded+raw[m.end()+end:]
    assert key not in json.loads(raw),key
    return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'


def change(p,fn):
    before=p.read_bytes();backup=BACK/p.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8')
    assert p.read_bytes()==before,'Cambio concurrente '+str(p)
    stage=p.with_name(p.name+'.s2vu.tmp')
    with stage.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==before,'Cambio concurrente '+str(p)
    os.replace(stage,p)
    changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p),'backup':rel(backup)})


index={'id':'S2-F0-ULT-20261023','author':'Codex','as_of_utc':NOW,'path_base':'workspace_root',
    'status':'technically_ready_for_initial_price_training_under_declared_assumptions',
    'run':rel(RUN),'report':rel(RUN/'report.json'),'report_sha256':sha(RUN/'report.json'),
    'producer':'Hackaton/Repositorio_IAA2026/src/semana2/variables_ultimo.py','producer_sha256':report['code_sha256'],
    'plan':'Hackaton/Repositorio_IAA2026/registro/semana2_variables_ultimo_plan.json','plan_sha256':report['plan_sha256'],
    'availability_contract':rel(RUN/'availability_contract.json'),'availability_sha256':sha(RUN/'availability_contract.json'),
    'training_contract':'Hackaton/Repositorio_IAA2026/registro/semana2_contrato_entrenamiento.json',
    'documentation':'Hackaton/Repositorio_IAA2026/docs/semana2/VARIABLES_Y_ULTIMO.md',
    'base_index':'Hackaton/Repositorio_IAA2026/registro/semana2_preparacion_actual.json',
    'base_target_sha256':report['base_target_sha256'],'partitions_sha256':report['partitions_sha256'],
    'F0':{line:{'path':rel(RUN/f'F0_{line}.parquet'),'sha256':sha(RUN/f'F0_{line}.parquet'),'feature_count':len(json.loads((RUN/'availability_contract.json').read_text(encoding='utf-8'))['blocks'][line]['all'])} for line in ['motor','buildings','contents']},
    'features':report['features'],'capital_uncertainty_audit':rel(RUN/'capital_uncertainty_audit.parquet'),
    'scope_mapping':{'temporal':'temporal_2024','development_fold_k':'exclude_foldk','cold_fold_k':'exclude_foldk','final_refit':'production_2025'},
    'scopes':7,'peril_reporting_curves':105,'price_models_trained':0,'price_model_inference':0,
    'reporting_estimation_performed':True,'reserve_development_fitted':False,
    'readiness':report['readiness'],'conditions':report['conditions'],
    'weather2025':{'default':False,'official_availability_clarified':False,'past_weather_variant':'Last full calendar year before inferred quote date; missing years not backfilled','future_poisoning_invariant_verified':True},
    'ultimate_link':{'base_reserve_factor':1.,'reserve_stresses':[.75,1.25],'tail_cost_mass_stresses_long_perils':[.05,.10],
        'unseen_tail_location':'after maximum 730-day observed calendar window','double_IBNR_forbidden':True,
        'target_truth':'T0 retained as observed incurred; no fabricated ultimate labels','line_cost_mix':'fit-only approximation; per-peril links retained'},
    'temporal_2024_observation_links':report['scopes'][0]['observation_link'],
    'checks':{'producer':194,'separate_checker':1138,'known_answer_and_poisoning_cases':20,'loss_identity_and_imports':9,'counts_overlap':True},
    'verification':{'path':rel(VERIFY),'sha256':sha(VERIFY),'failed':0},'environment_check':'Hackaton/Repositorio_IAA2026/registro/semana2_contrato_entrenamiento_comprobacion.json',
    'forum_prior':'COD-S2-20261023-004','forum_result':'COD-S2-20261023-005',
    'human_general_review_complete':False,'independent_professional_validation':False,
    'scope':'Preparation and reporting-pattern estimation; requested readiness statement. No price training, submissions, remote jobs, publication or new delegation.'}
active=REPO/'registro/semana2_listo_entrenar.json'
with active.open('x',encoding='utf-8') as f:json.dump(index,f,ensure_ascii=False,indent=2);f.write('\n')


def routes(raw):
    for k,p in {'week_2_training_readiness_index':active,'week_2_variables_ultimate_report':REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md',
        'week_2_feature_availability':RUN/'availability_contract.json','week_2_training_contract':REPO/'registro/semana2_contrato_entrenamiento.json'}.items():
        assert p.exists();raw=top(raw,k,rel(p))
    return raw


def state(raw):
    raw=top(raw,'memory_as_of',BOGOTA,True)
    raw=top(raw,'current_phase',{'as_of_utc':NOW,'phase':'week2_ready_for_first_price_training_conditional_ultimate','current_state_key':'week_2_variables_ultimate_20261023','historical_fields_notice':'Los índices anteriores conservan sus cortes. La disponibilidad actual y el vínculo a último se consultan en semana2_listo_entrenar.json.'},True)
    forum=json.loads(raw)['collaboration_forum'];forum.update({'latest_Codex_comment':'COD-S2-20261023-005','updated_utc':NOW})
    raw=top(raw,'collaboration_forum',forum,True)
    return top(raw,'week_2_variables_ultimate_20261023',{'id':index['id'],'as_of_utc':NOW,'path_base':'workspace_root','index':rel(active),'documentation':index['documentation'],
        'status':index['status'],'default_features':{'motor':40,'buildings':32,'contents':33},'weather_2025_default':False,'capital_masked_train':110,'capital_masked_test':239,
        'reporting_scope_curves':105,'scopes':7,'price_models_trained':0,'readiness':report['readiness'],'forum_decisions':[index['forum_prior'],index['forum_result']],
        'pending':['human review','ultimate/reserve adequacy not identifiable with one valuation','weather2025 interpretation remains unconfirmed; excluded default','score and sensitivity of price models not yet measured']})


memory='''

## Segunda semana: variables y vínculo de observación listos para las primeras referencias

Codex, 23 de octubre de 2026. Por petición directa del participante se revisaron variables, clima 2025, reporte tardío y reservas; decisiones previas COD-S2-20261023-004 y resultado COD-S2-20261023-005. El índice actual es Hackaton/Repositorio_IAA2026/registro/semana2_listo_entrenar.json y el informe está en docs/semana2/VARIABLES_Y_ULTIMO.md del repositorio común. La preparación permite iniciar las primeras referencias de precio bajo supuestos declarados; no se ha entrenado un modelo de precios.

F0 contiene 40 predictores de autos, 32 de edificios y 33 de contenidos. Admite datos contractuales y físicos bajo estabilidad del maestro y antigüedad del cliente; excluye identificadores como predictores, resultados, folds/grupos, contactos, decisiones de renovación, prima/descuento y perfiles sin fecha. Género queda fuera de la base aunque el diccionario permita usarlo. Sin imputación/codificación aprendida fuera de los folds. Capitales de escala incierta: logaritmo ausente en 110 filas de entrenamiento y 239 de test, sin dividir por mil ni cambiar originales; filtros de revisión 10 millones/1 millón, no límites de cobertura.

Kaggle sigue describiendo clima 2023–2024 y no aclara la disponibilidad del clima anual 2025. Los valores de 2025 difieren de 2024 y quedan fuera del modelo inicial. La tabla histórica usa solo el último año completo anterior a cotización inferida; en 2023 no existe ese historial y no se fabrica. Hay 18.774 filas de entrenamiento con historial y todas las de test, por lo que la variante no está aún validada como predictor. La sustitución de valores 2025 por extremos no cambia el bloque histórico.

Se estimaron patrones actuariales de reporte, distintos de entrenamiento de precios: producto-límite en tiempo inverso, por ramo/peligro y dentro del ajuste de cada partición; siete ámbitos y 105 curvas de conteos, con coste marcado bajo reserva b=0,75/1/1,25. Se tienen en cuenta truncamiento y asociación observada coste-demora, bajo estacionariedad e independencia del calendario de truncamiento. En 2023 hay 35 aceptados reportados después de 365 días, 24 de lesiones; una distribución empírica ingenua de 2024 no representa el último. No se usó la prehistoria excluida como muestra representativa de la cola.

La exposición efectiva integra completitud por días de cobertura. El modelo condicional aprende sobre T0 y exposición efectiva; 2025 usa exposición nominal, sin agregar otro IBNR o reserva. La mezcla de peligros por ramo es una aproximación y se conservan vínculos por peligro. Completitud de coste de 2024 ponderada por exposición y estimada con 2023: 80,64 % autos, 95,27 % edificios y 96,98 % contenidos. Son estimaciones condicionadas, no porcentajes de último comprobados.

La reserva ya está en T0. b=1 es una hipótesis condicional, no suficiencia acreditada; b=0,75/1,25 cambia solo la reserva y recalcula curvas de coste. La historia no identifica la cola fuera de su ventana: se prepararon escenarios de 5 %/10 % de masa de coste posterior a 730 días para lesiones/hundimiento. No son probabilidades estimadas. Reaperturas, desarrollo de reservas y recuperaciones siguen sin identificarse con una valoración; no se trasladó la aceptación de límites de S41 como nueva aprobación emergente.

Corrida: Hackaton/Repositorio_IAA2026/privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766. Pasaron 194 controles de preparación, 1.138 del comprobador separado, veinte casos conocidos/metamórficos y nueve de escala de pérdida/importaciones; los recuentos se solapan. Se verificaron originales, T0 y folds sin cambios. Para ajustar tasas con pérdida Tweedie total unitaria p=1,5 se fijó respuesta Y/e y peso sqrt(e), con identidad comprobada; cada ámbito mantiene su propio vínculo. El entorno importa scikit-learn 1.7.2, LightGBM 4.6.0 y CatBoost 1.2.8.

Estado técnico: listos para las primeras referencias F0 sobre T0 y para una variante a último condicional a las hipótesis de reserva, cola y reporte. No se conoce todavía su desempeño predictivo ni se acredita último observado, suficiencia o revisión profesional independiente. Sin modelos de precio ajustados, inferencia de precios, envíos, remoto, publicaciones, automatizaciones o delegación. Fuentes y límites de acceso conservados; S41 y recetas históricas intactos.
'''
decision='''

## S2-F0-ULT-20261023: disponibilidad, reporte y supuestos para empezar a entrenar

Codex, 23 de octubre de 2026, por petición del participante. Preinscripción COD-S2-20261023-004; resultado COD-S2-20261023-005. Índice vigente: ../Hackaton/Repositorio_IAA2026/registro/semana2_listo_entrenar.json. Decisiones técnicas verificadas, sin atribuir revisión humana general.

Se admite F0 contractual/físico bajo estabilidad del maestro, con listas exactas de 40/32/33 predictores. Se excluyen resultados, claves como predictores, contactos, renovación posterior, tarifa, perfiles sin fecha y género del bloque inicial. Clima 2025 fuera por disponibilidad no confirmada; variante histórica con último año completo anterior a cotización, sin relleno futuro. Capitales en la agrupación de escala incierta se representan como log-capital desconocido (110 train/239 test), sin corrección automática por mil; filtros de calidad no son límites contractuales.

Se adopta un vínculo de observación basado en producto-límite truncado por peligro, estimado solo con el ajuste de cada partición. Se separan conteos y coste marcado para no imponer independencia de severidad y demora. Siete ámbitos, cinco grupos persistidos sin cambio y 105 curvas, reutilizando los ámbitos de desarrollo para población nueva. La valoración única y los supuestos de estacionariedad impiden afirmar prospectividad o identificación completa del último.

Se conserva la reserva ya incluida en T0. Base b=1 condicional y sensibilidades b=0,75/1,25, con recálculo de marcas y mezclas. La cola no observada permanece no identificada; 5 %/10 % de masa de coste posterior a 730 días en lesiones/hundimiento son escenarios de diseño. No se certifica suficiencia, no se usan factores S41 y no se agrega dos veces IBNR. Para 2025 la tasa ajustada se multiplica solo por exposición nominal; el proxy observado de validación usa su exposición efectiva del ámbito correspondiente.

Se fija el contrato de pérdida para tasas: Y/e y peso e^(2-p), con p=1,5, para alinear devianza de totales sin pesos adicionales de evaluación. Las listas, matrices, curvas, casos conocidos y dependencias pasaron los controles. Se declara disponibilidad técnica para entrenar las primeras referencias, con las condiciones publicadas y sin seleccionar un modelo ni conocer aún su score. El encargo actual termina en preparación y aviso de disponibilidad; no ejecutó entrenamiento de precios o envíos. La revisión humana y la incertidumbre del último conservan su alcance.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
change(ROOT/'Preparación/MEMORIA_PROYECTO.md',lambda x:x+memory)
change(ROOT/'Preparación/DECISIONES.md',lambda x:x+decision)
change(ROOT/'Hackaton/Semana 2/README.md',lambda x:x+'\n\n## Variables y vínculo a último preparados\n\nEl [informe de variables y último](../Repositorio_IAA2026/docs/semana2/VARIABLES_Y_ULTIMO.md) y el [índice para entrenar](../Repositorio_IAA2026/registro/semana2_listo_entrenar.json) identifican las matrices y ámbitos actuales. Hay disponibilidad técnica para iniciar referencias F0, con clima 2025 excluido y supuestos explícitos de reporte, reserva y cola. Se estimaron patrones de reporte; todavía no se entrenaron modelos de precio.\n')
change(ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',lambda x:x+'\n\n## Avance del 23 de octubre: entradas listas para las primeras referencias\n\nLas [variables y el vínculo de observación](../Repositorio_IAA2026/docs/semana2/VARIABLES_Y_ULTIMO.md) ya están preparados y verificados. El [contrato de entrenamiento](../Repositorio_IAA2026/registro/semana2_contrato_entrenamiento.json) fija listas, ámbitos, pérdida y tratamiento único de IBNR. El bloque base excluye clima 2025 y variables posteriores; la interpretación a último depende de las hipótesis declaradas, con sensibilidades de reserva y cola. Siguiente trabajo: medir las referencias previstas, sin cambiar los folds ni atribuirles un score todavía. Las entradas anteriores conservan sus cortes.\n')
dump={'id':index['id'],'utc':NOW,'index':rel(active),'changes':changes,'pricing_models_trained':0}
(RUN/'registration.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'index':rel(active),'shared_files':[x['path'] for x in changes]},ensure_ascii=True))
