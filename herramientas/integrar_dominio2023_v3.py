"""Integra solo el nuevo diagnóstico de atributos, separado del contador de precios."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/prefiltro_dominio2023_v3';assert not (OUT/'integration.json').exists()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat();changes=[]
report=read(OUT/'report.json');assert report['diagnostic_classifier_fits']==15 and report['price_fits']==0
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
  p=OUT/'integration_cuts'/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 tmp=path.with_name(path.name+'.domain2023.tmp')
 with tmp.open('xb') as h:h.write(after);h.flush();os.fsync(h.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(tmp,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})
record={'id':report['id'],'utc':now(),'report':rel(OUT/'report.json'),'report_sha256':sha(OUT/'report.json'),'diagnostic_classifier_fits':15,'price_fits':0,'C0_fits':0,'eligible_for_considering_weight_recipe':['motor'],'not_eligible':['buildings','contents'],'not_price_authorization_or_promotion':True,'2024_closed':True,'B00_preserved':True}
idx=R/'registro/semana2_dominio2023_actual.json';assert not idx.exists();idx.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
counter=R/'registro/semana2_contadores_propios_actual.json';c=read(counter);previous=c.get('mission017_domain_diagnostics',[]);assert not any(x['id']==record['id'] for x in previous);change(counter,{'mission017_domain_diagnostics':previous+[record],'cumulative_diagnostic_classifier_fits':c.get('cumulative_diagnostic_classifier_fits',0)+15,'as_of_utc':now()})
next_unit='C34 proposed,notfitted: motor-only densityweighted standard sourceGLM1.5 and same residualtrees;reuse frozen domainmotorfoldk classifier,clipodds.2..5 and normalize sqrt-exposuremean1fitonly;sourcepilot5blocks before full perouterfoldteachers/target;budget30pricefits,0newdomainfits,0C0. New preregistration/forum required beforepricefits. Home fails domainoverlap screen and staysR36;do not relaxscreens. PublicfrozenCSV pendingdailyquota,notbefore18:02:22UTCbackoff,notresetprediction.'
mission=R/'registro/semana2_mision017_actual.json';change(mission,{'domain_diagnostic2023':record,'next_unit':next_unit,'utc':now()})
state=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(state).get(key,{});branch.update(domain_diagnostic2023=record,next_unit=next_unit);change(state,{key:branch})
change(ROOT/'RUTAS_PROYECTO.json',{'week_2_domain_diagnostic2023_index':rel(idx)})
note=f'''\n\n## Misión0,17: diferencia conjunta de atributos2023, 25 de octubre de2026\n\nCodex,{now()}. Se midió una carencia distinta del solapamiento marginal:15 clasificadores logísticos por los mismos cinco bloques fuente/folds emergentes, sin cargar costes, exposición o C0. MotorAUC0,7155–0,7226,ESS/nmínimo0,5141,recorte máximo7,13% y cola emergente<3,46%:pasa el prefiltro congelado de necesidad/solapamiento para considerar una receta posterior, no aprobarla. EdificiosAUC0,6786–0,6905:incumple cola de probabilidad>0,95 en dos folds(5,18%/5,45% frente al máximo5%). ContenidoAUC0,7264–0,7337:ESS/n0,4760–0,4816 y cola>5% en los cinco folds, incumple. No se relajan límites ni se agrupan celdas para pasar. No se entrenaron precios o C0, no hubo envíos. Los15 clasificadores se cuentan por separado;el contador de precios permanece{c['cumulative_price_base_fits']}. Todos los objetos hicieron replay exacto.\n\nDos fallos previos se preservan:preparaciónv1 pidió región excluida,lecturav2 pidió franquicia log no almacenada. Ambos0 clasificadores reales/0precios. V3 proyecta solo columnas admisibles y deriva log1p de bruto no negativo;18esquemas y equivalencia sintética bruto/log comprobados antes del primer ajuste real. Se reutilizó la sonda logística sin repetirla;fuentes/códigos porSHA. Índice{rel(idx)};reporte{rel(OUT/'report.json')},SHA{sha(OUT/'report.json')}. AUC/ESS no prueban igualdad de costes condicionales ni transporte a último, independencia o validación profesional. B00/alternativas conservadas,2024cerrado. Siguienteunidad propuestaC34soloautos ponderado,requiere plan/foro propios antes de ajustar;no es orden humana nueva ni autorización por el informe.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,note=note)
dump={'utc':now(),'record':record,'changes':changes,'new_fits_during_integration':0}
(OUT/'integration.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'diagnostic_fits':15,'price_fit_counter_unchanged':c['cumulative_price_base_fits'],'index':rel(idx)}))
