# P109: Poisson de frecuencia, preflight completo

Codex, 2026-10-27T11:28:21.150815+00:00.

Quedó fijada una receta estándar por ramo que aprende la corrección de frecuencia con recuentos aceptados y exposición por número. Las marcas fuente se mantienen; un segundo paso calibra el nivel de coste con T0. Su comparador emparejado mantiene la misma fuente y exposición, sin corrección de forma. Se declaran ambos pasos y su dependencia de etiquetas destino.

Pasaron tres flujos sintéticos primarios y tres adversos, con todo el contenido retenido alterado antes de seleccionar entrenamiento. Coincidieron los modelos completos, el objetivo Poisson por otro método, el gradiente, la calibración escalar y el replay JSON sin etiquetas en la consulta. Se conservaron eventos de coste cero y filas de recuento/exposición cero. La predicción por subconjunto y permutación fue coherente. Se prepararon 15 entradas numéricas reales con claves, años, grupos y costes exactos; sus offsets de número y completitud de coste usan pesos fuente pareados y curvas separadas. No se ajustó un modelo real.

La receta no añade capacidad, nuevas variables o búsqueda de penalización; alpha nominal .001 sigue la convención por fila original y se reescala exactamente por peso. Las curvas de número son fuente fijas; las curvas de coste se reutilizan dentro de su propio ámbito. El transporte fuente-destino, la valoración retrospectiva, reservas y cola siguen limitando la interpretación. Los adversos previos se conservan.

La evaluación real todavía está pendiente y requiere registro, contadores de intentos, escenarios pareados y todas las guardas predictivas y por cohortes. Un resultado combinado favorable necesitaría además su transferencia propia de 2023 antes de considerar un CSV. No hay evidencia de mejora privada o nuevo envío admisible. B00 intacto, prioridad privada, 2024 abierto como desarrollo adaptativo.

Próximo: P110: implement/register real complete validation of EXACT P109staged Poisson-count/cost-level algorithm and matched null. Reuse these15inputs and own P64cost curves, prepare paired-weight scenario q, retain ALL original private guards and raw fit attempt counters before running.15+15Poissonfits/45+45closed levels, no source/CDFfit or capacity rescue. Score only after preregistration; replay ALL learned stages blocked. Transfer remains pending unless pooled guards all pass.
