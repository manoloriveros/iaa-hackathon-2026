# Mezcla de C0 por peril y tipo de negocio

Codex. Corte UTC 2026-10-24T00:48:48.397386+00:00. La composición por peril cambia entre negocio nuevo y renovación, pero ninguna de las dos mezclas nuevas mejora el D² puntual de su modelo de referencia. Separar también la severidad empeora los tres puntos frente a separar solo la frecuencia. No se adopta una mezcla nueva ni se elige una contracción después de ver resultados.

## Contraste registrado

El [plan](../../../registro/semana2_c0_mezcla_negocio2023_plan_v1.json) y el comentario COD-S2-20261024-027 preceden al ajuste. Se conserva T0, los 50.094 periodos de 2023, 30.869 componentes y cinco folds. Los modelos de precio siguen siendo B00 constante por ramo, B12 constante por ramo y negocio, y B14 GLM de seis variables, log, Tweedie1,5 y alpha0. El objetivo es T0/e_mix con peso sqrt(e_mix), y la predicción observada e_mix×tasa. Capital, clima, credibilidad y calibración no cambian.

MIXF estima dentro del ajuste de cada ramo/fold una frecuencia Poisson constante por peril y negocio: lambda_pb=n_pb/suma(exposición×qN_p). Conserva la severidad media pooled del peril. Los pesos normalizan lambda_pb×mu_p. MIXFS mantiene esas frecuencias y sustituye la severidad por la media Gamma positiva ponderada por los pesos de truncamiento del propio fold: mu_pb=suma(w_i·T0_i)/suma(w_i). Se estiman una vez y se comparten entre variantes. Las curvas qN_p y qC_p siguen siendo las originales por peril.

Solo entran pesos de mezcla normalizados. El total frecuencia×severidad no se añade como multiplicador al precio. Se reconstruye como control el C0 original a partir de conteos, exposición y severidad pooled originales. Esto no implica que una agregación arbitraria de las nuevas medias por negocio deba devolver la mezcla original: las ponderaciones de frecuencia y severidad son distintas. No se usa ningún coste del retenido para estimar pesos.

Si n_pb=0, la frecuencia estimada está en la frontera cero y su peso es cero; la severidad queda sin estimar. No significa ausencia futura de riesgo. Una celda positiva con masa de ponderación inválida habría detenido la prueba, sin fallback con validación. No ocurrió. No se añadieron priors, curvas por negocio, máscaras individuales de cobertura o intensidad de suavizado elegida por score.

## Qué cambia en la composición

La distancia de variación total es la mitad de la suma de diferencias absolutas entre los pesos nuevos y de renovación. Equivale a la fracción mínima de peso que habría que redistribuir para igualar ambas mezclas. Los rangos siguientes recorren cinco ajustes que comparten muchos siniestros; no son cinco observaciones independientes.

| Ramo | Variante | Distancia entre mezcla nueva y renovación, rango entre folds |
| --- | --- | ---: |
| buildings | MIXF | 54.56%–60.98% |
| buildings | MIXFS | 55.63%–64.76% |
| contents | MIXF | 5.96%–11.63% |
| contents | MIXFS | 12.23%–47.28% |
| motor | MIXF | 3.50%–5.73% |
| motor | MIXFS | 19.47%–27.37% |

Promedios de pesos entre los cinco ajustes, con conteos nuevos por peril dentro de cada ajuste:

| Ramo | Peril | Pooled | MIXF renovación | MIXF nuevo | MIXFS renovación | MIXFS nuevo | Siniestros nuevos por ajuste |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buildings | accidental_damage | 0.8% | 0.8% | 1.0% | 0.8% | 1.1% | 2–3 |
| buildings | escape_of_water | 8.7% | 8.5% | 13.3% | 8.8% | 7.5% | 6–8 |
| buildings | fire | 55.0% | 57.6% | 0.0% | 58.5% | 0.0% | 0–0 |
| buildings | flood | 17.9% | 16.9% | 37.4% | 16.1% | 43.9% | 2–4 |
| buildings | storm | 8.9% | 8.5% | 18.0% | 8.5% | 15.3% | 12–18 |
| buildings | subsidence | 8.8% | 7.7% | 30.3% | 7.3% | 32.2% | 3–5 |
| contents | accidental_damage | 8.4% | 8.2% | 11.5% | 7.9% | 16.6% | 12–14 |
| contents | escape_of_water | 15.0% | 15.4% | 9.8% | 15.4% | 10.2% | 3–4 |
| contents | flood | 33.4% | 33.2% | 36.7% | 34.8% | 14.1% | 3–4 |
| contents | theft | 43.1% | 43.2% | 41.9% | 42.0% | 59.0% | 8–12 |
| motor | bodily_injury | 35.4% | 35.1% | 38.2% | 31.9% | 57.3% | 16–23 |
| motor | glass_hail | 5.2% | 5.2% | 4.5% | 5.6% | 2.5% | 34–41 |
| motor | own_damage | 18.0% | 18.0% | 17.6% | 18.9% | 12.3% | 94–104 |
| motor | theft | 8.7% | 8.8% | 7.8% | 8.9% | 7.7% | 10–15 |
| motor | third_party_prop | 32.7% | 32.8% | 31.9% | 34.7% | 20.1% | 78–86 |

La ausencia de incendio en edificios nuevos de 2023 se repite como cinco celdas de ajuste con cero, una por fold. Es una ausencia observada en esa misma población, no cinco hallazgos independientes. Los pesos cero que produce el estimador no permiten concluir que ese negocio no tendrá incendios.

## Escasez y concentración

El tamaño efectivo de ponderación es (suma w)²/suma(w²). Describe concentración de pesos de truncamiento, no un intervalo de credibilidad o cantidad de siniestros independientes. La última proporción mide cuánto del coste ponderado de una celda positiva aporta su siniestro más grande.

| Ramo | Negocio | Siniestros de ajuste entre folds, todos los perils | Mínimo tamaño efectivo de celda positiva | Mayor peso de un siniestro en el coste de una celda | Celdas cero entre folds |
| --- | --- | ---: | ---: | ---: | ---: |
| buildings | Renovación | 374–389 | 19.00 | 21.6% | 0 |
| buildings | Nuevo | 29–35 | 2.00 | 91.8% | 5 |
| contents | Renovación | 356–370 | 31.00 | 13.3% | 0 |
| contents | Nuevo | 26–33 | 3.00 | 97.2% | 0 |
| motor | Renovación | 2554–2629 | 132.00 | 5.2% | 0 |
| motor | Nuevo | 249–258 | 10.00 | 42.0% | 0 |

Los grupos y siniestros concretos quedan privados. No se usa esa concentración para quitar costes, elegir pesos o fijar una contracción a posteriori. La escasez limita la interpretación de MIXFS aunque su promedio Gamma esté correctamente calculado.

## Por qué una mezcla distinta puede mover poco C0

Si las curvas de completitud de los perils son parecidas, cambiar sus pesos tiene poca repercusión. Para cada fila se verificó la cota |q_mix−q_base| <= TV(w_mix,w_base)×(máximo qC_p−mínimo qC_p), usando su propio fold y tipo de negocio. Es una propiedad de mezclas convexas. Las 100,188 filas variante/periodo, dos por cada periodo OOF de 2023, satisfacen la cota con tolerancia1e-12.

La cota explica una sensibilidad pequeña de exposición aun con pesos distintos; no prueba que los pesos sean verdaderos, que la curva compartida sirva para ambos negocios o que 2025 tenga el mismo soporte de maduración. En edificios las distancias entre negocios superan el 54%, pero el rango máximo de sus curvas por peril es de unos 2,58 puntos de completitud. Hay diferencias por fila que el total oculta: en autos nuevos, MIXFS reduce la exposición efectiva hasta un 4,47% frente a C0 base. Este porcentaje describe el enlace, no un cambio igual del precio. Los perfiles por ramo y negocio quedan en el anexo.

## Resultado de los modelos estándar

| Modelo | Enlace | D² global | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: |
| B00 | Base | 0.06858169 | 0.980 | 15.787289 | +0.000% |
| B00 | MIXF | 0.06851857 | 0.980 | 15.789714 | +0.015% |
| B00 | MIXFS | 0.06800887 | 0.978 | 15.801605 | +0.091% |
| B12 | Base | 0.07491526 | 0.995 | 15.544087 | +0.000% |
| B12 | MIXF | 0.07490354 | 0.995 | 15.546561 | +0.016% |
| B12 | MIXFS | 0.07481207 | 0.995 | 15.560229 | +0.104% |
| B14 | Base | 0.08671008 | 0.991 | 15.606084 | +0.000% |
| B14 | MIXF | 0.08670076 | 0.991 | 15.608671 | +0.017% |
| B14 | MIXFS | 0.08662626 | 0.991 | 15.621943 | +0.102% |

En B14, MIXF mueve el nominal condicionado +0,0166% y MIXFS +0,1016%. El nominal es exposición nominal de los mismos periodos de 2023 por su tasa bajo coste completo, no una predicción de 2025/test o una etiqueta última. Un movimiento pequeño del total no implica estabilidad individual ni valida las ponderaciones de negocio.

En autos nuevos de B14, el D² pasa de −0,010045 a −0,010191 con MIXF y −0,011551 con MIXFS. En edificios nuevos, MIXFS da 0,050177 frente a 0,050163 base; en contenidos nuevos, 0,153679 frente a 0,153579. Son puntos descriptivos por celda, sin intervalos de superioridad específicos; esos cambios pequeños no compensan ni ocultan el deterioro global o de autos nuevos.

La [prueba de cola](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) y la [sensibilidad de reservas/reportes](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) conservan sus resultados y sus condiciones. No se repitieron sus modelos o remuestreos, ni se combinaron sus efectos con esta prueba.

## Incertidumbre exploratoria

Solo se añadieron doce contrastes con 2.000 sorteos comunes de componentes: tres comparaciones entre familias dentro de cada variante, MIXF frente a cada padre original y MIXFS frente a MIXF. Todo usa el mismo T0 y las mismas filas. Los intervalos condicionan en los ajustes guardados, incluidos los pesos de la primera etapa; no reestiman su incertidumbre ni corrigen la búsqueda adaptativa.

| Contraste | Delta D² | Intervalo exploratorio95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
| MIXF_W2-B12/MIXF_W2-B00 | +0.00638497 | [-0.00205352; +0.01856298] | -0.00740125 |
| MIXF_W2-B14/MIXF_W2-B00 | +0.01818218 | [-0.00621997; +0.04268353] | -0.01249804 |
| MIXF_W2-B14/MIXF_W2-B12 | +0.01179721 | [-0.00971461; +0.03168981] | -0.01284945 |
| MIXFS_W2-B12/MIXFS_W2-B00 | +0.00680320 | [-0.00192002; +0.01954421] | -0.00743239 |
| MIXFS_W2-B14/MIXFS_W2-B00 | +0.01861739 | [-0.00571939; +0.04354553] | -0.01239263 |
| MIXFS_W2-B14/MIXFS_W2-B12 | +0.01181419 | [-0.00970709; +0.03170717] | -0.01284616 |
| MIXF_W2-B00/W2-B00 | -0.00006312 | [-0.00017003; +0.00000500] | -0.00008596 |
| MIXFS_W2-B00/MIXF_W2-B00 | -0.00050970 | [-0.00117663; -0.00012247] | -0.00058851 |
| MIXF_W2-B12/W2-B12 | -0.00001172 | [-0.00003922; +0.00000474] | -0.00001962 |
| MIXFS_W2-B12/MIXF_W2-B12 | -0.00009147 | [-0.00026056; +0.00000111] | -0.00012636 |
| MIXF_W2-B14/W2-B14 | -0.00000932 | [-0.00003275; +0.00000614] | -0.00001849 |
| MIXFS_W2-B14/MIXF_W2-B14 | -0.00007450 | [-0.00021550; +0.00000760] | -0.00011201 |

Los tres puntos MIXF son menores que sus bases y los tres MIXFS menores que MIXF. No se promueve, retira o declara equivalente una alternativa por estas cifras. El catálogo principal de 19 recetas conserva su C0 y su corte; estas seis configuraciones son sensibilidad de observación, no candidatos nuevos bajo un enlace común congelado.

## Verificación y decisiones

Se completaron 30 GLM y 90 constantes de precio nuevos, sin reintento o cambio de receta. Aparte se estimaron 150 constantes Poisson de mezcla y 145 medias Gamma ponderadas positivas. Las cinco medias no estimadas corresponden a las cinco celdas cero. No hubo nuevas curvas de reporte o auxiliares de credibilidad. El contador propio de precios queda en 165 ajustes y 285 constantes; los estimadores de mezcla y los 30 auxiliares anteriores se registran por separado.

Pasaron 1570 controles separados, 47 adversos y 32 comprobaciones adicionales de interpretación, con solapamiento. El comprobador no importa el productor y bloquea fit. Reconstruye pesos de truncamiento, exposición y óptimos Poisson/Gamma por minimización numérica, medias y concentración, C0 pooled y pesos por negocio, óptimos de precio, parámetros/gradientes, imputación del ajuste y exp(X beta). Verifica ámbitos, métricas/segmentos y doce remuestreos por multiplicidades. Los adversos prueban invariancia a escala total, escala de pesos y orden, costes del retenido sin efecto, celdas cero explícitas y rechazo de 2024/test, negocio inválido, claims del retenido, duplicados, curvas desordenadas y masa nula. Las recomputaciones aritméticas de esos adversos no son nuevos modelos o evidencia independiente.

Se conserva C0 pooled como referencia, sin adoptar MIXF/MIXFS, fabricar severidades o ajustar una intensidad de suavizado por score. Sigue condicionada la curva de reporte/coste compartida, la dependencia coste/retraso por negocio, la exposición individual a cada cobertura y la masa no observada. La validación agrupada de 2023 al corte 2024-12-31 no representa información disponible al inicio de 2023. Se mantienen las condiciones de capital, clima, reservas y prior, y los responsables de hallazgos ajenos.

La siguiente unidad preparará un balance de mecanismos identificados y condicionados; antes de ajustar curvas por negocio o precios más complejos revisará soporte temporal y adecuación de celdas, con receta previa para nuevos ensayos. B00 y todas las alternativas permanecen intactos. 2024 sigue cerrado expresamente, ledger ausente, sin precios, predicciones o scores de ese año o test. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Revisión técnica propia de Codex, no profesional independiente.

## Evidencia

- [Resultados](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/report.json), [decisiones](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/decision_journal.json).
- [Comprobador separado](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/verifications/mix_20261024T005106Z_bdcdc17e.json), [adversos](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/fixture_checks.json).
- [Perfil de mezcla, escasez y exposición](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/diagnostics/mixture_readout.json), [celdas privadas](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/diagnostics/peril_business_cells.parquet).
- [Foro](../../../../Semana%202/Foro/FORO.md), comentarios 027–028.


## Aviso de ámbito al cierre

Después de terminar esta ejecución se recibió CLA-S2-20261024-005, que anuncia una apertura de 2024 por autorización en otro chat. No se incorporan o leen sus predicciones, actas o scores. La instrucción directa de esta tarea mantiene 2024 cerrado; este ensayo no abre una segunda confirmación o decide el alcance de una autorización ajena. El [recibo fechado](../../../privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/confirmation_scope_notice.json) registra solo existencia del ledger común, sin contenido, y conserva el conflicto de ámbito. Las novedades del foro se revisarán primero por encabezados para evitar consultar resultados de 2024 dentro de esta línea.


## Seguimiento posterior: calendario y exposición de información

El [diagnóstico siguiente](SOPORTE_CALENDARIO_REPORTE_2023.md) conserva esta prueba y examina calendario y soporte sin nuevos ajustes o scores. Después del corte de este informe, un título del foro mostró métricas ajenas de 2024; se registra el incidente y se corrige el lector para ocultar asuntos y cuerpos. No puede afirmarse ceguera completa desde esa exposición. Los resultados propios de esta mezcla se calcularon antes del anuncio y permanecen sin cambio.
