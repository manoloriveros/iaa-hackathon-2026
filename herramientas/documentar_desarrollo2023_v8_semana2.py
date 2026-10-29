"""B19: resultados adversos, recetas preservadas y procedencia de contrastes."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib,importlib.metadata
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    run=Path(sys.argv[1]).resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');f=read(run/'fixture_checks.json');old=read(ROOT/p['parent_index_snapshot']);NOW=datetime.now(timezone.utc).isoformat()
    assert v['failed']==f['failed']==0 and r['new_price_base_fits']==15
    seg=read(run/'diagnostics/segments.json');tv=read(run/'diagnostics/train_validation.json');pairs=r['pairs'];checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    summaries={x['model_id']:x for x in r['summary']};new=summaries['W2-B19'];parent=summaries['W2-B14'];parts=[]
    for line in ['motor','buildings','contents']:
        before=next(x for x in seg if x['model_id']=='W2-B14' and x['dimension']=='line' and x['label']==line)
        after=next(x for x in seg if x['model_id']=='W2-B19' and x['dimension']=='line' and x['label']==line)
        parts.append({'line':line,'B14_D2':before['D2'],'B19_D2':after['D2'],'D2_change_within_line':after['D2']-before['D2'],
            'contribution_to_global_D2_change':(before['deviance_sum']-after['deviance_sum'])/parent['null_deviance_sum']})
    check('Line loss contributions add to global, not mean oflineD2',np.isclose(sum(x['contribution_to_global_D2_change'] for x in parts),new['D2']-parent['D2'],rtol=0,atol=1e-12))
    check('Nestedfit deviance improves all15',len(v['nested_fit_diagnostics'])==15 and all(x['B19_minus_B14_fit_deviance']<0 for x in v['nested_fit_diagnostics']))
    check('No level-based promotion',not r['promotion'] and r['all_alternatives_preserved'])
    coefficients=[]
    for line in ['motor','buildings','contents']:
        block=p['recipe']['features_by_line'][line]
        for fold in range(5):
            b=joblib.load(run/f'models/W2-B19_{line}_fold{fold}/bundle.joblib');names=b['transformer'].get_feature_names_out();values=dict(zip(names,b['estimator'].coef_))
            if line=='motor':
                for name,value in values.items():
                    if name.startswith('categorical__x_cover_type_'):coefficients.append({'line':line,'fold':fold,'contrast':str(name).removeprefix('categorical__x_cover_type_')+' / comprehensive','rate_ratio':float(np.exp(value))})
            else:
                j=block['numeric'].index('x_accidental_damage_cover');value=values['numeric__x_accidental_damage_cover'];scale=b['transformer'].named_transformers_['numeric']['scale'].scale_[j]
                coefficients.append({'line':line,'fold':fold,'contrast':'AD_yes / AD_no','rate_ratio':float(np.exp(value/scale))})
    check('20coverage coefficient readouts',len(coefficients)==20 and all(np.isfinite(x['rate_ratio']) and x['rate_ratio']>0 for x in coefficients))
    for entry in f['expected_failure_runs']:
        folder=ROOT/entry;events=[json.loads(x) for x in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        check('Expected adversary has no fit attempt '+entry,not any(x['event']=='fit_started' for x in events))
        marker={'author':'Codex','utc':NOW,'kind':'expected_negative_fixture_failure_not_pending_price_training','successful_unit':rel(run),
            'fixture_receipt':rel(run/'fixture_checks.json'),'price_fit_attempts':0,'report_absence_expected':True}
        with (folder/'expected_adversary_failure.json').open('x',encoding='utf-8') as target:json.dump(marker,target,ensure_ascii=False,indent=2)
    versions={name:importlib.metadata.version(name) for name in ['numpy','pandas','pyarrow','scikit-learn','scipy','joblib']}
    environment={'utc':NOW,'python':sys.version,'executable':sys.executable,'versions':versions,'training_threads':2,'seed':p['bootstrap']['seed'],
        'scope':'Same local interpreter at postfit verification; no Linux/remote or independent runtime reproduction claim.'}
    summary={'utc':NOW,'global_new':new,'global_parent':parent,'line_contributions':parts,'coverage_rate_ratios':coefficients,
        'nominal2023_change_CU':new['conditional_nominal_2023']-parent['conditional_nominal_2023'],
        'nominal2023_relative_change':new['conditional_nominal_2023']/parent['conditional_nominal_2023']-1,
        'nested_all15_fit_improves_but_OOF_global_worsens':True,'no_promotion_or_retirement':True}
    reconciliation={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
    for name,obj in [('readout.json',summary),('readout_reconciliation.json',reconciliation),('environment.json',environment)]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert reconciliation['failed']==0,[x for x in checks if not x['pass']]
    names={'motor':'Autos','buildings':'Edificios','contents':'Contenidos'}
    line_table='\n'.join(f'| {names[x["line"]]} | {x["B14_D2"]:.6f} | {x["B19_D2"]:.6f} | {x["D2_change_within_line"]:+.6f} |' for x in parts)
    business=[]
    for line in ['motor','buildings','contents']:
        for business_label in ['new_business','renewal']:
            label=line+'_'+business_label;before=next(x for x in seg if x['model_id']=='W2-B14' and x['dimension']=='line_business' and x['label']==label);after=next(x for x in seg if x['model_id']=='W2-B19' and x['dimension']=='line_business' and x['label']==label)
            business.append(f'| {names[line]} | '+('Nuevo' if business_label=='new_business' else 'Renovación')+f' | {before["D2"]:.6f} | {after["D2"]:.6f} |')
    ranges=[]
    for line in ['motor','buildings','contents']:
        a=[x['D2'] for x in tv if x['line']==line and x['role']=='fit'];z=[x['D2'] for x in tv if x['line']==line and x['role']=='validation']
        ranges.append(f'| {names[line]} | {min(a):.6f} a {max(a):.6f} | {min(z):.6f} a {max(z):.6f} |')
    contrast_table='\n'.join(f'| {x["candidate"]} / {x["reference"]} | {x["delta_D2"]:+.6f} | [{x["exploratory_lower95"]:+.6f}; {x["exploratory_upper95"]:+.6f}] | {x["delta_after_removal"]:+.6f} |' for x in pairs)
    doc=f'''# GLM sencillo con coberturas como efectos principales

Codex, corte UTC {NOW}. B19 añade un campo de cobertura a B14 y mantiene exactamente T0, C0 y las particiones de 2023. La receta se publicó antes del ajuste en el comentario 034. Terminaron quince GLM, sin retocar parámetros o volver a ajustar las referencias.

## Resultado observado

El D² global baja de **0,086710** en B14 a **0,082470** en B19. B00 conserva **0,068582**. El ajuste de entrenamiento mejora en los quince nodos respecto a B14, pero esa ganancia no se sostiene en el OOF global. No se promueve B19 ni se retira: B00 y todas las alternativas permanecen.

| Ramo | D² B14 | D² B19 | Cambio dentro del ramo |
| --- | ---: | ---: | ---: |
{line_table}

Edificios concentra el deterioro; contenidos también pierde. Autos mejora ligeramente agregado, con deterioro en nuevo negocio. Las contribuciones al cambio global se calculan con la misma desviancia nula global; no se promedian D² de ramos.

| Ramo | Negocio | D² B14 | D² B19 |
| --- | --- | ---: | ---: |
{chr(10).join(business)}

Las tablas por cobertura conservan los resultados adversos: en autos third_party_only el D² pasa de −0,015892 a −0,042793. En edificios con cobertura accidental activa, el A/E se acerca a uno (1,076 a 1,010), mientras el D² empeora (−0,008318 a −0,029774). Una mejor conciliación del total no establece mejor predicción por fila. Son perfiles descriptivos, sin intervalos propios de cada celda ni pruebas nuevas de superioridad por segmento.

## La receta probada

Cada ramo usa las seis variables originales de B14 más cover_type en autos o accidental_damage_cover en hogar. No hay interacciones ni restricciones de coste cero. En hogar se conservan los treinta siniestros positivos con la bandera desactivada identificados en la [auditoría previa](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md); cobertura se interpreta como predictor, no como exclusión contractual validada.

Tweedie de potencia 1,5, enlace log e intercepto, alpha cero, solver lbfgs, 2.000 iteraciones máximas y tolerancia 1e-6, sin warm_start. Medianas y escala numéricas y OHE dropfirst/min_frequency50/max_categories40/ignore, aprendidos únicamente en ajuste. Respuesta T0/e y peso raíz(e), con e=e_cost_mix_1.0 original de cada fold. La predicción observada multiplica la tasa por e una sola vez. Los valores de capital de B14 se conservan con sus condiciones abiertas; no entran clima o credibilidad nuevos.

C0 de entrenamiento procede del mismo archivo de B14 para ese fold. El C0 de una fila OOF se compara con el de su propio fold retenido, pues las curvas de otros folds son distintas por diseño. Se verifican 50.094 periodos, 30.869 componentes y cinco folds guardados, con clientes/direcciones/componentes disjuntos. No se reseleccionan variables, semillas o regularización tras ver resultados.

## Ajuste, incertidumbre y nivel

| Ramo | Rango D² de ajuste por fold | Rango D² de validación por fold |
| --- | ---: | ---: |
{chr(10).join(ranges)}

Los rangos recorren muestras solapadas; no son intervalos de confianza. Los coeficientes de cobertura y sus razones por fold están archivados para examinar estabilidad, sin atribución causal o contractual. Los quince ajustes convergen con gradiente normalizado por debajo de 1e-4. Ese control técnico no garantiza generalización.

| Contraste nuevo | Cambio D² | Intervalo exploratorio 95% | Tras retirar sus 31 grupos favorables |
| --- | ---: | ---: | ---: |
{contrast_table}

Se usan 2.000 sorteos agrupados comunes por pareja y la misma nula del objetivo. Ambos intervalos incluyen cero. Son intervalos sin ajuste por búsqueda adaptativa, condicionados a modelos y primera etapa ya ajustados; no incorporan su incertidumbre de reajuste. El diagnóstico de influencia no borra siniestros o grupos del modelo. La ventaja puntual sobre B00 invierte signo con esa perturbación de evaluación. No se repite el bootstrap de las parejas antiguas ni se interpreta un punto como permiso de selección.

El total observado predicho pasa de 15.429.695,38 CU a 15.436.941,83 CU. El nominal condicionado de los mismos periodos de 2023 pasa de 15.606.084,09 a 15.613.508,68 CU (+0,0476%). Es exposición nominal de esos contratos por su tasa bajo el vínculo declarado, no prima final o verdad de último de 2025/test. Mantener un nivel cercano tampoco demuestra equivalencia estadística.

## Controles y decisiones

Pasaron {v['passed']} comprobaciones separadas con fit bloqueado, {f['passed']} adversos focales y {reconciliation['passed']} conciliaciones de lectura, con solapamiento. El comprobador reconstruye medianas, escalas y categorías de ajuste, la predicción exp(Xβ), el gradiente, la igualdad entre objetivo ponderado y desviancia observada, métricas con sklearn y dos remuestreos nuevos mediante multiplicidades. El replay de B19 y B14 es exacto sin ajuste. Los cuatro comandos adversos reales rechazan año sintético 2024, cobertura ausente o cambios de T0/C0 antes de iniciar fit; sus fallos esperados llevan marcador para que no se confundan con entrenamientos pendientes.

Se conservan exactamente las 19 alternativas anteriores en el OOF de veinte modelos, más los archivos e índices históricos. El contador propio actual suma 180 ajustes de precio y 285 constantes. El linaje exclusivo del catálogo principal tiene 105 ajustes y 60 constantes; las diferencias corresponden a sensibilidades previas, no se ocultan o recuentan como trabajo nuevo. Auxiliares, curvas de reporte y estimaciones de mezcla mantienen sus contadores separados. Hay dos contrastes nuevos y 171 históricos heredados; no se calcularon las otras 17 parejas posibles con B19.

La decisión es conservar la receta adversa y estudiar estabilidad de coeficientes y contribuciones de grupos antes de otra receta. Este resultado no demuestra que hagan falta árboles o interacciones ni justifica ajustar regularización después de verlo. No se promueve, retira o congela una lista final. Revisión propia de Codex, no profesional independiente ni aprobación humana.

## Ámbito temporal y trazabilidad

2024 permanece cerrado para este trabajo, sin precios, predicciones, puntuación, acta o lectura del ledger; también test, remoto y envíos. Se conserva la exposición previa de un asunto ajeno con métricas de confirmación, sin repetirlas o usarlas; no se afirma ceguera completa. El lector del foro solo emite autor, ID y UTC. Sin nuevas conversaciones, delegación, publicación externa o cambios a otras automatizaciones.

[Plan congelado](../../registro/semana2_desarrollo2023_plan_v8.json), [índice actual](../../registro/semana2_desarrollo2023_actual.json), [snapshot anterior](../../registro/semana2_desarrollo2023_v7_snapshot.json), [productor](../../src/semana2/entrenar_desarrollo2023_v8.py), [comprobador](../../herramientas/verificar_desarrollo2023_v8_semana2.py), [adversos](../../herramientas/probar_desarrollo2023_v8_semana2.py). Fuentes, modelos, entorno, OOF y recibos restringidos: `{rel(run)}`. El [balance nocturno](BALANCE_NOCTURNO_PARCIAL_20261024.md) conserva su carácter parcial hasta las 07:00 de Bogotá.
'''
    docpath=REPO/'docs/archivo/semana2/GLM_COBERTURAS_2023.md';assert not docpath.exists();docpath.write_text(doc,encoding='utf-8')
    warnings=[{'id':'DEV8-HOME-OOF','status':'open','effect':'All15 nestedfit objectives improve but globalB19D2 falls; building D2.021094->.008352. A-E close1 does not establish row-level performance.'},
        {'id':'DEV8-MOTOR-NEW','status':'open','effect':'Motor aggregate slightly improves but newbusinessD2-.010045->-.031822 and thirdpartyonly worsens. Descriptive segment evidence, no segment superiority interval.'},
        {'id':'DEV8-INFLUENCE','status':'open','effect':'B19/B00 positive point reverses after own31 favorable groups; B19/B14 negative point and both exploratoryCIs include0. No promotion/equivalence/retirement.'},
        {'id':'DEV8-SEARCH','status':'open','effect':'20 adaptive catalogrecipes;171 inherited+2new pair contrasts,17 possibleB19pairs uncomputed. Fixedfit exploratory intervals omit first-stage/model refit uncertainty.'},
        {'id':'DEV8-COVERAGE-SEMANTICS','status':'open','effect':'Coverage effects are predictors, not contract masks or causal estimates;30positive home claims retained. BroadperilC0 and ultimate, capital, climate and prior conditions persist.'},
        {'id':'DEV8-2024-EXPOSURE','status':'open','effect':'User keeps2024/test closed; prior external header metric exposure disclosed, no complete-blindness claim, no external outcome used or new external confirmation artifact read.'}]
    oldassessment=read(ROOT/old['assessment']);assert sha(ROOT/old['assessment'])==old['assessment_sha256']
    assessment={'author':'Codex','utc':NOW,'status':'coverage_GLM_verified_adverse_against_parent_no_promotion_conditions_open','warnings':oldassessment['warnings']+warnings,'professional_independent_validation':False}
    journal={'author':'Codex','utc':NOW,'decisions':[{'hypothesis':p['hypothesis'],'criterion_before_fit':p['decision_rule'],'configuration':p['recipe'],'sources':p['frozen_sources'],
        'result':summary,'verification':rel(run/'verification.json'),'consequence':'KeepB00/B01-B19. No adopted coverage mask, C0/target change, regularization change, promotion or finalroster. Diagnose coefficient/group stability before another registered recipe.','professional_independent_validation':False}]}
    for name,obj in [('assessment.json',assessment),('decision_journal.json',journal)]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    history=list(old['history']);history[-1].update(index_snapshot=p['parent_index_snapshot'],index_sha256=p['parent_index_sha256']);history.append({'id':p['id'],'run':rel(run),'documentation':rel(docpath)})
    assert isinstance(old['pairs'],list) and len(old['pairs'])==171
    idx={'id':p['id'],'author':'Codex','as_of_utc':NOW,'path_base':'workspace_root','status':assessment['status'],'run':rel(run),'documentation':rel(docpath),
        'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,'new_price_base_fits':15,'new_closed_form_constants':0,'new_auxiliary_fits':0,'new_curve_fits':0,
        'cumulative_price_base_fits':180,'cumulative_closed_form_constants':285,'counter_scope':'Current own lineage including observation sensitivities; dated parent indices retain their original scope.',
        'catalog_lineage_price_base_fits':105,'catalog_lineage_closed_form_constants':60,'own_fit_counter_index':rel(REPO/'registro/semana2_contadores_propios_actual.json'),
        'models_consulted':old['models_consulted']+['W2-B19'],'summary':old['summary']+[new],'primary_contrasts':pairs,'pairs':old['pairs']+pairs,
        'pair_provenance':{'historical171':p['parent_index_snapshot'],'new2':rel(run/'diagnostics/new_pairs.json'),'B19_other_possible_pairs_uncomputed':17},
        'reference':'W2-B00','alternatives_preserved':old['alternatives_preserved']+['W2-B19'],'promotion':False,'confirmation_2024_open':False,
        'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,'history':history,'forum_prior':p['forum_prior'],'forum_result':'COD-S2-20261024-035',
        'submissions':0,'professional_independent_validation':False,'selector_status_not_assessed_here':True,'night_continuation_index':rel(REPO/'registro/semana2_continuidad_nocturna.json'),
        'external2024_subject_exposure_previously_disclosed':True,'complete_blindness_claim_allowed':False}
    for name,path in [('report',run/'report.json'),('plan',ROOT/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v8.json'),('producer',ROOT/p['code']),('oof',run/'oof_2023.parquet'),('manifest',run/'manifest.json'),('assessment',run/'assessment.json'),('decision_journal',run/'decision_journal.json')]:idx[name]=rel(path);idx[name+'_sha256']=sha(path)
    for name in ['verification','fixtures','readout_reconciliation']:
        path=run/('fixture_checks.json' if name=='fixtures' else name+'.json');obj=read(path);idx[name]={'path':rel(path),'sha256':sha(path),'passed':obj['passed'],'failed':obj['failed']}
    (run/'index_proposed.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=f'''La receta B19 registrada en 034 terminó con quince GLM estándar, sin reintento o modificación de parámetros. Añade solo cobertura como efecto principal a B14, con los mismos T0, C0, capital, 50.094 periodos, 30.869 componentes y cinco folds de 2023. Se conservan B00 y todas las alternativas. Informe: `{rel(docpath)}`.

Resultado adverso: D² global B14 0,086710 frente a B19 0,082470; B00 conserva 0,068582. Edificios cae de 0,021094 a 0,008352 y contenidos de 0,037343 a 0,036281. Autos mejora ligeramente agregado (0,033101 a 0,033722), pero nuevo negocio empeora de −0,010045 a −0,031822; third_party_only también pierde. El objetivo de entrenamiento mejora en los quince ajustes, sin sostenerlo en OOF global. A/E más cerca de uno en ciertas coberturas no acredita mejor D² por fila.

Solo dos contrastes nuevos, 2.000 sorteos agrupados comunes: B19/B14 delta −0,004240, intervalo exploratorio [−0,009969; +0,000507], y −0,007145 tras retirar sus 31 grupos favorables de evaluación. B19/B00 delta +0,013888, intervalo [−0,011053; +0,037614], y −0,014724 bajo su influencia. No se borran o reajustan grupos; intervalos exploratorios tras búsqueda adaptativa, condicionados a modelos/primera etapa. No se promueve, retira, declara equivalencia o congela lista final.

El nominal condicionado de los mismos periodos de 2023 pasa de 15.606.084,09 a 15.613.508,68 CU (+0,0476%); no es prima o verdad de último de 2025/test. No se cambia respuesta, enlace, curva o máscara y se conservan los treinta costes positivos de hogar con bandera desactivada.

Pasaron {v['passed']} verificaciones separadas con fit bloqueado, {f['passed']} adversos y {reconciliation['passed']} conciliaciones nuevas, con solapamiento. Replay nativo exacto, exp(Xβ), preparación de ajuste, gradientes, objetivo por otro método y bootstrap por multiplicidades cotejados. Cuatro comandos reales rechazan año sintético 2024, cobertura ausente o T0/C0 cambiados antes de fit; están marcados como fallos esperados, no corridas pendientes. No hay constantes, curvas o auxiliares nuevos. Contador propio: 180 ajustes de precio y 285 constantes; linaje del catálogo105/60 por separado. Hay veinte recetas conservadas y 171 parejas históricas más dos nuevas, no comparación completa de las 190 posibles.

Siguiente revisión: estabilidad de coeficientes y contribuciones de grupos antes de otra receta, sin reentrenar por rutina o saltar a árboles/interacciones. 2024 sigue cerrado en este trabajo, sin acta, predicciones, score o ledger, también test/remoto/envíos. La exposición previa de un título externo se conserva y no se afirma ceguera completa ni se usan sus cifras. El lector solo muestra autor, ID y UTC. Revisión técnica propia, no profesional independiente ni aprobación humana; sin nuevos chats, delegación o cambios a otras automatizaciones.
'''
    (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v8_resultado.md').write_text(body,encoding='utf-8')
    print(json.dumps({'documentation':rel(docpath),'reconciliations':reconciliation['passed'],'failed':0,'line_contributions':parts,'coverage_rate_ratios':coefficients}))

if __name__=='__main__':main()
