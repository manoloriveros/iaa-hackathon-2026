# Matriz F0, contrato de disponibilidad y particiones

Carpeta de Claude (Cowork), a solicitud del participante (17 de octubre de 2026; decisión D68 en `Preparación/DECISIONES.md`). Cumple de forma preliminar las tareas T02 y T03 del plan de pruebas D67 (`../Bases_actuariales_claude/PLAN_PRUEBAS.md`): una matriz por ramo con todas las filas de entrenamiento 2021–2024 y de test 2025, un contrato que dice para cada columna a qué bloque de información pertenece y por qué, las etiquetas T0 por fila y por peligro, la exposición efectiva por peligro y las particiones V22, V23, V24 y producción. No modifica datos ni índices y no entrena modelos.

| Archivo | Qué es |
| --- | --- |
| `construir_f0.py` | Lee la capa vigente (`current_dataset.json`) y la corrida vigente de `Bases_actuariales_claude`, comprueba hashes y escribe la corrida; admite ejecución completa o por partes (`--ramo`, `--run`, `--finalizar`) |
| `verificar_entrega.py` + `cifras_f0.json` | Comprobación de manifiesto, controles, capa vigente, contrato, filas y 30 cifras; escribe `verification.json` |
| `current_run.json` | Corrida vigente |

En la corrida: `tables/f0_motor.parquet` (1.234.954 filas, 108 columnas), `tables/f0_buildings.parquet` (891.881, 105), `tables/f0_contents.parquet` (909.115, 99), cada una con un grupo de filas por año; `tables/particiones.parquet` (3.035.950 filas con `row_id`, ramo, año, `cal_half` y las columnas V22, V23, V24 y PROD); `contrato_disponibilidad.json`; `evidencia.json`; los tres parciales por ramo, las piezas de partición y `manifest.json`.

## Qué hay en cada matriz

Las columnas originales de la póliza, el maestro de clientes y el de direcciones unidos por `customer_id` y `address_id`, el clima del año anterior en la dirección (sufijo `_prev1`; nulo en 2021 porque el archivo empieza en 2021), dos variables de historia (`f1_notificaciones_previas` y `f1_dias_desde_ultima_notificacion`, con notificaciones reportadas antes del 1 de enero del año del periodo, el mismo corte en entrenamiento y test), la exposición efectiva por peligro (`e_ef_<peligro>`) y ponderada por coste (`e_ef_coste`), y las etiquetas `T0`, sus componentes y `y_<peligro>`/`n_<peligro>` (nulas en test).

El contrato asigna cada columna a un bloque: F0 contractual y físico (la matriz base), F1 historia, F2 clima rezagado, F3 información condicionada sin fecha (atributos del maestro de clientes, telemática, impagos), F4 tarifario (prima escrita y descuento), `excluida`, `clave` o `etiqueta`. Quedan excluidas por contrato `customer_service_contacts` (D50), `renewal_decision` y `audit_ren00` (D45), el apellido, el `construction_type` original (se usa `construction_type_harmonized`, con t y w unificados en `tw_code`), `sum_insured_raw` y las tres marcas de capital. El selector que use el runner debe leer el bloque desde el contrato y rechazar `excluida`, `clave` y `etiqueta`, además de lo que ya rechaza el guard 1.0.

## Capital, exposición efectiva y particiones

El capital sigue el contrato de D66: `sum_insured` es el valor leído entre mil cuando supera el umbral del ramo, con el original en `sum_insured_raw`. Se ajustan 1.454 filas (691 de edificios y 763 de contenidos, 190 de ellas en el test), las mismas que la base deja pendientes; 1.305 tienen confirmación por historia (rama CAP02R a CAP06R o lista autorizada en D66) y 149 son las de PRM01-R.

La exposición efectiva multiplica la exposición EXP01 por la completitud media del periodo, ponderada por días, del chain-ladder de D67: para 2021 y 2022 es casi la nominal y para 2024 queda en 0,7947 de la nominal en autos (lesiones corporales pesa el 41,36 % del coste del ramo), 0,9259 en edificios y 0,969 en contenidos; en 2025 es igual a la nominal. En frecuencia se usa como offset de entrenamiento; en predicción se usa `exposure`.

Las particiones siguen la metodología: V22 entrena 2021 y evalúa 2022; V23 entrena 2021–2022 y divide 2023 en calibración (312.840 filas) y selección (313.515) con el hash `cal_v1|customer_id`, de modo que cada cliente cae en una sola mitad; V24 entrena 2021–2023 (1.783.121 filas) y evalúa 2024 (626.190); PROD entrena 2021–2024 (2.409.311) y predice 2025 (626.639).

## Cómo reproducir

En Windows, con el entorno del proyecto y sin límite de tiempo:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Matriz_F0_claude\construir_f0.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Matriz_F0_claude\verificar_entrega.py'
```

La corrida vigente se hizo por partes en la VM Linux local (3,9 GB de memoria, llamadas de tres minutos): `--ramo motor` (46 s, 2,2 GB de pico), `--run <id> --ramo buildings,contents` (56 s) y `--run <id> --finalizar` (13 s). Dos corridas anteriores del mismo día quedan como historial: la primera se quedó sin memoria al unir los maestros sobre la tabla completa de autos y la segunda tenía una tolerancia de control que no absorbía el redondeo de EXP01. Ambas se describen en `current_run.json`.
