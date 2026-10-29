

## Dos años emergentes con C0 y credibilidad por componentes, 25 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T01:23:33.574112+00:00. 2024 permanece abierto por la instrucción humana más reciente. La misión 0,17 sigue activa y no depende del cierre antiguo que conserva el texto del tool de objetivos. B00, F2 y todas las alternativas siguen conservados; no se gastó ningún envío.

El padre T2b de F2, autor Claude, se reconstruyó con sus variables históricas: las 109.296 filas de 2023–2024 reproducen las predicciones guardadas salvo un factor constante por antiguo fold, con desviación relativa máxima 4,44e-16. No se entrenó ni puntuó en ese replay. La fuente incluye desarrollado hasta 2024; es información disponible al inicio de 2025, no una predicción prospectiva del año 2024.

La nueva comparación usa los folds guardados por componentes cliente-dirección de ambos años. Todos los objetos de reporte, marcas, mezcla, factores por bandas y niveles se aprenden excluyendo el componente retenido. D² local OOF: N0=0.133829, N1=0.134137, N2=0.134961, N3=0.135250. N1 añade la corrección relativa NCB/previos con credibilidad 300; N2 contrae el nivel por negocio con credibilidad 400; N3 combina ambas.

N3 mejora +0.001420 frente a N0 y gana en cinco folds y en ambos años. Su IC95 individual por componentes es [+0.000043, +0.003138], pero el intervalo simultáneo de las tres comparaciones incluye cero. La mejora no alcanza el mínimo preinscrito de 0,002 y pasa a -0.000957 al retirar los 31 grupos más favorables. Ninguna alternativa cumple todos los criterios. Se conserva el resultado adverso y no se promueve un modelo por esa cifra.

Los quince ámbitos reales se reprodujeron exactamente, con ajuste bloqueado, y alterar costes retenidos no cambió las predicciones. Se cotejó que cada ámbito contiene solo las filas y los siniestros de los componentes permitidos. Una prueba sintética anterior también verificó la invariancia de todo el aprendizaje frente a cambios de costes/perils protegidos. La métrica se contrastó con scikit-learn. Son verificaciones propias, no revisión profesional independiente.

Esta tanda añade 75 curvas de reporte, 105 constantes de nivel, 140 factores por bandas y 40 normalizadores aprendidos en entrenamiento; cero ajustes de nuevos estimadores de precio y cero envíos. No se vuelve a ajustar C0 para la próxima comparación si sus fuentes y ámbitos son los mismos. Continúan las limitaciones de la valoración única a diciembre de 2024, maestros sin fecha, cola no observada y suficiencia de reservas. La marca pública del equipo sigue en 0,16033, todavía por debajo de 0,17.

Próxima unidad: Preparar una comparación estándar de familia fuente sobre desarrollado 2021–2024, con CatBoost Tweedie y mezclas fijas frente a T2b. Primero revisar antecedentes CB y preparar variables comunes/fechas y unidades; 2024 está autorizado. Reutilizar las 15 curvas/mezclas C0 por ámbito de esta tanda para los grupos emergentes: no volver a ajustarlas ni remuestrear esta comparación. Congelar código/configuración/coste/criterio y foro antes del nuevo ajuste o score. No usar niveles derivados del leaderboard ni las sondas antiguas; conservar F2 y los cupos hasta una mejora local robusta. La fuente externa 2024 sirve para el ámbito de información al inicio de 2025, no para llamar prospectiva una validación de 2024.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda2_20261025_v1/validation_v1/report.json. Plan congelado: Hackaton/Repositorio_IAA2026/registro/semana2_mision017_fase2_tanda2_plan_v1.json. Índice vigente: Hackaton/Repositorio_IAA2026/registro/semana2_mision017_fase2_actual.json.
