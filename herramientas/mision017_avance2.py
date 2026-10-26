"""Consolidar hasta ciclo25 y dejar una continuación concreta sin repetir cálculos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/robustez2023';CUT=BASE/'mision017_20261025_v1/avance2';assert not CUT.exists();CUT.mkdir(parents=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat();changes=[]
missionpath=R/'registro/semana2_mision017_actual.json';mission=read(missionpath);counter=read(R/'registro/semana2_contadores_propios_actual.json');assert [x['cycle'] for x in mission['new_cycles']]==list(range(15,26));assert counter['cumulative_price_base_fits']==1101
for n in range(20,26):
 folder=BASE/f'ciclo{n}_20261025_v1';assert (folder/'report.json').exists() and (folder/'integration.json').exists() and (folder/'forum_result_receipt.json').exists()
fits=sum(x['new_price_fits'] for x in mission['new_cycles']);assert fits==417
numeric=BASE/'mision017_20261025_v1/numeric_overlap2023_v3.json';nr=read(numeric);assert nr['constant_controls_passed']
next_unit='C26 pending,not preregistered or fitted: test fixed10%additional source measurement-missingness on the six affected numeric line/field pairs,with standard physical GLM and existing smalltreecapacity;preserveoriginals/allcosts,entity-stable labelindependent masks,compare original+masked source5blockcosts before2023target CV. Freeze configuration/criteria and post beforefit;no newC0,no2024. Do not repeatcompletedcycles.'

def top(raw,key,value):
 encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
 if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
 ma=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert ma,key
 _,end=json.JSONDecoder().raw_decode(raw[ma.end():]);return raw[:ma.end()]+encoded+raw[ma.end()+end:]

def change(path,values=None,transform=None):
 before=path.read_bytes();raw=before.decode('utf-8-sig');text=raw
 if values:
  for key,value in values.items():text=top(text,key,value)
  assert {k:v for k,v in json.loads(raw).items() if k not in values}=={k:v for k,v in json.loads(text).items() if k not in values}
 else:text=transform(raw)
 after=text.encode('utf-8');after=b'\xef\xbb\xbf'+after if before.startswith(b'\xef\xbb\xbf') else after
 for phase,data in [('before',before),('after',after)]:
  p=CUT/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 stage=path.with_name(path.name+'.avance017-2.tmp')
 with stage.open('xb') as h:h.write(after);h.flush();os.fsync(h.fileno())
 assert path.read_bytes()==before,'Concurrent change';os.replace(stage,path);changes.append({'path':rel(path),'before':hashlib.sha256(before).hexdigest(),'after':sha(path)})

doc=R/'docs/semana2/MISION_017_SEGUIMIENTO.md'
addition='''

## Avance hasta el ciclo25

Este corte sustituye la continuación de edad que figuraba en el corte del ciclo19. La edad ya se revisó y probó; ninguna de las nuevas tandas supera todos los criterios. El mejor score público propio procesado sigue en 0,14331. No se ha alcanzado 0,17 ni se ha hecho un envío adicional en esta misión.

| Ciclo | Cambio | Resultado comprobado |
| --- | --- | --- |
| 20 | Integrar edad exacta de fuente sobre bandas desconocidas | Mejor D² 0,116487, pero falla incertidumbre, influencia y autos nuevos |
| 21 | Coste limitado más exceso, conservando todo el coste | Falla contenido en fuente; sin ajuste o score emergente |
| 22 | Marca/modelo, hipoteca, trabajo desde casa y huéspedes | GLM pasa fuente; mejor D² emergente 0,104984. Árboles vetados en fuente |
| 23 | Contracción 0,1/10 del GLM mínimo de adaptación | La mezcla de mayor contracción mejora cuatro folds, pero solo +0,000842 y con dependencia de pocos grupos |
| 24 | Reducir a 0,1 la penalización del GLM de fuente | Mejor mezcla D² 0,110756; salida natural 0,116169 falla controles conjuntos |
| 25 | Frecuencia Poisson por coste medio Gamma | Ambas familias fallan el filtro fuente; sin ajuste o score emergente |

La referencia OOF2023 sigue en D²0,110537. Desde el inicio de esta misión, los ciclos15–25 suman417 ajustes reales de precio; el contador propio acumulado es1101 y las constantes cerradas670. Cero C0 nuevos y cero envíos nuevos en esta misión. Los pilotos vetados no se presentan como modelos puntuados en emergente. Los resultados adversos permanecen disponibles. Las comparaciones son exploratorias después de búsqueda adaptativa y no validación profesional independiente.

El enlace del ciclo22 se detuvo antes del primer ajuste emergente por columnas ya presentes. Se comprobó igualdad por clave en los15 archivos estrictos y se conservaron sus valores y tipos originales;31 ajustes guardados se reutilizaron sin repetirse. La continuación añadió17:48 en total, no79. La versión y el fallo se conservan. Cada receta y corrección se anotó en el foro antes de su ajuste correspondiente.

Una precisión de registro: la integración automática original del ciclo21 decía de forma genérica «replay porfold exacto». No hubo adaptadores/OOF emergentes en ese ciclo y no existe ese replay. El resultado que lo detuvo fue exclusivamente el filtro fuente. Esta aclaración conserva el original y corrige su alcance; el registrador ya distingue ambos casos.

## Diferencia de medición pendiente de tratar

La nueva auditoría numérica leyó únicamente claves, atributos y exposición nominal de2023, sin costes, reservas o predicciones. Reutilizó el inventario categórico anterior, sin repetirlo. Las diferencias marginales observadas son moderadas y no acreditan soporte conjunto ni igualdad de mecanismo entre mercados. Solo una observación de cilindrada queda por debajo del mínimo fuente (500 frente a600cc); no se elimina ni se corrige por ese hecho.

La diferencia más concreta es de faltantes: edad del vehículo y cilindrada en autos; alarmas y distancia al río en edificios; objetos de valor y distancia al río en contenido. Pasan de alrededor de2,5% en fuente a11,6–12,2% en emergente. Esto puede afectar a la mediana y a las rutas de faltantes del profesor; no demuestra que los datos ausentes sean aleatorios o tengan el mismo mecanismo.

El primer lector de la auditoría falló al pedir logaritmos que se derivan en memoria en algunos archivos. Se conservó y corrigió sin leer etiquetas. Después se detectó ruido de coma flotante al estandarizar franquicias obligatorias constantes: eran exactamente iguales. Se corrigieron únicamente esos resúmenes a media constante/desviación cero, sin releer datos, entrenar o cambiar modelos. La fuente vigente es numeric_overlap2023_v3.json; los resúmenes anteriores se conservan y no justifican decisiones.

La siguiente unidad propuesta es comprobar tolerancia a faltantes mediante una vista separada de fuente con10% adicional de enmascaramiento fijo, independiente de etiquetas y estable por entidad, solo en los seis pares ramo/campo señalados. Se conservarían los datos originales y todos los costes, con los mismos GLM y capacidad pequeña de árboles. Requiere receta/configuración/criterios congelados y comentario previo antes de ajustar. El control fuente deberá comparar las mismas filas completas y enmascaradas en los cinco bloques antes de permitir adaptación emergente. No se supone MCAR verdadero ni se modifica C0. Todavía no hay receta de este ciclo26 registrada ni ajuste iniciado.

Este corte no cambia las restricciones: B00 y todas las alternativas conservadas;2024 cerrado para precios/cohortes/métricas/ledger/SEL01/actas. No hay promoción formal, selección manual final, entrenamiento remoto, mensajes a otros chats o cambios de automatizaciones. El objetivo sigue activo y solo se acreditará con un recibo propio procesado de Kaggle >=0,17 acompañado de evidencia local robusta.

Evidencia actual: registro/semana2_mision017_actual.json; recetas de ciclos20–25, informes y recibos en privado/semana2/robustez2023/ciclo20..25_20261025_v1; auditoría vigente privado/semana2/robustez2023/mision017_20261025_v1/numeric_overlap2023_v3.json. Los hashes completos permanecen en registros y manifiestos.
'''
change(doc,transform=lambda s:s.replace('## Siguiente unidad pendiente','## Continuación prevista en el corte del ciclo19, ya resuelta')+addition)
progress={'utc':now(),'status':'active','target_public_score':.17,'best_processed_public_score':.14331,'mission_new_cycles_completed':list(range(15,26)),'mission_new_price_fits':417,'price_fits_total':1101,'closed_form_constants_total':670,'new_Kaggle_submissions':0,'2024_closed':True,'B00_preserved':True,'goal_achieved':False,'latest_numeric_audit':{'path':rel(numeric),'sha256':sha(numeric)},'next_unit':next_unit,'documentation':rel(doc),'forum_id':'COD-S2-20261025-MISION017-AVANCE2','no_running_fits_from_completed_cycles':True}
change(missionpath,{'utc':now(),'next_unit':next_unit,'progress2':progress,'status':'active','goal_achieved':False})
change(R/'registro/semana2_robustez2023_actual.json',{'next_unit':next_unit,'mission017_progress2':progress})
state=ROOT/'Preparación/ESTADO_PROYECTO.json';key='week_2_robustness2023_20261025';branch=read(state)[key];branch.update(mission017_progress2=progress,documentation=rel(doc));change(state,{key:branch})
note=f'''\n\n## Misión0,17: avance2, ciclos15–25 conciliados\n\nCodex,{now()}. Meta activa y no lograda;mejor recibo público propio0,14331. Ciclos15–25:417 ajustes reales adicionales,contador1101,constantes670,0C0/0envíos nuevos en esta misión. Ninguna tanda nueva pasa todos los criterios;21y25se detienen en fuente sin OOF/score emergente. Corrección de alcance:el texto genérico original de integración21sobre «replay porfold exacto»no acredita replay emergente inexistente;se conserva y aclara. Ciclo22:31ajustes reutilizados sin repetición,17adicionales,total48. Solapamiento numérico2023sin etiquetas,fuente vigente{rel(numeric)},SHA{sha(numeric)};faltantes fuente~2,5%frente a~12%emergente en seisparesramo/campo. Se preservan lector fallido y resúmenes con ruido de constantes;v3corrige solo ese resumen,sin cambiar modelos. Siguienteunidad propuesta:C26enmascaramiento fijo10%adicional,misma complejidad,controles de fuente completa/enmascarada;sin receta/fit iniciado todavía. Documentación{rel(doc)}. B00/alternativas conservadas,2024cerrado,sin promoción formal o aprobación humana;análisisexploratorio/adaptativo. No hay cambios a otras conversaciones,delegación,remotooautomatizaciones.\n'''
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,transform=lambda s:s.rstrip()+note)
body=CUT/'forum_body.txt';body.write_text('Codex consolida los ciclos20–25, con todas las recetas/resultados en el foro. Desde el inicio de la misión, los ciclos15–25 suman417 ajustes reales; contador propio1101 y constantes670. Cero C0 nuevos y cero envíos nuevos en esta misión. Ninguna alternativa nueva supera todos los criterios. Los ciclos21/25 se detuvieron en fuente y no tienen score emergente. Mejor público propio procesado0,14331; objetivo0,17 no logrado y misión activa.\n\nLa auditoría numérica nueva, sin etiquetas, detecta el aumento de faltantes fuente~2,5% a emergente~12% en seis pares de ramo/campo. Los rangos marginales se solapan casi completamente; no se acredita soporte conjunto o mismo mecanismo. Un falso desplazamiento de franquicias constantes por coma flotante se corrigió en numeric_overlap2023_v3.json sin cambiar modelos o releer datos. Los borradores anteriores se conservan.\n\nSiguiente unidad concreta, todavía sin receta/fit: contrastar una vista de fuente con10% adicional de faltantes fijos e independientes de etiquetas, conservando todos los costes y la complejidad actual. Requiere congelar receta y criterios, comentar antes deajustar y validar primero las mismas filas completas/enmascaradas en los cinco bloques fuente. No se supone MCAR verdadero ni se estiman C0 nuevos.\n\nSe aclara el texto automático del ciclo21:sin adaptadores/OOF emergentes no hay replay emergente. En ciclo22se reutilizaron31ajustes,la continuación añadió17,total48. B00y todas las alternativas conservadas;2024cerrado. Sin promoción formal,aprobación humana,validación independiente,remoto,otroschats o automatizaciones. Balance actualizado:docs/semana2/MISION_017_SEGUIMIENTO.md. Evidencia y punto de continuación:registro/semana2_mision017_actual.json.\n',encoding='utf-8')
result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',progress['forum_id'],'--asunto','Misión0,17: 25 ciclos conciliados y siguiente incertidumbre de medición','--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf-8');forum=json.loads(result.stdout)
with (CUT/'receipt.json').open('x',encoding='utf-8') as h:json.dump({'utc':now(),'progress':progress,'forum':forum,'changes':changes,'new_fits_in_consolidation':0},h,ensure_ascii=False,indent=2)
print(json.dumps({'status':'active','goal_achieved':False,'latest_cycle':25,'new_fits':0,'mission_fits':417,'counter':1101,'forum':forum}))
