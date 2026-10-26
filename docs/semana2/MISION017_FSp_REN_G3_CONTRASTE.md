

## FSp aislado sobre G3: señal favorable, concentración pendiente, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T06:25:39.845489+00:00. Se completó el contraste único registrado de FSp en renovación: pesos motor/edificios de 0,25 y contenidos de 0,5, con los factores residuales G3 guardados, sin reestimarlos. Se mantuvieron exactamente nuevo negocio y los totales por año/ramo. Se usó la calibración recibida kf/ks/kg con contracción n/(n+100), adaptada expresamente al C0 protegido por grupos. No es el F4c/K original ni la igualación de coste sin contracción de la prueba anterior de edificios.

| Medida | Resultado |
|---|---:|
| D² G3 | 0.13709993 |
| D² RFS1 | 0.13868724 |
| Diferencia | +0.00158732 |
| IC 95 % por componentes | [+0.00007185; +0.00315472] |
| Aporte global de 2023 | +0.00090664 |
| Aporte global de 2024 | +0.00068068 |
| Sin los 31 grupos más favorables, mismo denominador | -0.00121593 |
| Sin los 31 grupos de mayor coste observado | +0.00111381 |

Los cinco folds son positivos y ambos años ganan. El intervalo condicionado a los modelos fuente también es positivo. Aun así, la diferencia no llega al mínimo global de +0,002 y no resiste retirar los 31 grupos más favorables. Retirar los grupos de mayor coste observado mantiene una ganancia: esa comprobación distinta no sustituye el fallo de influencia. No se relaja el criterio ni se admite un envío por la media favorable.

| Ramo, solo renovación | Aporte 2023 al D² global | Aporte 2024 al D² global |
|---|---:|---:|
| motor | +0.00011269 | +0.00025628 |
| buildings | +0.00042564 | -0.00003003 |
| contents | +0.00036830 | +0.00045443 |

Motor y contenidos ganan en ambos años. Edificios mejora en 2023 y pierde ligeramente en 2024 con esta receta; los modelos, variantes y fallos quedan conservados. La separación del componente frente a G3 es ahora numérica y no una atribución a partir de CSV compuestos con factores reestimados. G3 sigue siendo un sustituto: el comparador F3c/F2 completo y sus vetos no están reproducidos íntegramente. No se asigna al público de F3c la mejora local de este contraste.

El primer intento falló antes de puntuar por un valor de control -1e30 que no cabe en int64. Se guardó el fallo, se cambió solo el payload adverso a un entero negativo válido y se preinscribió v2 antes de continuar. Las funciones matemáticas learn/apply/G3 conservaron su AST y los parámetros, criterios y bootstrap fueron idénticos. Se reutilizaron los 11 momentos de motor/fold0 ya guardados, sin estimarlos otra vez; los otros 154 se calcularon una sola vez. El control adverso recomputa esos mismos 165 momentos por separado y no añade parámetros distintos.

Pasaron los 15 controles del flujo real: costes, recuentos y reservas retenidos alterados sin efecto; reproducción exacta de los artefactos guardados sin aprender; identidad de peso cero; orden de claves; suma independiente de momentos y aritmética por otra fórmula. La pérdida coincide con scikit-learn. El bootstrap por componentes usa 2.000 réplicas y recalcula el nulo por fórmula cerrada en cada réplica; la incertidumbre fuente queda condicionada a sus modelos fijos. Estas verificaciones no eliminan la concentración ni acreditan prospectividad.

Coste: 15 niveles globales de coste, 75 momentos de frecuencia y 75 de marca; 75 factores contraídos derivados que no se cuentan otra vez como ajustes. Hay 30 normalizadores sin etiquetas, cero modelos/C0 nuevos, precios de2025 o envíos. Los 36 ajustes MC y los 24 de edificios ya estaban contabilizados. 2024 es desarrollo adaptativo y se mantienen los límites de maestros sin fecha, completitud de coste, cola y reservas. El mejor recibo sigue en 0,16914, sin alcanzar 0,17; B00, F2/C1/F3c y todas las alternativas permanecen.

Queda una diferencia concreta del flujo a resolver antes de preparar la producción: la referencia T2b/G3 usa fuente 2021–2024 para ambos años, mientras FSp usó 2021–2023 al evaluar 2023 en este contraste. La predicción 2025 usará fuente 2021–2024. Ese control de consistencia debe registrarse por adelantado y no convertirse en una elección de ventana por score. También se registró la búsqueda por tags exactos del A1 corregido de tres semillas: no aparecieron sus modelos o relatividades históricas en las raíces indicadas, aunque el productor original sí los guardaba. No se presenta el A1 original de2024 como su sustituto corregido.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_REN_G3_contraste_20261026_v2/report.json.

Siguiente unidad: RFS1 está completo:15ámbitos,165momentos únicos (11reutilizados de v1 y154nuevos en v2),sin nuevos árboles/C0. No repetirlo, retocar K/pesos o ocultar el fallo post31. Siguiente incertidumbre concreta: alinear el flujo de despliegue con la fuente2021–2024 disponible para ambos años objetivo. G3/T2b usa el padre fuente2021–2024 en2023/24, mientras el primer FSp usó dev2021–2023 en2023; la producción2025 necesita prod2021–2024. Registrar antes un control de consistencia usando únicamente las salidas prod ya guardadas, sin nuevos modelos, conservando todos los demás parámetros y criterios. No elegir la ventana por el mejor score ni reescribir RFS1. Además, sigue faltando el comparador F3c/F2 completo: el A1 corregido de tres semillas no tiene archivos históricos/modelos con los tags exactos en la búsqueda registrada (el código original sí los guardaba). No repetir ese inventario; revisar el contrato/offset/matrices y metadatos de rondas de ese productor antes de proponer una reconstrucción, no usar el A1 original2024como si fuera el corregido. No hay CSV nuevo listo o aprobado para enviar. Cuota0conservada,2024abierto,B00/alternativas preservados,meta0.17activa.
