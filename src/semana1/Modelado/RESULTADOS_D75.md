# Resultado D75

S07 superó el umbral local autorizado y se envió una sola vez. Su score público fue inferior al mejor previo.

| Medida | Resultado |
| --- | ---: |
| V23 selección, receta fijada antes de la comprobación global V24 | 0,139420 |
| V24 global, 626.190 filas, T0 completo, D² p=1,5 | 0,131729 |
| Control S06 V24 | 0,124037 |
| Control mezcla D74 V24 | 0,126275 |
| S07 público, COMPLETE, 57325337 | 0,12360 |
| Mejor público vigente, S04 F3 | 0,12435 |

Receta: autos usa coste total LightGBM F0124, 690 árboles en V24 y 780 en producción, siete hojas, tasa 0,025, mínimo 2.000 por hoja, regularización de categorías y semilla 2026. Desarrollo mensual de notificaciones estimado solo con siniestros de filas train, con cola exponencial declarada, offset de coste ponderado por peligro. Tope solo en ajuste de 15.000 CU y recargo uniforme que devuelve el coste completo; las etiquetas y el scorer conservan las pérdidas grandes. Edificios combina al 50 % el nuevo coste total nominal y componentes Poisson/Gamma F012; contenidos usa estos últimos. Todos los CSV se balancean finalmente al total último S02 de cada ramo, sin duplicar IBNR ni leer etiquetas test.

V23 eligió modelos y pesos. La confirmación V24 ya era un conjunto inspeccionado y no acredita validación independiente. El remuestreo por cliente condicionado a la receta da una mejora frente a S06 de +0,007693, intervalo aproximado [0,005558; 0,009981]. La diferencia público/local impide afirmar que ese intervalo prediga la mejora oculta. El nivel último S02 es un supuesto operativo; completar reporte no reconstruye desarrollo de reservas ni demuestra estabilidad entre años. Los componentes hogar aún se ajustan con exposición nominal y el balance final aporta el nivel agregado.

El modelo previo S04 del productor declara 0,13244 V24. La auditoría D75 coincide en métrica y T0 (0,1324400305), pero su exposición efectiva global incorpora siniestros de 2024. Se mantiene su score público por archivo y hash; su diagnóstico local no se usa como prueba de ausencia de esa dependencia.

Se guardan 34 ajustes nuevos en 16 paquetes. No se repiten modelos por cambios editoriales. Tres comprobaciones funcionales nuevas pasan; el núcleo D74 no cambió y conserva sus 31 pruebas previas. La preparación conserva un primer fallo por tratar fechas como extremo abierto, el problema de nombre select.py que ocultaba un módulo estándar y la corrección de arrays de solo lectura al preparar el CSV. No generaron un envío incorrecto ni sustituyeron modelos válidos.

S07: 626.639 filas; SHA-256 363ec0d0725de7c3a40af137ce4c728905230bcb20d5a7330e08c620227553d3. Aceptado 2026-10-17 20:44:43.490 UTC, score 0,12360. Cinco envíos hoy: se conserva el límite provisional de cinco hasta las 19:00 Bogotá. Mejor público y selección final no se cambian automáticamente.

Reproducción: experiment.py prepare; experiment.py train por ramo/corte/variante; choose_recipe.py V23 y V24; adjust_components.py por corte; blend.py V23 y V24; validate_gate.py; producción de coste total y production_fs.yaml mediante run_wave2.py; prepare_s07.py. Las configuraciones y metadatos conservan parámetros, semillas, hashes de entrada y código. extra_fit.py conserva en carpeta propia el contraste adicional nominal de edificios. Los comandos de registro y cierre son operaciones de una sola vez y no se deben repetir sobre el registro vigente.

Las curvas siguen el cálculo de [desarrollo por cocientes de volumen](https://chainladder-python.readthedocs.io/stable/user_guide/development.html) y una [extrapolación de cola](https://chainladder-python.readthedocs.io/stable/getting_started/tutorials/tail-tutorial.html); no se presenta esa elección como validación del supuesto. La evidencia principal está en [threshold_verification.json](../../../Preparación/artifacts/verification/improvement_D75/threshold_verification.json), [S07_audit.json](../../../Preparación/artifacts/verification/improvement_D75/S07_audit.json) y [submission_receipt.json](../../../Preparación/artifacts/verification/improvement_D75/submission_receipt.json).

Aplicación IAA: Documentación §§2–6 (linaje, parámetros y operación), Gobernanza §2.8 (validación propia y límites), Consideraciones profesionales §§3.5–3.6 (responsabilidad humana y aportación de IA). Codex propuso, implementó y comprobó los contrastes; el participante fijó el umbral y autorizó el envío condicional. No hay revisión independiente ni certificación profesional.
