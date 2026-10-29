"""Conclusiones de la segunda tanda desde modelos y OOF ya congelados."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('doc_v2_checker',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq
read=c.read;sha=c.sha;rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x));f.write('\n')
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
report=read(run/'report.json');plan=read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];review=read(ROOT/plan['diagnostic_review'])
verification_path=sorted((run/'verifications').glob('*.json'))[-1];verification=read(verification_path)
assert verification['failed']==0 and all(x['technical_complete'] for x in report['summary'])
oof=pq.read_table(run/'oof_2023.parquet').to_pandas();assert oof.year.eq(2023).all()
points={x['model_id']:x for x in report['summary']};train={x['model_id']:x for x in report['training_summary']}
segments=read(run/'diagnostics/segments.json');pairs=read(run/'diagnostics/pairs.json')['pairs']
segment=lambda mid,dim,label:next(x for x in segments if x['model_id']==mid and x['segment']==dim and x['label']==label)
old_training=read(parent/'diagnostics/fit_vs_oof.json')['nodes'];new_training=read(run/'diagnostics/training_nodes.json')
building_null=segment('W2-B00','line','buildings')['null_deviance_sum'];building={};coefs={}
for mid,folder in [('W2-B01',parent),('W2-B03',run)]:
    entries=old_training if mid=='W2-B01' else new_training
    field='training_deviance_sum' if mid=='W2-B01' else 'deviance_sum'
    total=sum(x[field] for x in entries if x['model_id']==mid and x['line']=='buildings')
    base=segment(mid,'line','buildings');train_D2=1-total/(4*building_null)
    rows=[]
    for fold in range(5):
        bundle=c.joblib.load(folder/'models'/f'{mid}_buildings_fold{fold}'/'bundle.joblib')
        rows.extend({'feature':str(name),'fold':fold,'coefficient':float(value)} for name,value in zip(bundle['transformer'].get_feature_names_out(),bundle['estimator'].coef_))
    matrix=pd.DataFrame(rows).pivot(index='feature',columns='fold',values='coefficient').fillna(0)
    coefs[mid]={'features':len(matrix),'mean_std_across_folds':float(matrix.std(axis=1).mean()),
                'mean_squared_norm':float(np.mean(np.sum(matrix.to_numpy()**2,axis=0)))}
    building[mid]={'OOF_D2':base['D2'],'training_D2':train_D2,'gap':train_D2-base['D2'],
                   'A_over_E':base['actual_over_expected'],'coefficient_stability':coefs[mid]}
error_blocks=[]
baseline=oof.loc[oof.model_id.eq('W2-B00')&oof.line.eq('buildings')].sort_values(c.KEY).reset_index(drop=True)
for mid in ['W2-B01','W2-B03']:
    part=oof.loc[oof.model_id.eq(mid)&oof.line.eq('buildings')].sort_values(c.KEY).reset_index(drop=True)
    assert part[c.KEY].equals(baseline[c.KEY])
    for positive in [False,True]:
        mask=part.T0.gt(0).eq(positive)
        error_blocks.append({'model_id':mid,'positive':positive,'rows':int(mask.sum()),
            'advantage_over_reference_full_buildings_null':float((baseline.loc[mask,'unit_deviance'].sum()-part.loc[mask,'unit_deviance'].sum())/building_null)})
readout={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'fit_calls':0,'year':2023,'building_GLM':building,
         'building_error_blocks':error_blocks,'diagnostic_expectations':{
            'B03_building_point_improves_and_gap_shrinks':building['W2-B03']['OOF_D2']>building['W2-B01']['OOF_D2'] and building['W2-B03']['gap']<building['W2-B01']['gap'],
            'B04_global_point_improves_and_gap_shrinks':points['W2-B04']['D2']>points['W2-B02']['D2'] and train['W2-B04']['gap_train_minus_OOF']<train['W2-B02']['gap_train_minus_OOF'],
            'B05_global_point_improves_and_gap_shrinks':points['W2-B05']['D2']>points['W2-B02']['D2'] and train['W2-B05']['gap_train_minus_OOF']<train['W2-B02']['gap_train_minus_OOF']},
         'meaning':'These are the predeclared descriptive mechanisms, not acceptance of a candidate or a promotion test',
         'source':rel(Path(__file__)),'source_sha256':sha(Path(__file__))}
dump(run/'diagnostics/mechanism_readout.json',readout)
reference_pairs=[x for x in pairs if x['candidate'] in ['W2-B03','W2-B04','W2-B05'] and x['reference']=='W2-B00']
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'reference_retained':'W2-B00',
    'all_alternatives_preserved':['W2-B01','W2-B02','W2-B03','W2-B04','W2-B05'],'promotion':False,
    'original_B02_warning_not_closed':'DEV2023-B02-GENERALIZATION and S2-VAL-MOD-007 apply to the unchanged original recipe; new IDs do not resolve them',
    'warnings':[
      {'id':'DEV2-2023-UNCERTAINTY','class':'condition','status':'open','effect':'Each new-vs-reference 95% exploratory interval crosses zero; none establishes superiority/equivalence. No promotion.'},
      {'id':'DEV2-2023-INFLUENCE','class':'condition','status':'open','effect':'All three advantages turn negative when 31 most favorable components are removed as predeclared diagnostic; retain full objective and reference.'},
      {'id':'DEV2-2023-LEVEL','class':'condition','status':'open','effect':'Observed aggregate levels remain low; stronger building GLM improves deviance while A/E worsens. No implicit rescaling or claim of ultimate sufficiency.'},
      {'id':'DEV2-2023-SEARCH','class':'inform','status':'open','effect':plan['search_disclosure']},
      {'id':'DEV2-2024-CLOSED','class':'block','status':'open','effect':'Explicit current user instruction keeps 2024 closed even if separate selector repair finishes; no opening or confirmation freeze here.'}],
    'reference_pairs':reference_pairs,'mechanism_expectations_descriptive':readout['diagnostic_expectations'],
    'confirmation_2024_open':False,'final_confirmation_roster_frozen':False,'professional_independent_validation':False}
dump(run/'assessment.json',assessment)
names={'W2-B00':'Referencia','W2-B01':'GLM inicial','W2-B02':'LightGBM inicial, 300 árboles','W2-B03':'GLM, alpha=10 en edificios','W2-B04':'Prefijo LightGBM, 25 árboles','W2-B05':'Boosting simple, 80 árboles'}
rows='\n'.join(f"| {mid}: {label} | {points[mid]['D2']:.5f} | {points[mid]['predicted_total']/1e6:.3f} | {points[mid]['actual_over_expected']:.3f} |" for mid,label in names.items())
ci_rows='\n'.join(f"| {x['candidate']} | {x['delta_D2']:.5f} | [{x['exploratory_lower95']:.5f}, {x['exploratory_upper95']:.5f}] | {x['delta_after_removal']:.5f} |" for x in reference_pairs)
gap_rows='\n'.join(f"| {mid} | {train[mid]['training_repeated_rows']['D2']:.5f} | {points[mid]['D2']:.5f} | {train[mid]['gap_train_minus_OOF']:.5f} |" for mid in ['W2-B01','W2-B03','W2-B02','W2-B04','W2-B05'])
building_rows='\n'.join(f"| {mid} | {building[mid]['training_D2']:.5f} | {building[mid]['OOF_D2']:.5f} | {building[mid]['gap']:.5f} | {building[mid]['A_over_E']:.3f} |" for mid in building)
line_rows='\n'.join('| '+label+' | '+' | '.join(f"{segment(mid,'line',line)['D2']:.5f}" for mid in ['W2-B00','W2-B03','W2-B04','W2-B05'])+' |' for line,label in [('motor','Autos'),('buildings','Edificios'),('contents','Contenidos')])
business_rows='\n'.join('| '+label+' | '+' | '.join(f"{segment(mid,'business',business)['D2']:.5f}" for mid in ['W2-B00','W2-B03','W2-B04','W2-B05'])+' |' for business,label in [('new_business','Nuevo negocio'),('renewal','Renovación')])
scenario=read(run/'diagnostics/observation_sensitivity.json');scenario_index={(x['model_id'],x['scenario']):x['D2'] for x in scenario}
scenario_rows='\n'.join('| '+case+' | '+' | '.join(f"{scenario_index[mid,case]-scenario_index['W2-B00',case]:.5f}" for mid in ['W2-B03','W2-B04','W2-B05'])+' |' for case in ['reserve075','reserve125','late_cost05','late_cost10'])
rp='../../'+run.relative_to(REPO).as_posix();review_link='../../'+Path(plan['diagnostic_review']).relative_to(Path('Hackaton/Repositorio_IAA2026')).as_posix()
doc=f'''# Revisión del GLM y segunda tanda de desarrollo de 2023

Codex, 23 de octubre de 2026. Las nuevas recetas mejoran sus puntos de desarrollo y reducen las brechas de ajuste revisadas. W2-B03 tiene el mejor punto global de las seis recetas consultadas. Se conserva W2-B00: las tres diferencias nuevas frente a ella tienen intervalos exploratorios que cruzan cero y cambian de signo al retirar los 31 componentes más favorables. 2024 continúa cerrado.

El [plan v2](../../registro/semana2_desarrollo2023_plan_v2.json) y COD-S2-20261023-010 preceden a la prueba. El resultado está en COD-S2-20261023-011 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice activo](../../registro/semana2_desarrollo2023_actual.json) distingue la primera tanda, sus artefactos y esta ejecución. Los resultados de 2023 ya informaron esta nueva tanda: hay búsqueda adaptativa y la incertidumbre exploratoria no la corrige.

## Qué explicaba la primera brecha

La [revisión de v1]({review_link}) cargó únicamente datos y modelos guardados de 2023, con fit bloqueado. En edificios había 497 filas positivas y 12.083 sin coste. El GLM ganaba 0,07897 de contribución al D² completo de edificios sobre las filas sin coste; perdía más en las positivas, hasta dejar una diferencia neta de −0,06231 frente a la referencia. Es una descomposición por resultado observado, no un filtro que deba entrar como predictor.

Retirar solo cinco de los grupos más adversos cambiaba el signo de esa diferencia. Se conservaron todos los grupos y el objetivo íntegro. Los 26 capitales desconocidos de 2023 no tuvieron siniestros y apenas contribuían al deterioro. La revisión no justifica corregirlos por mil. Algunos coeficientes de categorías cambiaban de signo entre folds; se planteó mayor penalización sin seleccionar campos por su resultado.

En el último árbol de LightGBM se encontraron hojas con pocos siniestros positivos; en contenidos hubo hojas sin ninguno. Es un diagnóstico local de soporte, no una explicación causal de todo el bosque. min_child_samples=200 describe un parámetro aproximado por Hessianos y no garantiza doscientas filas reales por hoja, según [LightGBM 4.6](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#min_data_in_leaf). La revisión encontró hojas menores; se precisa la redacción de v1 y se conserva su receta.

## Recetas fijadas antes de probar

| Receta | Cambio registrado |
| --- | --- |
| W2-B03 | Alpha pasa de 1 a 10 solo en el GLM de edificios; autos y contenidos reutilizan exactamente B01 |
| W2-B04 | Primeros 25 árboles de cada B02 guardado; misma trayectoria y categorías, sin nuevo ajuste o elección de etapa por una curva de scores |
| W2-B05 | 80 árboles de profundidad uno, dos hojas, min_child_samples=1000 y L2=100; resto igual a B02 |

El prefijo usa la exportación por número de iteraciones de [Booster](https://lightgbm.readthedocs.io/en/v4.6.0/pythonapi/lightgbm.Booster.html). Se verificó igualdad con los primeros 25 árboles del padre y se reconstruyeron sus predicciones sumando valores de hojas. La receta simple cambia conjuntamente capacidad y regularización; no aísla la contribución causal de cada parámetro.

Se mantienen 50.094 periodos de 2023, 30.869 componentes y cinco folds. No cambian F0, T0, C0, pesos, exposición, semilla o particiones. Se hicieron veinte ajustes nuevos, diez reutilizaciones de bundles GLM y quince exportaciones de prefijos. Los tres comparadores de v1 se conservaron exactamente, incluida la referencia. La tanda y primera agregación tardaron {report['elapsed_seconds']:.1f} segundos en CPU con dos hilos; la revisión y documentación son trabajo adicional. No se calibraron niveles o mezclas.

## Resultado global fuera de muestra

El observado es 15,297 millones CU. Son predicciones del incurrido T0 con el vínculo C0, no scores de Kaggle ni validación contra el último real. A/E es observado dividido por predicho. El D² global usa un solo nulo sobre todas las filas.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{rows}

La primera receta de GLM y el bosque de 300 árboles permanecen visibles y sin cambios. No se retira una alternativa por el mejor punto de otra.

| Nueva receta frente a B00 | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
{ci_rows}

Los 2.000 remuestreos pareados usan los mismos componentes y sorteos que v1, con nulo recalculado en cada réplica. Se publican las quince parejas de las seis recetas en el [recibo]({rp}/diagnostics/pairs.json). Los intervalos son condicionales y sin ajuste de multiplicidad o búsqueda previa; no son confirmación simultánea de 2024. La inversión del diagnóstico de influencia tampoco demuestra equivalencia o inferioridad general. Las condiciones de incertidumbre e influencia permanecen abiertas.

## Qué cambió en edificios

| GLM de edificios | D² ajuste | D² OOF | Brecha | A/E OOF |
| --- | ---: | ---: | ---: | ---: |
{building_rows}

El punto OOF de edificios mejora {building['W2-B03']['OOF_D2']-building['W2-B01']['OOF_D2']:.5f}, pero queda por debajo de la referencia del ramo ({segment('W2-B00','line','buildings')['D2']:.5f}). La media de la desviación de coeficientes entre folds pasa de {coefs['W2-B01']['mean_std_across_folds']:.4f} a {coefs['W2-B03']['mean_std_across_folds']:.4f}. Es variación descriptiva de cinco ajustes solapados, no incertidumbre inferencial de parámetros.

La penalización reduce la brecha y la pérdida, pero el nivel agregado observado de edificios empeora: A/E sube de {building['W2-B01']['A_over_E']:.3f} a {building['W2-B03']['A_over_E']:.3f}. Una mejora de devianza no resuelve por sí sola esa diferencia de totales ni la incertidumbre del último. No se forzó A/E a uno. El [desglose de mecanismos]({rp}/diagnostics/mechanism_readout.json) conserva las contribuciones de filas positivas y sin coste.

## Qué cambió en LightGBM

| Receta | D² ajuste | D² OOF | Brecha |
| --- | ---: | ---: | ---: |
{gap_rows}

Las columnas de ajuste repiten cada fila en cuatro folds y solo son diagnósticas. El prefijo reduce la brecha de B02 de 0,80982 a {train['W2-B04']['gap_train_minus_OOF']:.5f}; la receta simple la reduce a {train['W2-B05']['gap_train_minus_OOF']:.5f}. Los nuevos puntos son positivos, pero conservan infrapredicción agregada observada. Los resultados son consistentes con exceso de capacidad en la receta inicial; no prueban que un único parámetro explique toda la diferencia.

| Ramo | B00 | B03 | B04 | B05 |
| --- | ---: | ---: | ---: | ---: |
{line_rows}

B03 mejora su antecedente en edificios y mantiene idénticos autos/contenidos de B01. B05 mejora los puntos de edificios/contenidos frente a B00 y empeora autos. Los D² por ramo tienen nulos propios; no se promedian para obtener el global.

| Segmento | B00 | B03 | B04 | B05 |
| --- | ---: | ---: | ---: | ---: |
{business_rows}

Nuevo negocio es la marca contractual del periodo; no representa la prueba temporal de nuevos clientes de 2024. Ninguna tabla anterior ejecuta sus salvaguardas futuras de confirmación.

## Sensibilidad, verificación y decisión

Las siguientes diferencias frente a B00 mantienen las tasas OOF base fijas y cambian únicamente la observación y respuesta del escenario guardado. No reentrenan las recetas y no sustituyen los escenarios completos de confirmación.

| Escenario | B03−B00 | B04−B00 | B05−B00 |
| --- | ---: | ---: | ---: |
{scenario_rows}

Pasaron 21 controles de rutas, guardas y prefijo y {verification['passed']} controles del comprobador separado. Los recuentos se solapan. Se contrastaron parámetros, transformaciones dentro de fold, gradiente GLM, árboles y categorías del prefijo, objetivos y exposición comunes, replay con fit bloqueado, métricas e intervalos por otra fórmula, influencia y sensibilidades. [Verificación]({rp}/{verification_path.relative_to(run).as_posix()}). Es revisión propia de Codex y no revisión profesional independiente.

Se mantiene W2-B00 como referencia y se conservan B01–B05. Los tres mecanismos cumplen la dirección descriptiva preinscrita, pero sus diferencias frente a la referencia siguen siendo inciertas y sensibles a pocos componentes. Los bloqueos DEV2023-B02-GENERALIZATION y S2-VAL-MOD-007 de la receta original permanecen con sus responsables; probar IDs nuevos no los cierra. Las [advertencias de esta tanda]({rp}/assessment.json) conservan incertidumbre, influencia, nivel y búsqueda.

2024 sigue cerrado por instrucción expresa del participante, con independencia del avance del encargo separado que repara el selector. No se abre el ledger, consulta un score de modelos de 2024 o congela la lista final aquí. Tampoco hay predicciones de test, envíos o entrenamiento remoto. Los [supuestos del último](VARIABLES_Y_ULTIMO.md) conservan su alcance. El [primer resultado](DESARROLLO_2023.md) permanece como corte histórico.

## Reproducir la comprobación

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_v2_semana2.py' --run '{rel(run)}'
```

El comando carga y comprueba, con fit bloqueado. Los modelos, OOF, filas, recetas y dependencias están identificados por SHA en el [manifiesto]({rp}/manifest.json); los anexos de revisión y cierre posteriores conservan sus propios cortes.
'''
docpath=REPO/'docs/archivo/semana2/DESARROLLO_2023_TANDA2.md'
with docpath.open('x',encoding='utf-8') as f:f.write(doc)
prior_index_path=REPO/'registro/semana2_desarrollo2023_actual.json';prior=read(prior_index_path)
assert prior['id']=='S2-DEV2023-v1-20261023'
snapshot=REPO/'registro/semana2_desarrollo2023_v1_snapshot.json'
with snapshot.open('xb') as f:f.write(prior_index_path.read_bytes())
index={'id':report['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root',
 'status':'two_2023_development_batches_verified_reference_retained_no_promotion','run':rel(run),
 'report':rel(run/'report.json'),'report_sha256':sha(run/'report.json'),'documentation':rel(docpath),
 'plan':rel(REPO/'registro/semana2_desarrollo2023_plan_v2.json'),'plan_sha256':report['plan_sha256'],
 'producer':rel(REPO/'src/semana2/entrenar_desarrollo2023_v2.py'),'producer_sha256':report['code_sha256'],
 'oof':rel(run/'oof_2023.parquet'),'oof_sha256':sha(run/'oof_2023.parquet'),'manifest':rel(run/'manifest.json'),'manifest_sha256':sha(run/'manifest.json'),
 'verification':{'path':rel(verification_path),'sha256':sha(verification_path),'passed':verification['passed'],'failed':0},
 'assessment':rel(run/'assessment.json'),'assessment_sha256':sha(run/'assessment.json'),
 'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
 'new_estimator_fits_this_batch':20,'cumulative_estimator_fits':50,'cumulative_closed_form_constants':15,
 'GLM_bundle_reuses_this_batch':10,'prefix_exports_this_batch':15,'models_consulted':list(points),
 'summary':report['summary'],'reference_pairs':reference_pairs,'reference':'W2-B00',
 'alternatives_preserved':['W2-B01','W2-B02','W2-B03','W2-B04','W2-B05'],'promotion':False,
 'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
 'history':[{'id':prior['id'],'run':prior['run'],'documentation':prior['documentation'],'index_snapshot':rel(snapshot),'index_sha256':sha(snapshot)},
            {'id':report['id'],'run':rel(run),'documentation':rel(docpath)}],
 'forum_prior':'COD-S2-20261023-010','forum_result':'COD-S2-20261023-011','submissions':0,'professional_independent_validation':False}
dump(run/'active_index_proposed.json',index)
body=f'''Codex. Cierro la tanda preinscrita en COD-S2-20261023-010 por la petición del participante. El [informe](../../Repositorio_IAA2026/docs/archivo/semana2/DESARROLLO_2023_TANDA2.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conservan la revisión, recetas y evidencia; v1 mantiene su snapshot y todas sus corridas.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{rows}

Se completaron veinte ajustes nuevos solo en 2023, diez reutilizaciones GLM y quince exportaciones de prefijo, sin fallos. Son cinco folds y 50.094 filas OOF por receta. Los tres comparadores de v1, incluido B00, quedaron exactamente iguales. No hubo calibración posterior, búsqueda de otra ronda o nueva mezcla.

En edificios, alpha=10 mejora D² de {building['W2-B01']['OOF_D2']:.5f} a {building['W2-B03']['OOF_D2']:.5f}, aún por debajo de la referencia del ramo ({segment('W2-B00','line','buildings')['D2']:.5f}). Reduce la brecha de ajuste y variación de coeficientes, pero empeora A/E de {building['W2-B01']['A_over_E']:.3f} a {building['W2-B03']['A_over_E']:.3f}. No se presenta la menor devianza como cierre de nivel o reservas. Autos/contenidos de B03 son idénticos a B01.

La brecha global de B02 (ajuste menos OOF), 0,80982, baja a {train['W2-B04']['gap_train_minus_OOF']:.5f} con los primeros 25 árboles y a {train['W2-B05']['gap_train_minus_OOF']:.5f} con árboles simples. Cumplen la dirección descriptiva previa, sin demostrar una causa única del error ni resolver los adversos de la receta original. DEV2023-B02-GENERALIZATION y S2-VAL-MOD-007 no se cierran aquí.

| Nueva receta frente a B00 | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
{ci_rows}

Los tres intervalos cruzan cero y los tres diagnósticos de influencia invierten la ventaja. Se conserva la referencia y B01–B05, sin promoción, retiro o equivalencia declarada. Los intervalos de 2.000 sorteos comunes son exploratorios, sin corregir búsqueda adaptativa o las quince parejas. Las sensibilidades publicadas son a tasas fijas y no sustituyen escenarios reentrenados de confirmación.

Pasaron 21 controles focales y {verification['passed']} del comprobador separado; se solapan. Replay exacto con fit bloqueado, parámetros/encoders por fold, 25 árboles exactos y oráculo de suma de hojas, objetivos/exposiciones, métricas, intervalos e influencia contrastados. Es revisión propia de Codex. T0, folds, F0, vínculos y artefactos v1 no cambiaron.

2024 sigue cerrado por instrucción expresa del participante, aunque avance la reparación separada del selector. No hay ajuste, predicción o score de precios de 2024 o test, apertura del ledger o lista final congelada. Sin envíos, remoto o delegación. La referencia conserva su papel previo y las incertidumbres del último permanecen.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v2_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(docpath),'proposed_index':rel(run/'active_index_proposed.json'),'building_diagnostic':building,'expectations':readout['diagnostic_expectations']},ensure_ascii=True))
