"""Contar una sola vez el ajuste final de investigación; no cambiar elegibilidad."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';CUT=OUT/'integration_fit';assert not CUT.exists();CUT.mkdir(parents=True);changes=[]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key;_,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]
def change(p,values):
 before=p.read_bytes();raw=before.decode('utf-8-sig');text=raw
 for key,value in values.items():text=top(text,key,value)
 assert {k:v for k,v in json.loads(raw).items() if k not in values}=={k:v for k,v in json.loads(text).items() if k not in values};after=text.encode('utf-8');after=b'\xef\xbb\xbf'+after if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  f=CUT/phase/p.relative_to(ROOT);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
 stage=p.with_name(p.name+'.home27-fit.tmp')
 with stage.open('xb') as h:h.write(after);h.flush();os.fsync(h.fileno())
 assert p.read_bytes()==before,'Concurrent change';os.replace(stage,p);changes.append({'path':rel(p),'before':hashlib.sha256(before).hexdigest(),'after':sha(p)})
receipt=read(OUT/'training_receipt.json');assert receipt['price_estimator_fits']==1
record={'id':'HOME27-RESEARCH-FINAL-v1','utc':now(),'new_price_fits':1,'newsource':0,'newC0':0,'training_receipt':rel(OUT/'training_receipt.json'),'training_receipt_sha256':sha(OUT/'training_receipt.json'),'ready':rel(OUT/'ready.json'),'ready_sha256':sha(OUT/'ready.json'),'recipe':rel(R/'registro/semana2_comparacion_publica_hogar_plan_v2.json'),'research_only':True,'gates_remain_failed':True,'promotion':False}
p=R/'registro/semana2_contadores_propios_actual.json';counter=read(p);history=counter.get('mission017_research_deployments',[]);assert all(x['id']!=record['id'] for x in history);change(p,{'as_of_utc':now(),'cumulative_price_base_fits':counter['cumulative_price_base_fits']+1,'mission017_research_deployments':history+[record]})
p=R/'registro/semana2_robustez2023_actual.json';idx=read(p);allfinal=counter.get('robustness_final_deployment',{}).get('real_price_fits',0)+sum(x['new_price_fits'] for x in history)+1;total=sum(x['fits'] for x in idx['completed_cycles'])+allfinal;change(p,{'new_deployment_fits':allfinal,'total_new_fit_attempts':total,'research_public_home':record,'next_unit':'frozenhome researchcomparison:finish fullreplay,dryrun,livequota and boundedbatch;preservefailedgates and2024closed'})
p=R/'registro/semana2_mision017_actual.json';mission=read(p);change(p,{'utc':now(),'status':'active','goal_achieved':False,'research_public_comparisons':mission.get('research_public_comparisons',[])+[record],'next_unit':'finish frozen home-only researchcomparison,notpromotion;1finalfitdone,2CSVs frozen,ownCOMPLETEscoresneeded;2024closed'})
p=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(p)[key];branch.update(research_public_home=record,own_new_fits=total,goal_achieved=False);change(p,{key:branch})
note=f'''\n\n## Misión0,17: ajuste final de comparación pública de hogar\n\nCodex,{now()}. Se registra una excepción operativa de investigación autorizada por la petición explícita de envío propio y autonomía,sin promoción o relajación de las cribas2023fallidas. Un solo GLM conjunto de hogar tau20ajustado en28414periodos2023con profesores/C0existentes;dos salidas ya fijadas,R104natural yR102mezcla50/50soloenhogar. Autos copia exactamente90521preciosR36. Coste real1ajuste,0fuente/0C0;contador{counter['cumulative_price_base_fits']+1}. Receta{record['recipe']};modelo/CSV/hash/validaciones en{rel(OUT)}. La fuente ytodosloscriterios/alternativasB00permanecen;2024cerrado. No se declara robustez oaprobaciónhumana,niéxitosinrecibopropioCOMPLETEyrobustezevidenciada. Pendientesdryrun/cuota/envíoscotadosyrecibos;sin selecciónmanualfinal.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
 p=ROOT/'Preparación'/name;before=p.read_bytes();after=before+note.encode('utf-8');stage=p.with_name(p.name+'.home27-fit-note.tmp');stage.write_bytes(after);assert p.read_bytes()==before;os.replace(stage,p)
with (CUT/'receipt.json').open('x',encoding='utf-8') as h:json.dump({'utc':now(),'record':record,'counter':counter['cumulative_price_base_fits']+1,'changes':changes,'new_fits_in_registration':0},h,ensure_ascii=False,indent=2)
print(json.dumps({'counter':counter['cumulative_price_base_fits']+1,'new_final_fit':1,'new_C0':0,'promotion':False}))
