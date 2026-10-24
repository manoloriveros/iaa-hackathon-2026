# Modelos estándar: primera unidad nocturna

Codex, 23 de octubre de 2026. Una constante por tipo de negocio y un GLM con seis variables por ramo proporcionan referencias sencillas útiles. Sus ventajas observadas en 2023 siguen inciertas y dependen de pocos grupos de evaluación. Se conserva B00, todas las alternativas y el cierre de 2024. Esta prueba no justifica añadir complejidad.

La petición nueva del participante prioriza validación de decisiones y modelos estándar. El [plan nocturno](PLAN_NOCTURNO_20261023.md) programa continuidad en este chat cada hora de 19:00 a 07:00 de Bogotá. El estado nativo está activo y acotado al 24 de octubre de 2026 a las 07:00; eso acredita programación, no ejecuciones futuras. Se requiere que el equipo y la aplicación estén disponibles. Las otras automatizaciones no se modificaron.

El [plan v5](../../registro/semana2_desarrollo2023_plan_v5.json) quedó en COD-S2-20261023-016 antes del ajuste. El resultado está en COD-S2-20261023-017 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice de continuidad](../../registro/semana2_continuidad_nocturna.json) separa lo terminado del trabajo siguiente. El [registro de decisiones del ciclo](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/decision_journal.json) vincula cada decisión con su comprobación y consecuencia.

## Recetas y entradas

B12 aprende una constante por ramo y nuevo negocio/renovación, solo con filas de ajuste: `r_b=sum(T0/sqrt(e))/sum(sqrt(e))`. Son treinta constantes Tweedie, no cocientes actuariales sum(T0)/sum(e), balance OOF o calibración posterior.

B13 es un GLM Tweedie 1,5 con enlace log, alpha0, intercepto, efectos principales y seis predictores por ramo. No tiene interacciones o selección posterior de variables. Autos usa nuevo negocio, NCB, edad y grupo de valor del vehículo, banda de edad del conductor y región. Edificios usa nuevo negocio, logcapital, edad del inmueble, zona inundable, tipo de inmueble y región. Contenidos usa nuevo negocio, logcapital, dormitorios, objetos valiosos, tipo de inmueble y región. Mediana y StandardScaler numéricos; OHE con primera categoría de referencia, mínimo50/máximo40. Todo se aprende dentro del ajuste. L-BFGS, tolerancia1e-6, máximo2000, sin rejilla. La fuente registra además tolerancia técnica del gradiente 1e-4 antes del ajuste; el máximo observado fue 4,843e-6.

Mismos 50.094 periodos de 2023, 30.869 componentes, cinco folds, T0 y C0 de las tandas anteriores. B13 usa un subconjunto exacto de F0; conserva el capital dudoso enmascarado, sin clima ni factores transferidos. El objetivo es tasa T0/e, peso sqrt(e), con predicción observada e×tasa. Se comprobó la identidad de pérdida que justifica esa ponderación. Los originales y las doce tablas OOF anteriores permanecen exactos. Se ajustaron quince GLM y treinta constantes, sin factores o mezclas posteriores. Acumulado: ochenta estimadores base y sesenta constantes; estrés y adaptadores históricos siguen identificados con su linaje.

## Resultados OOF de 2023

Observado total 15,297 millones CU; nuevo negocio 1,528 millones. A/E significa observado/predicho. D² es Tweedie1,5 sobre importes con nulo global, no media de los ramos.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
| W2-B00 | 0.06858 | 15.614 | 0.980 | 0.04783 | 1.550 |
| W2-B08 | 0.09318 | 15.599 | 0.981 | 0.07297 | 1.182 |
| W2-B12 | 0.07492 | 15.367 | 0.995 | 0.09220 | 0.906 |
| W2-B13 | 0.08671 | 15.430 | 0.991 | 0.11119 | 0.906 |

B12 mejora 0,00633 puntos frente a B00; B13 mejora 0,01180 frente a B12. Ambos contrastes tienen intervalos exploratorios que incluyen cero y ventajas que se invierten al retirar sus 31 grupos más favorables. La cercanía global de A/E a uno no acredita calibración futura, último o suficiencia de reservas.

| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar sus 31 grupos favorables |
| --- | ---: | --- | ---: |
| W2-B12 / W2-B00 | 0.00633 | [-0.00205; 0.01843] | -0.00739 |
| W2-B13 / W2-B00 | 0.01813 | [-0.00620; 0.04266] | -0.01251 |
| W2-B13 / W2-B08 | -0.00647 | [-0.02446; 0.01289] | -0.02798 |
| W2-B13 / W2-B12 | 0.01180 | [-0.00970; 0.03170] | -0.01286 |

Se guardaron 91 parejas con 2.000 sorteos comunes por componente. Son exploratorias y no corrigen la búsqueda adaptativa entre catorce recetas, multiplicidad o cambio de población. B13 tiene menor punto global que B08, con intervalo de la diferencia que cruza cero; esto no prueba equivalencia ni autoriza retirar ninguna alternativa.

| Ramo, D² | B00 | B12 | B13 |
| --- | ---: | ---: | ---: |
| Autos | -0.00581 | 0.01221 | 0.03310 |
| Edificios | 0.02085 | 0.01811 | 0.02105 |
| Contenidos | 0.02893 | 0.02663 | 0.03743 |

B13 mejora los puntos de los tres ramos frente a B12. Edificios tiene A/E global1,0005, pero en edificios nuevos D²0,05022 sigue por debajo del 0,06523 de B00, aunque supera 0,03542 de B12. Autos nuevos sigue con D² negativo (−0,01004) y A/E0,879; contenidos nuevos tiene A/E1,184 y D²0,15363. La renovación agregada B13 tiene A/E1,0019 y D²0,08293. El diagnóstico por celdas sigue siendo necesario; solo hay40/36 positivos nuevos en edificios/contenidos.

## Qué quedó comprobado

Pasaron 22 casos focales y 712 controles del [comprobador separado](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/verifications/20261023T232550Z_bf02f31b.json), con solapamiento. El comprobador no importa el productor y bloquea fit/fit_transform durante replay. Reconstruye constantes con suma compensada, pérdida por fórmula general, gradiente GLM en unidades totales y diferencias finitas; coteja parámetros efectivos, mediana/escalado/categorías aprendidos en ajuste, disjunción de grupos, predicciones sin respuestas, métricas/segmentos/escenarios e influencia. Se reconstruyeron numéricamente los 25 contrastes nuevos; las parejas anteriores se conservan mediante OOF exacto, utilidad y sorteos idénticos, sin repetir sus suites completas.

Los casos adversos rechazan2024, test, repetición de claves, segmentos inválidos, costes negativos, exposición inválida y ajustes sobre el fold retenido. Todos los quince GLM convergieron dentro del máximo y pasaron gradiente. El [informe íntegro](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/report.json), [manifiesto](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/manifest.json), [casos focales](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/fixture_checks.json) y [valoración](../../privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/assessment.json) conservan cifras y fuentes. Estas son verificaciones propias de Codex, no validación profesional independiente ni aprobación humana.

## Decisiones y trabajo siguiente

Se conserva B00 y B01–B13. No se promueve, retira, congela lista final o abre2024. Tampoco se añaden interacciones, modelos por peligro, transferencia o boosting por estos resultados. Primero se revisará la evidencia recibida de CLA-S2-20261023-003: capital por fila, alcance temporal del clima y estimación de credibilidad/calibración dentro del fold. La versión que usa clima2024 para2023 requiere declarar retrospectividad; los factores estimados con todo2023 no pueden validar esos mismos folds como una prueba nueva. Las decisiones y tablas de Claude conservan su autoría y se integrarán únicamente mediante una receta y revisión propias del cambio.

Después se tratará el problema residual de nivel/cola con una prueba que pueda refutar la explicación, antes de escalar complejidad. El [plan de la noche](PLAN_NOCTURNO_20261023.md) y su índice evitan repetir trabajo ya concluido sobre fuentes idénticas. Cada ciclo conserva decisiones, fallos, verificaciones y pendientes y comunica un progreso breve. A las07:00 de Bogotá concluye esta ventana con un balance honesto.

Continúan los supuestos de observación T0/C0, reservas, reporte, datos físicos sin fecha y representatividad del negocio transferido. Se aplican las [prácticas IAA](../../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) de gobernanza §2.8 y §§3.3.2,3.4–3.6, documentación §§2–3 y comparación de segmentos de consideraciones profesionales §3.3, sin presentar cumplimiento o equidad certificados. No hay predicciones/scores/precios de2024 o test, ledger, envíos, cómputo remoto, publicación externa o delegación en esta unidad.


## Corte posterior: capital, clima y credibilidad

La [sexta prueba](CAPITAL_CLIMA_CREDIBILIDAD_2023.md) conserva estas recetas y ensaya dos cambios con criterios previos. El [snapshot de índice v5](../../registro/semana2_desarrollo2023_v5_snapshot.json) preserva exactamente este corte; el índice activo recoge el avance.
