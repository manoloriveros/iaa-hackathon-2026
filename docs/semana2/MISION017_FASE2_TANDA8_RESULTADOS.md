

## Frecuencia meteorológica por peril: tanda 8, 25 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T04:25:05.971241+00:00. Se completaron once Poisson GLM estándar en los periodos del desarrollado 2021–2024. Usan recuentos conciliados y exposición de número de reportes RKM ya guardada. Se transfieren solo los cambios meteorológicos dentro de la misma dirección, con mezcla de coste de cada C0 de entrenamiento y normalización sin etiquetas por ramo/año/negocio. Los controles de riesgo, crédito, región, edad, mes y año se quedan en la fuente. No se inventó crédito emergente.

| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia con ponderación2025, solo sensibilidad |
|---|---:|---:|---|---:|
| P1 | 0.135924 | +0.000674 | [+0.000067; +0.001268] | -0.000786 |
| P2 | 0.135607 | +0.000357 | [+0.000056; +0.000654] | -0.000414 |
| P3 | 0.135433 | +0.000183 | [+0.000032; +0.000333] | -0.000212 |

La referencia N3 vale 0.135250; es un comparador de investigación sobre T2b, no el envío C1/F2 completo. P1 aplica los coeficientes completos, P2 la mitad y P3 la cuarta parte, sin otros ajustes. Ninguna supera los criterios preinscritos: todas quedan por debajo de +0,002, ganan en tres de cinco folds y pasan a diferencia negativa tras retirar los 31 grupos más favorables. Los intervalos marginales son positivos, pero los simultáneos de P1/P2 incluyen cero; no compensan los controles adversos ni la búsqueda adaptativa. P3 tampoco supera los demás criterios.

Con la ponderación diagnóstica hacia la composición de 2025, las tres diferencias son negativas. El fallo previo de ESS sigue vigente: esa ponderación no es estimando principal y no se recortó ni reagruparon bandas para cambiarlo. La corrección mejora el sustituto A1 original2024, pero ese archivo no es el A1 corregido ni reproduce F2 completo. No se admite un nuevo CSV de test y no se activan los once ajustes condicionales de sensibilidad de observación: faltó su condición previa.

La primera ejecución terminó en el tercer GLM por no superar el gradiente máximo de 1e-6, aunque el solver declaró convergencia por reducción relativa. Se guardaron el fallo y los dos modelos ya terminados. La enmienda numérica se registró antes de continuar, redujo ftol de 1e-12 a 1e-15 y mantuvo objetivo, priors, datos y límite de gradiente. Los dos modelos se reutilizaron por SHA y solo se ajustaron los nueve pendientes. El coste real es doce intentos para once modelos únicos, incluido el intento fallido; no se oculta ese coste.

Los once modelos pasaron codificación dispersa independiente, objetivo Poisson de scikit-learn, gradiente y Hessiano por diferencias finitas. La covarianza aproximada por 48 bloques región/año se reprodujo. Las 15 reproducciones del flujo de precios fueron exactas, con un segundo cálculo algebraico y el optimizador bloqueado. Alterar siniestros y reservas retenidos no cambia los factores o normalizadores. Los objetos C0 excluyen los componentes retenidos y se conservaron los totales de referencia. Estos controles comprueban implementación; no convierten el resultado predictivo adverso en una mejora.

Se mantienen los límites de cola última, suficiencia de reservas, mezcla global de perils y disponibilidad prospectiva del clima. La incertidumbre de destino condiciona en la fuente ajustada, la covarianza es aproximada y 2024 es desarrollo adaptativo abierto por el participante. La revisión propia no es revisión profesional independiente ni aprobación humana. Coste adicional: 180 normalizadores sin etiquetas, cero curvas C0, cero inferencias T2b nuevas, cero precios de test y cero envíos.

El mejor recibo público procesado sigue en 0,16519, referencia 57651126; no se ha alcanzado 0,17 y no hay score público nuevo. B00, F2, C1 y todas las alternativas permanecen.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda8_poisson_20261026_v2/validation_v1/report.json; receta y enmienda en registro/semana2_mision017_fase2_tanda8_plan_v1.json y _v2.json.

Siguiente unidad: Revisar los artefactos y recetas de severidad fuente FS/FSp y su ajuste E25 antes de otra tanda. La señal meteorológica de frecuencia no resolvió la inestabilidad ni la transferencia a nuevo negocio; no repetir W7/P1-P3, cambiar el umbral a posteriori o usar un subconjunto de perils elegido por sus resultados retenidos. Identificar qué soporte/modelos de severidad son recuperables, si ya se probaron las alternativas propuestas y qué diferencia material queda sin contrastar. Reutilizar recuentos, objetos de reporte y offsets fuente conciliados; no reconstruir curvas por desconocer sus rutas. Una prueba posterior debe registrar comparador, necesidad, objetivo/exposición, configuración, presupuesto y criterio antes de ajustar o puntuar. 2024 permanece abierto como desarrollo por instrucción humana. Conservar B00, F2, C1, alternativas, autoría y el último cupo; no gastar un envío por mejoras pequeñas/adversas o sin replay del flujo de entrega. Objetivo0.17 activo, mejor recibo0.16519.
