# Revisión del panel para cerrar la parte 1

Guía de Codex para la revisión del participante, 19 de octubre de 2026. Es una propuesta de recorrido; no registra aprobación humana ni cierra hallazgos. Las reglas se reconfirmaron mediante Kaggle MCP: cierre 23 de octubre, 11:00 Bogotá. Informe, video y repositorio finales corresponden al fin de la parte 2.

| Sección del panel | Qué comprobar | Evidencia existente y cierre pendiente |
| --- | --- | --- |
| Estado de entrega | Identidad del candidato, archivo y envío; coste del periodo y tres ramos | S30 ref. 57371361, S22 ref. 57370117; dos CSV de 626.639 filas con esquema, IDs, orden, cobertura, finitud y SHA cotejados. Falta decidir candidato y confirmar selección final. S30 es recomendación provisional. |
| Datos y variables | Unidad, fecha de captura, faltantes y significado de variables materiales | Once originales íntegros, 107 definiciones y perfiles D30/D61. Los perfiles son anteriores a la limpieza. Revisar exposición, capital, franquicias, reservas, fechas, historial, prima y telemática. Separar disponibilidad en el dataset de disponibilidad al cotizar. |
| Limpieza y objetivo | Justificación y alcance de cada regla; enlace temporal y una asignación por siniestro | Ocho reglas N62, conciliación D67 y contrato F0 D68. Base con 1.454 capitales pendientes; F0 trata esos casos, 149 sin confirmación histórica. AGE01 cambia convención. Las marcas audit_* no son predictores. Falta decisión humana sobre estos criterios y su incertidumbre. |
| Modelo actual | Razón de cada componente, pesos por ramo, exposición, desarrollo y nivel 2025 | S30 combina diez componentes; receta y 44 fuentes de modelo identificadas por SHA. Desarrollo de reporte una vez. Reservas de caso sin IBNER adicional: supuesto, no suficiencia demostrada. Revisar disponibilidad temporal y sensibilidad del nivel, especialmente edificios. |
| Resultados y ensayos | D² completo, estabilidad por ramo, calibración e intervalos | Público S30 0,12996 frente a S22 0,12988; ganancia local agregada 0,000138041 con IC95 condicional que incluye cero. V23/V24 y público participaron en selección. 199 archivos indexados incluyen planes; no son 199 experimentos aprobados. Falta aceptar y registrar el criterio de elección. |
| Validación y riesgos | Alcance real de cada control, fuente y fecha; qué falta para cerrar | Batería final 45/45; expediente 57 controles archivados. Replay Windows reproduce los CSV exactos y conserva diferencias mínimas Parquet con código 3. Falta reproducción completa desde originales y revisión por otra persona si se pretende afirmar independencia. GOV-007 tiene reparación técnica posterior al registro importado; no confundir estado histórico con estado técnico actual. |
| Requisitos y fechas | Separar obligación oficial de hitos internos | Viernes: predicción final de parte 1. Propuesta interna: congelar receta/CSV y decidir el jueves. Video, informe y repositorio completos al final de parte 2. Revisar elegibilidad documental para premio, licencias/costes y formulario cuando se publique. |
| Tu revisión | Identidad, fecha, archivo/hash y decisión específica | Notas del navegador exportables; el acta sigue pendiente. Registrar aceptar para el concurso, corregir o mantener abierto, con motivos y alcance. La revisión del participante no acredita por sí sola validación profesional independiente. |
| Fuentes y reproducción | Que la evidencia corresponda al código y al CSV elegidos | Git privado y fuentes por SHA. Recoger la corrida integral pendiente; si no existe, completar la verificación pertinente sin atribuirla anticipadamente. Mantener secretos, datos y predicciones por fila fuera de Git. |

## Decisiones prioritarias antes del viernes

1. Confirmar el uso previsto: concurso con datos suministrados o cotización prospectiva. Para la segunda afirmación deben acreditarse los cortes de acceso de predictores; hoy permanecen hallazgos materiales abiertos.
2. Documentar el objetivo observado, el ajuste de reporte aplicado una vez y la incertidumbre de reservas/último no observado. Una sola valoración no permite demostrar suficiencia de reservas.
3. Revisar los 149 capitales sin confirmación y la sensibilidad pertinente antes de aceptar su tratamiento. La aceptación del supuesto no confirma su unidad real.
4. Evaluar S30 frente a S22 con la evidencia completa. Conservar la selección reutilizada y los intervalos; no justificar una superioridad concluyente por una diferencia pública pequeña.
5. Recoger evidencia de reproducción integral, registrar la revisión del candidato exacto y congelar receta, CSV y commit. La mezcla reproducida desde componentes es un alcance distinto del entrenamiento completo.
6. Antes de las 11:00 del viernes, confirmar en Kaggle el envío final y conservar recibo/captura. Las reglas toman el mejor público si no hay selección manual; elegir explícitamente hace la decisión trazable.

Algunas incertidumbres solo se resolverán con nueva información o revisión especializada. Para el concurso pueden conservarse como limitaciones aceptadas con alcance y evidencia; no deben marcarse como hechos resueltos. Un pendiente de revisión profesional no es automáticamente una prohibición de entregar el CSV.

## Corrección de presentación durante esta revisión

El recolector leía únicamente algunos nombres de campos en inglés. Quince criterios de cierre existentes en las fuentes quedaban vacíos. Se corrigió la lectura de nombres en español e inglés: los veinte hallazgos muestran su criterio literal y el origen del campo. Se preservaron todos los estados y la aprobación humana pendiente. Evidencia: registro/verificacion_hallazgos.json. No se repitieron entrenamientos ni se cerró un hallazgo por esta corrección.
