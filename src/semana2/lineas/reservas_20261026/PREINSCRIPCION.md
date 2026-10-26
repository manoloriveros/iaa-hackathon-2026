# Preinscripción: acotación de reservas de la semana 2 con el modelo actual (F3c)

Claude (Cowork, sesión de la línea principal), 26 de octubre de 2026. Petición del participante en esta sesión: «Actualiza y recalcula la acreditación de reserva (y los adicionales que sean necesarios), al trabajo, el modelo y la información de la segunda semana, el modelo actual». Este plan se escribe antes de calcular nada de lo que describe. No se envía nada, no se cambia F3c ni ningún archivo de la cadena y no se toca la selección. Nada de esto es revisión humana.

## Qué es el modelo actual y por dónde le pueden llegar las reservas

El modelo actual es F3c (`Repositorio_IAA2026/privado/semana2/claude_mision017_20261025/F3c_2025.csv`, SHA-256 5ab5e4e3…), con 0,16914 en el público (envío 57654514). Se construye en cinco pasos:

1. La mezcla 50/50 de la designada A1fixF1b3n y de la línea ML independiente (`mezcla50_designada_mlind_2025.csv`, 12831ef4…). Sus relatividades vienen de un LightGBM Tweedie entrenado en el mercado desarrollado. Su nivel por ramo sale del emergente 2023-2024: la designada por balance (Σ T0 / Σ m) y la línea ML con el escalar Tweedie (Σ y/√m / Σ √m), con m la predicción a nivel observado (exposición por completitud de reporte).
2. La sonda global: F = mezcla × g, g = c*_g^Z_g, con c*_g = 1,2231 el óptimo del público y Z_g = 0,854 (`final_sonda_global_2025.csv`, 42659dbb…).
3. F2: factores de NCB y de siniestros previos y forma 0,9 en renovación de autos, estimados con los OOF de 2023-2024 (119627d9…).
4. El nivel por celda (ramo × nuevo negocio) de las sondas por celda: factor g · (c*_s/c*_g)^Z_s, acotado a [0,75; 1,33], con los Z_s preinscritos (0,534, 0,36 y 0,81 en renovación de contenidos, edificios y autos; 0,736, 0,724 y 0,866 en nuevo negocio), y la forma de nuevo negocio con su Z.
5. Factores de género, teletrabajo y segmento, Tweedie-óptimos con credibilidad, estimados con los OOF de 2023-2024, y razón de nivel Tweedie local por celda.

F3d (5103f6fd…), preparado para el 27, solo cambia la credibilidad de los factores de contenidos.

Las etiquetas de los organizadores no dependen de nuestras reservas. Un error en la reserva de caso o en el IBNR del emergente cambia T0 de 2023-2024, y con él tres cosas: el nivel base de la mezcla (paso 1), los factores estimados con esas etiquetas (pasos 3 y 5) y, a través de los datos del desarrollado, las relatividades transferidas. Las sondas miden el óptimo del público en nivel absoluto, así que corrigen la mayor parte de un error de nivel base, pero solo en la medida de su Z.

## Parte A. Hechos de reservas del emergente

Siniestros asignados a su periodo por póliza, ramo y fecha de ocurrencia dentro del periodo, como `mision017/codigo/etiquetas.py`. Neto = incurrido − recobros; reserva de caso = incurrido − pagado en los abiertos. Control: T0 de entrenamiento 27.997.991,57 CU (Codex y validación de datos). Si no coincide al céntimo, se detiene y se investiga antes de seguir.

Se informan por ramo, año del periodo, peligro y negocio (nuevo o renovación): abiertos, reserva, reserva sobre T0, abiertos sin reserva, rechazados y sus importes, recobros en abiertos y en cerrados por peligro y, como en la semana 1, la sobrestimación de T0 si la reserva de los abiertos no anticipa los recobros que sí tienen los cerrados del mismo peligro.

## Parte B. Suficiencia de la reserva de caso (supuesto S1)

S1 dice que, dentro de un ramo, peligro y trimestre de reporte, lo que acaba costando un siniestro no depende de cuánto tarde en cerrarse. β es la reserva que haría falta para que los abiertos cuesten en media lo mismo que los cerrados de su celda, dividida por la reserva contabilizada. Mismo código y definiciones que `herramientas/reservas_consistencia.py` de la semana 1: celdas con al menos 20 cerrados, intervalo al 90 % con 400 réplicas Poisson por siniestro (semilla 20261026), y la prueba A2 de S1 (pendiente del logaritmo del cociente abiertos/cerrados frente al logit de la fracción cerrada; contradice S1 si |t| > 2).

Por ramo y por peligro largo (lesiones corporales en autos, hundimiento en edificios), y también por negocio si cada parte tiene celdas suficientes. Se compara con β del desarrollado (semana 1, `reservas_20261019T225357Z_99b45271/resultados/parte_a.json`): diferencia con su intervalo al 90 % por bootstrap independiente. Lectura secundaria: β agrupado de los dos mercados, solo si la diferencia no excluye el cero.

Hipótesis previa (H1): el generador es el mismo, así que β emergente y desarrollado no difieren de forma detectable.

## Parte C. IBNR

La completitud de reporte ponderada por coste se calcula como en `etiquetas.py`: curva por ramo y peligro con los siniestros aceptados del desarrollado de al menos 1.095 días de desarrollo, integrada sobre el periodo de cada fila hasta el 31-12-2024.

Backtest en el emergente, que es lo nuevo que permiten estos datos: para los siniestros ocurridos en 2023, la fracción de su coste (y de su número) reportada durante 2024, observada frente a la que prevé la curva del desarrollado. k_e = coste tardío observado / previsto, con intervalo al 90 % por bootstrap de siniestros (400 réplicas). Por ramo y por peligro largo. k_e es el análogo emergente del supuesto S3 de la semana 1: un k_e por debajo de 1 indicaría que el IBNR de 2024 está sobrevalorado.

Hipótesis previa (H4): los retrasos no difieren entre mercados (Kolmogórov-Smirnov, p ≥ 0,13 en los 15 peligros, CLA-S2-20261023-001), así que se espera k_e compatible con 1.

## Parte D. Del dato al nivel de F3c

D1. Nivel base. Para cada ramo r y escenario, ρ_r = nivel de la mezcla con las etiquetas del escenario / nivel con T0. Escenario b: reserva de caso de los abiertos × b en 2023-2024 (todo el ramo; y, en autos y edificios, solo el peligro largo o solo el resto). Escenario k: IBNR × k, es decir, completitud c' = c / (c + k(1 − c)) fila a fila. La designada usa el balance; la línea ML, el escalar Tweedie con m = μ × c, con μ las predicciones cruzadas de 2023-2024 de T2b (PCV); ρ de la mezcla pondera las dos por su total de 2025 en el ramo.

D2. Paso por las sondas. Con los óptimos del público fijos en nivel absoluto, un nivel base ρ_s en la celda s cambia los óptimos relativos a c*_s/ρ_s y c*_g' = Σ a_s ρ_s^−½ / Σ b_s ρ_s^½ (a_s y b_s de la sonda por celda), y el nivel final de la celda pasa a L_s' = ρ_s · c*_g'^Z_g · acotar((c*_s/ρ_s)/c*_g')^Z_s. Con ρ uniforme, la elasticidad es 1 − Z_g = 0,146; con un error en un solo ramo es mayor en las celdas de Z bajo (renovación de edificios y de contenidos). Los pasos 3 y 5 conservan el nivel de cada celda con una razón de dos escalares Tweedie sobre las mismas etiquetas, así que no se recalculan; se declara como supuesto.

D3. Umbrales. Para cada ramo, el b y el k que mueven el nivel 2025 de F3c del ramo un 1 % (nivel del ramo = celdas ponderadas por el total de F3c), primer cruce desde 1 con rejilla de paso 0,0025 hasta 3 y 0,05 hasta 20, afinado por bisección. Lo mismo por celda como lectura secundaria.

D4. Clasificación, la misma regla de la semana 1 con la materialidad que fijó el participante el 19 de octubre (1 % del nivel 2025 del ramo): «acotado» si el intervalo al 90 % de β (o de k_e) queda dentro del intervalo de quiebre, «indicio de desvío material» si queda entero fuera, «incertidumbre material» si lo cruza.

D5. Variantes, sin cambiar la clase principal: Z_g = 0,90 (la pendiente empírica que citó la preinscripción de la sonda global); solo la fórmula de la designada o solo la de la línea ML; b solo en 2024.

Hipótesis previa (H2): la sonda global absorbe el 85 % de un error uniforme, de modo que en autos (Z de 0,81 y 0,866) las reservas quedarían acotadas, y lo más expuesto serán las celdas de renovación de hogar.

## Parte E. Estructura

E1. Inclinación de las relatividades: el exponente a que mejor ajusta y frente a e · g · (r/g)^a, con el nivel reoptimizado, en el emergente 2023-2024 con la estructura T2b (PCV), con T0 y con las etiquetas de los escenarios b (0,75; 1,25 y los extremos del intervalo de β). Δa y su coste en D² con la curva de 2023-2024.

E2. Lo mismo en el desarrollado con las predicciones V24 de S30 (semana 1), como aproximación de cuánto inclinarían las reservas del desarrollado las relatividades que T2b aprende allí.

E3. Factores de los pasos 3 y 5 (NCB, siniestros previos, género, teletrabajo y segmento): cuota de reserva de cada nivel frente a la de su ramo, ponderada con 1/√m, y el cambio de cada factor en los extremos del intervalo de β sin la contracción de credibilidad, como cota.

## Parte F. Coste en la métrica

D² público de ±1 % de nivel por ramo alrededor de F3c, con la forma cerrada de cada celda (a_s y b_s de la sonda por celda), como aproximación declarada. Se citan, sin recalcularlos, los escenarios R075/R125 y de cola de Codex sobre PUL2 (COD-S2-20261026-MISION017-PUL2-OBS-STRESS-RESULTADO) y sobre 2023 (`docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md`).

## Salidas y reglas

Código, evidencia JSON, figuras, `INFORME.md` didáctico, cifras con verificador y manifiesto en `Hackaton/Semana 2/Claude/reservas_20261026/`; tablas por siniestro o fila, si hacen falta, en `Repositorio_IAA2026/privado/semana2/claude_reservas_20261026/`. Un resultado adverso se informa igual que uno favorable. Lo que se calcule fuera de este plan se marca como no preinscrito. Revisión independiente por un subagente antes de publicar.
