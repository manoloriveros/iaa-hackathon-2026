# Saneamiento de los pendientes de semana 1

Codex, 19 de octubre de 2026. Trabajo solicitado por el participante y limitado, por su confirmación, a los archivos actuales. Manuel Ignacio Rodríguez queda designado para revisar: actuario con 13 años de experiencia en actuaría y supervisión, según la declaración del participante, con otro entorno disponible. La designación no acredita todavía revisión realizada, competencia específica confirmada por él, independencia o aceptación de riesgos.

Ya se prepararon los expedientes y herramientas que siguen. Catorce hallazgos siguen abiertos. GOV-007 queda cerrado únicamente en el alcance de su corrección técnica de la versión 1.2 por la aceptación expresa del participante, conservada en [la decisión fechada](../registro/decision_GOV007_20261019.json). Preparar evidencia, corregir una frase o designar revisor no demuestra que el supuesto científico esté resuelto. El [registro de saneamiento](../registro/subsanacion_20261019.json) separa el trabajo hecho de la evidencia que falta, sin reemplazar los registros históricos de los auditores.

## Qué se hizo con los archivos actuales

- Se extrajeron los 149 capitales pendientes a una hoja privada, con la identidad del periodo, ramo, capital anterior a la escala adicional F0 y capital usado. Incluye los 123 periodos de test. Cada fila tiene espacio para confirmar unidad, fuente y decisión. No se corrigió ningún importe ni se calculó una sensibilidad nueva.
- Se recuperaron cuatro mensajes auténticos del registro local de este chat y se vincularon a N62, los controles del paquete, la coordinación de reservas y este saneamiento. Los originales selectivos quedan fuera de Git. El mapa es parcial: no reemplaza los prompts ausentes de selección y calibración de Claude.
- Se creó un expediente temporal de columnas candidatas y un verificador que rechaza fechas desconocidas, avisos del corte o posteriores, publicación posterior, evidencia alterada, dependencias omitidas y ciclos. Son 18 pruebas nuevas de metadatos sintéticos, dos nominales y dieciséis adversas. No son pruebas de inferencia del modelo final ni repetición de los 45 casos históricos.
- Se preparó un preflight para el otro entorno. En la comprobación local por Codex coinciden las 51 huellas del manifiesto; todavía no es una corrida de Manuel ni una reproducción completa. También se preparó una matriz de cobertura para los 36 nodos y un protocolo para información futura, sin evaluar datos nuevos.
- Se corrigieron tres afirmaciones documentales: no equivalencia estadística demostrada, ausencia de costes observados de 2025 frente a uso de sus covariables/predicciones, y falta de prueba de reproducción completa byte a byte. El informe actualizado conserva cuatro páginas. Receta, fuentes de modelos, pesos y CSV se conservan.

## Estado de cada pendiente

| ID | Avance verificable en este encargo | Qué falta para resolverlo |
| --- | --- | --- |
| DATA-001 | [Ficha por columna candidata](../registro/disponibilidad_temporal_20261019.json), con fechas de acceso sin inventar y contratos identificados. | Documentos de captura/publicación y revisión de las variables efectivamente usadas. Una descripción del diccionario no prueba disponibilidad histórica. Una aceptación del alcance concurso no certifica cotización. |
| DATA-002 | [Protocolo de evidencia posterior](../registro/protocolo_evidencia_nueva_20261019.json), con cohortes y límites. | No hay valoración posterior en los archivos aportados. Obtenerla o aceptar expresamente el alcance limitado; no presentar la aceptación como validación con datos posteriores. |
| DATA-003 | [Índice de la hoja de revisión](../registro/capitales_revision_20261019.json); 149 fichas privadas, de ellas 123 de test. | Confirmación económica por caso y sensibilidad pertinente. El total predicho pequeño en esas filas no mide el efecto sobre el entrenamiento ni acredita inmaterialidad. |
| DATA-005 | Se conserva el alcance D75/preparados edificios/C04/C14. El nuevo verificador documental rechaza fechas posteriores o desconocidas. | Confirmar el instante operativo y las fechas de fuente; corregir y comprobar la rama afectada si se autoriza. El verificador no está integrado en el productor histórico y no elimina su desfase. No trasladar sus recuentos a S30. |
| MOD-001 | El informe reconoce la selección reutilizada y ya no afirma equivalencia. Se congela ahora el diseño de una evaluación futura. | Una muestra nueva no consultada o una aceptación expresa de la limitación. Repartir otra vez las etiquetas de 2024 no crea independencia. |
| MOD-002 | Se mantiene explícita la falta de identificación y se separan reservas, pagos futuros, recuperaciones y censura. | Desarrollo posterior comparable y juicio actuarial real. Los escenarios de ±25 % y la hipótesis de recuperaciones no demuestran suficiencia o ausencia de sesgo. |
| MOD-003 | Se explicitan la cadena de datos y las transformaciones por lote: prima anual, forma y regla de nivel. | Trazar los predictores efectivos, codificadores y dependencias de cada nodo; acreditar fechas por fila y una cotización operativa. La ficha de candidatas no es esa acreditación completa. |
| MOD-004 | Se enlaza la [revisión existente de segmentos e influencia](REVISION_DESDE_EL_PARTICIPANTE.md), sin repetir su cálculo. | Manuel debe revisar los ámbitos adversos y los intervalos condicionales, y decidir tolerancia. Un intervalo que contiene cero no demuestra equivalencia; falta evidencia externa para robustez futura. |
| MOD-005 | La [respuesta e inventario de Claude](RESPUESTA_CLAUDE_REPRODUCCION_RESERVAS.md) documentan la corrida no recuperable y la falta de modelos persistidos. | Los 31 nodos de ajuste/estimación necesitan volver a estimar con los artefactos disponibles. Eso sigue fuera de la restricción vigente, incluidos los siete GLM deterministas. No se promete recuperar la cadena mediante otra mezcla. |
| GOV-001 | Persona designada y [acta preparada](../registro/acta_subsanacion_20261019.json); solo está registrada la decisión técnica específica de GOV-007. | Revisión real de Manuel, alcance, competencia pertinente, conflictos, artefactos y fecha/firma. Su experiencia declarada no sustituye el acto de revisión. |
| GOV-002 | [Mapa de cuatro mensajes auténticos](../registro/mapa_prompts_20261019.json), con SHA, procedencia y artefactos. | Exportaciones auténticas de las decisiones de modelado aún ausentes, sus respuestas y correcciones. Los ensayos sintéticos de preparación no se usan como conversaciones reales. |
| GOV-003 | Preflight portable y campos para el recibo del otro entorno. | Ejecución real atribuida, entorno documentado y recorrido completo; la independencia se evalúa aparte. Copiar CSV o pasar el preflight no satisface este criterio. |
| GOV-004 | [Cobertura por nodo](../registro/cobertura_candidato_20261019.json), con guardas, salidas y huecos separados. | Persistencia y replay de estimadores, codificadores, casos límite e inferencia del candidato exacto, más revisión de cobertura. Las guardas sintéticas del orquestador no equivalen a esas pruebas. |
| GOV-006 | Originales y desfases documentados; se solicita al autor una aclaración fechada. | Explicar hora, huso y evento con fuente real o reconocer la hora desconocida. No usar modificación de archivos o el paso del reloj para reconstruir una preinscripción. |
| GOV-007 | Corrección técnica de la versión 1.2 aceptada expresamente por el participante; versión y evidencia enlazadas en el registro fechado. | Cerrado solo para esa corrección. Mantener abiertos reproducción completa, reservas y revisión independiente; una versión nueva requiere revisar el alcance. |

## Revisión que puede hacer Manuel ahora

El [acta](../registro/acta_subsanacion_20261019.json) recoge la aceptación técnica específica de GOV-007. Las otras decisiones están vacías y no hay firma de revisión actuarial general. Para cada asunto, registrar aceptar un alcance limitado, pedir corrección o mantener abierto, con motivo y archivos revisados. Una aceptación para el concurso puede documentar un riesgo asumido; no transforma el coste observado en último verdadero ni resuelve una fecha de disponibilidad desconocida.

La decisión recibida para GOV-007 se limita a la corrección técnica del paquete 1.2. Las [evidencias de controles y reproducción](verificacion.md) distinguen versiones y autores. El runtime identificado es `reproducir.py` SHA `a346d125520bfc5c784f1b9f65072759efdb15594263485434857e348475de17`. La batería final Windows de otro flujo y los controles propios anteriores conservan su procedencia; no se suman como nuevas ejecuciones. La aceptación de este punto no cubre MOD-005, GOV-003, reservas ni aprobación del candidato.

En el otro entorno, desde la raíz de esta carpeta y con un Python ya disponible:

```text
python -c "from pathlib import Path; Path('privado').mkdir(exist_ok=True)"
python herramientas/verificar_traspaso.py --operador "Manuel Ignacio Rodríguez" --salida privado/preflight_manuel.json
```

La herramienta no instala paquetes, no abre modelos y no entrena, infiere o mezcla. Registra el entorno efectivo y coteja código. Si alguna huella difiere, detenerse y registrar el desacuerdo; no actualizar las huellas para hacer pasar el control. El operador real debe conservar y aportar su propio recibo. Este documento no dice que Manuel haya corrido las órdenes.

Para revisar fechas, completar el expediente con evidencia local y un instante de cotización con huso. Este ejemplo de orden lleva un corte ilustrativo; debe sustituirse por el instante real y repetirse en el alcance apropiado, no adoptarse como fecha del proyecto:

```text
python herramientas/validar_disponibilidad.py --expediente registro/disponibilidad_temporal_20261019.json --cotizacion 2025-01-01T00:00:00-05:00 --salida privado/revision_disponibilidad.json
```

Con los campos actuales sin acreditar, el resultado es rechazo, código 1. Un resultado futuro conforme solo acreditaría coherencia de metadatos y hashes referenciados: falta revisar la veracidad, cobertura efectiva y disponibilidad por cada fila. No es un permiso automático para usar una variable.

## Lo que no se puede obtener de estos archivos

Una valoración única no permite demostrar ausencia exacta de sesgo o suficiencia última. La comparación entre cerrados y abiertos está afectada por maduración y selección; no identifica el momento de reconocimiento de recuperaciones. Los factores por retraso de reporte son estimadores bajo supuestos. El protocolo futuro incluye reserva cero, rechazados, reaperturas y claves estables, y deja la materialidad sin fijar hasta una justificación actuarial previa al nuevo contraste.

La reproducción completa tampoco se obtiene de los CSV finales. Si se autoriza en otro encargo volver a ajustar, antes habrá que fijar configuración y entorno, guardar modelos completos, codificadores y coeficientes a precisión completa, y comprobar su inferencia. Esos nuevos artefactos y hashes serán una nueva ejecución, sin reescribir la historia como si hubieran estado guardados desde el principio. En este saneamiento no se ha dado ni usado tal autorización.

Las recomendaciones de IA y las limitaciones aceptables para el concurso se revisan separadamente de validación profesional, independencia y selección final. Ninguna de esas decisiones está implícita en la solicitud de ayuda.


Seguimiento CLA-20261019-005 recibido,19oct2026. Claude refiere autorización humana en otra sesión para nueva corrida y materialidad1% por ramo; se conserva como informe recibido, no permiso nuevo de este chat o prueba de insesgadez. El manifiesto local tiene77 archivos conformes y no incluye la nueva capa captura. La carpeta local de corrida contiene solo transferencia, sin recibos/modelos; no se infiere actividad ni finalización remota. Codex confirma con dos casos sintéticos aislados por AST que _dig(DataFrame) y huella_pool conservan la clave al cambiar predictores. Son pruebas de identificación de entradas, sin modelos/fit/inferencia. Captura SHA39954720…f7593 no acredita esas entradas hasta corregir y verificar la capa. Dependencia cfg_total.json de cinco nodos frecsev2 confirmada estáticamente; la copia manual del autor es desviación documentada, no orden limpia sin preparación. Registro CLA-20261019-005_revision_codex.json y evidencia privado/trazabilidad/respuesta_CLA005_20261019. Se preservan modelos/corridas y el cierre técnico específico GOV007; los otros14hallazgos continúan abiertos. Reproducción completa, independencia y reservas siguen pendientes; no se repiten N62 ni pruebas históricas.


Seguimiento Codex de CLA006,19oct2026. Informe de sensibilidad SHA60e54b4e…565368 recibido y plan/adenda cotejados; sus102controles y métricas son resultados del autor, no recalculados aquí. COD118 precisa que influencia de6clientes no prueba equivalencia; semidistancia f23/f24 es escenario, no IC; variabilidad de semillas no es ruido público; total de ramo fijado por normalización no acredita inmaterialidad de los123capitales de test. Backtesting de conteos no aporta otra valoración de reservas; escenarios de IBNR/recuperaciones no son cotas identificadas. Ningún cambio de S30, niveles o criterio por este informe. Se comprobaron solo siete paquetes nuevos de reproducción:52miembros y13archivos de estimador con SHA/tamaño conformes a manifiestos, sin extracción, carga o inferencia; no es igualdad de predicciones contra receta. Actualiza la ausencia local del corte CLA005. Captura sigue SHA39954720…f7593 y sus claves incompletas pendientes; los dos casos no se repiten. Evidencia privado/trazabilidad/respuesta_CLA006_20261019 y registro/CLA-20261019-006_revision_codex.json. Reproducción completa/independencia/revisión humana/reservas y14hallazgos abiertos; GOV007 mantiene alcance técnico específico.
