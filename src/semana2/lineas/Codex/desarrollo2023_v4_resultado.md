Codex. Respondo a COD-S2-20261023-014. La [prueba v4](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md) quedó completada y verificada exclusivamente con 2023. Las diez tablas OOF anteriores, B00 incluido, son exactas; no se tocaron recetas históricas. [Índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json).

B08 mejora frente a B00 en los cinco folds, pero la sensibilidad preinscrita de reentrenamiento muestra dependencia del nivel de pocos grupos. Se retiraron del ajuste 25 componentes de mayor coste por fold (46–53 filas; 2,715–3,408 millones CU), sin eliminar validación. S08 cae de D² 0,09318 a 0,06916 y de 15,599 a 11,625 millones CU predichos (−25,48 %), A/E 1,316. La mediana de cambio de tasa es −7,27 %. La constante S00 reestimada bajo el mismo estrés queda en D² 0,03932: S08 conserva una diferencia +0,02984. Es sensibilidad del modelo de riesgo/preprocesado con C0 fijo, que aún refleja grupos retirados; no estabilidad integral de reporting, jackknife completo o confirmación temporal. No se propone recortar siniestros grandes.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo | A/E nuevo |
| --- | ---: | ---: | ---: | ---: | ---: |
| W2-B00 | 0.06858 | 15.614 | 0.980 | 0.04783 | 1.550 |
| W2-B08 | 0.09318 | 15.599 | 0.981 | 0.07297 | 1.182 |
| W2-B09 | 0.08077 | 15.618 | 0.979 | 0.04065 | 1.502 |
| W2-B10 | 0.09424 | 14.161 | 1.080 | 0.08037 | 1.019 |
| W2-B11 | 0.08659 | 14.319 | 1.068 | 0.08304 | 1.043 |

Columnas de la tabla: receta, D² global, predicho millones CU, A/E global, D² nuevo negocio, A/E nuevo negocio. Observado total 15,297 millones CU y nuevo 1,528. B10/B11 usan los 60 escalares Tweedie por ramo/fold/tipo de negocio preinscritos, aprendidos solo en ajuste sobre B08/B09; sin nuevos estimadores base para estas dos variantes. El estrés ajustó quince GLM y quince constantes, sin árboles ni búsqueda. Acumulado de las cuatro tandas: 65 estimadores base y 30 constantes; reusos y adaptadores se cuentan aparte.

La brecha de B09 se concentra en autos nuevos (antes A/E 1,910, D² −0,14736); B11 pasa a A/E 1,042 y D² −0,04508. El agregado nuevo B11 mejora D² 0,04065→0,08304 y A/E 1,502→1,043. Sin embargo, edificios nuevos empeora en ambos: B08→B10 D² 0,03253→0,01111, B09→B11 0,05680→0,02595, pese a sus A/E cercanos a uno. Solo hay 40 positivos nuevos en edificios y 36 en contenidos. No se confunden nivel y forma ni se cierra la advertencia de B09 por una receta nueva.

| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar 31 grupos |
| --- | ---: | --- | ---: |
| W2-B10 / W2-B00 | 0.02566 | [0.01358; 0.03766] | 0.00691 |
| W2-B11 / W2-B00 | 0.01801 | [0.00955; 0.02745] | 0.00346 |
| W2-B10 / W2-B08 | 0.00106 | [-0.00349; 0.00648] | -0.00336 |
| W2-B11 / W2-B09 | 0.00582 | [-0.00158; 0.01619] | -0.00506 |

Comparaciones: candidato/padre o referencia, delta D², intervalo exploratorio 95 %, delta al retirar 31 grupos favorables a esa pareja. B10/B08 y B11/B09 tienen intervalos que incluyen cero y cambian a signo adverso tras el retiro. Frente a B00, B10/B11 siguen positivos tras retiro propio (+0,00691/+0,00346) y las listas congeladas de B08/B09 (+0,00701/+0,00835). Las 66 parejas y 2.000 sorteos comunes no corrigen búsqueda adaptativa o multiplicidad; no equivalen a la confirmación de2024.

Pasaron 21 casos focales y 1178 controles del comprobador separado (con solapamiento): factores/derivadas, fuentes, reproducción sin fit, transformaciones y selección de grupos del estrés, métricas, escenarios, remuestreo e influencia. Revisión propia de Codex, no validación profesional independiente. El intento inicial de corrida abortó antes de factores o entrenamiento por una comprobación de claves del OOF multirreceta; se corrigió sin cambiar recetas y se conserva. El primer comprobador abortó por una variable local y se corrigió sin reentrenar. La lectura inicial duplicada del OOF se conserva sin contarse como evidencia adicional.

Se mantiene B00 y B01–B11, sin promoción, retiro, equivalencia o lista final congelada. Quedan visibles sensibilidad del nivel de B08, celdas adversas de edificios nuevos, incertidumbre de la ventaja sobre los padres y supuestos de último/reservas. No se inicia otra tanda tras ver estos resultados. 2024 permanece cerrado por instrucción expresa independientemente del selector: cero precios, scores y predicciones de ese año o test, ningún ledger, envío, remoto, publicación externa o delegación. Las advertencias ajenas conservan responsables y alcance.
