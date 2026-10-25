Claude, línea ML independiente, continuación de CLA-S2-20261024-023 a pedido del participante («continua»). Adenda en `Hackaton/Semana 2/Claude/ml_independiente_20261023/evolucion/EVOLUCION.md`; E25 y E26 se declararon en `experimentos.jsonl` antes de correr (19:42 UTC).

E25 ajusta la severidad Gamma de frecuencia × severidad con una rejilla elegida en el pliegue interno del desarrollado 2021-2023. FSt mejora a FS en DES24 (+0,0006 de media: autos −0,0011, edificios +0,0018, contenidos +0,0012) y por la regla entra en la mezcla, que pasa a llamarse v2.1.

E26 estima los pesos de la mezcla en el desarrollado 2024 (v3). Pierde 0,0013 frente a v2 en 2023 y no entra.

Evaluación anidada con C1, en el orden T2b / v2 / v2.1 / v3:
- 2023: 0,1292 / 0,1286 / 0,1287 / 0,1273.
- 2024: 0,1253 / 0,1281 / 0,1284 / 0,1295.
- 2023-2024 con troncos de producción: 0,1326 / 0,1359 / 0,1354 / 0,1358.

v2.1 empata con v2 (correlación de logaritmos 0,9996).

Archivos sin enviar en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`:
- `prediccion_2025_mlind_v21.csv`: 70.706.999 CU, SHA 481b679b09393b7fdf9f84508a8edc85ca694a8be60bde0aa4e045bef5a30bea.
- `mezcla50_designada_mlind_v21_2025.csv`: 68.937.720 CU, SHA 666b79258cf3521ea5c4c693f1379cdcf904c400994591a8ada9dc9ad82d822f.

Corrección a CLA-S2-20261024-023, a raíz de CLA-S2-20261024-024: el ruido de 0,003 que cité era el de la diferencia MLind − A1 (correlación 0,987) y no vale para dos mezclas casi iguales. Medido en 2024 con submuestras del 33 %, la mezcla 50/50 con v2.1 frente a la enviada (A1 en lugar de la designada) da +0,0013 con desviación típica 0,0007 (`evolucion/ruido_pareado_v2.json`). Coincido con la lectura de 024: el resultado de la mezcla robusta muestra que mejoras locales de este orden pueden no trasladarse a 2025.

Lectura: la estructura de esta línea queda agotada con estos datos; lo abierto es el nivel de 2025. Sin envíos; si se envía, lo hace Codex con autorización expresa del participante. Verificación de IA, no revisión profesional humana.
