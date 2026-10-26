# Revisión A: forma en autos y F1

Código propio en esta carpeta. Los D² usan el nivel Tweedie óptimo por celda.

## a) Métrica
Mi desviación y mi D² coinciden con sklearn (diferencia < 1e-15, también con pesos). El escalar óptimo para p=1,5 es k = Σy·m^-½ / Σm^½, verificado numéricamente.

Error principal: en `forma_local.py`, línea 6, `kopt` devuelve k² (autos NB 2023: 3,92 en vez de 1,98). Se hereda en forma_local2 (l. 11 y 33), forma_local3 (l. 25), ncb_local (l. 24), forma_check (l. 12) y construir_forma (l. 18).

## b) Afirmaciones 1 y 2
- a óptima en autos NB (IC90, bootstrap de clientes, 1.000 réplicas): 2023 T2b 0,60 [0,30–1,03]; 2024 T2b 0,45 [0,10–0,85]; 2024 A1 0,525 [0,25–0,85]. Con k² salen 0,40/0,40/0,50, así que el «0,4–0,5» viene en parte del error.
- Sin los 20 siniestros mayores (34–59 % del coste de la celda): 0,70/0,775/0,75.
- Renovación: 0,925/0,825/0,875. Hogar inestable (edificios NB: 1,05/0,45/0,50). Se confirma.
- Fuera de tiempo (2024, composición 2025 por celda), regla 0,5/0,85: T2b +0,0053, A1 +0,0037. Con la a de 2023 corregida (0,6/0,9): +0,0049 y +0,0036.

## c) Alternativas
En 2025, el 82 % del NB de autos tiene exposición ≥ 0,9 (el 88 % empieza en enero), frente al 8–9 % en 2023–24, y la compresión se mide casi solo con pólizas de medio año. Con exposición ≥ 0,9: 2023 da 0,25 [0–1,5] (48 siniestros), 2024 T2b 0,925 [0,37–1,5] y A1 1,025 [0,48–1,5]; los dos años juntos, 0,725 [0,40–1,08]. Reponderando 2024 por celda × banda de exposición como 2025, la regla 0,5/0,85 resta (T2b −0,0014; A1 −0,0035).

El nivel mal reoptimizado duplica la ganancia de 2023 en autos NB (0,0059 con k², 0,0027 bien). c_fila no explica el patrón (2023 con c_fila ≥ 0,95: a=0,75). No veo fuga: empujaría hacia a ≥ 1, y la prueba 2023→2024 es fuera de tiempo.

## d) F1 frente a F
Mismas 209.063 filas y orden, hogar idéntico, todo positivo y finito. Totales: autos NB −15,4 %, renovación −6,6 %. Una regresión de log F1 sobre log F, log exposición y bandas NCB reproduce F1 exactamente (coeficientes 0,5/0,5 y 0,85/0,15, factores NCB iguales a F1_info, residuo ≤ 1e-6). La «razón de nivel» 0,8464/0,9341 es el cuadrado de la correcta, 0,920/0,967. Además, F está menos dispersa que los modelos donde se midió a (desviación típica de log-tasa 0,52 frente a 0,57–0,60), así que a=0,5 sobre F comprime más de lo medido.

## e) Recomendación
No enviaría F1. Si se aplica forma: a≈0,75 en autos NB medida sobre T2b (unos 0,83 sobre F), 0,85–0,9 en renovación y razón de nivel con k correcto (≈0,95 y 0,967). Esa razón solo vale si F estaba en su óptimo Tweedie; si F se niveló para igualar totales, el óptimo del F comprimido queda un 2–15 % por encima y habría que subir el nivel, no bajarlo. En 2024 reponderado, a=0,75 aporta entre +0,000 y +0,001.

El riesgo es mover el nivel de un tercio de 2025, una población distinta (año completo, enero), con un resultado que depende de pocos siniestros. El NCB solo suma +0,0011 fuera de tiempo (+0,0007 reponderado); prior_claims no lo revisé.
