"""Conclusiones acotadas de concentración y AD, con denominadores explícitos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,x):
    with path.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item() if hasattr(v,'item') else str(v));f.write('\n')


def main(run):
    run=run.resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');assert r['failed']==v['failed']==0
    now=datetime.now(timezone.utc).isoformat();z=read(run/'concentration_scopes.json');s=z['scope_statistics'];share=z['shares_with_explicit_denominators'];fire=z['fixed_fire'];checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    coef=pq.read_table(run/'AD_coefficient_by_fold.parquet').to_pandas();a=pq.read_table(run/'AD_period_composition_by_fold.parquet').to_pandas();c=pq.read_table(run/'AD_peril_composition_by_fold.parquet').to_pandas();m=pq.read_table(run/'fixed_fire_training_membership.parquet').to_pandas();local=pq.read_table(run/'existing_B19_local_influence_fixed_fires.parquet').to_pandas()
    check('Fixed row and fullcomponent explicitly equal in thiscase',s['fire_row']['rows']==s['fire_full_component']['rows']==1 and s['fire_row']['net_gain']==s['fire_full_component']['net_gain'])
    for kind in ['row','component']:
        check('Global fixed exclusion arithmetic '+kind,math.isclose(s['global_without_fire_'+kind]['net_gain']+s['fire_'+('row' if kind=='row' else 'full_component')]['net_gain'],s['global']['net_gain'],rel_tol=1e-12,abs_tol=1e-8))
    fitrows=a[a.role.eq('fit')].groupby(['fold_view','AD_group'],as_index=False)[['rows','T0_cents','nominal_exposure','effective_C0_exposure']].sum()
    fitfire=c[c.role.eq('fit')&c.peril.eq('fire')].groupby(['fold_view','AD_group'],as_index=False)[['claims','T0_cents','fixed_two_fire_cents']].sum()
    foldviews=[]
    for fold in range(5):
        row={'fold':fold}
        for mid in ['W2-B19','W2-B20']:
            y=coef[coef.model_id.eq(mid)&coef.fold.eq(fold)];check('One source coefficient '+mid+str(fold),len(y)==1);row[mid+'_AD_ratio']=float(y.rate_ratio_yes_no.iloc[0]);row[mid+'_AD_logbeta']=float(y.beta_raw.iloc[0])
        for ad in ['yes','no']:
            q=fitrows[fitrows.fold_view.eq(fold)&fitrows.AD_group.eq(ad)].iloc[0]
            w=fitfire[fitfire.fold_view.eq(fold)&fitfire.AD_group.eq(ad)].iloc[0]
            row[ad+'_periods']=int(q.rows);row[ad+'_T0_CU']=float(q.T0_cents/100);row[ad+'_nominal_exposure']=float(q.nominal_exposure)
            row[ad+'_fire_claims']=int(w.claims);row[ad+'_fire_T0_CU']=float(w.T0_cents/100);row[ad+'_fixed_fire_share_of_firecost']=float(w.fixed_two_fire_cents/w.T0_cents) if w.T0_cents else None
        row['both_fixed_fires_in_fit']=bool(m[m.fold_view.eq(fold)].present_in_fit.all())
        foldviews.append(row)
    negative={mid:coef.loc[coef.model_id.eq(mid)&coef.beta_raw.lt(0),'fold'].astype(int).tolist() for mid in ['W2-B19','W2-B20']}
    approx={label:{'delta_min':float(g.local_delete_delta_coverage_beta.min()),'delta_max':float(g.local_delete_delta_coverage_beta.max()),'max_leverage':float(g.group_leverage_trace.max())} for label,g in local.groupby('fixed_group_label')}
    inputinfo=read(run/'plan_snapshot.json');check('Zero model operations allreceipts',all(obj[k]==0 for obj in [r,v] for k in ['successful_fit_calls','model_loads','new_price_predictions']))
    check('No claimrow null score invented',s['fire_row']['derived_delta_D2'] is None)
    readout={'author':'Codex','utc':now,'explicit_shares':share,'scope_statistics':s,'fixed_fire_no_private_ids':{k:v for k,v in fire.items() if k not in ['private_key','private_group','secondary_private_group']},
             'AD_fold_training_views':foldviews,'negative_AD_folds':negative,'old_B19_local_approximation_only':approx,
             'same_AD_target_all_perils':True,'data_composition_is_not_causal_identification':True,'no_group_removed':True,
             'global_point_advantage_not_only_thisfire':s['global_without_fire_component']['net_gain']>0,'no_promotion':True}
    dump(run/'readout.json',readout);dump(run/'readout_reconciliation.json',{'utc':now,'passed':len(checks),'failed':0,'checks':checks})
    warnings=[{'id':'B20-FIRE-NET-DENOMINATOR','status':'open','effect':'93.9% refers to selectednet gain,35.8%globalnet,7.2%globalgross positivecomponent gains. Singlefire removal leaves a positive point but does not cure prior31group concentration or demonstrate superiority.'},
              {'id':'B20-AD-FOLD-COMPOSITION','status':'open','effect':'Both fixedfires areADyes and excluded fromfit3, whereADlogbeta isnegative forB19/B20. Composition is descriptive; wholefold omissions/confounding and allperil target prevent singlefire causal attribution.'},
              {'id':'B20-AD-OLD-LOCAL-ONLY','status':'open','effect':'Existing B19local deletion estimates are approximate/highleverage, notB20 influence or exact refit. No alteredbeta, mask, target or price adopted.'}]
    assessment={'author':'Codex','utc':now,'status':'fixed_fire_concentration_and_AD_composition_verified_conditions_open','warnings':warnings,'new_fits':0,'new_price_predictions':0,'new_bootstrap':0,'professional_independent_validation':False};dump(run/'assessment.json',assessment)
    nextstep='Consolidate existing2023 risk matrix and decisions for standard B00/B12/B14/B19/B20, including completed bands, attribution, contraction and fixedfire/AD receipts. No unchanged suites, resampling, fitting, routing or finalroster. Retain unresolved ultimate/capital/reporting limits and own2024/test closed.'
    dump(run/'decision_journal.json',{'author':'Codex','utc':now,'decisions':[{'hypothesis':p['hypothesis'],'criteria_before':{k:p[k] for k in ['concentration','AD_diagnostic','influence_limits']},'sources':p['frozen_sources'],'result':readout,'verification':rel(run/'verification.json'),'consequence':'Retain B00/all alternatives and all valid expensive claims. No ADfilter, coefficient deletion/pricefactor, newalpha or causal conclusion. Further complexity not justified by this diagnosis.'}],'next_artifact_diagnostic':nextstep})
    def fmt(x,n=3):return f'{x:,.{n}f}'.replace(',','_').replace('.',',').replace('_','.')
    table='\n'.join('| '+str(q['fold'])+' | '+fmt(q['W2-B19_AD_ratio'])+' | '+fmt(q['W2-B20_AD_ratio'])+' | '+str(q['yes_periods'])+' / '+str(q['no_periods'])+' | '+fmt(q['yes_fire_T0_CU'],2)+' | '+fmt(q['no_fire_T0_CU'],2)+' | '+('sí' if q['both_fixed_fires_in_fit'] else 'no')+' |' for q in foldviews)
    ratios=[q['yes_fixed_fire_share_of_firecost'] for q in foldviews if q['both_fixed_fires_in_fit']]
    document=f'''# Mejora de B20 en el incendio fijado y variación de AD en edificios

Codex, corte UTC {now}. El incendio de 261.192,30 CU concentra gran parte de la ganancia neta de la selección previa, pero no explica por sí solo la ventaja puntual global de B20 sobre B19. AD sigue cambiando de dirección en el fold 3, cuyo ajuste no contiene ese incendio ni el segundo caso destacado. Se conservan B00, todos los modelos y cada siniestro, sin reentrenar o producir precios nuevos.

## Cada porcentaje tiene un denominador diferente

Se mantuvo el incendio fijado por el primer grupo adverso de B19, antes de mirar este diagnóstico. Su fila y su componente completo coinciden en este caso: un periodo, un grupo. La selección anterior conserva doce grupos y veinte periodos; no es una muestra representativa.

| Denominador de la mejora atribuida al incendio | Participación |
| --- | ---: |
| Ganancia neta de los doce grupos fijados | {fmt(share['fire_row_of_selected_net']*100,1)} % |
| Ganancia bruta positiva por componente en esos doce grupos | {fmt(share['fire_component_of_selected_gross_positive_groups']*100,1)} % |
| Ganancia neta global de 2023 | {fmt(share['fire_component_of_global_net']*100,1)} % |
| Ganancia bruta positiva global por componente | {fmt(share['fire_component_of_global_gross_positive_groups']*100,1)} % |
| Ganancia bruta positiva global por fila | {fmt(share['fire_row_of_global_gross_positive_rows']*100,1)} % |

La ganancia es desviación guardada de B19 menos la de B20. El global combina {fmt(s['global']['gross_group_positive_gain'],2)} unidades positivas por componente y {fmt(s['global']['gross_group_negative_gain_abs'],2)} adversas, para {fmt(s['global']['net_gain'],2)} netas. Hay {s['global']['positive_groups']} componentes con ganancia positiva y {s['global']['negative_groups']} con ganancia negativa. Las compensaciones hacen que una fracción neta sea mucho mayor que la participación bruta. No son probabilidades ni porcentajes intercambiables.

## La sensibilidad a un caso no sustituye la de muchos grupos

La contribución del incendio es {fmt(s['fire_full_component']['net_gain'],2)} unidades. Al excluirlo únicamente del cálculo de evaluación quedan {fmt(s['global_without_fire_component']['net_gain'],2)} unidades positivas netas y ΔD² B20−B19 de +{fmt(s['global_without_fire_component']['derived_delta_D2'],6)}, frente a +{fmt(s['global']['derived_delta_D2'],6)} en el conjunto completo. Se recalcula el nulo común del subconjunto. La exclusión de su fila y de su componente dan el mismo resultado porque contiene una sola fila.

No se elimina el registro, modifica un precio o reajusta un modelo. El contraste es descriptivo sobre 2023 usado adaptativamente, sin intervalo nuevo. Un D² aislado para la sola fila del incendio queda indefinido por desviación nula cero; su contribución se informa en unidades de pérdida. La sensibilidad anterior a 31 grupos de la [atribución completa](ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md) se conserva, sin repetirla o neutralizar su advertencia porque la retirada de un solo caso siga positiva.

El [cotejo de origen](TRAZABILIDAD_SINIESTROS_B19_2023.md) encontró el incendio cerrado, pagado y correctamente asignado. Su T0 realizado no debe confundirse con coste esperado: las predicciones guardadas pasan de {fmt(fire['mu19'],2)} a {fmt(fire['mu20'],2)} CU. Su ganancia deriva del término de coste {fmt(fire['outcome_term'],2)} y del término de predicción {fmt(fire['prediction_term'],2)}, con suma {fmt(fire['saved_gain'],2)}. Se conserva un siniestro válido aunque tenga gran influencia en el score.

## AD cambia de signo en una vista con otra composición de costes

| Fold retenido | AD sí/no B19 | AD sí/no B20 | Filas de ajuste AD sí / no | T0 incendio AD sí, CU | T0 incendio AD no, CU | Ambos incendios fijados en el ajuste |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{table}

Los dos casos fijados suman 547.285,30 CU, tienen AD activado y pertenecen al fold 3. Están fuera del ajuste que produce sus propias predicciones OOF. En las otras cuatro vistas suman entre {fmt(min(ratios)*100,1)} % y {fmt(max(ratios)*100,1)} % del coste de incendios con AD activado. El fold 3 retiene muchos otros componentes: no es un experimento que elimine únicamente esos dos siniestros.

Por eso se distinguen dos afirmaciones. Es verificable que el ajuste 3 no recibe ambos incendios y tiene el coeficiente AD negativo en B19 y B20; los demás folds tienen coeficiente positivo. La mezcla de perils y costes es compatible con sensibilidad a pocos siniestros grandes. No permite demostrar que esos dos casos causen todo el cambio: también cambian otros grupos y relaciones entre variables. La prima modelada tiene todos los perils de T0; la bandera AD no convierte el objetivo en coste exclusivo de daño accidental ni autoriza restringir exposición o siniestros.

Las celdas privadas conservan exposición nominal y exposición efectiva C0 por AD/negocio/ámbito, recuentos de filas y positivos y coste de cada peril. Incluyen las celdas vacías de AD ausente y las vistas retenidas. No se calculan o adoptan tarifas por esas celdas. Cada fila aparece en cuatro vistas de ajuste y una retenida: no son cinco muestras independientes.

## La influencia local disponible pertenece a B19

Se reutilizaron ocho valores ya guardados, cuatro vistas por incendio. La aproximación local de retirar el primer caso cambia el logcoeficiente AD de B19 entre {fmt(approx['primary']['delta_min'],4)} y {fmt(approx['primary']['delta_max'],4)}; la del segundo entre {fmt(approx['secondary']['delta_min'],4)} y {fmt(approx['secondary']['delta_max'],4)}. Son direcciones compatibles con que esos costes sostengan AD en las vistas donde sí entrenan. No son reajustes exactos, valores de influencia de B20 o cambios aplicables a una tarifa. El leverage es alto y limita la aproximación. No se sumaron para inventar una beta conjunta tras borrado ni se calcularon nuevos Hessianos.

## Decisiones y comprobación

No se elimina el incendio, aplica una máscara AD, cambia T0/C0, normaliza B20, ajusta alpha o promueve/retira alternativas. AD permanece inestable; la concentración sigue abierta con sus denominadores correctos. Antes de añadir complejidad procede consolidar los recibos existentes y sus límites por ramo y negocio, incluida la calibración por bandas, sin repetir esas pruebas.

Pasaron {r['passed']} controles del productor, {v['passed']} cotejos propios por otro método y {len(checks)} conciliaciones de lectura, con solapamiento. Se usaron fsum/diccionarios, centavos Decimal y desviación general de sklearn solo para las dos exclusiones fijadas; no se repitieron bootstrap o las suites completas anteriores. El flujo real rechaza un año sintético ajeno a 2023 antes de las tablas de análisis. No se cargaron modelos, ajustaron parámetros o generaron predicciones nuevas. Las pruebas técnicas no convierten estas observaciones en causalidad, superioridad o revisión profesional independiente.

Plan [preinscrito](../../registro/semana2_b20_incendio_AD2023_plan_v1.json), índice `registro/semana2_b20_incendio_AD_actual.json`; fuentes con SHA y detalle por fila quedan en privado. Foro 043/044. 2024/test/SEL01/actas/precios/predicciones/scores/ledger siguen cerrados en este trabajo. La exposición anterior a un asunto externo permanece declarada, sin usar cifras o afirmar ceguera completa. No hubo remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Documentación IAA §§2–3 y Gobernanza §2.8 orientan la trazabilidad y separación de revisión propia, sin certificación o aprobación humana implícita.
'''
    doc=REPO/'docs/semana2/INCENDIO_Y_AD_B20_2023.md'
    with doc.open('x',encoding='utf-8') as f:f.write(document)
    body=f'''El diagnóstico 043 terminó solo con artefactos de 2023, sin entrenamiento, cargas de modelos, predicciones o bootstrap nuevos. Informe `Hackaton/Repositorio_IAA2026/docs/semana2/INCENDIO_Y_AD_B20_2023.md`. B00, todas las alternativas y siniestros conservados.

El incendio aporta 93,9% de la ganancia neta de los doce grupos previos, 71,8% de su mejora bruta positiva por componente, 35,8% de la ganancia global neta y 7,2% de la mejora bruta positiva global por componente (6,6% por fila). El 93,9% no describe a todo B20. Globalmente hay ganancias positivas por {fmt(s['global']['gross_group_positive_gain'],2)} y adversas por {fmt(s['global']['gross_group_negative_gain_abs'],2)}; las compensaciones explican la diferencia de denominadores.

La fila y el componente del incendio coinciden en una sola fila. Al omitirlo únicamente de evaluación quedan {fmt(s['global_without_fire_component']['net_gain'],2)} unidades positivas netas y ΔD² +{fmt(s['global_without_fire_component']['derived_delta_D2'],6)}, frente a +{fmt(s['global']['derived_delta_D2'],6)} global. No se elimina el registro, cambia el precio o reentrena. La advertencia anterior de sensibilidad a 31 grupos sigue vigente y no se repitió; un solo caso no agota la fragilidad ni prueba superioridad.

AD de edificios es negativo solo en el fold 3 de B19 y B20. Los incendios de 261.192,30 y 286.093,00 CU tienen AD activado, suman 547.285,30 CU y están fuera de ese ajuste. En las otras cuatro vistas suponen {fmt(min(ratios)*100,1)}–{fmt(max(ratios)*100,1)}% del coste de incendio con AD activado. La composición es compatible con sensibilidad a pocos costes grandes; no identifica una causa única, porque el fold 3 excluye muchos otros grupos. El objetivo incluye todos los perils, sin convertir la bandera AD en máscara de T0.

Se reutilizan solo ocho influencias locales de B19 ya guardadas, no influencia de B20, reajustes exactos o betas tras borrado. Se conservan celdas de exposición/peril/negocio y ceros, sin tarifas nuevas. Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones por otro método y {len(checks)} conciliaciones, con solapamiento. El comando real rechaza un año sintético antes de las salidas. No suites completas o remuestreo repetidos.

Decisión: mantener B00 y todas las alternativas, sin eliminar siniestros caros, máscara AD, nuevo alpha, normalización, promoción, retiro o lista final. Consolidar recibos existentes por ramo/negocio y advertencias antes de más complejidad. Conclusiones exploratorias, no profesionales independientes. 2024/test/SEL01/actas/precios/predicciones/scores/ledger cerrados; exposición previa de asunto externo declarada sin uso de cifras o ceguera completa. Alcance distinto de las bandas concurrentes, sin repetirlas ni alterar su continuidad. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones.
'''
    with (ROOT/'Hackaton/Semana 2/Codex/incendio_AD_b20_2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
    index={'id':p['id'],'author':'Codex','utc':now,'path_base':'workspace_root','run':rel(run),'documentation':rel(doc),'plan':rel(REPO/'registro/semana2_b20_incendio_AD2023_plan_v1.json'),
           'status':assessment['status'],'policy_years':[2023],'warnings':warnings,'reference':'W2-B00','all_alternatives_preserved':True,
           'new_fits':0,'model_loads':0,'new_price_predictions':0,'new_bootstrap':0,'new_candidate_recipes':0,
           'forum_prior':p['forum_prior'],'forum_result':p['forum_result'],'next_artifact_diagnostic':nextstep,
           'ledger_read':False,'professional_independent_validation':False,'complete_blindness_claim_allowed':False}
    for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check']:
        path=run/(name+'.json');index[name]={'path':rel(path),'sha256':sha(path)}
    dump(run/'index_proposed.json',index)
    print(json.dumps({'documentation':rel(doc),'readout_checks':len(checks),'fire_global_net_share':share['fire_component_of_global_net'],'fire_global_positive_gross_group_share':share['fire_component_of_global_gross_positive_groups'],'delta_without_fire':s['global_without_fire_component']['derived_delta_D2']},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);main(Path(parser.parse_args().run))
