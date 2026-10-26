"""Corte de recetas terminadas y consulta única aún viva, sin volver a ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,os,sys,subprocess
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/robustez2023';OUT=BASE/'comparacion_publica_hogar_20261025_v1';CUT=BASE/'mision017_20261025_v1/avance5'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat();changes=[]
assert not CUT.exists();missionp=R/'registro/semana2_mision017_actual.json';mission=read(missionp);counter=read(R/'registro/semana2_contadores_propios_actual.json');assert counter['cumulative_price_base_fits']==1336 and counter['cumulative_diagnostic_classifier_fits']==15
assert [x['cycle'] for x in mission['new_cycles']]==list(range(15,37))
for n in [34,35,36]:
 p=BASE/f'ciclo{n}_20261025_v1';assert (p/'integration.json').exists() and (p/'forum_result_receipt.json').exists() and not any(x['all_pass'] for x in read(p/'report.json')['gates'])
started=read(OUT/'single_deferred_quota_started.json');assert started['pid']==32136 and not (OUT/'single_deferred_quota_complete.json').exists();assert started['helper_sha256']==sha(R/'herramientas/enviar_comparacion_hogar2023_v2.py')
one=read(OUT/'synthetic_one_slot_v2/report.json');assert one['all_passed'] and one['external_requests']==0 and one['actual_submitter_sha256']==started['helper_sha256']
assert not list(OUT.glob('submission_started_*.json')) and not (OUT/'selected_frozen_batch.json').exists()
for x in read(OUT/'ready.json')['CSV']:assert sha(ROOT/x['path'])==x['sha256']
CUT.mkdir(parents=True)
job={'kind':'single_current_session_readonly_quota_preflight','exec_session_id':48990,'pid':32136,'not_before_utc':started['not_before_utc'],'started_receipt':rel(OUT/'single_deferred_quota_started.json'),'started_receipt_sha256':sha(OUT/'single_deferred_quota_started.json'),'last_confirmed_live_by_write_stdin_utc':'2026-10-25T17:49:08Z','last_poll_returned_same_live_session':True,'this_state_is_not_future_liveness_proof':True,'scheduled_app_automation_created':False,'new_price_fits':0,'new_submissions':0,'new_scores':0}
next_unit='Poll SAME live exec session48990/PID32136,which performs ONE authenticated preflight notbefore2026-10-25T18:02:22.672693UTC. Do not restart onobservationtimeout orlaunchanotherquotaquery;reconcile completion/quota_checks/markers. Ifavailable,selected immutableprefix naturalthenpool max2 is already authorized;submit with enviar_comparacion_hogar2023_v2.py submit,completeallselectedPOSTs beforereading anynewownscore;checkownrefs only. If0,recordrealblockwithoutCSV/weight/criterion changes oralternatechannel. C34/35/36done,do not repeatfits/suites/ESS. No furtherconcretepricehypothesisregistered atthiscut;do not invent fitsforcadence. Newlegitimatesourceevidence may be reviewed within2023scope;2024closed/B00kept.'
progress={'utc':now(),'status':'active_waiting_on_confirmed_live_readonly_process','target_public_score':.17,'goal_achieved':False,'best_processed_public_score':.14331,'completed_price_cycles':36,'mission_price_fits_CV':sum(x['new_price_fits'] for x in mission['new_cycles']),'mission_final_price_fits':1,'mission_total_price_fits':sum(x['new_price_fits'] for x in mission['new_cycles'])+1,'price_fits_total':1336,'closed_form_constants_total':670,'diagnostic_classifier_fits_total':15,'new_C0_fits_in_mission':0,'new_Kaggle_submissions_in_mission':0,'active_own_job':job,'next_unit':next_unit,'B00_preserved':True,'2024_closed':True,'all_registered_own_price_jobs_terminal':True,'forum_id':'COD-S2-20261025-MISION017-AVANCE5'}
assert progress['mission_total_price_fits']==652
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
 tmp=path.with_name(path.name+'.m017advance5.tmp')
 with tmp.open('xb') as h:h.write(after);h.flush();os.fsync(h.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
change(missionp,{'utc':now(),'progress5':progress,'next_unit':next_unit,'status':'active','goal_achieved':False})
change(R/'registro/semana2_robustez2023_actual.json',{'next_unit':next_unit,'status':'mission017_active_waiting_live_quota_read'})
state=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(state).get(key,{});branch.update(status='active_waiting_live_readonly_quota_job',latest_cycle=36,progress5=progress,next_unit=next_unit);change(state,{key:branch})
addition='''

## Avance hasta el ciclo 36: ponderación y faltantes sin mejora robusta

Codex, 25 de octubre de 2026. La meta sigue abierta: el mejor público propio procesado es 0,14331. Las tres recetas nuevas se registraron antes de probarse y conservaron B00, todas las alternativas y 2024 cerrado.

| Receta | Resultado comprobado | Decisión |
| --- | --- | --- |
| 34, ponderación directa de autos | ESS/n combinado con exposición entre 0,4776 y 0,4809, inferior a 0,5 en todos los ámbitos | Se detuvo antes de ajustar precios |
| 35, corrección moderada con potencia fija 0,5 | ESS/n cercano a 0,80 y filtro fuente favorable; todas las salidas pierden frente a R36 | No se adopta |
| 36, dos indicadores de faltantes por ramo con contracción fuerte | Mezcla D² 0,10962; natural 0,11496, pero falla las cribas de ganancia, incertidumbre, folds, segmentos e influencia | No se adopta |

El fallo de los pesos directos se confirmó por suma precisa y varianza, cotejando el mismo vector de pesos. La corrección moderada fue otra hipótesis, explícitamente distinta de una razón exacta de densidades; no convirtió la receta fallida en aprobada. Tampoco una mejora de fuente o un AUC de mercado alto acreditan transporte de costes. La prueba de faltantes añadió solo funciones de atributos ya admitidos. No estableció su mecanismo de ausencia o disponibilidad bitemporal, y no añadió campos futuros.

Los modelos nuevos conservaron la métrica Tweedie original, T0, exposición, C0 y los folds de 2023. Se cotejaron hashes, separación de grupos, fórmulas y replays desde disco. Los controles con indicadores a cero reprodujeron los quince modelos mínimos históricos y su OOF sin volver a ajustarlos. La misión acumula 652 ajustes de precios, incluidos 651 de investigación y uno final para la comparación preparada. El contador propio total es 1.336, con 670 constantes cerradas; los quince clasificadores diagnósticos siguen separados. En esta misión no hay nuevos C0 o envíos.

La consulta pública de inventario sigue mostrando dos temas con los mismos conteos y fechas de comentarios. Solo se cotejaron esos metadatos; no se afirma haber revisado nuevas versiones del diccionario o cuerpos, ni se descartan ediciones sin cambio de fecha. No surgió evidencia nueva de contenido con la que justificar otra receta de precios.

Los dos CSV de hogar conservan sus hashes y prioridad. Una consulta única de cuota está viva en el proceso de esta sesión y respetará la espera hasta las 18:02:22 UTC. Esa hora es un intervalo operativo, no una reapertura de cuota certificada. La última cuota real leída sigue siendo cero. Se confirmó el proceso activo, pero todavía no hay resultado nuevo de Kaggle. No se duplicará la consulta si una observación del proceso tarda o vence.

Se comprobó además el único caso operativo que faltaba: con un cupo, el ejecutor selecciona solo el primer CSV del orden congelado, hace un POST simulado y espera a completar esa tanda antes de leer el score simulado. No envía el segundo archivo. La prueba usó una API aislada, sin red, y no sustituye los dry-runs reales o un recibo de procesamiento. Se mantienen los seis controles operativos anteriores sin repetirlos.

El siguiente paso depende de esa consulta concreta: si existe cupo, enviar el prefijo ya fijado y verificar los recibos propios; con cero cupos, registrar el bloqueo externo. No se cambiarán pesos, criterios o archivos para perseguir un score, ni se encadenarán ajustes sin una necesidad nueva documentada. La investigación permanece activa y exploratoria, sin promoción, selección final o aprobación profesional independiente.
'''
change(R/'docs/semana2/MISION_017_SEGUIMIENTO.md',note=addition)
note=f'''\n\n## Misión0,17: avance5, ciclos34–36 y consulta viva, 25 de octubre de2026\n\nCodex,{now()}. C34directo fallaESS/n0,4776–0,4809 antes deprecios,0ajustes. C35moderado0,5 pasaESS~0,80pero pierde en destino;30ajustes. C36indicadoresdeausencia conridge10no supera R36enmezcla y falla las cribas tambiénnatural;15ajustes. Todos integrados y con foro;no repetir. Misión652ajustes(651investigación+1final),contador1336/670constantes,15clasificadores aparte;0C0nuevos y0envíos. Mejor propio procesado0,14331,meta no lograda. Solo metadatos públicos reconsultados,iguales;no se atribuye revisión de cuerpos/diccionario nuevos.\n\nProceso propio de consulta única y sololectura confirmado vivo por write_stdin a17:49:08UTC,sesión48990/PID32136,esperando hasta18:02:22,672693UTC. Marcador{rel(OUT/'single_deferred_quota_started.json')};no tratar archivo como prueba futura de vida:volverapollMISMOhandle,no reiniciar por timeout. No hay precios propios corriendo. No es hora de reset certificada ni una automatización periódica;no se modificó ninguna automatización de la app. CSV de hogar/hash/prioridad sin cambios. Nuevo control operativo de uncupopasa,sinred/POSTreal;los seis anteriores se conservan sin repetirse. Si llega cuota,prefijo inmutable ya autorizado y todosPOSTseleccionados antes de scores;solo recibos propios. Con cuota0 registrar bloqueo real,sin canal alterno o ejercicios inventados. No hay otra hipótesis concreta registrada al corte;el siguientehechopendiente es estaconsulta. B00/alternativasconservadas,2024cerrado,sin promoción,delegación,remoto,otroschats o selecciónfinal. Informe{rel(R/'docs/semana2/MISION_017_SEGUIMIENTO.md')}.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
body=CUT/'forum_body.txt';body.write_text(addition+'\nContinuidad: registro/semana2_mision017_actual.json, progress5; sesión de consulta48990/PID32136. El proceso debe conciliarse, no duplicarse.\n',encoding='utf8');r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',progress['forum_id'],'--asunto','Misión0,17: ponderación y faltantes adversos; consulta única de cuota en espera','--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8');forum=json.loads(r.stdout)
(CUT/'receipt.json').write_text(json.dumps({'utc':now(),'progress':progress,'active_job':job,'forum':forum,'changes':changes,'new_fits_during_cut':0,'new_submissions':0},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':progress['status'],'price_fits_total':1336,'mission_fits':652,'active_quota_session':48990,'goal_achieved':False,'forum':forum}))
