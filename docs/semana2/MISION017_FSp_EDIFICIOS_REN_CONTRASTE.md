

## Edificios en renovación: contraste adverso conservado, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T05:58:35.136847+00:00. Se completó el único contraste registrado del componente recuperado: peso fijo del 25 % en edificios en renovación, sin cambiar nuevo negocio, los otros ramos o los totales de precio por año. El denominador conserva los multiplicadores de prior claims de N3; los componentes se anualizaron por la exposición original del productor y se aplicó una sola vez la exposición canónica. Se reutilizaron los cinco ámbitos globales y sus C0. Las treinta constantes por peligro se estimaron exclusivamente en entrenamiento.

| Medida | Resultado |
|---|---:|
| D² N3 | 0.13524973 |
| D² alternativa ER1 | 0.13540500 |
| Diferencia global | +0.00015527 |
| IC 95 % por grupos, condicionado a fuente fija | [-0.00115241; +0.00155308] |
| Aporte global de 2023 | +0.00036245 |
| Aporte global de 2024 | -0.00020718 |
| Tras retirar 31 grupos favorables, mismo denominador global | -0.00217443 |
| Sin los 31 grupos de mayor coste observado | -0.00019416 |

Tres de cinco folds empeoran. El intervalo incluye pérdidas; 2024 pierde y el contraste por renovación de edificios de ese año también incumple el umbral por celda registrado. La ganancia media no es robusta y queda por debajo del mínimo global de +0,002. Se conservan la alternativa, los modelos y todas las salidas; no se incorpora este cambio ni se genera otro CSV de envío por este resultado. Las previsiones positivas recibidas para K no se trasladan: esta reconstrucción, la fórmula y el ámbito son distintos.

El comparador es N3, no el F3c completo. No está disponible aquí el contraste íntegro F3c/F2 ni los vetos de sensibilidad2025/A1, por lo que también faltan esos requisitos. No se confunde un fallo del contraste actual con una prueba de que cualquier FSp futuro de edificios deba retirarse. El bootstrap condiciona a los modelos fuente guardados y no incluye su incertidumbre. La valoración a diciembre de 2024, los maestros sin fecha y el desarrollo adaptativo limitan la interpretación prospectiva.

Pasaron los controles numéricos y de fuga del flujo nuevo: etiquetas retenidas totales y por peligro alteradas sin efecto en el aprendizaje o las predicciones, exclusión de grupos, integración independiente de C0, reproducción con parámetros guardados sin estimar, exponenciales/normalización por otra fórmula y pérdida Tweedie contrastada con scikit-learn. Los controles mecánicos no corrigen el deterioro predictivo. Coste de este contraste: 30 constantes de precio por peligro, 10 normalizadores de predicciones, cero árboles, C0, precios de test o envíos; las 30 recomputaciones idénticas del control adverso se cuentan aparte. Los 24 ajustes fuente de la recuperación anterior ya estaban contabilizados y no se suman de nuevo.

La comprobación acotada de las dos carpetas FSp recibidas encontró solo los cuatro metadatos de motor/contenidos, sin sus Parquet numéricos. Se guarda el inventario exacto y no se afirma ausencia global. El siguiente paso es resolver ese faltante para separar el componente FSp de los factores del donante compuesto, antes de otra comparación o envío. B00, F2/C1/F3c y las versiones fallidas se mantienen; 2024 está abierto por autorización humana. El mejor recibo continúa en 0,16914 y faltan 0,00086 para 0,17. La cuota 0 impide otro envío por ahora, pero el trabajo local sigue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_REN_contraste_20261026_v1/report.json.

Siguiente unidad: FSp de edificios ya está reconstruido y su inserción REN .25 no pasó: no repetir esos24fits,30constantes o bootstrap. Mantener la alternativa y B00/F2/C1/F3c. La composición F3c/F4c REN motor/contenidos sigue provisional y no es FSp puro. Primero buscar de forma acotada salidas numéricas motor/contents f/s en otras rutas recibidas pertinentes, sin repetir las dos carpetas ya inventariadas ni el inventario K. Si no existen, preparar entradas de precisión completa de esos dos ramos y conciliar metadatos ya presentes usando los recuentos y C0 existentes; no reconstruir los edificios otra vez. Registrar la necesidad, rondas fijas, coste y foro antes de cualquier recuperación fuente adicional. El propósito es aislar FSp de los factores y contrastar en los mismos grupos antes de considerar un envío. No relajar criterios ni retocar pesos por el resultado adverso de edificios o el score público.2024abierto como desarrollo; cuota0; meta0.17activa.
