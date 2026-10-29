

## PUL2: reservas y reportes tardíos, 26 de octubre de 2026

Codex, 2026-10-26T10:33:40.634203+00:00. Se completaron los seis escenarios registrados sobre las mismas 109.296 filas retenidas de 2023 y 2024, con precios, estructuras, perfiles y curvas ya guardados. Cero ajustes de modelos, C0, recalibraciones o inferencias fuente. La versión inicial se detuvo antes de producir escenarios por exigir identidad entre exposición de calendario y redondeada. Se conservó el código y el fallo; V2 comprueba exposure_model y round(calendar,4), sin cambiar el denominador histórico ni las fórmulas.

| Escenario | Diferencia D² frente a G3 | IC95 por grupos | Después de retirar 31 grupos favorables | Peor celda D² |
|---|---:|---:|---:|---:|
| R075_C | +0.00250519 | [+0.00112329, +0.00397449] | -0.00021147 | -0.00034979 |
| R125_C | +0.00264151 | [+0.00114856, +0.00422682] | -0.00037462 | -0.00079031 |
| R075_V | +0.00262017 | [+0.00116483, +0.00415338] | -0.00003284 | -0.00490388 |
| R125_V | +0.00252881 | [+0.00104462, +0.00411594] | -0.00060317 | -0.00128564 |
| TAIL005 | +0.00259096 | [+0.00118227, +0.00408654] | -0.00021852 | -0.00232483 |
| TAIL010 | +0.00256596 | [+0.00114796, +0.00410737] | -0.00018577 | -0.00426495 |

C corresponde a cambiar la completitud con tasas agregadas fijas; V añade la revaloración analítica de marcas por peril. R075/R125 usan las respuestas oficiales con reservas al 75%/125%. TAIL005/010 conserva T0 y desplaza hipotéticamente un 5%/10% de masa más allá del soporte observado solo en lesión corporal y subsidencia, según el contrato previo. Ninguna variante identifica los siniestros desconocidos. No son ajustes completos del modelo ni una prueba de suficiencia de reservas.

Los seis incrementos son positivos en ambos años y los cinco folds. Los límites inferiores simultáneos exploratorios de los seis escenarios también son positivos. La concentración persiste en todos: post31 es negativo. La revaloración al 75% empeora autos nuevos de 2023 en -0,00490388; la cola del 10% empeora esa misma celda en -0,00426495. No se escogerá un escenario favorable para el CSV, se eliminarán grupos o se cambiarán los criterios.

Quince ámbitos verificaron ancestros/grupos, la identidad del enlace base, simetría lineal de reservas e integración diaria por un método escalar independiente. El máximo error absoluto de integración fue 2.7200464103316335e-14. Se aceptan ceros legítimos por peril sin suelo artificial. Los SHA de las fuentes permanecieron iguales; estos recibos cubren únicamente el código registrado.

La consulta de cupos del 26 de octubre a las 10:32 UTC devolvió 10 envíos del día, 22 acumulados y cero disponibles ahora; no es un límite total. El primer intento de lectura falló por DNS dentro del entorno restringido; la lectura posterior autorizada tuvo respuesta. No se envió archivo ni se consultó score privado.

La instrucción directa vigente del participante abre 2024 para desarrollo, análisis, ajustes y validación. Sustituye el cierre histórico, incluso si el texto antiguo del objetivo automático todavía lo menciona. Los resultados de 2024 son adaptativos y no constituyen confirmación intacta. B00, F3c procesado con 0,16914 y todas las alternativas, prototipos y versiones fallidas se conservan. El objetivo público de 0,17 sigue activo y no se ha logrado.

Siguiente unidad: aislar la corrección H1 en las bases ya guardadas, sin la forma FSp de renovaciones. H1 pasó el control post31 local y PUL2 no; esa diferencia concreta justifica comprobar si una corrección más simple transfiere mejor. Se registrará antes de puntuar, sin entrenar ni repetir la tanda PUL2. Permanecen la falta de replay completo de F3c y de validación anidada del ensemble final, además del soporte insuficiente de la sensibilidad ponderada.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/sensibilidad_observacion_PUL2_20261026_v2/report.json.
