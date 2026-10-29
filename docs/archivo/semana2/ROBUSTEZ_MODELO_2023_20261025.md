# Robustez del modelo: investigación2023 y entregas verificadas

El score público propio subió de 0,13310 a 0,13956 en la combinación conservadora y a 0,14331 en la combinación al50%. Es una mejora pública modesta. La investigación continúa para buscar un avance mayor con evidencia, sin ajustar pesos al leaderboard. Las dos nuevas recetas superaron todas las cribas exploratorias preinscritas de2023; eso no equivale a confirmación independiente ni a una promoción formal.

Codex, 2026-10-25T12:26:27.266284+00:00. El participante pidió autonomía hasta obtener un modelo más robusto y resultados significativamente mejores. Se mantuvieron B00 y todas las alternativas;2024 permanece cerrado. No se abrió la ventana nocturna anterior ni se cambiaron automatizaciones, chats, delegación o cómputo remoto.

## Qué mejoró

La mejor mejora que pasa las cribas es R36, con D² OOF2023 de0,11054 frente a0,08938 deB20. Su delta es+0,02115499, intervalo bootstrap exploratorio[0,01032137;0,03163706], mejora en los cincofolds y en los seis segmentos ramo/negocio. Tras retirar los31grupos más favorables como diagnóstico, el delta sigue en+0,00410578. R37, más conservador, también pasa: delta+0,01289871, intervalo[0,00702441;0,01857855] y+0,00337692 después de ese diagnóstico. Ningún siniestro se retiró de los ajustes.

Los pesos1/4y1/2 se fijaron antes de evaluar las mezclas y antes de ver cualquiera de sus nuevos scores públicos. Se combinan las raíces de los precios y luego se elevan al cuadrado. Para Tweedie1,5 la pérdida es convexa en sqrt(mu), lo que permite verificar una cota Jensen por fila. Esa propiedad no garantiza superar al mejor componente. No se probó una serie de factores de nivel en Kaggle.

## Resultados conservados

| Modelo | D²2023 | DeltaB20 | Foldsfavorables | Delta sin31grupos | Cribas |
| --- | ---: | ---: | ---: | ---: | --- |
| W2-COD-R21 | 0.09476 | +0.00538 | 4/5 | -0.01173 | No pasa |
| W2-COD-R22 | 0.08143 | -0.00796 | 1/5 | -0.03411 | No pasa |
| W2-COD-R23 | 0.08650 | -0.00289 | 2/5 | -0.01753 | No pasa |
| W2-COD-R24 | 0.08227 | -0.00711 | 1/5 | -0.02621 | No pasa |
| W2-COD-R25 | 0.09179 | +0.00241 | 4/5 | -0.00293 | No pasa |
| W2-COD-R26 | 0.09438 | +0.00500 | 3/5 | -0.00815 | No pasa |
| W2-COD-R27 | 0.09246 | +0.00307 | 5/5 | -0.00057 | No pasa |
| W2-COD-R28 | 0.09548 | +0.00610 | 5/5 | -0.00296 | No pasa |
| W2-COD-R29 | 0.09419 | +0.00481 | 3/5 | -0.00690 | No pasa |
| W2-COD-R30 | 0.07828 | -0.01111 | 2/5 | -0.02412 | No pasa |
| W2-COD-R31 | 0.10382 | +0.01444 | 5/5 | -0.00416 | No pasa |
| W2-COD-R32 | 0.11508 | +0.02570 | 5/5 | -0.00258 | No pasa |
| W2-COD-R35 | 0.11643 | +0.02705 | 5/5 | -0.00189 | No pasa |
| W2-COD-R36 | 0.11054 | +0.02115 | 5/5 | +0.00411 | Pasa |
| W2-COD-R37 | 0.10228 | +0.01290 | 5/5 | +0.00338 | Pasa |

Las cribas exigían delta>=0,005, límite inferior exploratorio>0,0005, al menos4folds favorables, daño máximo por ramo/negocio de0,0005de la desviación nula completa y delta>=0,0005tras retirar0,1%de grupos favorables. Bootstrap2000porcomponentes,semilla2026102501,cuantiles0,0041667/0,9958333 y nulo recalculado. Se conserva la búsqueda adaptativa completa: estos intervalos no corrigen todas las decisiones anteriores o la incertidumbre de la fuente transferida.

## Arquitectura y datos

Los primeros GLM ampliados, splines, PoissonGamma y árboles aprendidos directamente del pequeño mercado emergente no dieron mejoras estables. La transferencia lineal de2023mejoró todoslosfolds,pero seguía concentrada. El avance vino al aprender la forma en626.355periodos desarrollados de2023, con GLM estándar y una corrección de árboles de capacidad fija, y adaptar en el ajuste exterior emergente solo intercepto,nuevo negocioyregión. Los grupos desarrollados nunca se contaron como soporte emergente.

El componente de edificios excluye construcción: la fuente usa W/w, cuyo material no quedó confirmado en la revisión histórica, y el emergente dice timber. No se hizo esa equivalencia por intuición. Se conservaron las versiones previas y la advertencia. Motor y contenidos reutilizan exactamente sus profesores anteriores.

La fuente desarrollada tiene incurrido neto observado y exposición nominal reconciliada, con44siniestros2023sinperiodo asignable archivados por separado. Su nivel no se presenta como último identificado. En el emergente siguen T0,C0yexposición anteriores, con reserva1ycola no observada0condicionales. No se añadieron primas como predictores, clima realizado futuro o desocupación de ventana incierta. La disponibilidad histórica sellada de algunos atributos sigue sin acreditarse; es un benchmark condicionado a los datos suministrados, no una certificación de tarifa prospectiva.

## Entrega y procesamiento

| Modelo | Envío | Scorepúblico | Estado |
| --- | ---: | ---: | --- |
| W2-COD-R37-FINAL | 57629584 | 0.13956 | COMPLETE |
| W2-COD-R36-FINAL | 57629589 | 0.14331 | COMPLETE |

La receta conservadoraR37 conserva la prioridad fijada antes de medir;R36 es una alternativa congelada. No se cambió la selección manual final de Kaggle. La página es [IAA2026Part2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2). Solo se leyeron los scores públicos de estos envíos propios. No se consultó privado, ni scores/mensajes ajenos, ni métricas,actas,ledger oSEL01de2024.

Cada CSV tiene209.063IDsúnicos en el orden oficial, columnasrow_id/prediction y valores positivos finitos. Tres adaptadores se ajustaron con las50.094filas completas de2023;los profesores,C0ycapitales se reutilizaron. Se verificó equivalencia numérica del adaptador con la receta deCV, coincidencia de capitales, preservación de las columnas basales y enriquecimiento físico2025solo después de los tresfits. Un proceso separado reconstruyó ambas entregas exactamente confit/optimización prohibidos y modelos intactos. Kaggle cotejó ID,competición,mensaje,nombre ytamaño;no devolvió SHA remoto.

Las dos cargas se hicieron antes de leer el nuevo score de cualquiera, consumieron2cuposy dejaron4en la última consulta. Se conservó el CSV originalSHAe5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab. Paquetes,código ydatos siguen locales/privados;solo se enviaron los CSV a la competición.

## Fallos y continuidad

Hubo una serialización incompleta después de30fits en eltanda1:se recuperaron los resúmenes/pares escritos sin repetir entrenamiento obootstrap;eldigest de sorteos no alcanzó a guardarse. La tanda2falló solo al imprimir el evento final, después de guardar reporte/manifiesto. En la transferencia se rechazó un intento por gradiente aunque eloptimizador informaba convergencia;se mantuvo1e-4y se aumentó precisiónftol,sin repetir15modelos aprobados. Se cuenta ese intento fallido.

Elestudio suma212intentos reales adicionales desdeG4(incluye1fallido), con15recetas y tresajustes finales;losfitssintéticos se registran aparte. Elcontadorpropio total queda420. Estos números describen coste, no evidencia predictiva independiente.

El avance público todavía no satisface el salto grande pedido. Próxima hipótesis: frecuencia y severidad porperil con denominadores de cobertura y exposición compatibles, manteniendo referencias y2024cerrado;requiere configuración/criterio previos y validación de toda la cadena. No se modifica una mezcla a partir del público. G1/G2 del ensayo de calibración original siguen abiertos;ninguno de estos resultados los borra.

Fuentesprimariasdelmétodo: [Tweedieenseguros](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html), [SplineTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.SplineTransformer.html). Lasversiones locales y los códigos ejecutados quedan fijados porSHA;no se actualizaron bibliotecas por ver documentación nueva. La revisión es propia deCodex, sin revisión actuarial profesional independiente o aprobación técnica humana inventada.

Índice `Hackaton/Repositorio_IAA2026/registro/semana2_robustez2023_actual.json`;recibos2023enprivado/semana2/robustez2023/ciclo1..7_20261025_v1 yentrega_20261025_v1. Planes,modelos,OOF,replays,adversos,versionesfallidasyautoresseconservan.
