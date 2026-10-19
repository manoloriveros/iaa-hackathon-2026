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
