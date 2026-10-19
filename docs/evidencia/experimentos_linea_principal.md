# Modelos de Claude para la parte 1

Carpeta de Claude (Cowork), abierta el 17 de octubre de 2026 a petición del participante («ayúdame a mejorar todo significativamente… independiente al trabajo que está haciendo codex»). Contiene el código, las configuraciones, los registros y los resúmenes de los modelos LightGBM que produjeron S03 y los candidatos siguientes. El entrenamiento corrió en el espacio de trabajo en la nube de Claude, con el precedente de D50 y D59: se copiaron las matrices F0 de D68, la asignación de D67, el clima original y la plantilla, y se comprobó el SHA-256 de cada archivo contra el manifiesto de su corrida o contra el catálogo activo antes de usarlo. No se publicó ni redistribuyó nada; los resultados vuelven aquí.

## Origen de S03

| Campo | Valor |
| --- | --- |
| Archivo | `Envios/archivos/S03_lgbm_F0124.csv`, SHA-256 `7877e9e968dfc094df6b9450f51ff1d5f97f12fa82b4d985e2fce18d6af93217`, 626.639 filas |
| Corrida | `runs/S03_lgbm_F0124/` (`resumen.json`, `config.json`, `log.txt`, `prediccion_2025.parquet`, `v24.parquet`) |
| Código | `produccion.py` con `comun.py` y `experimentos.py` (hashes en `runs/S03_lgbm_F0124/manifest.json`) |
| Datos | Matrices `Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca` (hashes del manifiesto D68), asignación `Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0`, `Datos/weather.parquet` y `Datos/sample_submission.parquet` (hashes del catálogo activo) |
| Bloques | F0, F1, F2 y F4, los autorizados en D71; F3 fuera |
| Modelo | LightGBM Tweedie por ramo, potencia de ajuste 1,5, offset log(e_ef_coste) sobre T0 (nivel último por exposición efectiva, sin segundo factor de IBNR, D70), predicción de 2025 con la exposición nominal; tres semillas promediadas |
| Ajustes | learning_rate 0,02; num_leaves 7 en autos y contenidos y 5 en edificios; min_data_in_leaf 2.000 (4.000 en contenidos); regularización de categóricas (cat_smooth 200, cat_l2 50, min_data_per_group 1.000, max_cat_threshold 16); feature_fraction 0,6 en autos |
| Siniestros grandes | En autos la etiqueta de entrenamiento se acota a 15.000 CU por fila y el exceso vuelve como recargo uniforme (×1,30092 en producción); hogar sin tope |
| Validación local | V23 selección 0,13877 global; V24 0,13114 global (autos 0,08366, edificios 0,11018, contenidos 0,0892) |
| Kaggle | Enviado por Codex con el ID 57323464; D² público 0,12321 (S02 0,07211) |

## Qué se probó y qué decidió cada prueba

Todas las comparaciones usan T0 como etiqueta, el offset de exposición efectiva y el D² Tweedie con potencia 1,5 sobre importes, global (tres ramos concatenados) y por ramo. En V23 la parada temprana usa la mitad de calibración de 2023 y la comparación la mitad de selección; V24 se consultó para confirmar candidatos ya elegidos y para decidir el tope de siniestros grandes, y esas consultas quedan registradas aquí.

| Prueba | Resultado | Decisión |
| --- | --- | --- |
| M00 frente a LightGBM F0124 con ajustes por defecto | V23 0,08306 → 0,12485; V24 0,07332 → 0,11836 | El modelo con variables multiplica la señal; M00 en V24 (0,0733) coincidió con su público (0,0721) |
| Rejilla de árboles poco profundos y regularización de categóricas (`grid_g1`, `grid_g2`) | Global V23 0,1249 → 0,1353; `make_model` sobreajustaba con los ajustes por defecto | Hojas 5–7, tasa 0,02, categóricas regularizadas |
| Tope de siniestros grandes en autos (`log_cap*`) | V23: sin tope 0,0808, 100.000 0,0815, 25.000 0,0843, 15.000 0,0859, 10.000 0,0864; mejora también a igual nivel | Tope de 15.000 con recargo uniforme; en hogar el tope empeora V23 |
| Componentes por peligro (Tweedie por peligro con su exposición efectiva) | Global V23 0,1330 frente a 0,1388 del total; la mezcla tampoco mejora | Se descarta para la parte 1 |
| Bloque F3 | Autos 0,0862 → 0,0903; edificios 0,1120 → 0,1098; contenidos 0,0848 → 0,0774; solo en autos, global 0,1388 → 0,1406. `marketing_segment` no añade | El participante autorizó F3 completo solo en autos, sin `marketing_segment` (17 de octubre) |
| `prior_claims_5y` | Constante por cliente; el 66,2 % de los clientes con dos o más siniestros observados en 2021–2024 lo tiene en 0; gradiente igual en 2021 y 2024; distribución idéntica en test | Atributo estático declarado, no una foto posterior de la siniestralidad |
| Calibración al año siguiente | El factor Tweedie estimado en V23 (autos 1,0047, edificios 1,0648, contenidos 1,0771) aplicado a V24 sube el global de 0,13114 a 0,13182 | Candidato aparte, con el factor medio de los dos pliegues |

## Cómo reproducir

Los scripts leen las rutas de `comun.py`, que por defecto apuntan a la copia verificada en la nube. En otra máquina basta con fijar `HAKATON_SEMANA1` a la carpeta `Hackaton/Semana 1` y `MODELOS_WORK` a una carpeta de trabajo, y después:

```text
python construir_variables.py
python rejilla.py <nombre> F0124
python evaluar.py <nombre> F0124 <config.json> total
python produccion.py S03_lgbm_F0124 F0124 runs/S03_lgbm_F0124/config.json --semillas=3
```

`construir_variables.py` añade a cada matriz F0 la historia de la póliza por peligro, su exposición previa y su tasa de notificación previa, la historia de la dirección en hogar (todas con el corte del 1 de enero del año del periodo), la media del clima de los años anteriores y la prima escrita relativa a la media de su año.

## Límites

Verificación propia asistida por IA, sin revisión humana ni independiente. V24 se consultó para decidir el tope de autos y para confirmar candidatos; ya no es una evaluación intacta. El tope de 15.000 CU convierte el exceso de los siniestros grandes en un recargo uniforme: si en 2025 la propensión a grandes pérdidas difiere por segmento, esa diferencia no la ve el modelo. La calibración al año siguiente supone que la tendencia de 2023 y 2024 continúa.

## Segunda ronda, 17 de octubre por la tarde

Envíos puntuados que salieron de esta carpeta: S03_lgbm_F0124 (ID 57323464) con 0,12321 y S04_lgbm_F3autos (ID 57323789) con 0,12435, que sigue siendo el mejor público del proyecto. S04 cambia solo autos respecto de S03 y la mejora pública (+0,00114) coincide con la de V24 (+0,0013).

### Escala de validación

Con S01, S03 y S04 la relación entre V24 y el público es **público ≈ 0,0099 + 0,8644 × V24**, con residuos de ±0,00002. La ganancia local llega al público al 86 %. La recta predijo después el S07 de Codex (V24 0,1317, esperado 0,1238, público 0,1236). S02 se separa de la recta en +0,0012 porque V24 no ve el efecto de nivel: 2024 está inmaduro.

El bootstrap de filas de V24 da una desviación de ±0,0045 en el nivel del D² y de ±0,005 en un subconjunto del 50 %, como el público. Esa oscilación la mueven unos pocos siniestros grandes. Las diferencias pareadas entre modelos son mucho más precisas: S04 − S03 da +0,0013 ± 0,0003. Las decisiones se toman con diferencias pareadas en V23 y se confirman en V24.

Codex anota en D75 una dependencia: la exposición efectiva de 2024 sale de un chain-ladder estimado con todo el triángulo, también en V24. Afecta al nivel de todas las predicciones de 2024 por igual, no al orden entre modelos, y la recta anterior absorbe ese desplazamiento.

### Qué aportó y qué no

| Prueba | V23 selección | V24 | Decisión |
| --- | --- | --- | --- |
| Frecuencia por peligro × severidad media del peligro (Poisson por peligro con su exposición efectiva) | Autos 0,0901 frente a 0,0903 del Tweedie; mezcla 50/50 0,0913 | Autos 0,0867 en las dos estructuras; mezcla 0,0876 | Componente del ensamble en autos (y 20 % en contenidos) |
| CatBoost Tweedie, mismo contrato, profundidad 6, tasa 0,05 | Autos 0,0927 (+0,0025) | Autos 0,0886 (+0,0019) | Componente principal de autos; en hogar no mejora (0,1077 y 0,0751) |
| CatBoost profundidad 8 o tasa 0,03 | 0,0901 y 0,0918 | — | Se queda profundidad 6 y tasa 0,05 |
| Quitar `make_model` y podar 35 variables por permutación en LightGBM de autos | 0,0934 (+0,0032) | 0,0866 (−0,0002) | No se confirma: componente minoritario del ensamble, no sustituto |
| Propensión a grandes siniestros en lugar del recargo uniforme | 0,0884 frente a 0,0903 | — | Se descarta |
| Componente de inundación separado en hogar | Edificios 0,1073, contenidos 0,0837 | — | Se descarta |
| Clima del mismo año | Sin cambio (±0,001) | — | Se descarta; no hay dilema metodológico |
| Interacciones explícitas, codificación suavizada de `make_model`, variables de cartera, credibilidad por póliza | Global 0,1402, 0,1406, 0,1406 y 0,1396 frente a 0,1406 | — | Se descartan |
| Exposición efectiva por segmento (mezcla de peligros por cobertura o suelo) | Sin cambio | Autos −0,0006 | Se descarta |
| Hogar con regularización fuerte, sin región, hojas lineales o elasticidad del capital | Mixto | Contenidos +0,0001 a +0,0004 | Sin cambio en producción |
| Restricciones monótonas en edificios | +0,0006 | +0,0002 (P>0 = 0,84) | Mejora pequeña y coherente; candidata para un componente interpretable |
| XGBoost Tweedie en autos | 0,0832 | — | Se descarta |

### Candidatos preparados

`Envios/archivos/S05r_mezcla_robusta.csv` (SHA-256 `53d740a6…92d814ec8`): autos 50 % Tweedie acotado con F3 y 50 % frecuencia por peligro; contenidos 80/20; edificios Tweedie; factor de calibración al año siguiente por ramo. V24 0,13341; público esperado 0,1252.

`Envios/archivos/S06_ensamble_cat.csv` (SHA-256 `dc5e24e153a71f7368aa9928a8ff453db70caa1bcac6a38331cec6b00a36098b`): igual que S05r, pero en autos CatBoost 0,5, LightGBM 0,1, LightGBM reducido 0,1 y frecuencia por peligro 0,3. V24 0,13396; público esperado 0,1257. Corridas: `runs/S06_ensamble_cat`, `runs/CAT_motor`, `runs/FS_frecsev`, `runs/S06c_lgbm_motor_red`.

## Tercera ronda, noche del 17 al 18 de octubre

Codex subió en este intervalo su S08 (stack CatBoost D76), que marcó 0,12532 en el público. Con S08, la recta de escala predecía 0,1244, así que el resultado quedó 0,0009 por encima. El primer puesto del leaderboard estaba en 0,12815.

### Variables de cliente F3 en hogar (D80)

El participante autorizó siete variables de cliente en edificios y contenidos: `prior_claims_5y`, `credit_band`, `missed_payments_12m`, `household_size`, `years_at_address`, `marital_status` y `licence_points`. Ninguna es comercial y ninguna tiene alta cardinalidad. La comparación pareada (`prueba_f3_hogar.py`: misma configuración, rondas de V23 y tres semillas en V24) dio lo siguiente:

| Ramo | Variables | V23 selección | V24 |
| --- | --- | --- | --- |
| Edificios | las siete | +0,0017 (P>0 = 0,91) | +0,0020 (P>0 = 0,99) |
| Edificios | solo `prior_claims_5y` | +0,0016 | +0,0012 |
| Contenidos | las siete | −0,0004 (P>0 = 0,48) | +0,0036 (P>0 = 1,00) |
| Contenidos | solo `prior_claims_5y` | −0,0025 | +0,0024 |

El F3 completo empeoraba el hogar (contenidos 0,0774 frente a 0,0848 en V23). Quitar las variables comerciales de alta cardinalidad resuelve ese problema. Corrida de producción: `runs/S08h_hogar_F3s2`, con LightGBM de 334 y 322 rondas en V23 y tres semillas.

### Mezcla con el S08 de Codex

`mezcla_codex.py` y `mezcla3.py` mezclan predicciones de las dos líneas de trabajo. Primero igualan el total de cada componente con el del primero del ramo, usando solo predicciones; después aplican el factor de año siguiente de la mezcla. El D² de V24 se informa con el factor estimado en V23.

| Ramo | Claude solo | Codex S08 solo | Mejor mezcla (peso Claude) |
| --- | --- | --- | --- |
| Autos | 0,08877 | 0,08460 | Claude solo (1,0) |
| Edificios (con F3 hogar) | 0,11348 | 0,11326 | 0,11437 (0,5) |
| Contenidos (con F3 hogar) | 0,09308 | 0,08846 | 0,09322 (0,7) |

Las dos líneas se complementan en edificios, con mezcla mejor que cada una en V23 y en V24. En autos el S08 de Codex resta.

### Candidato S09b

`Envios/archivos/S09b_claude_mezcla_hogar_F3s2.csv` (SHA-256 `3961893c2b1766cbf504f370d54ee8f16b6085b48373a271b0c0f6ba422ce1a6`) combina el ensamble de autos de S06 con hogar al 50/50 y al 70/30 con S08. V24 global 0,13552; público esperado 0,1270. El participante eligió que lo suba Codex; la nota de entrega está en `Envios/S09b_claude_entrega_codex.json`.

### Pruebas que no se adoptaron

| Prueba | V23 selección | V24 | Lectura |
| --- | --- | --- | --- |
| Repartir el exceso sobre 15.000 de autos según la frecuencia predicha de lesiones (`hibrido_autos.py`) | 0,08951 frente a 0,09026 | 0,08429 frente a 0,08641 | El recargo uniforme sigue siendo mejor |
| Tweedie sin lesiones más lesiones por frecuencia × severidad | 0,08916 | 0,08581 | Peor que el Tweedie total |
| Recargo del exceso por tipo de cobertura | 0,09065 | 0,08455 | Inestable entre años: se descarta |
| Ventana 2022-2023 y pesos por recencia (`prueba_ventana.py`) | — | Peor en los tres ramos | 2021-2023 completo es lo mejor |
| Potencia Tweedie 1,65 y 1,8 en entrenamiento (`prueba_potencia.py`) | 0,0872 y 0,0797 | 0,0829 y 0,0744 | Se queda 1,5 |
| CatBoost potencia 1,3 | 0,09264 frente a 0,0927 | — | Sin cambio |
| Red neuronal Tweedie con embeddings (`mlp_tweedie.py`, tres semillas) | Autos 0,0859, edificios 0,1116, contenidos 0,0774 | Autos 0,0817, edificios 0,1007, contenidos 0,0862 | Sola es más débil. En la mezcla resta en autos, no confirma en edificios y suma +0,0007 en V24 de contenidos con peso 0,1 |
| Variables de cambio respecto del periodo anterior: prima, capital, NCB, vehículo (`variables_cambio.py`, `prueba_cambio.py`) | Edificios −0,0029, contenidos −0,0029 | Edificios −0,0003, contenidos −0,0006 | Se descartan en hogar |

Una nota operativa: el contenedor de cálculo se reinició a las 21:39 de Bogotá y se perdieron los procesos en segundo plano. Desde entonces las colas esperan por PID y no por patrones de `pgrep -f`, porque la línea de comandos de la herramienta contenía el patrón y la espera nunca terminaba.

## Cuarta ronda, madrugada del 18 de octubre

Esta noche Codex subió S09b (envío 57336991) y obtuvo 0,12889 en el público, por encima del primer puesto que se veía hasta entonces (0,12815). La recta de escala lo situaba en 0,1270: el público respondió más que la pendiente 0,8644 a las mejoras de hogar y a la mezcla con Codex. Después Codex subió N01_A_G (57338908), S09b con un combinador aditivo por peligro, que obtuvo 0,12908.

### Calibración de forma (S11)

`mezcla3.py --forma=<ramo>:<a>:<b>` aplica a la mezcla mu' = e (e/ē)^(b−1) g (r/g)^a. Aquí r = mu/e, g y ē son medias geométricas del corte y e es la exposición efectiva en V23/V24 y la nominal en 2025. El nivel lo fija después el factor de año siguiente. En los tres ramos las predicciones salen demasiado concentradas y el exponente de la tasa coincide entre años: autos 1,095 (V23) y 1,097 (V24), edificios 1,079 y 1,084, contenidos 1,043 y 1,091. Edificios pide además b > 1 en los dos años (1,159 y 1,122) y autos b < 1 (0,966 y 0,849). Fijado en un año y medido en el otro, mejora autos en +0,0004 en ambos sentidos, edificios en +0,0009 y +0,0012, y contenidos en +0,0006 y +0,0001. `S11_claude_forma_tasa_exposicion.csv` mejora a S09b en V24 en autos (+0,00105), edificios (+0,00095) y contenidos (+0,00067), y en el global en +0,00091 con P>0 de 0,993.

### Componentes nuevos (S12)

- `frecsev2.py`: frecuencia Poisson por peligro por severidad modelada. La severidad es un gamma por peligro con al menos 1.500 siniestros positivos; en el resto se usa severidad media. Corrida `runs/FS2_contents`. En contenidos, sola, da 0,0878 en V23 (Tweedie 0,0848). Sustituyendo a la frecuencia con severidad constante en la mezcla suma +0,0005 en V23 y +0,0006 en V24. En edificios no suma.
- `rejilla_hogar.py`: en edificios, `min_data_in_leaf` 1000 mejora V23 en +0,0007 y V24 en +0,0004 (corrida `runs/S12h_edif_md1000`). Más hojas o menos restricción en contenidos empeoran.
- `S12_claude_fs2_md1000_forma.csv` (SHA-256 `fb9ffe5d376b00a61e996587ce6a901cfa6d76d91f847cfc3f51dd8e2ed78b5b`) da V24 0,13661. Frente a S11 mejora en edificios (+0,00020) y contenidos (+0,00061) y queda igual en autos. Frente a S09b mejora en los tres ramos, con un global de +0,00103 y P>0 de 0,997. Su nota de entrega está en `Envios/S12_claude_entrega_codex.json`.

### Lo que se descartó esta noche

Restricciones monótonas en autos (V24 −0,00055), variables de fin de periodo, variables de cambio respecto del periodo anterior, entrenar con el objetivo llevado al nivel del año, la red neuronal en autos y edificios, más hojas en edificios y más o menos restricción en contenidos. El detalle de IBNR, tendencias y nivel está en `../Evaluacion_integral_claude/INFORME.md`.

## Quinta ronda, madrugada del 18 de octubre (S13 y S14)

Codex subió además N01_B (0,12855) y N01_G (0,12825), dos candidatos suyos con mejor D² local de 2024 que bajaron en el público. No quedan envíos hasta las 19:00 de Bogotá del 18 de octubre.

### Frecuencia CatBoost en autos (S13)

`cat_frecsev.py` entrena un CatBoost Poisson por peligro, con offset de la exposición efectiva del peligro, y lo multiplica por la severidad media del peligro en el entrenamiento de cada corte. Se puede reanudar por peligro (`v23_<p>.npz`, `v24_<p>.npy`, `prod_<p>.npy`). En autos (`runs/CFS_motor`), solo, da V23 0,0918 y V24 0,0886, lo mismo que el CatBoost Tweedie. La mezcla de autos pasa a CatBoost Tweedie 0,4, CatBoost de frecuencia 0,4 y los dos LightGBM 0,1 cada uno: `S13_claude_cfs_motor_forma.csv`, V24 0,13678.

### Semillas (S14)

Dos semillas más del CatBoost Tweedie de autos (`runs/CAT_motor_s23`, `cat_produccion.py --semilla_inicial=2`) dan V24 0,08795 frente a 0,08864 del primer par, así que diferencias de 0,0003 en un ramo caben en el ruido de semilla. `combinar_semillas.py` promedia las cuatro (`runs/CAT_motor_4s`, V24 0,08841). `S14_claude_cat4s_forma.csv` (SHA-256 `f22b0033f457858e90c4d9c1d838a71119a838cd99f960a1549379ee8ec8da28`) es S13 con ese componente: V24 0,13674 y menos varianza en 2025. Es el candidato recomendado.

### Robustez frente a la cola (S14c)

`robustez.py` reconstruye cada mezcla igual que `mezcla3.py` y la compara con una referencia: diferencia de D² en V23 y V24, bootstrap pareado por cliente con 1.000 réplicas y la prueba de Codex sin el 0,1 % superior de la pérdida, también con cada predicción renivelada en el subconjunto.

| Frente a S09b | V23 (P de mejora) | V24 (P de mejora) | Sin el 0,1 % superior, V23 / V24 |
| --- | --- | --- | --- |
| S14 | +0,00101 (0,99) | +0,00122 (0,999) | −0,00172 / −0,00051 |
| S14c (forma solo en autos) | +0,00047 (0,93) | +0,00086 (0,99) | +0,00034 / +0,00020 |

En hogar la forma gana en la cola y pierde en el resto, porque los siniestros grandes se concentran en el decil de tasa más alta en los dos años (`../Evaluacion_integral_claude/INFORME.md`, sección 4.5). `S14c_claude_cat4s_forma_autos.csv` (SHA-256 `7360c1a4d68b2bfa7d5f5e708c63b21967226189386601820ce16856e59c7318`) conserva los componentes de S14 con forma solo en autos, pasa esa prueba en el agregado y sirve de contraste en el público. Las dos notas de entrega están en `Envios/`.

## Sexta ronda, mañana del 18 de octubre: foro con Codex y estimación propia S16

El participante pidió que Codex y Claude colaboren en `foros/FORO.md` y que las estimaciones nuevas de cada línea sean independientes: ninguna usa predicciones, totales ni factores de la otra sin una decisión explícita del participante. S09b, S14 y S14c conservan su linaje mixto, porque llevan el stack S08 de Codex en hogar. Los aportes de Claude en el foro son CLA-20261018-001 y siguientes; los escribe `foro/escribir_aporte.py`, que sigue el formato de `foros/comentar.py` sin archivo de bloqueo, porque la máquina virtual de Claude no puede borrar archivos y el bloqueo quedaría puesto.

### Revisión cruzada

- `comparar_codex.py` compara una mezcla de Claude con A_G y H de Codex sobre los mismos 626.190 IDs y T0 de 2024, leyendo sus predicciones sin modificarlas. A_G y H ajustan su meta con validación cruzada por cliente dentro de 2024, así que su D² local no es comparable sin más con el de una mezcla entrenada hasta 2023.
- `importar_gam_codex.py` se usó una sola vez, antes del acuerdo, para revisar el GAM de contenidos de Codex: gana en 2024 (+0,00059 con peso 0,1) y pierde en 2023 (−0,00021). No entra en ningún candidato de Claude.
- `selecciones_v23/` archiva las cuatro selecciones V23 de autos que pedía Codex para reconstruir S12, con `MANIFIESTO.json`.
- `publico_simulado.py` mide, en 1.000 subconjuntos aleatorios del 30 % y el 50 % de los clientes de V23 y V24, cuánto puede variar en el público la diferencia entre dos candidatos.

### Dinámica de nivel de los componentes

La mezcla reescala cada componente al total medio de los de Claude en cada corte. Eso supone que todos se mueven igual entre V24 y 2025, y no es así: las frecuencias con severidad media constante caen un 3 % a 4 % frente al Tweedie de árboles entre V24 y 2025, y la red neuronal de contenidos queda un 10 % por encima del real en V24 y vuelve al nivel de los árboles en 2025. Desde S15 las redes no entran en la referencia de nivel (`NIVEL_INESTABLE` en `mezcla3.py`). Detalle en `../Evaluacion_integral_claude/INFORME.md`, sección 4.6.

### Estimación propia S16_claude_propio

`frecsev2.py --aditivo` entrena por peligro una frecuencia Poisson y una severidad gamma con árboles de una sola división, es decir, un modelo aditivo sin interacciones del estilo de un GAM. La idea viene del GAM que Codex describió en el foro; la implementación es propia y no usa predicciones de Codex. En contenidos (`runs/FSA_contents`) es el mejor modelo de la línea de Claude en los dos cortes: V23 0,08925 y V24 0,09352 solo. En edificios no suma en V23 y no se llevó a producción; en autos estaba corriendo al cierre de esta sección.

`S16_claude_propio.csv` (SHA-256 `65023125e57443b585e6a107f4f68434fa02bfbbe61e61514322bcd60640e012`) es la estimación propia vigente:

| Ramo | Componentes y pesos | V23 / V24 frente a S09b |
| --- | --- | --- |
| Autos | CatBoost Tweedie y frecuencia CatBoost por peligro, cuatro semillas cada uno (0,4 y 0,4); dos LightGBM (0,1 y 0,1) | +0,00057 / +0,00140 |
| Edificios | LightGBM con las siete F3 y `min_data_in_leaf` 1000 (0,8); frecuencia CatBoost por peligro (0,2) | +0,00135 / +0,00065 |
| Contenidos | LightGBM con las siete F3 (0,3); red neuronal (0,1); modelo aditivo (0,6) | +0,00150 / +0,00291 |
| Agregado | | +0,00097 / +0,00135 |

En el D² local de 2024 da 0,13687, frente a 0,13610 de A_G y 0,13726 de H. Frente a A_G las medias son positivas en los tres ramos y el agregado gana +0,00077, con un intervalo por cliente que incluye cero ([−0,00028; +0,00192]); frente a H pierde en autos y edificios y gana en contenidos (+0,00066). S15_claude_propio, la versión anterior sin el modelo aditivo, quedó en `runs/` pero no se entregó como archivo. S14 y S14c siguen como candidatos de linaje mixto.

### Lo que no se adoptó en esta ronda

- La rejilla del LightGBM de autos: `min_data_in_leaf` 1000, tasa 0,01 y `feature_fraction` 0,8 empeoran V23 y V24 (−0,0001 a −0,0018; `experimentos/log_rej_m.txt`).
- CatBoost Tweedie en edificios con las siete F3 (V23 0,1117 solo; en la mezcla no suma con ningún peso).
- La frecuencia CatBoost en contenidos dentro de la mezcla mixta: +0,00036 en V23 y −0,00022 en V24.
- El modelo aditivo en edificios.

Nota operativa: una prueba de CatBoost lanzada en paralelo provocó un error de memoria que mató la frecuencia de autos, y el contenedor se reinició a las 05:44. `cat_frecsev.py` reanudó por peligro sin perder resultados. Con la frecuencia de autos en marcha no se lanzan entrenamientos pesados en paralelo.

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

### Cierre de la ronda

- FSAS en autos (`FSAP_motor_b`, relanzada sola, con la severidad por valor y antigüedad del vehículo) da 0,09158 en V23 y 0,08938 en V24, frente a 0,09306 y 0,09100 de CFSS, y su total se aparta −3,85 % del ancla. Con la regla de la peor de las dos mejoras, el agregado ganaría +0,00003 y +0,00002 (`experimentos/robustez_s21_prueba.json`), por debajo del +0,0001 fijado: no hay S21 y S20 sigue vigente (cierre de D84).
- Por peligro aislado en 2024 (`peligro_aislado.py`, `experimentos/peligro_aislado_buildings.json`), la severidad por capital mejora la cabeza de todos los peligros de edificios con la reserva nominal y con +25 %. La frecuencia CatBoost es mejor en hundimiento y tormenta, y la aditiva en inundación, incendio, escape de agua y daños accidentales.
- `calibracion_deciles.py` da el cociente real/esperado de S20 por decil de tasa predicha (`experimentos/calibracion_deciles_s20.json`).
- Codex repitió S20 desde los componentes guardados (N21) y verificó S18 y S20 en su revisión periódica VAL03. Su hallazgo DATA-005 sobre el clima del año anterior, que aún no está cerrado al cotizar, alcanza también a las F2 de esta carpeta.

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

Preinscrito en CLA-20261018-009 para hogar y en CLA-20261018-011 para autos: LightGBM Poisson por peligro de profundidad intermedia (`frecsev2.py` sin `--aditivo`, con `--partes`) y la severidad GLM encima, con el umbral de +0,0001 en el agregado en los dos cortes frente a S21. En edificios da 0,11472 en V23 y 0,11433 en V24 con la severidad por capital (FS2S_buildings, deriva −1,46 %, dentro de la referencia de nivel); en contenidos, 0,09175 y 0,09322 con la severidad ampliada (FS2Xc_contents, deriva −1,58 %, fuera). En los dos ramos ninguna combinación con peso positivo para el componente nuevo mejora V23 y V24 a la vez, y la rejilla de la peor de las dos mejoras conserva los pesos de S21 (`experimentos/tercer_motor/`). Quedan como resultados adversos. Autos (FS2P_motor y FS2S_motor) tampoco pasa; ver el cierre de la décima ronda.

## Décima ronda, 18 de octubre a media tarde: resultado público de S21 y variante robusta S22

Con autorización del participante (N30), Codex envió H y S21. H obtuvo 0,12886 y S21 0,12874 en el público, por debajo de A_G (0,12908) y de S09b (0,12889) (COD-20261018-049). En V24, S21 superaba a S09b en +0,00255 y lo hacía en el 99,6 % de los subconjuntos del 30 % de los clientes, así que la inversión no se parece al ruido de muestreo de clientes de 2024.

### Diagnóstico sin etiquetas de 2025

- Nivel. S21 predice para 2025 un 2,4 % más que S09b (214,3 frente a 209,2 millones de CU). Mover todo S21 un 2,4 % cambia el D² agregado entre −0,00031 y +0,00015 en V24 y −0,00008 en V23, muy lejos de las 0,0027 de la inversión.
- Forma y nivel. `diagnostico_forma_nivel.py` mide el cociente entre el total con forma y sin ella en cada corte: autos 1,011, 1,010 y 1,013 (V23, V24 y 2025), edificios 1,079, 1,083 y 1,080, contenidos 1,034, 1,034 y 1,031. La forma no desplaza el nivel de 2025 respecto de los cortes donde se ajusta el factor (`experimentos/diag_forma_nivel_s21.json`).
- Cola. Frente a S09b, sin el 0,1 % superior de las filas, S21 queda en −0,00103 en V23 (edificios −0,00335, contenidos −0,00186) y +0,00036 en V24. La misma mezcla sin la forma de hogar gana a S09b en los tres ramos y los dos cortes con y sin ese 0,1 % (`experimentos/robustez_s21_sin_forma_hogar.json`).

### S22_claude_propio

`S22_claude_propio.csv` (SHA-256 `c21a02e14de4a89f892604239b7cfd9ac4e95ea7d175460a25ba806a5a3541b0`, nota `../Envios/S22_claude_entrega_codex.json`) es S21 con la forma solo en autos: mismos componentes, pesos, regla de nivel y factor de año siguiente. Total 211.689.735,38 CU; tasas 2025 por unidad de exposición 594,5, 492,1 y 125,7. `reproducir_mezcla.py` lo repite en el equipo con el SHA-256 idéntico (`experimentos/reproduccion_s22_equipo.json`).

| Ramo | V23 / V24 frente a S09b | Sin el 0,1 % superior | V23 / V24 frente a S21 | Sin el 0,1 % superior |
| --- | ---: | ---: | ---: | ---: |
| Autos | +0,00095 / +0,00283 | +0,00075 / +0,00099 | 0 / 0 | 0 / 0 |
| Edificios | +0,00197 / +0,00114 | +0,00136 / +0,00170 | −0,00153 / −0,00089 | +0,00471 / +0,00146 |
| Contenidos | +0,00328 / +0,00340 | +0,00112 / +0,00074 | −0,00016 / −0,00010 | +0,00298 / +0,00160 |
| Agregado | +0,00164 / +0,00222 | +0,00097 / +0,00114 | −0,00054 / −0,00033 | +0,00200 / +0,00077 |

En 2024, frente a A_G gana +0,00165 (IC95 por cliente [+0,00052; +0,00308]) y sigue por encima con la reserva × 0,75 (+0,00156) y × 1,25 (+0,00173); frente a H queda en +0,00048 ([−0,00041; +0,00138]), +0,00069 y +0,00030, y en edificios por debajo de H (−0,00030 nominal, −0,00087 con +25 %). En los subconjuntos del 30 % de 2024, S21 supera a S22 en el 86,4 % de los casos en V23 y el 79,8 % en V24: si 2025 se comportara como 2024, lo esperable sería que S21 quedara por encima. Sin la forma, el factor de año siguiente deja el total de edificios por debajo del observado en V23 (cociente observado/predicho 1,080, frente a 1,001 con forma; `experimentos/medias_por_ramo_s22.json`), porque el factor que minimiza la devianza Tweedie no coincide con el que iguala totales cuando las predicciones quedan concentradas.

La lectura del resultado público de S22 quedó fijada antes de cualquier envío (CLA-20261018-012): si supera a S21, es coherente con que la forma de hogar no se traslada a 2025; si queda igual o por debajo, la inversión viene de otra parte y la forma no se cambia solo por eso.

### Cierre de la ronda

- El tercer motor de frecuencia también falla en autos: FS2S_motor da 0,09166 en V23 y 0,08926 en V24 (CFSS: 0,09306 y 0,09100), se aparta −3,86 % del ancla y con la rejilla de la peor de las dos mejoras sube el agregado +0,00003 y +0,00004, por debajo del +0,0001 fijado en CLA-20261018-011 (`experimentos/tercer_motor/robustez_s21_prueba_fs2s_motor.json`). Queda adverso en los tres ramos (cierre de D86).
- `intervalos_region.py` añade el remuestreo por región (12 regiones) que usa Codex, con cliente y dirección, la diferencia dentro de cada región y la reserva × 0,75, × 1 y × 1,25. S22 frente a A_G: +0,00165, región [+0,00041; +0,00352], una región negativa; S21 frente a A_G: +0,00198, región [+0,00060; +0,00412] (`experimentos/intervalos_region_s22.json` y `intervalos_region_s21.json`).
- Codex reprodujo S22 desde los componentes y lo retiene por adversos puntuales frente a A_G en la cohorte del segundo semestre de 2024 (COD-20261018-062). Autos es el mismo en S20, S21 y S22, y en contenidos ese semestre S22 retrocede menos que S21 (−0,00392 frente a −0,00458).
- `mezcla3.py` deja fuera de la referencia de nivel FS2Xc de contenidos y FS2S de autos; S21 y S22 se repiten en el equipo con el mismo SHA-256 después del cambio.
- `diagnostico_cuerpo_cola.py` compara el orden de los candidatos enviados en 2024 con y sin el percentil superior de T0, reescalando cada uno por ramo con su factor óptimo dentro del subconjunto. Con todas las filas el orden local (S21, S22, H, A_G, S09b) es casi el inverso del público (A_G 0,12908, S09b 0,12889, H 0,12886, S21 0,12874); sin el p99,5 queda S22, S09b, A_G, H y S21, más parecido al público. Son cuatro puntos y recortar por la etiqueta no es una regla de puntuación válida: es un diagnóstico, calculado después de fijar S22 (`experimentos/diag_cuerpo_cola_publicos.json`, CLA-20261018-015).
- Con la regla preinscrita en CLA-20261018-016, `rejilla_robusta.py` busca pesos de hogar sobre S22 que mejoren a la vez V23 y V24 con y sin el 0,1 % superior de T0. No hay ninguna combinación así en edificios ni en contenidos, de modo que no hay S23 y S22 queda como está (`experimentos/log_rejilla_robusta_buildings.txt` y `log_rejilla_robusta_contents.txt`).

## Undécima ronda, 18 de octubre al final de la tarde: S22 en el público y pruebas sobre S22

El participante decidió probar S22 y Codex lo envió (ref 57370117, archivo neutral `S22_riesgo_ultimo.csv`, mismo SHA-256): 0,12988 en el público, primer puesto al momento de la consulta, +0,00080 frente a A_G y +0,00114 frente a S21 (COD-20261018-084). Según la lectura fijada antes del envío (CLA-20261018-012), es coherente con que la forma de hogar no se traslada a 2025. El participante pidió seguir mejorando S22; cada prueba se fijó en el foro antes de calcularla.

| Prueba sobre S22 | V23 / V24, todas las filas | V23 / V24, sin el 0,1 % superior | Decisión |
| --- | ---: | ---: | --- |
| Sin forma en autos | −0,00024 / −0,00047 | −0,00017 / −0,00012 | La forma de autos se queda (`experimentos/robustez_s22_sin_forma_autos.json`) |
| Relatividades de severidad acotadas al p99,5 (`--tope=0.995`) | −0,00001 / −0,00001 | +0,00001 / +0,00004 | Efecto en el redondeo; no justifica un envío |
| Lo anterior más LightGBM de hogar con tope y recargo uniforme | −0,00020 / +0,00023 | +0,00006 / +0,00009 | No llega al mínimo: no hay S23 |

- `severidad_cfs.py` y `severidad_cfs3.py` aceptan `--tope=q`: la severidad por fila (y_p / n_p en filas con siniestro, sin ponderar por n) se acota al cuantil q del peligro en el entrenamiento del corte solo para estimar las pendientes; sin la opción los componentes se reproducen exactamente. La severidad media base no cambia, pero el total de 2025 sí cambia un poco después de la regla s17 (+0,003 % en autos, −0,066 % en edificios y −0,054 % en contenidos), como señaló Codex (COD-20261018-086).
- Los LightGBM de hogar con tope (`experimentos/s23_pruebas/cfg_hogar_tope.json`: 142.260 CU en edificios y 28.359,5 en contenidos, p99,5 de T0 positivo de 2021-2022, con el mismo mecanismo `cap` que autos) mejoran edificios en V24 (0,11257 → 0,11444) y lo empeoran en V23 (0,1143 → 0,11298). El recargo es un factor multiplicativo, total del entrenamiento entre total acotado (1,046 y 1,017 en 2021-2022).
- Dos semillas más de la frecuencia CatBoost por peligro de autos (`CFS_motor_s45`) dan en V24 0,08861, igual que las anteriores; con cuatro semillas en V24 la mezcla cambia +0,00000 en el agregado (`experimentos/robustez_s22_semillas_v24.json`). Sin efecto: no hay archivo nuevo (CLA-20261018-022, cierre de D87).
- La línea B de Claude entregó S30 (S22 con severidad con tendencia en autos y edificios y pesos de cuerpo en contenidos), que obtuvo 0,12996 en el público (D88, CLB-20261018-002 y 003).
- Las partes de las dos semillas nuevas quedan en `runs/CFS_motor_s45` y `runs/CFSS6_motor` (con `selecciones_v23/sel_CFSS6_motor.parquet`). CFSS6 iguala a CFSS en V23 y V24; en 2025 mueve las predicciones por fila entre −2,2 % y +2,5 % (percentiles 1 y 99) y el total +0,036 %. No hay S22b (CLA-20261018-023).
- Nivel de 2025: en edificios la tasa de S22 (492,1 por unidad de exposición) queda un 4,1 % por debajo de la proyección por tendencias de la sección 3 del INFORME (513,0) y en autos un 1,4 % por encima (594,5 frente a 586,4). Es coherente: sin forma, las predicciones de edificios quedan más concentradas y el factor que minimiza la devianza Tweedie queda por debajo del que iguala totales (cociente observado/predicho en V23 de 1,080 frente a 1,001 con forma). No se toca el nivel.

## Cierre de la parte 1, 18 de octubre por la noche: selección final y paso a los entregables

El participante aprobó S30_claude_b como selección final de la parte 1, con S22_claude_propio de respaldo (D89, CLA-20261018-024). Desde aquí esta carpeta deja de producir candidatos de la parte 1 y el trabajo pasa a los entregables.

- Repositorio reproducible en `Hackaton/Repositorio_IAA2026/`: los scripts de esta carpeta y de `Modelos_claude_b` que producen S22 y S30, copiados sin cambios (hashes en `receta/codigo.json`), la receta de 36 nodos con la orden exacta de cada corrida y su procedencia (colas y registros de la nube) y las huellas de las 184 salidas originales. `python reproducir.py mezcla` repite S22 y S30 con el SHA entregado en la nube y en la máquina virtual del participante; `python reproducir.py componentes` reentrena todo desde las variables y compara cada artefacto (en curso).
- `CFS_motor` es la única corrida que no se reproduce entera con el código actual: su V23 y su V24 se calcularon en float64 antes del cambio a float32; aguas abajo solo se usan sus partes de 2025 y sus mejores iteraciones (iguales a las de `CFS_motor_v23`).
- Borrador del informe de cinco páginas y guion del video de cinco minutos en Claude Docs; lista de adaptación para la parte 2 en `docs/parte2/lista_adaptacion.md` del repositorio.

