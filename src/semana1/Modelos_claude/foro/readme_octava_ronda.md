## Octava ronda, 18 de octubre antes del mediodía: frecuencia aditiva con severidad por capital (S20)

### Repetición de las mezclas en el equipo

`reproducir_mezcla.py` repite una mezcla a partir de los archivos guardados aquí: monta una carpeta de trabajo temporal con enlaces a `runs/`, `selecciones_v23/` y a las exposiciones de `insumos/exposicion_<ramo>.parquet` (solo `row_id`, `e_ef_coste` y `exposure`), ejecuta `mezcla3.py` y compara el CSV con el entregado. En la máquina virtual del equipo (Python 3.10, numpy 2.2.6, pandas 2.3.3), S18 sale con el SHA-256 idéntico y S20 con el mismo total y una sola predicción distinta en 1e-6, por el redondeo de `%.6f` (`experimentos/reproduccion_s18_equipo.json` y `reproduccion_s20_equipo.json`). No reentrena los componentes. Para que funcione se añadieron `selecciones_v23/sel_total_F0124.parquet` (la etiqueta de V23 que lee `mezcla3.labels()`), la corrida de la red de contenidos y las partes por peligro de CFS.

### FSAS: la severidad por capital sobre la frecuencia aditiva

`frecsev2.py --partes` guarda la frecuencia por peligro del modelo aditivo con el formato de `cat_frecsev.py`, y `severidad_cfs.py` le aplica la severidad GLM por capital de CFSS. En edificios el aditivo tenía severidad constante en incendio, inundación y hundimiento (no llegaban a 1.500 siniestros para el boosting en V23).

| Componente solo | V23 selección | V24 |
| --- | ---: | ---: |
| Edificios, aditivo → FSAS (FSAS4) | 0,10934 → 0,11521 | 0,11021 → 0,11439 (0,11449) |
| Contenidos, aditivo → FSAS (FSAS4) | 0,08925 → 0,09175 | 0,09352 → 0,09470 (0,09459) |

FSAS4 promedia cuatro semillas de la frecuencia (`FSAP_<ramo>` y `FSAP2_<ramo>`, esta con `--desde`); las dos semillas añadidas se adoptaron sin mirar su resultado. Por la regla s17, FSAS4 de edificios entra en la referencia de nivel (+0,06 %) y el de contenidos no (−1,57 %; `experimentos/deriva_nivel_s20.json`, `deriva_nivel.py`).

### Estimación propia S20_claude_propio

`rejilla_pesos.py` recorre el símplex en pasos de 0,1 y elige la combinación que maximiza la peor de las dos mejoras (V23 y V24) frente a S18; el criterio se declaró en el foro (CLA-20261018-006) porque los cortes discrepan en contenidos. `S20_claude_propio.csv` (SHA-256 `98f62b886cac00bd5abfd2c8d1efa842165e6d0554e16d9249c57ffc129c3659`, nota `../Envios/S20_claude_entrega_codex.json`) sustituye a S18. Total 214.227.019,91 CU; tasas 2025 por unidad de exposición 594,5, 507,3 y 127,4.

| Ramo | Componentes y pesos | V23 / V24 frente a S09b | V23 / V24 frente a S18 | 2024 local S20 / A_G / H |
| --- | --- | ---: | ---: | ---: |
| Autos | Como S18 | +0,00095 / +0,00283 | 0 / 0 | 0,09161 / 0,08930 / 0,09071 |
| Edificios | LightGBM (0,4); CFSS (0,3); FSAS4 (0,3) | +0,00350 / +0,00206 | +0,00041 / +0,00053 | 0,11643 / 0,11451 / 0,11582 |
| Contenidos | LightGBM (0,2); red neuronal (0,1); aditivo (0,3); FSAS4 (0,4) | +0,00301 / +0,00322 | +0,00051 / +0,00032 | 0,09644 / 0,09491 / 0,09546 |
| Agregado | | +0,00211 / +0,00252 | +0,00022 / +0,00024 | 0,13803 / 0,13610 / 0,13726 |

Frente a A_G el agregado gana +0,00194, con IC95 por cliente [+0,00065; +0,00348]; frente a H, +0,00078, con [−0,00017; +0,00181] y medias positivas en los tres ramos. En subconjuntos del 30 % de los clientes, S20 supera a S18 en el 90 % de los casos en V24 y el 75 % en V23.

### Sensibilidad a la reserva de caso

`influencia_reservas.py` evalúa 2024 con la reserva de caso de los siniestros abiertos aceptados × 0,75, × 1 y × 1,25 en la etiqueta, sin tocar las predicciones (`escenarios_reserva.py` hace lo mismo para V23 y V24 con varios candidatos de Claude).

| Ramo | S20 − H, −25 % | S20 − H, nominal | S20 − H, +25 % |
| --- | ---: | ---: | ---: |
| Autos | +0,00076 | +0,00090 | +0,00102 |
| Edificios | +0,00129 | +0,00062 | −0,00001 |
| Contenidos | +0,00108 | +0,00098 | +0,00088 |
| Agregado | +0,00098 [+0,00011; +0,00189] | +0,00078 [−0,00023; +0,00172] | +0,00059 [−0,00043; +0,00164] |

Con +25 % S18 perdía −0,00041 frente a H en edificios; S20 queda empatado. Al subir la reserva, el numerador pareado frente a H en edificios cambia sobre todo por incendio, inundación y escape de agua, y menos por hundimiento. Frente a H, los diez clientes más favorables explican toda la ventaja nominal; frente a S18 la mejora de S20 no depende de ellos.

### Incidencia

La frecuencia aditiva de autos (`FSAP_motor`) murió por falta de memoria al correr en paralelo con las semillas de hogar, después de terminar V23. Se relanzó sola como `FSAP_motor_b` con `--desde`; con dos procesos de LightGBM y una evaluación a la vez, la memoria de 7 GB no alcanza.
