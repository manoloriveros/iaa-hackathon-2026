"""Registro previo y posterior con autoría propia y bloqueo del foro."""
from pathlib import Path
import sys,json,hashlib,subprocess
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/robustez2023'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def post(n,kind,body,subject):
 out=BASE/f'ciclo{n}_20261025_v1';p=out/f'forum_{kind}_receipt.json';assert not p.exists()
 bodypath=out/f'forum_{kind}_body.txt'
 with bodypath.open('x',encoding='utf-8') as h:h.write(body)
 ident=f'COD-S2-20261025-ROBUSTEZ{n}-'+('PREVIO' if kind=='prior' else 'RESULTADO')
 result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',ident,'--asunto',subject,'--cuerpo',str(bodypath)],check=True,capture_output=True,text=True,encoding='utf-8');receipt=json.loads(result.stdout)
 with p.open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2)
 print(json.dumps(receipt))

if __name__=='__main__':
 n=int(sys.argv[1])
 if n==21:
  path=BASE/'ciclo21_20261025_v1/report.json';report=read(path)
  lines=['La receta R78–R81 se detiene por su filtro previo de fuente, tal como se registró. No se ha ajustado ningún adaptador emergente ni la fuente completa. El coste limitado más el exceso conserva exactamente el coste original, pero esa identidad no acredita capacidad predictiva.','', '| Ramo | Cambio relativo de pérdida completa | Filtro previo |','|---|---:|---|']
  for row in report['source_pilots']:lines.append(f"| {row['line']} | {100*row['relative_difference']:.6f}% | {row['pass']} |")
  lines+=['',f"Se hicieron {report['new_price_fits']} ajustes piloto reales y cero C0 nuevos. El empeoramiento de contenido supera el máximo de +0,2%; por ello no se flexibiliza el criterio para continuar. No hay predicciones, score emergente, CSV o envío nuevos. Se conservan modelos y resultados adversos. La misión 0,17 sigue activa; el mejor recibo público propio continúa en 0,14331. B00 y todas las alternativas permanecen; 2024 cerrado. Revisión exploratoria propia, no validación independiente.",'',f"Evidencia: privado/semana2/robustez2023/ciclo21_20261025_v1/report.json, SHA256 {sha(path)}. Próxima unidad distinta: comprobar atributos contractuales ya admitidos pero omitidos del profesor físico, con cinco bloques fuente antes de validación emergente."]
  post(21,'result','\n'.join(lines),'Misión 0,17: capas detenidas en el filtro de fuente; sin ajuste emergente')
 elif n==22:
  p=R/'registro/semana2_robustez2023_ciclo22_plan.json';s=BASE/'ciclo22_20261025_v1/synthetic.json';assert read(s)['synthetic_price_fits']==12
  body='''Se registra antes de ajustar con datos reales R82–R85. Los profesores físicos actuales omiten marca/modelo de autos, hipoteca en edificios y trabajo desde casa/huéspedes en contenido. La auditoría comprobó disponibilidad contractual F0 en los periodos de 2023 y enlaces completos dentro de cada mercado, conservando todas las columnas anteriores; cero filas de pólizas 2024. Los 300 códigos de marca/modelo están presentes en ambos mercados, pero su coincidencia no demuestra igualdad del efecto de riesgo. No se enlazan registros entre mercados ni se añade soporte emergente con la fuente desarrollada.

R82 mantiene el GLM Tweedie 1,5 alpha 1 con efectos principales y las transformaciones anteriores. Solo se amplía el máximo de categorías de 40 a 400 para conservar los 300 códigos. R83 añade el residual anterior de 200 árboles, profundidad 3, ocho hojas, tasa 0,025, mínimo 5.000 y penalizaciones L2 500/L1 100, semilla 2026102506. Región de fuente y construcción en edificios siguen excluidas. No hay más capacidad de árboles ni variables nuevas basadas en primas, resultados posteriores o clima realizado.

Primero, cinco bloques guardados de fuente, con sus componentes completos retenidos y referencia C17 de la misma familia en los mismos periodos. Para admitir una familia deben pasar todos los ramos: pérdida completa conjunta de sus cinco bloques <= 1,002 veces la referencia y al menos cuatro bloques dentro de esa tolerancia. Los bloques ya se han observado en la búsqueda adaptativa; no son confirmación independiente. Si una familia falla, no produce salida emergente. Presupuesto máximo: 30 ajustes piloto, seis de fuente completa y 30 adaptadores; 66 en total, cero C0 nuevos.

Adaptadores mínimos de 2023: intercepto libre, negocio y región ridge 1, cinco folds guardados, T0/exposición/C0 sin cambios. R82/R83 mezclan raíces 50/50 con B20 como R36; R84/R85 conservan salidas naturales. Pesos fijos, sin optimización. Referencia R36, diferencia D² >= 0,005, límite inferior exploratorio > 0,0005, cuatro folds positivos como mínimo, daño por ramo/negocio <= 0,0005 del denominador nulo total y diferencia >= 0,0005 tras los 31 grupos más favorables (diagnóstico sin eliminarlos del ajuste o métrica principal). Remuestreo de 2.000 grupos, semilla 2026102501, cuantiles 0,0041666666667/0,9958333333333. Preferencia previa R82, R83, R84, R85 solo si pasan todos los criterios.

Doce ajustes sintéticos cubrieron los tres ramos, ambas familias y los adaptadores. Se comprobaron la fórmula matricial por otro método, etiquetas retenidas envenenadas, rechazo de 2024/mercado incorrecto y enlaces incompletos. Las fuentes y el código están congelados por hashes; se guardarán replays exactos. B00 y alternativas conservadas, 2024 cerrado. No hay promoción, aprobación humana o validación profesional independiente. Meta pública 0,17 pendiente.
'''
  body+=f'\nReceta: registro/semana2_robustez2023_ciclo22_plan.json, SHA256 {sha(p)}. Sintéticos: privado/semana2/robustez2023/ciclo22_20261025_v1/synthetic.json, SHA256 {sha(s)}.\n'
  post(22,'prior',body,'Misión 0,17: atributos contractuales omitidos, receta y filtros previos')
 else:raise ValueError(n)
