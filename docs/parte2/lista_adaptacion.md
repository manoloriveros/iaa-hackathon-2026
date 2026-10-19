# Qué adaptar cuando lleguen los datos de la parte 2

Lista de trabajo para pasar la receta de la parte 1 al mercado nuevo. Está ordenada: cada paso usa lo que deja el anterior. La parte 2 se evalúa con otra competición y las bases piden explicar en el informe y en el video cómo cambió la solución, así que cada cambio se registra con su motivo y su efecto medido desde el primer día, con commits en este repositorio.

## 0. Antes de tocar datos

- [ ] Leer las reglas y la página de datos de la parte 2 y actualizar `Hackaton/REGLAS_2026.md`: fecha de cierre, cupo diario, regla de selección final, métrica (¿sigue siendo Tweedie 1,5?), fecha de valoración de los siniestros y periodo a predecir.
- [ ] Copiar los Parquet originales a una carpeta nueva (`Hackaton/Semana 2/Datos`), guardar sus SHA-256 en un manifiesto y no modificarlos nunca.
- [ ] Fijar en el foro el calendario de validación de la parte 2 antes de entrenar nada (el equivalente de V23, V24 y producción) y el criterio de aceptación de cambios (mejora en los dos cortes, con todas las filas y sin el 0,1 % superior).

## 1. Calendario en un solo sitio

Los años están escritos a mano en unos diez scripts: `range(2021, 2026)` y `cum[2025]` en `comun.py`; `year.isin([2021, 2022])`, `year == 2023`, `year <= 2023`, `year == 2024` y `year == 2025` en `experimentos.py`, `evaluar.py`, `produccion.py`, `cat_frecsev.py`, `frecsev2.py`, `severidad_cfs.py`, `severidad_cfs3.py`, `cat_produccion.py`, `cat_experimento.py` y `linea_b/severidad_tendencia.py`; y los nombres de archivo `v24.parquet` y `prediccion_2025.parquet`.

- [ ] Llevar el calendario a un módulo `calendario.py` (primer año, año de selección, año de confirmación, año a predecir) leído por todos, con los valores de la parte 1 por defecto.
- [ ] Comprobar que con los valores por defecto `reproducir.py mezcla` y la reconstrucción siguen dando el SHA de S30 y S22: el cambio no debe mover un solo byte de la parte 1.
- [ ] Hacer lo mismo con las rutas fijas de `comun.py` (`F0RUN`, `BASESRUN` y la ruta por defecto de `HAKATON_SEMANA1`) y con las listas `LINES`, `PERILS` y `WEATHER_VARS`, que pueden cambiar si el mercado nuevo trae otros ramos, peligros o variables de clima.

## 2. Calidad de datos

Repetir cada comprobación de la parte 1 sobre los datos nuevos, sin suponer que los mismos defectos están o faltan:

- [ ] Claves: formato de `customer_id` y del resto de identificadores, cruces sin pareja (ID01).
- [ ] Exposición: convenciones mezcladas (año/365, año/360, días) y su efecto en el total (EXP01).
- [ ] Capitales: valores extremos, saltos de escala entre periodos de la misma póliza y umbrales por ramo (CAP00, CAP01, contrato D66). Los umbrales de 10 millones en edificios y 1 millón en contenidos son de la parte 1.
- [ ] Siniestros duplicados con otro `claim_id` (DUP01) y siniestros anteriores al primer periodo (PRE00).
- [ ] Variables con información posterior al inicio del periodo: `customer_service_contacts` y `renewal_decision` lo eran en la parte 1 (D50, REN00); medir el D² univariante de cada columna nueva y su distribución en entrenamiento frente a test.
- [ ] Contrato de disponibilidad de F0: asignar cada columna nueva a un bloque (F0 a F4, excluida, clave o etiqueta) antes de usarla.

Codex construye en N62 un productor de la capa base desde los originales con las ocho reglas; es la pieza que se reutiliza aquí, con los parámetros de la parte 2.

## 3. Etiqueta, IBNR y reservas

- [ ] Fecha de valoración: `CUTOFF` en `bases_actuariales.py` vale 30-12-2024 en la parte 1.
- [ ] Chain-ladder de conteos por peligro y mes de ocurrencia con los datos nuevos; comprobar que el patrón es estable entre cohortes y revisar los peligros de cola larga (en la parte 1, lesiones y hundimiento).
- [ ] Exposición efectiva por peligro y por ramo con las completitudes nuevas; la predicción sigue usando la exposición nominal y no recibe un segundo factor de IBNR (D70).
- [ ] Peso de la reserva de caso en el T0 de los años recientes y estrés de ±25 %, como en la parte 1.
- [ ] Si el mercado nuevo tiene menos historia o un desarrollo distinto, decidir antes de modelar cómo se combina con lo aprendido en la parte 1 (por ejemplo, credibilidad entre los patrones de desarrollo de los dos mercados) y dejarlo escrito.

## 4. Variables y componentes

- [ ] Reconstruir F0 y las variables F1, F2 y F4 con el corte del 1 de enero del año del periodo; F3 necesita una decisión nueva del participante para el mercado nuevo (en la parte 1, completo en autos y siete variables en hogar, D80).
- [ ] Reentrenar las familias de la parte 1 con parada temprana en el nuevo año de selección: LightGBM Tweedie del total, CatBoost Tweedie, frecuencia por peligro (CatBoost Poisson y aditiva) por severidad GLM. Los ajustes que dependen del tamaño de los datos (`min_data_in_leaf`, número de rondas) se revisan si el mercado nuevo es más pequeño.
- [ ] Revisar el tope de 15.000 CU de autos con recargo uniforme y las relatividades de severidad por capital y por vehículo: son estimaciones del mercado de la parte 1.
- [ ] Reestimar la tendencia anual de severidad por peligro; el tope de ±15 % se fijó con la parte 1 y debe fijarse de nuevo antes de mirar resultados si la inflación del mercado nuevo es otra.
- [ ] Probar, como hipótesis registrada, si las relatividades de la parte 1 sirven de punto de partida (offset o variable) en el mercado nuevo.

## 5. Mezcla y nivel

- [ ] Factores de nivel del año siguiente con los dos cortes nuevos (en la parte 1, media de los factores Tweedie óptimos de 2023 y 2024).
- [ ] Anclas de la regla s17: en la parte 1 son `CAT_motor_4s`, `S12h_edif_md1000` y `S08h_hogar_F3s2` (nombres fijos en `mezcla3.py` y `linea_b/nivel_b.py`); definir las de la parte 2.
- [ ] Pesos y forma de la mezcla con la misma regla de aceptación; la forma de tasa en hogar se quitó en la parte 1 porque solo ganaba en la cola (D86).
- [ ] Batería completa sobre el candidato: bootstrap pareado por cliente, dirección y región, semestres, reservas ±25 %, calibración por deciles y cuerpo frente a cola.

## 6. Entrega

- [ ] Receta nueva (`receta/receta_parte2.json`) y huellas esperadas, con la misma reconstrucción por SHA que la parte 1.
- [ ] CSV con `row_id,prediction` en el orden de la plantilla, todas las filas de los tres test, valores positivos.
- [ ] Selección final de la parte 2 marcada por el participante.
- [ ] Informe y video: completar la sección de adaptación (qué cambió, qué se reestimó, efecto medido) y decidir el idioma.
- [ ] Formulario final con los dos archivos de predicción, video, informe y enlace o archivo del repositorio, según indique la organización.
