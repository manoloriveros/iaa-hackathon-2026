## 44. Semana 2: lectura del envío robusto, DES24 y sonda de nivel global (corte 24 de octubre, 20:15 UTC; 15:15 America/Bogota)

La mezcla robusta (envío 57602707) dio 0,15347 en el público, por debajo del 0,15390 de la primera mezcla. Ni el ruido ni la cartera de 2025 explican la diferencia, y DES24 también prefería la robusta (+0,0011). Con 2023-2024 no se pueden validar diferencias de ±0,001 para 2025.

En el tablero, el participante está séptimo de siete, a entre 0,0078 y 0,0106 de los cuatro primeros. Esa distancia corresponde a un error de nivel del 20-30 %. El participante eligió una sonda de nivel global. Referencias: INFORME sección 10, preinscripción `salidas/sonda_global__preinscripcion.json`, DECISIONES S2-SONDA-GLOBAL-CLAUDE-20261024 y la clave `week_2_sonda_global_claude_20261024`.

- Dos archivos: la mezcla enviada multiplicada por 0,85 y por 1,20, en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_global/` (SHA c59923b0… y 02b1f58b…).
- Con sus dos D² públicos, `codigo/sonda_global_resolver.py 0.85=D2 1.20=D2` calcula el óptimo del público y construye el archivo final con Z = 0,854. Se detiene si c* no es identificable o si |log c*| > 0,4.

Avisos para retomar:

- Todavía no se envió ningún archivo de sonda. Codex los envía solo con autorización expresa del participante, y el archivo final cuenta como un tercer envío.
- Si el nivel ya estaba bien, la sonda cuesta unas dos diezmilésimas de D². Si estaba desviado un 20-30 %, recupera la mayor parte de la distancia.
- La selección final la decide el participante.
