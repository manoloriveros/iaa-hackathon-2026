"""Informe de contracción y nivel a partir de artefactos ya verificados."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,x):
    with path.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False,default=lambda v:v.item() if hasattr(v,'item') else str(v));f.write('\n')


def main(run):
    run=run.resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');assert r['failed']==v['failed']==0
    now=datetime.now(timezone.utc).isoformat();checks=[]
    reused=bool(r['concurrent_full_log_decomposition_reused'])
    concurrency_text=('Se reutilizaron sus términos guardados con SHA y se cotejaron en estos veinte periodos.' if reused else 'La fuente concurrente no estaba materializada al registrar. Se fijó entonces el cotejo del diseño común solo en veinte periodos, con replay nativo y reconstrucción manual. No se consumieron resultados que todavía no existían ni se repitió la descomposición completa de 50.094 filas.')
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    norms=pq.read_table(run/'standardized_coefficient_norms.parquet').to_pandas()
    c=pq.read_table(run/'coefficients_original_scale.parquet').to_pandas()
    focused=c[c.feature.isin(['x_new_business','x_accidental_damage_cover','x_cover_type']) & c.level.ne('comprehensive')].copy()
    stability=[]
    for keys,g in focused.groupby(['model_id','line','feature','level','reference'],sort=True):
        b=g.beta_raw.to_numpy();check('Five saved folds for contrast',len(g)==5 and g.fold.nunique()==5)
        stability.append(dict(zip(['model_id','line','feature','level','reference'],keys),beta_min=float(b.min()),beta_max=float(b.max()),beta_sd_overlap_folds=float(np.std(b)),ratio_min=float(np.exp(b.min())),ratio_max=float(np.exp(b.max()))))
    dump(run/'coefficient_stability_readout.json',stability)
    levels=read(run/'level_diagnostics_2023.json');levelmap={(x['dimension'],x['label']):x for x in levels}
    rows=pq.read_table(run/'fixed_period_comparison_2023.parquet').to_pandas();groups=pq.read_table(run/'fixed_group_comparison_2023.parquet').to_pandas();d=pq.read_table(run/'fixed_period_logratio_decomposition.parquet').to_pandas()
    check('Original20rows12groups',len(rows)==20 and rows.group_id.nunique()==12)
    for item in levels:
        check('Ratio of existing bridge totals',math.isclose(item['observed_bridge_ratio_B20_B19'],item['B20_observed_bridge_total']/item['B19_observed_bridge_total'],rel_tol=1e-12))
    reasons=pq.read_table(ROOT/p['selection_reasons']).to_pandas();cases=[]
    for scope,rank,label in [('motor_new',1,'Autos nuevos, lesión corporal principal'),('buildings',1,'Edificios, incendio OOF más adverso'),('buildings',2,'Edificios, incendio influyente sobre AD')]:
        g=reasons.loc[reasons.reason.eq('OOF_top5_adverse_'+scope)&reasons['rank'].eq(rank),'group_id'].iloc[0]
        part=rows[rows.group_id.eq(g)&rows.line.eq('motor' if scope=='motor_new' else 'buildings')]
        check('Highlighted component remains its original period',len(part)==1)
        record=part.iloc[0];change=d[d.row_id.eq(record.row_id)&d.line.eq(record.line)].iloc[0]
        cases.append({'label':label,'T0_CU':float(record.T0),'B19_expected_period_CU':float(record.B19_prediction),'B20_expected_period_CU':float(record.B20_prediction),
                      'prediction_ratio':float(record.B20_prediction/record.B19_prediction),'saved_deviance_gain_B20':float(record.saved_deviance_gain_B20),
                      **{term:float(change[term]) for term in ['delta_intercept','delta_coverage','delta_newbusiness','delta_other_main_effects','delta_log_rate']}})
    attribution=read(run/'fixed_gain_attribution.json')
    check('Selected gain matches same20rows',math.isclose(attribution['fixed_group_saved_gain'],float(rows.saved_deviance_gain_B20.sum()),rel_tol=1e-12,abs_tol=1e-8))
    readout={'author':'Codex','utc':now,'norm_pairs':len(norms),'joint_norm_contracts':int(norms.joint_norm_contracts.sum()),
             'joint_norm_reduction_range':[float(norms.relative_norm_reduction.min()),float(norms.relative_norm_reduction.max())],
             'pairs_with_growing_coordinates':int(norms.absolute_coordinates_larger.gt(0).sum()),'growing_coordinates_across_pairs':int(norms.absolute_coordinates_larger.sum()),
             'selected_group_line_cells':len(groups),'selected_cells_gain_positive':int(groups.saved_deviance_gain_B20.gt(0).sum()),'selected_cells_gain_negative':int(groups.saved_deviance_gain_B20.lt(0).sum()),
             'cases_no_private_ids':cases,'level_summaries':levels,'gain_attribution':attribution,
             'fixed_group_selection_not_representative':True,'group_norm_not_coordinatewise_guarantee':True,
             'decomposition_is_common_coding_not_causal':True,'new_fits':0,'new_models':0,'new_price_predictions':0,'new_bootstrap':0}
    dump(run/'readout.json',readout);dump(run/'readout_reconciliation.json',{'utc':now,'passed':len(checks),'failed':0,'checks':checks})
    warnings=[{'id':'B20-CONTRACTION-COORDINATES','status':'open','effect':'Jointnorm contraction does not contract everycoordinate; rawscale units/common references required. Fiveoverlappingfolds are not independent CI.'},
              {'id':'B20-LEVEL-CODING','status':'open','effect':'Intercept/coverage/business/other decomposition depends on shared centering/reference and all effects change. No coverage-only causal effect or adopted calibration.'},
              {'id':'B20-FIXED-GROUPS','status':'open','effect':'The12groups were selected by priorB19 loss/influence. Their gain fraction of netportfolio gain can exceed100%; no freshvalidation, groupdeletion or model promotion.'}]
    dump(run/'assessment.json',{'author':'Codex','utc':now,'status':'saved_B20_coefficient_and_level_audit_verified_no_promotion','warnings':warnings,'new_fits':0,'professional_independent_validation':False})
    nextstep='When the concurrent B20 attribution completes, reconcile its existing receipts with this coefficient audit; consolidate2023 line/business level and no-promotion evidence, without rerunning either suite or training. PreserveB00/all alternatives and unresolved ultimate/reporting/capital conditions; no2024/test opening.'
    dump(run/'decision_journal.json',{'author':'Codex','utc':now,'decisions':[{'hypothesis':p['hypothesis'],'criteria_before':p['criterion_before'],'source_hashes':p['frozen_sources'],'result':readout,'verification':rel(run/'verification.json'),'consequence':'Keep all data/models/B00, no routing/normalization/alpha/feature change or final roster. Concurrent same-author work is not independent professional validation.','concurrent_source_reused':reused}],'next_artifact_diagnostic':nextstep})
    def number(x,n=3):return f'{x:,.{n}f}'.replace(',','_').replace('.',',').replace('_','.')
    def contrast(line,feature,level):
        z=[x for x in stability if x['line']==line and x['feature']==feature and x['level']==level]
        return {x['model_id']:x for x in z}
    coefrows=[]
    for line,feature,level,label in [('buildings','x_accidental_damage_cover','unit','Edificios AD sí/no'),('motor','x_cover_type','third_party_only','Autos TPOnly/comprehensive'),('motor','x_cover_type','third_party_fire_theft','Autos TPFireTheft/comprehensive'),('motor','x_new_business','unit','Autos nuevo negocio'),('buildings','x_new_business','unit','Edificios nuevo negocio')]:
        z=contrast(line,feature,level);a,b=z['W2-B19'],z['W2-B20'];coefrows.append('| '+label+' | '+number(a['ratio_min'])+'–'+number(a['ratio_max'])+' | '+number(b['ratio_min'])+'–'+number(b['ratio_max'])+' |')
    predictiontable='\n'.join('| '+z['label']+' | '+number(z['T0_CU'],2)+' | '+number(z['B19_expected_period_CU'],2)+' | '+number(z['B20_expected_period_CU'],2)+' | '+number(z['prediction_ratio'])+' |' for z in cases)
    termtable='\n'.join('| '+z['label']+' | '+' | '.join(number(z[key]) for key in ['delta_intercept','delta_coverage','delta_newbusiness','delta_other_main_effects','delta_log_rate'])+' |' for z in cases)
    leveltable='\n'.join('| '+label+' | '+number(z['B19_observed_bridge_total'],2)+' | '+number(z['B20_observed_bridge_total'],2)+' | '+number(100*(z['observed_bridge_ratio_B20_B19']-1),2)+' % |' for label,z in [
        ('Global 2023',levelmap[('global','all2023')]),('Doce grupos, veinte periodos',levelmap[('fixed_union','same12groups20periods')]),
        ('Cinco edificios adversos de B19',levelmap[('fixed_OOF_top5','buildings')]),('Cinco autos nuevos adversos de B19',levelmap[('fixed_OOF_top5','motor_new')])])
    fraction=attribution['fixed_gain_over_global_net_gain'];fractiontext=number(fraction*100,1)+' %' if fraction is not None else 'no definida por ganancia global nula'
    doc=REPO/'docs/semana2/CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md'
    text=f'''# Contracción y nivel de B20 frente a B19

Codex, corte UTC {now}. Se compararon los quince pares de GLM guardados y los mismos doce grupos, veinte periodos de 2023, de la traza de B19. La norma conjunta se reduce en {readout['joint_norm_contracts']} de quince pares; hay {readout['pairs_with_growing_coordinates']} pares con alguna coordenada que crece en valor absoluto. El diagnóstico no cambia un modelo, T0/C0 o la referencia B00.

## Alcance y concurrencia

El primer borrador del diagnóstico encontró una unidad concurrente de atribución B20 que ya preparaba los cambios de tasa por grupos. Se conserva sin ejecutar y v2 se registró en el comentario 040 antes del cálculo. {concurrency_text} El trabajo nuevo compara coeficientes/transformaciones y hace replay nativo focal y una reconstrucción manual. No se repitió su análisis global de retirada de grupos, las suites 542/48 de B20 ni bootstrap. Una colisión con el archivo del cuerpo v1 detuvo la preparación de v2 después de guardar su plan, sin cálculos; se conservó el cuerpo anterior y se completó un cuerpo v2 separado, sin alterar fuentes o plan. La colaboración entre cálculos de Codex no se presenta como validación profesional independiente.

Se mantienen los cinco folds guardados, siete efectos por ramo y las transformaciones aprendidas dentro de cada ajuste. Se comprobaron medianas, medias/escalas y categorías/referencias iguales entre B19 y B20. La única diferencia de parámetros del estimador es alpha 0 frente a 1. El intercepto queda libre. Solo se reproducen las veinte predicciones OOF existentes de cada modelo para cotejo; no se producen precios con coeficientes alterados, nuevos aspirantes o un factor de normalización.

## Qué contrae la penalización

La reducción de norma L2 estandarizada va de {number(readout['joint_norm_reduction_range'][0]*100,1)} % a {number(readout['joint_norm_reduction_range'][1]*100,1)} %. Se observaron {readout['growing_coordinates_across_pairs']} excepciones de coordenada entre los quince pares. La norma suma cuadrados en el diseño estandarizado y las dummies fijadas; no se compara mezclando unidades originales distintas ni garantiza contracción de cada beta. La penalización one-hot depende de su referencia, que aquí no cambió.

| Contraste de tasa en escala original | B19: rango entre cinco folds | B20: rango entre cinco folds |
| --- | ---: | ---: |
{chr(10).join(coefrows)}

Son cocientes condicionales de tasa del GLM, con los demás efectos fijos. Los ajustes comparten cuatro de cinco folds: su dispersión no es un intervalo de confianza independiente. Una menor dispersión no prueba mejor respuesta en cada segmento ni atribuye la mejora a cobertura sola, porque se penalizan todos los efectos.

La reducción de norma no resuelve el cambio de dirección de AD en edificios: ambos rangos siguen cruzando 1. En autos, third_party_only se acerca a 1 y el rango de B20 llega a superarlo ligeramente; el efecto de nuevo negocio permanece próximo al de B19. Son advertencias concretas para evitar presentar la regularización como estabilización uniforme.

## Nivel de los mismos grupos

| Ámbito fijo | Predicción B19 CU | Predicción B20 CU | Cambio del total |
| --- | ---: | ---: | ---: |
{leveltable}

Estos totales usan la predicción existente con el mismo vínculo observado C0. El anexo privado conserva por separado los totales nominales condicionales de 2023, calculados como exposición nominal por tasa anual; no son estimaciones validadas de 2025. El intercepto no equivale a calibración agregada: el total resulta de todos los efectos, composición y exposiciones. Los cinco grupos por ámbito ya se fijaron por resultados de B19; no se reseleccionan a favor de B20.

| Caso de la selección | T0 realizado CU | Coste esperado B19 CU | Coste esperado B20 CU | Razón B20/B19 |
| --- | ---: | ---: | ---: | ---: |
{predictiontable}

Un coste esperado de periodo no es una severidad ni debe igualar un siniestro realizado. La [traza de origen](TRAZABILIDAD_SINIESTROS_B19_2023.md) confirmó que la lesión corporal principal y el incendio de 286.093 CU están cerrados y pagados. Se conservan aunque pesen en la evaluación; no se adopta una tarifa para estos casos ni se eliminan registros.

## Descomposición del cambio real

Con el mismo diseño Z, `log(tasa20/tasa19) = cambio de intercepto + cobertura + nuevo negocio + otros efectos`. Los términos siguientes son diferencias de los dos modelos guardados, en escala logarítmica, y suman el cambio completo:

| Caso | Intercepto | Cobertura | Nuevo negocio | Otros efectos | Total log |
| --- | ---: | ---: | ---: | ---: | ---: |
{termtable}

El centrado y las categorías base fijan el reparto. No es una atribución causal ni un modelo donde se cambió únicamente cobertura. Su igualdad se comprobó frente al replay nativo y mediante un predictor manual en escala original, con medianas y codificación guardadas.

Los mismos veinte periodos aportan {number(attribution['fixed_group_saved_gain'],2)} unidades de mejora de desviación guardada, frente a {number(attribution['saved_global_deviance_gain_B20'],2)} globales. Equivale a {fractiontext} de la ganancia neta; el resto aporta {number(attribution['remaining_group_saved_gain'],2)}. El cociente usa ganancia neta, admite compensaciones y puede exceder 100 %: no es fracción de mejora bruta ni probabilidad. Los grupos estaban enriquecidos por errores previos de B19. No se calcula otra retirada o una validación nueva con este resultado.

## Comprobación y decisión

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones propias por otro método y {len(checks)} conciliaciones de lectura, con solapamiento. Se verificaron normas con fsum, balances por grupo/ámbito, escala original de coeficientes, transformaciones y veinte predictores manuales por modelo. El flujo real con C0 sintético incompatible falla antes de abrir modelos y producir coeficientes. Guardas de año, claves, objetivo y transformaciones rechazan casos adversos; las entradas de fit quedan bloqueadas. No se reentrena ni se repiten las verificaciones estadísticas originales.

La lectura queda preparada para conciliarse con la atribución concurrente cuando termine y mantiene las advertencias de concentración, segmentos, nivel y último. No promueve B20, retira B19 o congela una lista. No se adopta enrutamiento por grupo, otro alpha, cobertura, factor de nivel o mayor complejidad. Las conclusiones son exploratorias tras búsqueda adaptativa de 2023. B00 y todas las alternativas siguen conservados.

La exposición previa de un asunto externo se mantiene declarada, sin usar cifras o afirmar ceguera completa. 2024/test siguen cerrados: no precios, predicciones, scores, actas, SEL01 o ledger de esos ámbitos. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Documentación IAA §3 y Gobernanza §2.8 sustentan la separación de evidencia, decisiones y revisión propia; no hay aprobación humana o profesional independiente implícita.

Plan: [diagnóstico v2](../../registro/semana2_b20_contraccion2023_plan_v2.json). Índice: `registro/semana2_b20_contraccion_actual.json`; datos por fila, fuentes y hashes quedan en privado. Foro 040/041. La siguiente unidad debe conciliar ambos diagnósticos terminados y consolidar la evidencia ya existente por ramo/negocio, sin repetir cálculos o iniciar otra tanda.
'''
    with doc.open('x',encoding='utf-8') as f:f.write(text)
    body=f'''El diagnóstico v2 registrado en 040 terminó con los mismos doce grupos y veinte periodos, sin reentrenar, nuevos precios, receta, alpha o bootstrap. Se conservan B00 y todas las alternativas. Informe: `Hackaton/Repositorio_IAA2026/docs/semana2/CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md`.

Se concilió el alcance con la unidad concurrente de atribución B20. {concurrency_text} El borrador v1 se conservó sin comentario previo o cálculos; v2 precede al diagnóstico. El trabajo nuevo compara los quince pares de coeficientes y estados de transformación, con replay nativo focal y predictor manual por otro método. La colisión del cuerpo v1 se resolvió preservándolo y creando el cuerpo v2, con plan/fuentes intactos y sin cálculos previos.

La norma L2 estandarizada contrae en {readout['joint_norm_contracts']}/15 pares, con reducción entre {number(readout['joint_norm_reduction_range'][0]*100,1)}% y {number(readout['joint_norm_reduction_range'][1]*100,1)}%; {readout['pairs_with_growing_coordinates']} pares tienen coordenadas que crecen. No se supone contracción individual o causalidad de cobertura. Se mantienen referencias, escalas, T0/C0 y folds. Los rangos de efectos por ramo y nuevo negocio están en la tabla del informe; cinco folds solapados no son CI independiente.

AD de edificios sigue cambiando de dirección entre folds; third_party_only de autos se acerca a 1 y el rango B20 lo supera ligeramente. El efecto de nuevo negocio de autos cambia poco. Una norma menor no elimina esas inestabilidades.

Sobre la unión fija, el total observado B20/B19 es {number(levelmap[('fixed_union','same12groups20periods')]['observed_bridge_ratio_B20_B19'])}; globalmente es {number(levelmap[('global','all2023')]['observed_bridge_ratio_B20_B19'])}. El componente principal de autos nuevos pasa de {number(cases[0]['B19_expected_period_CU'],2)} a {number(cases[0]['B20_expected_period_CU'],2)} CU esperadas; su coste realizado es 136.767,16 CU y no se equipara a una prima esperada. Los términos de intercepto/cobertura/negocio/otros se cotejan como diferencias de modelos completos, sin precios con betas alteradas.

Los doce grupos aportan {number(attribution['fixed_group_saved_gain'],2)} de mejora de desviación guardada, {fractiontext} de la mejora global neta ya existente. El resto aporta {number(attribution['remaining_group_saved_gain'],2)}; hay compensaciones y la selección es posterior a B19, sin nueva validación, eliminación o superioridad acreditada.

Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones propias y {len(checks)} conciliaciones, con solapamiento. C0 sintético incompatible falla en el flujo real antes de abrir modelos; guardas y fit bloqueado cotejados. No se repiten suites 542/48 o bootstrap. Próximo paso: conciliar ambos diagnósticos y consolidar advertencias por ramo/negocio con artefactos existentes. No promover, retirar, ajustar un factor o complejizar por este resultado. 2024/test/SEL01/actas/scores/ledger cerrados en este trabajo; exposición previa de asunto externo declarada sin uso de cifras o ceguera completa. Revisión propia, no profesional independiente. Se preservan concurrencia, autoría ajena, catálogo/contador y otras automatizaciones.
'''
    with (ROOT/'Hackaton/Semana 2/Codex/contraccion_b20_2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
    index={'id':p['id'],'author':'Codex','utc':now,'path_base':'workspace_root','run':rel(run),'documentation':rel(doc),'plan':rel(REPO/'registro/semana2_b20_contraccion2023_plan_v2.json'),
           'status':'saved_B20_coefficient_and_level_audit_verified_no_promotion','policy_years':[2023],'fixed_groups':12,'fixed_periods':20,'warnings':warnings,
           'reference':'W2-B00','all_alternatives_preserved':True,'new_fits':0,'new_models':0,'new_price_predictions':0,'new_bootstrap':0,'new_global_D2_or_CI':False,
           'concurrent_attribution_reused':reused,'professional_independent_validation':False,'ledger_read':False,'complete_blindness_claim_allowed':False,
           'forum_prior':p['forum_prior'],'forum_result':p['forum_result'],'next_artifact_diagnostic':nextstep}
    for key in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check']:
        path=run/(key+'.json');index[key]={'path':rel(path),'sha256':sha(path)}
    dump(run/'index_proposed.json',index)
    print(json.dumps({'documentation':rel(doc),'readout_checks':len(checks),'norm_contracts':readout['joint_norm_contracts'],'growing_coordinates':readout['growing_coordinates_across_pairs'],'fixed_gain_over_global_net':fraction,'main_motor_expected_B20':cases[0]['B20_expected_period_CU']},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);main(Path(parser.parse_args().run))
