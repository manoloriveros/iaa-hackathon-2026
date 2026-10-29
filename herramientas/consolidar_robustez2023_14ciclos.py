"""Balance de evidencia existente, sin repetir entrenamiento, scoring o remuestreo."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/balance14_20261025_v1'
DOC=R/'docs/archivo/semana2/BALANCE_ROBUSTEZ_2023_20261025.md';INDEX=R/'registro/semana2_robustez2023_actual.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
assert not OUT.exists() and not DOC.exists();OUT.mkdir(parents=True);idx=read(INDEX);counter=read(R/'registro/semana2_contadores_propios_actual.json');assert len(idx['completed_cycles'])==14 and counter['cumulative_price_base_fits']==684
entries=[]
for cycle in idx['completed_cycles']:
 rp=ROOT/cycle['report'];assert sha(rp)==cycle['report_sha256'];report=read(rp);summaries={x['model_id']:x for x in report['summaries']}
 for gate in report['gates']:
  mid=gate['model_id'];pair=next(x for x in report['pairs'] if x['candidate']==mid)
  entries.append({'cycle':cycle['cycle'],'model_id':mid,'primary':pair['reference'],'D2':summaries[mid]['D2'],'delta':pair['delta_D2'],'interval':pair['exploratory_interval'],'folds':pair['positive_folds'],'after31':pair['delta_after_removal'],'all_pass':gate['all_pass'],'checks':gate['checks']})
assert len(entries)==31 and sum(x['all_pass'] for x in entries)==2
release=R/'privado/semana2/robustez2023/entrega_20261025_v1';pub=read(release/'public_check02.json');build=read(R/'privado/semana2/robustez2023/paquete_20261025_v1/build_receipt.json');replaypath=R/'privado/semana2/robustez2023/paquete_20261025_v1/extracted_replay/package_replay_receipt.json';replay=read(replaypath)
assert replay['success'] and sha(ROOT/build['zip'])==build['zip_sha256']
for item in read(release/'ready.json')['CSV']:assert sha(ROOT/item['path'])==item['sha256']
powers=[]
for mid in ['W2-COD-R51','W2-COD-R52']:
 for line in ['motor','buildings','contents']:
  values=[x['teacher_risk_power'] for x in read(R/'privado/semana2/robustez2023/ciclo14_20261025_v1/training_receipts.json') if x['model_id']==mid and x['line']==line]
  assert len(values)==5 and min(values)>=-1e-12 and max(values)<=2+1e-12;powers.append({'model_id':mid,'line':line,'min':min(values),'max':max(values)})
table='\n'.join(f"| {x['cycle']} | {x['model_id']} | {x['D2']:.6f} | {x['primary']} | {x['delta']:+.6f} | {x['folds']}/5 | {x['after31']:+.6f} | {'Pasa' if x['all_pass'] else 'No pasa'} |" for x in entries)
powertext='; '.join(f"{x['model_id']}/{x['line']}: {x['min']:.3f}–{x['max']:.3f}" for x in powers)
doc=f'''# Balance de robustez del modelo, 25 de octubre de 2026

El mejor score público propio observado pasó de **0,13310 a 0,14331**, diferencia +0,01021 (+7,67% respecto al score inicial). Es una mejora procesada por Kaggle; no demuestra por sí sola significancia estadística ni el salto grande solicitado. El trabajo deja dos alternativas que pasan los controles exploratorios de 2023, los resultados adversos de catorce ciclos y un paquete privado que reproduce exactamente ambos CSV. No se declara alcanzado el objetivo de una mejora pública grande.

Codex, {now()}. Solo cohortes de precios de 2023 para ajustes y validación; cotizaciones de 2025 para las entregas autorizadas, después de congelar recetas y completar ajustes finales. 2024 sigue cerrado para cohortes, precios, scores, ledger, actas y SEL01. La exposición ajena previa de un asunto ya declarada impide afirmar ceguera completa; no se usa en estas decisiones. No se cambian automatizaciones, otros chats, autorizaciones ajenas o selección final manual.

## Resultado que sí se sostiene en estas comprobaciones

R36 tiene D² OOF2023 **0,11053677**, frente a B20 **0,08938179** y B00 **0,06858169** sobre los mismos 50.094 periodos. Delta frente a B20 +0,02115499; intervalo bootstrap de grupos exploratorio [0,01032137; 0,03163706]. Mejora en cinco de cinco folds y en los seis segmentos ramo/negocio. Al retirar del diagnóstico los 31 grupos de contribución más favorable sigue +0,00410578. No se retiraron grupos o siniestros del ajuste. R37, con menor peso transferido, también pasa: D² 0,10228050, delta +0,01289871 y +0,00337692 después de ese diagnóstico.

Estas cribas son exploratorias tras búsqueda adaptativa. El remuestreo no corrige todas las decisiones previas, ni toda la incertidumbre del profesor fuente o la identificación de último. No hay revisión actuarial profesional independiente ni aprobación humana técnica inventada. No se promociona una lista final por el score de 2023.

## Recetas y evidencia conservadas

| Ciclo | Modelo | D² OOF2023 | Referencia | Delta | Folds positivos | Delta sin 31 grupos | Cribas |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
{table}

El comparador pasó de B20 a R36 en el ciclo 8; los deltas de filas distintas no se suman. Se exigió delta >=0,005, límite inferior exploratorio >0,0005, >=4 folds favorables, daño por ramo/negocio <=0,0005 de la desviación nula completa y delta >=0,0005 al retirar 31 grupos favorables solo del diagnóstico. Los ciclos 11/12 añadieron un veto fuente separado; el 9 un veto por sexo y necesidad incremental. Las reglas no se relajaron para aceptar un resultado. Bootstrap de 2.000 grupos, semilla 2026102501 y cuantiles 0,0041666666667/0,9958333333333, con nulo recalculado.

La arquitectura conservada aprende forma física en desarrollado2023 (626.355 periodos, incurrido neto observado/exposición nominal) con GLM y corrección pequeña fija de 200 árboles. En emergente2023 aprende solo intercepto, negocio y región dentro de cada ajuste exterior. La fuente no aporta soporte emergente y su incurrido no es último identificado. Los profesores de edificios excluyen construcción por la codificación W/w sin material confirmado. Capitales/C0 y el resto del objetivo se conservaron.

R36 mezcla en raíz cuadrada 50% de ese precio y 50% de B20; R37 usa 25%/75%. Ambos pesos se fijaron antes de sus scores locales y públicos. No se afinaron con el leaderboard. R37 mantiene su prioridad conservadora preinscrita; R36 se identifica aquí como mejor público propio observado, sin cambiar selección final manual.

## Qué se descartó y por qué

Los GLM ampliados, splines, frecuencia/severidad, árboles emergentes y transferencia conjunta no mostraron la ganancia estable exigida. El desglose por peril mantuvo los costes presentes con banderas de cobertura apagadas, sin suprimirlos ni inventar exposición asegurada. La descomposición no superó materialmente a R36.

Las declaraciones previas en el emergente aportaron un incremento pequeño sin robustez suficiente; añadir sexo empeoró frente a la declaración sola. El diccionario permite M/F en emergente y define prior_claims_5y antes de incorporarse, pero no certifica versiones históricas del maestro. No se adoptaron estos perfiles.

La ampliación física por densidad, edad en hogar y banderas del inmueble no mejoró al incumbente. El primer enlace se detuvo porque esas columnas ya estaban en las entradas estrictas: se comprobó igualdad exacta de los 15 archivos y la continuación conservó tres ajustes ya válidos. No hubo sobrescritura silenciosa ni tres ajustes repetidos.

La mayor capacidad fuente empeoró en el control separado por cliente/domicilio y en el emergente. El bloque de perfiles comunes tampoco ayudó. Su extracción detectó 23.628 clientes fuente ausentes del maestro (25.571 periodos de motor); se conservaron filas, costes y exposición con perfiles ausentes, sin inventar identidades. Los primeros extractores fallidos quedaron preservados. Los valores libres de ocupación desconocidos no se reagruparon después de observar resultados.

Los efectos contractuales de adquisición, ya admitidos por F0, no superaron el umbral. La nueva pendiente de riesgo del ciclo 14 tampoco: R51 0,099645, R52 0,109081, R53 natural sin mezcla 0,115048; ninguno pasa el conjunto de controles. Potencias estimadas por fold: {powertext}. Las 16 variables categóricas físicas transferidas, excluida construcción, tienen los mismos dominios de 2023 en ambos mercados; el chequeo nuevo no encontró un error de categorías que justifique otra tanda.

El total propio es **684 intentos de ajuste de precios**, de los que 476 son adicionales desde G4 (473 en investigación y tres finales), incluyendo un intento numérico rechazado antes del ajuste aceptado. Son 31 variantes evaluadas en catorce ciclos, no 31 confirmaciones independientes. Los fits sintéticos y 445 constantes cerradas se contabilizan aparte. Nuevos C0 de esta investigación: cero. Los 29 candidatos que no pasan siguen guardados. El reporte recuperado del ciclo 1 conserva la limitación del digest de sorteos no archivado y la serialización fallida; no se repitieron sus ajustes o remuestreo para ocultarla.

## Entrega comprobada

| Variante | Envío propio Kaggle | Estado | Público |
| --- | ---: | --- | ---: |
| G4 original | 57628123 | COMPLETE | 0,13310 |
| R37 | 57629584 | COMPLETE | 0,13956 |
| R36 | 57629589 | COMPLETE | 0,14331 |

Competición: [IAA AI Assisted Hackathon 2026 Part 2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2). Solo se subieron predicciones propias autorizadas; código, modelos y datos siguen privados. Las dos variantes se cargaron antes de consultar cualquiera de sus nuevos scores. Se consumieron dos cupos; la última consulta autenticada dejó cuatro disponibles, sin afirmar que sea una cuota actualizada en este balance. No se enviaron las tandas adversas para perseguir el público.

Ambos CSV contienen 209.063 IDs únicos en orden oficial, columnas row_id/prediction y valores positivos finitos. SHA R36 b4ca8806b01bd5dfaab597774c5a4d1229e910a7638db0d1bc8bbff890d9baa2; R37 0f4ab80ec5b44e08cd457dae15e85ac0ce2910df132499be71051deb54b59cb6. Kaggle cotejó referencia, mensaje, nombre y tamaño; no devolvió SHA remoto. B00, B20 y el CSV G4 original permanecen conservados.

Paquete local: `{build['zip']}`, SHA {build['zip_sha256']}, {build['bytes']} bytes. Se verificó cada archivo comprimido por SHA y se extrajo en otra carpeta. El proceso separado `replay.py` leyó únicamente los modelos/cotizaciones/baseline incluidos, bloqueó fits y optimización, y reprodujo exactamente las 209.063 predicciones de cada CSV. Es validación de la nueva portabilidad del paquete; no repite entrenamiento, no vuelve a evaluar 2023 y no certifica rendimiento nuevo. ZIP y CSV están excluidos de Git. Recibo: `{rel(replaypath)}`.

## Límites y punto de continuación

La mejora pública es real pero modesta. Faltan prueba independiente de una ganancia pública grande, soporte emergente adicional legítimo y mejor identificación temporal de perfiles/último. Las carencias G1/G2 del contraste original no se resuelven con un score mejor: el mecanismo sigue plausible, el soporte retenido original falla en cinco de diez celdas y el soporte interno no queda establecido. No se presenta la transferencia como sustituto de ese soporte.

No hay una ejecución pendiente de estos catorce ciclos. El siguiente trabajo útil requiere una evidencia nueva de 2023 o una corrección material de origen que cambie una hipótesis, con procedencia y disponibilidad revisadas; no repetir estas recetas sobre fuentes iguales. La confirmación independiente sigue pendiente dentro del ámbito que pueda autorizarse, sin abrir 2024 en este trabajo. No se relajan los controles ni se inventa que el objetivo grande ya se alcanzó. El informe anterior de siete ciclos queda como corte histórico, con sus decisiones y recibos originales.

Índice de continuidad: `{rel(INDEX)}`. Resultados, fuentes SHA, configuraciones, modelos, OOF, replays, adversos y autoría real se conservan en privado/semana2/robustez2023.
'''
with DOC.open('x',encoding='utf-8') as f:f.write(doc)
def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key
 _,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]
changes=[]
def change(path,values=None,note=None):
 before=path.read_bytes();raw=before.decode('utf-8-sig');text=raw
 if values:
  old=json.loads(raw)
  for k,v in values.items():text=top(text,k,v)
  new=json.loads(text);assert {k:v for k,v in old.items() if k not in values}=={k:v for k,v in new.items() if k not in values}
 else:text=raw.rstrip()+note
 after=text.encode('utf-8');after=(b'\xef\xbb\xbf'+after) if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  p=OUT/'cuts'/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(data)
 tmp=path.with_name(path.name+'.balance14.tmp')
 with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
checkpoint={'utc':now(),'cycles':14,'variants':31,'price_fit_attempts_total':684,'new_fit_attempts_since_G4':476,'new_C0_fits_in_research':0,'passed':['W2-COD-R36','W2-COD-R37'],'large_public_gain_established':False,'2024_closed':True,'B00_preserved':True,'fits_running':False,'package':build,'package_replay':{'path':rel(replaypath),'sha256':sha(replaypath)},'no_manual_final_selection':True,'no_formal_promotion':True}
change(INDEX,{'utc':now(),'status':'research_checkpoint_public_gain_modest','documentation':rel(DOC),'documentation_sha256':sha(DOC),'checkpoint_14':checkpoint,'goal_large_public_improvement_achieved':False,'next_unit':'Review new legitimate2023 evidence or material source correction before another preregistered trial; do not repeat completed recipes on unchanged sources; independent confirmation remains pending;2024closed'})
statepath=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(statepath).get(key,{});branch.update({'status':'checkpoint_completed_not_running','completed_cycles':14,'latest_cycle':14,'index':rel(INDEX),'documentation':rel(DOC),'new_real_fit_attempts':476,'large_public_improvement_goal_achieved':False,'checkpoint_14':checkpoint});change(statepath,{key:branch})
change(ROOT/'RUTAS_PROYECTO.json',{'week_2_robustness_report':rel(DOC),'week_2_robustness_private_packet':build['zip']})
dev=R/'registro/semana2_desarrollo2023_actual.json';follow=read(dev).get('robustness2023_followup',{});follow.update({'index':rel(INDEX),'latest_cycle':14,'completed_cycles':14,'new_real_fit_attempts':476,'checkpoint_14_report':rel(DOC),'formal_promotion':False,'2024_closed':True});change(dev,{'robustness2023_followup':follow})
note=f'''\n\n## Robustez2023: balance de catorce ciclos, 25 de octubre de 2026\n\nCodex,{now()}. Mejor público propio observado R36 0,14331 (57629589,COMPLETE), antes G4 0,13310;R37 0,13956 también procesado. Ganancia pública modesta, salto grande no demostrado; no se declara objetivo alcanzado. R36/R37 son las únicas2de31variantes que pasan todas las cribas exploratorias de2023. Se preservan preferencia conservadora preinscrita R37, selección final manual y todas las alternativas/B00.\n\nCiclos8–14 adversos concluidos;no hay fits pendientes o ejecutándose. Contador propio684intentos de precios,476nuevos desdeG4incl1fallido;0C0nuevo en investigación,445constantescerradas aparte. No son observaciones independientes. Los perfiles fuente ausentes de25571periodos motor se conservaron;la construcciónW/w sigue excluida,no se identificó por intuición.\n\nNuevo paquete privado{build['zip']},SHA{build['zip_sha256']},extraído y reproducido exactamente con solo entradas incluidas y fits/optimización bloqueados,0ajustes/0envíosnuevos. ZIP/CSVexcluidosGit. Balance{rel(DOC)},índice{rel(INDEX)}. Siguiente trabajo requiere nueva evidencia2023o corrección material y receta previa;no repetir tandas sobre fuentesiguales ni afinar con el público. G1/G2originales y confirmación independiente siguen pendientes.2024cerrado;no ceguera completa ficticia,ni aprobación humana/profesional inventada,ni cambios aautomatizaciones,otroschats,delegaciónoremoto.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
with (OUT/'receipt.json').open('x',encoding='utf-8') as f:json.dump({'utc':now(),'checkpoint':checkpoint,'changes':changes,'report':rel(DOC),'report_sha256':sha(DOC),'new_fits_or_scores_during_balance':0},f,ensure_ascii=False,indent=2)
print(json.dumps({'report':rel(DOC),'cycles':14,'variants':31,'price_fits':684,'best_public':.14331,'large_goal_achieved':False,'2024_closed':True,'package_replay_success':True}))
