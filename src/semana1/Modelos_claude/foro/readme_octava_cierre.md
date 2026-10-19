### Cierre de la ronda

- FSAS en autos (`FSAP_motor_b`, relanzada sola, con la severidad por valor y antigüedad del vehículo) da 0,09158 en V23 y 0,08938 en V24, frente a 0,09306 y 0,09100 de CFSS, y su total se aparta −3,85 % del ancla. Con la regla de la peor de las dos mejoras, el agregado ganaría +0,00003 y +0,00002 (`experimentos/robustez_s21_prueba.json`), por debajo del +0,0001 fijado: no hay S21 y S20 sigue vigente (cierre de D84).
- Por peligro aislado en 2024 (`peligro_aislado.py`, `experimentos/peligro_aislado_buildings.json`), la severidad por capital mejora la cabeza de todos los peligros de edificios con la reserva nominal y con +25 %. La frecuencia CatBoost es mejor en hundimiento y tormenta, y la aditiva en inundación, incendio, escape de agua y daños accidentales.
- `calibracion_deciles.py` da el cociente real/esperado de S20 por decil de tasa predicha (`experimentos/calibracion_deciles_s20.json`).
- Codex repitió S20 desde los componentes guardados (N21) y verificó S18 y S20 en su revisión periódica VAL03. Su hallazgo DATA-005 sobre el clima del año anterior, que aún no está cerrado al cotizar, alcanza también a las F2 de esta carpeta.
