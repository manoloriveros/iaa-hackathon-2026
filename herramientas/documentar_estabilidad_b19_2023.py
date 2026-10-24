"""Lectura de estabilidad e influencia; sin convertir retiros en recetas."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    run=Path(sys.argv[1]).resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');NOW=datetime.now(timezone.utc).isoformat();assert r['failed']==v['failed']==0
    table=lambda name:pq.read_table(run/(name+'.parquet')).to_pandas()
    coef=table('coefficients_original_scale');groups=table('oof_group_contributions');local=table('training_group_local_influence');marks=table('focus_group_perils');pair=table('paired_oof_2023');selections=table('ranked_group_selections')
    focus=read(run/'focus_summary.json');removals=read(run/'group_removal_evaluation.json');h=read(run/'hessian_conditions.json');checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    stability=[]
    for keys,g in coef.groupby(['model_id','line','feature','level'],sort=True):
        same=g.reference.nunique()==1 and g.fold.nunique()==5
        check('Comparable rawcoding '+str(keys),same)
        stability.append({'model_id':keys[0],'line':keys[1],'feature':keys[2],'level':keys[3],'reference':g.reference.iloc[0] if same else None,'comparable':same,
            'folds':g.fold.nunique(),'beta_min':float(g.beta_raw.min()),'beta_max':float(g.beta_raw.max()),'ratio_min':float(np.exp(g.beta_raw.min())),'ratio_max':float(np.exp(g.beta_raw.max())),
            'negative_folds':int(g.beta_raw.lt(0).sum()),'positive_folds':int(g.beta_raw.gt(0).sum()),'independent_CI':False})
    pd.DataFrame(stability).to_parquet(run/'coefficient_stability_summary.parquet',index=False)
    check('Each training group appears in4otherfolds',local.groupby(['line','group_id']).fold.nunique().eq(4).all() and local.group_validation_fold.ne(local.fold).all())
    links=[];top_public=[]
    for scope,line,field in [('buildings','buildings','x_accidental_damage_cover'),('motor_new','motor','x_cover_type')]:
        g=groups[groups.scope.eq(scope)].sort_values(['loss_delta','group_id'],ascending=[False,True]);top=g.head(5);allfocus=next(x for x in focus if x['scope']==scope)
        frame=pq.read_table(ROOT/p['b19_run']/f'inputs_2023/{line}_fold0.parquet',columns=['group_id',field]).to_pandas()
        for rank,row in enumerate(top.itertuples(index=False),1):
            inf=local[local.group_id.eq(row.group_id)&local.line.eq(line)];per=marks[marks.scope.eq(scope)&marks.group_id.eq(row.group_id)];pred=pair[pair.group_id.eq(row.group_id)&pair.line.eq(line)]
            record={'scope':scope,'rank_adverse':rank,'group_id':row.group_id,'validation_fold':int(row.fold),'rows':int(row.rows),'T0_CU':row.T0,'loss_delta':row.loss_delta,
                'fraction_gross_adverse':float(row.loss_delta/allfocus['gross_adverse_loss']),'perils':per.groupby('peril').net_cents.sum().to_dict(),
                'coverage_values':[str(x) for x in frame[frame.group_id.eq(row.group_id)][field].unique()],
                'B19_existing_OOF_prediction':float(pred.B19_prediction.sum()),'B14_existing_OOF_prediction':float(pred.B14_prediction.sum()),
                'present_in_fit_folds':sorted(int(x) for x in inf.fold),'local_coverage_delta_log_min':float(inf.local_delete_delta_coverage_beta.min()),
                'local_coverage_delta_log_max':float(inf.local_delete_delta_coverage_beta.max()),'max_group_leverage_trace':float(inf.group_leverage_trace.max())}
            links.append(record);top_public.append({k:x for k,x in record.items() if k!='group_id'})
            check('Focal group not inownfit '+scope+str(rank),row.fold not in inf.fold.tolist() and len(inf)==4)
    check('Top5building adverse groups arefire',all(set(x['perils'])=={'fire'} for x in links if x['scope']=='buildings'))
    motor=next(x for x in links if x['scope']=='motor_new' and x['rank_adverse']==1)
    check('Motor dominant component isTPOnly bodilyinjury',motor['coverage_values']==['third_party_only'] and set(motor['perils'])=={'bodily_injury'} and motor['rows']==1)
    build=next(x for x in focus if x['scope']=='buildings');motorfocus=next(x for x in focus if x['scope']=='motor_new')
    check('All individualbuilding deletions remainnegative',build['single_group_delta_max']<0)
    check('Motor onegroupevaluation flipscontrast',motorfocus['delta_B19_minus_B14']<0 and motorfocus['single_group_delta_max']>0)
    summary={'utc':NOW,'focus':focus,'top_groups_without_IDs':top_public,'local_hessian_condition_min':min(x['condition'] for x in h),'local_hessian_condition_max':max(x['condition'] for x in h),
        'max_directional_derivative_error':max(x['relative_error'] for x in v['directional_derivatives']),
        'building_top5_gross_adverse_fraction':float(sum(x['loss_delta'] for x in links if x['scope']=='buildings')/build['gross_adverse_loss']),
        'motor_top1_gross_adverse_fraction':motor['fraction_gross_adverse'],'no_retraining_or_model_mutation':True,'new_bootstrap':0,'no_deletion_adopted':True}
    for name,obj in [('group_training_OOF_links.json',links),('readout.json',summary),('readout_reconciliation.json',{'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks})]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert all(x['pass'] for x in checks)
    curves=[]
    for scope in ['buildings','motor_new']:
        for k in p['removal_k']:
            a=next(x for x in removals if x['scope']==scope and x['direction']=='adverse' and x['requested_groups']==k)
            b=next(x for x in removals if x['scope']==scope and x['direction']=='favorable' and x['requested_groups']==k)
            curves.append(f'| '+('Edificios' if scope=='buildings' else 'Autos nuevos')+f' | {k} | {a["delta_scope_D2"]:+.6f} | {b["delta_scope_D2"]:+.6f} |')
    selected=[x for x in stability if x['model_id']=='W2-B19' and ((x['feature']=='x_accidental_damage_cover') or (x['feature']=='x_cover_type' and x['level']!='comprehensive') or x['feature']=='x_new_business')]
    ratios=[]
    for x in selected:
        if x['feature']=='x_new_business':label='Nuevo / renovación'
        elif x['feature']=='x_accidental_damage_cover':label='AD sí / AD no'
        else:label=x['level']+' / comprehensive'
        ratios.append(f'| {x["line"]} | {label} | {x["ratio_min"]:.3f}–{x["ratio_max"]:.3f} | {x["negative_folds"]} | {x["positive_folds"]} |')
    co=read(ROOT/p['counter_snapshot'])
    doc=f'''# Estabilidad de coeficientes e influencia de grupos en B19

Codex, corte UTC {NOW}. Solo artefactos de 2023: modelos B19 y B14 guardados, OOF y siniestros canónicos. Cero entrenamientos, recetas nuevas o remuestreos. B00 y todas las alternativas permanecen. La receta diagnóstica se publicó en el comentario 036 antes del cálculo.

## Dos formas distintas de influencia

La pérdida relativa de autos nuevos depende mucho de un componente con lesiones corporales. En edificios la influencia se reparte entre varios componentes, especialmente incendios. La dispersión de coeficientes se mantiene al compararlos en su escala original; no es un artefacto de comparar coeficientes estandarizados con escalas diferentes.

La contribución OOF de un componente mide cómo cambia la desviancia B19 frente a B14 en sus filas retenidas. La influencia local de ajuste aproxima cómo cambiarían los coeficientes si se redujera el peso de ese componente en otros modelos donde sí participó. Cada componente está fuera del ajuste que produjo su propia predicción OOF. No se confunden esos dos mecanismos.

## Coeficientes comparables

Las pendientes numéricas se recuperan como beta_estandarizado/escala, con la corrección del intercepto por centrado. Se comprueban las mismas referencias categóricas; no se fabrica una comparación para categorías ausentes o agrupadas. Los cinco folds comparten datos y no son cinco observaciones independientes para construir un intervalo.

| Ramo | Razón condicional de tasa | Rango entre folds | Coeficiente negativo | Positivo |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(ratios)}

En edificios, AD sí / AD no va de 0,795 a 1,388 y cambia dirección: el fold 3 es inferior a uno. En autos, third_party_only/comprehensive va de 0,567 a 0,857; third_party_fire_theft/comprehensive es más estable, aproximadamente 0,587–0,611. Nuevo negocio de autos conserva una razón próxima a la de B14; no se atribuye toda la inestabilidad al campo añadido. Estas son asociaciones condicionales del GLM para coste total, no efectos causales de una cobertura o confirmación del clausulado.

## Pérdida OOF por componente

Se define A_g como la suma de desviancia B19 menos B14. Valores positivos son adversos para B19. La selección de grupos se fijó por signo y rango, con empates por ID y tamaños 1, 5, 10 y 31. No se ajustó el número de grupos para elegir un modelo. Se recalcula la nula común al retirar filas únicamente de la evaluación.

En edificios hay 12.107 componentes y delta D² B19−B14 de −0,012743. Todos los retiros individuales mantienen el signo negativo; retirar el más adverso deja −0,009127. Los cinco componentes más adversos son incendios y reúnen 1.237.635,60 CU de T0, aproximadamente el {100*summary['building_top5_gross_adverse_fraction']:.1f}% de las pérdidas brutas de desviancia adversa. Su compensación con grupos favorables se conserva, sin presentar solo una cola de la distribución.

Autos nuevos tiene 2.427 componentes y delta D² −0,021777. Un componente con una fila, third_party_only y lesiones corporales concentra el {100*summary['motor_top1_gross_adverse_fraction']:.1f}% de la pérdida bruta adversa. Su T0 es 136.767,16 CU; los costes esperados OOF ya guardados son 90,25 CU en B19 y 132,77 CU en B14. Son costes esperados por periodo: su distancia a un siniestro grande no significa que el precio deba igualar ese importe. Al retirar solo ese componente de la evaluación del segmento, el contraste cambia a +0,009766. El contraste global del portafolio continúa negativo, −0,002430, al retirar su componente completo.

| Ámbito | Grupos retirados de evaluación | Delta D² al retirar adversos | Delta D² al retirar favorables |
| --- | ---: | ---: | ---: |
{chr(10).join(curves)}

La tabla se limita al segmento indicado. El anexo conserva además la retirada del componente completo en todos los ramos para la métrica global, y todos los retiros individuales. Los IDs están en artefactos restringidos. Los grupos se ordenan después de observar las pérdidas de 2023; estas sensibilidades son exploratorias, no nuevos conjuntos de validación o intervalos. No se eliminan registros de datos o modelos y no se declara superioridad del modelo sobre el subconjunto elegido.

## Influencia local sobre el ajuste, sin reentrenar

Para diez modelos guardados de autos/edificios se usa el Hessiano observado del GLM con su diseño completo y el gradiente de cada componente. La aproximación de retirada es delta_beta ≈ H⁻¹G_g, convirtiendo después a escala original. Se mantiene H completo y C0 fijo: no es un ajuste sin el grupo, no vuelve a estimar transformaciones o curvas y no sustituye coeficientes para producir precios. El gradiente residual del ajuste y la traza de leverage quedan registrados.

El componente de lesiones corporales anterior aparece en los ajustes 1, 2, 3 y 4, pero no en el 0 que lo predijo. Es el de mayor influencia local absoluta sobre third_party_only entre los componentes de ajuste con negocio nuevo en esos cuatro modelos. Su retirada local aproxima cambios de −0,223 a −0,245 en el logcoeficiente de cobertura y de −0,195 a −0,213 en el de nuevo negocio. El modelo 0, donde falta todo ese fold, tiene la razón third_party_only más baja. Esa coincidencia no aísla el efecto exacto del componente: también faltan los demás grupos de su fold.

En edificios, un incendio de 286.093 CU es el componente con mayor influencia local sobre AD en cuatro ajustes. Sus cambios aproximados del logcoeficiente van de −0,100 a −0,156. No explica por sí solo toda la inversión de signo entre folds. Los cinco mayores grupos adversos OOF también son incendios; una bandera de daño accidental está asociándose a diferencias de coste total, que incluye otros perils. No se infiere una exclusión contractual o una limpieza de incendios caros.

Los Hessianos tienen condiciones de aproximadamente {summary['local_hessian_condition_min']:.1f} a {summary['local_hessian_condition_max']:.1f}, lejos del límite técnico previo de 1e12, sin pseudoinversa o ridge. Esto respalda la solución numérica, no la precisión de una retirada completa. Las trazas máximas de leverage de grupos llegan aproximadamente a 0,461 en edificios y 0,293 en autos; ante grupos influyentes, cambios grandes y el Hessiano de grupo omitido limitan la aproximación local. No se usa como prueba causal ni se calcula un precio corregido con ella.

## Verificación, decisiones y continuidad

Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones separadas y {sum(x['pass'] for x in checks)} conciliaciones de lectura, con solapamiento. Fit está bloqueado. La segunda implementación contrasta coeficientes originales, cuentas de grupos por otra fórmula de desviancia y métricas por filas con sklearn, selección de signos/empates, derivadas direccionales del Hessiano y soluciones duales por Cholesky. El error relativo máximo de derivadas es {summary['max_directional_derivative_error']:.2g}. El flujo real rechaza un cambio de T0 entre modelos antes de calcular Hessianos; el fallo esperado queda marcado. Una guarda inicial de continuidad detuvo el intento previo al completarse otra unidad concurrente; no hubo cálculo o ajuste, y se preservó su trabajo al registrar este diagnóstico.

Se conservan los modelos, T0, C0, OOF y grupos. La revisión documenta sensibilidad a siniestros grandes y a composición de folds, sin promover o retirar alternativas. El siguiente paso es cotejar la traza de los componentes destacados (pagado, reservas, recuperaciones, estado y fechas), manteniendo importes y cohortes; cualquier nuevo ensayo requiere su propia receta y autorización aplicable. No se repite el remuestreo anterior ni se salta a otra familia de modelos.

El contador al corte de entrada era {co['cumulative_price_base_fits']} ajustes de precio y {co['cumulative_closed_form_constants']} constantes. Esta revisión añade cero; no modifica el contador o el catálogo activo de otras continuaciones. Sus cortes y cambios concurrentes se conservan. Revisión técnica propia de Codex, no validación profesional independiente o aprobación humana.

2024 permanece cerrado para este trabajo, también test, actas, predicciones, scores y ledger. Se mantiene la exposición previa de un título ajeno con métricas externas, sin repetirlas o usarlas ni afirmar ceguera completa. Solo se muestran autor, ID y UTC del foro. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones.

[Plan congelado](../../registro/semana2_b19_estabilidad2023_plan_v1.json), [índice de esta revisión](../../registro/semana2_b19_estabilidad_actual.json), [productor](../../src/semana2/diagnosticar_estabilidad_b19_2023.py), [comprobador](../../herramientas/verificar_estabilidad_b19_2023.py), [ensayo B19 original](GLM_COBERTURAS_2023.md). Evidencia y hashes restringidos: `{rel(run)}`. El [balance nocturno](BALANCE_NOCTURNO_PARCIAL_20261024.md) sigue siendo parcial hasta las 07:00 Bogotá.
'''
    docpath=REPO/'docs/semana2/ESTABILIDAD_E_INFLUENCIA_B19_2023.md';assert not docpath.exists();docpath.write_text(doc,encoding='utf-8')
    warnings=[{'id':'B19-STABILITY-FOLDS','status':'open','effect':'Coverage coefficients vary on common original scale;5overlappingfits are not independent CI. Numerical Hessian conditioning does not establish generalization.'},
        {'id':'B19-GROUP-MOTOR','status':'open','effect':'OneTPOnly bodilyinjury component accounts for56.1%gross adverse motornewloss; evaluation deletion flipssegmentcontrast but not wholeportfolio. No record removal or promotion.'},
        {'id':'B19-GROUP-BUILDINGS','status':'open','effect':'No individualgroup deletion removes building loss; top5adversegroups arefire. AD effect associates with totalcost/perils, not contract-only accidental risk.'},
        {'id':'B19-LOCAL-APPROX','status':'open','effect':'H^-1G localdeletion uses fullH/frozenC0, not refit; highleverage and largecomponents make exact deletion uncertain. No changedcoefficient price or score.'},
        {'id':'B19-SOURCE-TRACE','status':'open','effect':'Validate payment/reserve/recovery/status/date lineage of highlighted heavyclaims before another recipe; never delete a valid expensive claim to improve score.'}]
    assessment={'author':'Codex','utc':NOW,'status':'B19_saved_artifacts_stability_verified_influence_conditional_no_model_change','warnings':warnings,'fit_calls':0,'new_bootstrap':0,'professional_independent_validation':False}
    journal={'author':'Codex','utc':NOW,'decisions':[{'hypothesis':p['hypothesis'],'criterion_before':p['OOF_influence'],'local_method_before':p['training_local_influence'],'sources':p['frozen_sources'],
        'result':summary,'verification':rel(run/'verification.json'),'consequence':'Preserve every group/model and B00. No new coefficients, prediction, fit or deletion adopted. Trace highlighted sources next; local approximation and posthoc sensitivity are not independent validation.'}]}
    for name,obj in [('assessment.json',assessment),('decision_journal.json',journal)]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    idx={'id':p['id'],'author':'Codex','utc':NOW,'path_base':'workspace_root','status':assessment['status'],'run':rel(run),'documentation':rel(docpath),'plan':rel(REPO/'registro/semana2_b19_estabilidad2023_plan_v1.json'),
        'b19_run':p['b19_run'],'audited_policy_years':[2023],'new_fits':0,'new_models':0,'new_bootstrap':0,'reference':'W2-B00','all_alternatives_preserved':True,
        'forum_prior':p['forum_prior'],'forum_result':'COD-S2-20261024-037','warnings':warnings,'ledger_read':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False}
    for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest']:
        path=run/(name+'.json');idx[name]={'path':rel(path),'sha256':sha(path)}
    (run/'index_proposed.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=f'''El diagnóstico registrado en 036 terminó sin reentrenamiento, nuevas recetas, cambios de T0/C0 o bootstrap, usando solo artefactos de 2023 de B19/B14. B00 y todas las alternativas se conservan. Informe: `{rel(docpath)}`. No se modifica el catálogo o contador activo de otras continuaciones.

Los coeficientes se comparan en escala original y con referencias categóricas comunes. En edificios, AD sí/no va de 0,795 a 1,388 y cambia dirección; en autos, third_party_only/comprehensive va de 0,567 a 0,857 y third_party_fire_theft es más estable (0,587–0,611). Los folds solapan y no forman cinco observaciones independientes.

Edificios tiene delta D² B19−B14 de −0,012743. Ninguna retirada individual de evaluación lo vuelve positivo. Sus cinco componentes más adversos son incendios, con 1.237.635,60 CU de T0 y {100*summary['building_top5_gross_adverse_fraction']:.1f}% de pérdidas brutas adversas. Retirar de evaluación 1/5/10/31 adversos deja deltas −0,009127/−0,002984/+0,000851/+0,006178; retirar favorables empeora el contraste. No se convierte esa selección a posteriori en limpieza o validación nueva.

Autos nuevos tiene delta −0,021777. Un componente de una fila con third_party_only, lesiones corporales y T0 136.767,16 CU aporta {100*summary['motor_top1_gross_adverse_fraction']:.1f}% de la pérdida bruta adversa. Su retirada de evaluación cambia el delta del segmento a +0,009766; el global del portafolio sigue negativo, −0,002430. El componente está ausente del ajuste0 que lo predice y presente en los otros cuatro: su error OOF no es su influencia sobre su propio ajuste.

La aproximación local del GLM H⁻¹G detecta influencia sobre cobertura/nuevo negocio en esos otros ajustes. En autos el cambio local del logcoeficiente de third_party_only va de −0,223 a −0,245; en edificios un incendio de 286.093 CU es el más influyente sobre AD en cuatro ajustes. No son modelos reentrenados: H completo y C0 fijo, grupos con leverage elevado y cambios grandes limitan la aproximación. No se predice o puntúa con coeficientes alterados y no se atribuye una diferencia de folds exclusivamente a un grupo.

Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones separadas y {sum(x['pass'] for x in checks)} conciliaciones focales, con solapamiento. Fit bloqueado, derivadas direccionales, Cholesky por otro método, cuentas por grupos y sklearn por filas cotejados. El flujo real rechaza T0 distinto entre modelos antes de Hessianos y conserva el fallo esperado. La guarda inicial detectó un cambio concurrente de continuidad; el intento no creó plan ni calculó nada y se concilió sin sobrescribir la otra unidad.

Siguiente paso: cotejar pagado, reservas, recuperaciones, estado y fechas de los componentes destacados, sin modificarlos ni reentrenar. No promover, retirar, fijar una lista final o borrar siniestros caros por estos diagnósticos exploratorios. 2024 sigue cerrado en este trabajo, también test, actas/predicciones/scores y ledger. Exposición previa de un título externo registrada, sin repetir o usar cifras ni afirmar ceguera completa. Revisión técnica propia, no profesional independiente o aprobación humana; sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones.
'''
    (ROOT/'Hackaton/Semana 2/Codex/estabilidad_b19_2023_resultado.md').write_text(body,encoding='utf-8')
    print(json.dumps({'documentation':rel(docpath),'reconciliations':sum(x['pass'] for x in checks),'failed':0,'building_top5_gross_adverse_fraction':summary['building_top5_gross_adverse_fraction'],'motor_top1_gross_adverse_fraction':summary['motor_top1_gross_adverse_fraction'],'max_derivative_error':summary['max_directional_derivative_error']}))

if __name__=='__main__':main()
