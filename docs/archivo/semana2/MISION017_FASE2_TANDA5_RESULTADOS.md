

## Prima anual como información residual, 2026-10-25 (Bogotá)

Codex, 2026-10-26T02:32:01.601191+00:00. La tanda 5 terminó y se conservan todos sus artefactos. La comprobación de pares de tramos por póliza/año aporta evidencia empírica de que written_premium se comporta como prima anual en ambos mercados: la mediana de cambio logP/logE queda próxima a cero, seleccionando los pares por duración y sin leer siniestros. No demuestra una fórmula tarifaria exacta ni controla todos los cambios de cobertura. Esta receta no divide la prima por exposición.

Se ajustaron seis GLM Tweedie sencillos en el mercado desarrollado 2021–2024: un efecto residual de prima y otro conjunto de prima/marketing por ramo. El objetivo sigue siendo el coste neto de siniestros y el offset es el riesgo del padre T2b. Región, canal y año actúan como controles en la fuente. Los efectos se trasladan sobre N3 con fuerzas fijadas y se conservan los totales por ramo/negocio mediante covariables y predicciones, sin etiquetas retenidas.

| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia tras retirar 31 grupos favorables |
|---|---:|---:|---|---:|
| S1 | 0.135080 | -0.000169 | [-0.001008; +0.000671] | -0.001050 |
| S2 | 0.135568 | +0.000318 | [-0.000873; +0.001541] | -0.001043 |
| S3 | 0.135542 | +0.000292 | [-0.000292; +0.000897] | -0.000413 |

N3 = 0.135250 es una referencia de investigación, no la reproducción íntegra de F2 ni un candidato promovido. La prima sola empeora; añadir marketing produce una mejora pequeña, compatible con cero y dependiente de pocos grupos. Ninguna variante cumple los criterios registrados. Se conserva el resultado adverso y no se envía ninguna de ellas.

La codificación dispersa y las medianas de prima se reconstruyeron por otro método. Los seis objetivos y sus derivadas se cotejaron con scikit-learn y diferencias finitas, sin ajustar. Los 15 ámbitos se reprodujeron exactamente con el optimizador bloqueado. Cambiar las etiquetas, la exposición o la unidad monetaria no altera la transformación más allá de precisión numérica; se conserva el total de cada celda. No se repitieron los ajustes de C0.

Coste real: seis estimadores de precio fuente, cero curvas C0 nuevas, cero niveles aprendidos de nuevas etiquetas emergentes y 90 normalizadores de cartera sin etiquetas. Estos normalizadores y las medianas dependen de la cartera conocida; no acreditan un flujo prospectivo en línea. 2024 se usa como desarrollo adaptativo autorizado. La incertidumbre de reservas, cola y fecha de los maestros permanece abierta; los intervalos condicionan en la fuente fijada. La revisión es exploratoria, realizada por Codex, y no constituye revisión profesional independiente.

B00 y F2 se conservan. Cero envíos nuevos. La última marca pública conciliada del equipo sigue siendo 0,16033; no se ha alcanzado 0,17.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda5_prima_20261025_v1/validation_v1/report.json.

Siguiente unidad: Conciliar los dos componentes de la mezcla que produjo F2 y su disponibilidad local, antes de otra familia. El replay anterior comprobó T2b, no la mezcla completa A1fixF1b3n/T2b. Cotejar por SHA y aritmética los CSV ya existentes de 2025 y el linaje de los factores, sin enviar ni ajustar. Separar el A1 original de 2024 de la versión corregida de tres semillas: no llamar al primero replay del segundo. El inventario acotado no ha encontrado los pesos ni las relatividades históricas de A1 corregido en las carpetas de intercambio; comprobar la disponibilidad real y registrar cualquier parte no reproducible. No repetir marketing, prima, CatBoost, replays o remuestreos cerrados con fuentes iguales. 2024 permanece abierto como desarrollo. B00, F2 y alternativas se conservan; la misión 0,17 sigue activa y los cupos se reservan para evidencia suficiente.
