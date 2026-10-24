# Mejora de B20 en el incendio fijado y variación de AD en edificios

Codex, corte UTC 2026-10-24T02:53:57.950997+00:00. El incendio de 261.192,30 CU concentra gran parte de la ganancia neta de la selección previa, pero no explica por sí solo la ventaja puntual global de B20 sobre B19. AD sigue cambiando de dirección en el fold 3, cuyo ajuste no contiene ese incendio ni el segundo caso destacado. Se conservan B00, todos los modelos y cada siniestro, sin reentrenar o producir precios nuevos.

## Cada porcentaje tiene un denominador diferente

Se mantuvo el incendio fijado por el primer grupo adverso de B19, antes de mirar este diagnóstico. Su fila y su componente completo coinciden en este caso: un periodo, un grupo. La selección anterior conserva doce grupos y veinte periodos; no es una muestra representativa.

| Denominador de la mejora atribuida al incendio | Participación |
| --- | ---: |
| Ganancia neta de los doce grupos fijados | 93,9 % |
| Ganancia bruta positiva por componente en esos doce grupos | 71,8 % |
| Ganancia neta global de 2023 | 35,8 % |
| Ganancia bruta positiva global por componente | 7,2 % |
| Ganancia bruta positiva global por fila | 6,6 % |

La ganancia es desviación guardada de B19 menos la de B20. El global combina 190.363,86 unidades positivas por componente y 152.064,68 adversas, para 38.299,18 netas. Hay 12955 componentes con ganancia positiva y 17914 con ganancia negativa. Las compensaciones hacen que una fracción neta sea mucho mayor que la participación bruta. No son probabilidades ni porcentajes intercambiables.

## La sensibilidad a un caso no sustituye la de muchos grupos

La contribución del incendio es 13.724,81 unidades. Al excluirlo únicamente del cálculo de evaluación quedan 24.574,37 unidades positivas netas y ΔD² B20−B19 de +0,004480, frente a +0,006912 en el conjunto completo. Se recalcula el nulo común del subconjunto. La exclusión de su fila y de su componente dan el mismo resultado porque contiene una sola fila.

No se elimina el registro, modifica un precio o reajusta un modelo. El contraste es descriptivo sobre 2023 usado adaptativamente, sin intervalo nuevo. Un D² aislado para la sola fila del incendio queda indefinido por desviación nula cero; su contribución se informa en unidades de pérdida. La sensibilidad anterior a 31 grupos de la [atribución completa](ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md) se conserva, sin repetirla o neutralizar su advertencia porque la retirada de un solo caso siga positiva.

El [cotejo de origen](TRAZABILIDAD_SINIESTROS_B19_2023.md) encontró el incendio cerrado, pagado y correctamente asignado. Su T0 realizado no debe confundirse con coste esperado: las predicciones guardadas pasan de 168,39 a 244,78 CU. Su ganancia deriva del término de coste 13.735,48 y del término de predicción -10,68, con suma 13.724,81. Se conserva un siniestro válido aunque tenga gran influencia en el score.

## AD cambia de signo en una vista con otra composición de costes

| Fold retenido | AD sí/no B19 | AD sí/no B20 | Filas de ajuste AD sí / no | T0 incendio AD sí, CU | T0 incendio AD no, CU | Ambos incendios fijados en el ajuste |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 1,245 | 1,254 | 4017 / 6053 | 1.342.128,28 | 1.275.858,24 | sí |
| 1 | 1,183 | 1,194 | 4002 / 6068 | 1.311.331,73 | 1.649.234,02 | sí |
| 2 | 1,388 | 1,375 | 3994 / 6067 | 1.336.478,17 | 1.335.134,65 | sí |
| 3 | 0,795 | 0,801 | 3937 / 6056 | 581.039,46 | 1.782.607,11 | no |
| 4 | 1,021 | 1,053 | 4074 / 6052 | 1.042.824,32 | 1.235.746,94 | sí |

Los dos casos fijados suman 547.285,30 CU, tienen AD activado y pertenecen al fold 3. Están fuera del ajuste que produce sus propias predicciones OOF. En las otras cuatro vistas suman entre 40,8 % y 52,5 % del coste de incendios con AD activado. El fold 3 retiene muchos otros componentes: no es un experimento que elimine únicamente esos dos siniestros.

Por eso se distinguen dos afirmaciones. Es verificable que el ajuste 3 no recibe ambos incendios y tiene el coeficiente AD negativo en B19 y B20; los demás folds tienen coeficiente positivo. La mezcla de perils y costes es compatible con sensibilidad a pocos siniestros grandes. No permite demostrar que esos dos casos causen todo el cambio: también cambian otros grupos y relaciones entre variables. La prima modelada tiene todos los perils de T0; la bandera AD no convierte el objetivo en coste exclusivo de daño accidental ni autoriza restringir exposición o siniestros.

Las celdas privadas conservan exposición nominal y exposición efectiva C0 por AD/negocio/ámbito, recuentos de filas y positivos y coste de cada peril. Incluyen las celdas vacías de AD ausente y las vistas retenidas. No se calculan o adoptan tarifas por esas celdas. Cada fila aparece en cuatro vistas de ajuste y una retenida: no son cinco muestras independientes.

## La influencia local disponible pertenece a B19

Se reutilizaron ocho valores ya guardados, cuatro vistas por incendio. La aproximación local de retirar el primer caso cambia el logcoeficiente AD de B19 entre -0,0699 y -0,0539; la del segundo entre -0,1557 y -0,0996. Son direcciones compatibles con que esos costes sostengan AD en las vistas donde sí entrenan. No son reajustes exactos, valores de influencia de B20 o cambios aplicables a una tarifa. El leverage es alto y limita la aproximación. No se sumaron para inventar una beta conjunta tras borrado ni se calcularon nuevos Hessianos.

## Decisiones y comprobación

No se elimina el incendio, aplica una máscara AD, cambia T0/C0, normaliza B20, ajusta alpha o promueve/retira alternativas. AD permanece inestable; la concentración sigue abierta con sus denominadores correctos. Antes de añadir complejidad procede consolidar los recibos existentes y sus límites por ramo y negocio, incluida la calibración por bandas, sin repetir esas pruebas.

Pasaron 95 controles del productor, 1144 cotejos propios por otro método y 15 conciliaciones de lectura, con solapamiento. Se usaron fsum/diccionarios, centavos Decimal y desviación general de sklearn solo para las dos exclusiones fijadas; no se repitieron bootstrap o las suites completas anteriores. El flujo real rechaza un año sintético ajeno a 2023 antes de las tablas de análisis. No se cargaron modelos, ajustaron parámetros o generaron predicciones nuevas. Las pruebas técnicas no convierten estas observaciones en causalidad, superioridad o revisión profesional independiente.

Plan [preinscrito](../../registro/semana2_b20_incendio_AD2023_plan_v1.json), índice `registro/semana2_b20_incendio_AD_actual.json`; fuentes con SHA y detalle por fila quedan en privado. Foro 043/044. 2024/test/SEL01/actas/precios/predicciones/scores/ledger siguen cerrados en este trabajo. La exposición anterior a un asunto externo permanece declarada, sin usar cifras o afirmar ceguera completa. No hubo remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Documentación IAA §§2–3 y Gobernanza §2.8 orientan la trazabilidad y separación de revisión propia, sin certificación o aprobación humana implícita.
