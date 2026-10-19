# Anexo técnico de la primera semana

Este anexo conserva el detalle del informe anterior a la revisión editorial solicitada por el participante. Los identificadores, cifras exactas, parámetros y referencias sirven para localizar y contrastar evidencia. El informe principal presenta la explicación y los resultados de forma resumida. Los alcances pendientes conservan su estado.

Las referencias a un PDF de cinco páginas dentro del texto conservado corresponden a la versión anterior. El PDF vigente se enlaza desde el informe principal.

[Volver al informe](INFORME_SEMANA1.md) · [Panel de revisión](panel_revision.html) · [Evidencia de reproducción](verificacion.md)

---

# Prima de riesgo por periodo de póliza: semana 1

Borrador para revisión del participante, 19 de octubre de 2026, Bogotá. El informe del concurso debe cubrir las dos partes; solo se califican sus primeras cinco páginas. Este documento prepara la primera y conserva pendientes reales. La versión PDF tiene cinco páginas; el panel amplía datos, ensayos y evidencias para la revisión.

## 1. Propósito, resultado y estado de entrega

El reto pide el coste último esperado de cada periodo de póliza de 2025 en autos particulares, edificios y contenidos del hogar, en unidades monetarias ficticias (CU). Incluye siniestros ocurridos durante la cobertura, netos de franquicia y recuperaciones, y excluye rechazados. La prima comercial escrita no es la variable objetivo. La métrica publicada es D² Tweedie con potencia 1,5, que se maximiza; no es un porcentaje de aciertos.

El candidato principal de revisión es S30, una mezcla por ramo construida por Claude a partir de componentes conservados de su línea principal y su línea B. El respaldo es S22. La preparación de datos y parte de la verificación incorporan trabajo de Codex. La gestión se unifica desde hoy sin cambiar ese linaje. S30 conserva un CSV de 626.639 filas con SHA-256 `fd9528e0b1ee4b674dea63834a97523fd4ddc743d1495a422ce31a2eb76e3bc5`, envío Kaggle 57371361, estado COMPLETE y score público 0,12996. S22 tiene score público 0,12988, envío 57370117. Fuente: recibos archivados en `docs/evidencia/recibo_S30.json` y `recibo_S22.json`.

S30 alcanza D² local V24 completo de 0,137879634652177 sobre T0, con ganancia 0,000138041187091 frente a S22. La ganancia agregada es pequeña: el IC95 condicional por cliente [-0,00008236; 0,00036948] y por dirección [-0,00007807; 0,00038911] incluye cero. No se presenta como superioridad concluyente. El objetivo y muestra del leaderboard difieren de los de la validación local.

La revisión actual vuelve a comprobar esquema, cobertura de los tres test, IDs únicos, orden frente a sample_submission, valores finitos no negativos y SHA de ambos CSV frente a entrega y recibo. También coteja los once originales. Copias exactas quedan en `privado/predicciones/`, fuera de Git. La revisión no produce nuevas predicciones ni entrena. Los resultados exactos están en `docs/evidencia/preflight.json` y `registro/panel_datos.json`.

El cierre de la parte 1 es el viernes 23 de octubre de 2026 a las 16:00 UTC, 11:00 a. m. Bogotá, según metadatos oficiales consultados el 19 de octubre. Los CSV ya puntuados son candidatos; no se acredita selección final manual. Las reglas permiten elegir hasta uno y toman el mejor público si no se elige. Informe, video, ambos CSV y repositorio se entregan al finalizar la parte 2, por un formulario cuyo enlace sigue pendiente. Fuentes oficiales archivadas: `docs/fuentes/reglas_kaggle_20261019.json`, páginas rules y Submissions.

## 2. Datos, limpieza y construcción del objetivo

Se conservan once Parquet sintéticos: clientes, direcciones, clima dirección-año, siniestros, tres tablas de pólizas 2021-2024, tres test 2025 y la plantilla. Hay 2.409.311 periodos de entrenamiento y 626.639 de test. El diccionario de 107 campos y los perfiles originales D30/D61 están en el panel; ese corte histórico precede al modelado. Las claves permanecen como texto. Clientes y direcciones pueden repetirse entre ramos y años, por lo que la dependencia se considera al analizar incertidumbre.

| Regla base | Cambio documentado | Alcance e interpretación |
| --- | --- | --- |
| ID01 | 123.664 claves de cliente de autos | Normalización contra maestro, sin cambiar identidad asegurada |
| EXP01 | 14.229 exposiciones | Conversión de registros en días o ACT360 a años |
| CAP01 | 2.073 capitales extremos | Escala /1000 con referencia anterior admisible; base conserva 1.454 pendientes |
| CAT01 | 700.210 valores de construcción | Unificación de alias por mayúsculas; no resuelve por sí sola t/w |
| AGE01 | 2.936 edades de hogar | Convención de edad al inicio, no 2.936 errores demostrados; dos diferencias D59 sin explicar |
| DUP01 | 604 copias de siniestro | Exclusión por igualdad estricta, conservando 162.546 siniestros |
| REN00 | 12.041 periodos de 2.742 pólizas | Marca de continuidad con rechazo de renovación; solo auditoría |
| PRE00 | 413 siniestros | Marca de prehistoria; se preservan y no se asignan a T0 del historial |

N62 reconstruyó históricamente las once tablas de la base con igualdad en bytes; su comparador conserva 148.424.183 celdas sin diferencias. Esa corrida no se repite al organizar el expediente. La base activa es preaudit. La rama retrospectiva de capitales se documenta aparte. D66/D68 trata los 1.454 restantes en F0: 1.305 apoyados por historia y 149 bajo PRM01-R sin confirmación. No se atribuyen esas 1.454 transformaciones a los originales ni a la capa base. Las marcas audit_* quedan excluidas de predictores.

D67 asigna cada siniestro por policy_id, ramo y fecha de ocurrencia al periodo cubierto, una sola vez. Los 160.432 aceptados asignados producen T0 = incurred_to_date - recoveries; no se vuelve a restar franquicia porque paid_to_date ya es neto. Rechazados fuera y periodos sin aceptados con cero. T0 suma 741.156.868,43 CU; 146.368 periodos tienen coste positivo. La reserva de caso abierta asciende a 90.168.216,94 CU. Son conciliaciones históricas D67, no importes últimos observados.

## 3. Método, variables y receta congelada

La etiqueta T0 usa la valoración declarada del 31-12-2024. La fecha máxima observada de reporte es 30-12-2024; se conserva la distinción. Hay siniestros no reportados y abiertos que cambiarán. El modelo aprende T0 con exposición efectiva, calculada mes a mes mediante completitud de reporte por peligro estimada con chain-ladder de conteos. Su logaritmo actúa como offset. En 2025 se usa exposición nominal, de modo que no se multiplica otra vez por el mismo IBNR. La receta no agrega IBNER sobre las reservas de caso; su suficiencia sigue siendo un supuesto no identificado con una sola valoración.

La validación temporal usa V23: ajuste 2021-2022, parada del boosting en mitad de calibración 2023 y medición en mitad de selección por cliente. V24 ajusta 2021-2023, usa rondas V23 multiplicadas por 1,15 y mide 2024. Producción ajusta 2021-2024, rondas por 1,3, y predice 2025. V23 y V24 se reutilizaron para elegir modelos, pesos y reglas; no son una evaluación final independiente. Las etiquetas históricas tienen valoración posterior y no existen snapshots anteriores para reconstruirla sin supuestos.

| Ramo | Componente S30 | Peso |
| --- | --- | ---: |
| Autos | CatBoost Tweedie total, cuatro semillas | 0,20 |
| Autos | CatBoost Poisson por peligro × severidad GLM con tendencia | 0,60 |
| Autos | LightGBM total F0124 y F3 autos | 0,10 |
| Autos | LightGBM reducido | 0,10 |
| Edificios | LightGBM con siete F3 y hoja mínima 1.000 | 0,40 |
| Edificios | CatBoost por peligro × severidad por capital con tendencia | 0,30 |
| Edificios | Frecuencia aditiva × severidad por capital con tendencia | 0,30 |
| Contenidos | LightGBM con siete F3 | 0,30 |
| Contenidos | Frecuencia aditiva × severidad modelada | 0,30 |
| Contenidos | Frecuencia aditiva × GLM con covariables físicas | 0,40 |

Autos usa exponentes 1,09 para tasa y 0,95 para exposición; contenidos, 1 y 0,95. El nivel 2025 toma la media de factores Tweedie óptimos de V23 y V24. La regla s17 aparta de la referencia de nivel los componentes cuyo cociente total 2025/V24 se aleja más de 1,5 % del ancla; siguen aportando forma. Las tendencias de severidad extrapolan un año con tope ±15 %. Todo esto está congelado en las especificaciones y 36 nodos de `receta/receta.json`.

## 4. Verificación, experimentos y limitaciones

Se separa cada evidencia por corte y autor. D59 conserva 41 comprobaciones sobre ocho reglas base y la rama hasta CAP05R; no certifica capas posteriores. D67 conserva 18 controles y D68, 25. La integral recibida del 19 de octubre, 12:02 UTC, informa 99 controles de datos y 429 de modelos. Estos conteos y los 49 pytest históricos no se cuentan como pruebas nuevas. La comparación S22/S30 conserva 72 ámbitos con D² completo, semestres, segmentos, escenarios fijos de reserva e influencia; los recortes de cola se presentan solo como diagnósticos.

S30 mejoró levemente completo y cuerpo en V23/V24 y obtuvo +0,00008 público frente a S22. El criterio de cuerpo se motivó con el orden público de pocos candidatos, por lo que añade selección. Más semillas (S33), pesos/calibración por segmento, deriva de frecuencia S34/S34s y ruptura de severidad S35 no aportaron evidencia suficiente para sustituir S30. El clima del año S31 no se entregó. Los README históricos copiados y el índice del panel conservan pruebas y resultados adversos; tener un plan o un archivo no acredita un proceso activo.

Los CSV se reprodujeron históricamente desde componentes guardados en nube y VM. La VM produjo diferencias de último bit en Parquet y CSV exactos; con versión 1.1 el modo diagnóstico devuelve código 3, no éxito íntegro. La reconstrucción completa de componentes desde originales sigue pendiente de recoger. No se presenta la reproducción de mezcla como reentrenamiento completo ni reproducción por otra persona.

En esta revisión, la batería 1.1 se interrumpió en Windows por privilegios de symlink y codificación de consola. La versión 1.2 copia insumos, resuelve la ruta de entrada y arranca los dos escritores finales con serialización LF, sin modificar los scripts de modelo, etiquetas o pesos. La batería final de 45 casos pasa: nueve nominales y 36 adversos, incluido el código 3 exacto, sin etapas reales. El replay real desde 47 archivos congelados en la carpeta común reproduce ambos CSV byte a byte. Los Parquet conservan diferencias relativas máximas inferiores a 7,2 × 10^-16; el proceso devuelve 3 y no acredita igualdad completa. Evidencia: `docs/controles/20261019_windows_v12_lf/resultado.json` y `docs/evidencia/replay_windows.json`. Los intentos iniciales adversos se conservan.

Quedan abiertos: disponibilidad temporal de F3, telemática, historia y clima; valoración única e IBNER no observado; 149 capitales sin confirmación; selección sobre V23/V24 y público; reproducción completa y por otra persona; revisión humana especializada; trazabilidad completa de prompts y una aclaración cronológica histórica. GOV-007 tiene corrección técnica posterior al registro importado, sin cierre automático global. Cada límite tiene criterio de cierre y fuente en el panel; los especialistas humanos aún no están designados. Las verificaciones IA no equivalen a validación profesional independiente.

## 5. IA, responsabilidad, adaptación y operación

El participante dirige el problema y conserva las decisiones y responsabilidades. Claude construyó las líneas predictivas que forman S30/S22; Codex desarrolló reglas y el productor N62, contrastó entregas y controles y consolidó el expediente. Las revisiones cruzadas detectaron controles permisivos del orquestador y afirmaciones excesivas sobre reservas. Los parches, fallos y pruebas posteriores muestran una aportación verificable de la IA a la fiabilidad. No se inventan transcripciones de prompts ni firmas humanas; el registro de conversaciones completas sigue pendiente.

La rúbrica oficial pesa rendimiento/adaptación 40 %, IA 25 %, confianza/controles 20 % y comunicación 15 %. La primera categoría combina scores privados de ambas partes con igual peso y evaluación del jurado de métodos y adaptación; no se inventa otra ponderación. El informe final reservará espacio para lo que cambie en la segunda semana. Al llegar los datos se contrastarán contrato, unidades, exposición, mezcla de riesgos, faltantes, disponibilidad de predictores, desarrollo y estabilidad. Se congelará una referencia antes de adaptar, con hipótesis, criterios y resultados adversos; aún no hay evidencia del segundo mercado.

La carpeta común es `Hackaton/Repositorio_IAA2026`: código en src, receta en receta, documentación en docs, seguimiento en registro y archivos restringidos en privado, excluido de Git. Originales y corridas previas quedan en sus rutas como evidencia. El repositorio privado es https://github.com/manoloriveros/iaa-hackathon-2026. Git comienza el 19 de octubre; el desarrollo anterior se conserva por hashes, decisiones y foro, sin commits retrospectivos inventados. No se suben datos, predicciones por fila, checkpoints o credenciales. Licencia de entrega, costes reales de herramientas y elegibilidad documental para premio siguen pendientes de revisión. El equipo continúa individual; no hay contacto nuevo a terceros ni inscripción en asociaciones.

Para inspeccionar la receta: `python reproducir.py plan`. Para mezcla desde artefactos autorizados: `python reproducir.py mezcla --semana1=<Semana 1> --trabajo=privado/mezcla`. Componentes/todo implican entrenamiento y no se lanzaron en esta preparación. Entorno de referencia declarado en requirements y entorno; los controles Windows usan Python 3.12.14, numpy 2.3.5 y pyarrow 26.0.0. Códigos 0/1/2/3 distinguen coincidencia, fallo, uso incorrecto y diferencias toleradas. Antes del viernes: revisión del participante, evidencia de reproducción pendiente, decisión del candidato y confirmación de selección en Kaggle. El acta humana queda sin aprobar hasta que se registre una decisión real.
