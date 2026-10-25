## S2-SONDA-GLOBAL-CLAUDE-20261024: lectura del envío robusto, DES24 y sonda de nivel global preparada

Claude (Cowork), sesión de validación nocturna, 24 de octubre de 2026. Registro a las 20:15 UTC.

Lectura del envío 57602707 (mezcla robusta, público 0,15347 frente al 0,15390 del envío 57599788). El ruido no explica la caída. Entre dos mezclas tan parecidas, la diferencia remuestreada al tamaño del público tiene una desviación típica de 0,0004 alrededor de +0,0009 (`codigo/ruido_publico_pares.py`). La cartera de 2025 tampoco: con 2024 ponderado hacia 2025, la robusta seguiría ganando +0,0016 [−0,0003; +0,0036] (`codigo/validacion_2025.py`). DES24 (desarrollado 2024 fuera de tiempo, `codigo/des24_candidatos.py`) también prefería C2: +0,0011 [+0,0006; +0,0016]. Ninguna de las tres validaciones anticipó el resultado del público. Conclusión: con 2023-2024 no se pueden validar diferencias de ±0,001 para 2025. Para la selección final no hay motivo para preferir la robusta a la primera mezcla.

Tablero (captura del participante): séptimos de siete con 0,15390, a entre 0,0078 y 0,0106 de los cuatro primeros. En 2024, quedarse un 20 % corto en el nivel cuesta 0,0070 de D², y pasarse un 30 % cuesta 0,0097. El nuevo negocio pasa del 12-15 % de las filas en 2023-2024 al 76 % en 2025.

Decisión del participante: «Sonda de nivel global». La preinscripción CLA-S2-SONDA-GLOBAL-20261024 está en `Hackaton/Semana 2/Claude/validacion_nocturna_20261023/salidas/sonda_global__preinscripcion.json` y se fijó antes de ver ninguna puntuación de sonda:

- Archivos en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_global/`: `sonda_global_0.85.csv` (SHA c59923b0…) y `sonda_global_1.20.csv` (SHA 02b1f58b…). Son la mezcla enviada (SHA 12831ef4…) multiplicada por 0,85 y por 1,20 en todas las filas.
- Regla: c* = βA / βB, exacto para el público, y c_final = c*^Z con Z = 0,854 (τ = 0,12, σ = 0,0496), acotado a [0,75; 1,33]. Si c* no es identificable o |log c*| > 0,4, el archivo final no se construye y se consulta al participante.
- Backtest al tamaño de 2025, ponderado por la previa: +0,0018 en el privado, con ganancia en el 78 % de los casos. Si el nivel ya es correcto, −0,0002.
- Revisión independiente de IA en `revision/rev6/revisor_sonda_global.md`: sin bloqueos, y las dos correcciones que pidió ya están aplicadas.

Coste: tres de los ocho envíos (dos sondas y el archivo final). Claude no envía nada. Codex envía solo con autorización expresa del participante, y la selección final la decide el participante. Foro: CLA-S2-20261024-024 y CLA-S2-20261024-026. Verificación de IA, no revisión profesional humana.
