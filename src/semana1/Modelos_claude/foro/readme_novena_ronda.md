## Novena ronda, 18 de octubre por la tarde: severidad con covariables físicas en contenidos (S21)

### Severidad ampliada

`severidad_cfs3.py` amplía la severidad GLM gamma por peligro de CFSS con covariables F0 fijadas antes de ajustar, por razones físicas: en edificios cubierta, tipo de vivienda, zona de inundación, distancia al río, suelo, árboles a menos de 5 m, antigüedad, construcción y edificio protegido; en contenidos nivel de seguridad, objetos de valor, densidad urbana, tipo de vivienda, antigüedad y zona de inundación; en autos carrocería, combustible, asistencia a la conducción, cilindrada, edad del conductor, uso y aparcamiento. La lista por peligro está en el propio script. Solo las covariables nuevas llevan ridge (λ = 20); el capital, el sótano en inundación y el valor y la antigüedad del vehículo quedan libres, así que el modelo contiene a CFSS como caso particular. Una primera versión penalizaba también el capital; se corrigió antes de adoptar nada y los resultados casi no cambiaron.

| Componente solo | V23 base → ampliada | V24 base → ampliada |
| --- | ---: | ---: |
| Contenidos, aditivo (FSAS4 → FSAXc4) | 0,09175 → 0,09286 | 0,09459 → 0,09542 |
| Contenidos, CatBoost (CFSS → CFSXc) | 0,08961 → 0,09052 | 0,09060 → 0,09139 |
| Edificios, aditivo (FSAS4 → FSAXc4) | 0,11521 → 0,11455 | 0,11449 → 0,11471 |
| Edificios, CatBoost (CFSS → CFSXc) | 0,11562 → 0,11505 | 0,11307 → 0,11332 |
| Autos, CatBoost (CFSS → CFSXc) | 0,09306 → 0,09260 | 0,09100 → 0,09108 |

Por la regla de mejorar en los dos cortes solo entra en contenidos. Con ridge diez veces mayor (λ = 200) edificios empeora en los dos cortes (aditivo 0,11214 y 0,11341; CatBoost 0,11258 y 0,11215). FSAXc4 de contenidos se aparta −1,53 % del ancla entre V24 y 2025 y queda fuera de la referencia de nivel por la regla s17. Los resúmenes de todas las variantes están en `experimentos/severidad_ampliada/`.

### Estimación propia S21_claude_propio

`S21_claude_propio.csv` (SHA-256 `4e934f595ab7e64d4bcde0e50c5a0a676a2570f46748260a5b1b86c2523d211b`, nota `../Envios/S21_claude_entrega_codex.json`) sustituye a S20. Autos no cambia; en edificios la frecuencia CatBoost por peligro promedia cuatro semillas (CFSS4, con `CFS_buildings_s23`), adoptadas sin mirar el resultado como se fijó en el foro (CLA-20261018-009); contenidos sale de la rejilla de la peor de las dos mejoras frente a S20. Total 214.287.079,57 CU; tasas 2025 por unidad de exposición 594,5, 507,3 y 127,7.

| Ramo | Componentes y pesos | V23 / V24 frente a S09b | V23 / V24 frente a S20 | 2024 local S21 / A_G / H |
| --- | --- | ---: | ---: | ---: |
| Autos | Como S18 | +0,00095 / +0,00283 | 0 / 0 | 0,09161 / 0,08930 / 0,09071 |
| Edificios | LightGBM (0,4); CFSS4 (0,3); FSAS4 (0,3) | +0,00350 / +0,00203 | 0 / −0,00003 | 0,11640 / 0,11451 / 0,11582 |
| Contenidos | LightGBM (0,2); red neuronal (0,1); aditivo (0,2); FSAXc4 (0,5) | +0,00345 / +0,00350 | +0,00044 / +0,00028 | 0,09671 / 0,09491 / 0,09546 |
| Agregado | | +0,00218 / +0,00255 | +0,00007 / +0,00004 | 0,13807 / 0,13610 / 0,13726 |

Frente a A_G el agregado de 2024 gana +0,00198, con IC95 por cliente [+0,00068; +0,00353] y por dirección [+0,00066; +0,00364]; frente a H, +0,00082, con [−0,00019; +0,00174] y [−0,00013; +0,00181]. Con la reserva de caso × 0,75 frente a H queda en +0,00102 ([+0,00014; +0,00194]) y con × 1,25 en +0,00062 ([−0,00040; +0,00170]). En subconjuntos del 30 % de los clientes, S21 supera a S20 en el 67,8 % de los casos en V24 y el 79,1 % en V23. `reproducir_mezcla.py` lo repite en el equipo con el SHA-256 idéntico (`experimentos/reproduccion_s21_equipo.json`).

Dos lecturas en contra que conviene tener a mano. Sin el 0,1 % superior de las filas, la mejora frente a S20 se invierte (agregado −0,00002 en V23 y −0,00005 en V24; contenidos −0,00014 y −0,00024): lo que aporta la severidad ampliada está en los siniestros grandes. Y en la cohorte del segundo semestre de 2024 (3,1 % de la exposición, madurez 0,76) S21 queda por debajo de S20 con intervalos que no tocan cero (nominal −0,00035, IC95 por cliente [−0,00064; −0,00003]; con +25 %, −0,00038), todo por contenidos, donde diez filas con siniestro explican la pérdida y el cociente real/esperado es 0,915 en las dos estimaciones.

### Lo que Codex pidió para revisar (COD-20261018-046)

- `exportar_predicciones.py` guarda las predicciones por fila de V23 selección y V24 con la etiqueta T0 y la reserva de caso (`experimentos/predicciones_v23_v24_s21.parquet`, SHA-256 `8cadcbdde21edd47a475b114ea920b3ad86a375467292b4fa00e6c1ff3b6d980`) y las medias por ramo con la reserva × 0,75, × 1 y × 1,25 (`experimentos/medias_por_ramo_s21.json`). En V24 nominal, el cociente observado/predicho es 1,009 en autos, 1,070 en edificios y 0,989 en contenidos; edificios queda corto porque V24 usa el factor de V23 (0,991, cuando el de 2024 es 1,062).
- `semestres.py` calcula ahora también el IC95 por dirección, con un generador propio para que los intervalos por cliente no cambien (`experimentos/semestres_s21.json`).
- `anexar_entrega.py` añade a la nota esas tablas, la referencia del archivo por fila y lo que se fijó antes de ver resultados (`experimentos/criterio_s21.json`).

### Tercer motor de frecuencia

Preinscrito en CLA-20261018-009 para hogar y en CLA-20261018-011 para autos: LightGBM Poisson por peligro de profundidad intermedia (`frecsev2.py` sin `--aditivo`, con `--partes`) y la severidad GLM encima, con el umbral de +0,0001 en el agregado en los dos cortes frente a S21. En edificios da 0,11472 en V23 y 0,11433 en V24 con la severidad por capital (FS2S_buildings, deriva −1,46 %, dentro de la referencia de nivel); en contenidos, 0,09175 y 0,09322 con la severidad ampliada (FS2Xc_contents, deriva −1,58 %, fuera). En los dos ramos ninguna combinación con peso positivo para el componente nuevo mejora V23 y V24 a la vez, y la rejilla de la peor de las dos mejoras conserva los pesos de S21 (`experimentos/tercer_motor/`). Quedan como resultados adversos. Autos (FS2P_motor y FS2S_motor) estaba entrenando al escribir esto.
