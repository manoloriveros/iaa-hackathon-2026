# Qué contienen los datos recibidos

Codex, 23 de octubre de 2026. Se leyeron y validaron en memoria los trece Parquet emergentes. Los agregados, esquemas, nulos, versiones y huellas están en [diagnostico_inicial.json](diagnostico_inicial.json); las incidencias ampliadas, en [hallazgos_ampliados.json](hallazgos_ampliados.json). No se modificaron originales.

## Integridad y escala

Los once archivos sueltos de `../Datos/` coinciden byte a byte por SHA-256 con semana 1. Faltaba todo el mercado emergente. Se descargaron trece Parquet oficiales, 26.562.843 bytes, en `../Datos/emerging/`. Sus tamaños coinciden con el inventario remoto; los SHA-256 son locales, pues Kaggle no aportó hashes en ese inventario. Se excluyeron los archivos auxiliares `desktop.ini` y no se duplicó el mercado desarrollado.

| Ramo | Filas de entrenamiento 2023–2024 | Filas de test 2025 | Filas de test de clientes ausentes en el entrenamiento del ramo |
| --- | ---: | ---: | ---: |
| Autos | 47.283 | 90.521 | 76,03 % |
| Edificios | 27.447 | 52.295 | 75,95 % |
| Contenidos | 34.566 | 66.247 | 76,14 % |
| Total | 109.296 | 209.063 | Comparaciones por ramo, no clientes únicos sumables |

Hay 135.856 clientes y 136.914 direcciones. Las claves de cliente y dirección de las seis tablas de pólizas encuentran referencia. Los 209.063 IDs del test son únicos y coinciden exactamente con la plantilla; ninguno coincide con la plantilla desarrollada. Las veinte pólizas de referencia están en test.

El archivo de siniestros tiene 9.258 filas y 9.258 IDs distintos, sin copias exactas: 8.082 cerrados, 1.056 abiertos y 120 rechazados. Por ramo, 7.183 autos, 1.059 edificios y 1.016 contenidos. Son recuentos crudos, anteriores a construir el objetivo; los pocos siniestros de hogar aconsejan controlar la complejidad de los modelos.

## Hallazgos que condicionan el trabajo

| ID | Evidencia local | Tratamiento propuesto |
| --- | --- | --- |
| S2-DAT-001 | 452 exposiciones de train mayores que uno: 189 autos, 117 edificios y 146 contenidos; máximo 365. Ninguna fila tiene un periodo superior a 365 días. | Conciliar unidades y convención de días con cada periodo. Guardar exposición original y derivada; no sustituirla sin una regla comprobada. |
| S2-DAT-002 | 9.222 siniestros encuentran un solo periodo; 36 no encuentran ninguno, sin asignaciones ambiguas. De los 36, 34 ocurren en 2021–2022 y dos en 2023. | Separar prehistoria y revisar los dos casos de 2023. No forzar la asignación ni eliminarlos silenciosamente. |
| S2-DAT-003 | Coinciden 752 IDs de clientes y 8.046 de direcciones entre mercados. | Claves con mercado explícito. La coincidencia textual no acredita identidad. |
| S2-DAT-004 | Clima: 136.914 direcciones por cada año 2023, 2024 y 2025; sin duplicados dirección-año. El diccionario anuncia 2023–2024. | Base con información disponible al inicio del periodo; rama de clima 2025 identificada como escenario y pendiente de aclaración de disponibilidad. |
| S2-DAT-005 | Comisión de `comparison_site` vacía en emerging, con 5 % aproximado de filas por ese canal. | No convertir el vacío en cero. Las veinte referencias tienen 17 broker y tres directas. |
| S2-DAT-006 | Faltan edad exacta, crédito, kilometraje y telemática según tabla; aparecen bandas de edad y género. | Esquema común para transferencia y tratamiento explícito de bandas, sin inventar edades. |
| S2-DAT-007 | Ocupación tiene 80 valores no nulos y variantes de mayúsculas/espacios; 16.517 clientes sin ocupación. Varias covariables presentan alrededor de 12 % de nulos. | Normalización conservadora con diccionario revisable y categoría ausente. Las equivalencias semánticas requieren evidencia. |
| S2-ACT-001 | Una valoración al cierre de 2024 y 1.056 siniestros abiertos; no hay triángulo de valoraciones. | Distinguir incurrido observado de último. Estudiar retrasos y sensibilidad de reservas sin declarar identificado su desarrollo completo. |

Como diagnóstico de unidades, la suma de exposición cruda es 127.105,449 años, mientras los días inclusivos divididos por 365,25 suman 91.431,896. Esa comparación detecta una distorsión material; **365,25 es una convención diagnóstica, no una corrección adoptada**. Hay 499 diferencias absolutas mayores que 0,01 frente a esa convención; el umbral solo sirvió para revisar, no para aprobar datos.

Los capitales de edificios y contenidos son numéricos, positivos y completos. Esto no descarta errores de escala o de contexto. Tampoco se observaron pagos o recuperaciones negativos, incurridos menores que pagos, ni reportes anteriores a ocurrencia o posteriores al corte. Son controles puntuales, no una aprobación global.

## Gastos y decisiones pendientes

| Concepto | Desarrollado | Emergente |
| --- | ---: | ---: |
| Gasto fijo por póliza, CU | 45 | 85 |
| Gasto variable, proporción de prima | 12 % | 15 % |
| Comisión directa | 0 % | 0 % |
| Comisión comparison_site | 10 % | Vacía |
| Comisión broker | 15 % | 20 % |
| Impuesto, proporción de prima | 12 % | 8 % |
| Reaseguro catastrófico, proporción de prima de riesgo de hogar | 6 % | 12 % |
| Margen objetivo, proporción de prima | 5 % | 8 % |

Quince de las veinte referencias cubren menos de 0,99 años; el mínimo es 0,0685. Aunque los veinte IDs de póliza son distintos en esa tabla, debe decidirse la asignación del gasto fijo a periodos parciales o cambios de póliza. El nombre del gasto indica «por póliza» y no resuelve por sí solo esa asignación.

La inspección confirma un problema de adaptación con menos historia, población nueva y variables distintas. Todavía faltan el objetivo conciliado, las reglas de limpieza, el contrato de disponibilidad, las particiones y cualquier comparación de modelos.
