Codex. Continúo COD-S2-20261023-011 por nueva petición del participante. La [revisión de nivel e influencia](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_nivel_20261023T181136Z_82668c37/report.json) usa solo OOF2023 congelado y no calculó factores o nuevas predicciones.

B03 predice 14,320 millones CU y B05 14,113 frente a 15,614 de B00 y 15,297 observados. El déficit respecto del observado se concentra en edificios: 0,718 millones CU en B03 y 0,695 en B05. Los 31 grupos más favorables representan 140,5 % y 130,0 % de la ventaja neta, respectivamente; compensan contribuciones adversas del resto. Contienen 12,31 % y 9,48 % del coste observado, con cerca de 0,12 %/0,13 % de la exposición. Basta retirar 14 grupos favorables en B03 o 18 en B05 para invertir la ventaja. Diecinueve grupos pertenecen a ambas listas. Son diagnósticos condicionales con modelos fijos, no errores de datos ni un jackknife con reentrenamiento.

El [plan v3](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v3.json) fija una prueba de nivel y contracción antes de calcular resultados. Para cada padre, ramo y fold se aprende exclusivamente en sus filas de ajuste:

`s = sum_ajuste(e × c0) / sum_ajuste(e × r_padre)`

Aquí c0 es la tasa B00 ya guardada y e su exposición efectiva C0. No se usa la suma observada para forzar A/E, el total OOF ni información del fold retenido para aprender s. Se comprueba la igualdad del total predicho de ajuste con el de B00. Usa predicciones dentro del ajuste, no una calibración independiente o interna fuera de muestra; el ancla B00 también depende de siniestros y puede ser sensible a eventos grandes.

- B06: forma B03 × s, sin cambiar su orden anual de riesgos dentro del ramo/fold.
- B07: forma B05 × s, con la misma regla.
- B08: 50 % de la tasa B00 y 50 % de B06.
- B09: 50 % de la tasa B00 y 50 % de B07.

Los pesos 1 y 0,5 quedan fijos; no se buscará el mejor. Las cuatro recetas comparten treinta factores y se guardarán sesenta adaptadores, sin ajustar nuevos GLM o árboles. B08/B09 reducen exactamente a la mitad la desviación de la tasa anclada frente a B00, pero eso no garantiza reducir a la mitad su influencia en devianza. No se elimina ningún grupo de ajuste, calibración o score completo.

La lectura previa exige comprobar el momento de ajuste y después observar nivel OOF por ramo/fold, A/E, devianza e influencia. Se repetirá el retiro de 31 grupos favorables de cada receta y, además, el de la lista congelada de su padre para hacer comparable el diagnóstico. Se conservarán B00–B05 exactos, las 45 parejas de diez recetas y 2.000 sorteos comunes exploratorios. La búsqueda adaptativa y multiplicidad quedan declaradas; no se confunden con confirmación de2024 o equivalencia.

Se mantiene B00 cualquiera que sea el punto de esta tanda; todas las alternativas siguen registradas. Los supuestos del último y los bloqueos de recetas anteriores conservan sus responsables. Se recibió el cierre técnico del vínculo del selector y el seguimiento GOV005 publicados por otros encargos, sin adjudicar cierres aquí. 2024 permanece cerrado por instrucción expresa, sin importar su avance. No hay lista final congelada, precios de2024/test, envíos, remoto o delegación en esta prueba.
