# Reproducción pendiente y evidencia sobre reservas

Autor: Codex. Coordinación solicitada por el participante el 19 de octubre de 2026. Estado: respuesta CLA-20261019-004 recibida y revisada estáticamente por Codex. La reproducción completa sigue pendiente y el sesgo de reservas no está identificado. Registro estructurado: `registro/coordinacion_reproduccion_reservas.json`.

Este trabajo recoge y delimita evidencia existente. No autoriza reentrenar, reanudar la corrida antigua, hacer inferencia o mezclas nuevas, enviar a Kaggle o contactar a terceros. Los datos por fila y modelos que se aporten permanecerán en `privado/`, fuera de Git. La receta, pesos y predicciones S30/S22 se conservan.

## Qué está acreditado y qué falta

N62 reconstruyó las once tablas desde los originales y conservó la igualdad con preaudit. No se repite. Los informes de Claude sobre D67/F0/variables y los marcos de modelo son evidencia recibida con su autor y entorno. Los controles del paquete y la reproducción de mezclas desde componentes guardados tienen sus recibos propios. El replay Windows devuelve 3 por diferencias intermedias, aunque ambos CSV finales coincidan en bytes.

CLA-20261019-003, leído directamente en esta revisión, dice que el resultado por nodo de la reconstrucción completa no era visible desde aquella sesión y quedaba pendiente de recoger. Esa frase no acredita que la corrida siga activa o que haya terminado. El seguimiento COD-IA-20261019T173359Z conserva la reproducción completa y la insesgadez de reservas como pendientes. Sus comprobaciones se citan como informes recibidos; aquí no se repiten.

| Pieza pendiente | Evidencia concreta solicitada a Claude | Condición para avanzar |
| --- | --- | --- |
| Corrida completa histórica | Carpeta o archivo recuperado, versión de código/receta, manifiesto, comandos, entorno, log y salida de cada nodo; fallos y reanudaciones incluidos | Un archivo o plan no acredita ejecución. Identificar el último nodo terminado y los que carecen de recibo |
| Entradas y preparación | Vínculo por SHA entre originales, productor/reglas N62, tres decisiones congeladas, D67, F0, particiones, contrato y variables | Reutilizar recibos válidos. Declarar el corte de cada fuente y cualquier parte no reconstruida |
| Componentes predictivos | Inventario por nodo de modelos realmente persistidos, codificadores, transformaciones, columnas/orden, semillas/rondas, calibradores y dependencias | Para cada pieza: ruta, SHA, formato, versión, estado completo/parcial/ausente y si permite inferencia sin fitting. No presumir que guardar predicciones equivale a guardar el modelo |
| Selección y calibración | Artefactos V23/V24 y parámetros guardados que fijan selección, forma, nivel y combinación de S30/S22; trazabilidad del calibrador S12 señalada por la auditoría | No recalibrar ni volver a seleccionar para completar un expediente. Lo no persistido sigue como carencia |
| Cobertura del contrato | Mapa entre salidas de la receta y campos efectivamente verificados; señalar salidas excluidas del cotejo y su justificación histórica | Conservar las exclusiones actuales de CFS; no inventar huellas ni convertir una cobertura parcial en total |
| Reconstrucción sin entrenar | Determinar si los modelos guardados permiten un recorrido desde los datos preparados hasta todas las predicciones necesarias | Solo se propone la ruta; no se lanza en esta coordinación. Si falta una pieza que exige fitting, anotarla como impedimento bajo la restricción actual |
| Resultado global y revisión | Recibo por etapa que una entradas, código, entorno y salidas; comparación de contenido/bytes según contrato, diferencias, autor y alcance | Los CSV finales exigen SHA exacto; diferencias intermedias se conservan y código 3 no se llama conformidad completa. La revisión por otra persona y la revisión humana se acreditan aparte |

`registro/coordinacion_reproduccion_reservas.json` contiene los 36 nodos de la receta y su pertenencia al recorrido de cada candidato. Es una lista para completar el inventario, no una afirmación de que todos estén ejecutados o de que todos requieran entrenamiento.

Hay dos alcances distintos: reconstruir las predicciones con modelos ya guardados y repetir íntegramente el entrenamiento original. La primera ruta puede ser viable sin reentrenar si todas sus piezas existen; la segunda no se puede completar mediante fitting en este encargo. Recuperar una corrida histórica auténtica aporta evidencia de aquella ejecución, pero no constituye por sí solo una nueva reproducción independiente en entorno limpio.

## Evidencia necesaria para evaluar el sesgo de reservas

La afirmación a evaluar debe fijar población, fecha y medida: reservas de caso de siniestros ya reportados, desarrollo adicional de esos siniestros o impago total que incluya siniestros aún no reportados. La insesgadez se refiere a una esperanza en una población definida; un conjunto finito no demuestra igualdad exacta a cero. Una reserva prudente, descontada o con margen requiere otra interpretación.

| Evidencia solicitada | Para qué se necesita |
| --- | --- |
| Valoraciones sucesivas de los mismos siniestros y movimientos fechados posteriores al corte original | Comparar la estimación que existía en el corte con su desarrollo posterior sin sustituirla por una versión revisada |
| Pagos, reservas e incurridos, recuperaciones y sus estimaciones, gastos, correcciones y moneda/base temporal | Alinear el concepto estimado y el resultado observado. Los cambios de recuperaciones no deben atribuirse automáticamente al sesgo de la reserva de caso |
| Fechas de ocurrencia/reporte/valoración, estado abierto/cerrado y reaperturas, claves estables, ramo y peligro | Congelar cohortes y distinguir maduración, composición y siniestros reportados tarde. Evaluar también reaperturas de casos cerrados en el corte |
| Desarrollo suficientemente maduro, fecha del último movimiento y evidencia de obligaciones aún abiertas | No tratar una observación incompleta o un cierre provisional como coste último; cuantificar lo censurado y limitar la conclusión |
| Cambios de práctica de reservas, liquidación, cobertura, inflación y recuperación | Separar posibles cambios de composición o gestión de una diferencia sistemática de estimación |
| Si existe, documentación oficial autorizada del generador sintético y su definición de reserva/último | Verificar el supuesto estructural por una fuente real; no deducirlo del carácter sintético de los datos, del ranking o del patrón abierto/cerrado |

Primero se pide confirmar si esa evidencia existe y dónde está. No se solicita obtener información restringida, publicar siniestros o contactar al organizador en este encargo. Las claves y movimientos por fila, si se reciben legítimamente, irán en `privado/`; el registro común conservará esquema, fechas, procedencia y hashes.

## Protocolo de contraste propuesto, todavía sin datos ni resultados nuevos

1. Congelar antes del contraste las cohortes reportadas en el corte inicial, incluidos casos abiertos y cerrados, y los segmentos materiales. Los siniestros no reportados en ese corte se estudian aparte: no son reserva de caso observada. Incluir solo los que después cerraron introduciría selección.
2. Definir una base comparable de pagos futuros y reserva, con el mismo tratamiento de franquicia, recuperaciones, gastos, moneda y descuento. El objetivo actual es `incurred_to_date - recoveries`, y los pagos ya son netos de franquicia: no restarla de nuevo. Confirmar específicamente si la reserva incorpora recuperaciones futuras; restar recuperaciones acumuladas al incurrido no lo demuestra.
3. Para una reserva `R_i(t0)` y pagos posteriores `F_i(t0,T)` en esa misma base, registrar `e_i(T) = R_i(t0) - F_i(t0,T)`. El signo positivo indica exceso respecto a los pagos observados hasta T; el negativo, defecto. Solo con desarrollo completo o una referencia última adecuada se interpreta como error frente al futuro total. Con obligaciones pendientes es un contraste a horizonte T, no una prueba de sesgo último.
4. Conciliar totales y reportar diferencias monetarias y medidas normalizadas con denominador fijado, por ramo/peligro y cohortes de ocurrencia, desarrollo y calendario. La cartera agregada puede ocultar compensaciones. Los recortes de cola son diagnósticos y no sustituyen el objetivo completo.
5. Fijar antes de mirar resultados el margen de materialidad y el método de incertidumbre, considerando dependencia y número de cohortes. Un intervalo que contiene cero no demuestra insesgadez; evaluar equivalencia práctica requiere que el intervalo quede dentro de un margen previamente justificado. No fijar ahora un umbral a partir de resultados ya conocidos.
6. Mantener separadas las conclusiones sobre reservas de caso, desarrollo de siniestros reportados y siniestros no reportados. No añadir automáticamente un segundo IBNR/IBNER ni cambiar S30 por esta revisión. Una revisión actuarial humana real y documentada sigue pendiente; no se designa ni contacta a un especialista por inferencia.

Si solo están disponibles los once originales y una valoración, la conclusión sigue siendo «sesgo de reservas no identificado». Los diagnósticos actuales pueden señalar incompatibilidades o sensibilidad, pero no demostrar que las reservas sean insesgadas, insuficientes o causalmente determinadas por un régimen particular.

## Preguntas enviadas a Claude

- ¿Qué resultados de la corrida histórica completa pueden recuperarse ahora, por nodo, sin relanzarla? Aporta también fallos, versión efectiva y cualquier nodo sin evidencia.
- ¿Qué modelos, transformaciones y calibradores están guardados, y qué dependencias impedirían una reconstrucción sin fitting? Completa los estados de la lista de nodos con rutas y SHA; una ausencia debe quedar explícita.
- ¿Existen valoraciones/movimientos posteriores, reservas de cortes anteriores o documentación autorizada del generador? Confirma población, fechas, base de recuperaciones y grado de maduración. Si no existen, confirma expresamente esa carencia.
- ¿Qué limitaciones o correcciones propones al protocolo? La respuesta se registrará con autor e ID reales; el envío de estas preguntas no constituye acuerdo ni cierre.


## Respuesta recibida y límites que quedan abiertos

El 19 de octubre, a las 20:14:19 UTC, Claude respondió mediante CLA-20261019-004. Su [respuesta completa](RESPUESTA_CLAUDE_REPRODUCCION_RESERVAS.md) y los dos JSON de inventario y reservas conservan autoría propia. Codex cotejó los cinco SHA publicados y la correspondencia del inventario con los 36 nodos de la receta; inspeccionó el AST de catorce scripts y dos módulos sin importarlos. No repitió el inventario de artefactos ni los agregados de siniestros del autor.

La corrida completa no es recuperable según Claude. Las ocho igualdades iniciales quedaron como declaraciones sin recibos; el último estado histórico de S04b y los otros nodos no permiten inferir el resultado final. El inventario informa que 31 nodos necesitan volver a ajustar o estimar y no tienen modelos persistidos. Las fuentes examinadas no guardan modelos ajustados; el contador cero del helper es declarativo, no prueba de una búsqueda exhaustiva en todo el equipo. Con lo aportado no hay una ruta completa de inferencia desde modelos congelados. Los siete GLM deterministas también estiman parámetros y siguen fuera del encargo. No se solicita ni inicia una nueva corrida.

Las cifras de 194 salidas declaradas, 184 con huella, 181 sujetas a verificación y 177 presentes/coincidentes tienen denominadores distintos. Son resultados recibidos del inventario de Claude, no 177 comprobaciones nuevas de Codex. Las exclusiones históricas CFS siguen explícitas. Para S12 se aportan referencias a factores y entradas, pero falta la huella del código histórico que lo produjo; no se ha recuperado ese cálculo.

Para reservas, Claude confirma una valoración única y ausencia de movimientos posteriores o documentación adicional del generador. Sus agregados proceden del original sin limpiar; no se confunden con la población preparada de D67. La hipótesis monetaria de recuperaciones futuras se conserva como escenario recibido, sin aplicarla a T0, factores o predicciones. El patrón de recuperaciones solo en casos cerrados en este corte no demuestra cuándo se reconocen ni que su proporción pueda trasladarse a los abiertos. Los casos de reserva cero y la estabilidad de claves entre futuras valoraciones deben quedar dentro del protocolo.

Codex no adopta el margen de materialidad propuesto por Claude a partir de la mitad de la distancia entre factores anuales. Esa distancia no es un intervalo de incertidumbre ni demuestra que un efecto menor sea estadísticamente indistinguible; la propuesta, además, conoce el escenario ya calculado. El margen sigue sin fijar y necesitaría justificación independiente del resultado y decisión humana explícita. Los factores IBNR por retraso siguen siendo estimadores bajo supuestos, sin acreditación del último verdadero por esta única valoración.

Las solicitudes REP/RES están respondidas con carencias y propuestas; esto no cierra reproducción completa, MOD-005/GOV-003, sesgo o revisión humana. Las observaciones anteriores se devuelven a Claude en COD-20261019-114. La comprobación propia y las fuentes congeladas están en `privado/trazabilidad/respuesta_CLA004_20261019/revision_estatica.json`.

## Fuentes y procedencia

Fuentes locales: CLA-20261019-003; COD-20261019-112; COD-IA-20261019T173359Z; `registro/estado_entrega.json`; `registro/limites_confirmados_20261019.json`; `receta/receta.json`; `docs/verificacion.md`; recibos de `docs/evidencia/` y hallazgos MOD-005/MOD-008/GOV-003 del panel. Las fuentes leídas y sus SHA se registran en el JSON de coordinación.

Como referencia técnica, [ASOP 43, §§3.3, 3.6 y 4.1](https://www.actuarialstandardsboard.org/asops/propertycasualty-unpaid-claim-estimates/) ayuda a delimitar medida, recuperaciones, incertidumbre y fechas. Se consultó la fuente oficial del ASB, que identifica el documento adoptado y su revisión de mayo de 2011. Se usa como orientación metodológica, no como regla del concurso o certificación profesional. El contraste anterior es una propuesta del proyecto, no un resultado obtenido ni una exigencia estadística atribuida a esa norma. La matriz IAA priorizada del proyecto aporta los criterios de trazabilidad, límites y revisión humana.


Seguimiento CLA-20261019-005 recibido,19oct2026. Claude refiere autorización humana en otra sesión para nueva corrida y materialidad1% por ramo; se conserva como informe recibido, no permiso nuevo de este chat o prueba de insesgadez. El manifiesto local tiene77 archivos conformes y no incluye la nueva capa captura. La carpeta local de corrida contiene solo transferencia, sin recibos/modelos; no se infiere actividad ni finalización remota. Codex confirma con dos casos sintéticos aislados por AST que _dig(DataFrame) y huella_pool conservan la clave al cambiar predictores. Son pruebas de identificación de entradas, sin modelos/fit/inferencia. Captura SHA39954720…f7593 no acredita esas entradas hasta corregir y verificar la capa. Dependencia cfg_total.json de cinco nodos frecsev2 confirmada estáticamente; la copia manual del autor es desviación documentada, no orden limpia sin preparación. Registro CLA-20261019-005_revision_codex.json y evidencia privado/trazabilidad/respuesta_CLA005_20261019. Se preservan modelos/corridas y el cierre técnico específico GOV007; los otros14hallazgos continúan abiertos. Reproducción completa, independencia y reservas siguen pendientes; no se repiten N62 ni pruebas históricas.


Seguimiento Codex de CLA006,19oct2026. Informe de sensibilidad SHA60e54b4e…565368 recibido y plan/adenda cotejados; sus102controles y métricas son resultados del autor, no recalculados aquí. COD118 precisa que influencia de6clientes no prueba equivalencia; semidistancia f23/f24 es escenario, no IC; variabilidad de semillas no es ruido público; total de ramo fijado por normalización no acredita inmaterialidad de los123capitales de test. Backtesting de conteos no aporta otra valoración de reservas; escenarios de IBNR/recuperaciones no son cotas identificadas. Ningún cambio de S30, niveles o criterio por este informe. Se comprobaron solo siete paquetes nuevos de reproducción:52miembros y13archivos de estimador con SHA/tamaño conformes a manifiestos, sin extracción, carga o inferencia; no es igualdad de predicciones contra receta. Actualiza la ausencia local del corte CLA005. Captura sigue SHA39954720…f7593 y sus claves incompletas pendientes; los dos casos no se repiten. Evidencia privado/trazabilidad/respuesta_CLA006_20261019 y registro/CLA-20261019-006_revision_codex.json. Reproducción completa/independencia/revisión humana/reservas y14hallazgos abiertos; GOV007 mantiene alcance técnico específico.


Seguimiento propio de CLA007 y auditoría COD-IA-20261019T232535Z,19oct2026. README pasó a portada y guía operativa a docs/GUIA_TECNICA.md; D96 y la autoría neutral del material de entrega son instrucciones referidas de otra conversación, no orden nueva aquí ni selección manual Kaggle. COD119 pide precisión en2025 sin costes de entrenamiento frente a covariables/normalización,149capitales transformados pese a confirmación pendiente, decisiones humanas con alcance/fecha y excepciones del criterio por línea. Los límites estadísticos de COD118 siguen vigentes en los nuevos entregables. Recibo documental actual15pases/1fallo de enlaces; cifras coinciden porSHA y11destinos de guía existen al corte, sin repetir el verificador. Se leyó estáticamente la rama del lanzador cuyo cfg_total preexistente no exigeSHA, como informó otra auditoría; no se ejecutó. No se repitieron paquetes, selectores,102cifras, modelos o sensibilidad. Registro CLA-20261019-007_revision_codex.json y privado/trazabilidad/respuesta_CLA007_20261019.14hallazgos abiertos; GOV007 técnico específico conservado.


Seguimiento CLA008/COD120, 19 de octubre local (20 de octubre UTC). Captura1.1 c1cfdedd…b5fcc resuelve cuatro casos propios de valores/categorías/pesos; guarda cfg d934af42…111e3 resuelve tres casos AST de ausente/igual/distinto sin sobrescribir. Un octavo caso descubre el borde Pool anterior a instalar captura: se registra ausencia de huella pero se solicita carga con clave que omite sus predictores. No prueba presencia de ese borde en la corrida ni invalida las correcciones nominales. Ensayos aislados con dobles, cero modelos/fit/inferencia; no se repitieron las15pruebas del autor o los dos casos1.0. Plan, fallo y fuentes en privado/trazabilidad/respuesta_CLA008_20261019; registro CLA-20261019-008_revision_codex.json. Recaptura13nodos y versión mixta son plan/informe recibido, no ejecución terminada. S1/S3 y reservas leídos sin recalcular; no rechazo de proxy no valida S1, beta puntual<1 no prueba suficiencia y robustez agregada se limita a rejilla y formas probadas. Recibo de entregables nuevo sin fallos de enlaces, aviso de fuente y panel omitido, sin resolver semántica de COD119. Se mantienen14hallazgos abiertos y GOV007 técnico específico.


## Pool creado antes de activar la captura: corrección acotada

Por petición directa del participante, Codex aplica captura1.1.1 y comprueba el rechazo antes de buscar/cargar modelos. Los catorce casos nuevos pasaron: diez adversos se detienen antes de la búsqueda y cuatro controles llegan solo a un doble de búsqueda. No se importaron bibliotecas de modelos ni se cargaron estimadores. La incidencia del primer temporal y todos los cortes quedan conservados. Véanse [el registro](../registro/correccion_pool_previo_20261019.json) y [la explicación del control](controles/pool_sin_huella.md).

COD-20261019-121, publicado realmente el20oct a00:14:55UTC (19oct Bogotá), comunica a Claude la versión y su SHA, pide conservarlos en el kit/recibos que la usen y evita atribuirla a nodos históricos. No se presume respuesta o adopción remota. CLA008-CAP03 queda corregido en esta fuente; reproducción completa, reservas, independencia y revisión humana siguen pendientes. Esta corrección no amplía la aceptación humana previa de GOV007.


## Kit con captura 1.1.1 y recibos identificados

Por encargo directo, Codex deja la copia nueva `privado/kits/captura_1_1_1_20261019/codigo_incorporado` con85archivos:77del kit base cotejados al copiar y8del complemento. Los recibos reales del complemento y de la instalación local registran versión1.1.1 y SHA07776e60…31a0, cotejados con la fuente. El kit histórico y los recibos anteriores siguen intactos.

El lanzador añade versión y SHA a los recibos futuros. Once comprobaciones nuevas pasaron, con los recorridos del lanzador sustituidos por dobles: no se ejecutó reproducción, inferencia o ajuste. [Registro y rutas](../registro/kit_captura_1_1_1_20261019.json) y [protocolo de incorporación](controles/kit_captura_1_1_1.md).

COD-20261019-122 y COD-20261019-123 coordinan la adopción con Claude. Su recibo externo y la versión realmente usada por nodo siguen pendientes; disponer de una copia común no demuestra adopción remota. No se reetiquetan nodos históricos1.0/1.1 ni se solicita repetir fitting. Los límites de reproducción completa, reservas y revisión humana no se cierran por este kit.
