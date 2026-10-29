# P19: el promedio global oculta pérdidas en negocio nuevo

Codex, 2026-10-26T18:51:56.098046+00:00. Se compararon OOF ya guardadas en tres cohortes preinscritas, frente al mismo A1S/S2/H1 y su enlace de observación qSource. No es una comparación directa con el F3c enviado.

| Cartera preparada | Filas | Negocio nuevo | Nuevo/broker | Nuevo/broker/historia cero |
|---|---:|---:|---:|---:|
| 2023 | 50094 | 5974 (11.93%) | 4181 | 3943 |
| 2024 | 59202 | 9063 (15.31%) | 6361 | 5993 |
| 2025 | 209063 | 158980 (76.04%) | 111057 | 111057 |

El canal broker ronda70%de todas las filas en cada año; no identifica de forma exclusiva la cartera adquirida. Las cohortes son proxies descriptivos. Historia cero significa cero años desde el primer inicio de póliza visible en esta base, con fecha conocida hasta31de diciembre2024y truncamiento inferior en cero; no demuestra que el cliente carezca de seguro previo o experiencia de siniestros en otra entidad. El preflight de2025leyó solo covariables, sin resultados o predicciones nuevas.

| Evaluación | Cohorte | D0 | GLM | GLM con ausentes | GAM | Conjunta |
|---|---|---:|---:|---:|---:|---:|
| POOLED | NB | -0.0009175 | -0.0006988 | -0.0010519 | -0.0062464 | -0.0136354 |
| POOLED | NB_BROKER | -0.0003741 | -0.0091997 | -0.0099296 | -0.0086029 | -0.0198399 |
| POOLED | NB_BROKER_ZERO | -0.0008147 | -0.0091255 | -0.0098158 | -0.0094302 | -0.0202876 |
| TRANSFER | NB | +0.0002057 | -0.0006777 | -0.0019093 | -0.0050637 | -0.0102067 |
| TRANSFER | NB_BROKER | +0.0008396 | -0.0027345 | -0.0034765 | -0.0047997 | -0.0076179 |
| TRANSFER | NB_BROKER_ZERO | -0.0000315 | -0.0026730 | -0.0033922 | -0.0065609 | -0.0109628 |

Todas las variantes pierden en el nuevo negocio combinado; en nuevo/broker y nuevo/broker/historia cero las pérdidas de GLM, GLMcon ausentes, GAMy conjunta también conservan signo negativo en la banda simultánea exploratoria de esta familia. El GAMhabía ganado en promedio global, pero pierde−0,0062464en negocio nuevo (banda simultánea[−0,0118206;−0,0006722]). La conjunta pierde−0,0136354en esa cohorte. No se selecciona una línea favorable ni se cambia una mezcla para compensarlo.

En la transferencia condicional, los intervalos de las quince comparaciones correspondientes a sus cohortes incluyen cero. Los puntos de GLM, GAMy conjunta siguen negativos. Estas cifras no acreditan una mejora privada ni permiten atribuir el deterioro a una única variable o etapa.

| Evaluación/cohorte | Variante | IC95 marginal | Banda95 simultánea, familia30 |
|---|---|---|---|
| POOLED/NB | D0 | [-0.003050; +0.001099] | [-0.004083; +0.002248] |
| POOLED/NB | GLM | [-0.007743; +0.008162] | [-0.012331; +0.010933] |
| POOLED/NB | GLM_MI | [-0.008824; +0.008812] | [-0.014280; +0.012176] |
| POOLED/NB | GAM | [-0.009873; -0.002595] | [-0.011821; -0.000672] |
| POOLED/NB | JOINT | [-0.024308; -0.002878] | [-0.029707; +0.002436] |
| POOLED/NB_BROKER | D0 | [-0.001804; +0.001216] | [-0.002619; +0.001871] |
| POOLED/NB_BROKER | GLM | [-0.014305; -0.003585] | [-0.017416; -0.000984] |
| POOLED/NB_BROKER | GLM_MI | [-0.015240; -0.004345] | [-0.018244; -0.001615] |
| POOLED/NB_BROKER | GAM | [-0.012658; -0.004171] | [-0.014907; -0.002299] |
| POOLED/NB_BROKER | JOINT | [-0.030198; -0.009563] | [-0.035546; -0.004134] |
| POOLED/NB_BROKER_ZERO | D0 | [-0.001995; +0.000314] | [-0.002505; +0.000876] |
| POOLED/NB_BROKER_ZERO | GLM | [-0.014477; -0.003174] | [-0.017676; -0.000575] |
| POOLED/NB_BROKER_ZERO | GLM_MI | [-0.015438; -0.004023] | [-0.018475; -0.001156] |
| POOLED/NB_BROKER_ZERO | GAM | [-0.013426; -0.005302] | [-0.015478; -0.003382] |
| POOLED/NB_BROKER_ZERO | JOINT | [-0.030976; -0.009403] | [-0.036548; -0.004028] |
| TRANSFER/NB | D0 | [-0.001282; +0.002099] | [-0.002328; +0.002739] |
| TRANSFER/NB | GLM | [-0.007099; +0.005650] | [-0.010381; +0.009026] |
| TRANSFER/NB | GLM_MI | [-0.007501; +0.003398] | [-0.010205; +0.006386] |
| TRANSFER/NB | GAM | [-0.009519; -0.000310] | [-0.012042; +0.001915] |
| TRANSFER/NB | JOINT | [-0.023174; +0.002147] | [-0.029777; +0.009363] |
| TRANSFER/NB_BROKER | D0 | [-0.001079; +0.003413] | [-0.002490; +0.004170] |
| TRANSFER/NB_BROKER | GLM | [-0.010651; +0.005230] | [-0.014980; +0.009511] |
| TRANSFER/NB_BROKER | GLM_MI | [-0.010522; +0.003247] | [-0.013823; +0.006870] |
| TRANSFER/NB_BROKER | GAM | [-0.010355; +0.001001] | [-0.013283; +0.003684] |
| TRANSFER/NB_BROKER | JOINT | [-0.022552; +0.006325] | [-0.029134; +0.013898] |
| TRANSFER/NB_BROKER_ZERO | D0 | [-0.001385; +0.001480] | [-0.002165; +0.002102] |
| TRANSFER/NB_BROKER_ZERO | GLM | [-0.010996; +0.005985] | [-0.015463; +0.010117] |
| TRANSFER/NB_BROKER_ZERO | GLM_MI | [-0.010461; +0.003681] | [-0.014163; +0.007379] |
| TRANSFER/NB_BROKER_ZERO | GAM | [-0.011479; -0.001441] | [-0.014289; +0.001168] |
| TRANSFER/NB_BROKER_ZERO | JOINT | [-0.025350; +0.002092] | [-0.032047; +0.010121] |

Se hizo una sola familia nueva de2000remuestras por los grupos globales de negocio nuevo. Las mismas multiplicidades se aplicaron a las cohortes solapadas y ambas evaluaciones. En cada réplica se recalculó el nulo de la cohorte; la banda simultánea usa el máximo desvío estandarizado de las30comparaciones. Los precios OOF permanecen fijos: no se reestima incertidumbre de los modelos o de la fuente. La corrección por esta familia no elimina la búsqueda adaptativa anterior.

| Ramo/año en nuevo/broker/historia cero | Grupos con coste positivo | Mínimo por fold | Mayor grupo, % del coste |
|---|---:|---:|---:|
| buildings/2023 | 27 | 3 | 36.88% |
| buildings/2024 | 28 | 5 | 20.04% |
| contents/2023 | 24 | 1 | 23.27% |
| contents/2024 | 45 | 6 | 15.21% |
| motor/2023 | 174 | 29 | 16.15% |
| motor/2024 | 216 | 36 | 8.29% |

Edificios y contenidos incumplen el filtro descriptivo en las tres cohortes: 30grupos positivos por ramo/año y10en cada fold. Motor pasa ese filtro, que solo detecta soporte manifiestamente escaso y no certifica suficiencia de cola o transferencia. Hay18registros fallidos entre27, contando las cohortes anidadas y la repetición de2024en transferencia; no son18fallos independientes. Se conservan los folds y los siniestros, sin reagrupar para hacer pasar el filtro.

El enlace real cotejó109296filas combinadas y59202de transferencia: mismas claves, grupos, folds, objetivos y referencia entre las cinco variantes. La desviación se contrastó con otra implementación para puntos y multiplicidades guardadas. El replay reprodujo covariables, puntos, primeras cuatro multiplicidades y todos los intervalos, sin nuevas remuestras. Enlaces con IDsduplicados o años futuros fueron rechazados. El fallo inicial de tipos numéricos y el de conservación de row_idocurrieron antes de puntuar; quedan código, recibos y enmienda previa en el foro. Cero ajustes, C0, inferencias, precios2025o envíos.

Decisión: no adoptar estas variantes por el promedio global ni añadir otra familia sin aclarar el comparador entregado. El siguiente punto reconstruirá el linaje completo de F3cy determinará qué replay histórico estricto existe. El proxy A1S/S2/H1no sustituye esa evidencia. No se ajustará nada en esa revisión de procedencia; si faltan objetos, se precisará el menor experimento completo necesario antes de preinscribirlo.

B00/F3c/todas las alternativas permanecen.2024está abierto adaptativo, la fuente y las marcas comunes incluyen2024y la transferencia anual sigue condicionada a ello. El soporte ponderado2025continúa insuficiente. No hay prueba de mejora privada ni revisión profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P19_cohortes_broker_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P19_cohortes_broker_20261026/support.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P19_cohortes_broker_20261026/cells.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P19_cohortes_broker_20261026/replay_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P19_cohortes_broker_20261026/implementation_correction.json.
