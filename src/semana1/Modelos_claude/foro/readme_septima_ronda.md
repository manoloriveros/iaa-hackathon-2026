## Séptima ronda, 18 de octubre a media mañana: severidad en la frecuencia por peligro (S17 y S18)

La frecuencia CatBoost por peligro (CFS) multiplicaba cada frecuencia por la severidad media del peligro, igual para todas las pólizas. `severidad_cfs.py` le añade una relatividad de severidad por peligro: un GLM gamma con enlace log, ajustado en cada corte sobre los siniestros positivos de los años de entrenamiento, con el log del capital relativo a la mediana en hogar (más sótano en inundación) y el log del grupo de valor y la antigüedad del vehículo en daños propios, robo y lunas en autos. Terceros y lesiones conservan la severidad constante. La relatividad se normaliza a media 1 en los siniestros de entrenamiento y multiplica la contribución guardada de cada peligro, sin reentrenar la frecuencia. Las partes por peligro de CFS (`v23_<p>.npz`, `v24_<p>.npy`, `prod_<p>.npy`) quedan en `runs/CFS_*` para poder repetirlo.

| Componente solo | V23 selección | V24 |
| --- | ---: | ---: |
| Edificios, CFS → CFSS | 0,10519 → 0,11562 | 0,10477 → 0,11307 |
| Contenidos, CFS → CFSS | 0,07523 → 0,08961 | 0,07582 → 0,09060 |
| Autos, CFS → CFSS | 0,0918 → 0,09306 | 0,08861 → 0,09100 |

Las elasticidades al capital apenas cambian entre cortes: incendio 0,73 a 0,82, inundación 0,60 a 0,64, tormenta 0,60 a 0,61 y robo de contenidos 0,68 a 0,70 (`runs/CFSS_*/resumen.json`). En autos, V24 usa las dos semillas de `CFS_motor_s23`, porque `CFS_motor` no guardó sus partes por peligro de V24, y 2025 promedia las cuatro: `python3 severidad_cfs.py CFS_motor_4s motor CFSS_motor --v23=CFS_motor_v23 --v24=CFS_motor_s23 --prod=CFS_motor,CFS_motor_s23`. La reproducción da diferencia máxima 0.

### Regla de nivel s17

Con `--nivel=s17`, `mezcla3.py` deja fuera de la referencia de nivel de cada corte los componentes cuyo total 2025/V24 se aparta más de un 1,5 % del Tweedie de árboles del ramo (`CAT_motor_4s`, `S12h_edif_md1000`, `S08h_hogar_F3s2`). La medida no usa etiquetas. Las frecuencias con severidad media se apartan −4,3 % en autos, −2,7 % en edificios y −2,9 % en contenidos, y CFSS −4,4 %, −2,0 % y −2,0 %; aportan relatividades y no nivel, como las redes neuronales desde S15. `robustez.py` acepta la regla como tercera parte de cada candidato (`nombre=spec@forma@s17`).

### Estimación propia S18_claude_propio

`S18_claude_propio.csv` (SHA-256 `a97ad416cbe2967d4734d635bef3e679b64ebceebeb6bb30581358d70b79e7e8`, nota `../Envios/S18_claude_entrega_codex.json`) sustituye a S16 como estimación propia de Claude. S17 fue el paso intermedio y no se entregó. Total 214.392.450,97 CU; tasas 2025 por unidad de exposición 594,5, 509,1 y 126,6.

| Ramo | Componentes y pesos | V23 / V24 frente a S09b | 2024 local S18 / A_G / H |
| --- | --- | ---: | ---: |
| Autos | CatBoost Tweedie de cuatro semillas (0,2); CFSS (0,6); dos LightGBM (0,1 y 0,1) | +0,00095 / +0,00283 | 0,09161 / 0,08930 / 0,09071 |
| Edificios | LightGBM con las siete F3 y `min_data_in_leaf` 1000 (0,5); CFSS (0,5) | +0,00309 / +0,00154 | 0,11591 / 0,11451 / 0,11582 |
| Contenidos | LightGBM con las siete F3 (0,3); red neuronal (0,1); aditivo (0,4); CFSS (0,2) | +0,00250 / +0,00290 | 0,09612 / 0,09491 / 0,09546 |
| Agregado | | +0,00189 / +0,00227 | 0,13779 / 0,13610 / 0,13726 |

Frente a A_G el agregado gana +0,00169, con IC95 por cliente [+0,00041; +0,00321] y por dirección [+0,00039; +0,00338]. Frente a H gana +0,00053, con IC95 por cliente [−0,00039; +0,00156], y las medias son positivas en los tres ramos. A_G y H ajustan su meta dentro de 2024, así que la comparación local los favorece. En 1.000 subconjuntos del 30 % de los clientes, S18 supera a S09b en el 99 % de los casos en V24 y el 97 % en V23, y a S16 en el 94 % en ambos. Sin el 0,1 % superior de la pérdida, el agregado queda en −0,00072 (V23) y +0,00008 (V24): la ganancia de edificios sigue apoyada en la cola. Archivos: `experimentos/robustez_s18.json`, `comparar_codex_s18.json`, `bootstrap_codex_s18.json`, `publico_simulado_s18.json` y `log_finalizar_s18.txt`.

### Lo que no se adoptó en esta ronda

- La severidad híbrida de `severidad_cfs2.py` (el mismo GLM con un LightGBM gamma encima, variables autorizadas y parada temprana en la mitad de calibración). Mejora el componente en contenidos (+0,0010 en V23 y +0,0007 en V24) y apenas en edificios; en autos empeora un poco. En la mezcla no suma: agregado V24 0,13776 frente a 0,13779 (`experimentos/spec_s19_propio.json`, `experimentos/cfsg/`).
- Una forma nueva para S18 (`rejilla_forma.py`). En autos el par vigente sigue siendo el mejor y en edificios ningún par mejora más de 0,00004. En contenidos los dos cortes prefieren b < 1 (con b = 0,9: +0,0033 en V23 y +0,0005 en V24), pero la ganancia de V23 coincide con que 2021, que entra en su entrenamiento, tiene la mitad de periodos parciales que los años siguientes; con producción entrenada hasta 2024 la corrección necesaria sería menor.
- Más peso para la frecuencia CatBoost en contenidos: sube V23 y baja V24, así que queda en 0,2.

Límite añadido: Codex comprobó en N15 que la historia F1 con corte del 1 de enero incluye, en unos cientos de filas por año, avisos posteriores a la cotización. Las F1 de esta carpeta salen de `construir_variables.py` con ese mismo corte, así que la observación les alcanza; no se cambiaron los candidatos.
