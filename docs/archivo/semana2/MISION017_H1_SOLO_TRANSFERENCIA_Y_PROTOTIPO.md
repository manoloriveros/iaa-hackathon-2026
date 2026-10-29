

## H1 sola: mejora más estable y prototipo simple, 26 de octubre de 2026

Codex, 2026-10-26T10:42:30.543852+00:00. Se aisló la corrección de exposición por peril H1/G3, sin forma FSp de renovaciones, pesos nuevos o normalizadores adicionales. La hipótesis surgió de un fallo concreto: PUL2 perdió la mejora al retirar grupos favorables y H1 original no. Se usaron exclusivamente predicciones y ámbitos guardados de 2023/2024, sin entrenar, recalibrar, inferir tasas fuente o reestimar C0.

| Base guardada | Diferencia D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---:|---:|---:|
| S0 | +0.00117333 | [+0.00073330, +0.00164676] | +0.00059653 | -0.00036850 |
| S1 | +0.00104548 | [+0.00061514, +0.00149910] | +0.00049200 | -0.00045295 |
| S2 | +0.00104636 | [+0.00061610, +0.00149156] | +0.00049149 | -0.00049100 |

S2 era la base principal preinscrita. Las tres mejoran en ambos años y los cinco folds, conservan dirección positiva bajo niveles fijos ±5%, y sus bandas simultáneas exploratorias de familia excluyen cero. Todas mantienen mejora post31 y pérdidas por celda menores que 0,001. Ninguna supera el mínimo formal de ganancia 0,002. No se modificó ese criterio.

El proxy A1 original2024 muestra diferencia +0.00226989, IC95[+0.00133164,+0.00322773] y post31 +0.00124927. Su linaje original de observación no acredita independencia por grupo. Es evidencia condicional, sin sustituir el F3c histórico completo ni asegurar la misma ganancia pública.

| Escenario guardado, H1 frente a G3 | Diferencia D² | IC95 por grupos | Post31 |
|---|---:|---:|---:|
| R075_C | +0.00096998 | [+0.00061471, +0.00133194] | +0.00050034 |
| R125_C | +0.00084415 | [+0.00033719, +0.00137867] | +0.00023271 |
| R075_V | +0.00097509 | [+0.00043228, +0.00150860] | +0.00047815 |
| R125_V | +0.00083701 | [+0.00034497, +0.00134601] | +0.00001212 |
| TAIL005 | +0.00089840 | [+0.00041505, +0.00138804] | +0.00036567 |
| TAIL010 | +0.00084995 | [+0.00026602, +0.00142417] | +0.00028866 |

Se reutilizaron los seis multiplicadores de observación ya calculados; no se repitió integración de CDF, estimación o controles de curvas. Las diferencias agrupadas y los límites inferiores marginales siguen positivos y post31 conserva signo positivo en todos. Nuevo negocio es exactamente igual al de PUL2 y conserva sus resultados adversos: autos nuevos2023 pierde -0,00490388 con revaloración75% y -0,00426495 con cola10%. La simplificación reduce concentración, pero no resuelve esas sensibilidades de reservas/reportes. Los escenarios no son verdad conocida de último.

Se preparó un CSV de 209.063 filas con cinco miembros de precio F3c*H1/G3 y media aritmética, sin forma REN. Total redondeado 88,803,466.882889 CU. Sus 158.980 filas NB son idénticas al prototipo PUL2 anterior. Las 50.083 REN cambian de distribución, conservando por miembro los totales sin redondear de PUL2; la diferencia global de 0,000098 CU tras redondear es aritmética. No se buscó un nivel nuevo en el leaderboard. El total continúa aproximadamente 1,758% por encima de F3c procesado.

Pasaron las claves/orden oficiales, importes positivos, fórmula logarítmica independiente, redondeo racional y Decimal, readback y SHA de fuentes. La revisión de transferencia añadió invariancia ante perfiles desordenados por clave y recuperó H1 a partir de G3 sin repetir sus estadísticas. Estos controles certifican la aritmética revisada, no la calidad predictiva del futuro. Persisten el replay F3c completo ausente, la falta de validación anidada del ensemble y el ESS ponderado insuficiente. 2024 está abierto por instrucción directa y se trata como desarrollo adaptativo, sin confirmación intacta o revisión profesional independiente.

La corrección H1 queda como alternativa de investigación más simple frente a PUL2. No hay promoción formal, nueva aprobación humana, envío o mejora pública verificada. Los indicadores de este diagnóstico conservan submission_allowed=false. El siguiente paso será una decisión separada y trazable de entrega de investigación: copia por SHA, dry run oficial y transporte idempotente con un máximo de un envío si los cupos reales lo permiten. La consulta vigente devolvió cero disponibles; no impide seguir preparando esa entrega. Se conservarán los fallos formales y las sensibilidades adversas en cualquier decisión.

B00, F3c procesado0,16914, PUL2 y todas las alternativas se conservan; el objetivo público0,17 sigue activo. CSV: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/H1_solo_prototipo_20261026_v1/F3c_H1_solo_prototipo_2025.csv; SHA256 d9cccc8dbcdd1ae7d12f00b6ce895c83c1d8018a38c1ffc44eb46017f4d42c89. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/transferencia_H1_solo_20261026_v1/report.json y Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/H1_solo_prototipo_20261026_v1/report.json.
