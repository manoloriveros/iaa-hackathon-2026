# Revisión de primer orden de la predicción 2025 (agente C)

Scripts en `revision/` (`comun.py`, `recalculo_kopt.*`, `nb_desde_renovacion.*`). "Composición 2025": celdas ramo × nuevo negocio ponderadas como en el test.

## 1. El escalar Tweedie óptimo va al cuadrado (error real, accionable sin tablero)

`forma_local.py` define `kopt = (Σy/√m / Σ√m)**2`. Para p = 1,5 el óptimo es Σy/√m / Σ√m, sin cuadrado. Comprobado con un minimizador numérico (buildings_0 2024: 0,619 frente a 0,383). La función se usa en `construir_forma`, `ncb_local`, `prior_local`, `residual_glm`, `forma_local2/3` y las dos `sonda_forma_*_prep`.

- **F1 está bajo de nivel en autos.** La razón aplicada es 0,846 en motor_1 y 0,934 en motor_0; la correcta es 0,920 y 0,967. Con el álgebra de las sondas públicas (a_s, b_s de `preinscripcion.json`) eso cuesta unas −0,0019 de D² público.
- **Las sondas de forma miden nivel.** La de buildings_1 con a = 1,3 lleva un +16 % de nivel y la de a = 0,7 un −8,6 %. Solo por nivel, eso mueve el D² público −0,0018 y +0,0004, más que la señal de forma: la parábola elegiría a < 1 sin motivo. En motor_1 (a = 0,3 / 0,7) el sesgo es de −0,0002 / +0,0005, del mismo orden que la señal.
- **Las mediciones locales están distorsionadas.** El D² local con composición 2025 era 0,122–0,143 y con la fórmula correcta es 0,152–0,156, cerca del público. La ganancia de F1 en 2023 baja de +0,0103 a +0,0034, y el a óptimo de motor_1 en 2023 pasa de 0,4 a 0,6.

Hay que quitar el `**2`, rehacer F1 y las sondas, y volver a medir NCB, prior y el GLM residual. Las sondas por celda (c* = a/b) están bien.

## 2. El modelo casi no ordena el riesgo dentro del nuevo negocio

En 2023–2024 el nuevo negocio tiene exposición parcial y gran parte de su D² sale de ella; en 2025 cubre el año entero y solo cuenta la ordenación. Habilidad neta: desviación ahorrada frente a predecir solo con la exposición, entre la desviación nula de la celda.

| Celda | Mezcla 2024 | T2b 2023 | F1 2024 |
|---|---|---|---|
| motor_1 | 0,0003 | 0,009 | 0,0135 |
| buildings_1 | 0,0002 | 0,085 | igual |
| contents_1 | 0,017 | 0,067 | igual |

En renovación la habilidad va de 0,04 a 0,11. Con composición 2025, el nuevo negocio pesa 0,67–0,69 de la desviación nula: cada +0,01 de habilidad ahí suma unos +0,007 de D². La brecha de 0,012 equivale a unos +0,018 de habilidad. El nivel por celda, según las sondas, aporta solo +0,0022.

Sin tablero se puede actuar solo en parte. Un LightGBM entrenado solo con renovaciones ordena mejor el nuevo negocio de autos: 0,0147 frente a 0,0043 del equipo, con 613 siniestros de 2023–2024. En hogar empeora (0,014 frente a 0,046 y 0,033; 75 y 100 siniestros). El encogimiento en buildings_1 da a ≈ 0,5 en 2024 y a ≈ 1,05 en 2023, o sea ruido. La vía razonable es aprender las relatividades del nuevo negocio en el mercado desarrollado (no probado aquí).

## 3. Revisado y descartado (≤ 0,0005)

- **Alineación.** Los 209.063 row_id coinciden con el test, sin duplicados, y F = mezcla × 1,18766. La correlación por póliza renovada entre las tasas 2025 y 2024 es 0,86–0,96, y la tasa es plana en exposición, como en 2024.
- **Exposición cruda.** 114 filas de entrenamiento vienen en días (= 365); no afecta a las predicciones y el test está limpio.
- **Prima escrita.** Es anual (prima/exposición no es una tasa) y correlaciona con F como en 2024. Con nivel correcto, mezclarla da −0,002 a +0,003; mi +0,006 inicial era artefacto del punto 1.
- **Covariables.** Nuevo negocio 2025 frente al orgánico: AUC adversarial 0,56–0,61 (make_model, ocupación, capitales); canal, multiproducto y prior_claims iguales.
- **customer_service_contacts.** En el entrenamiento casi delata el siniestro: 0 % de filas con siniestro si vale 0, 50–95 % si vale 3 o más. En 2025 vale 0,40 sin relación con la exposición. F no lo usa, y hay que mantenerlo fuera.
- **Nuevo negocio de enero frente al de otros meses.** Hay 86, 10 y 15 siniestros (autos, edificios, contenidos); no es medible.
