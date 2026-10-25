## 39. Semana 2: validación antes del envío de la producción designada (corte 24 de octubre, 15:50 UTC; 10:50 America/Bogota)

Continuación de la sección 37, a petición del participante («continua validando todo antes de enviarlo»). Las cifras están en INFORME sección 10 de `Hackaton/Semana 2/Claude/validacion_nocturna_20261023/`, con 179 de 179 verificadas.

- Revisor independiente rev5: reconstruye `A1fixF1b3n_2025.csv` hasta el sexto decimal y confirma el formato de Kaggle (209.063 filas, orden de la plantilla, `row_id,prediction`, ASCII con saltos LF). No encuentra fuga en la historia y su veredicto es listo, sin bloqueos.
- Reproducibilidad: dos GBM reentrenados dan relatividades idénticas bit a bit.
- Factor de nuevo negocio, descartado fuera de tiempo. El exceso de autos en 2023 (A/E 1,62 frente a 0,94 de la renovación) no se repitió en 2024 (1,09 frente a 1,10). Aplicar el factor de 2023 baja el D² de 2024: −0,0010 bruto, −0,0001 con credibilidad. La producción no cambia.
- Línea ML independiente (sección 38): llega a la misma receta de fondo y a las mismas conclusiones sobre tendencia y nuevo negocio. Las predicciones correlacionan entre 0,969 y 0,985, y sus totales difieren +5,3 %, +7,6 % y −1,1 %. A igual total por ramo, la media 50/50 gana +0,0039 [+0,0004; +0,0074] en desarrollo 2023 y +0,0012 [−0,0005; +0,0029] en 2024. Opción preparada, sin enviar: `A1fixF1b3n_mlind50n_2025.csv`, SHA 0df5009c…c3dcacf7, mismo total que la designada.

Avisos para retomar:

- El participante debe elegir entre la designada y la mezcla.
- Falta confirmar que Kaggle acepta 209.063 filas. El envío lo hace Codex con autorización expresa del participante.
- Foro: CLA-S2-20261024-016. El 015 es de la sesión ML independiente.
