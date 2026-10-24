# Selección de modelos de semana 2: reglas vigentes

Codex, 23 de octubre de 2026. El participante pide aplicar el protocolo y fijar criterios antes de comparar modelos. Esta versión adopta reglas operativas derivadas de la [revisión S22→S30](../REVISION_SELECCION_S22_S30.md). La propuesta anterior se conserva en `privado/semana2/seleccion/registro_v1_20261023/`. La [política v1](../../registro/semana2_politica_seleccion_v1.json) fija los números; el [índice activo](../../registro/semana2_seleccion_actual.json) conserva su SHA y el del evaluador. Son tolerancias prudenciales del proyecto, no requisitos de Kaggle ni valores óptimos estimados. Al registrarlas no se consultaron scores de candidatos ni se abrió confirmación de 2024.

## Referencia y criterio común

La primera referencia designada es W2-B00, una tasa emergente sencilla por ramo y exposición que debe pasar los controles técnicos y del objetivo. Designarla no la declara entrenada. Cada promoción requiere el acta del evaluador común con referencia, candidato, diferencia en la métrica principal, incertidumbre, pruebas de población nueva, escenarios y motivo de decisión. Las variantes investigadas o enviadas no pasan a ser principales por ese hecho. Una excepción operativa conserva el filtro predictivo; no hay un filtro por asistente.

La métrica primaria es D² Tweedie 1,5 completo, global y sin pesos sobre las 59.202 filas temporales de 2024, con ajuste de precio solo en 2023. Las predicciones de último pasan al T0 observado mediante el vínculo de observación fijado y estimado solo en el ámbito de entrenamiento; el mismo vínculo se usa para ambos modelos. El score mide incurrido neto observado, no el último oculto. No se recorta la cola ni se reajusta nivel con etiquetas de 2024. Cuerpo, frecuencia-severidad, totales y A/E son diagnósticos. No se promedian D² por ramo o segmento para obtener el global.

La regla de desempate conserva la referencia si no hay evidencia suficiente para reemplazarla. No se usa el público como desempate. «No acreditada» no significa «equivalente»: una declaración de equivalencia exigiría un margen y análisis específicos. La alternativa técnicamente válida permanece registrada; reproducir otra receta no permite retirarla.

Una advertencia alta o crítica bloquea mientras no esté resuelta con evidencia y SHA. Reconocerla o aceptarla como limitación no satisface el bloqueo. Una advertencia condicional exige cumplir su condición y aportar evidencia. Falta de gravedad, clasificación o evidencia requerida impide promover. Las informativas se conservan en el acta. Los controles de disponibilidad, fuga, objetivo, linaje e integridad son obligatorios.

## Desarrollo y confirmación

Se mantienen los folds de cliente/dirección compartidos entre ramos, ya persistidos. El ajuste de transformaciones, nivel, hiperparámetros y pesos se hace dentro del desarrollo de 2023 con predicciones fuera de muestra. No se incorporan etiquetas de 2024, de ningún mercado, al ajuste que pretenda simular 2024.

Se permite una sola tanda de confirmación de 2024: referencia y hasta tres aspirantes. Se congelan recetas, artefactos y prioridades antes de abrir scores. Se aportan todos los pares. El evaluador recorre el orden fijado previamente y solo reemplaza a quien sea referencia en ese momento si el aspirante demuestra mejora clara frente a ella. Ganar a una referencia anterior no basta para reemplazar a la vigente. Los no incluidos en la lista corta se conservan con motivo, sin declararlos inferiores. Los datos ya se inspeccionaron para conciliación: no es un conjunto completamente ciego ni un backtest histórico plenamente prospectivo.

No se permiten otra tanda, recetas, aspirantes, semillas o márgenes bajo v1 después de abrir. Una modificación futura explícita del participante conservaría la versión, los resultados y el reconocimiento de que 2024 ya fue consultado; no recuperaría una confirmación intacta. El evaluador no ofrece reinicio ni opción de ignorar advertencias.

La prueba de población nueva evalúa 2024 con grupos que quedaron fuera del ajuste de 2023. Esos resultados son complementarios del contraste temporal, no observaciones independientes: comparten filas de 2024. Se informa por separado nuevo cliente y renovación y se analiza el cambio de composición hacia el test 2025.

Se registra cada candidato consultado, incluidos los no enviados y variantes intermedias. Se cuenta cada apertura del bloque de confirmación y cada consulta pública. La incertidumbre de una pareja fija no corrige por sí sola la búsqueda que la eligió. Si se evalúa un procedimiento de búsqueda, la selección debe repetirse dentro de los folds internos, sin usar resultados del fold externo.

## Parámetros fijados antes de comparar candidatos

| Parámetro | Regla vigente | Consecuencia |
| --- | --- | --- |
| Mejora mínima útil, δ2 | 0,0005 de D²; el límite inferior primario debe ser estrictamente mayor | Un mejor punto con intervalo insuficiente no promueve |
| Incertidumbre primaria | 10.000 remuestreos pareados de componentes cliente-dirección; semilla 2026102301; mismos sorteos entre pares | Cambiar método, semilla o cuantil bloquea |
| Comparaciones múltiples | Familia fija de seis pares; Bonferroni alfa familiar 0,05; intervalo bilateral 99,1666667 % | No se relaja por incluir menos modelos |
| Población nueva | Diferencia nominal ≥ 0 y límite inferior diagnóstico 95 % ≥ −0,001 | Conservar referencia si falla |
| Reservas ×0,75/1,25 y masa tardía de diseño 5 %/10 % en lesiones/hundimiento | Diferencia temporal global ≥ 0 en los cuatro escenarios | Un escenario adverso impide promover |
| Segmentos: tres ramos, nuevo cliente y renovación | Ninguna diferencia < −0,001 | Deterioro material impide promover |
| Influencia | Tras retirar max(5, ceil(0,001×n_grupos)) grupos más favorables, diferencia ≥ 0; conservar al menos un grupo | Dependencia de pocos grupos impide promover |
| Nivel 2025 por ramo | Un cambio absoluto > 5 % exige atribución y validación en desarrollo con evidencia | Un salto inexplicado bloquea |
| Confirmación | Una tanda; referencia más hasta tres aspirantes; recetas y orden congelados | No se admiten reaperturas o candidatos añadidos |
| Empate o falta de evidencia | Mantener referencia y conservar alternativa | No declarar equivalencia ni borrar alternativas |

El margen 0,0005 representa 0,05 % de la desviación nula completa, equivalente a cincuenta unidades de un score con cinco decimales. Se fija ahora como tolerancia prudencial sin esperar scores de candidatos, en lugar de estimarlo adaptativamente después. No se ha medido potencia en emerging. El mínimo 0,0002 de semana 1 y el ruido de semillas no se importan. Si el intervalo cruza 0,0005 se conserva la referencia, aunque el punto parezca mejor.

En cada remuestreo se recalcula la desviación nula completa, común a los dos modelos, sobre los grupos sorteados. Los cuantiles son 0,0041666667 y 0,9958333333 para cada par. La asignación sigue [Bonferroni según NIST](https://itl.nist.gov/div898/handbook/prc/section4/prc473.htm); los intervalos bootstrap son aproximados y condicionales, sin garantía de cobertura exacta ni corrección de toda la búsqueda previa. El intervalo de población nueva es diagnóstico, sin otra afirmación simultánea del 95 %. Los límites por segmento y estrés son vetos de riesgo puntuales, no exigencias de significación en cada subconjunto.

Si el tamaño del mercado emergente impide distinguir mejoras pequeñas, se conserva la incertidumbre en el acta y se restringen las variantes; no se redefine el umbral después de ver cuál conviene. El conjunto de hipótesis explorado debe ser compatible con el presupuesto de confirmación.

## Control de mecanismos y del público

Toda variante de tendencia, forma, transferencia o reservas debe compararse primero manteniendo fija el ancla de nivel de la referencia. Otra variante puede cambiar el nivel explícitamente. Si una modificación cambia qué componente fija el total, el acta lo muestra como un cambio adicional. Evitar que un umbral implícito cambie de forma discontinua el ancla, como ocurrió con s17.

El público puede detectar errores o generar hipótesis, pero no es un conjunto de confirmación después de usarlo para ajustar. Cada sonda debe tener propósito y efecto esperado escritos antes de enviarla. La adopción de una calibración necesita respaldo fuera de ese mismo marcador y un tratamiento de ruido que represente la parte no vista; no usar como sustituto la variabilidad de semillas. No se copian los factores de D100/D101, los exponentes D102 ni el factor 0,90 del mejor privado retrospectivo a emerging.

Los componentes de reservas y el puente T0→último mantienen sus decisiones propias. La incertidumbre no se resuelve normalizando totales ni porque una regla de nivel sea reproducible.

## Acta antes de seleccionar el archivo

La tabla de decisión final incluye la referencia vigente, todos los candidatos todavía plausibles y las variantes excluidas, con su motivo. Para cada candidato: código y SHA, objetivo, score de desarrollo y confirmación, incertidumbre y límites por búsqueda, población nueva, sensibilidad de nivel/reservas, integridad y reproducción. El público figura en una columna separada y se explica si intervino en la construcción.

Mantener las alternativas técnicamente válidas hasta esta acta; un respaldo predictivo no desaparece porque la receta principal se reproduzca. Si se desea una mezcla, sus pesos se fijan en desarrollo y se evalúa como candidato congelado; no se ensambla después por intuición con scores de confirmación.

Se documenta la recomendación y su incertidumbre antes de la decisión humana. Después se comprueba el archivo exacto, la marca en Kaggle y la concordancia con informe y video. La revisión técnica y el número de comprobaciones aprobadas no se presentan como superioridad predictiva.

La selección debe explicar por qué cambiar es preferible a conservar la referencia. Haber probado más arquitecturas, reproducido más archivos o alcanzado un mejor público no basta por sí solo.

## Límites y fundamento

La segunda semana tiene menos datos, años disponibles limitados, maduración desigual y ausencia de snapshots históricos completos. No se promete una prueba independiente perfecta ni se transforma el privado de semana 1 en un criterio nuevo optimizado para ganar retrospectivamente.

La separación entre desarrollo y evaluación del procedimiento sigue [Cawley y Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) y la [documentación de scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). Las prácticas IAA de validación, control de cambios y ficha del modelo se aplican como guía educativa. Esta implementación no entrena, publica ni envía nada y no modifica las particiones ni S41.

## Puerta de selección y evidencia

Desde la carpeta del repositorio:

```text
python herramientas/seleccionar_semana2.py estado
python herramientas/seleccionar_semana2.py congelar --manifest <manifiesto.json>
python herramientas/seleccionar_semana2.py abrir
python herramientas/seleccionar_semana2.py decidir --evidence <evidencia.json>
```

`congelar` verifica hashes del objetivo, particiones, variables, vínculo de observación, productor de métricas, recetas, predicciones de ambas vistas y recibos técnicos. `abrir` consume la única tanda antes de consultar scores2024. `decidir` exige los hashes de ambos recibos y comprueba pares, método, advertencias y límites. Un fallo conserva la referencia; ninguna alternativa se elimina. El ledger común está en `privado/semana2/seleccion/confirmacion_v1`, aún sin crear al registrar las reglas.

Hay plantillas de [manifiesto](plantillas_seleccion/manifest.json), [alternativas](plantillas_seleccion/alternatives.json) y [evidencia](plantillas_seleccion/evidence.json). Sus controles falsos, scores nulos y rutas de relleno impiden usarlas como evidencia real. El recibo de cada par debe hacer revisables los ámbitos, scores, remuestreo, influencia, nivel y escenarios. El productor de métricas queda fijado por SHA, igual que las predicciones.

El evaluador consume recibos: **no calcula scores o bootstrap ni certifica por sí solo el cálculo del productor**. Ese cálculo y su cotejo deberán implementarse/verificarse antes de abrir la tanda. Sí aplica las consecuencias de los datos recibidos y rechaza evidencia incompleta, alteraciones de hashes y cambios posteriores de decisión. No es una protección contra la edición manual de código o registros por un operador con acceso al workspace.

Salida 0: operación correcta; 2: bloqueo o entrada inválida; 3: acta válida sin promoción. Releer la misma decisión es idempotente; otra evidencia no la sobrescribe. No hay autorización de entrenamiento o envío por ejecutar esta puerta.

Pasaron 25 casos sintéticos: ganancia incierta, advertencia reconocida pero no resuelta, deterioro en población nueva/reservas, concentración de influencia, salto de nivel inexplicado, hash alterado, pares omitidos, cuantil modificado y reapertura, entre otros. Se conserva el intento inicial fallido por permisos de temporales; los fixtures finales se guardan en privado y no comparan modelos reales. El índice activo verifica política y ejecutable con SHA.
