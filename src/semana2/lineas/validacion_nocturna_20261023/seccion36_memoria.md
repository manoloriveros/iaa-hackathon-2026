## 36. Validación nocturna de la sección 34: correcciones posteriores, revisor rev4 y regla TEN-N2 (corte 24 de octubre, 13:20 UTC; 08:20 America/Bogota)

Continuación de la sección 34, con la misma carpeta `Hackaton/Semana 2/Claude/validacion_nocturna_20261023/`. La sesión se detuvo por el límite de uso entre las 02:57 y las 12:20 UTC, y los controles horarios de ese tramo no se ejecutaron. El acta de 2024 no cambia (R0 titular). Todo lo de esta sección es posterior a la apertura y es exploratorio. Registro en DECISIONES.md (S2-PUERTA2024-CLAUDE-20261024-ACTUALIZACION) y clave `week_2_nightly_validation_claude_20261024_actualizacion`.

- ID01 faltaba en mi constructor de variables para autos del desarrollado (98.110 filas sin variables de cliente). Corregido, el efecto es −0,0001 en desarrollo 2023 y en 2024. La producción corregida es A1fix (66,89 M CU).
- Tres semillas promediadas (A1fixb3): +0,0017 [+0,0005; +0,0031] en desarrollo, +0,0005 en 2024 sin significación.
- Historia de la póliza (siniestros reportados antes de `period_start` y años observados): +0,0050 en desarrollo y +0,0042 en 2024. El revisor independiente rev4 confirma el efecto en autos (relatividad de un siniestro 1,29 en el desarrollado y 1,32 en el emergente; +0,0039 [+0,0020; +0,0058] de D² de frecuencia en 2024) y encontró un efecto de calendario: calibrada en 2023, cuando nadie tiene historia, sube el total de autos un 3,8 % en 2024 y un 2,6 % en 2025. Con la calibración neutral (total de A1fix por ramo) la ganancia es +0,0040 [+0,0023; +0,0057]: casi toda es de orden. Versión propuesta: A1fixF1n.
- Tendencia, regla TEN-N2. La tendencia se estima con siniestros topados a 250.000 CU, y el exceso es carga estable. En autos 2023 una sola lesión de 11,9 M CU (10 % del coste del año) movía la tendencia de +3,5 % a +4,3 %. Factores 2025 sobre el nivel 2023–2024: 1,055, 1,094 y 1,053, frente a 1,072, 1,097 y 1,054 de A1T. rev4 coincide casi al punto en hogar (índice de edificios 2024 1,205 frente a 1,204; sesgo sin tendencia −7,0 % y −11,8 %) y propone cerca de 1,03 en autos, donde pesa más el IBNR de lesiones de 2024.
- Auditoría COD-S2-IA-20261024T052608Z. Recalculé la puerta con 10.000 réplicas y cuantil 0,025 en cliente nuevo y sin redondeos (`codigo/puerta_sensibilidad.py`). El límite de cliente nuevo de A1 va de −0,0104 a −0,0153 frente a −0,001, y el veredicto no cambia con ninguna variante.

Producciones sin enviar en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/`:

| Archivo | Total | SHA |
| --- | --- | --- |
| A1fixTc_2025.csv (A1fix con TEN-N2, recomendada para el nivel) | 71,34 M CU | b9a7e616… |
| A1fixF1nTc_2025.csv (historia neutral con TEN-N2, si se adopta una versión 2) | 71,34 M | 0c1db1db… |
| A1fixF1n_2025.csv (historia neutral sin tendencia) | 66,89 M | a81ec156… |

A1fixF1T (73,75 M) queda sustituida porque contaba el nivel dos veces. El informe tiene 127 de 127 cifras verificadas, y la tanda n4 (17 archivos) coincide en el equipo con su manifiesto.

Avisos para retomar:

- Decisiones del participante, sin cambios de fondo: la enmienda de la salvaguarda de cliente nuevo de SEL01, el nivel 2025 (A1fix, A1fixTc o una sonda) y la versión 2 con historia neutral y semillas.
- Codex registró a las 12:48 UTC metadatos oficiales nuevos en Kaggle: 24 Parquet con los mismos nombres y tamaños y otra fecha de creación, sin checksum remoto. Si cambiaran los datos, estas cifras habría que rehacerlas desde los originales nuevos. No está comprobado.
- Foro: esta sesión usó 005, 006, 009, 010 y 012. Comprobar siempre el último CLA-S2-* antes de publicar.
