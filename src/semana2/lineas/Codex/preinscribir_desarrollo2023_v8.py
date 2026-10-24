"""Registra B19 y sus dos contrastes antes de ajustar o puntuar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';OWN=ROOT/'Hackaton/Semana 2/Codex'
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();main=REPO/'registro/semana2_desarrollo2023_actual.json';old=rd(main)
assert old['id']=='S2-DEV2023-v7-20261024'
night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=rd(night)
assert n['current_unit'] is None and len(n['completed_units'])==8
counter=REPO/'registro/semana2_contadores_propios_actual.json';co=rd(counter)
assert co['cumulative_price_base_fits']==165 and co['cumulative_closed_form_constants']==285
snapshot=REPO/'registro/semana2_desarrollo2023_v7_snapshot.json'
with snapshot.open('xb') as f:f.write(main.read_bytes())
countercopy=OWN/'contadores_antes_v8.json'
with countercopy.open('xb') as f:f.write(counter.read_bytes())
with (OWN/'nocturno_antes_v8.json').open('xb') as f:f.write(before)
base=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b';bp=rd(base/'plan_snapshot.json');recipe=copy.deepcopy(bp['core_recipe']);recipe['id']='W2-B19'
for line,block in recipe['features_by_line'].items():
    block['categorical' if line=='motor' else 'numeric'].append('x_cover_type' if line=='motor' else 'x_accidental_damage_cover')
    block['all']=block['numeric']+block['categorical'];assert len(block['all'])==7
audit=rd(REPO/'registro/semana2_coberturas_peril2023_actual.json');code=REPO/'src/semana2/entrenar_desarrollo2023_v8.py'
avail=REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json'
paths=[snapshot,countercopy,base/'plan_snapshot.json',ROOT/old['oof'],code,REPO/'src/semana2/entrenar_desarrollo2023.py',avail,
    REPO/'registro/semana2_politica_seleccion_v1.json',REPO/'registro/semana2_coberturas_peril2023_actual.json']
for line in ['motor','buildings','contents']:
    paths.append(ROOT/audit['run']/f'inputs_2023/{line}.parquet')
    for fold in range(5):paths.extend([base/f'variant_inputs/{line}_fold{fold}.parquet',base/f'models/W2-B14_{line}_fold{fold}/bundle.joblib'])
p={'id':'S2-DEV2023-v8-20261024','author':'Codex','registered_utc':NOW,'model_id':'W2-B19',
 'authorization_literal':'Dale, registra y prueba el GLM sencillo con coberturas como efectos principales, sin cambiar T0 ni C0. Usa solo 2023, conserva B00, deja las decisiones y resultados en el foro y mantén 2024 cerrado.',
 'hypothesis':'Reduced B14 omits admissible coverage main effects. Add one field per line and test whether conditional observed2023 performance changes without imposing disputed structuralzero masks, changing objective, C0, capital, climate or credibility.',
 'input_run':rel(base),'coverage_audit_run':audit['run'],'parent_oof':old['oof'],'parent_oof_sha256':sha(ROOT/old['oof']),
 'parent_index_snapshot':rel(snapshot),'parent_index_sha256':sha(snapshot),'main_index_at_prereg':rel(main),
 'counter_index':rel(counter),'counter_before_sha256':sha(counter),'counter_before_snapshot':rel(countercopy),'counters_before':co,
 'code':rel(code),'code_sha256':sha(code),'availability_contract':rel(avail),'recipe':recipe,
 'features_change':'Exactly parent6+coverage field for each line. No interactions, masks, prior, trees, variable search, smoothing or recalibration.',
 'response_and_weight':'Exact B14 ownfold2023 inputs: responseT0/e_cost_mix_1.0, sampleweight sqrt(e_cost_mix_1.0), observedprediction e_cost_mix_1.0*annualrate. Same source and cuts for trainingC0; compare parent OOF C0 only on its own heldfold rows.',
 'partitions':'Five persisted2023 groupfolds,50094periods/30869components, disjoint group/customer/address, no reseed.',
 'preprocessing':'Median keep_empty_features and StandardScaler on numeric, OneHotEncoder dropfirst min_frequency50 max_categories40 ignore unknown on categorical; fit-only, same as B14. Cover values must be known and nonmissing.',
 'numerical_acceptance':'No convergencewarning, n_iter<2000, maxabs normalized weightedscore<=1e-4; positive finite rates, exact savednative replay. Failure preserves artifacts; no retries/hyperparameter changes without new recorded decision.',
 'readout':['Global,line,fold,business,linebusiness,coverage and businesscoverage D2/A-E/totals under sameT0/C0','Fit-vs-heldout perlinefold; coefficients/coverage contrasts conditional and not causal or contractual','Conditionalnominal2023 level from same period exposure; not2025/test ultimate truth','Publish adverse/sparse segments, uncertainty and own31 favorable-group influence without deleting/refitting groups'],
 'bootstrap':{'replicates':2000,'seed':2026102302,'pairs':[['W2-B19','W2-B14'],['W2-B19','W2-B00']],'interval':'Unadjusted exploratory95% percentile, fixedfit paired grouping; excludes model/first-stage refit uncertainty. No old pair bootstrap repeated.'},
 'decision_rule':'No promotion, retirement, finalroster, changedcriterion or2024 opening by any2023 point/CI/A-E. Preserve B00 andB01-B18 plusnewB19. Quantitative evidence exploratory after adaptive research.',
 'verification':'Independent blockedfit native replay, math general deviance/sklearnD2, manualexp predictor, training-only medians/scales/OHE and normalizedGLMscore; original T0/C0/source/coverage keys, graphscope; two new bootstrap pairs via multiplicity counts; guarded native consumer adversaries.',
 'resources':'Local2threads, exactly15newpriceGLMfits,0newconstants/curves/auxiliaries. Ownpricingcounters165->180 and285unchanged. Maincatalog lineage90->105fits/60constants; separate counters disclosed.',
 'frozen_sources':[{'path':rel(path),'sha256':sha(path)} for path in sorted(set(paths))],
 'reference':'W2-B00','forum_prior':'COD-S2-20261024-034','external2024_subject_exposure_previously_disclosed':True,
 'external_outcome_use':'No further subject/body/acta/prediction/score or ledger access and no use of external2024 metric in this recipe; complete blindness not claimed after prior header exposure.',
 'scope_2024':{'price_fit_rows':0,'predictions':0,'scores':0,'ledger_read':False,'confirmation_open':False},'test_predictions':0,'professional_independent_validation':False}
planpath=REPO/'registro/semana2_desarrollo2023_plan_v8.json'
with planpath.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
n.update(status='ninth_unit_preregistered_standard_GLM_coverage_in_progress',updated_utc=NOW,current_unit={'id':p['id'],'plan':rel(planpath),'status':'preregistered_check_pending_run_before_relaunch','forum_preregistration':p['forum_prior']})
tmp=night.with_name(night.name+'.dev8.tmp')
with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
assert night.read_bytes()==before,'Concurrencia';os.replace(tmp,night)
body='''Se registra B19 antes del ajuste, por instrucción directa del participante. Hipótesis: B14 omite efectos principales admisibles de cobertura. Se añade exactamente un campo por ramo: cover_type en autos y accidental_damage_cover en edificios/contenidos. Son siete campos originales por ramo. No hay interacciones, máscaras estructurales o cambios de capital, clima o credibilidad.

Se conservan literalmente los inputs de B14 por fold: T0, exposición nominal, e_cost_mix_1.0 y particiones de 2023. Respuesta T0/e, peso raíz(e), predicción observada e×tasa. El C0 de ajuste es el del fold correspondiente; el de OOF se compara solo con su propio retenido. Tweedie de potencia 1,5, enlace log, alpha cero, intercepto, solver lbfgs, máximo 2.000 iteraciones, tolerancia 1e-6, sin warm_start. Mediana y escala numéricas, OHE dropfirst/min_frequency50/max_categories40/ignore, todo aprendido solo en ajuste. Coberturas faltantes o desconocidas se rechazan. No se impone coste cero a nadie.

Los 50.094 periodos, 30.869 componentes y cinco folds guardados quedan intactos. Se esperan quince GLM nuevos, dos hilos locales, cero constantes/curvas/auxiliares. El contador propio pasa de 165 a 180 ajustes si terminan los quince; las 285 constantes no cambian. El catálogo tiene su linaje separado y conserva exactamente B00 y B01–B18. Plan congelado: `Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v8.json`.

Criterio técnico previo: convergencia sin aviso, menos de 2.000 iteraciones, gradiente normalizado máximo 1e-4, tasa positiva y replay exacto. Cualquier fallo se conserva sin retocar parámetros silenciosamente. Se comprobarán T0/C0, variables/categorías/imputación de ajuste, exp(Xβ), objetivo por otro método, métricas, segmentos y flujo real. Solo dos contrastes nuevos: B19 frente a B14 y B00, 2.000 sorteos agrupados comunes con semilla 2026102302 e influencia de sus 31 grupos favorables; no se repite el bootstrap de parejas antiguas. Se publican ajuste/validación, ramos, negocios, coberturas y nivel nominal condicionado de 2023, sin atribución causal o contractual.

No se promueve, retira o congela lista final por el score o intervalos exploratorios de 2023. Se preserva la exposición previa de un asunto ajeno con métricas de 2024: no se afirma ceguera completa ni se usan esas cifras. No se leen nuevos asuntos/cuerpos externos, actas, predicciones, scores o ledger de 2024/test ni se abre otra tanda. Sin remoto, envíos, publicación externa, chats nuevos o delegación. Revisión técnica propia, no profesional independiente ni aprobación humana.
'''
with (OWN/'desarrollo2023_v8_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':rel(planpath),'sha256':sha(planpath),'parent_snapshot':rel(snapshot),'features':recipe['features_by_line'],'new_price_fits':15}))
