# Exposición, objetivo y validación de la segunda semana

Codex, 23 de octubre de 2026. Preparación solicitada por el participante y preinscrita en el foro como COD-S2-20261023-002, antes de materializar la capa. Los originales y la receta de semana 1 se conservan.

La [corrida](../../privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/report.json) prepara el incurrido neto observado y las particiones, sin ajustar modelos. El [índice activo](../../registro/semana2_preparacion_actual.json) identifica las rutas, versiones y huellas. No hay un objetivo último observado en estos datos; el tratamiento de reporte pendiente y suficiencia de reservas continúa abierto.

## Exposición conciliada

La convención adoptada es días de cobertura inclusivos / 365, redondeados a cuatro decimales. Coincide con las 108.687 filas normales de entrenamiento y con todo el test. No se impone un tope de uno: una cobertura real de 366 días tendría 1,0027. En los datos actuales ningún periodo supera los 365 días.

| Ramo | Filas corregidas | Guardadas como días | Divisor 360 | Exposición original, años | Exposición conciliada, años |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos | 254 | 47 | 207 | 54.429,4651 | 38.968,5384 |
| Edificios | 155 | 33 | 122 | 33.783,0830 | 23.468,0047 |
| Contenidos | 200 | 34 | 166 | 38.892,9009 | 29.057,9822 |
| Total | 609 | 114 | 495 | 127.105,4490 | 91.494,5253 |

La revisión inicial marcó 452 exposiciones mayores que uno; la conciliación exacta detectó también errores en periodos parciales, hasta llegar a 609. El test no cambia. La convención de 365,25 usada como diagnóstico exploratorio no se adoptó para la capa.

Cada tabla derivada guarda `exposure_original`, días cubiertos, exposición corregida, motivo y diferencia. Las fechas mantienen exactamente el mismo día de cobertura, con conversión de su representación original a tipo temporal. No se alteraron otras características. Los seis archivos originales de pólizas siguen intactos, y se comprobaron los trece hashes emergentes antes y después.

## Los 36 siniestros fuera de periodo

Los 36 son anteriores al primer inicio disponible de su propia póliza y ramo. Treinta y cuatro ocurren en 2021–2022. Los dos de 2023 son de autos: ocurren el 12 de junio y el 4 de julio; sus primeras coberturas disponibles comienzan el 25 de noviembre y el 26 de diciembre. Las distancias son 166 y 175 días.

Se etiquetan como anteriores a la cobertura disponible y se excluyen del objetivo de estos periodos. La causa operativa original de su presencia no puede identificarse solo con estas tablas; la clasificación describe su relación con las coberturas disponibles. No se cambian las fechas, no se fuerzan asignaciones y no se convierten en historia de siniestros disponible al cotizar.

El [archivo de casos](../../privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/precoverage_claims_36.parquet) conserva los registros, fechas, importes y razones. Su incurrido neto suma 92.267,26 CU y queda conciliado por separado.

| Conciliación de siniestros | Filas |
| --- | ---: |
| Originales conservados en auditoría | 9.258 |
| Asignados a un único periodo, incluidos rechazados | 9.222 |
| Rechazados, excluidos del objetivo | 120 |
| Aceptados y asignados al objetivo | 9.102 |
| Anteriores a cobertura, excluidos del objetivo | 36 |
| Ambiguos o sin explicación | 0 |

## Objetivo preparado y límites

T0 suma `incurred_to_date − recoveries` de los siniestros aceptados y asignados a un único periodo mediante mercado, ramo, póliza y fecha de ocurrencia. Los importes se concilian en centavos enteros. No se vuelve a descontar la franquicia.

| Componente asignado | CU |
| --- | ---: |
| Pagos | 23.902.206,28 |
| Reserva de caso, incurrido menos pagos | 4.995.797,64 |
| Incurrido antes de recuperaciones | 28.898.003,92 |
| Recuperaciones | 900.012,35 |
| T0, incurrido neto observado | 27.997.991,57 |

Hay una etiqueta por cada uno de los 109.296 periodos de entrenamiento. Los 101.225 periodos sin siniestro aceptado asignado conservan objetivo cero. Los demás tienen coste positivo. Se conservan conteos de aceptados, positivos y abiertos; hay 1.055 siniestros abiertos dentro del objetivo.

Las 209.063 filas de test tienen etiquetas nulas, nunca ceros inventados. La tabla incluye los componentes en CU y en centavos, exposición corregida y el estado explícito `observed_net_incurred_not_ultimate`. Las columnas de sensibilidad de reservas son:

`T1_reserve075 = T0 − 0,25 × reserva`

`T1_reserve125 = T0 + 0,25 × reserva`

Son escenarios de diseño, sin ajuste a datos ni afirmación de desarrollo real. No se aplicó un IBNR, no se supuso suficiencia de reservas ni se trasladó la limitación aceptada de S41 a este mercado como una aprobación nueva. Una evaluación futura sobre T0 debe llamarse evaluación del incurrido observado.

## Particiones persistidas antes del primer modelo

Se construyen componentes conectados de cliente y dirección sobre las filas de entrenamiento de 2023–2024 y los tres ramos. Eso mantiene juntas renovaciones, cambios de domicilio y hogares compartidos. La agrupación usa solo identidades, sin etiquetas ni enlaces del test de 2025.

Hay 36.398 componentes, con un máximo de doce periodos en el mayor. La semilla es fija, `IAA2026-S2-GROUPS-v1`; el hash del componente asigna uno de cinco folds. No se buscó otra semilla según las pérdidas o el balance. Los treinta cruces de ramo, año y fold contienen casos positivos, entre 88 y 660 periodos por cruce.

| Uso | Ajuste futuro | Evaluación futura | Filas de evaluación |
| --- | --- | --- | ---: |
| Desarrollo 2023, cinco folds | Otros cuatro grupos de 2023 | Grupo retenido de 2023 | 9.835–10.174 por fold; 50.094 en conjunto |
| Contraste temporal | Los 50.094 periodos de 2023 | Los 59.202 de 2024 | 59.202 |
| Población nueva, cinco folds | 2023 sin el grupo retenido | Ese grupo en 2024, sin clientes ni direcciones comunes | 11.600–11.957 por fold; 59.202 en conjunto |
| Producción, después de seleccionar | Los 109.296 periodos de 2023–2024 | Test 2025 sin etiquetas | 209.063 predicciones futuras |

Cada fila aparece exactamente una vez como validación en los cinco folds de desarrollo y una vez en los cinco de población nueva. Las pruebas agrupadas no comparten clientes o direcciones entre ajuste y evaluación. El contraste temporal admite entidades repetidas para representar renovaciones; las marca para diagnósticos.

En 2024 solo alrededor del 15,3 % de las filas pertenece a clientes nuevos para su ramo, frente a cerca del 76 % en test. Por eso el contraste temporal necesita la prueba adicional de población nueva y lecturas separadas de renovación. No se conoce el resultado de ningún modelo sobre estas particiones.

Las identidades de entrenamiento de 2024 se usan para agrupar de forma conservadora, sin sus resultados. Las etiquetas de ambos años están valoradas al mismo cierre de 2024 y faltan snapshots de covariables: no se presenta esto como un backtest histórico plenamente prospectivo. El ajuste de transformaciones, calibradores o pesos debe quedar dentro del desarrollo. La comparación temporal se reserva para candidatos y criterios previamente fijados.

## Archivos y reproducción

El [productor](../../src/semana2/preparar_base.py) guarda seis tablas de periodos, auditoría de todos los siniestros, los 36 excluidos, la tabla objetivo, pertenencia a grupos, particiones y doce archivos con los roles de cada split. Su [configuración previa](../../registro/semana2_preparacion_plan.json) y el código se copiaron dentro de la corrida con hashes.

Desde la raíz del proyecto:

```powershell
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/src/semana2/preparar_base.py'
```

El comando crea otra corrida identificada y no sobrescribe la actual ni ajusta modelos. No ejecutarlo para comprobar un cambio editorial.

La preparación pasó 78 controles internos. Un [comprobador separado](../../herramientas/verificar_preparacion_semana2.py), sin importar el productor, reconstruyó los importes con Decimal desde los originales y pasó 106 comprobaciones sobre fechas, campos, etiquetas, roles y grupos. Además pasaron diecinueve casos adversos y de límites. Los recuentos se solapan y no constituyen pruebas independientes sumables.

El primer intento del comprobador dejó seis fallos por comparar fechas de texto con timestamps. Se conserva [ese informe](../../privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/verification.json). Tras corregir únicamente la comparación de representaciones, la [verificación final](../../privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/verifications/20261023T164607Z_90a4bf51.json) pasa 106/106. La capa preparada no se regeneró por esa corrección del comprobador.

Esta es una preparación y verificación propia de Codex. No acredita revisión profesional independiente ni aprobación humana general. Antes del entrenamiento sigue siendo necesario fijar las variables admisibles y la estrategia para reporte pendiente y reservas; las discrepancias de clima y gastos mantienen su registro.
