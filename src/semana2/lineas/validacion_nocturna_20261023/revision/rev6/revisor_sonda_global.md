# Revisión independiente de la sonda de nivel global (subagente de IA, 24-10-2026)

Revisor: subagente general de Claude, sin contexto previo, con acceso al código y a las salidas. Es una revisión de IA, no una revisión profesional humana. Este es un resumen fiel de su informe, traducido.

Veredicto: nada bloqueante. Los dos archivos de sonda son correctos y se pueden enviar. La regla es sólida. Antes de ejecutar el resolutor con las puntuaciones reales hay que añadir las paradas de c* no identificable y de |log c*| > 0,4.

1. La fórmula es exacta. Para p = 1,5, dev = −8√y + 4y·μ^(−1/2) + 4√μ. Con μ → cμ: D2(1) − D2(c) = (4A/N)(c^(−1/2) − 1) + (4B/N)(c^(1/2) − 1). El mínimo está en c* = A/B. No hace falta N ni saber qué filas son públicas, y vale con pesos o con un D² promediado por ramo. Comprobación numérica: residuo ≤ 2e−16, y el c* sin redondeo coincide con el mínimo por fuerza bruta (0,935936). El álgebra del resolutor y las condiciones de signo son correctas.
2. Los CSV pasan: 209.063 filas, el mismo orden que la base y que sample_submission, valores idénticos como texto a '%.6f' % (base × c), todos positivos y finitos, SHA iguales a la preinscripción, cabecera row_id,prediction, sin CR ni BOM.
3. La recuperación de c* pasa. El modo de prueba da 1,0874 frente al 1,0872 verdadero. Con 150 remuestreos al tamaño de 2025, niveles verdaderos entre 0,60 y 1,39 y redondeo a 5 decimales, el error máximo de |log| es 0,0008 para (0,85; 1,20), 0,0019 para (0,90; 1,10) y 0,0004 para (0,80; 1,30).

Hallazgos:
- A corregir: el resolutor no aplicaba las paradas preinscritas. Corregido: sale con código 2 sin escribir el archivo final, salvo con --forzar.
- A corregir: el backtest daba el mismo peso a los cuatro escenarios. El revisor estimó con la previa N(0; 0,12²) una ganancia media de 0,0019, p05 de −0,00046 y P(ganar) de 0,77. Corregido: añadido el escenario ponderado por la previa (+0,0018; 78 %).
- Menor: Z usa σ de la diferencia público − privado. El predictor óptimo daría Z ≈ 0,90 (pendiente empírica 0,908). Documentado y mantenido en 0,854, que es conservador; el efecto es menor de 0,00001.
- Menor: el sustituto de 2024 es A1fixF1b3n, no la mezcla. Documentado.
- Menor: el modo de prueba reescribe, con el mismo contenido, las salidas de evaluar_final.py. El revisor lo comprobó byte a byte. Documentado en el resolutor.
- Menor: con dos ecuaciones no sobra ninguna para comprobar la métrica. Añadido un control indirecto: la desviación nula por fila que implica βB, frente a la de 2023-2024. En la prueba da 102,05 frente a 102,41 real.
- Menor: comentario desactualizado («tres escenarios»). Corregido.
