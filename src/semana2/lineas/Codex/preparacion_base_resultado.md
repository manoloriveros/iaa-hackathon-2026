Codex. Cierro la preparación preinscrita en COD-S2-20261023-002, con la corrida `../../Repositorio_IAA2026/privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3`. El [informe de preparación](../../Repositorio_IAA2026/docs/semana2/PREPARACION_BASE.md) explica las reglas, archivos y límites; el [índice activo](../../Repositorio_IAA2026/registro/semana2_preparacion_actual.json) conserva rutas y huellas.

La capa corrige exactamente 609 exposiciones (114 guardadas como días y 495 con divisor 360). La exposición de entrenamiento pasa de 127.105,4490 a 91.494,5253 años. El test y las fechas de cobertura no cambian. Se conserva el valor original y la causa en cada fila; no se aplicó un tope de uno ni la convención exploratoria 365,25.

Los 36 siniestros quedaron auditados como anteriores al primer inicio disponible de cobertura y excluidos del coste de estos periodos, por 92.267,26 CU netos. No hay siniestros con asignación ambigua o sin explicación. De 9.258 originales, 9.222 encuentran periodo; se excluyen 120 rechazados y el objetivo incluye 9.102 aceptados asignados.

T0 suma 27.997.991,57 CU: incurrido 28.898.003,92 menos recuperaciones 900.012,35. Los componentes concilian en centavos; la reserva de caso incluida es 4.995.797,64 CU. Se mantienen los 109.296 periodos de entrenamiento, con 101.225 ceros legítimos por ausencia de siniestro aceptado asignado. Las 209.063 etiquetas de test son nulas. Las sensibilidades de reserva 0,75/1,25 son escenarios de diseño, sin desarrollo estimado ni doble descuento de franquicias.

T0 se identifica como incurrido observado al cierre de 2024, no como coste último conocido. No se estimó aún la completitud de reporte ni se acreditó suficiencia de reservas. Este punto sigue abierto antes de atribuir a un modelo precisión sobre el último.

Particiones ya guardadas: cinco folds agrupados dentro de 2023; temporal con 50.094 filas de 2023 para ajuste y 59.202 de 2024 para evaluación; cinco pruebas de población nueva que cubren 2024 una vez sin compartir cliente o dirección; y roles de producción 2023–2024/test 2025. Hay 36.398 componentes de cliente-dirección, mayor de doce periodos, con semilla y hash fijados. El test no intervino en el grafo. No hubo búsqueda de otra semilla según etiquetas o costes.

La necesidad de la prueba de población nueva se confirma: alrededor de 15,3 % de filas de 2024 corresponde a clientes ausentes en su ramo en 2023, frente a cerca de 76 % del test. Los grupos de desarrollo y de población nueva no comparten cliente ni dirección; el temporal admite renovaciones y las marca.

Pasaron 78 controles del productor, 106 comprobaciones del verificador separado y diecinueve casos de límites/adversos. Los recuentos se solapan. El primer verificador dejó seis fallos por comparar texto de fecha con timestamps; el informe fallido se conserva y se corrigió solo esa comparación. No se regeneró la base ni se modificó el objetivo por ello.

Las decisiones de exposición, prehistoria, T0 y particiones quedan implementadas y verificadas localmente. La matriz de predictores y el puente a último no se presentan como resueltos. Continúan el contrato de disponibilidad (incluido clima 2025), los supuestos de reservas/reporte y la revisión humana. No hubo entrenamiento, calibración, inferencia de modelos, envíos, remoto o cambios en S41.
