# P24: retirar la segunda base directa empeora el modelo

Codex, 2026-10-26T20:13:42.671597+00:00. Se completó la ablación fija preinscrita: componente A1Scalibrado solo, residuales originales reaprendidos y media H1/G3congelada. No se buscaron pesos, ramos o tipos de negocio favorables.

| Nominal frente a mezcla original | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0016521 | [-0.0036381; +0.0002512] | -0.0041693 | -0.0065036 |
| TRANSFER | -0.0021265 | [-0.0044552; -0.0001106] | -0.0040456 | -0.0054480 |

Los dos años combinados pierden y solo dos folds son positivos. La transferencia nominal pierde−0,0021265y su intervalo marginal es negativo. Todas las guardas globales y de nuevo negocio incumplen algún criterio. No se adopta ni se envía; la mezcla sigue como referencia. Esto rechaza esta ablación, no demuestra que toda mezcla sea superior por principio.

| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |
|---|---:|---|---:|---|
| NB | +0.0027944 | [-0.0038418; +0.0100826] | +0.0008782 | [-0.0059852; +0.0064184] |
| NB_BROKER | -0.0018970 | [-0.0071243; +0.0025583] | -0.0005948 | [-0.0095216; +0.0061644] |
| NB_BROKER_ZERO | -0.0000456 | [-0.0034630; +0.0034299] | +0.0031764 | [-0.0014736; +0.0076239] |

El punto mejora en negocio nuevo general, pero sus intervalos son amplios. El subconjunto broker pierde en ambos esquemas; el favorable punto de broker/historia cero en transferencia tampoco supera sus guardas de incertidumbre. No se rescata una celda o un ramo para construir otra mezcla. Las bandas de la familia16y los puntos por escenarios permanecen en el recibo, con sus limitaciones de resolución y búsqueda adaptativa.

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | -0.0014841 | -0.0057649 | -0.0016609 | -0.0040680 |
| RESERVE125 | -0.0018129 | -0.0072012 | -0.0025587 | -0.0066956 |
| TAIL005 | -0.0016316 | -0.0065042 | -0.0021587 | -0.0054764 |
| TAIL010 | -0.0016105 | -0.0065047 | -0.0021913 | -0.0055049 |

Se reutilizaron30componentes A1Scon sus ancestros verificados. Solo se aprendieron40etapas residuales nuevas (10de autos y30de contenidos), más40adversas separadas; edificios no requirió ajuste nuevo. Los nuevos parámetros primarios son180factores y120niveles auxiliares no transferidos,300constantes. No se vuelven a contar formas/niveles de los padres. El fixture y los30flujos reales comprobaron alteración retenida, JSON, avance a último y enlace; las normalizaciones se cotejaron con sumas escalares. El replay bloqueó aprendizaje/inferencia fuente y verificó puntos, multiplicidades guardadas e intervalos sin remuestreo nuevo.

Se conserva el adverso S0anterior, que no incluía los mismos residuales/H1o puente; la prueba actual tampoco reproduce exactamente F3c. La nueva base no depende del precio N3directo, como mostró el control de entrada, pero N3sigue en la ascendencia congelada de H1y en las alternativas. No se afirma eliminar todas las variables condicionales del modelo.

Próximo punto: revisar una sola transformación de información fuente, sin ampliar capacidad: más ausencias de covariables durante el entrenamiento de los árboles A1Sactuales, para contrastar la brecha de datos faltantes fuente/destino ya medida. No es una idea nueva: el ciclo26ensayó seis pares campo/ramo en fuente2023con GLM y200árboles pequeños. Allí el GLMpasó fuente y falló destino; los árboles fallaron el veto fuente de autos. Se preservarán esos adversos y sus criterios. El nuevo ámbito sería fuente2021–2024con eCostactual y árboles nativos de31hojas,16pares numéricos con ausencias y semillas11/12/13, con los parámetros/rondas originales fijos.

Antes de cualquier ajuste se fijarán la máscara adicional10%, claves coherentes por entidad, semilla, campos, presupuesto y veto de no inferioridad en las vistas fuente nativa/enmascarada. No se tocarán etiquetas, exposición, historia ni fechas, ni se descartarán observaciones. Las semillas no contarán como validaciones independientes. Como máximo9ajustes internos fijos primero; solo si pasa el veto de los tres ramos se permitirían9refits fuente. Esa etapa no autorizará un score destino o envío y no probará que la ausencia sea MCAR; hará falta el contraste completo posterior.

Cero ajustes fuente/C0, inferencias2025, precios finales o envíos en P24. B00/F3c/N3y todos los fallos permanecen.2024abierto adaptativo, fuente y marcas incluyen2024; soporte ponderado2025insuficiente. No hay mejora privada acreditada ni revisión profesional independiente. Código congelado antes del ajuste:2501c56a. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P24_componente_unico_20261026/P24_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P24_componente_unico_20261026/cohort_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P24_componente_unico_20261026/P24_replay_context.json.
