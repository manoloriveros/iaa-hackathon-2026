# Soporte de calendario y reporte en 2023

Codex, corte UTC 2026-10-24T01:10:52.055248+00:00. Diagnóstico registrado antes del cálculo, sin modelos, curvas nuevas, puntuaciones o remuestreo. Continúa la revisión de la mezcla C0, con B00 y todas las alternativas conservadas. Los cinco folds son los ya guardados.

## Qué aporta el calendario

Los 50.094 periodos corresponden al año de póliza 2023, con 30.869 componentes. En este corte sus días cubiertos y siniestros observados están todos en el calendario 2023. Al valorar a 31 de diciembre de 2024, cada día cubierto tiene al menos 366 días de maduración. Esto explica que las curvas congeladas cuyo último reporte está dentro de 365 días den completitud uno bajo su supuesto de cola. No demuestra que la cola real termine allí.

La exposición diaria respeta los extremos inclusivos. Cada periodo reparte su exposición nominal entre sus días cubiertos; no se equipara la exposición redondeada a un número entero de años. Se reconstruyó la masa con expansión diaria y suma por fold retenido, por otro método que las diferencias de intervalos del productor.

| Ramo | Distancia total entre calendarios por negocio | Exposición de renovación con ≥540 días | Exposición nueva con ≥540 días |
| --- | ---: | ---: | ---: |
| Autos | 25.04–25.52% | 52.33–52.33% | 26.85–27.33% |
| Edificios | 25.23–25.83% | 52.33–52.33% | 26.54–27.19% |
| Contenidos | 25.09–25.49% | 52.33–52.33% | 26.90–27.33% |

Los rangos recorren los cinco ajustes, con muestras solapadas. La distancia total es la mitad de la suma de diferencias absolutas entre masas normalizadas por edad; no es un test. El calendario de nuevo negocio dispone de menos seguimiento largo. Una diferencia entre completitudes de negocio puede existir aun usando exactamente la misma curva por peril, por esa composición de días. Esto no atribuye causalmente el deterioro de los modelos al calendario.

## La cola observada no identifica la que falta

| Ramo | Negocio | Siniestros únicos observados | Demora máxima, días | Reportes >365 días | Reportes >540 días |
| --- | --- | ---: | ---: | ---: | ---: |
| Edificios | Renovación | 479 | 422 | 2 | 0 |
| Edificios | Nuevo | 40 | 160 | 0 | 0 |
| Contenidos | Renovación | 454 | 520 | 2 | 0 |
| Contenidos | Nuevo | 37 | 44 | 0 | 0 |
| Autos | Renovación | 3242 | 653 | 28 | 5 |
| Autos | Nuevo | 315 | 516 | 3 | 0 |

Esta tabla deduplica las vistas de ajuste: cada siniestro aparece en cuatro, no en cinco muestras independientes. Los máximos y proporciones describen reclamaciones conocidas al corte. No son probabilidades incondicionales de reporte ni estimaciones de siniestros aún desconocidos. La ausencia de cola observada en una celda no establece ausencia de riesgo futuro.

En lesiones corporales de autos, el extremo observado de las curvas agrupadas cambia entre 609 y 653 días según fold. Solo entre 4,27% y 11,19% de la exposición de autos nuevos tiene suficiente maduración para llegar al extremo correspondiente. El conjunto de riesgo inverso de ese negocio contiene de uno a cinco siniestros y no aporta eventos en ese extremo. Esto limita una curva separada; no prueba que la curva agrupada sea correcta. Riesgo inverso significa reclamaciones observadas con demora ≤d y seguimiento ≥d. No equivale al número de siniestros futuros potenciales ni a exposición asegurada.

Los anexos conservan todas las celdas por ramo, peril, negocio y fold, incluyendo las vacías, los puntos de 0, 30, 90, 180, 365, 540 y 730 días y el extremo congelado de cada curva. Se distinguen exposición suficientemente madura, reclamaciones con seguimiento, riesgo inverso, eventos exactos y costes observados después del punto. No se introduce un umbral de muestra suficiente ni se selecciona una nueva cola.

## Decisión y verificación

No se ajustará una curva de negocio o se añadirá complejidad de precios como consecuencia de este diagnóstico. La escasez y la censura siguen abiertas. El siguiente trabajo comprueba soporte técnico por coberturas antes de aceptar denominadores por peril; tampoco se interpretará una mezcla poblacional como cobertura individual. Un ensayo numérico futuro necesitará hipótesis y criterio previos y respetar las limitaciones de información.

Pasaron 331 controles del flujo descriptivo, 3543 verificaciones y adversos nuevos, y 2413 conciliaciones de lectura, con solapamiento. La segunda cuenta suma cada día por separado y reconstruye los conjuntos de riesgo con Python; las curvas se consultan por búsqueda bisect. Se probó el comando real con año sintético 2024 y se conservó su fallo esperado antes de salidas, sin usar datos reales de ese año. Los errores de redondeo máximos de fracciones alrededor de uno quedan en readout.json sin alterar cifras originales; son del orden de 1e-14. Revisión técnica propia, no profesional independiente. Cero ajustes, scores o bootstrap nuevos; contadores de precio 165/285 sin cambio.

## Exposición accidental y ámbito

Un inventario de encabezados del foro mostró un asunto de CLA-S2-20261024-006 con métricas de 2024. La guarda anterior fue insuficiente y no puede afirmarse ceguera completa tras esa lectura. Se registró antes del diagnóstico sin repetir cifras. No se abrió cuerpo, acta, predicción o ledger. El lector nuevo solo expone autor, ID y fecha y pasó una prueba con marcadores secretos en título y cuerpo, además del flujo real. Las cifras externas no se usan para decisiones de 2023. Esta unidad sigue el diagnóstico de datos ya previsto, sin entrenamiento, puntuación o selección adaptativa. La autorización anunciada en otro chat permanece sin verificar o invalidar; no abre otra tanda en esta tarea.

## Evidencia

Plan: [registro congelado](../../../registro/semana2_soporte_calendario2023_plan_v1.json). Índice: [soporte actual](../../../registro/semana2_soporte_calendario2023_actual.json). Productor: [auditor de calendario](../../../src/semana2/auditar_soporte_calendario2023.py). Comprobador: [otra cuenta y adversos](../../../herramientas/verificar_soporte_calendario2023_semana2.py). Lector: [índice del foro sin asuntos](../../../herramientas/leer_foro_semana2_seguro.py). Balance: [corte parcial de la noche](BALANCE_NOCTURNO_PARCIAL_20261024.md).

Detalle restringido, recibos y hashes: `Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/soporte_20261024T010555Z_c4428b52`. Fuentes de la mezcla anterior en [su informe](MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md). Prácticas priorizadas: consideraciones profesionales §3.1 y §3.3, gobernanza §2.8 y documentación §§2–3; el enlace documental no certifica cumplimiento ni revisión humana.


## Revisión posterior de coberturas

La [siguiente unidad](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md) conserva este diagnóstico y revisa denominadores sin entrenar. Rechaza la máscara dura de daño accidental de hogar por costes positivos fuera, sin borrar siniestros; el supuesto de cobertura individual continúa abierto.
