# G4: capital real de 2023 y preparación de un modelo propio

Codex, 2026-10-25T00:56:31.560339+00:00. Preinscripción COD-S2-20261024-067; resultado COD-S2-20261024-068. Se generaron quince artefactos de parámetros de capital y quince vistas de entrada de edificios con datos reales de 2023. La conexión base a G4 pasó los controles por ámbito. No se ajustaron modelos ni se llamó a C0; no hubo inferencias, scores o CSV nuevos. El participante pide continuar con un modelo propio para el envío.

Son 12.580 periodos únicos de edificios. Las vistas contienen 125.800 copias de periodos porque cada uno aparece en cuatro ajustes exteriores y seis pares interiores. Cada ámbito abre únicamente los archivos permitidos; la producción y referencia independiente solo leen metadatos, capital y prima. La conexión abre objetivos/notificaciones de los folds permitidos, conserva T0/exposición y no usa valores protegidos. Los reportes heredados hasta valoración2024 corresponden a ocurrencias2023, sin abrir la cohorte2024.

| Ámbito | Periodos permitidos | Capitales normales de referencia | Log capital ausente |
| --- | ---: | ---: | ---: |
| exclude_0 | 10070 | 10047 | 0 |
| exclude_1 | 10070 | 10050 | 0 |
| exclude_2 | 10061 | 10043 | 0 |
| exclude_3 | 9993 | 9970 | 0 |
| exclude_4 | 10126 | 10106 | 0 |
| exclude_0_1 | 7560 | 7543 | 0 |
| exclude_0_2 | 7551 | 7536 | 0 |
| exclude_0_3 | 7483 | 7463 | 0 |
| exclude_0_4 | 7616 | 7599 | 0 |
| exclude_1_2 | 7551 | 7539 | 0 |
| exclude_1_3 | 7483 | 7466 | 0 |
| exclude_1_4 | 7616 | 7602 | 0 |
| exclude_2_3 | 7474 | 7459 | 0 |
| exclude_2_4 | 7607 | 7595 | 0 |
| exclude_3_4 | 7539 | 7522 | 0 |

La población normal de los ámbitos tiene entre 7459 y 10106 filas. Los recibos de población se reprodujeron contra el capital permitido. La referencia independiente calculó límites con Decimal y capital corregido/log con Decimal y `math.log`: error absoluto máximo de límites 0.0 y de log 0.0, con criterio1e-12 y las mismas decisiones de ausencia. Seleccionar capitales normales para referencias no elimina periodos o siniestros del modelo. La prima sigue fuera de los predictores.

Los parámetros, poblaciones/recibos, vistas por ámbito y comprobaciones independientes están enlazados desde `Hackaton/Repositorio_IAA2026/privado/semana2/capital_real_g4_2023/produccion_20261024_v1/real_capital_connection_registry.json`. Cada vista tiene `base_features_ready=true`, `C0_present=false`, `fit_allowed=false` y `model_input_ready=false`. El punto reutilizable es `Hackaton/Repositorio_IAA2026/privado/semana2/capital_real_g4_2023/produccion_20261024_v1/prepared_current.json`. La suite sintética anterior no se repitió; sus fuentes congeladas se conservaron. Fit/predict de modelos/preprocesadores,C0 fit/apply,cargas de modelos y red estuvieron bloqueados durante la producción real, sin llamadas prohibidas.

## Preparación del modelo para el envío

La configuración `Hackaton/Repositorio_IAA2026/registro/semana2_g4_modelo_envio_preparacion_v1.json` conserva la receta GLM estándar de efectos principales ya especificada en B20: Tweedie1,5, enlace log, alpha1, mediana y escala numéricas aprendidas solo del ajuste y codificación categórica del ajuste. Copia la definición por los tres ramos y su objetivo original; no añade clima, credibilidad, tendencia o calibración de nivel/pendiente. B00 permanece como referencia y los resultados adversos previos se conservan. Esta preparación no promueve B20 ni reabre su ensayo de calibración.

Se inventariaron quince objetos guardados por fold de la receta B20 y sus SHA coinciden con el manifiesto de origen. No se deserializaron, predijeron o puntuaron; esa comprobación solo identifica activos reutilizables. No se repite la tanda histórica sobre las mismas fuentes ni se crea otro identificador experimental por cambiar el empaquetado.

Faltan contratos y objetos concretos antes de producir un CSV propio. El flujo actual soporta exclusiones de uno o dos folds; debe declararse un ámbito de despliegue de todo2023, sin disfrazar un objeto exterior como si fuera de toda la cohorte. Hace falta C0 congelado del ámbito correcto y la aplicación a2025, más los objetos finales de preprocesado/GLM de los ramos que se usen. El paquete actual no registra esos objetos finales ni la conexión de motor/contenidos y2025. La restricción de esta continuación sigue siendo no ajustar modelos ni recalcular C0. La lista exacta está en `Hackaton/Repositorio_IAA2026/privado/semana2/capital_real_g4_2023/produccion_20261024_v1/model_readiness.json`; es una revisión de configuración y activos, no una nueva validación numérica del modelo.

La entrega se preparará con el modelo propio cuando estén resueltas esas dependencias. No se copió el CSV existente de otra receta, no se generó un CSV de ceros o valores auxiliares y no se envió nada a Kaggle. Los metadatos públicos de Kaggle se consultaron para el contrato de entrega; siguen las inconsistencias documentales de la página de reglas etiquetada parte1. No se usaron scores públicos para elegir receta o parámetros, ni se abrieron resultados de2024.

G4 avanza a parámetros/conexión base reales verificados. Su flujo predictivo completo continúa abierto; G1/G2, mecanismo/soporte y límites de último/disponibilidad temporal no se resuelven con estos cálculos. Ningún artefacto de capital equivale a un precio o modelo listo para producción.

Decisiones G4R-01 a G4R-06. B00/alternativas,T0/exposición/C0/folds/catálogo/contadores de modelos conservados;2024/test de modelado/ledger/actas/SEL01 cerrados en este trabajo. Cero modelos, C0, predicciones, scores o envíos nuevos. Sin promoción,lista final,publicación,remoto,otros chats,delegación o automatizaciones. Ventana nocturna cerrada. Autor Codex,verificación propia exploratoria en Windows,no revisión profesional independiente ni aprobación humana. Procedencia y límites conforme a IAA Documentación§2 y Gobernanza§2.8.
