# F3c-R: adaptador validado y aprendizaje pendiente

Corte del 2026-10-28T20:26:08.124935+00:00, autor Codex. F3c-R sigue en desarrollo. El F3c actual, R1 y B00 se conservan; este corte no demuestra superioridad privada ni autoriza sustituir el envio.

## Lo comprobado

El adaptador recorre 26 ambitos de base y 16 de receta. Cada rama excluye sus grupos antes de convertir costes o aprender completitud, niveles, C1, F2 y bloque propio. Mantiene la mezcla 50/50 y las transformaciones heredadas. La contraccion terminal tiene diez coeficientes activos y selecciona la penalizacion con los cinco folds guardados de 2023.

La prueba sintetica corregida pasa 17 controles con 49 ajustes. Las etiquetas2024 alteradas y las de cada fold retenido dejan exactamente iguales las entradas, parametros y predicciones pertinentes. Pasan replay con estimadores bloqueados, extremos del bloque propio, devianza por otra biblioteca y optimizacion final por SLSQP. El ejecutor completo pasa sus 8 controles con 34 ajustes sinteticos. La conexion con fuentes reales pasa seis controles de lectura, sin inferir ni ajustar nuevos modelos: 50.094 filas2023 y 59.202 filas2024, hashes de18pares fuente y rechazos de ambito/digest/recuento incorrectos.

Los fuentes artificiales sustituyen arboles y RKM solo en las pruebas sinteticas. La invariancia nativa se apoya en sus controles y recibos separados; estas pruebas destino no son un nuevo reentrenamiento adverso de la fuente.

## Fallos preservados y recuperacion

La primera prueba del adaptador fallo en cuatro controles agrupados. Costes permitidos numericamente identicos se sumaban de manera distinta al quedar columnas object por la alteracion de etiquetas retenidas, con diferencias de hasta5,46e-12. El extremo heredado diferia hasta5,69e-14 por orden de multiplicacion. Se normalizo float64 despues de seleccionar filas y se restauro el orden heredado. Se conservaron codigo y49ajustes fallidos; la repeticion corregida conserva las tolerancias originales.

El primer lector real esperaba texto en scope cuando el recibo contiene un objeto con nombre y folds. Se corrigio antes de cualquier ajuste real destino. Digest, hashes y exclusiones no se relajaron.

La ejecucion se interrumpio alrededor de19:45UTC. Las sesiones anteriores ya no estaban disponibles y los registros dejaron de avanzar. Las consultas de PID no los mostraron, aunque ese metodo no es concluyente bajo el aislamiento de Windows. Se archivaron leases y parciales; la causa de la interrupcion no esta establecida. La recuperacion se comprueba por sesiones vivas y nuevos eventos de avance, no por consultas de PID aisladas. La cola fuente retomo el checkpoint con el mismo codigo. La prueba del ejecutor recupero sus16calibradores primarios sin volver a ajustarlos y completo18verificaciones. El contador de constantes analiticas de esa prueba es parcial desde la reanudacion; no se inventa un total anterior.

## Comparacion y ejecucion vigentes

La contraccion se comparara con trainlevel_full construido sobre el mismo flujo anidado. public_full temporal del F3c original permanece como referencia practica. El trainlevel_full historico se conserva, pero no aisla contraccion al tener otros ancestros. Se registraron dos contrastes, familia20 y los umbrales previos antes de cualquier resultado nuevo.

Al corte hay 4/26 ambitos fuente completos, 77 pares con recibo y 101 intentos nativos nuevos en el diario, incluido el intento full interrumpido. Intento no significa ajuste completado. Las26preparaciones de curvas terminaron:52bundles RKM primarios y52adversos separados. No se repitieron esas preparaciones.

La cola fuente corre en PID18128, ambito exclude_3; su sesion local es23196. La continuacion destino corre en PID28568, sesion16482, esperando fuentes. Solo comienza tras26ambitos completos, hashes y controles admitidos. Presupuesto destino:16calibradores primarios y18de verificacion; no nuevos arboles ni RKM desde ese ejecutor. Se detiene ante error y conserva parciales. Termina con parametros, predicciones2024 y controles sellados, antes de comparar scores2024 o producir2025.

## Lo que falta para elegir un modelo

- Terminar los ambitos fuente restantes y el calibrador real de2023 con sus controles.
- Comparar temporalmente con los dos controles preinscritos, por ramo, negocio nuevo/renovacion, fold y duracion; medir influencia de grupos y cola.
- Aplicar los escenarios de reportes tardios, reservas y completitud, y los intervalos por grupos. El umbral global, los pisos de segmento y la estabilidad deben cumplir conjuntamente.
- Solo con evidencia suficiente, preparar y reproducir un candidato2025 y decidir si merece un cupo. No se genera ni envia un nuevo CSV en esta etapa.

2024 es desarrollo adaptativo; los intervalos seran condicionales, no validacion privada independiente. Permanecen la normalizacion por lote, el condicionamiento historico A_M1 y la escasez de soporte de edificios nuevos de larga duracion. La contraccion no resuelve automaticamente esas limitaciones.

## Trazabilidad

Codigo: commit cbe60ad. Planes en registro/semana2_F3c_regularizado_destino_plan.json y registro/semana2_F3c_regularizado_ejecucion_plan.json, con enmiendas y fallos conservados en privado/semana2/F3c_regularizado_20261028/target_adapter y target_real. Resultados: target_adapter/corrected_numeric_types/synthetic.json, target_real/read_admission.json y target_real/orchestration_smoke/controls.json. Estados vivos: source_scoped/queue_status.json y target_real/status.json. No hay nuevos scores predictivos, precios2025 ni envios.
