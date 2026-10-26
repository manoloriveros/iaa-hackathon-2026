"""Continuidad de la meta explícita0.17, preservando ramas y evidencia previa."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';P=R/'registro/semana2_mision017_actual.json';OUT=R/'privado/semana2/robustez2023/mision017_20261025_v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
action=sys.argv[1];cut=OUT/('inicio' if action=='start' else 'ciclo'+str(int(action)));assert not cut.exists();cut.mkdir(parents=True)
def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key
 _,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]
changes=[]
def change(path,values=None,note=None):
 before=path.read_bytes();raw=before.decode('utf-8-sig');text=raw
 if values:
  for key,value in values.items():text=top(text,key,value)
  assert {k:v for k,v in json.loads(raw).items() if k not in values}=={k:v for k,v in json.loads(text).items() if k not in values}
 else:text=raw.rstrip()+note
 after=text.encode('utf-8');after=(b'\xef\xbb\xbf'+after) if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  q=cut/phase/path.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write(data)
 tmp=path.with_name(path.name+'.mision017.tmp')
 with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
if action=='start':
 assert not P.exists()
 mission={'id':'S2-MISION017-v1-20261025','author':'Codex','utc':now(),'target_own_public_score':.17,'status':'active','user_instruction':'la misión es llegar a 0.17, sigue haciendo las mejoras que sean necesarias, pero que sean consistentes y robustas',
 'scope':'autonomous necessary local work and own authorized Kaggle submissions;2024closed,B00/allalternatives preserved;no remote/delegation/otherchat/automation changes',
 'best_own_processed_public':{'model_id':'W2-COD-R36-FINAL','submission':57629589,'score':.14331,'receipt':'Hackaton/Repositorio_IAA2026/privado/semana2/robustez2023/entrega_20261025_v1/public_check02.json'},
 'inherited_cycles':list(range(1,15)),'new_cycles':[],'goal_achieved':False,'promotion':False,
 'validation':'saved five2023componentfolds,T0/exposure/C0kept;criteria preregistered;group uncertainty/fold/segment/influence;fullflow+replay;exploratory after adaptive search',
 'next_unit':'cycle15: main-effect corrections strongly shrunk toward frozen physical source teacher; standardGLM, no new source fits or C0',
 'previous_checkpoint_not_a_human_fit_prohibition':True,'success_requires':'own COMPLETE Kaggle receipt >=0.17 and archived robust local evidence, not forecast or promise'}
 with P.open('x',encoding='utf-8') as f:json.dump(mission,f,ensure_ascii=False,indent=2)
 note=f'''\n\n## Misión0,17: instrucción directa del participante, 25 de octubre de 2026\n\nCodex,{now()}. El participante precisa: «la misión es llegar a0.17,sigue haciendo las mejoras que sean necesarias,pero que sean consistentes y robustas». Objetivo público propio>=0,17,partiendo deR36procesado0,14331. El corte anterior no es una prohibición humana de ajustar otra receta justificada. Se retoma trabajo autónomo autorizado;no se promete un score ni se declara éxito sin reciboCOMPLETEy evidencia local robusta. Índice{rel(P)}. Primera unidad nueva:GLMde correcciones físicas penalizadas10/100hacia profesor congelado,solo2023/folds guardados,0C0/0fuente nuevos;prerregistro antes deajustar. B00ytodaslasalternativas se conservan;2024cerrado,sin promoción/selecciónmanualfinal,delegación,remoto,otroschatsoautomatizaciones.\n'''
 for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
else:
 n=int(action);mission=read(P);rp=R/f'privado/semana2/robustez2023/ciclo{n}_20261025_v1/report.json';report=read(rp);assert all(x['cycle']!=n for x in mission['new_cycles']);cycles=mission['new_cycles']+[{'cycle':n,'report':rel(rp),'sha256':sha(rp),'gates':report['gates'],'summaries':report['summaries'],'new_price_fits':report['new_price_fits']}]
 change(P,{'utc':now(),'new_cycles':cycles,'status':'active','goal_achieved':False,'next_unit':'choose a distinct justified uncertainty based on latest report;do not rerun completedfits on unchanged inputs'})
 mission=read(P)
idx=R/'registro/semana2_robustez2023_actual.json';change(idx,{'status':'mission017_active','mission017':{'index':rel(P),'target':.17,'status':'active','best_processed_public':mission['best_own_processed_public'],'achieved':False},'next_unit':mission['next_unit']})
s=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(s).get(key,{});branch.update({'status':'active','mission017':rel(P),'target_public_score':.17,'goal_achieved':False,'2024_closed':True,'B00_preserved':True});change(s,{key:branch})
change(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_index':rel(P)})
with (cut/'receipt.json').open('x',encoding='utf-8') as f:json.dump({'utc':now(),'action':action,'changes':changes,'new_fits':0},f,ensure_ascii=False,indent=2)
print(json.dumps({'mission':rel(P),'target':.17,'status':'active','action':action,'new_fits':0}))
