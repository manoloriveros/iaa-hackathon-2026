"""Integra evidencia propia de un ciclo sin repetir sus cálculos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,sys,subprocess
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
now=lambda:datetime.now(timezone.utc).isoformat()
num=int(sys.argv[1]);out=R/f'privado/semana2/robustez2023/ciclo{num}_20261025_v1'
rp=out/('report_recovered.json' if num==1 else 'report.json');d=read(rp)
assert not (out/'integration.json').exists(),'Ciclo ya integrado'
def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key
 _,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]
changes=[]
def change(p,values=None,note=None):
 before=p.read_bytes();raw=before.decode('utf-8-sig');old=json.loads(raw) if values else None
 aftertext=raw
 if values:
  for k,v in values.items():aftertext=top(aftertext,k,v)
  new=json.loads(aftertext);assert {k:v for k,v in old.items() if k not in values}=={k:v for k,v in new.items() if k not in values}
 else:aftertext=raw.rstrip()+note
 after=aftertext.encode('utf-8');after=(b'\xef\xbb\xbf'+after) if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  snapshot=out/'integration_cuts'/phase/p.relative_to(ROOT);snapshot.parent.mkdir(parents=True,exist_ok=True)
  with snapshot.open('xb') as f:f.write(data)
 tmp=p.with_name(p.name+f'.robust{num}.tmp')
 with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
 assert p.read_bytes()==before,'Concurrent change: '+str(p)
 os.replace(tmp,p);changes.append({'path':rel(p),'before':hashlib.sha256(before).hexdigest(),'after':sha(p)})
counterpath=R/'registro/semana2_contadores_propios_actual.json';c=read(counterpath)
entries=c.get('robustness_cycles',[]);assert all(x['cycle']!=num for x in entries)
entries=entries+[{'cycle':num,'utc':now(),'price_fits':d['new_price_fits'],'C0_fits':0,'report':rel(rp),'report_sha256':sha(rp)}]
updates={'as_of_utc':now(),'cumulative_price_base_fits':c['cumulative_price_base_fits']+d['new_price_fits'],'robustness_cycles':entries,
 'latest_robustness_index':'Hackaton/Repositorio_IAA2026/registro/semana2_robustez2023_actual.json'}
if d.get('new_closed_form_constants',0):updates['cumulative_closed_form_constants']=c['cumulative_closed_form_constants']+d['new_closed_form_constants']
change(counterpath,updates)
idxpath=R/'registro/semana2_robustez2023_actual.json';idx=read(idxpath)
history=idx.get('completed_cycles',[]);assert all(x['cycle']!=num for x in history)
record={'cycle':num,'report':rel(rp),'report_sha256':sha(rp),'fits':d['new_price_fits'],'new_closed_form_constants':d.get('new_closed_form_constants',0),'primary_reference':d.get('primary_reference','W2-B20'),'summaries':d['summaries'],'gates':d['gates'],'2024_closed':True,'B00_preserved':True}
history=history+[record]
passed=[x['model_id'] for x in d['gates'] if x['all_pass']]
passed_all=sorted({g['model_id'] for h in history for g in h['gates'] if g['all_pass']})
deployed_fits=c.get('robustness_final_deployment',{}).get('real_price_fits',0)+sum(x['new_price_fits'] for x in c.get('mission017_research_deployments',[]))
change(idxpath,{'status':'exploratory_robust_screens_passed_deployment_pending' if passed else ('research_continues_with_validated_incumbents' if passed_all else 'working_no_robust_replacement_yet'),'completed_cycles':history,'utc':now(),'new_fit_total':sum(x['fits'] for x in history),'new_deployment_fits':deployed_fits,'total_new_fit_attempts':sum(x['fits'] for x in history)+deployed_fits,'promotion':False,'exploratory_screen_passed':passed_all})
statepath=ROOT/'Preparación/ESTADO_PROYECTO.json';statekey='week_2_robustness2023_20261025'
branch=read(statepath).get(statekey,{})
branch.update({'status':'active','index':rel(idxpath),'latest_cycle':num,'completed_cycles':len(history),'own_new_fits':sum(x['fits'] for x in history)+deployed_fits,'2024_closed':True,'B00_preserved':True,'exploratory_screen_passed':passed_all,'robust_replacement_formally_established':False})
change(statepath,{statekey:branch})
change(ROOT/'RUTAS_PROYECTO.json',{'week_2_robustness_index':rel(idxpath),'week_2_robustness_report':'Hackaton/Repositorio_IAA2026/docs/semana2/ROBUSTEZ_MODELO_2023_20261025.md'})
devpath=R/'registro/semana2_desarrollo2023_actual.json'
change(devpath,{'robustness2023_followup':{'index':rel(idxpath),'latest_cycle':num,'new_fits':sum(x['fits'] for x in history),'formal_promotion':False,'2024_closed':True}})
own=[x for x in d['summaries'] if x['model_id'].startswith('W2-COD')]
short='; '.join(x['model_id']+' D²'+format(x['D2'],'.8f') for x in own)
primary=d.get('primary_reference','W2-B20');primary_score=next(x['D2'] for x in d['summaries'] if x['model_id']==primary)
replay_scope='replay emergente porfold exacto según recibos' if (out/'new_oof_2023.parquet').exists() else 'filtro de fuente;sin OOF o replay emergente nuevo'
screen_note=(('Pasan todas las cribas exploratorias preinscritas: '+', '.join(passed)+'. No es promoción formal o confirmación2024.') if passed else 'Ningún candidato de este ciclo pasa todas las cribas preinscritas de ganancia/incertidumbre/folds/segmentos/influencia.') if d['gates'] else 'El filtro de fuente detuvo la transferencia; no se calcularon nuevas cribas u OOF emergentes.'
note=f'''\n\n## Robustez2023: ciclo{num}, 25 de octubre de 2026\n\nCodex,{now()}. Nueva instrucción humana pide un modelo más robusto y mejoras significativas, con autonomía vigente. {short}. Comparador{primary} D²{primary_score:.8f};B00conservado. {screen_note} Evidencia {rel(rp)},SHA{sha(rp)};índice {rel(idxpath)}. {d['new_price_fits']}ajustes nuevos,{d.get('new_closed_form_constants',0)}parámetroscerradosnuevos,0C0,0envíos;{replay_scope} y códigos/fuentes preservados. Evidencia exploratoria/adaptativa;sin promoción o aprobación profesional. 2024 sigue cerrado;no se modifican otros chats,delegación,remotooautomatizaciones. Se mantienen modelos anteriores y adversos.\n'''
if num==1:note+='\nFallo de serialización numpy preservado;reporte recuperado desde resúmenes/pares ya escritos,sin repetirfitobootstrap.Digestdelosdrawsnoarchivado,indisponible.\n'
if num==2:note+='\nReporte/manifiesto completos guardados;el evento final de consola falló por serializar numpy.bool_. No repitefit,puntuaciónoremuestreo;recibo separado certifica solo lectura de los resultados existentes.\n'
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
receipt={'utc':now(),'cycle':num,'new_fits':d['new_price_fits'],'report':rel(rp),'report_sha256':sha(rp),'shared_changes':changes,'new_fits_during_registration':0,'2024_closed':True,'B00_preserved':True}
with (out/'integration.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2,ensure_ascii=False)
print(json.dumps({'cycle':num,'price_fits_total':updates['cumulative_price_base_fits'],'new_fits_this_cycle':d['new_price_fits'],'all_gates_pass':[x['all_pass'] for x in d['gates']]}))
