"""Corte sin ajustes: ciclos29–33, nuevo diagnóstico y bloqueo real de cuota."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re,os,sys,subprocess,importlib.metadata,platform
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/robustez2023';OUT=BASE/'comparacion_publica_hogar_20261025_v1';CUT=BASE/'mision017_20261025_v1/avance4'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat();changes=[]
assert not CUT.exists();missionp=R/'registro/semana2_mision017_actual.json';mission=read(missionp);counterp=R/'registro/semana2_contadores_propios_actual.json';counter=read(counterp)
assert counter['cumulative_price_base_fits']==1291 and counter['cumulative_diagnostic_classifier_fits']==15
assert [x['cycle'] for x in mission['new_cycles']]==list(range(15,34))
for n in range(29,34):
 p=BASE/f'ciclo{n}_20261025_v1';assert (p/'integration.json').exists() and (p/'forum_result_receipt.json').exists() and not any(x['all_pass'] for x in read(p/'report.json')['gates'])
domain=BASE/'prefiltro_dominio2023_v3';assert (domain/'integration.json').exists() and (domain/'forum_result_receipt.json').exists() and read(domain/'report.json')['diagnostic_classifier_fits']==15
quota_path=sorted((OUT/'quota_checks').glob('*.json'))[-1];quota=read(quota_path);assert quota['limits']['num_allowed_now']==0 and not quota['matching_own_submissions'];assert not list(OUT.glob('submission_started_*.json')) and not (OUT/'selected_frozen_batch.json').exists()
synthetic_path=OUT/'synthetic_actual_submitter_v2/report.json';synthetic=read(synthetic_path);assert synthetic['all_passed'] and synthetic['external_requests']==0 and synthetic['actual_submitter_sha256']==sha(ROOT/synthetic['actual_submitter'])
ready=read(OUT/'ready.json')
for x in ready['CSV']:assert sha(ROOT/x['path'])==x['sha256']
CUT.mkdir(parents=True)
retry=(datetime.fromisoformat(quota['utc'])+timedelta(minutes=60)).isoformat()
next_unit='C34 proposed,notimplemented/registered/fitted: motor-only densityweighted standard sourceGLM1.5 plus original residualtrees. Reuse each frozen domainmotorfoldk classifier;clipodds.2..5 then normalize sqrt-exposureweightedmean1fitonly,allcaseweightspositive. Beforeanypricefit gate combined sqrt(exposure)*density ESS/n>=.5 on all planned pilot/fullscopes;no thresholdrelaxation. Then five pairedsourcepilotblocks comparedtoC17samefamily with unweightedTweedie1.5 sourceveto(<=1.002pooled and>=4/5inside tolerance),followedonlyifeligible by fold-specificfullsource/targetfits,budget30pricefits,0newdomainfits,0C0. Freezecode/config/criteria/hypothesis andforum beforefit/score. KeephomeR36 asit failed domainoverlap;allR36primarygates unchanged. FrozenpublichomeCSVpriority/hashunchanged;recheckquota noearlierthan'+retry+' backoff,notclaimedreset;use enviar_comparacion_hogar2023_v2.py.'
queue={'utc':now(),'status':'pending_external_daily_quota','last_authoritative_quota':quota['limits'],'quota_utc':quota['utc'],'quota_receipt':rel(quota_path),'quota_receipt_sha256':sha(quota_path),'retry_not_before_utc':retry,'retry_is_backoff_not_verified_reset_time':True,'timing_deviation':'Lastquery17:02:22UTC was9seconds earlier than previousselfchosen30minbackoff;noPOSTornewscore. New60minbackoff anchoredtoactualreceipt;do not repeatquerynow.','CSV':ready['CSV'],'synthetic_flow_receipt':rel(synthetic_path),'synthetic_flow_sha256':sha(synthetic_path),'new_real_submissions':0,'new_public_scores':0,'failed2023gates_retained':True,'promotion':False,'2024_closed':True}
(OUT/'queue_followup4.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2),encoding='utf8')
progress={'utc':now(),'status':'active','target_public_score':.17,'goal_achieved':False,'best_processed_public_score':.14331,'completed_price_cycles':33,'mission_price_fits_CV':sum(x['new_price_fits'] for x in mission['new_cycles']),'mission_final_price_fits':1,'mission_total_price_fits':sum(x['new_price_fits'] for x in mission['new_cycles'])+1,'price_fits_total':1291,'closed_form_constants_total':670,'new_diagnostic_classifier_fits':15,'new_C0_fits_in_mission':0,'new_Kaggle_submissions_in_mission':0,'public_comparison':{'queue':rel(OUT/'queue_followup4.json'),'sha256':sha(OUT/'queue_followup4.json'),'status':queue['status']},'next_unit':next_unit,'B00_preserved':True,'2024_closed':True,'no_running_own_fit_jobs_in_reconciled_units':True,'forum_id':'COD-S2-20261025-MISION017-AVANCE4'}
assert progress['mission_total_price_fits']==607
def top(raw,key,value):
 v=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+v+'\n}\n'
 m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m;_,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+v+raw[m.end()+end:]
def change(path,values=None,note=None):
 before=path.read_bytes();raw=before.decode('utf-8-sig');text=raw
 if values:
  for k,v in values.items():text=top(text,k,v)
  assert {k:v for k,v in json.loads(raw).items() if k not in values}=={k:v for k,v in json.loads(text).items() if k not in values}
 else:text=raw.rstrip()+note
 after=text.encode('utf8');after=b'\xef\xbb\xbf'+after if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  p=CUT/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 tmp=path.with_name(path.name+'.m017advance4.tmp')
 with tmp.open('xb') as h:h.write(after);h.flush();os.fsync(h.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
change(missionp,{'utc':now(),'progress4':progress,'next_unit':next_unit,'status':'active','goal_achieved':False})
idx=R/'registro/semana2_robustez2023_actual.json';change(idx,{'next_unit':next_unit,'status':'mission017_active','domain_diagnostic':rel(R/'registro/semana2_dominio2023_actual.json')})
state=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(state).get(key,{});branch.update(status='active',latest_cycle=33,progress4=progress,next_unit=next_unit);change(state,{key:branch})
addition='''

## Avance hasta el ciclo 33: mejoras de fuente que aún no resuelven la estabilidad

Codex, 25 de octubre de 2026. El mejor público propio procesado permanece en 0,14331. Ninguna de las nuevas recetas pasa todas las cribas fijadas frente a R36; no se declara alcanzada la meta de 0,17 ni una sustitución robusta. B00 y todos los resultados adversos se conservan.

| Ciclo | Resultado comprobado en 2023 | Consecuencia |
| --- | --- | --- |
| 29, hogar con fuente enmascarada | La salida natural llega a D² 0,11727, pero mantiene incertidumbre e influencia | No se adopta |
| 30, correcciones GLM alpha1 | Ambas mezclas pierden en los cinco folds | Se conserva R36 |
| 31, curvas aditivas de fuente | El GLM mejora hogar; autos veta la receta global | No se ajusta destino en esta receta |
| 32, GLM aditivo solo hogar | Salida natural conjunta D² 0,11684, cuatro folds favorables; falla incertidumbre e influencia | No se adopta |
| 33, varianza de trabajo de fuente en autos | Mejora la pérdida fuente; la mejora emergente del residual mezclado es apenas 0,000087 de D² | No es una mejora material |

Los controles del flujo conservaron fuentes por hash, separación de grupos, clientes y direcciones, fórmulas y gradientes cotejados y replays desde disco. No sustituyen la evidencia estadística que sigue faltando. Los cinco ciclos suman 121 ajustes de precios desde el corte anterior. La misión reúne 606 ajustes de investigación más un ajuste final para los CSV pendientes; el contador propio acumulado es 1.291, con 670 constantes cerradas y ningún C0 nuevo en esta misión.

Antes de ajustar otra tanda de precios se midió una carencia distinta: la diferencia conjunta de atributos entre mercados. Quince clasificadores logísticos, sin cargar costes, exposición o C0, separan los mercados en los cinco folds de cada ramo. Solo autos pasa los criterios congelados de necesidad y solapamiento para considerar una prueba de ponderación. Edificios falla por cola emergente en dos folds y contenido por ESS y cola en los cinco. No se rebajan esos límites. La lectura falló en dos versiones antes de los ajustes reales; la tercera comprobó los dieciocho esquemas y la equivalencia de columnas brutas y transformadas. Los fallos, el código y sus recibos se conservan. El detalle está en DIFERENCIA_ATRIBUTOS_MERCADOS_2023.md. AUC de mercado y ESS no son resultados de predicción de siniestros ni pruebas de transporte.

La siguiente unidad propuesta es una ponderación de fuente limitada a autos, con un GLM estándar y el residual original, sin más variables o capacidad. Reutilizará clasificadores de dominio que excluyen el fold retenido, mantendrá positivos todos los pesos y primero comprobará el ESS al combinar densidad y exposición. Después requerirá los controles de fuente y las mismas cribas de precio contra R36. Todavía no está implementada, registrada o ajustada: debe congelar su configuración y dejar comentario previo antes de avanzar. Hogar permanece en R36 para esa prueba.

Los dos CSV de la comparación de hogar conservan sus hashes y prioridad, sin sustituirlos por resultados posteriores. La consulta autenticada de las 17:02:22 UTC sigue informando diez envíos usados hoy y cero disponibles. No hubo POST, score nuevo o rechazo de formato. El ejecutor real pasó seis escenarios simulados aislados, incluidos cuota agotada, tanda parcial y pérdida de respuesta, sin duplicación de POST o lectura anticipada de scores. Esa simulación no acredita procesamiento real de Kaggle. Los casos parciales se detienen y exigen conciliación exacta; no tienen reanudación automática.

La próxima consulta de cuota tiene una espera operativa de sesenta minutos desde ese recibo, no una hora de reapertura certificada. No se sondeará otro canal o cuenta. No se modifica ninguna automatización. La investigación permanece activa, sin promoción o selección final; 2024 continúa cerrado.
'''
change(R/'docs/semana2/MISION_017_SEGUIMIENTO.md',note=addition)
change(R/'docs/semana2/COMPARACION_PUBLICA_HOGAR_20261025.md',note='\n\nConsulta posterior: a las 17:02:22 UTC Kaggle volvió a informar diez envíos usados hoy y cero disponibles. Los archivos permanecen iguales y no se intentó POST. La cola posterior queue_followup4.json conserva el nuevo recibo y una espera de sesenta minutos, sin afirmar una hora de reapertura. El ejecutor vigente se probó con seis escenarios sintéticos aislados; esos resultados no equivalen a aceptación o scoring real.\n')
note=f'''\n\n## Misión0,17: avance4 hasta ciclo33 y prefiltro de dominio, 25 de octubre de2026\n\nCodex,{now()}. Ciclos29–33 terminales, integrados y con resultado en foro;ningún candidato nuevo pasa todas las cribas. No se repiten pilotos,bootstrap o replays ya terminados.607ajustes de precios en la misión(606investigación+1final),contador total1291/670constantes;15clasificadores diagnósticos aparte.0C0nuevos,0envíos nuevos. Mejor propio procesado0,14331;meta activa,no lograda. Fuente mejora sin transporte material;soloautos pasa el prefiltro de atributos para considerar una receta posterior, no aprobarla. Fallos de lectores v1/v2 preservados,0ajustes reales;v3terminó15clasificadores/replay.\n\nComparación pública congelada y sin POST:cuota0 en{quota['utc']};recibo{rel(quota_path)},SHA{sha(quota_path)}. El ejecutor real inalterado pasó seis escenarios simulados aislados,0red;no certifican scoring propio. Se corrigió la espera elegida tras consultar nueve segundos antes del anteriorbackoff:próximaconsulta no antesde{retry},esperaoperativa,noresetcertificado. Cola{rel(OUT/'queue_followup4.json')}. Nueva unidad C34 propuesta,noimplementada/registrada/ajustada:soloautos con pesos de densidad de clasificadores guardados y prueba previa ESS/n>=0,5 al combinar exposición;pilotos fuente antes de30fitsmáximos,misma métrica y cribas,sin nuevoC0oclasificadores. Requiere plan/código/foro antes de fit. No relajar filtros de hogar ni cambiar CSV ya congelados. Ningún trabajo propio reconciliado sigue corriendo. B00/alternativasconservadas,2024cerrado,sin promoción,remoto,delegación,otroschats,selecciónfinaloautomatizaciones. Informe{rel(R/'docs/semana2/MISION_017_SEGUIMIENTO.md')}.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
environment={'utc':now(),'python':sys.version,'platform':platform.platform(),'versions':{name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','scikit-learn','lightgbm','joblib']},'pyarrow_reader_path':str(ROOT/'Preparación/.cache/parquet-reader'),'no_package_changes':True}
(CUT/'environment.json').write_text(json.dumps(environment,ensure_ascii=False,indent=2),encoding='utf8')
body=CUT/'forum_body.txt';body.write_text(addition+'\nContinuidad: registro/semana2_mision017_actual.json, progress4; próxima consulta de cuota no antes de '+retry+'. Evidencia de flujo de envío: '+rel(synthetic_path)+', SHA '+sha(synthetic_path)+'. No se presentan sus scores sintéticos como públicos propios.\n',encoding='utf8')
r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',progress['forum_id'],'--asunto','Misión0,17: cinco ciclos conciliados, nuevo prefiltro y cuota aún agotada','--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8');forum=json.loads(r.stdout)
(CUT/'receipt.json').write_text(json.dumps({'utc':now(),'progress':progress,'queue':queue,'forum':forum,'changes':changes,'new_fits_in_consolidation':0,'new_submissions':0},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'active','achieved':False,'price_fits_total':1291,'mission_price_fits':607,'diagnostic_fits':15,'new_submissions':0,'retry_not_before':retry,'forum':forum}))
