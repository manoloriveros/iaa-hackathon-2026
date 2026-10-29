# Revisión integral desde la posición del participante

Autor: Codex. 19 de octubre de 2026. Revisión crítica solicitada por el participante, con cálculos propios sobre evidencia congelada. Es una revisión de IA; no constituye una firma humana, validación profesional independiente ni aceptación de los riesgos por el participante.

## Dictamen para decidir

S30 y S22 son candidatos técnicamente consistentes con los archivos y el objetivo observable que conserva el proyecto. Mantendría S30 como propuesta provisional y S22 como respaldo. No daría por cerrada la entrega ni aprobaría todavía su uso como tarificador real. La diferencia entre ambos no demuestra superioridad estadística de S30 y la reconstrucción completa del entrenamiento sigue sin acreditarse.

Asumir tu perspectiva significa exigir evidencia y formular una decisión razonada, también cuando contradice una conclusión anterior de Codex o Claude. No permite registrar mi juicio como si lo hubieras emitido tú. Tu solicitud autoriza esta revisión; la aceptación de los supuestos y la selección final permanecen sin firmar.

La revisión cubre las reglas, preparación, datos, objetivo actuarial, selección, archivos finales, reproducción, documentación y adaptación. Los recálculos se concentran en la cadena vigente y los candidatos finales. Los experimentos anteriores se conservan como historia de selección; no se reentrenó cada alternativa ni se presentó la preparación sintética de octubre como evidencia sobre el modelo final.

## Qué queda respaldado por comprobaciones nuevas

El [registro de esta revisión](../../../registro/revision_participante_20261019.json) enlaza el plan previo, el código del auditor, los resultados y sus fuentes. Hay 310 controles técnicos distintos conciliados. Ese número cuenta cotejos de hashes, claves y cálculos; no representa 310 pruebas independientes de calidad predictiva. La corrida principal dejó 307 conformes y tres comparadores de asignación pendientes. El seguimiento puntual comprobó cero diferencias de valores: el desacuerdo era entre dos tipos de texto de pandas. Los intentos fallidos del auditor se conservan y no se suman como controles nuevos.

| Evidencia examinada | Resultado nuevo | Qué permite concluir |
| --- | --- | --- |
| Once originales y once tablas del catálogo activo | Coinciden con sus SHA registrados | Los archivos leídos conservan la integridad declarada. |
| Duplicados de siniestros | 604 copias estrictas; los valores originales de los retenidos se conservan | La eliminación no altera los importes de los siniestros conservados. |
| Asignación por ramo, póliza y fechas inclusivas | 162.546 siniestros revisados; cero asignaciones diferentes o múltiples | La asignación de D67 coincide con una implementación alternativa. Los 413 sin periodo pertenecen a la prehistoria marcada. |
| T0, reservas y conteos por periodo | 2.409.311 periodos; diferencia máxima por fila de 0 CU | La etiqueta observable y sus sumas concilian. No prueba que sean costes últimos. |
| F0 y particiones | T0 concilia, test sin etiquetas, exposición efectiva válida; ningún cliente compartido entre las dos mitades V23 | Los controles examinados de estructura y separación se cumplen. No resuelve la disponibilidad histórica de las variables. |
| Comparación S30 frente a S22 | 72 ámbitos recalculados; diferencia máxima de métrica de 3,34 × 10⁻¹⁶ | Las métricas archivadas son reproducibles desde las predicciones guardadas. Los cortes siguen reutilizados. |
| CSV finales | Cada archivo tiene 626.639 filas, valores positivos finitos, orden y cobertura exactos; SHA igual al recibo puntuado | Los dos archivos de entrega están técnicamente conformes. |
| Insumos y receta | 47 insumos guardados y 51 entradas del manifiesto de código cotejados; dependencias ordenadas | Las piezas inspeccionadas corresponden a la receta conservada. No acredita que todos los nodos se hayan reconstruido. |

La conciliación alternativa obtiene estos importes, todos a la valoración disponible:

| Ramo | Siniestros aceptados asignados | T0 en CU | Reserva de caso en CU |
| --- | ---: | ---: | ---: |
| Autos | 110.496 | 428.762.846,58 | 63.698.064,13 |
| Edificios | 26.266 | 246.656.437,27 | 23.822.203,49 |
| Contenidos | 23.670 | 65.737.584,58 | 2.647.949,32 |
| Total | 160.432 | 741.156.868,43 | 90.168.216,94 |

El criterio financiero se mantiene: incurrido menos recuperaciones de siniestros aceptados; los pagos ya son netos de franquicia. No se resta otra franquicia. La descripción oficial confirma la valoración única al 31 de diciembre de 2024 y advierte que faltan notificaciones y que los abiertos pueden desarrollarse. [Datos oficiales del reto](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/data).

## Qué significa la ventaja de S30

| Comparación | S22 | S30 | Diferencia a favor de S30 |
| --- | ---: | ---: | ---: |
| V24 completo sobre T0 | 0,13774159 | 0,13787963 | 0,00013804 |
| Score público del recibo archivado | 0,12988 | 0,12996 | 0,00008 |

La métrica local se recalculó mediante la fórmula de desviación Tweedie para potencia 1,5 y se contrastó con scikit-learn. Coincidir con esa implementación no demuestra equivalencia con todos los detalles del scorer oficial. [Definición de D² Tweedie](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html).

S30 no pasó el criterio histórico N48 de mejora clara: la ganancia V24 quedó por debajo de 0,0002, hubo ámbitos adversos y los límites inferiores de los intervalos condicionales no fueron positivos. La evaluación regional exacta no se hizo porque los criterios anteriores ya fallaban; no debe describirse como otra prueba ejecutada y fallida. N56 autorizó un ensayo comparativo específico, conservando ese resultado adverso. La puntuación pública posterior no convierte retroactivamente el ensayo en una promoción estadística.

El intervalo histórico por cliente, aproximadamente de −0,000082 a 0,000369, incluye cero. Es evidencia recibida del remuestreo anterior, no un intervalo nuevo calculado en este encargo. No demuestra equivalencia entre candidatos. Además, el recálculo de influencia encuentra que los diez clientes más favorables aportan 0,000173 de D², más que la ganancia neta de 0,000138. Hay compensaciones entre pérdidas grandes y el resultado depende de pocos casos. Ese diagnóstico conserva el denominador completo y no elimina observaciones para mejorar la métrica.

En edificios V24, el coste observado equivale a 1,099 veces la predicción de S30. Es una señal para revisar nivel y sensibilidad; no justifica multiplicar automáticamente las predicciones de 2025 por ese cociente. La calibración Tweedie no exige balance monetario exacto, y el coste observado todavía depende del desarrollo.

Mi propuesta es conservar los dos candidatos y explicar la elección de S30 como decisión pragmática y condicionada. Cambiar de candidato o crear una mezcla exige otra razón verificable; esta auditoría no modifica pesos ni convierte el leaderboard en criterio único.

## Supuestos que aún necesitan tu decisión

### Coste último y reservas

El ajuste de exposición representa la completitud de notificación bajo el método declarado. No demuestra por sí mismo que la frecuencia omitida, la severidad de los tardíos y el desarrollo de reservas estén correctamente identificados. No añadiría otro IBNR a la salida existente sin revisar primero qué ajuste ya contiene.

Una sola valoración no permite comprobar si las reservas son insesgadas. Harían falta valoraciones o movimientos posteriores sobre cohortes comparables, o documentación autorizada del generador que respalde el supuesto. Los escenarios de reserva de −25 % y +25 % son sensibilidades, no pruebas de suficiencia. La guía profesional consultada distingue propósito, recuperaciones, condiciones e incertidumbre de la estimación; se usa como orientación, no como regla del concurso ni certificación. [ASOP 43, secciones 3.3 y 3.6](https://www.actuarialstandardsboard.org/asops/propertycasualty-unpaid-claim-estimates/).

Aceptaría provisionalmente el supuesto para el experimento del concurso si se declara con claridad. Mantendría abierta su validación actuarial.

### Disponibilidad de variables y forma de uso

Hay predictores condicionados por falta de fecha de captura: información de cliente, telemática, contactos y otros campos F3. Usar las tablas suministradas en el concurso no acredita que esos campos existieran al cotizar una póliza real. Las etiquetas históricas valoradas en 2024 también limitan la interpretación prospectiva de los cortes anteriores.

La frase del README «Ningún dato de 2025 interviene en el ajuste» es demasiado amplia. `comun.py` normaliza la prima con la media de la cartera del mismo año y la regla s17 consulta totales predichos de 2025 frente a V24. No se usan sus costes reales, pero sí covariables y predicciones de ese año. La descripción correcta debe separar ambas cosas.

También hay una limitación operativa: la transformación de forma usa medias geométricas del lote. El procedimiento actual produce un archivo para una cartera completa; todavía no acredita una cotización estable de una póliza aislada. Antes de llamarlo tarificador operativo, fijaría las referencias de normalización y verificaría que la predicción de una misma póliza no cambia por acompañarla de otras filas. Esta observación procede de inspección de las fórmulas, no de una prueba nueva de inferencia.

### Capitales sin confirmación

La regla aplicada en F0 coincide con lo documentado: 1.454 ajustes adicionales, de los cuales 149 carecen de confirmación histórica. De estos últimos, 123 están en test: 77 de edificios y 46 de contenidos.

En S30 esas 123 filas suman 24.667,97 CU, aproximadamente el 0,01164 % del total predicho. Es un dato de alcance, no una sensibilidad contrafactual ni una prueba de que el riesgo sea inmaterial. Los casos de entrenamiento también pueden influir en otras predicciones. Mantendría el tratamiento como supuesto trazable del concurso, sujeto a aceptación real y sin trasladar automáticamente la división por mil al nuevo mercado.

## Reproducción y documentación que todavía no aprobaría

La receta contiene 36 nodos: S30 necesita 30 y S22, 32. El replay histórico de Windows acredita CSV exactos desde componentes guardados y conserva diferencias intermedias con salida 3. La batería histórica de 45 casos se vincula al código actual; no se volvió a ejecutar ni se contó como evidencia nueva.

Falta la cadena completa de recibos desde datos hasta modelos, calibradores y predicciones finales. En los productores LightGBM y CatBoost inspeccionados se ajustan estimadores y se guardan predicciones; no se persiste allí el estimador completo. La búsqueda de extensiones habituales en las dos líneas originales y `privado/` no encontró modelos de esos formatos. Eso no prueba que no existan en otro entorno o con otro nombre, pero impide afirmar hoy que se pueda recuperar toda la inferencia sin fitting.

Tampoco todas las salidas declaradas se cotejan: la receta excluye 12 salidas del nodo CFS_motor y una de CFS_motor_4s. La exclusión no se interpreta automáticamente como error; obliga a delimitar qué parte verifica realmente el contrato. El registro contiene los nombres exactos.

Dos afirmaciones documentales merecen corrección antes de publicar la entrega: `requirements.txt` garantiza una reconstrucción byte a byte aún no acreditada en toda la cadena, y el informe habla de resultados «equivalentes» sin una prueba de equivalencia. Esta revisión deja propuestas concretas en el registro, sin reescribir el historial ni cambiar el PDF ya revisado.

El panel es una fotografía anterior al último ciclo de auditoría: su fuente `ultimo_ciclo.json` cambió. Hay que leer GOV-007 con su remediación técnica posterior y su aceptación humana todavía pendiente. El número de hallazgos abiertos no se usa como número de defectos distintos. Las prioridades generales también conservan entradas históricas, como S06 pendiente; el estado común de entrega es la referencia vigente para S30/S22.

El índice Git inspeccionado no contiene artefactos restringidos por las rutas y extensiones buscadas. No equivale a una auditoría de secretos de todo el historial ni a una verificación nueva de permisos remotos. Siguen abiertos los vínculos completos de prompts auténticos con decisiones, el inventario efectivo de costes y licencias y la elegibilidad documental al premio. No inventaría evidencia para cerrar ninguna de esas casillas.

## Decisiones concretas para el cierre

| Decisión | Mi recomendación como revisor IA | Evidencia o intervención que falta |
| --- | --- | --- |
| Uso previsto | Limitar esta aceptación al concurso y a la cartera suministrada | Tu aceptación explícita de ese alcance; cotización real requiere controles adicionales. |
| Candidato | Mantener S30 provisional y S22 de respaldo | Decidir si aceptas S30 pese al criterio estadístico no superado; dejar razón y versión. |
| Reservas y variables | Conservar supuestos y limitaciones visibles | Aceptación de alcance; validación especializada pendiente cuando exista evidencia apropiada. |
| Capitales | Mantener trazabilidad de los 149 casos y de los 123 presentes en test | Confirmación o aceptación razonada; la cifra agregada no cierra el riesgo. |
| Reproducción | Recuperar recibos y piezas guardadas antes de prometer una cadena completa | Inventario por nodo y evidencia faltante; no sustituirlo con otro replay de mezcla. |
| Control del paquete | Reconocer la corrección técnica de GOV-007 | Decisión humana sobre la versión identificada, sin cerrar el resto de la reproducción. |
| Entrega de parte 1 | Confirmar el candidato y la selección final antes del viernes | Acción real del participante en Kaggle; esta revisión no seleccionó un envío. |
| Informe final y parte 2 | Incorporar adaptación observada y aportación real de IA | Nuevos datos y contrato, prompts vinculados, licencia/elegibilidad y revisión final. |

La consulta oficial de esta sesión confirma el cierre de parte 1 el viernes 23 de octubre de 2026 a las 11:00 de Bogotá y diez envíos diarios. Informe, video y código corresponden al cierre de parte 2. La rúbrica conserva 40 % para rendimiento/adaptación, 25 % para IA, 20 % para confianza y 15 % para comunicación. Son motivos para completar la evidencia y la explicación, además del score. [Reglas oficiales](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/rules).

## Evidencia y límites de esta revisión

- [Plan previo](../../../registro/revision_participante_20261019_plan.json), [registro consolidado](../../../registro/revision_participante_20261019.json) y [observaciones estáticas](../../../registro/revision_participante_20261019_estatica.json).
- [Auditor numérico](../../../herramientas/auditar_revision_participante.py) y [seguimiento de asignación](../../../herramientas/conciliar_asignacion_revision_participante.py). Resultados completos y fallos conservados bajo `privado/revision_participante_20261019*`, fuera de Git.
- [Consulta oficial de esta sesión](../../fuentes/revision_participante_20261019.json), [coordinación pendiente de reproducción y reservas](COORDINACION_REPRODUCCION_RESERVAS.md) y [acta humana sin firmar](../../../registro/revision_humana.json).

Las 163 fuentes de la corrida numérica permanecieron estables durante su lectura; el seguimiento conserva sus propios hashes. Se calcularon comprobaciones sobre datos y predicciones existentes. No hubo entrenamiento, nuevos modelos, inferencia, mezcla, envío, selección final, publicación externa, automatización ni delegación. El rol crítico solicitado queda ejercido y documentado; las aprobaciones humanas permanecen abiertas.
