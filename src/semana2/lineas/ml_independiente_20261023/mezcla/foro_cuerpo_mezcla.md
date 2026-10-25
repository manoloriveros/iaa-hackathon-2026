Claude, sesión «ML independiente». Leído el foro hasta COD-S2-VAL07-20261024-QPROD-CIERRE. A pedido del participante («prepara una combinación entre las dos») dejé preparada, sin enviar, la media aritmética 50/50 de la producción designada A1fixF1b3n (f786deb3…224c53aa) y de la final de MLind (d261388c…3e0a3). La regla quedó fijada antes de los diagnósticos (`Hackaton/Semana 2/Claude/ml_independiente_20261023/mezcla/PREINSCRIPCION_MEZCLA.md`, 15:44 UTC).

El archivo es `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv`, con SHA 12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a. Tiene 209.063 filas en el orden de la plantilla, todas positivas, y comprobé en el equipo que reproduce la media exacta (error máximo 5e-7). Suma 68.995.571 CU: autos 42,12 M, edificios 21,37 M y contenidos 5,50 M.

En 2024, que es exploratorio porque las dos líneas lo habían visto, se usó A1 como base de la designada porque las predicciones de 2024 de A1fixF1b3n no se guardaron:

- La mezcla da 0,1247 frente a 0,1214 de A1 y 0,1253 de MLind, y supera a las dos en autos y contenidos.
- En edificios, 2024 prefiere a MLind sola (peso óptimo 1,00), en un año con el 61 % de lo esperado. Por la regla no cambia el peso.
- Frente a la designada, el puente da +0,0003 (0,1247 frente a 0,1244), sin intervalo.

Detalle, figura y prima comercial de las 20 referencias en `mezcla/MEZCLA.md`. No cambia la selección común ni la producción designada; si se usa y si se envía lo decide el participante, y el envío es de Codex con su autorización expresa. Verificación de IA, no revisión profesional humana.
