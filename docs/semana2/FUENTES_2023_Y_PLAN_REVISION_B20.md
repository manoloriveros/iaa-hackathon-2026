# Fuentes2023 para revisar mecanismo y soporte de B20

Codex, corte UTC 2026-10-24T12:48:49.630901+00:00. No se confirmó una cohorte adicional de 2023 ni una corrección material de los datos. Sí se identificó un cambio de metadatos de publicación que merece resolver primero y fuentes existentes con preguntas de procedencia/semántica aún pertinentes al mecanismo. No las presento como nuevos siniestros o como variables nunca usadas en otro modelo del proyecto.

## Qué se buscó y qué apareció

Se consultó el [diccionario oficial](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data) mediante KaggleMCP y el inventario autenticado de archivos, sin descargar tablas. El diccionario es igual al archivado. El inventario actual contiene24 Parquet activos de developed/emerging: mismos nombres y tamaños que sus equivalentes históricos. Las fechas de creación remotas ahora son del24 de octubre alrededor de 03:07UTC; las históricas eran del22. No se atribuye la causa a la incidencia de envío ni se infiere cambio de contenido por esa fecha.

El inventario histórico también contenía11 rutas archive/public y dos desktop.ini, ausentes en el actual; se separan de los24 Parquet activos para no llamar ampliación o pérdida de una cohorte a un cambio de estructura del catálogo. La consulta de campos confirmó que el servicio devuelve solo nombre,tamaño,fecha, sin checksum. Mismo tamaño no prueba igualdad binaria. Los hashes locales siguen en el manifiesto de descarga; no se recalcularon o compararon con un hash remoto inexistente en esa respuesta.

El conector integrado no exponía el listado. La CLI local no tenía el paquete Kaggle; no se instaló. Se usó el cliente MCP existente para una petición limitada al inventario con acceso de red aprobado, sin leaderboard, notebooks, descargas, filas o cambios de cuenta. Esa consulta de procedencia no repite un diagnóstico predictivo o cotejo de test. Los intentos y la respuesta filtrada quedan guardados sin credenciales.

## Prioridad y contribución esperada

| Orden | Fuente y disponibilidad | Qué podría aportar | Límite y primer paso |
| --- | --- | --- | --- |
| 1, F01 | Versión oficial de claims,policies_buildings,addresses emergentes: metadatos consultados, contenido pendiente | Una nota de corrección/versionado o checksum podría establecer si hay una fuente 2023 realmente distinta | Buscar evidencia oficial de contenido. No descargar tablas mixtas o test. Si no existe, dejar identidad de versión no resuelta; si hashes coinciden, no repetir revisión |
| 2, F02 | Declaraciones y términos de edificios 2023; archivo/diccionario existentes, condiciones/endosos completos no localizados | Delimitar heterogeneidad técnica y significado del coste neto usando construcción,ocupación,desocupación,alarmas,franquicias | Revisar definición y fecha de declaración. No sumar positivos o recalcular bandas/A/E; campos fuera de B20 no crean nuevas observaciones |
| 3, F03 | Cartera desarrollada 2023, disponible en originales multiaño y ya relacionada con prior histórico | Contrastar semántica y transportabilidad contractual como contexto separado | Solo correspondencia documental 2023. No juntar mercados, sumar su soporte al emergente o cargar modelos/scores de 2024 |
| Alta si aparece, F04 | Movimientos/cortes de siniestros de ocurrencia2023 o cohorte emergente adicional: no localizados | Es la vía potencial para nueva información de maduración o componentes reales que pueda afectar G1/G2 | No prometer disponibilidad. Exigir fuente legítima,fecha,valoración,llaves y extracción solo 2023; no sustituirla con simulación o remuestreo |
| Baja, F05 | Clima anual sintético 2023: ya existente | Solo una aclaración oficial nueva de hazard estático frente a realización anual podría aportar contexto | No repetir el diagnóstico climático. Año realizado no es información disponible al inicio de 2023; no usar años posteriores |

## Primera revisión documental accesible

El contrato F0 enumera x_construction_type,x_occupancy,x_days_unoccupied,x_smoke_alarms,x_voluntary_excess y x_compulsory_excess. La receta B20 de siete efectos de edificios no los incluye. Esa diferencia de listas se comprobó en los metadatos, sin leer valores o medir efectos. No se afirma que nunca hayan aparecido en otra receta amplia.

La revisión debe precisar qué era conocido al cotizar o al iniciar cada periodo 2023. days_unoccupied necesita distinguir declaración de experiencia realizada. Los campos físicos sin fecha conservan la hipótesis de estabilidad del maestro, no una fotografía histórica demostrada. Construcción conserva su regla de calidad/codificación; no se retoca para mejorar un score. La documentación dice que paid_to_date ya es neto de franquicia: no descontarla de nuevo.

No se añaden automáticamente campos por estar en F0 ni se propone ampliar el GLM ahora. Esta fuente podría ayudar a formular o descartar una explicación de G1; no altera el soporte de las bandas originales y no resuelve por sí sola G2. Una revisión posterior de valores necesitaría lectura restringida a2023 antes de materializar datos; no se ejecuta un productor que lea todos los años.

## Fuentes que no resolverían el bloqueo

Las regiones E01–E06, direcciones y moneda son sintéticas, según el diccionario. No se encontró una correspondencia geográfica que admita unir siniestros/clima reales de 2023. No se inventa esa correspondencia ni se recomienda una descarga externa sin ella. Información real general no añade componentes de esta cartera ficticia.

reference_policies son 20 pólizas 2025 tomadas del test y expenses sirve para prima comercial; no son fuentes de siniestros2023 y no se abrieron. El único claims oficial descrito es un snapshot de valoración, no historial de transacciones. Los grupos ya trazados, curvas,perils,reservas y metadatos C0 siguen como evidencia anterior; no se renombran como fuente nueva o repiten para llenar el plan.

## Plan finito de revisión y parada

F01: hasta20 minutos documentales si existe evidencia oficial accesible de versión; ante falta de checksum/cambio documentado, dejar la carencia sin más peticiones idénticas. F02: 30–45minutos de semántica/disponibilidad de los seis campos y condiciones2023, con ficha que separe hechos y supuestos. F03: 20–30minutos de correspondencia documental si hay sustento para comparar mercados; detenerse si no lo hay. Son estimaciones orientativas del trabajo documental futuro, no tareas programadas ni autorización de entrenamiento.

F04 es de alto impacto potencial, pero no existe una tarea de análisis ejecutable mientras no aparezca la fuente. No se envían mensajes externos para obtenerla bajo este encargo. Si aparece legítimamente, primero origen/corte/diferencias y versiones; después se decide si cambia la información. F05 queda aparcada salvo aclaración nueva. No hay nueva automatización ni reapertura de la ventana nocturna.

Hasta entonces el mecanismo sigue plausible/no establecido y el soporte retenido del contraste sigue fallido. No relajar reglas, combinar bandas, eliminar casos o usar la cartera desarrollada para pasar la pantalla emergente. Solo evidencia nueva admisible permitiría revisar la necesidad y una eventual receta estándar congelada con comentario previo; este plan no entrena o puntúa.

B00 y B01–B20 se conservan, con T0/C0 y folds intactos.2024/test/SEL01/actas/ledger permanecen cerrados aquí; solo se consultó documentación e inventario de nombres/tamaños/fechas, sin datos o resultados protegidos. Se mantiene declarada la exposición previa a un asunto ajeno sin usar sus métricas o afirmar ceguera completa. Cero ajustes,cargas de modelos,inferencias,scores,remuestreos o diagnósticos numéricos nuevos. Codex firma revisión propia exploratoria, no aprobación humana o validación profesional independiente.

[Plan estructurado](../../registro/semana2_b20_fuentes2023_plan_v1.json), [índice](../../registro/semana2_b20_fuentes2023_actual.json), [balance concluido](BALANCE_NOCTURNO_20261024.md) y [evidencia anterior](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md). Fuentes, comparación de metadatos y decisiones en Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/fuentes_nuevas2023_20261024_v1.
