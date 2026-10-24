"""Balance, conciliación incremental y documentación de la séptima tanda."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,copy
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v7_document_oracle',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_snapshot.json');parent=ROOT/p['parent_run']
    oldidx=c.read(REPO/'registro/semana2_desarrollo2023_actual.json');assert oldidx['id']=='S2-DEV2023-v6-20261023'
    ver=sorted((run/'verifications').glob('v7_*.json'))[-1];fixtures=run/'fixture_checks.json';assert c.read(ver)['failed']==c.read(fixtures)['failed']==0
    dr=c.read(ROOT/p['diagnostic_review']);cap=pq.read_table((ROOT/p['diagnostic_review']).parent/'capital_56_rows.parquet').to_pandas()
    mids=['W2-B00','W2-B14','W2-B15','W2-B16','W2-B17','W2-B18'];oof=pq.read_table(run/'oof_2023.parquet',filters=[('model_id','in',mids)]).to_pandas();K=c.KEY
    cells={m:f[f.line.eq('motor')&f.x_new_business.eq(1)].sort_values(K).reset_index(drop=True) for m,f in oof.groupby('model_id')};baseline=cells['W2-B14'];motor=[];folds=[];outcome=[];check=[]
    for mid,q in cells.items():
        assert q[K].equals(baseline[K]);dev=c.dev(q.T0,q.prediction);harm=dev-c.dev(baseline.T0,baseline.prediction)
        d2=c.d2_tweedie_score(q.T0,q.prediction,power=1.5);n=q.T0.mean();den=c.dev(q.T0,np.full(len(q),n)).sum()
        check.append({'name':'Motor score and loss identity '+mid,'pass':bool(np.allclose(d2,1-dev.sum()/den) and np.allclose(dev,q.unit_deviance))})
        groups=pd.DataFrame({'group_id':q.group_id,'harm':harm}).groupby('group_id').harm.sum().sort_values(ascending=False)
        motor.append({'model_id':mid,'rows':len(q),'positive_rows':int(q.T0.gt(0).sum()),'D2':float(d2),'observed':float(q.T0.sum()),'predicted':float(q.prediction.sum()),
          'AE':float(q.T0.sum()/q.prediction.sum()),'harm_vs_B14':float(harm.sum()),'top5_harm_vs_B14':float(groups.head(5).sum()),'top31_harm_vs_B14':float(groups.head(31).sum())})
        partitions=[]
        for dim,labels in [('fold',q.fold.astype(str)),('outcome',np.where(q.T0.gt(0),'positive','zero'))]:
            records=[]
            for label in sorted(set(labels)):
                sel=np.asarray(labels)==label;cell=q.loc[sel];records.append({'model_id':mid,'dimension':dim,'label':str(label),'rows':int(sel.sum()),
                  'observed':float(cell.T0.sum()),'predicted':float(cell.prediction.sum()),'D2':float(c.d2_tweedie_score(cell.T0,cell.prediction,power=1.5)) if cell.T0.gt(0).any() else None,
                  'loss':float(dev[sel].sum()),'harm_vs_B14':float(harm[sel].sum())})
            (folds if dim=='fold' else outcome).extend(records);partitions.append(records)
            check.append({'name':'Partition reconciliation '+mid+dim,'pass':bool(sum(x['rows'] for x in records)==len(q) and np.allclose(sum(x['harm_vs_B14'] for x in records),harm.sum()))})
    recon={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'Incremental motor-new readout from frozen OOF, external D2/general deviance formula; no new inference or fit',
      'passed':sum(x['pass'] for x in check),'failed':sum(not x['pass'] for x in check),'checks':check,'professional_independent_validation':False}
    assert recon['failed']==0;dump(run/'diagnostics/motor_new_components.json',{'summary':motor,'folds':folds,'outcome':outcome});dump(run/'motor_reconciliation.json',recon)
    by={x['model_id']:x for x in r['summary']};bm={x['model_id']:x for x in motor}
    rows='\n'.join(f"| {m.replace('W2-','')} | {by[m]['D2']:.6f} | {by[m]['actual_over_expected']:.3f} | {bm[m]['D2']:.6f} | {bm[m]['AE']:.3f} | {bm[m]['predicted']/1e6:.3f} |" for m in mids)
    contrasts=[x for x in r['pairs'] if x['candidate'] in mids[-3:] and x['reference']=='W2-B14']
    pt='\n'.join(f"| {x['candidate'].replace('W2-','')}/B14 | {x['delta_D2']:+.8f} | [{x['exploratory_lower95']:+.8f}; {x['exploratory_upper95']:+.8f}] | {x['delta_after_removal']:+.8f} |" for x in contrasts)
    ctab=[]
    for line,g in cap.groupby('line'):
        f=[z for z in dr['capital_folds'] if z['line']==line]
        ctab.append(f"| {line} | {len(g)} | {g.capital_divided.min():,.0f}–{g.capital_divided.max():,.0f} | {min(np.exp(z['old_training_imputation_log']) for z in f):,.0f}–{max(np.exp(z['old_training_imputation_log']) for z in f):,.0f} | {g.total_relative_change.min():+.2%} a {g.total_relative_change.max():+.2%} | {g.refit_log_effect.abs().max():.5f} |")
    ctab='\n'.join(ctab)
    folds_tab='\n'.join(f"| {z['fold']} | {z['theta_price']:.3f} | {z['theta_auxiliary_total']:.3f} | {z['theta_credible']:.3f} | {z['c_frequency']:.3f} | {z['c_severity']:.3f} | {z['replacement_c_diagnostic_only_not_scored']:.3f} |" for z in dr['motor_credibility_decomposition'])
    harm_tab='\n'.join(f"| {m.replace('W2-','')} | {next(x['harm_vs_B14'] for x in outcome if x['model_id']==m and x['label']=='positive'):,.2f} | {next(x['harm_vs_B14'] for x in outcome if x['model_id']==m and x['label']=='zero'):,.2f} | {bm[m]['harm_vs_B14']:,.2f} |" for m in mids[2:])
    warnings=[{'id':'DEV7-CAPITAL-UNIT','status':'open','effect':'56 corrected2023 records have no positive T0. Values within training support and formula replay cannot confirm economic scale; B13/B14 and private row detail retained.'},
      {'id':'DEV7-MOTOR-CRED','status':'open','effect':'All3 prespecified motor-only corrections worsen point D2 againstB14; CIs include0. No choice of weight or substitution established; keep B15 and ablations without promotion.'},
      {'id':'DEV7-PRIOR-OBJECTIVE','status':'open','effect':'Received developed2021-2023 prior/seasonality not raw-reproduced here; prior uncertainty omitted in Z; tau uses correlated effects. Auxiliary count/severity and price Tweedie objectives/observation differ.'},
      {'id':'DEV7-SEARCH','status':'open','effect':'19 adaptive recipes,171 unadjusted exploratory contrasts; no temporal confirmation, equivalence or final roster.'},
      {'id':'DEV7-ULTIMATE','status':'open','effect':'Reporting, late-cost and reserves remain conditional; fixed-rate stresses are not full refits or final2025 ultimate validation.'},
      {'id':'DEV7-2024-CLOSED','status':'open','effect':'Explicit participant instruction: keep2024/test unpriced, unpredicted and unscored, ledger absent.'}]
    assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'verified_technical_exploration_conditions_open','reference':'W2-B00','promotion':False,'warnings':warnings,'professional_independent_validation':False}
    dump(run/'assessment.json',assessment);dump(run/'decision_journal.json',{'author':'Codex','utc':assessment['utc'],'preregistration':p['forum_preregistration'],'decisions':[
      {'topic':'capital','decision':'No score-driven adjustment. Keep56-row evidence and both B13/B14, economic unit condition open.'},
      {'topic':'motor credibility','decision':'No automatic adoption of frequency-only, severity-only or coefficient replacement; no optimized fourth blend. Preserve B15/B16/B17/B18 and B14.'},
      {'topic':'standard models','decision':'Zero new fits; frozen GLM main effects and existing Poisson/Gamma suffice to diagnose this question. No reason established to add a complex learner.'},
      {'topic':'next work','decision':'Next unit may review common C0/late-report/reserve and level/tail sensitivity only2023; preregister before any new fit. Do not tune c on these scores.'},
      {'topic':'scope','decision':'B00 retained;2024 closed by participant irrespective of selector technical state. No roster, submissions, remote, delegation or external messages.'}],
      'warnings':warnings,'verification':rel(ver),'fixtures':rel(fixtures),'incremental_reconciliation':rel(run/'motor_reconciliation.json'),'professional_independent_validation':False})
    doc=REPO/'docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md'
    text=f'''# Capital por fila y credibilidad en autos nuevos

Codex. Corte UTC {r['completed_utc']}. La prueba registrada antes de calcular sus scores conserva los modelos estándar. Las tres correcciones nuevas empeoran el D² puntual de autos nuevos frente a B14. Los intervalos globales cruzan cero: esta tanda no establece superioridad, equivalencia o descarte. B00 sigue como referencia y 2024 permanece cerrado.

## Qué explica los cambios de capital

Se guardaron las 56 filas de 2023, sus valores bruto, dividido e imputado, el fold y el efecto separado de representación y reajuste. Para cada fila se volvió a predecir con B13 congelado, sustituyendo únicamente logcapital. El cociente satisface log(r_corregida/r_imputada)=beta_capital·(logcapital_corregido−mediana_del_ajuste). La discrepancia máxima de esta identidad es {dr['capital_formula_error_max']:.2e}. El reajuste B14 se mide después, con log(r_B14/r_B13_corregido). No se mezcla esa explicación con una nueva receta de precio.

| Ramo | Filas | Capital dividido, CU | Capital imputado previo según fold, CU | Cambio final de tasa | Mayor efecto absoluto del reajuste, log |
| --- | ---: | ---: | ---: | ---: | ---: |
{ctab}

Los valores corregidos quedan dentro del rango normal de ajuste de cada fold; no son extrapolación univariante de capital. Eso tampoco garantiza soporte conjunto de las otras variables. El reajuste mueve como máximo 0,157%/0,272% en escala log, mientras la sustitución de un capital desconocido por uno propio explica los cambios grandes y su signo. No se debe interpretar como estabilidad de precio por póliza que el efecto agregado sea pequeño.

Las 56 filas tienen T0=0. El score premia una menor predicción en esas observaciones y no permite confirmar la moneda/unidad o severidad económica. Se conserva la decisión CAPS2-01 y su procedencia como hipótesis condicionada; no se retocan los capitales para mejorar ese score. B13, B14 y el F0 original permanecen guardados. Prima escrita solo audita escala; no es predictor. El detalle con identificadores queda privado.

## Dónde empeoró la credibilidad original

En los 2.620 autos nuevos hay 265 filas con coste positivo y 2.355 con coste cero. B15 reduce el predicho de 1,238 a 0,890 millones CU frente a 1,088 millones observados. La pérdida aumenta 34.727,49 en las positivas y baja 27.119,35 en las cero: saldo adverso 7.608,15. El fold 0 aporta 8.637,79, compensado parcialmente en otros folds. Los cinco grupos más perjudicados suman 18.085,65; esta cifra supera el saldo porque existen compensaciones. No son cinco grupos que expliquen una fracción acotada de la pérdida ni una regla para excluirlos.

El corrector original c=c_f·c_s reduce poco por frecuencia y mucho por severidad. La severidad recibe casi todo el peso del prior. La aplicación directa de c sobre B14 desplaza su coeficiente de negocio, pero no lo sustituye por el coeficiente creíble: el efecto bruto del GLM de precio ya es mayor que la suma de los efectos auxiliares. La estandarización de la variable binaria se deshace al comparar coeficientes. Esa diferencia entre objetivos y ajustes no demuestra un error de programación o causa única del deterioro.

| Fold | Theta precio | Theta auxiliares | Theta creíble | c frecuencia | c severidad | c sustitución |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{folds_tab}

## Prueba registrada y resultado

El [plan v7](../../registro/semana2_desarrollo2023_plan_v7.json) y el comentario {p['forum_preregistration']} preceden a las nuevas predicciones. B16 aplica solo c_f a autos nuevos; B17 solo c_s; B18 aplica exp(theta_creíble−theta_precio), sustituyendo el coeficiente bruto de negocio con intercepto y demás efectos congelados. Todas parten de B14 y conservan hogar y renovaciones exactamente. B15 sigue como comparación completa, pero su hogar también cambia; su comparación global con estas ablaciones no aísla únicamente autos.

Se usan los 50.094 periodos de 2023, los 30.869 componentes cliente-dirección y cinco folds guardados. T0, C0 y variables técnicas siguen idénticos. Cero nuevos ajustes de precio, auxiliares o calibración; se reutilizan las treinta estimaciones Poisson/Gamma v6 y se calculan quince factores algebraicos de autos. Treinta archivos nativos de hogar son copias exactas. Ningún factor consulta costes del retenido. No se usa un c estimado en todo 2023 o calibración ordinaria con OOF de otros folds.

| Receta | D² global | A/E global | D² autos nuevos | A/E autos nuevos | Predicho autos nuevos, millones CU |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

| Comparación global | Delta D² | Intervalo exploratorio 95% | Delta retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
{pt}

Las tres correcciones nuevas tienen puntos negativos frente a B14; ninguna acredita mejora. La sustitución explícita empeora más, aunque su intervalo global también cruza cero. La diferencia de coeficientes detectada no queda resuelta como explicación causal ni como arreglo de desempeño. No se elige un cuarto peso a partir de esta lectura.

| Corrección | Aumento pérdida positivas | Aumento pérdida ceros | Saldo adverso frente a B14 |
| --- | ---: | ---: | ---: |
{harm_tab}

Las pérdidas de frecuencia y severidad no son aditivas al multiplicar factores sobre una devianza no lineal. La tabla sirve para localizar consecuencias, no para sumar efectos causales. Se conservan las 16 OOF previas y sus 120 parejas exactamente. Solo se añadieron 51 parejas y sus 2.000 réplicas con el mismo flujo aleatorio. Tras 19 recetas adaptativas hay 171 comparaciones exploratorias sin corrección por búsqueda o multiplicidad. No se abre la confirmación temporal ni se congela una lista final.

## Comprobaciones y límites vigentes

Pasaron {c.read(fixtures)['passed']} adversos focales, {c.read(ver)['passed']} controles del comprobador separado y {recon['passed']} conciliaciones adicionales de esta lectura. Los recuentos se solapan y no equivalen a experimentos independientes. El comprobador no importa el productor, bloquea fit y reconstruye la predicción como exp(X beta+intercepto), las métricas con fórmula general/API externa y el bootstrap mediante multiplicidades de grupos y productos matriciales. Verifica las 51 parejas nuevas, influencia, factores, coeficiente bruto, copias nativas, ámbitos, invariancia de renovaciones y la identidad de capital de las 56 filas. Los adversos prueban escalas equivalentes, envenenamiento de costes/identificadores sin cambio de precio y rechazo de 2024, test, duplicados, ramo/fold incorrecto o negocio inválido.

El prior desarrollado 2021–2023 y su estacionalidad siguen como artefactos recibidos de Claude, sin reproducción desde raw en esta tanda. Su incertidumbre se omite en Z; tau usa efectos correlacionados. Una validación por grupos de 2023 con ese prior no es un backtest prospectivo al inicio de 2023. Los escenarios de reservas y reportes tardíos se recalculan a tasa fija, sin reajustar C0 o demostrar el último de 2025. El clima propuesto sigue fuera del contrato prospectivo por dependencia futura. Es revisión técnica propia de Codex, no revisión profesional independiente.

Se mantienen B00 y B01–B18, sin promoción o retiro. Continúa la programación nocturna existente; una próxima prueba de nivel/cola y vínculo de observación necesitará receta previa solo en 2023. No se ajustará c a estos resultados. 2024 queda cerrado por instrucción expresa, con ledger ausente, sin precios/predicciones/scores de ese año o test. No hubo envíos, entrenamiento remoto, publicación externa o delegación.

## Evidencia reproducible

- [Resultados y contadores](../../{run.relative_to(REPO).as_posix()}/report.json).
- [Decisiones y condiciones](../../{run.relative_to(REPO).as_posix()}/decision_journal.json).
- [Revisión de predicciones y estadística](../../{ver.relative_to(REPO).as_posix()}).
- [Capital por fila privado](../../{(ROOT/p['diagnostic_review']).parent.relative_to(REPO).as_posix()}/capital_56_rows.parquet).
- [Desglose de autos nuevos](../../{run.relative_to(REPO).as_posix()}/diagnostics/motor_new_components.json).
- [Foro con registro previo y resultados](../../../Semana%202/Foro/FORO.md).
'''
    with doc.open('x',encoding='utf-8') as f:f.write(text)
    body=f'''Codex. Resultado de {p['forum_preregistration']}, respuesta a019. [Informe por fila y autos nuevos](../../Repositorio_IAA2026/docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md), [decisiones](../../Repositorio_IAA2026/{run.relative_to(REPO).as_posix()}/decision_journal.json).

Las 56 filas de capital corregido están dentro del rango normal de su ajuste. Se separó con B13 congelado el cambio de dato del reajuste B14: casi todo el movimiento (−62,36% a +154,09%) lo explica sustituir el capital imputado por el propio dividido; el reajuste aporta como máximo 0,157%/0,272% en escala log. Identidad verificada fila a fila, no una deducción del total. Todos T0=0: no confirma la escala económica. Se conservan B13/B14, la decisión CAPS2-01 y sus condiciones, sin retocar capital o F0 para ganar score.

En autos nuevos B15/B14 aumenta la pérdida 34.727,49 en 265 filas positivas y la baja 27.119,35 en 2.355 ceros; saldo adverso 7.608,15. Fold0 aporta 8.637,79. Los cinco grupos más perjudicados suman 18.085,65, compensados por otros; no se eliminan. Severidad domina el corrector. El coeficiente de negocio de precio difiere del auxiliar, por lo que multiplicar c no lo sustituye por theta_creíble. No se declara causalidad única ni error aritmético.

Se probaron las tres recetas previstas, solo2023, sin nuevos ajustes: B16 frecuencia sola, B17 severidad sola, B18 sustitución explícita del coeficiente. Hogar y renovaciones exactos B14. B15 tiene cambios de hogar también: su comparación global con estas ablaciones no aísla autos.

| Receta | D² global | A/E global | D² autos nuevos | A/E autos nuevos | Predicho autos nuevos, millones CU |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

| Comparación global | Delta D² | Intervalo exploratorio95% | Delta retirando31 grupos favorables |
| --- | ---: | --- | ---: |
{pt}

Ninguna corrección acredita mejora; los tres puntos son peores y los intervalos cruzan cero. Sustituir el coeficiente empeora más: la diferencia detectada no se convierte por sí sola en arreglo. No se elige otro peso a posteriori. Las16 OOF anteriores/120parejas siguen exactas; solo se calcularon51 parejas nuevas con2.000sorteos comunes.19recetas adaptativas/171contrastes exploratorios, sin promoción, retiro, equivalencia o lista final.

Pasaron31adversos focales,622controles separados y18conciliaciones adicionales, con solapamiento. Se bloqueó fit y se reconstruyeron exp(X beta), escala binaria, capital, factores, métricas y51remuestreos por multiplicidades, con influencia/segmentos/escenarios. Cero nuevos estimadores o calibraciones; quince factores algebraicos y treinta copias hogar;90ajustes de precio/60constantes históricos intactos,30auxiliaresv6 reutilizados. Es revisión técnica propia, no profesional independiente.

Prior desarrollado recibido y no reproducido aquí, incertidumbre omitida enZ, objetivos auxiliares/precio distintos, reporte/reservas/último y soporte conjunto siguen condicionados. Clima propuesto continúa excluido prospectivamente. Se mantienen B00 yB01–B18. La continuidad nocturna retoma nivel/cola/C0 con nueva receta previa, sin retocar c por estos resultados.2024 cerrado por instrucción directa, ledger ausente; sin precios/predicciones/scores de ese año o test, envíos, remoto, publicación externa o delegación. Se respetan autorías y estados de hallazgos ajenos.
'''
    with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v7_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
    idx=copy.deepcopy(oldidx);idx.update(id=p['id'],as_of_utc=assessment['utc'],status='seven_2023_trials_verified_capital_rows_motor_credibility_conditions_open',run=rel(run),documentation=rel(doc),
      new_price_base_fits=0,new_auxiliary_Poisson_Gamma_fits=0,new_credibility_factors=0,new_motor_algebraic_factors=15,exact_motor_reuses=0,exact_home_reuses=30,
      auxiliary_counter_notice='30 auxiliary fits fromv6 reused, none new; fifteen algebraic motor factors, no new calibration.',models_consulted=[f'W2-B{i:02d}' for i in range(19)],summary=r['summary'],pairs=r['pairs'],
      alternatives_preserved=[f'W2-B{i:02d}' for i in range(1,19)],forum_prior=p['forum_preregistration'],forum_result='COD-S2-20261024-021')
    snap=REPO/'registro/semana2_desarrollo2023_v6_snapshot.json';idx['history'][-1].update(index_snapshot=rel(snap),index_sha256=c.sha(REPO/'registro/semana2_desarrollo2023_actual.json'))
    idx['history'].append({'id':p['id'],'run':rel(run),'documentation':rel(doc)})
    for key,path in [('report',run/'report.json'),('plan',REPO/'registro/semana2_desarrollo2023_plan_v7.json'),('producer',ROOT/p['code']),('oof',run/'oof_2023.parquet'),('manifest',run/'manifest.json'),('assessment',run/'assessment.json'),('decision_journal',run/'decision_journal.json')]:idx[key]=rel(path);idx[key+'_sha256']=c.sha(path)
    for key,path in [('verification',ver),('fixtures',fixtures),('motor_reconciliation',run/'motor_reconciliation.json')]:idx[key]={'path':rel(path),'sha256':c.sha(path),'passed':c.read(path)['passed'],'failed':0}
    idx['capital_row_diagnostic']={'path':p['diagnostic_review'],'sha256':p['diagnostic_sha256']};idx['auxiliary_producer_notice']='Inheritedv6 helper only; no auxiliary fit in v7.'
    dump(run/'active_index_proposed.json',idx)
    print(json.dumps({'document':rel(doc),'motor':motor,'capital_folds':dr['capital_folds'],'reconciliation':recon['passed'],'active_index_proposed':rel(run/'active_index_proposed.json')}))
if __name__=='__main__':main()
