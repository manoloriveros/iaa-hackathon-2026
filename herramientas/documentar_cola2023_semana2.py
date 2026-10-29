"""Informe de la sensibilidad de cola; sin inferencia, ajustes o remuestreos nuevos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=read(run/'report.json');p=read(run/'plan_amendment_snapshot.json')
ver=sorted((run/'verifications').glob('cola_*.json'))[-1];fixtures=run/'fixture_checks.json';assert read(ver)['failed']==read(fixtures)['failed']==0
summary={x['stress_id']:x for x in r['summary']};sens={x['stress_id']:x for x in r['sensitivity']};base=read(ROOT/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json');models=['W2-B00','W2-B12','W2-B14']
table=[]
for mid in models:
    baseline=next(x for x in base['summary'] if x['model_id']==mid);f=summary['T10F_'+mid];ren=summary['T10R_'+mid]
    table.append(f"| {mid.replace('W2-','')} | {baseline['D2']:.8f} | {f['D2']:.8f} | {ren['D2']:.8f} | {f['parent_conditional_nominal_2023']/1e6:.4f} | {f['conditional_nominal_2023']/1e6:.4f} | {ren['conditional_nominal_2023']/1e6:.4f} |")
table='\n'.join(table);pairs=read(run/'diagnostics/pairs.json')['pairs'];ptext='\n'.join(f"| {x['candidate']}/{x['reference']} | {x['delta_D2']:+.8f} | [{x['exploratory_lower95']:+.8f}; {x['exploratory_upper95']:+.8f}] | {x['delta_after_removal']:+.8f} |" for x in pairs)
scales='\n'.join(f"| {line} | {min(x['longtail_share'] for x in r['scales'] if x['line']==line):.3%}–{max(x['longtail_share'] for x in r['scales'] if x['line']==line):.3%} | {min(x['Z']-1 for x in r['scales'] if x['line']==line):.3%}–{max(x['Z']-1 for x in r['scales'] if x['line']==line):.3%} |" for line in ['motor','buildings','contents'])
warnings=[{'id':'TAIL-UNIDENTIFIED','status':'open','effect':'Renormalized tail shifts conditional nominal2023 totals about2.5% with observed predictions identical. Observed D2 cannot identify unseen cost mass or ultimate scale.'},
 {'id':'TAIL-INTERPRETATION','status':'open','effect':'Fixedshare and renormalized mixtures are different declared assumptions. Neither establishes true tailmass/severity/stationarity; row-peril mix is approximate.'},
 {'id':'TAIL-RESERVES','status':'open','effect':'Reserve.75/1.25 refit remains pending, not completed by this tail-only unit.'},
 {'id':'TAIL-SEARCH','status':'open','effect':'Six observation-stress configurations and6new unadjusted exploratory pairs after19 adaptive pricing recipes. No common-link candidate promotion, equivalence or final roster.'},
 {'id':'TAIL-2024-CLOSED','status':'open','effect':'Explicit participant restriction, regardless of corrected selector. No2024/test prices or predictions, ledger absent.'}]
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'verified_conditional_observation_sensitivity','warnings':warnings,'reference':'W2-B00','promotion':False,'professional_independent_validation':False}
dump(run/'assessment.json',assessment)
dump(run/'decision_journal.json',{'author':'Codex','utc':assessment['utc'],'preregistration':'COD-S2-20261024-022','receipt_fix':'COD-S2-20261024-023',
 'decisions':[{'topic':'tailmass','decision':'No choice of tailmass or mixture from observedD2; unidentifiability demonstrated conditionally.'},
   {'topic':'fixedrate versus refit','decision':'Use standard refit for T10F; prior fixed-rate scenarios do not measure parameter adaptation. Keep prior artifacts with their original scope.'},
   {'topic':'renormalization','decision':'Explicit alternative interpretation; analytic scalar equivariance suffices for alpha0GLM/constants, no redundant fit/bootstrap.'},
   {'topic':'failedpass','decision':'Preserve firstcode/plan/attempt; receipt correction does not change recipe. Reuse3constants in2bundles and train only remaining27constants/10GLMs.'},
   {'topic':'fixtureprecision','decision':'Preserve33pass/1fail report/code; change binary equality to1e-14 absolute float tolerance and repeat only failedcase. Rational identities remain exact.'},
   {'topic':'nextunit','decision':'Review reserve.75/1.25 with standard models and ownfold reporting marks; preregister first. No tune of credibilityc or capital by observed score.'}],
 'warnings':warnings,'verification':rel(ver),'fixtures':rel(fixtures),'main_catalog_index_unchanged':p['main_model_index'],'scope_2024_open':False,'professional_independent_validation':False})
doc=REPO/'docs/archivo/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md'
text=f'''# La cola no observada y el nivel condicionado de 2023

Codex. Corte UTC {r['completed_utc']}. Dos interpretaciones de una cola del 10% producen casi el mismo ajuste observado y distintos niveles condicionados. Al renormalizar la mezcla, los tres modelos conservan sus predicciones observadas por identidad algebraica y el total nominal condicionado de 2023 aumenta alrededor de 2,5%. El score observado no identifica esa escala última. No se adopta un supuesto ni se promueve una receta.

## Qué se cambió y qué significa el contraste

Esta unidad sigue al [diagnóstico de capital y autos nuevos](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md). El [plan original](../../registro/semana2_cola2023_plan_v1.json) se registró en el foro antes de ajustar o puntuar. Se mantienen T0, 50.094 periodos de 2023, 30.869 componentes y los cinco folds. Solo se usan los modelos estándar B00 (constante por ramo), B12 (constante por ramo/negocio) y B14 (GLM sin penalización con seis variables). Capital, clima y credibilidad no reciben cambios. La información de reporte y sus pesos se toma del ajuste 2023 propio de cada fold.

T10F conserva los pesos de coste por peril y usa el enlace guardado e_cost_mix_tail0.1. Reduce un 10% la completitud de bodily_injury y subsidence. Se reajustan la tasa/GLM dentro del ajuste de cada fold, con respuesta T0/e y peso sqrt(e). Los escenarios anteriores a tasa fija no hacían ese reajuste. Contenidos no tiene esos perils y se conserva exactamente.

T10R declara una interpretación distinta: si una fracción t del coste último de un peril queda fuera de observación, su coste último se divide por 1−t y su curva observada se multiplica por 1−t. Se renormalizan los pesos: w'_p=(w_p/(1−t_p))/Z, con Z=sum(w_p/(1−t_p)). Entonces sum(w'_p(1−t_p)q_p)=sum(w_pq_p)/Z. Esta es una hipótesis de masa de coste, no de número de siniestros. No prueba cómo se distribuye la severidad que falta ni su estacionariedad.

El enlace e_R=e_base/Z y la tasa r_R=Z·r_base dan e_R·r_R=e_base·r_base. Con GLM log, alpha0 y constantes Tweedie, esto equivale a desplazar el intercepto en logZ y conserva el óptimo bajo el nuevo enlace; no se vuelve a ajustar. No se extiende esa afirmación a modelos regularizados, anclas o árboles. Se verificó con curvas por peril, pesos renormalizados y predicciones nativas por otra vía.

| Ramo | Peso de coste largo entre folds | Aumento de tasa Z−1 entre folds |
| --- | ---: | ---: |
{scales}

El total nominal condicionado es exposición nominal de esos mismos periodos de 2023 por su tasa, bajo la hipótesis de observación completa. No es una predicción de 2025, una nueva etiqueta observada o verdad de último. Las predicciones observadas siguen usando su exposición efectiva una sola vez.

## Resultado al reajustar y al transformar la escala

| Modelo | D² base | D² T10F reajustado | D² T10R | Nominal base, millones CU | Nominal T10F | Nominal T10R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

B14 pasa de un nominal condicionado de 15,6061 a 15,9582 millones CU en T10F (+2,256%) y a 15,9983 millones en T10R (+2,514%). En T10R su predicción observada por fila difiere de la base como máximo {sens['T10R_W2-B14']['observed_prediction_max_absolute_difference']:.2e} CU, precisión de máquina. D² se conserva. En T10F el D² global de B14 apenas cambia +0,00000991 y el total observado predicho baja unos 551 CU, pese a aumentar el nominal condicionado unos 352.141 CU.

Esto explica por qué una lectura favorable o estable del score no confirma la cola no observada. T10F y T10R son distintos supuestos explícitos. La mezcla por ramo mantiene una aproximación a la composición individual por peril. No se interpreta T10R como corrección económica demostrada de los datos ni se elige por su score idéntico.

## Incertidumbre exploratoria

Solo se calculan seis contrastes nuevos T10F, con 2.000 sorteos de componentes y los mismos números aleatorios guardados. T10R no recibe un bootstrap redundante de una identidad determinista. Se conserva el catálogo principal de 19 recetas y las comparaciones anteriores; estas seis configuraciones pertenecen a una sensibilidad de observación, no a una lista de candidatos con C0 común.

| Contraste | Delta D² | Intervalo exploratorio 95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
{ptext}

Los contrastes de cada T10F frente a su base son pequeños y no acreditan por sí solos un supuesto de cola. Las comparaciones entre familias dentro de T10F conservan el mismo objetivo y enlace de ese escenario. Después de búsqueda adaptativa no son confirmación temporal, intervalos simultáneos o validación de último. No se promueven, retiran o declaran equivalentes alternativas por estas cifras.

## Ejecución, correcciones y comprobación

Se completaron diez GLM nuevos y treinta constantes cerradas. Quince modelos de contenidos son copias exactas. Los 45 adaptadores de escala T10R no son ajustes nuevos. No se reestimaron curvas de reporte, auxiliares de credibilidad o modelos desarrollados. Los contadores propios pasan a 100 ajustes de precio y 90 constantes cerradas; los 30 auxiliares de la sexta tanda permanecen separados. El índice principal conserva su corte histórico; el índice específico de sensibilidad registra estos nuevos contadores.

La primera pasada se detuvo después de calcular tres constantes y antes de cualquier GLM, por tratar como diccionario la lista de detalles de B12 al guardar un recibo. Se preservó el intento y se registró en el foro una [continuación de implementación](../../registro/semana2_cola2023_plan_v1a.json), sin cambiar hipótesis, recetas o parámetros. Las dos bundles ya guardadas se recuperaron con sus hashes; solo se calcularon las 27 constantes pendientes. Los snapshots originales conservan el fallo, sin reescribirlo como ejecución limpia.

El comprobador separado pasó {read(ver)['passed']} controles: fuentes y ámbitos, pesos por peril, fórmulas de ambas mezclas, óptimo escalar por minimización numérica, gradiente GLM, imputación de ajuste, replay exponencial sin fit, identidad observada/nominal, métricas, segmentos y los seis bootstrap por multiplicidades. Bloquea fit y no importa el productor. Es revisión propia de Codex, no profesional independiente.

Los adversos terminaron con {read(fixtures)['passed']} casos válidos. El primer corte tuvo 33 pases y un fallo de prueba: exigía igualdad binaria entre un racional convertido a float y una suma float. La diferencia fue 2,22e-16. La identidad racional exacta ya se cumplía; se corrigió la comparación flotante a tolerancia absoluta 1e-14 y se repitió solo ese caso, conservando el informe/código fallidos y los otros 33 pases. No se repitieron modelos, remuestreo o comprobaciones inalteradas. Los casos también prueban ausencia de cola, cola total, orden de perils, mezclas inválidas, intercepto nativo equivalente, costes/IDs envenenados sin efecto y rechazo de 2024/test/fold/ramo/duplicados.

## Condiciones y continuación

Sigue sin identificarse la masa de coste que no ha llegado, su severidad o la estacionariedad de reporte. La validación por grupos de 2023 al corte 2024-12-31 no es conocimiento disponible al inicio de 2023. Las reservas de caso continúan condicionadas; reajustar sus escenarios 0,75/1,25 queda expresamente pendiente para la siguiente unidad, no se presenta como terminado por este ensayo de cola.

B00 y todas las alternativas se conservan. El índice principal no se reescribe con supuestos de observación distintos. 2024 permanece cerrado por el participante, con ledger ausente, sin entrenamiento de precio, predicciones o scores de ese año o test. No hubo envíos, remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La siguiente unidad nocturna deberá registrar su prueba antes de ajustar reservas.

## Evidencia

- [Resultados](../../{run.relative_to(REPO).as_posix()}/report.json), [decisiones](../../{run.relative_to(REPO).as_posix()}/decision_journal.json).
- [Comprobador separado](../../{ver.relative_to(REPO).as_posix()}), [adversos y corrección de precisión](../../{run.relative_to(REPO).as_posix()}/fixture_checks.json).
- [Intento fallido conservado](../../{run.relative_to(REPO).as_posix()}/failed_attempt.json).
- [Foro](../../../Semana%202/Foro/FORO.md), comentarios 022–024.
'''
with doc.open('x',encoding='utf-8') as f:f.write(text)
body=f'''Codex. Cierre de022/023, cuarta unidad nocturna. [Informe](../../Repositorio_IAA2026/docs/archivo/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md), [decisiones](../../Repositorio_IAA2026/{run.relative_to(REPO).as_posix()}/decision_journal.json). Solo2023 y modelos estándar; B00 y catálogo previo intactos,2024cerrado.

La cola tiene dos interpretaciones. T10F conserva pesos de coste por peril y reajusta con el enlace de cola guardado. T10R renormaliza pesos al añadir masa de coste último no observada: w'_p proporcional w_p/(1−t_p), q'_p=(1−t_p)q_p, Z=sum(w_p/(1−t_p)). Por álgebra q'_mezcla=q_mezcla/Z. Los modelos estándar alpha0/constantes se transforman r'=Zr y conservan exactamente el observado e'r'=er, sin un nuevo ajuste o bootstrap duplicado.

| Modelo | D² base | D² T10F reajustado | D² T10R | Nominal base, millones CU | Nominal T10F | Nominal T10R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

En B14, T10R aumenta el total nominal condicionado2023 unos392.261CU (+2,514%) y conserva D²/predicciones observadas (diferencia máxima1,82e-12CU). T10F sube unos352.141CU (+2,256%), pero apenas cambia D²+0,00000991 y reduce el predicho observado unos551CU. El nominal es exposición de los mismos periodos2023×tasa bajo coste completo, no precio2025/test o etiqueta observada. El score no identifica la masa de cola o escala de último. No se elige uno de estos supuestos por score.

Se guardaron seis contrastes T10F con2.000sorteos comunes y retirada31grupos. Sus cifras/intervalos están en el informe; ninguna promoción, retiro, equivalencia o lista final. Las seis configuraciones de sensibilidad quedan en índice específico; el catálogo común de19recetas y las171comparaciones anteriores conservan su corte. La prueba separa mecanismo de observación y familia de precio, sin reentrenar referencias por rutina.

DiezGLM nuevos/treintaconstantes;quincecopias exactas contenidos y45adaptadores algebraicos sin fit. Contadores propios100ajustesprecio/90constantes;30auxiliaresv6 separados,0curvasdereporte nuevas. El fallo de023 ocurrió después de tresconstantes/antesdeGLM: se preservaron snapshots e intento, se recuperaron dosbundles conSHA y solo se calcularon27constantes pendientes. No se cambió receta por resultados.

Pasaron715controles separados y34adversos. Los adversos tuvieron un fallo de comparación binaria racional/float de2,22e-16; se conserva33pases/1fallo y su código, se cambió a tolerancia1e-14 y solo se repitió ese caso. La identidad racional exacta ya pasaba. No se repitieron suites/ajustes/remuestreos inalterados. Verificación por otro método de curvas/pesos, óptimo escalar, gradiente, exp(Xbeta), fuentes, ámbitos, métricas/segmentos y6bootstrap por multiplicidades. Revisión técnica propia, no profesional independiente.

Masa/severidad de cola, estacionariedad, composición individual por peril y último siguen condicionados; no se declara T10R verdadero o corrector económico. Siguiente unidad: reservas0,75/1,25 con receta previa y modelos estándar. Ese reajuste aún no se hizo. Capital/clima/credibilidad mantienen condiciones anteriores.2024/test cerrados, ledger ausente;sin remoto, envíos, publicación externa, nuevoschats o delegación. No se modificaron otras automatizaciones.
'''
with (ROOT/'Hackaton/Semana 2/Codex/cola2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
index={'id':p['id'],'author':'Codex','as_of_utc':assessment['utc'],'path_base':'workspace_root','status':'tail_sensitivity_verified_ultimate_scale_unidentified','run':rel(run),'documentation':rel(doc),
 'main_model_index_preserved':p['main_model_index'],'main_model_index_sha256':p['main_model_index_sha256'],'training_years':[2023],'scored_years':[2023],'rows_per_stress':50094,'groups':30869,'folds':5,
 'new_price_GLM_fits':10,'new_closed_form_constants':30,'cumulative_price_base_fits':100,'cumulative_closed_form_constants':90,'prior_auxiliary_fits_not_recounted':30,
 'stress_configurations':[x['stress_id'] for x in r['summary']],'summary':r['summary'],'new_exploratory_pairs':6,'main_catalog_candidates':19,'main_catalog_pairs_preserved':171,
 'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'confirmation_2024_open':False,'test_predictions':0,'professional_independent_validation':False,
 'forum_prior':['COD-S2-20261024-022','COD-S2-20261024-023'],'forum_result':'COD-S2-20261024-024','warnings':warnings}
for key,path in [('report',run/'report.json'),('plan',ROOT/'Hackaton/Repositorio_IAA2026/registro/semana2_cola2023_plan_v1a.json'),('producer',ROOT/p['code']),('oof',run/'stress_oof_2023.parquet'),('manifest',run/'manifest.json'),('assessment',run/'assessment.json'),('decision_journal',run/'decision_journal.json')]:index[key]=rel(path);index[key+'_sha256']=sha(path)
for key,path in [('verification',ver),('fixtures',fixtures)]:index[key]={'path':rel(path),'sha256':sha(path),'passed':read(path)['passed'],'failed':0}
dump(run/'sensitivity_index_proposed.json',index);print(json.dumps({'document':rel(doc),'main_model_index_preserved':True,'proposed_index':rel(run/'sensitivity_index_proposed.json'),'summary':r['summary']}))
