"""Cotejo posterior y documentación de la reevaluación protegida de F3c."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib, importlib.util, json, platform, sys
import numpy as np
import pandas as pd
from sklearn.metrics import d2_tweedie_score

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
RUN=REPO/'privado/validacion_cadena_f3c/20261027T153123Z'
spec=importlib.util.spec_from_file_location('protected',REPO/'herramientas/validar_cadena_f3c.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(v.clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def fmt(x):return f'{x:+.7f}'.replace('.',',')
def ci(a):return '['+'; '.join(fmt(x) for x in a)+']'

v.verify_inputs();r=read(RUN/'resultados.json');train=read(RUN/'training_complete.json');op=read(RUN/'opened.json')
assert train['all_passed'] and all(train['checks'].values())
assert read(RUN/'oraculos_escalares.json')['all_passed']
assert train['source_native_fit_attempts']==12
assert sha(RUN/'baseline_predictions.parquet')==op['predictions_sha256']
assert sha(RUN/'target2024_sealed.parquet')==op['target_sha256']
t=pd.read_parquet(RUN/'baseline_predictions.parquet').merge(pd.read_parquet(RUN/'target2024_sealed.parquet'),on='row_id',validate='1:1')
assert len(t)==59202 and t.row_id.is_unique
checks={}
canonical_path=REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/target_T0_and_stresses.parquet'
assert sha(canonical_path)=='114dd8ae8048a04530855c7be8f8e718ebd9fe969f491c4513fc1fadbd0bcca6'
canonical=pd.read_parquet(canonical_path,columns=['market','row_id','year','T0_cents'])
canonical=canonical[canonical.market.eq('emerging')&canonical.year.eq(2024)]
aligned=t[['row_id','y']].merge(canonical[['row_id','T0_cents']],on='row_id',validate='1:1')
checks['same_59202_canonical_T0_by_cent']=len(aligned)==59202 and np.array_equal(np.rint(aligned.y.to_numpy(float)*100).astype(np.int64),aligned.T0_cents.to_numpy(np.int64))
for model in ['sin_factores','F3c_reaprendido','constante']:
    checks['sklearn_'+model]=abs(d2_tweedie_score(t.y.to_numpy(float),t[model].to_numpy(float),power=1.5)-r['metrics']['global']['D2'][model])<1e-12
g,_=v.components(t);groups,ix=np.unique(g,return_inverse=True);rng=np.random.default_rng(2026102301)
boot=np.load(RUN/'bootstrap.npz');names=list(boot['models']);seg=list(boot['segments']);err=0.
for n in range(20):
    counts=np.bincount(rng.integers(0,len(groups),size=len(groups)),minlength=len(groups));w=counts[ix]
    for model in names:
        score=d2_tweedie_score(t.y.to_numpy(float),t[model].to_numpy(float),sample_weight=w,power=1.5)
        err=max(err,abs(score-boot['scores'][n,seg.index('global'),names.index(model)]))
checks['twenty_bootstrap_draws_match_sklearn']=err<1e-12
f3c=REPO/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
checks['production_F3c_preserved']=sha(f3c)=='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
checks['all_predicted_positive']=all(np.isfinite(t[k].to_numpy(float)).all() and t[k].gt(0).all() for k in names)
assert all(checks.values()),checks
save(RUN/'verificacion.json',{'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'bootstrap_check_max_error':err,'source_native_fits':12,'synthetic_native_fits':2,'rows':len(t),'all_passed':True,'professional_independent_review':False})
save(RUN/'entorno.json',{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__,'lightgbm':v.lgb.__version__,'threads_source':2})

primary=r['metrics']['global'];interval=r['intervals']['global'];nb=r['metrics']['new_business'];mix=r['metrics']['mix2025_global'];inf=r['influence']
renew_share=r['metrics']['renewal']['delta']*r['metrics']['renewal']['null_deviance']/(primary['delta']*primary['null_deviance'])
save(RUN/'comparacion_antes_despues.json',{'utc':datetime.now(timezone.utc).isoformat(),'historical_report':'docs/validacion_cinco_prioridades/20261027T142339Z/P03.md','historical_report_sha256':sha(REPO/'docs/validacion_cinco_prioridades/20261027T142339Z/P03.md'),'new_results_sha256':sha(RUN/'resultados.json'),'canonical_T0_sha256':sha(canonical_path),'historical_global_delta':0.0023923056907,'new_global_delta':primary['delta'],'new_renewal_share_of_net_deviance_gain':renew_share,'historical_top37_delta_approx':0.000004268,'new_top37_delta':inf['delta_without_top'],'causal_difference_identified':False,'source_scope':'Histórico con formas públicas y agrupación36398; nuevo sin esas formas y agrupación36408. No son estimandos idénticos.'})
influence_text=(f"La retirada retrospectiva de {inf['groups_to_erase']} grupos alcanza la anulación de la ganancia según ese cálculo." if primary['delta']>0 else 'La diferencia inicial ya es no positiva; un número de grupos hasta anularla no se interpreta como resistencia de una ganancia.')
doc=REPO/'docs/semana2/F3C_CADENA_PROTEGIDA_REEVALUACION.md'
rows=[]
for label,key in [('Global','global'),('Negocio nuevo','new_business'),('Renovación','renewal'),('Autos','motor'),('Edificios','buildings'),('Contenidos','contents'),('Autos nuevo','motor_1'),('Edificios nuevo','buildings_1'),('Contenidos nuevo','contents_1'),('Composición 2025','mix2025_global')]:
    q=r['metrics'][key];count=f"{q['rows']:,}".replace(',','.');sf=f"{q['D2']['sin_factores']:.7f}".replace('.',',');fc=f"{q['D2']['F3c_reaprendido']:.7f}".replace('.',',');rows.append(f"| {label} | {count} | {sf} | {fc} | {fmt(q['delta'])} |")
grows=[]
labels={'global_lower_above_margin':'Límite inferior familiar > 0,0005','broad_segments_floor':'Cinco segmentos amplios ≥ −0,001','new_business_protection':'Protección de negocio nuevo','motor_NB_stability_floor':'Autos nuevo ≥ −0,001','influence':'Ganancia después de retirar grupos favorables'}
for key,label in labels.items():grows.append(f"| {label} | {'Pasa el control puntual/condicional' if r['guard_status'][key] else 'No pasa'} |")
text=f'''# F3c: corrección de la cadena y nueva evaluación

Codex, 27 de octubre de 2026. Reevaluación exploratoria solicitada expresamente después de las cinco auditorías. Código nuevo sobre originales, con plan y fuentes congelados antes del entrenamiento. F3c de producción, las referencias, el PDF, el guion y la selección se conservan. La revisión es propia de IA y no equivale a validación profesional independiente.

Se corrigió la separación computacional de la cadena del contraste primario T2b: desde la construcción del objetivo y las curvas hasta los árboles fuente, los factores y el nivel. Los controles adversos nuevos pasan, incluida una repetición real de los ajustes fuente con costes de 2024 alterados. Esto cambia la conclusión técnica sobre esta implementación nueva; la cadena histórica conserva sus fallos documentados. La disponibilidad histórica de la información y la adaptación previa de 2024 siguen sin resolverse.

La ganancia global del bloque propio reaprendido es {fmt(primary['delta'])} de D², con banda condicional de familia 6 {ci(interval['family6'])}. El límite exigido sigue siendo 0,0005. El resultado del control es {'favorable dentro de ese alcance' if r['guard_status']['global_lower_above_margin'] else 'insuficiente para acreditar una mejora clara'}. Ningún resultado de este expediente autoriza una promoción formal o acredita un score privado.

## Qué se corrigió

Se reconstruyen T0, exposición y atributos desde los Parquet originales, conservando reglas puntuales de limpieza e identificación y su procedencia. La asignación sigue ramo, póliza y ocurrencia dentro del periodo. Los importes permanecen valorados al 31 de diciembre de 2024: no son snapshots recuperados de 2023.

Las curvas maduras de coste y las participaciones por peligro se vuelven a calcular únicamente con las filas permitidas en cada ámbito. Para seleccionar rondas del árbol fuente, se excluye la componente interna retenida antes de aprender curvas, participaciones y categorías. Después se recalculan los objetos del train completo y se reajusta con las rondas elegidas. El árbol fuente usa desarrollado de 2021–2023; ninguna etiqueta de 2024 de ambos mercados entra en esos argumentos.

Los folds agrupan clientes conectados por dirección entre ramos, dentro de cada mercado. La evaluación temporal permite renovaciones presentes en 2023; eso es diferente de afirmar independencia de entidades entre años. Los diccionarios categóricos se aprenden solo del entrenamiento fuente, con categorías no vistas como ausentes. No se unen con el destino ni con el test.

Las bases emergentes de entrenamiento de 2023 usan niveles OOF de cinco folds, con completitud y participaciones aprendidas fuera del fold evaluado. F2 y los factores propios se aprenden sobre esas bases OOF de 2023. Los niveles finales se estiman solo con 2023. La normalización de factores y forma se aprende en entrenamiento y queda fija para aplicar precios fila a fila; no se recalcula a partir de la cartera retenida.

La receta mantiene el esquema T2b y sus hiperparámetros históricos, K=300 y la secuencia de factores. Conserva como decisión fija heredada la forma 0,9 de autos renovación. El contraste principal retira los exponentes y el nivel del tablero, además de la forma auxiliar A_M1 procedente del diagnóstico histórico. No se buscaron K, subconjuntos, semillas o variantes después de evaluar. Son decisiones de receta heredadas o fijadas ahora: esta corrección no borra la selección histórica que condujo a ellas.

La versión sin factores propios conserva F2, con NCB y siniestros previos, y la forma común. La diferencia evaluada corresponde al bloque adicional de género en autos/contenidos y teletrabajo/marketing en contenidos, con sus niveles aprendidos en 2023. «Sin factores» en las tablas se refiere a ese bloque propio.

## Resultado nuevo

| Segmento | Filas | D² sin factores | D² F3c reaprendido | Diferencia |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

Todos los D² usan el mismo T0 observado y el mismo vínculo de completitud dentro de cada contraste. Los segmentos usan su propio nulo; no se promedian para obtener el global. La constante por ramo y negocio, aprendida en 2023, obtiene D² global {primary['D2']['constante']:.7f}.

En negocio nuevo, el IC95 condicional es {ci(r['intervals']['new_business']['CI95'])}. Con composición de 2025, el cambio global es {fmt(mix['delta'])}, IC95 {ci(r['intervals']['mix2025_global']['CI95'])}. Esa reponderación usa conteos por ramo, negocio y bandas de exposición; no identifica por sí sola el rendimiento futuro.

Se mantienen 10.000 remuestreos pareados de componentes cliente–dirección, semilla 2026102301 y familia nominal de seis pares. Se recalcula el nulo en cada cartera. Son intervalos condicionales a precios y modelos ya aprendidos; no repiten el entrenamiento de toda la cadena ni corrigen la búsqueda histórica. La repetición adversa de entrenamiento comprueba aislamiento, no añade años independientes para la inferencia estadística.

| Control conservado | Resultado |
| --- | --- |
{chr(10).join(grows)}

El diagnóstico de influencia utiliza {inf['groups']:,} componentes de las filas de 2024. Al retirar los {inf['removed']} más favorables, la diferencia es {fmt(inf['delta_without_top'])}. {influence_text} Es un diagnóstico de concentración, sin probabilidad asociada. La agrupación se construye en el ámbito nuevo; no se sustituye silenciosamente la unidad histórica de la revisión anterior.

## Qué conclusiones cambian

La auditoría anterior demostró que los costes retenidos cambiaban completitud y nivel del entrenamiento. En la implementación nueva, los argumentos completos de los ajustes fuente, los modelos, sus predicciones y los parámetros/precios finales permanecen exactamente iguales al perturbar los costes de 2024. También se comprueba la separación de direcciones entre folds y que la aplicación de factores es invariante al orden de las filas. La corrección computacional del contraste primario queda verificada con esos límites explícitos.

El +0,0023923 histórico frente a la referencia sin factores se conserva como resultado de la receta antigua. El número nuevo es {fmt(primary['delta'])}. No se interpreta su diferencia como efecto causal exclusivo de corregir la completitud: también cambian las particiones, las categorías, los normalizadores y la retirada de calibraciones públicas que estaban dentro de la comparación anterior. La vista antigua sin exponentes públicos tampoco es idéntica a esta receta nueva. No se suman ambos resultados ni se presentan como confirmaciones independientes.

| Conclusión del contraste | Auditoría anterior | Cadena nueva |
| --- | --- | --- |
| Separación computacional desde preparación | Fallaba | Pasa en el contraste primario corregido |
| Ganancia global | +0,0023923 | {fmt(primary['delta'])} |
| Protección de negocio nuevo | No acreditada | Sigue sin pasar |
| Diferencia de autos nuevo | −0,0010036 | {fmt(r['metrics']['motor_1']['delta'])} |
| Diferencia tras retirar 37 grupos favorables | +0,0000043; pasaba por poco el veto nominal | {fmt(inf['delta_without_top'])}; falla el veto |
| Ganancia con composición de 2025 | +0,0012080; intervalo cruzaba cero | {fmt(mix['delta'])}; intervalo sigue cruzando cero |

La concentración es una conclusión que empeora: el nuevo contraste falla el veto de influencia que el anterior apenas superaba. La renovación aporta aproximadamente {100*renew_share:.2f}% de la mejora neta de desviación del contraste nuevo. Esa proporción usa contribuciones de desviación sobre el mismo total; no suma D² con nulos distintos. Las recetas y las agrupaciones de ambas columnas tienen los límites de comparabilidad descritos.

El control de mejora global {'pasa' if r['guard_status']['global_lower_above_margin'] else 'no pasa'} ahora el umbral condicional registrado. La protección de negocio nuevo {'pasa ese control condicional' if r['guard_status']['new_business_protection'] else 'sigue sin pasar'}. El control puntual de autos nuevo {'pasa' if r['guard_status']['motor_NB_stability_floor'] else 'no pasa'}. Estos resultados actualizan el dictamen de este contraste, con todas las cifras adversas conservadas. La estabilidad entre años de cada factor necesita su propio contraste; un piso puntual no la acredita.

## Pendientes que siguen abiertos

El año 2024 ya fue consultado y usado para decidir. El plan nuevo es anterior a esta corrida, pero la evaluación continúa siendo adaptativa. No hay un año futuro independiente ni un score privado observado. La puerta formal v1 y sus actas históricas no se reabren, ni se marca resuelta una advertencia de disponibilidad por pasar una prueba de aislamiento computacional.

Esta ejecución protege la cadena del contraste primario T2b, que era la base de la afirmación global sobre los factores. No reentrena la rama A1 ni la mezcla en sus propios ámbitos, ni convierte el CSV F3c de producción, aprendido con 2023 y 2024, en una predicción OOF. Repetir esas sensibilidades bajo el diseño corregido sigue pendiente antes de extender a ellas el dictamen técnico.

Permanecen sin acreditar los maestros fechados y el acceso real al cotizar, la duración inicialmente contratada, el vintage climático y la operación de la contingencia sin factores. La historia del nuevo contraste conserva su corte anterior al inicio de cobertura; no se afirma que fuera conocida en la cotización. La valoración única de 2024 tampoco permite reconstruir reservas, estados o costes de 2023 tal como se conocían entonces.

La suficiencia de reservas, la cola no reportada y el transporte de las curvas siguen necesitando valoraciones posteriores y evidencia nueva. Los escenarios y las salvaguardas completos deben repetirse sobre la receta nueva antes de cualquier promoción; los resultados históricos de otra cadena no se transfieren como aprobaciones. El soporte escaso de negocio nuevo de hogar no aumenta con esta corrección. La revisión profesional por otra persona también permanece pendiente.

## Evidencia y reproducción

El código está en `herramientas/validar_cadena_f3c.py` y `herramientas/cerrar_validacion_cadena_f3c.py`, relativos al repositorio. Plan, manifiesto SHA, apertura exploratoria, entorno, intentos de ajuste, modelos, parámetros, precios históricos, bootstrap, resultados y verificación están en `privado/validacion_cadena_f3c/20261027T153123Z/`. No se publican identificadores o precios por fila. Se completaron doce ajustes fuente, seis originales y seis de repetición adversa, más dos ajustes sintéticos de comprobación. Los controles estadísticos se cotejaron con scikit-learn; las primeras veinte réplicas del bootstrap coinciden con error máximo {err:.3g}.

F3c de producción conserva su SHA exacto. No se hicieron inferencias nuevas de 2025, envíos, entrenamiento remoto, cambios de marca, modificaciones del PDF o del guion. Las referencias y los fallos históricos se conservan.
'''
doc.write_text(text,encoding='utf8')
idx={'id':'F3C-CADENA-PROTEGIDA-20261027','utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','path_base':'repository_root','status':'contraste_primario_reentrenado_y_verificado_exploratorio','report':str(doc.relative_to(REPO)).replace('\\','/'),'run':str(RUN.relative_to(REPO)).replace('\\','/'),'primary_delta':primary['delta'],'primary_family6':interval['family6'],'new_business_protection':r['guard_status']['new_business_protection'],'computational_primary_chain_verified':True,'all_production_branches_verified':False,'formal_promotion':False,'professional_independent_review':False,'selection_changed':False,'F3c_sha256':sha(f3c)}
save(REPO/'registro/validacion_cadena_f3c_actual.json',idx)
artifacts=[]
for p in sorted(RUN.rglob('*')):
    if p.is_file() and p.name!='cierre.json':artifacts.append({'path':str(p.relative_to(REPO)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size})
for p in [doc,REPO/'herramientas/cerrar_validacion_cadena_f3c.py']:artifacts.append({'path':str(p.relative_to(REPO)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size})
save(RUN/'cierre.json',{'utc':datetime.now(timezone.utc).isoformat(),'index':idx,'artifacts':artifacts})
print(json.dumps(idx,ensure_ascii=False,indent=2))
