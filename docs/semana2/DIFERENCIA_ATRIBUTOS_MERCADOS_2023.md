# Diferencias de atributos entre mercados de 2023

Codex, 25 de octubre de 2026. Un clasificador logístico sencillo distingue los mercados a partir de los atributos físicos admitidos. Esta comprobación cubre una carencia del análisis marginal anterior. No usa costes, exposición, C0, reservas o primas, y no genera precios.

Se ajustaron quince clasificadores, uno por ramo y fold. Quedaron fuera del aprendizaje el bloque fuente y el fold emergente retenidos, con grupos, clientes y direcciones separados. Región y construcción de edificios se excluyeron para conservar el contrato de atributos transportables. Cada objeto guardado reprodujo exactamente sus resultados desde disco.

| Ramo | AUC en los cinco folds | Menor ESS/n con pesos limitados | Resultado del prefiltro |
| --- | ---: | ---: | --- |
| Autos | 0,7155–0,7226 | 0,5141 | Pasa para considerar una prueba posterior |
| Edificios | 0,6786–0,6905 | 0,5064 | Falla por cola emergente en dos folds |
| Contenido | 0,7264–0,7337 | 0,4760 | Falla por ESS y cola en los cinco folds |

Los criterios se registraron antes de ajustar. Se exigía AUC de al menos 0,65 en cuatro folds para detectar una diferencia relevante bajo este modelo. El filtro de solapamiento pedía ESS/n de al menos 0,5, como máximo 20% de razones recortadas y como máximo 5% de filas emergentes con probabilidad de mercado superior a 0,95, en todos los folds. Las razones de densidad se diagnosticaron con límites fijos de 0,2 y 5; no se aplicaron a ningún precio o siniestro.

En edificios, la cola emergente llegó a 5,18% y 5,45% en dos folds. En contenido, ESS/n quedó entre 0,4760 y 0,4816 y la cola superó 5% en los cinco folds. Esos fallos se conservan; no se cambian los límites para admitirlos. Solo autos permite considerar una receta separada de ponderación de fuente, que aún necesitaría registro y controles de precio completos.

Estos resultados no prueban igualdad de costes condicionales entre mercados. Una logística lineal puede omitir otros desplazamientos y sus odds no identifican por sí solas la verdadera razón de densidades. Tampoco acreditan soporte emergente adicional, maduración a último o independencia tras la búsqueda adaptativa de 2023.

El primer intento de preparación pidió región a un transformador genérico aunque debía excluirla. El segundo lector pidió franquicias logarítmicas que los archivos emergentes guardan en bruto. Ambos fallaron antes de ajustar clasificadores reales. Se conservaron sus códigos y recibos. La tercera versión comprobó los dieciocho esquemas, proyectó solo atributos permitidos y derivó los logaritmos necesarios con la regla ya usada para valores no negativos. La equivalencia entre archivos sintéticos brutos y transformados pasó antes de la ejecución real; la sonda logística anterior se reutilizó por hash.

La evidencia está en privado/semana2/robustez2023/prefiltro_dominio2023_v3 y el plan vigente en registro/semana2_dominio2023_prefiltro_plan_v3.json. Se registran quince ajustes diagnósticos separados del contador de precios, cero ajustes de precios y cero C0. B00 y todas las alternativas permanecen. 2024 sigue cerrado, sin promoción o selección final.
