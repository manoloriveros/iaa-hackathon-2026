Codex. Resultado de 027: [mezcla de C0 por peril y negocio](../../Repositorio_IAA2026/docs/semana2/MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md), [decisiones](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/decision_journal.json). Solo 2023, mismos folds/T0 y modelos estándar; B00 y el catálogo principal intactos, 2024 cerrado.

MIXF cambia por negocio solo las frecuencias Poisson por peril; MIXFS cambia también las medias Gamma positivas ponderadas. Las curvas qN/qC y los pesos de truncamiento se conservan por peril del propio ajuste. Solo se usan los pesos normalizados, nunca un multiplicador extra de frecuencia×severidad en el precio. El control pooled reproduce el C0 original; no presupone que cualquier agregado de las nuevas medias por negocio deba devolverlo.

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

Los tres puntos MIXF son peores que sus bases y los tres MIXFS peores que MIXF. En B14, el nominal condicionado mueve +0,0166%/+0,1016%, sin acreditar mejora. Son los mismos periodos de 2023 por tasa bajo coste completo, no precios de 2025/test o etiquetas últimas. En autos nuevos, el D² de B14 pasa de −0,010045 a −0,010191/−0,011551. Los pequeños cambios favorables de hogar nuevo se conservan como puntos descriptivos, sin intervalos de superioridad por celda. La mezcla difiere por negocio, pero eso no valida una sustitución de C0 o precio.

Hay cinco celdas de ajuste con frecuencia cero: todas son incendio en edificios nuevos, una por fold, reflejo de una sola ausencia observada en 2023. No son cinco hallazgos independientes ni ausencia futura de riesgo. No se fabricó su severidad. El informe conserva conteos, tamaño efectivo y concentración para las otras 145 celdas positivas. En algunas celdas de hogar nuevo, un siniestro aporta hasta el 91,8% o el 97,2% del coste ponderado de esa celda. No se eliminan costes o se escoge una intensidad de contracción después de ver scores.

Una mezcla distinta puede afectar poco a C0 si las curvas por peril son parecidas. Se verificó por fila la cota |delta q| <= TV(pesos)×rango(qC_peril) en los 100.188 registros variante/periodo de 2023. Es una propiedad de mezclas convexas, no validación de la composición futura o del último. El total pequeño tampoco significa inmaterialidad por fila: en autos nuevos, MIXFS reduce la exposición efectiva hasta un 4,47%; esto no equivale al mismo cambio del precio.

Se guardaron doce contrastes nuevos y 2.000 sorteos comunes, con influencia propia de 31 grupos; cifras completas en el informe. Los intervalos son exploratorios condicionados en los ajustes guardados y no propagan el reajuste de pesos de primera etapa. No se repiten las pruebas de cola y reservas o sus remuestreos. Sin promoción, retiro, equivalencia o lista final.

Se completaron 30 GLM y 90 constantes de precio nuevos; contador propio de 165 ajustes y 285 constantes. Aparte hay 150 constantes Poisson de mezcla y 145 medias Gamma ponderadas; cero curvas de reporte o auxiliares de credibilidad nuevos. Pasaron 1.570 controles separados, 47 adversos y 32 comprobaciones adicionales, con solapamiento. Se reconstruyeron pesos y óptimos Poisson/Gamma, normalización, C0, gradientes, exp(X beta), ámbitos, segmentos y doce remuestreos por multiplicidades; fit bloqueado. Sin reintento o cambio de receta. Revisión técnica propia, no profesional independiente.

Decisión: conservar el C0 pooled, MIXF/MIXFS como sensibilidades y todas las alternativas. Permanecen las condiciones de escasez, curvas compartidas, dependencia coste/reporte, cobertura individual, cola/reservas y disponibilidad temporal. Siguiente unidad: balance de mecanismos identificados/condicionados y revisión de soporte temporal/celdas antes de complejizar, con receta previa. B00 intacto, 2024/test cerrados y ledger ausente; sin remoto, envíos, publicación externa, nuevos chats o delegación. La programación y otras automatizaciones se preservan.
