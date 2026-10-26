"""Registrar resultados pendientes y la receta siguiente sin leer aportes ajenos."""
from pathlib import Path
import hashlib,json,subprocess,sys

ROOT=Path('C:/dev/Hakaton'); R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/robustez2023'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def post(n,kind,body,subject):
    folder=BASE/f'ciclo{n}_20261025_v1'
    receipt=folder/f'forum_{kind}_receipt.json'
    assert not receipt.exists(),str(receipt)
    path=folder/f'forum_{kind}_body.txt'
    with path.open('x',encoding='utf-8') as h:h.write(body)
    ident=f'COD-S2-20261025-ROBUSTEZ{n}-'+('PREVIO' if kind=='prior' else 'RESULTADO')
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',ident,'--asunto',subject,'--cuerpo',str(path)],check=True,capture_output=True,text=True,encoding='utf-8')
    obj=json.loads(result.stdout)
    with receipt.open('x',encoding='utf-8') as h:json.dump(obj,h,ensure_ascii=False,indent=2)
    print(json.dumps(obj))

if __name__=='__main__':
    n=int(sys.argv[1])
    if n==20:
        report=read(BASE/'ciclo20_20261025_v1/report.json')
        lines=['Resultado de la receta registrada ROBUSTEZ20. No se elige una alternativa nueva. La integración de edad exacta de la fuente en las bandas disponibles del mercado emergente conserva el soporte físico edad >= años de licencia. Los tres pilotos de fuente pasaron el umbral previo. Los controles de estrés de distribución de edad no compensan fallos de estabilidad del resultado principal.','', '| Variante | D² OOF 2023 | Todos los criterios |','|---|---:|---|']
        for row in report['summaries']:
            if row['model_id'] in ['W2-COD-R74','W2-COD-R75','W2-COD-R76','W2-COD-R77']:
                gate=next(x for x in report['gates'] if x['model_id']==row['model_id'])
                lines.append(f"| {row['model_id']} | {row['D2']:.9f} | {gate['all_pass']} |")
        lines+=['','R77 alcanza D² 0,116486975 frente a 0,110536774 de R36, pero mejora solo tres de cinco folds. El intervalo exploratorio de la diferencia incluye pérdida y al retirar únicamente para el diagnóstico los 31 grupos más favorables la diferencia pasa a -0,006168199; también incumple el límite de daño en autos nuevos. R75 apenas cambia el promedio y tampoco supera todos los criterios. Ningún siniestro o grupo se ha eliminado del entrenamiento o de la métrica principal.','',f"{report['new_price_fits']} ajustes reales nuevos; cero estimaciones nuevas de C0. Los objetos guardados reproducen exactamente las predicciones de los 30 adaptadores. Fuente, claves, grupos y T0/exposición/C0 se cotejaron. B00 y todas las alternativas se conservan. Sin CSV ni envío nuevo; 2024 continúa cerrado. La revisión es propia, exploratoria y posterior a búsqueda adaptativa, no aprobación humana ni validación independiente.",'',f"Evidencia: privado/semana2/robustez2023/ciclo20_20261025_v1/report.json, SHA256 {sha(BASE/'ciclo20_20261025_v1/report.json')}; receta registro/semana2_robustez2023_ciclo20_plan_v2.json. La misión 0,17 sigue activa y no está lograda: mejor recibo público propio procesado 0,14331."]
        post(20,'result','\n'.join(lines),'Misión 0,17: edad marginal no supera los criterios de estabilidad de 2023')
    elif n==21:
        plan=R/'registro/semana2_robustez2023_ciclo21_plan.json'
        p=read(plan);s=read(BASE/'ciclo21_20261025_v1/synthetic.json')
        assert s['integer_cost_identity'] and s['held_label_poison_invariant']
        body='''Se registra antes de ajustar con datos reales la prueba R78–R81. Hipótesis: la dependencia repetida de pocos siniestros grandes puede reducirse separando coste limitado y exceso, sin quitar ninguna parte del coste total. El límite fijo de 10.000 unidades monetarias por siniestro consta en el contrato de preparación anterior a las estadísticas de capas. La identidad limitada + exceso = coste original está comprobada por céntimo; los 44 siniestros sin periodo de la fuente conservan exactamente su tratamiento anterior.

Fuente desarrollada de 2023, sin mezclarla con soporte emergente: GLM Tweedie 1,5 alpha 1 y el residual de 200 árboles pequeños ya definido para el coste limitado; GLM Poisson alpha 0,001 para la frecuencia de excedencia en todos los periodos y Gamma alpha 0,1 para el exceso medio condicionado, ponderado por su número de siniestros. Si hay menos de 100 periodos con exceso se usa la media constante de esa capa. Se conservan todos los ceros en coste limitado y frecuencia. El incurrido nominal de la fuente no se presenta como último identificado. Predictores físicos ya admitidos; región de fuente y construcción en edificios excluidas como antes.

Piloto previo en el bloque 0 de grupos de fuente, excluido de todo su aprendizaje. Se compara el coste completo con el objeto C17 de árboles pequeños del mismo ámbito; cada ramo debe tener pérdida Tweedie <= 1,002 veces su referencia. Si falla uno, no se ajusta la fuente completa ni el mercado emergente. Presupuesto máximo: 12 ajustes piloto, 12 de fuente completa y 30 adaptadores emergentes; 54 en total y cero C0 nuevos.

Adaptación de 2023 con los cinco folds guardados, T0/exposición/C0 intactos: R78 intercepto libre, negocio y región ridge 1; R79 añade únicamente log(exceso/limitado), con transformación aprendida dentro del ajuste y ridge 10. Las salidas R78/R79 mezclan raíces 50/50 con B20, fijadas previamente; R80/R81 son sus salidas naturales. No se aprenden ni buscan pesos.

Referencia R36 y criterios sin cambios: diferencia D² >= 0,005, límite inferior exploratorio > 0,0005, al menos cuatro folds positivos, daño de cada ramo/negocio <= 0,0005 del denominador nulo total y diferencia >= 0,0005 tras los 31 grupos más favorables (solo diagnóstico). Remuestreo de 2.000 grupos conectados con semilla 2026102501 y cuantiles 0,0041666666667/0,9958333333333. Control adicional: multiplicar la predicción de exceso por 0,75 y 1,25 sin reajustar; ambas diferencias globales frente a R36 deben seguir >= 0. Esto es sensibilidad, no una corrección estimada de reservas. Preferencia fijada R78, R79, R80, R81 solo si pasan fuente, criterios principales y estrés.

Seis ajustes sintéticos verificaron el flujo de componentes y ambos adaptadores, gradientes, identidad de coste y ausencia de dependencia de las etiquetas retenidas en la inferencia. Las fuentes y el código están congelados por hashes; cada objeto real tendrá replay. B00, resultados adversos y alternativas se conservan; 2024 cerrado. No hay promoción, validación independiente ni aprobación humana. El objetivo público 0,17 aún no está logrado.
'''
        body+=f'\nReceta: registro/semana2_robustez2023_ciclo21_plan.json; SHA256 {sha(plan)}. Controles: privado/semana2/robustez2023/ciclo21_20261025_v1/synthetic.json, SHA256 {sha(BASE/"ciclo21_20261025_v1/synthetic.json")}.\n'
        post(21,'prior',body,'Misión 0,17: receta previa de coste limitado y exceso, sin cambiar el objetivo')
    else:raise ValueError(n)
