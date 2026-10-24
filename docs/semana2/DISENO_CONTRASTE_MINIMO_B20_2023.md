# Contraste mínimo propuesto para B20: pendiente de riesgo en edificios

Se fija un único contraste estándar de calibración en log-tasa para comprobar si las relatividades de edificios están demasiado separadas. Se enfrenta una pendiente libre entre cero y uno con un control de pendiente uno; ambos permiten corregir el nivel. Añade un parámetro frente al control. El mecanismo todavía es una hipótesis y el soporte actual falla: el diseño queda condicionado y no se entrena.

## Evidencia que motiva la hipótesis

Las bandas B20 de edificios, fijadas en ajuste, tienen A/E 1,966 / 1,563 / 0,856 / 1,198 / 0,714. Las bajas infrapredicen en el agregado y la más alta sobrepredice; es compatible con un contraste de riesgo demasiado amplio. Las bandas intermedias no son monótonas. La banda 1 cambia de A/E 0,342 a 3,457 entre folds, comparte componentes y concentra costes. Esto no establece una pendiente verdadera menor que uno ni exige recalibrar.

El diagnóstico posterior de incendio/AD también queda incorporado: los dos incendios fijados están fuera del ajuste 3, donde AD cambia de signo, y un solo incendio representa 35,8% de la ganancia neta global B20/B19. La composición de perils y los costes grandes son explicaciones rivales. No se deriva una interacción AD×incendio, una máscara contractual ni la retirada de siniestros. El diseño no intenta identificar una causa de AD.

La calibración se refiere al coste observado T0 bajo el puente C0. No separa por sí sola un fallo de la prima de un fallo de maduración, reservas o mezcla. Tampoco identifica coste último. Los recibos ya existentes y la exposición previa a un título externo se declaran; este diseño posterior a los diagnósticos es exploratorio, aunque se registre antes de un eventual ensayo nuevo.

## Un cambio y un control que separa nivel de dispersión

Sea r la tasa anual B20 y e su exposición efectiva C0. Solo en las filas de calibración de ajuste se calcula m = Σ(e log r)/Σe y r* = exp(m). Para z = log r − m se propone:

    h(b) = e × r* × exp(b z)
    μ(a,b) = exp(a) × h(b)

| Brazo | Parámetros de calibración | Función |
| --- | --- | --- |
| B20 original | a=0, b=1 | Ancla sin cambios, salvaguarda descriptiva |
| L, control de nivel | a libre, b=1 | Permite que un desplazamiento de nivel explique la mejora |
| S, compresión | a libre, 0≤b≤1 | Comprueba una sola compresión continua del contraste de riesgo |

La comparación primaria es S−L. El efecto adicional es una pendiente, no cinco factores por banda. El intercepto se estima por separado en ambos brazos bajo el mismo objetivo, porque fijarlo a un valor común impondría niveles distintos de forma arbitraria al cambiar la pendiente. Se conserva una salvaguarda S−B20 original.

Se minimiza la suma no ponderada de devianzas de unidades observadas d₁,₅(T0, μ). En escala de tasas, la identidad exige pesos √e sobre d₁,₅(T0/e, tasa), no pesos e. Para un b fijo, el intercepto se perfila exactamente:

    a(b) = log[Σ T0/√h(b) ÷ Σ √h(b)]

Esto satisface el score del intercepto y no fuerza ΣT0/Σμ=1. La pendiente se estima dentro de [0,1], sin penalización, búsqueda de alpha o rejilla de recetas. b=1 expresa ausencia de compresión; b=0 borra toda relatividad de edificios y se rechaza como solución degenerada. No se calcula a, b o m en esta tarea.

Se conservan los siete efectos B20, alpha=1, transformaciones y codificación. El mismo cambio se aplicaría a todos los edificios, incluidos nuevos y renovación. Autos y contenidos mantienen exactamente sus predicciones B20. No hay pendientes por negocio, factores por bandas, isotónica, interacciones, enrutamiento, cortes nuevos, recortes del target o exclusión de siniestros.

## Soporte exigido antes de ajustar

Estos son límites prudenciales elegidos para este diseño después de ver los diagnósticos de 2023. No proceden de Kaggle o la IAA, no se estimaron mediante potencia y no convierten el análisis en confirmatorio. El tope de una quinta parte del coste limita el dominio de un componente; el equivalente de diez grupos describe dispersión de coste, sin ser un tamaño muestral inferencial. Los mínimos de positivos impiden sostener la dirección con muy pocos componentes; tampoco garantizan precisión.

| Ámbito | Regla conjunta |
| --- | --- |
| Cada cola agrupada, bandas originales 1 y 5 de edificios | ≥50 componentes positivos, mayor componente ≤20% del coste y equivalente de concentración ≥10 |
| Cada cola por fold | ≥10 componentes positivos, mayor componente ≤50% y equivalente de concentración ≥3 |
| Cada ámbito futuro de calibración interna | ≥100 componentes positivos totales; ambas colas con las reglas agrupadas; log-tasa P80−P20≥log(1,25); tasas y C0 estrictamente positivos y finitos |
| Integridad | Componentes completos, partición original, solo 2023, sin duplicados o fuga de ancestros; las cinco vistas deben pasar |

La comprobación barata previa usa las bandas OOF ya fijadas, sin cambiar sus cortes para obtener soporte. Las comprobaciones de calibración interna, si alguna vez procedieran, usarían cortes hechos solo con tasas de ajuste de su ámbito. Ante cualquier fallo o dato desconocido no se ajusta ni se elige una subpoblación favorable.

| Evidencia ya guardada | Frente a la regla | Estado |
| --- | --- | --- |
| Edificios banda 1: 69 grupos positivos, mayor 31,65%, equivalente 6,09 | Supera el tope 20% y queda bajo 10 equivalentes | Falla |
| Edificios banda 5: 124 positivos, mayor 19,02%, equivalente 14,16 | Cumple esas tres reglas agrupadas | Cumple solo esta celda |
| Edificios banda 1, fold más concentrado: mayor 91,82% | Supera el tope 50% por fold | Falla |
| Resto de soporte por fold, ámbitos internos y rango de log-tasa | No evaluados en este diseño | Pendientes |

La puerta actual está cerrada. No se presenta el soporte de la banda 5 como soporte global. Su apertura exigiría evidencia nueva pertinente o una revisión justificada y versionada que conserve este fallo; no se relajan umbrales automáticamente, combinan bandas después del resultado o borran componentes para pasar. El resultado de hoy es el diseño y su inadmisibilidad actual para entrenamiento.

Para evitar ambigüedad, en cada celda Cg es la suma de T0 de las filas de ese componente dentro de la celda. Se cuenta como positivo si Cg>0. La mayor participación es max(Cg)/ΣCg y el equivalente de concentración es (ΣCg)²/ΣCg². Un componente que aparece en varias bandas se cuenta dentro de cada una; los recuentos no se suman como observaciones independientes. Una celda vacía o sin coste positivo no satisface soporte. Las reglas de cada cola se aplican por separado, nunca al promedio de ambas.

## Cómo evitar fuga si el contraste llegara a ser admisible

Se conservan los cinco folds por componentes de 2023. Para evaluar Fk, todo lo aprendido usa exclusivamente los otros cuatro folds. Dentro de ellos, para producir la tasa de calibración de Fj, el B20 interno y todas sus dependencias se ajustan sin Fk ni Fj. Esto incluye medianas, escalas, OHE, curvas de reporte y mezcla de frecuencias/severidades de C0. Cada etiqueta de calibración se empareja con su tasa y C0 internos, ambos fuera de muestra respecto a esa etiqueta.

Con las predicciones internas de los cuatro folds se fijarían m, a y b. Solo después se aplicarían al B20 exterior guardado y al C0 exterior correspondiente, que ya excluyen Fk. No se puede entrenar un calibrador sobre toda la OOF actual y puntuarlo sobre las mismas filas. Tampoco basta usar el modelo OOF guardado de Fj: normalmente vio Fk, por lo que contaminaría la calibración del fold exterior. El C0 exterior no sustituye al C0 interno que debe excluir también Fj.

Hay 20 evaluaciones internas ordenadas, pero solo diez conjuntos de tres folds de ajuste: excluir Fk/Fj equivale a excluir Fj/Fk. Una caché con receta y fuentes idénticas permite diez B20 internos de edificios y diez flujos C0, con predicciones separadas para cada fold excluido. Se reutilizarían cinco modelos B20 exteriores, sin volver a entrenarlos.

Los productores históricos que recorren todos los años no se invocan. Hace falta un adaptador de ámbito 2023, funciones puras, manifiesto completo de ancestros y pruebas que alteren etiquetas exteriores sin cambiar ningún objeto aprendido. Su implementación y coste detallado aún no están congelados y también impiden la ejecución. No se crean datos ni resultados de confirmación.

Los modelos internos usan tres quintos de los folds y el exterior usa cuatro quintos. Transferir una pendiente entre ambos tamaños de ajuste puede cambiar su comportamiento; no se presupone equivalencia. La evaluación exterior conjunta y las salvaguardas deberían detectar deterioro. Seguiría siendo una comprobación exploratoria en los mismos datos elegidos para plantear la hipótesis.

## Criterios de aceptación del eventual ensayo local

Todas las condiciones se exigen juntas; un fallo o una condición desconocida conserva B20 original y todas las alternativas. Los márgenes siguientes son reglas de elegibilidad exploratoria, no pruebas de significación o promoción. El margen útil global de 0,0005 se toma de la política común; su aplicación local no sustituye la confirmación de esa política.

| Dimensión | Regla previa |
| --- | --- |
| Soporte y técnica | Todas las puertas anteriores; fuentes y ámbitos exactos; predicciones positivas/finita; objetivo y gradiente cotejados, KKT proyectado normalizado ≤10⁻⁶; sin reinicio del optimizador tras fallo |
| Ganancia primaria | ΔD² S−L global, sin ponderar y con nulo común, ≥0,0005 |
| Ancla original | ΔD² S−B20 global ≥0 |
| Estabilidad descriptiva | S−L no negativo en ≥4/5 folds; ningún fold por debajo de −0,001. b estrictamente entre 0 y 1 en ≥4/5 vistas; ninguna solución b=0 |
| Mecanismo observado | G_L=log(A/E banda1)−log(A/E banda5)>0 y 0≤G_S≤0,8 G_L, sobre las mismas membresías B20; reduce al menos 20% de la separación residual sin invertirla |
| Segmentos | ΔD² S−B20 ≥−0,001 en ramos, nuevo/renovación y edificios nuevo/renovación; autos/contenidos exactamente iguales |
| Influencia | Para S−L y S−B20 por separado, retirar de evaluación max(5,ceil(0,001G)) grupos más favorables, con tope G−1; ΔD² restante ≥0. No elimina datos ni reentrena |
| Nivel | Cambio absoluto del total nominal 2023 de edificios frente a B20 ≤5%; no se calcula 2025 |

La reducción del 20% de G exige que una ganancia de pérdida acompañe el mecanismo propuesto. Es una decisión de materialidad del diseño, no una estimación de cuánto debe mejorar. Los folds comparten ajuste y no son cinco experimentos independientes. No se calculan nuevos intervalos ni bootstrap de predicciones fijas para declarar certeza. Una eventual ganancia mantendría la selección adaptativa y la incertidumbre de reestimar la primera etapa y el modelo.

Un resultado favorable solo justificaría revisión posterior. B00 conserva la referencia; no hay roster, B21, promoción, retiro, otra tanda de 2024 ni cambio del protocolo común. Las salvaguardas de escenarios, nueva población, advertencias y acta de selección siguen pendientes de su procedimiento autorizado. Un resultado adverso se publica íntegro y no desencadena otro alpha, semilla, corte o familia.

## Coste, límites y decisiones

Ahora: cero parámetros estimados, ajustes, constantes, inferencias, recetas de catálogo o remuestreos. El contador propio permanece en 195 ajustes de precio y 285 constantes. El presupuesto hipotético, si en otra actuación se superaran las puertas y se autorizara entrenar, sería diez B20 internos de edificios, cinco pendientes de calibración y cinco constantes de nivel, además de diez flujos C0. Sus curvas y estimaciones auxiliares deben enumerarse separadamente antes de poder arrancar. No se ocultan dentro de los diez ajustes de precio. CPU local, dos hilos; sin remoto, escenarios adicionales, bootstrap completo o envíos.

Se registran las decisiones de mantener el mecanismo como hipótesis; elegir edificios por la evidencia previa; separar pendiente de nivel; usar un solo parámetro adicional; exigir soporte y detenerse porque falla; anidar C0 y transformaciones; fijar aceptación conjunta; conservar la política común; y no entrenar ni abrir otros años. La disponibilidad de último, reservas/reaperturas, reporte, capital y semántica contractual sigue condicionando el uso. Revisión de Codex, sin revisión humana o profesional independiente implícita.

2024, test, actas, scores, SEL01 y ledger permanecen cerrados en este trabajo. La exposición previa a un título ajeno queda declarada sin reproducir sus cifras, usarlas o afirmar ceguera completa. No se concilian aquí el estado o autorizaciones de una tanda externa.

[Plan estructurado](../../registro/semana2_b20_contraste_minimo_diseno_v1.json), [índice y recibos](../../registro/semana2_b20_contraste_minimo_actual.json), [síntesis anterior](SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md), [bandas](CALIBRACION_B20_BANDAS_AJUSTE_2023.md) e [incendio/AD](INCENDIO_Y_AD_B20_2023.md). Fuentes congeladas, decisiones y comprobación de estructura del diseño quedan en privado. Documentación IAA §3 y Gobernanza §2.8 orientan el registro y la distinción de revisión propia; los umbrales prudenciales no se atribuyen a esas referencias.

La verificación documental final pasa 174 comprobaciones, incluidas pruebas estructurales adversas del ámbito y de ancestros, fronteras de soporte y la identidad algebraica del objetivo en ejemplos fijos. No se estima ningún parámetro. El primer intento se detuvo por una diferencia de nombre de campo entre ficha y recibo; se conserva el comprobador inicial y su fallo. La reparación solo traduce el nombre, sin cambiar fuentes, diseño o umbrales. Que el contrato pase esta revisión no abre su puerta de soporte.
