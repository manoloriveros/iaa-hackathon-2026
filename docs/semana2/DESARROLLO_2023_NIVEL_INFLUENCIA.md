# Nivel agregado e influencia: tercera prueba de 2023

Codex, 23 de octubre de 2026. Igualar el nivel de ajuste al de B00 acerca los totales fuera de muestra a la referencia, pero por sí solo no resuelve la concentración de la ventaja. Las dos contracciones fijas del 50 % mantienen una diferencia positiva después de los retiros de grupos preinscritos. B08 obtiene el mejor punto de esta exploración. Se conserva B00, no hay promoción y 2024 sigue cerrado.

El [plan v3](../../registro/semana2_desarrollo2023_plan_v3.json) y COD-S2-20261023-012 preceden al cálculo de factores y predicciones. El resultado está en COD-S2-20261023-013 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice activo](../../registro/semana2_desarrollo2023_actual.json) identifica esta prueba y las tandas anteriores.

## Diagnóstico que motivó la prueba

La [revisión previa](../../privado/semana2/desarrollo2023/revision_nivel_20261023T181136Z_82668c37/report.json) usa únicamente OOF2023 guardado. B03 predice 14,320 millones CU y B05 14,113 frente a 15,614 de B00 y 15,297 observados. Quedan 8,29 % y 9,61 % por debajo del nivel de B00. El déficit frente al observado se concentra en edificios: 0,718 millones CU en B03 y 0,695 en B05.

Los 31 componentes más favorables representan 140,49 % de la ventaja neta de B03 y 130,02 % de la de B05, porque compensan pérdidas en otros componentes. Concentran 12,31 %/9,48 % del coste observado y 0,12 %/0,13 % de la exposición. Basta retirar 14 grupos favorables de B03 o 18 de B05 para invertir su ventaja; diecinueve componentes pertenecen a ambas listas.

No se interpretan como errores de datos o permiso para recortar la cola. Los retiros mantienen los modelos fijos: miden influencia en la evaluación, no la influencia de reentrenar sin esos grupos. Se conservaron todos los periodos en ajuste, factores y objetivo completo.

## Recetas y frontera de información

Para cada padre, ramo y fold se calcula, solo en las filas de ajuste de ese fold:

`s = sum(e × tasa_B00) / sum(e × tasa_padre)`

`tasa_nueva = (1−w) × tasa_B00 + w × s × tasa_padre`

e es la exposición efectiva C0. Los modelos base y la tasa constante B00 ya estaban guardados, con los mismos ámbitos de ajuste. B06 usa B03 y w=1; B07 usa B05 y w=1. B08 y B09 repiten esas fórmulas con w=0,5, fijado antes de probar. Los treinta factores se comparten entre las variantes de peso uno y medio.

La fórmula iguala exactamente el total predicho de ajuste con el de B00 por ramo/fold y conserva el orden de las tasas anuales dentro de ese ámbito. La contracción reduce a la mitad la desviación de la tasa anclada respecto de B00. No minimiza de nuevo la pérdida Tweedie de la escala ni garantiza reducir a la mitad la contribución a la devianza.

No se usa el total observado de validación, sus características o su distribución para aprender s o w. La comprobación reconstruyó cada factor con las filas de ajuste sin columnas de respuesta. Las predicciones usadas para normalizar son de los modelos dentro de su ajuste: no es calibración independiente o interna fuera de muestra. B00 también depende de los siniestros de ajuste y puede ser sensible a eventos severos. No se forzó A/E a uno ni igualdad de los totales OOF.

| Padre y ramo | Factor mínimo entre folds | Máximo |
| --- | ---: | ---: |
| W2-B03, motor | 1.0450 | 1.0741 |
| W2-B03, buildings | 1.1085 | 1.1464 |
| W2-B03, contents | 1.0541 | 1.0825 |
| W2-B05, motor | 1.0782 | 1.1077 |
| W2-B05, buildings | 1.0984 | 1.1473 |
| W2-B05, contents | 1.0767 | 1.1324 |

Se reutilizaron 45 archivos distintos de modelos base (treinta padres y quince B00). La referencia se usa para ambos padres por fold. Se aprendieron treinta factores y se guardaron sesenta adaptadores, con las funciones de ajuste de estimadores base bloqueadas y cero intentos de llamarlas. No se ajustaron otros GLM o árboles. Son 50.094 periodos, 30.869 componentes y los cinco folds de 2023, con F0, T0, C0 y seis comparadores anteriores exactamente iguales. La prueba y agregación inicial tardaron 19.8 segundos en CPU con dos hilos; revisión y documentación son trabajo adicional.

## Resultado fuera de muestra

El observado es 15,297 millones CU. A/E significa observado dividido por predicho. El D² es global sobre todas las filas, no promedio por ramo. Se evalúa T0 mediante C0; no es un score de Kaggle o una comprobación del último real.

| Receta | D² OOF2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| W2-B00: Referencia | 0.06858 | 15.614 | 0.980 |
| W2-B03: GLM, padre | 0.08672 | 14.320 | 1.068 |
| W2-B05: Boosting simple, padre | 0.07986 | 14.113 | 1.084 |
| W2-B06: B03 con nivel B00 | 0.08904 | 15.584 | 0.982 |
| W2-B07: B05 con nivel B00 | 0.08174 | 15.622 | 0.979 |
| W2-B08: 50 % B00 + 50 % B06 | 0.09318 | 15.599 | 0.981 |
| W2-B09: 50 % B00 + 50 % B07 | 0.08077 | 15.618 | 0.979 |

Los totales nuevos quedan cerca de los de B00 sin haberlos impuesto en OOF. Por eso sus A/E cercanos a 0,98 también heredan el nivel de referencia; no demuestran calibración futura o suficiencia de reservas. B08 alcanza 0,09318 frente a 0,08672 de su padre B03, y B09 0,08077 frente a 0,07986 de B05. No se escogió un peso alternativo después de verlos.

## Influencia con dos listas de grupos

Se repite el retiro de los 31 grupos más favorables de cada receta. Además se retiran las listas congeladas de su padre, idénticas para comparar padre, ancla y contracción. Se recalcula el nulo en el conjunto retenido. Los retiros solo son diagnósticos de evaluación y no afectan el score principal.

| Frente a B00 | Diferencia D² completa | Intervalo exploratorio 95 % | Tras retirar sus propios 31 favorables | Tras retirar los 31 del padre |
| --- | ---: | --- | ---: | ---: |
| W2-B06 | 0.02046 | [0.00138, 0.03877] | -0.00817 | -0.00809 |
| W2-B07 | 0.01316 | [0.00073, 0.02346] | -0.00430 | -0.00414 |
| W2-B08 | 0.02460 | [0.01468, 0.03497] | 0.00581 | 0.00587 |
| W2-B09 | 0.01219 | [0.00581, 0.01791] | 0.00119 | 0.00121 |

B06/B07 siguen cambiando de signo con ambas listas. Mover el nivel no resuelve ese diagnóstico. B08/B09 conservan signo positivo bajo los dos retiros fijados; es evidencia de menor dependencia en esta evaluación, no ausencia de influencia o de sensibilidad al reentrenamiento. La estructura B03/B05 y el ancla siguen aprendidas del mismo año.

Se conservaron 2.000 sorteos pareados comunes y se reconstruyó el nulo en cada réplica. Los cuatro intervalos nuevos frente a B00 tienen límites inferiores positivos, pero siguen siendo exploratorios, condicionales y sin corrección por la búsqueda de las tres tandas o por las 45 parejas de diez recetas. No equivalen a la confirmación simultánea de 2024. Los [recibos y réplicas](../../privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/diagnostics/pairs.json) mantienen todas las comparaciones; no solo el mejor punto.

## Ramos y negocio

| Ramo | B00 | B08 | B09 |
| --- | ---: | ---: | ---: |
| Autos | -0.00581 | 0.02100 | -0.00058 |
| Edificios | 0.02085 | 0.03355 | 0.02895 |
| Contenidos | 0.02893 | 0.07915 | 0.06969 |

| Segmento | B00 | B08 | B09 |
| --- | ---: | ---: | ---: |
| Nuevo negocio | 0.04783 | 0.07297 | 0.04065 |
| Renovación | 0.07062 | 0.09516 | 0.08530 |

B08 mejora el punto de los tres ramos y ambos segmentos frente a B00 en esta muestra. B09 mantiene deterioro en nuevo negocio pese a mejorar el global. Los nulos de cada subconjunto son propios y no se suman sus D². Nuevo negocio es una marca contractual, no la futura evaluación temporal de clientes nuevos.

## Sensibilidad y controles

Estas diferencias frente a B00 mantienen los adaptadores y sus factores base fijos. Cambian solo respuesta y exposición de los escenarios guardados. No reanclan o reentrenan, y no cumplen por sí solas las salvaguardas completas de confirmación.

| Escenario | B06−B00 | B07−B00 | B08−B00 | B09−B00 |
| --- | ---: | ---: | ---: | ---: |
| reserve075 | 0.02067 | 0.01357 | 0.02445 | 0.01232 |
| reserve125 | 0.02025 | 0.01276 | 0.02474 | 0.01206 |
| late_cost05 | 0.02037 | 0.01307 | 0.02467 | 0.01219 |
| late_cost10 | 0.02028 | 0.01299 | 0.02475 | 0.01219 |

Pasaron 21 casos focales del ancla, contracción, guardas y bloqueo de fit. El comprobador separado pasó 2,023 controles (los recuentos se solapan): reconstruyó factores con suma independiente, igualdad de ajuste, contracción y orden, parámetros padres inalterados, seis comparadores exactos, replay con fit bloqueado, pérdidas, intervalos, listas de grupos y sensibilidades. [Recibo](../../privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/verifications/20261023T181823Z_b26f9296.json). Es revisión propia de Codex, no revisión profesional independiente.

## Decisión

Se conserva B00 y se mantienen B01–B09. B08 queda como resultado prometedor de desarrollo, sin promoción o lista final congelada. Las [advertencias](../../privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/assessment.json) mantienen la reutilización del ajuste para normalizar, búsqueda adaptativa, influencia residual de B06/B07, segmento adverso de B09 y supuestos del último. Los bloqueos de recetas anteriores conservan su autoría; estos IDs nuevos no los cierran.

2024 permanece cerrado por instrucción expresa del participante. El cierre técnico del vínculo del selector y el seguimiento GOV005 publicados por otros encargos tienen evidencia y responsables propios; aquí no se actualiza su estado ni se infiere permiso de abrir. No hay precios, ajuste o métricas de 2024 o test, apertura de ledger, envíos o entrenamiento remoto. Los [supuestos de T0 a último](VARIABLES_Y_ULTIMO.md) y la revisión humana pendiente mantienen su alcance.

## Reproducir la comprobación

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_v3_semana2.py' --run 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3'
```

El comando comprueba los modelos guardados y reconstruye estadísticas con fit bloqueado. El [manifiesto de la prueba](../../privado/semana2/desarrollo2023/dev3_20261023T181613Z_24c943a3/manifest.json) conserva su corte; la revisión y registro posteriores tienen anexos propios. No se necesita reentrenar para revisar esta prueba.


## Corte posterior: estabilidad y negocio

La [cuarta prueba](DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md) revisa B08/B09 y contrasta factores por negocio y un estrés de reentrenamiento. El [snapshot del índice de esta tercera tanda](../../registro/semana2_desarrollo2023_v3_snapshot.json) conserva exactamente su registro. Este documento y sus cifras mantienen su corte original.
