# Combinación 50/50 de la designada y MLind

Preparada el 24 de octubre de 2026 a pedido del participante («prepara una combinación entre las dos»). La regla quedó fijada antes de calcular los diagnósticos, en `PREINSCRIPCION_MEZCLA.md` (15:44 UTC). No se envió nada.

![Mezcla](f11_mezcla.png)

## El archivo

| Pieza | Valor |
| --- | --- |
| Archivo | `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv` |
| SHA-256 | 12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a |
| Regla | media aritmética fila a fila de la designada A1fixF1b3n (f786deb3…224c53aa) y de MLind (d261388c…3e0a3), pesos iguales en los tres ramos, sin renivelar |
| Controles | 209.063 filas en el orden de la plantilla, sin nulos, todas positivas (mínimo 0,1023), diferencia máxima con la media exacta 5e-7 por el redondeo a seis decimales |
| Total 2025 | 68.995.571 CU: autos 42.122.566, edificios 21.369.469, contenidos 5.503.536 |
| Tasa por año de exposición | autos 533,1 (nuevo 567,6, renovación 418,7); edificios 451,1; contenidos 93,3 |

Las dos fuentes transfieren relatividades de un LightGBM del mercado desarrollado y fijan el nivel con el emergente 2023-2024, sin tendencia. Difieren en el código, los hiperparámetros, el tratamiento de la historia de la póliza y la calibración del nivel. Promediarlas reduce lo que cada una tiene de propio sin añadir supuestos nuevos.

## Diagnósticos en 2024

Son exploratorios: las dos líneas ya habían visto 2024. Para la parte designada se usa A1, su versión base, porque las predicciones de 2024 de A1fixF1b3n no se guardaron; según su propia línea, A1fixF1b3n mejora a A1 en +0,0030.

| | A1 | MLind | Mezcla 50/50 | Media geométrica |
| --- | --- | --- | --- | --- |
| D² total | 0,1214 | 0,1253 | 0,1247 | 0,1250 |
| Autos | 0,0803 | 0,0821 | 0,0833 | 0,0830 |
| Edificios | 0,0649 | 0,0764 | 0,0713 | 0,0723 |
| Contenidos | 0,0920 | 0,0903 | 0,0923 | 0,0926 |

- **Autos y contenidos:** la mezcla es mejor que cualquiera de las dos por separado. El peso óptimo de MLind es 0,55 en autos (IC95 [0,20; 0,90]) y 0,35 en contenidos ([0,00; 1,00]). Los dos intervalos incluyen 0,5.
- **Edificios:** 2024 prefiere a MLind sola (óptimo 1,00, IC95 [1,00; 1,00]). Es la única señal en contra de los pesos iguales. Viene de un año en el que los siniestros de edificios fueron el 61 % de lo esperado y el incendio cayó de 49 siniestros a 21, y además ese año lo vieron las dos líneas. Por la regla fijada, no cambia el peso; se informa como el principal aviso de la combinación.
- **Media geométrica:** queda +0,0002 por encima de la aritmética, que es despreciable. Se conserva la aritmética, que es la que conserva los totales.
- **Calibración:** observado/esperado de la mezcla en 2024: autos 1,05, edificios 0,61, contenidos 0,98. La descalibración de Murphy queda entre la de sus dos componentes (autos 1,4 % de la desviación, contenidos 2,1 %). En edificios ronda el 8 % en los tres modelos, por el mismo año bajo.

## Prima comercial de las 20 referencias

Misma fórmula que las dos líneas: P = [R (1 + 0,12 en hogar) + 85 × exposición] / (1 − 0,15 − comisión − 0,08 − 0,08), con R la predicción de la mezcla. Los componentes suman P en cada fila (`prima_comercial_20_mezcla.csv`, que trae también la sensibilidad con el gasto fijo repartido por póliza). Las medias por ramo son: autos 1.216,7 de prima comercial sobre 588,5 de riesgo; edificios 960,7 sobre 381,2; contenidos 258,8 sobre 50,3. La prima escrita media es 682,3, 247,8 y 138,2.

## Qué decide el participante

- **Entrega:** si esta combinación sustituye a la designada como candidata a entrega final. En 2024 empata con MLind y supera a la base de la designada. Frente a la designada, la diferencia estimada por puente es +0,0003 (0,1247 frente a 0,1244), sin intervalo.
- **Envío:** si se envía. Lo hace Codex con autorización expresa. El primer envío comprobaría además el arreglo de Kaggle anunciado el 24 a las 02:57 UTC.
