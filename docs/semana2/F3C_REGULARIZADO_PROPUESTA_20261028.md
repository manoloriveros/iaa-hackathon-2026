# F3c regularizado: propuesta orientada al privado

Codex, 28 de octubre de 2026. Propuesta solicitada después del cierre técnico de F3c. Es un candidato nuevo, F3c-R, todavía sin entrenamiento ni evidencia de superioridad predictiva. F3c sigue como referencia enviada. R1, B00 y los ensayos adversos se conservan.

## La decisión que propongo

Conservar el tronco completo de F3c y sustituir su capa final por una calibración Tweedie pequeña, conjunta y penalizada. El modelo aprendería cuánto corregir el nivel de cada combinación ramo/negocio y cuánto conservar del bloque propio. Las correcciones tenderían a la identidad cuando el entrenamiento no respalde apartarse de la base. No se impondría que el nivel de negocio nuevo se parezca al de renovación.

La complejidad nueva sería de seis niveles y, como máximo, seis intensidades de corrección. En la estructura actual edificios tiene bloque propio identidad: sus dos intensidades serían cero fijas, dejando diez coeficientes activos. El número total de parámetros del sistema sigue incluyendo todos los árboles y las etapas precedentes; diez describe únicamente esta capa.

Frente a seis niveles terminales libres, esto añade cuatro intensidades activas; no reduce por sí solo el número total de parámetros. La justificación es controlar la magnitud de ajustes existentes con una penalización explícita, no presentar más parámetros como una simplificación de toda la arquitectura.

La robustez es una hipótesis por comprobar. Regularizar puede reducir variabilidad, pero también empeorar un nivel correcto o amortiguar una señal útil. No hay garantía sobre el privado ni una meta de score deducible de este diseño.

## Qué evidencia respalda el cambio

| Evidencia conservada | Consecuencia para el diseño |
|---|---|
| R1 y F3c con el mismo operador: al separar el factor global histórico, los totales de sus entradas difieren aproximadamente 0,1071 %. | Conservar la base y estudiar las capas finales antes de cambiar otra vez de familia. La cercanía de totales no demuestra rankings equivalentes. |
| F3c completo: el bloque propio pierde 0,003649 D² en autos nuevos en la vista pública temporal. | Permitir atenuación de ese bloque, aplicando la misma regla a las seis celdas, sin escoger autos a posteriori. |
| Niveles públicos frente a niveles de entrenamiento: edificios nuevos pierde 0,041475 D² local. | Comparar calibración aprendida sin nuevos multiplicadores públicos; el punto por celda no identifica el nivel correcto de 2025. |
| NB-CRED300 gana globalmente, pero edificios nuevos pierde 0,009828 D². | No reutilizar como prior el nivel agregado del ramo ni modificar K para rescatar ese ensayo. |
| 94,27 % de la exposición de edificios nuevos de 2025 está en períodos largos; hubo ocho positivos largos en 2023 y tres en 2024. | El ajuste no resuelve por sí solo falta de soporte. Las bandas de duración y la cola deben poder impedir el reemplazo. |
| F3c público pierde su mejora al retirar los 37 grupos más favorables. | Mantener el control de concentración y toda la cola, sin borrar siniestros para mejorar el criterio. |

Fuentes locales: [comparación con tronco común](R1_F3C_TRONCO_COMUN_20261027.md), [contracción fallida](NB_NIVEL_CREDIBILIDAD_20261027.md), [soporte de edificios nuevos](NB_EDIFICIOS_PRIOR_DIAGNOSTICO_20261027.md), [validación completa](F3C_VALIDACION_COMPLETA_20261027.md) y [cierre técnico](F3C_REVISION_FINAL_20261028.md). Las cifras predictivas pertenecen a 2024 adaptativo. Los 158.980 registros de negocio nuevo son aproximadamente el 76 % de las 209.063 filas de entrega; esa proporción no describe la composición desconocida del privado ni su exposición.

## Modelo concreto

Para cada período i y celda c = ramo × nuevo/renovación:

`mu_i = b_i * exp(a_c + gamma_c * z_i)`, con `0 <= gamma_c <= 1`.

`b_i` es la prima observada de la mezcla completa A1/T2b después de F2 y su forma común, antes de niveles terminales y bloque propio. Conserva exposición, unidades y el puente q en el orden verificado. `z_i` es el logaritmo de la razón entre esa misma base con bloque propio y sin él, antes de nivel terminal. Para producir último, se aplica la calibración a la prima última y no se añade un segundo desarrollo.

El candidato conserva A1 N0/F1 con tres semillas, T2b/C1 y mezcla 50/50. Retira de la aplicación los multiplicadores globales, las formas NB y los niveles terminales públicos de la vista pública; parte de la vista temporal sin esos bloques que ya existe. F2, la forma de renovación y la construcción del bloque propio siguen siendo antecedentes heredados. En particular, la forma A_M1 usada para aprender ese bloque permanece congelada: no se afirma que el diseño esté libre de selección pública histórica.

Los niveles `a_c` y las intensidades `gamma_c` se aprenden conjuntamente. No se aplica primero un nuevo nivel y después un factor elegido por el score. `a=gamma=0` reproduce b. La restricción sobre gamma evita invertir o amplificar el bloque propio. No limita el precio total entre los dos precios antiguos, porque el nivel a también cambia.

La pérdida usa T0 por período y devianza Tweedie de potencia 1,5, sin doble ponderación por exposición. La exposición ya está incorporada en b. Se mantienen todos los siniestros y reservas. La documentación oficial de [GLM de scikit-learn](https://scikit-learn.org/stable/modules/linear_model.html#generalized-linear-models) respalda el uso de enlace logarítmico y penalización L2; su [ejemplo de seguros](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html) distingue coste total, tasa y exposición. La calibración concreta y sus restricciones son una propuesta de este proyecto, no una recomendación de esas fuentes.

Se propone minimizar `mean(d_1.5(y,mu))/(2*s) + lambda/2 * sum(D_j * beta_j^2)`, donde `s=mean(sqrt(b))`. Para la columna j de su celda c, `D_j=mean_c(sqrt(b)*X_j^2)/(6*s)`. Los centros de penalización son cero. Cada celda recibe peso de penalización comparable; una celda pequeña no reduce automáticamente su penalización en proporción a sus filas. Esto no equivale a credibilidad actuarial estimada ni garantiza menor contracción cuando hay más siniestros.

La normalización hace la pérdida y la penalización invariantes a un cambio común de moneda en y y b. Evita confundir unidades con regularización, como podía ocurrir al comparar priors de distinta escala. Columnas idénticamente cero se fijan a cero; una celda sin soporte de entrenamiento no adquiere un coeficiente mediante información retenida.

## Diferencia frente a caminos ya probados

P82/P85 y P88 probaron GLM sobre campos de riesgo y priors diferentes; no acreditan este calibrador de baja dimensión sobre el tronco completo F3c. Tampoco se reutilizan sus resultados como aprobación. P105 ya mostró que seleccionar pesos de mezcla no solucionaba el problema; aquí la mezcla queda fija. P102 resolvió cotización por fila, pero no mejoró suficientemente la predicción; aquí no se combina silenciosamente ese cambio con la receta nueva. El calibrador es por fila dados b y z, aunque el tronco heredado conserva dependencia del lote. No se presenta una prueba local del calibrador como invariancia de todo el sistema.

P111 documentó que número y coste por evento no se transportan igual entre años. Por eso no se propone ahora otro multiplicador fijo de frecuencia, un clima futuro o una nueva curva de reservas para forzar el nivel. Estas limitaciones se evalúan y se comunican; no desaparecen por penalizar coeficientes.

## Cómo se probaría sin elegir otra vez por el público

1. Construir entradas por ámbito del tronco completo. La calibración recibe predicciones y señales fuera de muestra; cada retenido debe quedar excluido de F2, factores, niveles, completitud y preprocesamiento que dependan de sus costes. Los OOF 2023 antiguos con curva compartida no se declararán automáticamente adecuados. Se reutilizarán solo objetos cuyo linaje cumpla el ámbito exacto.
2. Elegir un único lambda común entre 1, 0,1 y 0,01 por los cinco folds internos guardados de 2023. Minimizar devianza agregada por período, con empate relativo de 1e-10 favorable a mayor penalización. No seleccionar otro valor por ramo, por 2024 o por score público. Dentro de cada entrenamiento interno, las señales que entrenan el calibrador también necesitan exclusión por grupo: el conjunto de ámbitos objetivo tiene diez pares de folds excluidos, cinco folds individuales y el ámbito completo, dieciséis conjuntos únicos.
3. Registrar el código, entradas, costes y controles reales antes de ajustar. Son quince ajustes candidatos internos y uno final de calibración, más controles separados. El presupuesto de productores upstream y C0 depende de la conciliación de esos dieciséis ámbitos; todavía no está acreditado ni se supone cero. No se inicia una corrida con un presupuesto inventado o usando curvas de otro ámbito.
4. Evaluar una sola receta cerrada de 2023 a 2024. Contrastes nuevos: candidato frente a `trainlevel_full` para aislar la calibración y frente a `public_full` para valorar la sustitución práctica. Preservar también R1, B00 y las ablaciones como antecedentes, sin una nueva búsqueda de pesos. Los dos contrastes amplían de 18 a 20 la familia condicional de esta secuencia; no corrigen toda la búsqueda histórica.
5. Mantener margen global de 0,0005 respaldado por la banda de familia, piso de −0,001 por ramo y seis celdas, negocio nuevo no negativo y límite inferior 95 % por encima del piso, al menos cuatro cortes guardados positivos y mejora no negativa tras retirar los grupos más favorables. Los cortes son partes del mismo año, no cinco backtests independientes. Deben pasar ambos contrastes para proponer reemplazo; una ganancia aislada no basta.
6. Aplicar los escenarios existentes de reservas y reportes, mostrar cola y duración, y comprobar el aprendizaje afectado por cambios de entrenamiento antes de producción. Los escenarios de precios fijos por sí solos no certifican estabilidad de reentrenamiento. Una regresión en un segmento o falta de soporte impide presentar la receta como mejora robusta, aunque suba el global.

2024 sigue abierto como desarrollo adaptativo. No disponemos de otro año emergente etiquetado que convierta esta comparación en confirmación independiente. Nuevos folds de las mismas etiquetas no solucionan esa carencia. Tampoco se supone que los maestros y estados de siniestros reproduzcan su disponibilidad a la fecha de cotización.

## Alcance de esta entrega

Esta unidad documenta la propuesta y comprueba su matemática con datos sintéticos, sin optimizar un modelo. El recibo distingue gradiente, Hessiano, convexidad, escala y atenuación de las pruebas aún pendientes del optimizador y del flujo real. No genera nuevos scores, predicciones 2025 o envíos. El siguiente trabajo concreto es conciliar los dieciséis ámbitos del tronco completo y preparar el optimizador restringido con controles sintéticos antes de cualquier ajuste real.

El análisis sintético terminó: 17 comprobaciones pasan en 460 filas artificiales. El gradiente coincide con diferencias finitas con error máximo 3,42e-11 y el Hessiano con 1,94e-12. El menor autovalor del Hessiano activo es positivo, 0,0008803, en ese ejemplo. La prueba general para entradas fijas usa `H = X' diag((sqrt(mu)+y/sqrt(mu))/(2*N*s)) X + lambda*diag(D)`, positiva definida en las columnas activas con lambda positivo. Esto establece convexidad de la capa con entradas fijas, no de todo el procedimiento que aprende esas entradas. No se ejecutó un optimizador ni se validaron sus condiciones KKT.

También pasan la fórmula escalar independiente, precios positivos, identidad con coeficientes cero, cambio común de moneda y envolvente de atenuación. La consistencia por fila corresponde solo a la capa dados b y z. Recibo: `privado/semana2/F3c_regularizado_20261028/synthetic_math.json`; código: `herramientas/analizar_diseno_F3c_regularizado.py`. Cero ajustes sintéticos o reales, nuevos scores, predicciones del concurso y envíos.

El criterio de éxito es una mejora defendible que conserve los pisos, no llegar a una posición pública prefijada. Se siguen las prácticas locales IAA de propósito, límites, dependencias y seguimiento; este trabajo de Codex no constituye revisión profesional independiente ni aprobación humana.
