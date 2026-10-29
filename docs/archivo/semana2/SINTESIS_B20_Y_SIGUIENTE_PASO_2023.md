# B20: síntesis de atribución, contracción y calibración

B20 queda como alternativa estándar. Su regularización reduce la norma conjunta de los coeficientes y mejora el D² OOF agregado, pero la ventaja se invierte al retirar unos pocos grupos favorables. Las bandas muestran diferencias de calibración con soporte desigual. Esta evidencia explica el comportamiento; todavía no justifica recalibrar, promover B20 o añadir capacidad.

Codex, corte documental UTC 2026-10-24T02:53:16.816995+00:00. Se reúnen tres diagnósticos terminados de 2023 y el recibo original de B20. Solo se leen JSON y Markdown agregados guardados: cero entrenamiento, inferencia, remuestreo o lectura de OOF, modelos y originales. La unidad concurrente de incendio/AD queda fuera de este corte y se conserva sin alterar.

## Evidencia que comparten los diagnósticos

B20 conserva los siete efectos principales, transformaciones, folds por cliente/domicilio y objetivo T0/puente C0 de B19; cambia la penalización ridge de alpha 0 a 1 con intercepto libre. La comparación usa 50.094 periodos OOF y 30.869 componentes. El objetivo evaluado es coste observado: μ = C0 × tasa anual; sus totales no certifican coste último de 2025. El conteo propio acumulado sigue en 195 ajustes de precio y 285 constantes; esta síntesis añade cero.

| Comparación B20 frente a | ΔD² completo | IC 95% exploratorio guardado | ΔD² sin sus 31 grupos más favorables |
| --- | ---: | ---: | ---: |
| B19 | 0,006912 | [0,001420; 0,013511] | -0,003869 |
| B14 | 0,002672 | [-0,003673; 0,008683] | -0,006513 |
| B00 | 0,020800 | [0,000346; 0,041688] | -0,006580 |

Son intervalos condicionales a predicciones y ajustes ya realizados, procedentes de investigación adaptativa en 2023. No incorporan volver a estimar el modelo o el puente y no equivalen al intervalo simultáneo del protocolo de promoción. No se vuelven a calcular.

## Por qué se invierte la ventaja

La ganancia aditiva es devianza de la referencia menos devianza de B20. Frente a B14, el total es +14.803,66: sus 31 componentes más favorables aportan +48.637,02 y los restantes −33.833,36. Son 62 periodos, 31 positivos y el 10,93% del coste observado, aunque solo representan el 0,10% de los componentes. La ganancia de esos 31 supera la ganancia neta porque compensa pérdidas en otras filas.

Al excluirlos, el numerador pasa a negativo. El nuevo denominador nulo modifica la magnitud, pero al ser positivo no causa el cambio de signo. Aun manteniendo el denominador completo, la contribución restante frente a B14 es −0,006106 de D²; al recalcularlo queda −0,006513. Frente a B19 y B00 ocurre el mismo mecanismo con listas favorables diferentes. Estas listas se eligieron con resultados observados: describen sensibilidad, no una regla para depurar datos o identificar una población estable.

La pérdida remanente frente a B14 se extiende por varios segmentos, especialmente renovación de edificios y autos nuevos, mientras renovación de contenidos conserva ganancia. No significa que todos los grupos restantes empeoren: hay ganancias y pérdidas compensadas. Los 12 grupos/20 periodos fijados en el análisis anterior de B19 tampoco son una muestra representativa ni coinciden con cada lista de 31.

## Qué cambia la contracción

Las 15 parejas de ajustes reducen la norma L2 estandarizada entre 28,7% y 61,4%. En 14 de ellas aumenta al menos una coordenada en valor absoluto: hay 33 excepciones. La penalización contrae el conjunto; no garantiza que cada coeficiente o precio se acerque a cero o a una referencia comercial. La interpretación depende de codificación, centrado y categorías de referencia comunes.

El total esperado observado baja de 15.436.941,83 a 15.126.408,70 CU (2,01%). En los 12 grupos fijados baja 1,64%, mientras los cinco autos nuevos adversos aumentan 12,10%. El nivel global no explica por sí solo qué filas mejoran.

| Caso ya fijado | Coste T0 observado, CU | μ B19 → B20, CU | Ganancia de devianza B20 |
| --- | ---: | ---: | ---: |
| Autos nuevos, lesión corporal | 136767,16 | 90,25 → 95,07 | 1478,30 |
| Edificios, incendio OOF más adverso | 261192,30 | 168,39 → 244,78 | 13724,81 |
| Edificios, incendio influyente sobre AD | 286093,00 | 340,33 → 334,29 | -557,25 |

Los dos incendios comparten el mismo cambio de cobertura en log-tasa (+0,004636), pero el cambio total es +0,374102 y −0,017907. Los otros efectos explican la diferencia; no es un efecto causal aislado de la cobertura AD. La esperanza de coste del periodo tampoco tiene que igualar la severidad realizada de un siniestro.

Los 20 periodos fijados aportan +14.620,81 de los +38.299,18 globales frente a B19 (38,2% de ganancia neta). Un incendio aporta +13.724,81 y el otro −557,25. Este cotejo coincide con atribución y muestra compensación en una selección previa; no aporta una segunda validación independiente.

## Qué revela la calibración

A/E es suma observada dividida por suma esperada. El global B20 de 1,0113 y el B19 de 0,9909 ocultan diferencias entre riesgos. Los quintiles de tasa anual se fijaron exclusivamente en las filas de ajuste de cada ramo/fold. B19 se evalúa sobre las mismas bandas y filas de B20. Las bandas son posiciones relativas dentro de cada ajuste, no cinco umbrales monetarios universales.

| A/E B20, de menor a mayor tasa | Banda 1 | Banda 2 | Banda 3 | Banda 4 | Banda 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos | 1,082 | 0,861 | 1,038 | 1,019 | 0,981 |
| Edificios | 1,966 | 1,563 | 0,856 | 1,198 | 0,714 |
| Contenidos | 1,226 | 1,175 | 0,759 | 1,444 | 0,789 |

Varios extremos se acercan a uno frente a B19, pero otras bandas empeoran. En edificios, banda 1 tiene 69 periodos positivos y un componente reúne 31,65% del coste; su A/E varía entre 0,342 y 3,457 según fold. La banda 5 tiene 124 positivos y A/E 0,714. Los folds comparten entrenamiento: sus rangos no son intervalos de confianza ni cinco réplicas independientes.

En autos nuevos la banda 1 está vacía; la 2 tiene 13 periodos y dos positivos (A/E 11,991); la 3, 104 y seis (A/E 6,786), con 93,91% del coste en un componente. No se redibujan bandas para llenar celdas. El quintil más alto concentra 2.145 periodos, 232 positivos y A/E 0,823. El número de positivos cuenta periodos, no siniestros.

El replay guardado de ajuste tiene 200.376 apariciones de 50.094 periodos, no nuevas observaciones independientes. Un intercepto Tweedie libre satisface un score ponderado, no fuerza igualdad de sumas observada/esperada. Por eso A/E de ajuste distinto de uno no exige normalización automática. Cuatro tasas OOF fuera del rango de ajuste permanecen señaladas, sin recorte.

## Qué falta y qué decisión permite

| Pregunta pendiente | Evidencia necesaria | Consecuencia actual |
| --- | --- | --- |
| Fallo residual concreto | Mecanismo material y reproducible que se distinga de concentración de costes, soporte o maduración | No añadir una receta para perseguir un A/E extremo |
| Recalibración | Soporte y estabilidad; corrección aprendida dentro de ajuste y evaluada fuera de sus filas de estimación, con comparador y criterio previos | No factores por banda, isotónica o normalización |
| Complejidad adicional | Mejora incremental verificable de una modificación mínima que resuelva el mecanismo y conserve límites de riesgo | Mantener modelos estándar; no interacciones, árboles o routing por ahora |
| Confirmación predictiva | Evidencia admisible que trate búsqueda adaptativa e incertidumbre del aprendizaje completo; conciliación separada del estado y autorizaciones comunes | Más remuestreo de las mismas OOF no cierra la carencia; 2024/test siguen cerrados aquí |
| Promoción | Acta y recibos aplicables de la política común, además de advertencias resueltas con evidencia | B00 conserva referencia, todas las alternativas permanecen |
| Uso actuarial | Sustento de último, reservas/reaperturas, retrasos, capital, semántica y ancla de nivel; revisión humana competente registrada | Mantener el alcance condicional, sin certificar suficiencia de primas |

La política común ya fija ΔD² mínimo útil de 0,0005, límite inferior del intervalo simultáneo de 99,1667% estrictamente superior a ese margen, salvaguardas para población nueva, escenarios de reservas/cola y veto por segmentos. También exige influencia admisible y explicar variaciones nominales por ramo superiores al 5%. Aquí no se ejecuta esa evaluación ni se cambia ningún umbral. Los intervalos y cortes diagnósticos de 2023 no la sustituyen.

El siguiente paso defendible consiste en un diseño previo revisable: una hipótesis residual concreta, una sola modificación estándar, fuentes y disponibilidad temporal, separación de ajuste/evaluación, comparador, métricas, salvaguardas, criterio de parada y coste. Aún falta evidencia suficiente para escoger esa modificación. No queda autorizado ni seleccionado un B21, otro alpha o un calibrador. Si el mecanismo procede del objetivo o de información de último insuficiente, la respuesta es resolver esa carencia antes de aumentar capacidad.

2024 y test permanecen cerrados en este trabajo. Se conserva declarada la exposición previa a métricas en un título de otro chat, sin reproducirlas o usarlas; no se afirma ceguera completa. Esta síntesis no consulta la apertura global, actas, scores o ledger, ni presupone válida o inválida la autorización ajena. Una eventual conciliación de alcance requiere una actuación separada; no crea otra tanda ni restaura un holdout intacto.

## Recibos y decisiones registradas

| Diagnóstico | Recibo final consultado | Alcance |
| --- | --- | --- |
| Atribución | 1.014 comprobaciones, 16 adversos; cierre 20/0 | Ganancias por grupos/segmentos y descomposición de log-tasa |
| Contracción | 690 comprobaciones; cierre 227/0 | 15 parejas de coeficientes y replay focal de 20 periodos ya fijados |
| Bandas | 2.121 comprobaciones, 21 adversos; cierre 21/0 | Cortes solo de ajuste, mismas filas B20/B19 y soporte |

Se consultan esos recibos guardados, no se repiten sus suites ni se suman como evidencia independiente. Atribución usa el recibo corregido de representación null/NaN; el fallo inicial y la enmienda de arranque permanecen archivados. La contracción v1 se sustituyó antes de cálculo por v2. No se borran intentos adversos ni se presentan como éxito inicial.

Las decisiones SYN-01 a SYN-09 y las carencias G1 a G6 quedan en JSON, enlazadas a snapshots y SHA. Se aplica Documentación IAA §3 para la ficha de modelo y Gobernanza §2.8 para distinguir comprobación propia de revisión independiente; las consideraciones de propósito, desigualdad entre segmentos y competencia siguen §§3.1, 3.3 y 3.7–3.8. Esta revisión de Codex no constituye revisión profesional independiente.

[Atribución](ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md), [contracción](CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md), [calibración](CALIBRACION_B20_BANDAS_AJUSTE_2023.md), [B20 original](GLM_RIDGE_COBERTURAS_2023.md), [política común](../../../registro/semana2_politica_seleccion_v1.json), [plan de síntesis](../../../registro/semana2_b20_sintesis_plan_v1.json) e [índice](../../../registro/semana2_b20_sintesis_actual.json). Los snapshots y recibos de esta consolidación están en `privado/semana2/desarrollo2023/b20_sintesis_20261024_v1`, fuera de Git.
