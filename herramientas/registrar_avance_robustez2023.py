"""Punto de continuidad del estudio, dos entregas procesadas, sin nueva estimación."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/entrega_20261025_v1'
DOC=R/'docs/semana2/ROBUSTEZ_MODELO_2023_20261025.md';INDEX=R/'registro/semana2_robustez2023_actual.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key
 _,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]
def main():
 assert not (OUT/'registration_progress.json').exists()
 ready=read(OUT/'ready.json');public=read(OUT/'public_check02.json');replay=read(OUT/'separate_process_replay.json');idx=read(INDEX)
 assert replay['success'] and all(x['status']=='COMPLETE' and not x['error'] for x in public['results'])
 for x in ready['CSV']:assert sha(ROOT/x['path'])==x['sha256']
 entries=[]
 for cycle in idx['completed_cycles']:
  r=read(ROOT/cycle['report'])
  for row in r['summaries']:
   if not row['model_id'].startswith('W2-COD'):continue
   pair=next(p for p in r['pairs'] if p['candidate']==row['model_id']);gate=next(g for g in r['gates'] if g['model_id']==row['model_id'])
   entries.append({'cycle':cycle['cycle'],'model_id':row['model_id'],'D2':row['D2'],'delta_B20':pair['delta_D2'],'interval':pair['exploratory_interval'],'after31':pair['delta_after_removal'],'positive_folds':pair['positive_folds'],'all_pass':gate['all_pass']})
 table='\n'.join('| '+x['model_id']+' | '+f"{x['D2']:.5f}"+' | '+f"{x['delta_B20']:+.5f}"+' | '+str(x['positive_folds'])+'/5 | '+f"{x['after31']:+.5f}"+' | '+('Pasa' if x['all_pass'] else 'No pasa')+' |' for x in entries)
 publicrows='\n'.join('| '+x['model_id']+' | '+str(x['ref'])+' | '+x['public_score']+' | COMPLETE |' for x in public['results'])
 doc=f'''# Robustez del modelo: investigación2023 y entregas verificadas

El score público propio subió de 0,13310 a 0,13956 en la combinación conservadora y a 0,14331 en la combinación al50%. Es una mejora pública modesta. La investigación continúa para buscar un avance mayor con evidencia, sin ajustar pesos al leaderboard. Las dos nuevas recetas superaron todas las cribas exploratorias preinscritas de2023; eso no equivale a confirmación independiente ni a una promoción formal.

Codex, {now()}. El participante pidió autonomía hasta obtener un modelo más robusto y resultados significativamente mejores. Se mantuvieron B00 y todas las alternativas;2024 permanece cerrado. No se abrió la ventana nocturna anterior ni se cambiaron automatizaciones, chats, delegación o cómputo remoto.

## Qué mejoró

La mejor mejora que pasa las cribas es R36, con D² OOF2023 de0,11054 frente a0,08938 deB20. Su delta es+0,02115499, intervalo bootstrap exploratorio[0,01032137;0,03163706], mejora en los cincofolds y en los seis segmentos ramo/negocio. Tras retirar los31grupos más favorables como diagnóstico, el delta sigue en+0,00410578. R37, más conservador, también pasa: delta+0,01289871, intervalo[0,00702441;0,01857855] y+0,00337692 después de ese diagnóstico. Ningún siniestro se retiró de los ajustes.

Los pesos1/4y1/2 se fijaron antes de evaluar las mezclas y antes de ver cualquiera de sus nuevos scores públicos. Se combinan las raíces de los precios y luego se elevan al cuadrado. Para Tweedie1,5 la pérdida es convexa en sqrt(mu), lo que permite verificar una cota Jensen por fila. Esa propiedad no garantiza superar al mejor componente. No se probó una serie de factores de nivel en Kaggle.

## Resultados conservados

| Modelo | D²2023 | DeltaB20 | Foldsfavorables | Delta sin31grupos | Cribas |
| --- | ---: | ---: | ---: | ---: | --- |
{table}

Las cribas exigían delta>=0,005, límite inferior exploratorio>0,0005, al menos4folds favorables, daño máximo por ramo/negocio de0,0005de la desviación nula completa y delta>=0,0005tras retirar0,1%de grupos favorables. Bootstrap2000porcomponentes,semilla2026102501,cuantiles0,0041667/0,9958333 y nulo recalculado. Se conserva la búsqueda adaptativa completa: estos intervalos no corrigen todas las decisiones anteriores o la incertidumbre de la fuente transferida.

## Arquitectura y datos

Los primeros GLM ampliados, splines, PoissonGamma y árboles aprendidos directamente del pequeño mercado emergente no dieron mejoras estables. La transferencia lineal de2023mejoró todoslosfolds,pero seguía concentrada. El avance vino al aprender la forma en626.355periodos desarrollados de2023, con GLM estándar y una corrección de árboles de capacidad fija, y adaptar en el ajuste exterior emergente solo intercepto,nuevo negocioyregión. Los grupos desarrollados nunca se contaron como soporte emergente.

El componente de edificios excluye construcción: la fuente usa W/w, cuyo material no quedó confirmado en la revisión histórica, y el emergente dice timber. No se hizo esa equivalencia por intuición. Se conservaron las versiones previas y la advertencia. Motor y contenidos reutilizan exactamente sus profesores anteriores.

La fuente desarrollada tiene incurrido neto observado y exposición nominal reconciliada, con44siniestros2023sinperiodo asignable archivados por separado. Su nivel no se presenta como último identificado. En el emergente siguen T0,C0yexposición anteriores, con reserva1ycola no observada0condicionales. No se añadieron primas como predictores, clima realizado futuro o desocupación de ventana incierta. La disponibilidad histórica sellada de algunos atributos sigue sin acreditarse; es un benchmark condicionado a los datos suministrados, no una certificación de tarifa prospectiva.

## Entrega y procesamiento

| Modelo | Envío | Scorepúblico | Estado |
| --- | ---: | ---: | --- |
{publicrows}

La receta conservadoraR37 conserva la prioridad fijada antes de medir;R36 es una alternativa congelada. No se cambió la selección manual final de Kaggle. La página es [IAA2026Part2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2). Solo se leyeron los scores públicos de estos envíos propios. No se consultó privado, ni scores/mensajes ajenos, ni métricas,actas,ledger oSEL01de2024.

Cada CSV tiene209.063IDsúnicos en el orden oficial, columnasrow_id/prediction y valores positivos finitos. Tres adaptadores se ajustaron con las50.094filas completas de2023;los profesores,C0ycapitales se reutilizaron. Se verificó equivalencia numérica del adaptador con la receta deCV, coincidencia de capitales, preservación de las columnas basales y enriquecimiento físico2025solo después de los tresfits. Un proceso separado reconstruyó ambas entregas exactamente confit/optimización prohibidos y modelos intactos. Kaggle cotejó ID,competición,mensaje,nombre ytamaño;no devolvió SHA remoto.

Las dos cargas se hicieron antes de leer el nuevo score de cualquiera, consumieron2cuposy dejaron4en la última consulta. Se conservó el CSV originalSHAe5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab. Paquetes,código ydatos siguen locales/privados;solo se enviaron los CSV a la competición.

## Fallos y continuidad

Hubo una serialización incompleta después de30fits en eltanda1:se recuperaron los resúmenes/pares escritos sin repetir entrenamiento obootstrap;eldigest de sorteos no alcanzó a guardarse. La tanda2falló solo al imprimir el evento final, después de guardar reporte/manifiesto. En la transferencia se rechazó un intento por gradiente aunque eloptimizador informaba convergencia;se mantuvo1e-4y se aumentó precisiónftol,sin repetir15modelos aprobados. Se cuenta ese intento fallido.

Elestudio suma212intentos reales adicionales desdeG4(incluye1fallido), con15recetas y tresajustes finales;losfitssintéticos se registran aparte. Elcontadorpropio total queda420. Estos números describen coste, no evidencia predictiva independiente.

El avance público todavía no satisface el salto grande pedido. Próxima hipótesis: frecuencia y severidad porperil con denominadores de cobertura y exposición compatibles, manteniendo referencias y2024cerrado;requiere configuración/criterio previos y validación de toda la cadena. No se modifica una mezcla a partir del público. G1/G2 del ensayo de calibración original siguen abiertos;ninguno de estos resultados los borra.

Fuentesprimariasdelmétodo: [Tweedieenseguros](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html), [SplineTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.SplineTransformer.html). Lasversiones locales y los códigos ejecutados quedan fijados porSHA;no se actualizaron bibliotecas por ver documentación nueva. La revisión es propia deCodex, sin revisión actuarial profesional independiente o aprobación técnica humana inventada.

Índice `{rel(INDEX)}`;recibos2023enprivado/semana2/robustez2023/ciclo1..7_20261025_v1 yentrega_20261025_v1. Planes,modelos,OOF,replays,adversos,versionesfallidasyautoresseconservan.
'''
 DOC.parent.mkdir(parents=True,exist_ok=True)
 with DOC.open('x',encoding='utf-8') as f:f.write(doc)
 changes=[]
 def change(path,values=None,note=None):
  before=path.read_bytes();raw=before.decode('utf-8-sig');text=raw
  if values:
   old=read(path)
   for k,v in values.items():text=top(text,k,v)
   new=json.loads(text);assert {k:v for k,v in old.items() if k not in values}=={k:v for k,v in new.items() if k not in values}
  else:text=raw.rstrip()+note
  after=text.encode('utf-8');after=(b'\xef\xbb\xbf'+after) if before.startswith(b'\xef\xbb\xbf') else after
  for phase,data in [('before',before),('after',after)]:
   p=OUT/'progress_cuts'/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f:f.write(data)
  tmp=path.with_name(path.name+'.robust_progress.tmp')
  with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
  assert path.read_bytes()==before,'Concurrent change'
  os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
 counterpath=R/'registro/semana2_contadores_propios_actual.json';counter=read(counterpath);assert not counter.get('robustness_final_deployment')
 change(counterpath,{'as_of_utc':now(),'cumulative_price_base_fits':counter['cumulative_price_base_fits']+3,
   'robustness_final_deployment':{'real_price_fits':3,'source_fits':0,'C0_fits':0,'receipt':rel(OUT/'ready.json')}})
 deployment={'utc':now(),'models':ready['CSV'],'new_final_price_fits':3,'new_C0_fits':0,'public_results':public['results'],
  'public_receipt':{'path':rel(OUT/'public_check02.json'),'sha256':sha(OUT/'public_check02.json')},'replay':{'path':rel(OUT/'separate_process_replay.json'),'sha256':sha(OUT/'separate_process_replay.json')},'primary_per_prereg':'W2-COD-R37-FINAL','secondary_per_prereg':'W2-COD-R36-FINAL',
  'status':'processed_both_public_improvement_modest_research_continues','2024_closed':True,'B00_preserved':True,'promotion':False,'manual_final_selection':False}
 change(INDEX,{'status':'research_continues_public_gain_modest','documentation':rel(DOC),'documentation_sha256':sha(DOC),'final_scope_deployment':deployment,
  'next_unit':'preregister coherent peril frequency/severity hypothesis, source/target denominators and maturity;no additional public weight probes','goal_large_public_improvement_achieved':False})
 change(ROOT/'Preparación/ESTADO_PROYECTO.json',{'week_2_robustness2023_20261025':{'status':'active','index':rel(INDEX),'documentation':rel(DOC),'completed_cycles':7,
  'new_real_fit_attempts':212,'failed_attempts_included':1,'exploratory_screen_passed':['W2-COD-R36','W2-COD-R37'],'robust_replacement_formally_established':False,
  'public_results':public['results'],'large_public_improvement_goal_achieved':False,'2024_closed':True,'B00_preserved':True}})
 change(R/'registro/semana2_desarrollo2023_actual.json',{'robustness2023_followup':{'index':rel(INDEX),'completed_cycles':7,'new_real_fit_attempts':212,'public_delivery':deployment,'formal_promotion':False,'2024_closed':True}})
 note=f'''\n\n## Robustez2023: dosCSVprocesados, investigación continúa\n\nCodex,{now()}. R37envío57629584COMPLETEpúblico0,13956;R36envío57629589COMPLETEpúblico0,14331,frenteG40,13310.Ambasrecetas/pesoscongeladosantesdeverscores;R37prioridadconservadorafijada,R36alternativa,sinselecciónmanualfinalopromoción.Lamejorapúblicaesmodesta,objetivodegransaltoaúnnoalcanzado.\n\nCribasexploratorias2023pasadasR36yR37,5/5folds,6segmentosfavorables,gananciacon31gruposretirados.R36D²0,11053677vsB200,08938179,delta+0,02115499,intervalo[0,01032137;0,03163706],sin31grupos+0,00410578.R37D²0,10228050;no se confundeCVconpúblicooconfirmación.Lafuente2023noaumentasoporteemergente. ConstrucciónWnoidentificadacomotimber;seexcluyósoloedificios,conautoría/linajesguardados.\n\nTresadaptadoresfinales2023,0fuente/C0nuevo;212intentosrealesnuevostotalesincl1fallido,contadorpropio420.Sintéticosaparte.Replayde209063filasporCSVexactoenprocesoseparadoconfitsprohibidos;huellas/IDs/orden/columnaspreservados,tresfitsantesdeleerextras2025.B00/G4originaly demásalternativasinalterados.2024políticas/precios/scores/ledger/actas/SEL01cerrados,exposiciónajenapreviadeclarada,novalidaciónprofesionalindependiente.\n\nInforme{rel(DOC)},índice{rel(INDEX)},recibos{rel(OUT)}.Próximaunidad:hipótesisfrecuencia/severidadporperilcondenominadoresyobservacióncompatibles,antesdeotrofit.No se reoptimizaránpesosconelpúblico,ni se abrenotroschats/remoto/delegaciónoautomatizaciones.\n'''
 for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
 body=OUT/'forum_delivery_result.md'
 with body.open('x',encoding='utf-8') as f:f.write(doc)
 cp=subprocess.run([str(ROOT/'Preparación/.venv/Scripts/python.exe'),str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id','COD-S2-20261025-ROBUSTEZ-ENTREGA-RESULTADO','--asunto','Dos entregas robustas2023 procesadas, público0,13956/0,14331;avance modesto','--cuerpo',str(body)],capture_output=True,text=True,encoding='utf-8',check=True)
 forum=json.loads(cp.stdout)
 with (OUT/'forum_delivery_result_receipt.json').open('x',encoding='utf-8') as f:json.dump(forum,f,indent=2)
 with (OUT/'registration_progress.json').open('x',encoding='utf-8') as f:json.dump({'utc':now(),'shared_changes':changes,'forum':forum,'new_fits_during_registration':0,'large_public_improvement_achieved':False},f,indent=2)
 print(json.dumps({'forum':forum,'counter':counter['cumulative_price_base_fits']+3,'status':'research_continues','public_scores':[x['public_score'] for x in public['results']]}))


if __name__=='__main__':main()
