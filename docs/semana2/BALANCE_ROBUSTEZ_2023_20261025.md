# Balance de robustez del modelo, 25 de octubre de 2026

El mejor score público propio observado pasó de **0,13310 a 0,14331**, diferencia +0,01021 (+7,67% respecto al score inicial). Es una mejora procesada por Kaggle; no demuestra por sí sola significancia estadística ni el salto grande solicitado. El trabajo deja dos alternativas que pasan los controles exploratorios de 2023, los resultados adversos de catorce ciclos y un paquete privado que reproduce exactamente ambos CSV. No se declara alcanzado el objetivo de una mejora pública grande.

Codex, 2026-10-25T13:29:35.359969+00:00. Solo cohortes de precios de 2023 para ajustes y validación; cotizaciones de 2025 para las entregas autorizadas, después de congelar recetas y completar ajustes finales. 2024 sigue cerrado para cohortes, precios, scores, ledger, actas y SEL01. La exposición ajena previa de un asunto ya declarada impide afirmar ceguera completa; no se usa en estas decisiones. No se cambian automatizaciones, otros chats, autorizaciones ajenas o selección final manual.

## Resultado que sí se sostiene en estas comprobaciones

R36 tiene D² OOF2023 **0,11053677**, frente a B20 **0,08938179** y B00 **0,06858169** sobre los mismos 50.094 periodos. Delta frente a B20 +0,02115499; intervalo bootstrap de grupos exploratorio [0,01032137; 0,03163706]. Mejora en cinco de cinco folds y en los seis segmentos ramo/negocio. Al retirar del diagnóstico los 31 grupos de contribución más favorable sigue +0,00410578. No se retiraron grupos o siniestros del ajuste. R37, con menor peso transferido, también pasa: D² 0,10228050, delta +0,01289871 y +0,00337692 después de ese diagnóstico.

Estas cribas son exploratorias tras búsqueda adaptativa. El remuestreo no corrige todas las decisiones previas, ni toda la incertidumbre del profesor fuente o la identificación de último. No hay revisión actuarial profesional independiente ni aprobación humana técnica inventada. No se promociona una lista final por el score de 2023.

## Recetas y evidencia conservadas

| Ciclo | Modelo | D² OOF2023 | Referencia | Delta | Folds positivos | Delta sin 31 grupos | Cribas |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| 1 | W2-COD-R21 | 0.094757 | W2-B20 | +0.005376 | 4/5 | -0.011729 | No pasa |
| 1 | W2-COD-R22 | 0.081425 | W2-B20 | -0.007956 | 1/5 | -0.034115 | No pasa |
| 2 | W2-COD-R23 | 0.086496 | W2-B20 | -0.002885 | 2/5 | -0.017530 | No pasa |
| 2 | W2-COD-R24 | 0.082269 | W2-B20 | -0.007113 | 1/5 | -0.026210 | No pasa |
| 3 | W2-COD-R25 | 0.091788 | W2-B20 | +0.002407 | 4/5 | -0.002934 | No pasa |
| 3 | W2-COD-R26 | 0.094384 | W2-B20 | +0.005003 | 3/5 | -0.008148 | No pasa |
| 4 | W2-COD-R27 | 0.092456 | W2-B20 | +0.003075 | 5/5 | -0.000574 | No pasa |
| 4 | W2-COD-R28 | 0.095477 | W2-B20 | +0.006095 | 5/5 | -0.002964 | No pasa |
| 5 | W2-COD-R29 | 0.094192 | W2-B20 | +0.004810 | 3/5 | -0.006896 | No pasa |
| 5 | W2-COD-R30 | 0.078276 | W2-B20 | -0.011106 | 2/5 | -0.024116 | No pasa |
| 6 | W2-COD-R31 | 0.103820 | W2-B20 | +0.014438 | 5/5 | -0.004163 | No pasa |
| 6 | W2-COD-R32 | 0.115078 | W2-B20 | +0.025696 | 5/5 | -0.002584 | No pasa |
| 7 | W2-COD-R35 | 0.116431 | W2-B20 | +0.027049 | 5/5 | -0.001888 | No pasa |
| 7 | W2-COD-R36 | 0.110537 | W2-B20 | +0.021155 | 5/5 | +0.004106 | Pasa |
| 7 | W2-COD-R37 | 0.102280 | W2-B20 | +0.012899 | 5/5 | +0.003377 | Pasa |
| 8 | W2-COD-R38 | 0.105704 | W2-COD-R36 | -0.004832 | 2/5 | -0.016594 | No pasa |
| 8 | W2-COD-R39 | 0.111447 | W2-COD-R36 | +0.000910 | 4/5 | -0.005234 | No pasa |
| 9 | W2-COD-R40 | 0.113712 | W2-COD-R36 | +0.003175 | 4/5 | -0.004414 | No pasa |
| 9 | W2-COD-R41 | 0.112807 | W2-COD-R36 | +0.002270 | 4/5 | -0.004426 | No pasa |
| 10 | W2-COD-R42 | 0.101368 | W2-COD-R36 | -0.009169 | 0/5 | -0.015414 | No pasa |
| 10 | W2-COD-R43 | 0.108842 | W2-COD-R36 | -0.001694 | 2/5 | -0.006035 | No pasa |
| 10 | W2-COD-R44 | 0.110724 | W2-COD-R36 | +0.000188 | 2/5 | -0.002221 | No pasa |
| 11 | W2-COD-R45 | 0.106621 | W2-COD-R36 | -0.003915 | 0/5 | -0.010585 | No pasa |
| 11 | W2-COD-R46 | 0.099586 | W2-COD-R36 | -0.010951 | 1/5 | -0.020295 | No pasa |
| 12 | W2-COD-R47 | 0.101894 | W2-COD-R36 | -0.008643 | 1/5 | -0.015151 | No pasa |
| 12 | W2-COD-R48 | 0.109693 | W2-COD-R36 | -0.000843 | 3/5 | -0.005852 | No pasa |
| 13 | W2-COD-R49 | 0.101177 | W2-COD-R36 | -0.009359 | 0/5 | -0.017312 | No pasa |
| 13 | W2-COD-R50 | 0.110974 | W2-COD-R36 | +0.000437 | 3/5 | -0.004960 | No pasa |
| 14 | W2-COD-R51 | 0.099645 | W2-COD-R36 | -0.010892 | 0/5 | -0.016431 | No pasa |
| 14 | W2-COD-R52 | 0.109081 | W2-COD-R36 | -0.001456 | 1/5 | -0.003055 | No pasa |
| 14 | W2-COD-R53 | 0.115048 | W2-COD-R36 | +0.004511 | 4/5 | -0.006538 | No pasa |

El comparador pasó de B20 a R36 en el ciclo 8; los deltas de filas distintas no se suman. Se exigió delta >=0,005, límite inferior exploratorio >0,0005, >=4 folds favorables, daño por ramo/negocio <=0,0005 de la desviación nula completa y delta >=0,0005 al retirar 31 grupos favorables solo del diagnóstico. Los ciclos 11/12 añadieron un veto fuente separado; el 9 un veto por sexo y necesidad incremental. Las reglas no se relajaron para aceptar un resultado. Bootstrap de 2.000 grupos, semilla 2026102501 y cuantiles 0,0041666666667/0,9958333333333, con nulo recalculado.

La arquitectura conservada aprende forma física en desarrollado2023 (626.355 periodos, incurrido neto observado/exposición nominal) con GLM y corrección pequeña fija de 200 árboles. En emergente2023 aprende solo intercepto, negocio y región dentro de cada ajuste exterior. La fuente no aporta soporte emergente y su incurrido no es último identificado. Los profesores de edificios excluyen construcción por la codificación W/w sin material confirmado. Capitales/C0 y el resto del objetivo se conservaron.

R36 mezcla en raíz cuadrada 50% de ese precio y 50% de B20; R37 usa 25%/75%. Ambos pesos se fijaron antes de sus scores locales y públicos. No se afinaron con el leaderboard. R37 mantiene su prioridad conservadora preinscrita; R36 se identifica aquí como mejor público propio observado, sin cambiar selección final manual.

## Qué se descartó y por qué

Los GLM ampliados, splines, frecuencia/severidad, árboles emergentes y transferencia conjunta no mostraron la ganancia estable exigida. El desglose por peril mantuvo los costes presentes con banderas de cobertura apagadas, sin suprimirlos ni inventar exposición asegurada. La descomposición no superó materialmente a R36.

Las declaraciones previas en el emergente aportaron un incremento pequeño sin robustez suficiente; añadir sexo empeoró frente a la declaración sola. El diccionario permite M/F en emergente y define prior_claims_5y antes de incorporarse, pero no certifica versiones históricas del maestro. No se adoptaron estos perfiles.

La ampliación física por densidad, edad en hogar y banderas del inmueble no mejoró al incumbente. El primer enlace se detuvo porque esas columnas ya estaban en las entradas estrictas: se comprobó igualdad exacta de los 15 archivos y la continuación conservó tres ajustes ya válidos. No hubo sobrescritura silenciosa ni tres ajustes repetidos.

La mayor capacidad fuente empeoró en el control separado por cliente/domicilio y en el emergente. El bloque de perfiles comunes tampoco ayudó. Su extracción detectó 23.628 clientes fuente ausentes del maestro (25.571 periodos de motor); se conservaron filas, costes y exposición con perfiles ausentes, sin inventar identidades. Los primeros extractores fallidos quedaron preservados. Los valores libres de ocupación desconocidos no se reagruparon después de observar resultados.

Los efectos contractuales de adquisición, ya admitidos por F0, no superaron el umbral. La nueva pendiente de riesgo del ciclo 14 tampoco: R51 0,099645, R52 0,109081, R53 natural sin mezcla 0,115048; ninguno pasa el conjunto de controles. Potencias estimadas por fold: W2-COD-R51/motor: 0.757–0.914; W2-COD-R51/buildings: 0.858–1.137; W2-COD-R51/contents: 1.014–1.356; W2-COD-R52/motor: 0.765–0.885; W2-COD-R52/buildings: 0.728–1.004; W2-COD-R52/contents: 1.019–1.309. Las 16 variables categóricas físicas transferidas, excluida construcción, tienen los mismos dominios de 2023 en ambos mercados; el chequeo nuevo no encontró un error de categorías que justifique otra tanda.

El total propio es **684 intentos de ajuste de precios**, de los que 476 son adicionales desde G4 (473 en investigación y tres finales), incluyendo un intento numérico rechazado antes del ajuste aceptado. Son 31 variantes evaluadas en catorce ciclos, no 31 confirmaciones independientes. Los fits sintéticos y 445 constantes cerradas se contabilizan aparte. Nuevos C0 de esta investigación: cero. Los 29 candidatos que no pasan siguen guardados. El reporte recuperado del ciclo 1 conserva la limitación del digest de sorteos no archivado y la serialización fallida; no se repitieron sus ajustes o remuestreo para ocultarla.

## Entrega comprobada

| Variante | Envío propio Kaggle | Estado | Público |
| --- | ---: | --- | ---: |
| G4 original | 57628123 | COMPLETE | 0,13310 |
| R37 | 57629584 | COMPLETE | 0,13956 |
| R36 | 57629589 | COMPLETE | 0,14331 |

Competición: [IAA AI Assisted Hackathon 2026 Part 2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2). Solo se subieron predicciones propias autorizadas; código, modelos y datos siguen privados. Las dos variantes se cargaron antes de consultar cualquiera de sus nuevos scores. Se consumieron dos cupos; la última consulta autenticada dejó cuatro disponibles, sin afirmar que sea una cuota actualizada en este balance. No se enviaron las tandas adversas para perseguir el público.

Ambos CSV contienen 209.063 IDs únicos en orden oficial, columnas row_id/prediction y valores positivos finitos. SHA R36 b4ca8806b01bd5dfaab597774c5a4d1229e910a7638db0d1bc8bbff890d9baa2; R37 0f4ab80ec5b44e08cd457dae15e85ac0ce2910df132499be71051deb54b59cb6. Kaggle cotejó referencia, mensaje, nombre y tamaño; no devolvió SHA remoto. B00, B20 y el CSV G4 original permanecen conservados.

Paquete local: `Hackaton/Repositorio_IAA2026/privado/semana2/robustez2023/paquete_20261025_v1/modelo_propio_robusto2023_privado.zip`, SHA 0e447aa56cc23a128e6da3331827e14d188cf337f1da4a1fc39ce1c73757fad3, 15372147 bytes. Se verificó cada archivo comprimido por SHA y se extrajo en otra carpeta. El proceso separado `replay.py` leyó únicamente los modelos/cotizaciones/baseline incluidos, bloqueó fits y optimización, y reprodujo exactamente las 209.063 predicciones de cada CSV. Es validación de la nueva portabilidad del paquete; no repite entrenamiento, no vuelve a evaluar 2023 y no certifica rendimiento nuevo. ZIP y CSV están excluidos de Git. Recibo: `Hackaton/Repositorio_IAA2026/privado/semana2/robustez2023/paquete_20261025_v1/extracted_replay/package_replay_receipt.json`.

## Límites y punto de continuación

La mejora pública es real pero modesta. Faltan prueba independiente de una ganancia pública grande, soporte emergente adicional legítimo y mejor identificación temporal de perfiles/último. Las carencias G1/G2 del contraste original no se resuelven con un score mejor: el mecanismo sigue plausible, el soporte retenido original falla en cinco de diez celdas y el soporte interno no queda establecido. No se presenta la transferencia como sustituto de ese soporte.

No hay una ejecución pendiente de estos catorce ciclos. El siguiente trabajo útil requiere una evidencia nueva de 2023 o una corrección material de origen que cambie una hipótesis, con procedencia y disponibilidad revisadas; no repetir estas recetas sobre fuentes iguales. La confirmación independiente sigue pendiente dentro del ámbito que pueda autorizarse, sin abrir 2024 en este trabajo. No se relajan los controles ni se inventa que el objetivo grande ya se alcanzó. El informe anterior de siete ciclos queda como corte histórico, con sus decisiones y recibos originales.

Índice de continuidad: `Hackaton/Repositorio_IAA2026/registro/semana2_robustez2023_actual.json`. Resultados, fuentes SHA, configuraciones, modelos, OOF, replays, adversos y autoría real se conservan en privado/semana2/robustez2023.
