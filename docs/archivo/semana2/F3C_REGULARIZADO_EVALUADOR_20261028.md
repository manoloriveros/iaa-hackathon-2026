# F3c-R: evaluador y continuidad hasta completar

Corte 2026-10-28T21:26:44.987526+00:00, autor Codex. Hay 5/26 ambitos fuente terminados y 130 intentos nativos en el diario, incluidos los interrumpidos. La comparacion predictiva sigue pendiente. F3c actual, R1 y B00 permanecen conservados; cero nuevos envios.

El evaluador paso11controles sinteticos: metrica por sklearn, deltas, remuestreo por grupos contrastado por filas, mascaras, escenarios y rechazos de claves/precios/etiquetas invalidos. Cero ajustes. El primer fixture no contenia periodos largos; la prueba se detuvo por segmento vacio. Se preservaron codigo y traza, se amplio solamente el rango de exposicion artificial y se repitio el tramo afectado sin relajar validaciones.

Los dos contrastes finales, familia20, margen0.0005, pisos-0.001, influencia y50escenarios conservan los criterios preinscritos. Antes de ver nuevas salidas se concreto la estabilidad del aprendizaje completo: cinco omisiones de folds, con sus modelos y troncos ya estimados y lambda elegida solo en2023, deben conservar delta global no negativo y deltaNB>=-0.001 frente al control propio de cada ambito y frente a F3c original. Esos miembros no son alternativas seleccionables. No hay nuevos fits desde el evaluador.

La cadena local ahora corre mediante procesos ocultos separados de las sesiones efimeras de herramientas. Una inspeccion global confirmo que los antiguos propietarios Python ya no estaban activos; un PID habia sido reutilizado por node_repl, que no se toco. Checkpoints, leases antiguos y ambos intentos interrumpidos se conservan. La nueva cola fuente retoma el mismo codigo; destino espera sus26recibos; el evaluador espera el sello y controles destino. Si falla un paso, se detiene y conserva evidencia.

Estados vivos:

- Fuente: privado/semana2/F3c_regularizado_20261028/source_scoped/queue_status.json.
- Destino: privado/semana2/F3c_regularizado_20261028/target_real/status.json.
- Evaluacion: privado/semana2/F3c_regularizado_20261028/assessment/status.json.

Se activo seguimiento en este mismo chat cada15minutos, conforme a la peticion de continuar automaticamente hasta completar. ID f3c-r-completar-entrenamiento-y-validaci-n-privada. Solo comunica cambios materiales/fallos/final; no toca otras automatizaciones. Al completar y comprobar informe/foro, debe concluir ese seguimiento. No admite envios ni nuevas recetas por iniciativa del monitor.

El resultado se escribira en F3C_REGULARIZADO_RESULTADOS_20261028.md y el foro cuando termine. Ese archivo no es un resultado disponible mientras no exista su recibo. La evaluacion2024 es adaptativa, no privada independiente; persisten condicionamiento historico A_M1, normalizacion por lote y soporte futuro escaso en edificios nuevos largos.

Codigo evaluador: commit f23be96. Plan registro/semana2_F3c_regularizado_evaluacion_plan.json. Prueba y enmienda: assessment/synthetic.json y assessment/fixture_admission.json. Registros de recuperacion/lanzamiento: privado/corte_f3cr_20261028_2116. No se ha acreditado superioridad privada.
