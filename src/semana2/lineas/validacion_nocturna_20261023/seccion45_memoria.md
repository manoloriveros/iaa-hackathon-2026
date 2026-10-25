## 45. Semana 2: sonda de nivel por ramo × nuevo negocio, preparada (corte 25 de octubre, 01:35 UTC; 24 de octubre, 20:35 America/Bogota)

La sonda global (sección 44) pidió un nivel un 22 % más alto, pero solo mide un factor común. El participante eligió «Final + diseñar sonda por segmento». Detalle en INFORME sección 10, `codigo/sonda_segmento_*.py` y `salidas/sonda_segmento__*.json`; DECISIONES S2-SONDA-SEGMENTO-CLAUDE-20261025; clave `week_2_sonda_segmento_claude_20261025`.

- Seis celdas, ramo × nuevo negocio. Cinco sondas: F (`final_sonda_global_2025.csv`) con una celda ×1,2. El nuevo negocio de autos se deduce.
- Archivos en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_segmento/`.
- Simulación en el privado frente a F: −0,0005 si no hay desviación por celda, más de +0,011 con las desviaciones de 2023 o 2024 y unos +0,0024 con la previa.
- Revisión independiente sin bloqueos; sus correcciones están aplicadas.

Avisos para retomar:

- Orden: primero F. Solo si su D² público es 0,15947 o 0,15948 se envían las cinco sondas. Las puntuaciones se pasan al resolutor por nombre de archivo o SHA (`--recibos`).
- `codigo/sonda_segmento_resolver.py` construye el archivo por celda o se detiene: si F no encaja, si algún a_s ≤ 0 o si una celda se aparta más de max(0,7; 3σ).
- Envíos (siete en total) y selección final los decide el participante; los envíos los hace Codex.
