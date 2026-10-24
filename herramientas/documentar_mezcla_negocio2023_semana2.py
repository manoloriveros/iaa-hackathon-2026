"""Perfil de mezclas, cota de completitud e informe, sin ajustes o bootstrap nuevos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mix_document_reader',REPO/'herramientas/verificar_desarrollo2023_semana2.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;KEY=c.KEY;rel=lambda path:path.relative_to(ROOT).as_posix()
def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_snapshot.json');source=ROOT/p['input_run'];linkroot=ROOT/p['observation_run'];ver=sorted((run/'verifications').glob('mix_*.json'))[-1];fixtures=run/'fixture_checks.json'
assert c.read(ver)['failed']==c.read(fixtures)['failed']==0
new=pq.read_table(run/'mixture_oof_2023.parquet').to_pandas();old=pq.read_table(run/'base_oof_2023.parquet').to_pandas();claims=pq.read_table(run/'inputs_2023/claims_2023.parquet').to_pandas()
cells=[];tv_records=[];bounds=[];checks=[]
for fold in range(5):
    for line in ['motor','buildings','contents']:
        detail=c.read(run/f'mixtures/{line}_fold{fold}.json');perils=sorted(detail['pooled_shares_rebuilt'])
        for cell in detail['cell_estimates']:
            business=str(cell['business']);peril=cell['peril'];cells.append({**cell,'pooled_share':detail['pooled_shares_rebuilt'][peril],
              'MIXF_share':detail['business_shares']['MIXF'][business][peril],'MIXFS_share':detail['business_shares']['MIXFS'][business][peril]})
        frame=pq.read_table(source/f'variant_inputs/{line}_fold{fold}.parquet').to_pandas();valid=frame[frame.fold.eq(fold)].copy();qcols=['qC_1.0_'+peril for peril in perils]
        curves=pq.read_table(linkroot/f'exclude_fold{fold}/observation_link_{line}.parquet',filters=[('year','=',2023),('is_test','=',False)],columns=KEY+qcols).to_pandas();curves=valid[KEY].merge(curves,on=KEY,validate='one_to_one')
        spread=curves[qcols].max(axis=1).to_numpy()-curves[qcols].min(axis=1).to_numpy();basew=c.read(linkroot/f'exclude_fold{fold}/peril_cost_shares_{line}.json')['1.0']
        for variant in ['MIXF','MIXFS']:
            w0=detail['business_shares'][variant]['0'];w1=detail['business_shares'][variant]['1'];tv=.5*sum(abs(w0[x]-w1[x]) for x in perils);tv_records.append({'line':line,'fold':fold,'variant':variant,'TV_new_renewal':tv})
            q=new[new.variant.eq(variant)&new.model_id.eq('W2-B00')&new.line.eq(line)&new.fold.eq(fold)].set_index('row_id').loc[valid.row_id]
            tv_pool=np.asarray([.5*sum(abs(detail['business_shares'][variant][str(int(b))][x]-basew[x]) for x in perils) for b in valid.x_new_business])
            observed_q_diff=np.abs(q.effective_exposure.to_numpy()/valid.exposure.to_numpy()-valid['e_cost_mix_1.0'].to_numpy()/valid.exposure.to_numpy());bound=tv_pool*spread
            checks.append({'name':'Convex-mixture completion bound '+variant+line+str(fold),'pass':bool((observed_q_diff<=bound+1e-12).all())})
            b=valid[KEY+['year','fold','x_new_business']].copy();b['variant']=variant;b['TV_to_pooled']=tv_pool;b['peril_completion_spread']=spread;b['absolute_q_change']=observed_q_diff;b['bound']=bound;b['effective_exposure_ratio']=q.effective_exposure.to_numpy()/valid['e_cost_mix_1.0'].to_numpy();bounds.append(b)
cells=pd.DataFrame(cells);cells.to_parquet(run/'diagnostics/peril_business_cells.parquet',index=False);bounds=pd.concat(bounds,ignore_index=True);bounds.to_parquet(run/'diagnostics/mixture_completion_bound_2023.parquet',index=False)
checks.append({'name':'Complete single OOF bound pervariant', 'pass':bool(len(bounds)==2*50094 and not bounds.duplicated(['variant',*KEY]).any() and bounds.year.eq(2023).all())})
checks.append({'name':'Five zero fold cells describe one observed business/peril absence','pass':bool(len(cells[cells.claims.eq(0)])==5 and claims[claims.line.eq('buildings')&claims.x_new_business.eq(1)&claims.peril.eq('fire')].empty)})
recon={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'New interpretation and convex-mixture bound only; no refit/inference/bootstrap','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks};assert recon['failed']==0;dump(run/'readout_reconciliation.json',recon)
tv_summary=[];sparse=[];exposure_profile=[]
for (line,variant),sub in pd.DataFrame(tv_records).groupby(['line','variant']):tv_summary.append({'line':line,'variant':variant,'TV_min':float(sub.TV_new_renewal.min()),'TV_max':float(sub.TV_new_renewal.max())})
for (line,business),sub in cells.groupby(['line','business']):
    positive=sub[sub.claims.gt(0)];n=sub.groupby('fold').claims.sum();sparse.append({'line':line,'business':int(business),'training_claims_min':int(n.min()),'training_claims_max':int(n.max()),
      'minimum_positive_peril_ESS':float(positive.weighted_effective_sample_size.min()),'largest_single_weighted_cost_share':float(positive.largest_weighted_cost_share.max()),'zero_fold_cells':int(sub.claims.eq(0).sum())})
for (variant,line,business),sub in bounds.groupby(['variant','line','x_new_business']):exposure_profile.append({'variant':variant,'line':line,'business':int(business),'ratio_min':float(sub.effective_exposure_ratio.min()),
 'ratio_median':float(sub.effective_exposure_ratio.median()),'ratio_max':float(sub.effective_exposure_ratio.max()),'max_abs_q_change':float(sub.absolute_q_change.max()),'max_peril_spread':float(sub.peril_completion_spread.max())})
dump(run/'diagnostics/mixture_readout.json',{'tv_byline':tv_summary,'sparse_cells':sparse,'exposure_byline_business':exposure_profile,'positive_cell_count':int(cells.claims.gt(0).sum()),'zero_fold_cell_count':int(cells.claims.eq(0).sum()),
 'notice':'Cells repeat training observations across5folds. Zero building/newbusiness/fire is one observed absence, not5 independent findings. WeightedESS describes truncation-weight concentration, not a credible interval.'})
by={x['stress_id']:x for x in r['summary']};main=c.read(ROOT/p['main_model_index']);baseby={x['model_id']:x for x in main['summary']};table=[]
for mid in ['W2-B00','W2-B12','W2-B14']:
    for label,sid in [('Base',None),('MIXF','MIXF_'+mid),('MIXFS','MIXFS_'+mid)]:
        x=baseby[mid] if sid is None else by[sid];nom=float((old.loc[old.model_id.eq(mid),'exposure']*old.loc[old.model_id.eq(mid),'annual_rate']).sum()) if sid is None else x['conditional_nominal_2023'];change=0. if sid is None else x['nominal_relative_change']
        table.append(f"| {mid.replace('W2-','')} | {label} | {x['D2']:.8f} | {x['actual_over_expected']:.3f} | {nom/1e6:.6f} | {change:+.3%} |")
table='\n'.join(table);tvtab='\n'.join(f"| {x['line']} | {x['variant']} | {x['TV_min']:.2%}–{x['TV_max']:.2%} |" for x in tv_summary)
sparsetab='\n'.join(f"| {x['line']} | {'Nuevo' if x['business'] else 'Renovación'} | {x['training_claims_min']}–{x['training_claims_max']} | {x['minimum_positive_peril_ESS']:.2f} | {x['largest_single_weighted_cost_share']:.1%} | {x['zero_fold_cells']} |" for x in sparse)
mixrows=[]
for (line,peril),sub in cells.groupby(['line','peril']):
    a=sub[sub.business.eq(0)];b=sub[sub.business.eq(1)];mixrows.append(f"| {line} | {peril} | {sub.pooled_share.mean():.1%} | {a.MIXF_share.mean():.1%} | {b.MIXF_share.mean():.1%} | {a.MIXFS_share.mean():.1%} | {b.MIXFS_share.mean():.1%} | {b.claims.min()}–{b.claims.max()} |")
mixrows='\n'.join(mixrows);pairs=c.read(run/'diagnostics/pairs.json')['pairs'];pt='\n'.join(f"| {x['candidate']}/{x['reference']} | {x['delta_D2']:+.8f} | [{x['exploratory_lower95']:+.8f}; {x['exploratory_upper95']:+.8f}] | {x['delta_after_removal']:+.8f} |" for x in pairs)
warnings=[{'id':'MIX-SPARSE','status':'open','effect':'Business/peril positive severity has small weighted effective samples and concentrated costs. Five zerofoldcells represent one observed absence of newbusiness buildingfire, not no future risk.'},
 {'id':'MIX-REPRO-NOT-GAIN','status':'open','effect':'All MIXF pointD2 belowownbase; all MIXFS belowMIXF. No adopted business mixture, selected smoothing, equivalence or promotion.'},
 {'id':'MIX-COMPLETION','status':'open','effect':'Differences in mixture shares can have little impact when peril cost-completion curves are similar. Verified TV*spread bound only2023; not2025 or ultimate accuracy.'},
 {'id':'MIX-POOLED-CURVES','status':'open','effect':'Count/cost timing and truncation weights remain pooledbyperil; no business-specific curve, independent cost-report timing proof or individual coverage masks.'},
 {'id':'MIX-SEARCH','status':'open','effect':'Six further observation-stress configurations and12new unadjusted conditional bootstrap contrasts after adaptive research. Fixedfit OOF intervals omit first-stage parameter-refit uncertainty.'},
 {'id':'MIX-2024-CLOSED','status':'open','effect':'Direct participant instruction. MainB00 and19catalog retained; no2024/test prices/predictions/scores or ledger.'}]
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'business_peril_mixture_sensitivity_verified_no_point_gain_conditions_open','warnings':warnings,'reference':'W2-B00','promotion':False,'professional_independent_validation':False};dump(run/'assessment.json',assessment)
dump(run/'decision_journal.json',{'author':'Codex','utc':assessment['utc'],'preregistration':'COD-S2-20261024-027','decisions':[
 {'topic':'business mixture','decision':'Keep pooledC0 as original reference. Do not adopt MIXF/MIXFS because formulas reproduce or mixture weights differ; both publish adverse point results.'},
 {'topic':'zero/sparse cells','decision':'Frequency0 and absentseverity are observed estimator boundaries, not nofuture risk; no severity fabricated or strength tuned after scores.'},
 {'topic':'reproduction','decision':'Pooled control reconstructs original n/E*weightedmean. It does not assert that arbitrarily aggregating business weights reproduces the old mixture.'},
 {'topic':'pricelevel','decision':'Only normalized perilweights enter exposure. No extra total frequency/severity price multiplier; native standard price recipes unchanged.'},
 {'topic':'completion bound','decision':'Use TV*curve-spread to explain small exposure sensitivity with changed mix; no generalization to future business or ultimate truth.'},
 {'topic':'nextunit','decision':'Prepare an interim night balance of identified versus conditional mechanisms; prioritize reporting/calendar support and sparse-cell adequacy before any business-specific curve or more complex price. Preregister new work, keep2024 closed.'}],
 'warnings':warnings,'verification':rel(ver),'fixtures':rel(fixtures),'readout_reconciliation':rel(run/'readout_reconciliation.json'),'professional_independent_validation':False})
doc=REPO/'docs/semana2/MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md'
text=f'''# Mezcla de C0 por peril y tipo de negocio

Codex. Corte UTC {r['completed_utc']}. La composición por peril cambia entre negocio nuevo y renovación, pero ninguna de las dos mezclas nuevas mejora el D² puntual de su modelo de referencia. Separar también la severidad empeora los tres puntos frente a separar solo la frecuencia. No se adopta una mezcla nueva ni se elige una contracción después de ver resultados.

## Contraste registrado

El [plan](../../registro/semana2_c0_mezcla_negocio2023_plan_v1.json) y el comentario COD-S2-20261024-027 preceden al ajuste. Se conserva T0, los 50.094 periodos de 2023, 30.869 componentes y cinco folds. Los modelos de precio siguen siendo B00 constante por ramo, B12 constante por ramo y negocio, y B14 GLM de seis variables, log, Tweedie1,5 y alpha0. El objetivo es T0/e_mix con peso sqrt(e_mix), y la predicción observada e_mix×tasa. Capital, clima, credibilidad y calibración no cambian.

MIXF estima dentro del ajuste de cada ramo/fold una frecuencia Poisson constante por peril y negocio: lambda_pb=n_pb/suma(exposición×qN_p). Conserva la severidad media pooled del peril. Los pesos normalizan lambda_pb×mu_p. MIXFS mantiene esas frecuencias y sustituye la severidad por la media Gamma positiva ponderada por los pesos de truncamiento del propio fold: mu_pb=suma(w_i·T0_i)/suma(w_i). Se estiman una vez y se comparten entre variantes. Las curvas qN_p y qC_p siguen siendo las originales por peril.

Solo entran pesos de mezcla normalizados. El total frecuencia×severidad no se añade como multiplicador al precio. Se reconstruye como control el C0 original a partir de conteos, exposición y severidad pooled originales. Esto no implica que una agregación arbitraria de las nuevas medias por negocio deba devolver la mezcla original: las ponderaciones de frecuencia y severidad son distintas. No se usa ningún coste del retenido para estimar pesos.

Si n_pb=0, la frecuencia estimada está en la frontera cero y su peso es cero; la severidad queda sin estimar. No significa ausencia futura de riesgo. Una celda positiva con masa de ponderación inválida habría detenido la prueba, sin fallback con validación. No ocurrió. No se añadieron priors, curvas por negocio, máscaras individuales de cobertura o intensidad de suavizado elegida por score.

## Qué cambia en la composición

La distancia de variación total es la mitad de la suma de diferencias absolutas entre los pesos nuevos y de renovación. Una distancia de 20% significa que habría que redistribuir al menos ese peso para igualar ambas mezclas. Los rangos siguientes recorren cinco ajustes que comparten muchos siniestros; no son cinco observaciones independientes.

| Ramo | Variante | Distancia entre mezcla nueva y renovación, rango entre folds |
| --- | --- | ---: |
{tvtab}

Promedios de pesos entre los cinco ajustes, con conteos nuevos por peril dentro de cada ajuste:

| Ramo | Peril | Pooled | MIXF renovación | MIXF nuevo | MIXFS renovación | MIXFS nuevo | Siniestros nuevos por ajuste |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{mixrows}

La ausencia de incendio en edificios nuevos de 2023 se repite como cinco celdas de ajuste con cero, una por fold. Es una ausencia observada en esa misma población, no cinco hallazgos independientes. Los pesos cero que produce el estimador no permiten concluir que ese negocio no tendrá incendios.

## Escasez y concentración

El tamaño efectivo de ponderación es (suma w)²/suma(w²). Describe concentración de pesos de truncamiento, no un intervalo de credibilidad o cantidad de siniestros independientes. La última proporción mide cuánto del coste ponderado de una celda positiva aporta su siniestro más grande.

| Ramo | Negocio | Siniestros de ajuste entre folds, todos los perils | Mínimo tamaño efectivo de celda positiva | Mayor peso de un siniestro en el coste de una celda | Celdas cero entre folds |
| --- | --- | ---: | ---: | ---: | ---: |
{sparsetab}

Los grupos y siniestros concretos quedan privados. No se usa esa concentración para quitar costes, elegir pesos o fijar una contracción a posteriori. La escasez limita la interpretación de MIXFS aunque su promedio Gamma esté correctamente calculado.

## Por qué una mezcla distinta puede mover poco C0

Si las curvas de completitud de los perils son parecidas, cambiar sus pesos tiene poca repercusión. Para cada fila se verificó la cota |q_mix−q_base| <= TV(w_mix,w_base)×(máximo qC_p−mínimo qC_p), usando su propio fold y tipo de negocio. Es una propiedad de mezclas convexas. Las {len(bounds):,} filas variante/periodo, dos por cada periodo OOF de 2023, satisfacen la cota con tolerancia1e-12.

La cota explica una sensibilidad pequeña de exposición aun con pesos distintos; no prueba que los pesos sean verdaderos, que la curva compartida sirva para ambos negocios o que 2025 tenga el mismo soporte de maduración. Los perfiles de exposición por ramo y negocio quedan en el anexo.

## Resultado de los modelos estándar

| Modelo | Enlace | D² global | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: |
{table}

En B14, MIXF mueve el nominal condicionado +0,0166% y MIXFS +0,1016%. El nominal es exposición nominal de los mismos periodos de 2023 por su tasa bajo coste completo, no una predicción de 2025/test o una etiqueta última. Un movimiento pequeño del total no implica estabilidad individual ni valida las ponderaciones de negocio.

La [prueba de cola](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) y la [sensibilidad de reservas/reportes](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) conservan sus resultados y sus condiciones. No se repitieron sus modelos o remuestreos, ni se combinaron sus efectos con esta prueba.

## Incertidumbre exploratoria

Solo se añadieron doce contrastes con 2.000 sorteos comunes de componentes: tres comparaciones entre familias dentro de cada variante, MIXF frente a cada padre original y MIXFS frente a MIXF. Todo usa el mismo T0 y las mismas filas. Los intervalos condicionan en los ajustes guardados, incluidos los pesos de la primera etapa; no reestiman su incertidumbre ni corrigen la búsqueda adaptativa.

| Contraste | Delta D² | Intervalo exploratorio95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
{pt}

Los tres puntos MIXF son menores que sus bases y los tres MIXFS menores que MIXF. No se promueve, retira o declara equivalente una alternativa por estas cifras. El catálogo principal de 19 recetas conserva su C0 y su corte; estas seis configuraciones son sensibilidad de observación, no candidatos nuevos bajo un enlace común congelado.

## Verificación y decisiones

Se completaron {r['new_price_GLM_fits']} GLM y {r['new_closed_form_constants']} constantes de precio nuevos, sin reintento o cambio de receta. Aparte se estimaron {r['new_mixture_frequency_constants']} constantes Poisson de mezcla y {r['new_mixture_weighted_severity_means']} medias Gamma ponderadas positivas. Las cinco medias no estimadas corresponden a las cinco celdas cero. No hubo nuevas curvas de reporte o auxiliares de credibilidad. El contador propio de precios queda en {r['cumulative_price_base_fits']} ajustes y {r['cumulative_closed_form_constants']} constantes; los estimadores de mezcla y los 30 auxiliares anteriores se registran por separado.

Pasaron {c.read(ver)['passed']} controles separados, {c.read(fixtures)['passed']} adversos y {recon['passed']} comprobaciones adicionales de interpretación, con solapamiento. El comprobador no importa el productor y bloquea fit. Reconstruye pesos de truncamiento, exposición y óptimos Poisson/Gamma por minimización numérica, medias y concentración, C0 pooled y pesos por negocio, óptimos de precio, parámetros/gradientes, imputación del ajuste y exp(X beta). Verifica ámbitos, métricas/segmentos y doce remuestreos por multiplicidades. Los adversos prueban invariancia a escala total, escala de pesos y orden, costes del retenido sin efecto, celdas cero explícitas y rechazo de 2024/test, negocio inválido, claims del retenido, duplicados, curvas desordenadas y masa nula. Las recomputaciones aritméticas de esos adversos no son nuevos modelos o evidencia independiente.

Se conserva C0 pooled como referencia, sin adoptar MIXF/MIXFS, fabricar severidades o ajustar una intensidad de suavizado por score. Sigue condicionada la curva de reporte/coste compartida, la dependencia coste/retraso por negocio, la exposición individual a cada cobertura y la masa no observada. La validación agrupada de 2023 al corte 2024-12-31 no representa información disponible al inicio de 2023. Se mantienen las condiciones de capital, clima, reservas y prior, y los responsables de hallazgos ajenos.

La siguiente unidad preparará un balance de mecanismos identificados y condicionados; antes de ajustar curvas por negocio o precios más complejos revisará soporte temporal y adecuación de celdas, con receta previa para nuevos ensayos. B00 y todas las alternativas permanecen intactos. 2024 sigue cerrado expresamente, ledger ausente, sin precios, predicciones o scores de ese año o test. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Revisión técnica propia de Codex, no profesional independiente.

## Evidencia

- [Resultados](../../{run.relative_to(REPO).as_posix()}/report.json), [decisiones](../../{run.relative_to(REPO).as_posix()}/decision_journal.json).
- [Comprobador separado](../../{ver.relative_to(REPO).as_posix()}), [adversos](../../{run.relative_to(REPO).as_posix()}/fixture_checks.json).
- [Perfil de mezcla, escasez y exposición](../../{run.relative_to(REPO).as_posix()}/diagnostics/mixture_readout.json), [celdas privadas](../../{run.relative_to(REPO).as_posix()}/diagnostics/peril_business_cells.parquet).
- [Foro](../../../Semana%202/Foro/FORO.md), comentarios 027–028.
'''
with doc.open('x',encoding='utf-8') as f:f.write(text)
body=f'''Codex. Resultado de 027: [mezcla de C0 por peril y negocio](../../Repositorio_IAA2026/docs/semana2/MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md), [decisiones](../../Repositorio_IAA2026/{run.relative_to(REPO).as_posix()}/decision_journal.json). Solo 2023, mismos folds/T0 y modelos estándar; B00 y el catálogo principal intactos, 2024 cerrado.

MIXF cambia por negocio solo las frecuencias Poisson por peril; MIXFS cambia también las medias Gamma positivas ponderadas. Las curvas qN/qC y los pesos de truncamiento se conservan por peril del propio ajuste. Solo se usan los pesos normalizados, nunca un multiplicador extra de frecuencia×severidad en el precio. El control pooled reproduce el C0 original; no presupone que cualquier agregado de las nuevas medias por negocio deba devolverlo.

| Modelo | Enlace | D² global | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: |
{table}

Los tres puntos MIXF son peores que sus bases y los tres MIXFS peores que MIXF. En B14 el nominal condicionado mueve +0,0166%/+0,1016%, sin acreditar mejora. Son los mismos periodos de 2023 por tasa bajo coste completo, no precios2025/test o etiquetas últimas. La mezcla difiere por negocio, pero eso no valida una sustitución de C0 o precio.

Hay cinco celdas de ajuste con frecuencia cero: todas son incendio en edificios nuevos, una por fold, reflejo de una sola ausencia observada en 2023. No son cinco hallazgos independientes ni ausencia futura de riesgo. No se fabricó su severidad. El informe conserva conteos, tamaño efectivo y concentración para las otras145celdas positivas, sin eliminar costes o escoger una intensidad de contracción después de ver scores.

Una mezcla distinta puede afectar poco a C0 si las curvas por peril son parecidas. Se verificó por fila la cota |delta q| <= TV(pesos)×rango(qC_peril) en los100.188registros variante/periodo de2023. Es una identidad de mezclas convexas, no validación de la composición futura o del último.

Doce contrastes nuevos y2.000sorteos comunes, con influencia propia de31grupos; cifras completas en el informe. Los intervalos son exploratorios condicionados en los ajustes guardados y no propagan el refit de pesos de primera etapa. No se repiten las pruebas de cola/reservas o sus remuestreos. Sin promoción, retiro, equivalencia o lista final.

Se completaron30GLM/90constantes de precio nuevos; contador propio165ajustes/285constantes. Aparte150constantes Poisson de mezcla y145medias Gamma ponderadas; cero curvas de reporte/auxiliares de credibilidad nuevos. Pasaron1.570controles separados,47adversos y32comprobaciones adicionales, solapados. Reconstrucción de pesos y óptimos Poisson/Gamma, normalización, C0, gradientes, exp(Xbeta), ámbitos, segmentos y12bootstrap por multiplicidades; fit bloqueado. Sin reintento o cambio de receta. Revisión técnica propia, no profesional independiente.

Decisión: conservar el C0 pooled, MIXF/MIXFS como sensibilidades y todas las alternativas. Permanecen las condiciones de escasez, curvas compartidas, dependencia coste/reporte, cobertura individual, cola/reservas y disponibilidad temporal. Siguiente unidad: balance de mecanismos identificados/condicionados y revisión de soporte temporal/celdas antes de complejizar, con receta previa. B00 intacto, 2024/test cerrados y ledger ausente; sin remoto, envíos, publicación externa, nuevos chats o delegación. La programación y otras automatizaciones se preservan.
'''
with (ROOT/'Hackaton/Semana 2/Codex/mezcla_negocio2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
index={'id':p['id'],'author':'Codex','as_of_utc':assessment['utc'],'path_base':'workspace_root','status':assessment['status'],'run':rel(run),'documentation':rel(doc),
 'main_model_index_preserved':p['main_model_index'],'main_model_index_sha256':p['main_model_index_sha256'],'prior_sensitivity_index_snapshot':'Hackaton/Repositorio_IAA2026/registro/semana2_sensibilidad_observacion_c0_reservas_v1_snapshot.json','prior_sensitivity_index_sha256':p['prior_sensitivity_index_sha256'],
 'training_years':[2023],'scored_years':[2023],'rows_per_stress':50094,'groups':30869,'folds':5,'new_price_GLM_fits':r['new_price_GLM_fits'],'new_closed_form_constants':r['new_closed_form_constants'],
 'new_mixture_frequency_constants':r['new_mixture_frequency_constants'],'new_mixture_weighted_severity_means':r['new_mixture_weighted_severity_means'],'new_reporting_curve_fits':0,'new_auxiliary_fits':0,
 'cumulative_price_base_fits':r['cumulative_price_base_fits'],'cumulative_closed_form_constants':r['cumulative_closed_form_constants'],'prior_auxiliary_fits_not_recounted':30,
 'stress_configurations':[x['stress_id'] for x in r['summary']],'summary':r['summary'],'new_exploratory_pairs':12,'main_catalog_candidates':19,'main_catalog_pairs_preserved':171,
 'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'confirmation_2024_open':False,'test_predictions':0,'professional_independent_validation':False,
 'forum_prior':['COD-S2-20261024-027'],'forum_result':'COD-S2-20261024-028','warnings':warnings}
for key,path in [('report',run/'report.json'),('plan',REPO/'registro/semana2_c0_mezcla_negocio2023_plan_v1.json'),('producer',ROOT/p['code']),('oof',run/'mixture_oof_2023.parquet'),('manifest',run/'manifest.json'),('assessment',run/'assessment.json'),('decision_journal',run/'decision_journal.json')]:index[key]=rel(path);index[key+'_sha256']=c.sha(path)
for key,path in [('verification',ver),('fixtures',fixtures),('readout_reconciliation',run/'readout_reconciliation.json')]:index[key]={'path':rel(path),'sha256':c.sha(path),'passed':c.read(path)['passed'],'failed':0}
dump(run/'sensitivity_index_proposed.json',index);print(json.dumps({'documentation':rel(doc),'tv':tv_summary,'sparse':sparse,'readout_checks':recon['passed'],'exposure':exposure_profile}))
