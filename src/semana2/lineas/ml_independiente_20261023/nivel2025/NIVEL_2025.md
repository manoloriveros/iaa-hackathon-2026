# Nivel 2025 con evidencia actuarial (E27) y entrega recomendada

Pedido del participante, 25 de octubre de 2026: «aplica el punto 3 y preparemos una entrega». El punto 3 era estimar el nivel de 2025, sobre todo el del nuevo negocio de autos, solo con evidencia actuarial y con una regla fijada antes de calcular. Nada se envió.

En resumen, la tarifa de la aseguradora sugiere subir el nivel un 13 % en conjunto: un 21 % en autos, un 12 % en contenidos y nada en edificios. Es la misma dirección que el tablero, que pide un 22 %. Pero esa tarifa cambia tanto entre 2023 y 2024 que la regla preinscrita le da poco peso, y el archivo que sale de ella apenas se mueve (+0,8 %). La entrega que recomiendo es el nivel global creíble que otra sesión de Claude calculó con los sondeos del tablero (×1,1877). La verifiqué por mi cuenta y la evidencia de la tarifa la respalda en la dirección, aunque no en el reparto por ramo.

![Nivel 2025](f13_nivel_2025.png)

## Por qué el nivel importa tanto

En 2025 el 76 % de la cartera es nuevo negocio, frente al 12-15 % de 2023-2024. Los modelos aprenden bien el orden de riesgo, pero el nivel de ese bloque nuevo no se puede validar con los años anteriores. En E09, llevado a la cartera 2025, un error del 15 % en el nivel de autos costaba unas 0,002 de D². Es más que cualquier mejora de estructura que se haya medido en esta línea.

## El método: siniestralidad esperada sobre la prima escrita

Es un método clásico de reservas y tarifas (*expected loss ratio*). Cada póliza de 2025 trae la prima que le cobró la aseguradora, que es su propia estimación del riesgo y no depende ni del tablero ni de nuestros modelos. La prima escrita es anual: su mediana es la misma en tramos parciales y en años completos.

La idea es esta. Si en 2023-2024 la aseguradora pagó 0,73 CU de siniestros por cada CU de prima en la renovación de autos, y en 2025 cobra P por ese bloque, el coste esperado es 0,73 × P. Comparado con lo que predice la mezcla enviada, da un factor g. Para cada segmento (tres ramos por nuevo negocio y renovación):

1. Siniestralidad 2023-2024: coste último (y / c_fila) entre prima devengada (prima × exposición), con credibilidad hacia la del ramo (Z = n/(n + 200), n siniestros).
2. Coste que implica la tarifa en 2025: siniestralidad × prima devengada de 2025.
3. g = ese coste / el de la mezcla enviada.
4. Credibilidad frente al modelo: Z = τ²/(τ² + σ²), con τ = 0,07, el desvío típico de nivel del modelo en la parte 1. Aquí σ suma la incertidumbre de muestreo (bootstrap por cliente) y la discrepancia entre 2023 y 2024.
5. Factor f = g^Z, con tope [0,85; 1,15].

La regla está en `PREINSCRIPCION_NIVEL.md` (SHA-256 13d2ef2f…4c55), escrita en el equipo antes de calcular. Una aclaración de orden: la anoté en el registro un minuto después de que Codex publicara en el foro los sondeos globales de otra sesión. No los había leído y la regla no usa el tablero.

## Lo que da

| Segmento | Siniestralidad 2023 | 2024 | g | σ | Z | f |
| --- | --- | --- | --- | --- | --- | --- |
| Autos, nuevo negocio | 1,397 | 0,879 | 1,248 | 0,343 | 0,040 | 1,0089 |
| Autos, renovación | 0,680 | 0,777 | 1,060 | 0,099 | 0,335 | 1,0199 |
| Edificios, nuevo negocio | 1,378 | 0,693 | 0,948 | 0,495 | 0,020 | 0,9990 |
| Edificios, renovación | 1,502 | 0,902 | 1,037 | 0,375 | 0,034 | 1,0012 |
| Contenidos, nuevo negocio | 0,787 | 1,004 | 1,141 | 0,193 | 0,116 | 1,0154 |
| Contenidos, renovación | 0,734 | 0,655 | 1,039 | 0,103 | 0,315 | 1,0120 |

Fuente: `e27_nivel.json`. Una comprobación independiente con otra forma de agregar los datos reproduce los g con una diferencia de 2e-16.

Sin credibilidad, la tarifa pide subir el total un 13,0 %: autos un 21,4 %, edificios −3,2 % y contenidos un 11,8 %. Con credibilidad, el archivo preinscrito (`e27_nivel_2025.csv`, SHA 73040680…16a4) sube solo un 0,8 %, hasta 69,52 M CU.

La razón está en la columna de 2023 y 2024. La siniestralidad de edificios pasa de 1,50 a 0,90 en un año y la del nuevo negocio de autos de 1,40 a 0,88. Con esa inestabilidad, la regla no puede dar mucho peso a la tarifa.

Lo confirma el backtest de un año que fijó la preinscripción. Aplicada a T2b con la siniestralidad de 2023 sola, la regla baja el D² de 2024 de 0,1260 a 0,1248, y sin credibilidad a 0,1227 (`e27_backtest_2024.json`). La siniestralidad de un año no anticipó el nivel del siguiente. La tarifa sí ordena el riesgo igual que antes: la correlación de rangos entre prima y predicción es de 0,60 a 0,73 en 2025 y de 0,57 a 0,73 en 2023-2024.

## Lo que dice el tablero

Con autorización del participante en otra sesión, Codex envió dos sondeos globales sobre la mezcla enviada: ×0,85 dio 0,14095 y ×1,20 dio 0,15955 (COD-S2-20261024-ENVIOS-SONDA-GLOBAL). Con la forma cerrada de la desviación Tweedie, el óptimo del público es ×1,2231. La otra sesión, con su regla preinscrita, lo encoge a ×1,1877 por el ruido entre la parte pública y la privada. Reproduzco las dos cifras.

Las dos fuentes coinciden en la dirección: la mezcla enviada está baja. La tarifa sugiere +13 % y el tablero +22 %. En el reparto discrepan. El tablero solo ve el total, y la tarifa pondría casi todo en autos y nada en edificios.

## Elegir la entrega con escenarios

El tablero no dice cómo se reparte el nivel entre ramos, así que comparo dos hipótesis. U: el nivel correcto es el mismo en los tres ramos. T: se reparte como dice la tarifa. Las cifras salen de la forma cerrada, con el peso de cada ramo medido en las predicciones de 2025.

| Archivo | Factores (autos / edificios / contenidos) | Público esperado si U | si T |
| --- | --- | --- | --- |
| Mezcla enviada | 1 / 1 / 1 | 0,15390 | 0,15390 |
| E27 preinscrito | 1,011 / 1,000 / 1,015 | 0,15435 | 0,15449 |
| Global creíble (recomendado) | 1,188 / 1,188 / 1,188 | 0,15948 | 0,15948 |
| Global creíble repartido por la tarifa | 1,266 / 1,043 / 1,179 | 0,15846 | 0,16076 |

El reparto por la tarifa es una apuesta: gana 0,0013 si la tarifa acierta y pierde 0,0010 si no. Como la tarifa falló su backtest, no la preparo como entrega.

## La entrega recomendada

`Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv`

- SHA-256: 42659dbb4101d4f9a4ab00c287d77b2bd21d42be9734d2ca4a4074eb57c9add2.
- Contenido: la mezcla enviada multiplicada por 1,18766 en todas las filas. Total 81.943.158,72 CU.
- Origen: otra sesión de Claude, con su regla preinscrita (`salidas/sonda_global__preinscripcion.json`). Codex ya la validó.
- Comprobado aquí de forma independiente: misma huella; el cociente con la mezcla enviada está entre 1,1876565 y 1,1876626 en las 209.063 filas, que es el redondeo al sexto decimal; mismos `row_id` en el orden de la plantilla; saltos LF.
- Público esperado: 0,15948 frente a 0,15390. El privado debería moverse en la misma dirección, pero su tamaño no se puede asegurar.

No preparé un archivo nuevo para no duplicar el de la otra sesión. El de E27 queda en `privado/` como resultado de la regla preinscrita y no lo recomiendo para enviar. El envío lo hace Codex solo con autorización expresa del participante, y la marca final en Kaggle la decide él. Un aviso que viene de la parte 1: no marcar nunca un sondeo como entrega final, aunque el de ×1,20 haya puntuado 0,15955.

## Para el informe final

Este ejercicio es validación actuarial del nivel con una fuente que no depende del tablero. Conviene contarlo así:

- La tarifa de la aseguradora y el tablero coinciden en que el nivel del modelo estaba bajo.
- La tarifa no basta para fijarlo, porque su siniestralidad cambia entre un 10 % y un 50 % de un año a otro según el segmento.
- La corrección final la fija el tablero con una regla escrita antes de ver las puntuaciones, y se aplica encogida por credibilidad.

Código: `codigo/e27_nivel.py`, `e27_backtest.py` y `figura_nivel.py`. Registro: E27, E27-aviso, E27-resultado y E27-tablero en `experimentos.jsonl`.
