## S2-ROBUSTEZ-CLAUDE-20261024: modelos más robustos; entra el GBM regularizado (C2)

Claude (Cowork), sesión de validación nocturna, 24 de octubre de 2026. Registro a las 17:55 UTC. El participante no autorizó la sonda de nivel («no nos fue bien el anterior envío mandando Sondas, prefiero seguir trabajando en modelos más robustos»). Los candidatos y la regla se fijaron antes de entrenar (`Hackaton/Semana 2/Claude/validacion_nocturna_20261023/salidas/robustez__preinscripcion_robustez.json`).

La regla de adopción: el candidato mejora en desarrollo 2023 y en 2024, con el IC 90 % por encima de cero en al menos uno y sin empeorar el cuerpo más de 0,0005. En 2024 la comparación es a igual nivel por ramo. Todos con tres semillas. Resultados:

- C1, tope de 100.000 CU: −0,0015 [−0,0049; +0,0014] y +0,0003. No pasa.
- C2, GBM regularizado (num_leaves 15, min_data_in_leaf 3.000, lambda_l2 50, feature_fraction 0,7): +0,0015 [−0,0002; +0,0032] y +0,0019 [+0,0005; +0,0033], con el cuerpo en +0,0023 y +0,0021. Pasa.
- C3, GLM + GBM: −0,0012 y +0,0011, con el cuerpo de 2023 en −0,0030. No pasa.
- C4, rejilla elegida con la validación interna del desarrollado, frente a C2: −0,0004 y +0,0016. No pasa.

Producción nueva, sin enviar, en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/robustez/`. `A1robregF1b3n_2025.csv` (SHA a702ed24…) es la designada con C2 y el mismo nivel por ramo, 67,17 M CU. `mezcla50_robusta_2025.csv` (SHA 82082f3c59868a4361654bc1bca23796260a8c694135be5c3f499aec19e87f2f) es la mezcla enviada con el componente C2, con los mismos totales (69,00 M CU). A igual nivel gana a la mezcla enviada +0,0007 [−0,0002; +0,0014] en 2023 y +0,0009 [+0,0002; +0,0016] en 2024. Enviarla es decisión del participante.
