# Cierre de F3c-R: conservar F3c

Elegí conservar F3c después de revisar la comparación con la alternativa regularizada. Guardo el experimento completo y sus resultados adversos para explicar esa decisión, junto con la autoría técnica de sus comprobaciones.

Autor: Codex. Cierre del 28 de octubre de 2026, hora de Bogotá.

Terminaron los 26 ámbitos fuente, la calibración y la comparación registrada. F3c-R no aporta evidencia suficiente para sustituir F3c pensando en el privado. Conservo ambos modelos, R1 y B00, sin producir otro CSV ni gastar un envío.

## Qué encontró la comparación

La evaluación usa 59.202 periodos de 2024, con entrenamiento destino en 2023. El control del mismo tronco permite separar el efecto de la regularización de los cambios en el procesamiento. La segunda referencia es la reproducción temporal de F3c original. Estos resultados son locales; 2024 es desarrollo adaptativo, no una confirmación independiente ni una estimación del puesto privado.

| Resultado | F3c-R | Control del mismo tronco | F3c original |
|---|---:|---:|---:|
| D² global | 0,126662 | 0,126718 | 0,126806 |
| D² de negocio nuevo | 0,114614 | 0,108412 | 0,109150 |
| D² de renovaciones | 0,123638 | 0,124591 | 0,124586 |

El agregado de negocio nuevo mejora, pero la mejora no se distribuye de forma estable. Frente a F3c, motor pierde 0,003270 de D² y contenidos pierde 0,001518. En contenidos nuevos la caída es 0,014658. Edificios nuevos mejora frente al F3c original, pero empeora 0,004702 frente al control del mismo tronco: no corresponde atribuir toda aquella mejora a la regularización.

La diferencia global frente a F3c es −0,000144. Su intervalo simultáneo condicional de familia 20 va de −0,006320 a +0,005783. El intervalo del 95 % de negocio nuevo también incluye pérdidas (−0,010009 a +0,022905). Por tanto, la mejora puntual de ese agregado no justifica reemplazar el modelo actual.

Los 10.000 remuestreos por grupos, los 50 escenarios con precios fijos y las cinco omisiones completas de folds quedaron guardados. Al retirar los 37 grupos más favorables, la diferencia global frente a F3c cae a −0,003676. Ninguna de las cinco omisiones satisface conjuntamente las condiciones de estabilidad frente a F3c original. Conservo todos los resultados; no se elige el mejor fold ni un segmento ganador después de observarlos.

## Qué quedó comprobado

Se conciliaron 468 pares de ajustes fuente: 33 reutilizados y 435 nuevos. Los nuevos requieren 870 ajustes nativos terminados. El diario contiene 872 intentos, incluidos dos interrumpidos que se conservan separados. Se cotejaron los hashes de modelos, salidas guardadas, recibos y curvas, sin repetir sus estimaciones. Hay 52 preparaciones RKM primarias y otras 52 de controles adversos; son paquetes, no un recuento de modelos de precio.

El destino completó 16 ajustes primarios del calibrador y 18 de verificación. Pasaron los ocho controles del flujo real, incluidas las cinco ramas con etiquetas retenidas alteradas, el replay sin aprendizaje y el optimizador alternativo. La penalización común elegida con 2023 fue 0,1. El cotejo final verificó el sello de artefactos, las métricas mediante la fórmula explícita de devianza, los cuantiles ya guardados, los criterios, el informe y el recibo del foro. El CSV original de F3c conserva su SHA-256.

El primer intento del verificador de cierre no encontró el lector Parquet instalado en la caché del proyecto. Se conservó ese fallo y se corrigió únicamente su ruta de importación. No se cambió el entrenamiento, el evaluador congelado, las predicciones ni los umbrales.

## Decisión y límites

Se cierra esta comparación y se conserva F3c como modelo actual. F3c-R queda como alternativa documentada, sin promoción. Las comprobaciones son trabajo propio de IA, no revisión profesional independiente. Pasar los controles de ejecución no equivale a superar los criterios predictivos.

Siguen presentes el soporte escaso de edificios nuevos con exposición larga, las normalizaciones por lote, la historia adaptativa de A_M1 y la incertidumbre de cola y reservas. Una investigación posterior tendría que explicar el deterioro en renovaciones, contenidos nuevos y cola antes de registrar otra receta. Este resultado no autoriza escoger mezclas o segmentos a posteriori ni garantiza el desempeño privado de F3c.

El [informe de resultados](../archivo/semana2/F3C_REGULARIZADO_RESULTADOS_20261028.md) conserva las tablas completas y los criterios originales. El índice `registro/semana2_F3c_regularizado_actual.json` enlaza los recibos de `privado/semana2/F3c_regularizado_20261028/closeout/`, fuera de Git. El código de cotejo es `herramientas/verificar_cierre_F3c_regularizado.py`; no ajusta modelos ni genera inferencias.
