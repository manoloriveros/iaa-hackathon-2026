## 41. Semana 2: modelos más robustos tras el primer envío (corte 24 de octubre, 17:55 UTC; 12:55 America/Bogota)

La mezcla enviada (envío 57599788) dio un D² público de 0,15390, puesto 5 de 7. El participante no quiso sondas de nivel («no nos fue bien el anterior envío mandando Sondas, prefiero seguir trabajando en modelos más robustos»). La sonda quedó preparada y sin usar.

Robustez, con candidatos y regla fijados antes de entrenar (INFORME sección 10, `salidas/robustez/`):

- C1, tope de siniestros a 100.000 CU: no pasa.
- C2, GBM regularizado (15 hojas, 3.000 filas por hoja, λ 50, fracción de variables 0,7): pasa, con +0,0015 en desarrollo 2023 y +0,0019 [+0,0005; +0,0033] en 2024 a igual nivel.
- C3, GLM + GBM: no pasa.
- C4, rejilla elegida con la validación interna: no pasa.

Con C2 queda `mezcla50_robusta_2025.csv` (SHA 82082f3c…), sin enviar. Es la mezcla enviada con el componente regularizado, con los mismos totales. Gana a la enviada +0,0007 en 2023 y +0,0009 [+0,0002; +0,0016] en 2024. Registro en DECISIONES (S2-ROBUSTEZ-CLAUDE-20261024) y en la clave `week_2_robustez_claude_20261024`.

Avisos para retomar:

- La mejora es de orden y pequeña. El nivel por ramo sigue siendo la incertidumbre que más pesa.
- Enviar la mezcla robusta lo decide el participante. El envío lo hace Codex.
