## 37. Semana 2: decisiones del participante sobre la validación nocturna, política v2, A1 titular y producción designada (corte 24 de octubre, 15:05 UTC; 10:05 America/Bogota)

El 24 de octubre a las 09:46 de Bogotá, el participante respondió a las cuatro decisiones de la sección 36:

- «Enmiendala»: enmienda de la salvaguarda de cliente nuevo de SEL01.
- «Sin tendencia»: nivel 2025 por balance de 2023–2024.
- «me quedo con tu recomendación»: versión 2 con historia neutral y promedio de tres semillas.
- «me quedo con tu recomendación»: la transferencia del desarrollado entra en la selección común.

Política S2-SELECCION-v2-20261024, en `Repositorio_IAA2026/registro/semana2_politica_seleccion_v2_20261024.json` y en la carpeta de la validación nocturna. Es la enmienda humana explícita que v1 prevé, y v1 y su acta se conservan. Cambia una sola regla: en cliente nuevo basta con una diferencia puntual ≥ 0, y el límite del 95 % se informa como diagnóstico. El motivo es la potencia: según rev2, la regla pasaba el 26 % de las veces con el efecto observado. El acta enmendada se calculó sobre el acta original, sin leer etiquetas. A1 promueve frente a R0 (+0,0486 [+0,0265; +0,0733]) y A2 no promueve frente a A1 (−0,0040). Titular de la semana 2 bajo v2: A1. La enmienda se decidió conociendo el acta, así que no hay confirmación intacta de 2024 para v2.

Producción designada, sin enviar: `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/A1fixF1b3n_2025.csv`, con SHA f786deb3…224c53aa.

- Total 67,17 M CU: autos 41,04 M, edificios 20,59 M y contenidos 5,54 M.
- Receta: A1 con ID01, historia neutral y tres semillas, sin tendencia.
- La historia con tres semillas aporta +0,0020 [+0,0002; +0,0043] en desarrollo 2023 y +0,0025 [+0,0012; +0,0039] en 2024, menos que la semilla 11 sola.
- Las 20 primas comerciales con esta prima de riesgo suman 16.493 CU.
- Sin tendencia, el nivel de hogar puede quedar corto entre un 5 y un 12 % según los backtests. Las versiones con TEN-N2 siguen disponibles.

Avisos para retomar:

- La transferencia es la titular de la selección común. El registro de selección de Codex (`semana2_seleccion_actual.json`) no se tocó, y Codex debe integrar la decisión.
- Enviar a Kaggle sigue siendo tarea de Codex y requiere autorización expresa del participante. Esta decisión no la da.
- DECISIONES.md tiene la entrada S2-SELECCION-v2-20261024 y ESTADO_PROYECTO.json la clave `week_2_politica_seleccion_v2_20261024`. Foro: CLA-S2-20261024-014. Comprobar el último CLA-S2-* antes de publicar.
