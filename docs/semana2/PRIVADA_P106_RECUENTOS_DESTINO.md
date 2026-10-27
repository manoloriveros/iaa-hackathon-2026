# P106: recuentos observados preparados

Codex, 2026-10-27T11:04:51.727086+00:00.

Se reutilizaron las columnas de recuento del objetivo preparado; no se releyó o reasignó el inventario de siniestros. Las109296filas coinciden exactamente con las claves, año, grupos/folds, calendario y T0canónicos. Los céntimos coinciden por redondeo entero y Decimal. El coste objetivo permanece igual.

| Ramo | Año | Filas | Eventos aceptados | Eventos con coste positivo | Periodos con coste positivo | Aceptados sin coste positivo |
|---|---:|---:|---:|---:|---:|---:|
|motor|2023|21680|3557|3557|3027|0|
|motor|2024|25603|3491|3491|3064|0|
|buildings|2023|12580|519|519|497|0|
|buildings|2024|14867|537|537|514|0|
|contents|2023|15834|491|491|482|0|
|contents|2024|18732|507|507|487|0|

Un periodo positivo no equivale a un evento: se conservan varios siniestros por periodo y los aceptados de coste0. Son recuentos reportados y aceptados a la valoración2024-12-31, no frecuencia última ni una instantánea de lo conocido al inicio de cada póliza. Pasaron los casos adversos de claves, importes y tipos, sin entrenar.

La exposición de número de avisos y las vistas explícitas de frecuencia/marca de fuente todavía no están conectadas a esta ruta. Se retomarán los contratos P27/P29; P61ya documentó que fFSpnativo usó completitud de costes, por lo que no se reinterpretará como frecuencia última. También se conservan los resultados adversos de credibilidad y fuente anteriores. Preparar los recuentos no demuestra un nuevo modelo o una mejora privada.

Los aportes concurrentes revisados se trataron como evidencia, sin adoptar órdenes, sondas públicas, selección final o supuestos scores privados. Fuente, estado de siniestros/valoración, cola, transporte de mercado y búsqueda adaptativa siguen limitando la interpretación. Cero ajuste, CDF, inferencia, score o envío; B00 y alternativas preservados,2024abierto adaptativo, sin revisión profesional independiente.

Próximo: P107: design paired accepted-event count exposure for the new destination count path, using P27/P29definitions and current outer/inner group exclusions. Inspect existing source count-RKM support and q.cost_curves eligibility before implementing; count weights1must retain accepted cost0 events. Costweighted curves/caps cannot be silently reused as countCDF. Separate synthetic riskset/event enumeration and zero-exposure handling before any real CDFfit. Then registered historical P29frequency/mark export; no nativeFSpf-as-identified-frequency. No Poisson/cost model before complete paired-source/exposure recipe.
