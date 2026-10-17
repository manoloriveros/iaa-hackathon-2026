# CAP01: corrección autorizada de 2.073 capitales

El participante autorizó dividir por mil exactamente las 2.073 filas `prior_supported` de D34, solo en derivados, y dejar las demás pendientes. La lista queda congelada por `row_id`, tabla y hashes de la revisión. No se amplía al corregir filas que podrían convertirse en referencias para otros periodos.

Se parte de la capa D32, con customer_id y exposición ya preparados. Se crea una nueva corrida `capfix_*`: cuatro tablas de hogar con cambios exclusivos en sum_insured y dos copias byte a byte de autos. El catálogo identifica las once tablas; los cinco maestros/siniestros/plantilla siguen apuntando a originales. D32, D34 y sus bitácoras se conservan. `current_run.json` identifica el flujo histórico ID01/EXP01. El índice unificado `current_dataset.json` identifica la versión preparada vigente y se publica solo después de verificarla. `current_capital_correction.json` identifica la ejecución CAP01.

Desde `C:\dev\Hakaton`:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\correct_capitals.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\verify_capital_correction.py'
```

Cada ejecución parte de D32 y crea una corrida nueva; no vuelve a dividir una capa ya corregida. La función de transformación también es idempotente para la lista congelada: acepta el importe anterior o el ya corregido y rechaza cualquier otro. El verificador comprueba esa segunda aplicación sin escribir una versión adicional.

El registro de cada cambio conserva source_table, source_row, row_id, policy_id, cliente, dirección, old, new, divisor, regla, referencia anterior, importe y fechas de esa referencia, separación temporal, cociente resultante, hash del archivo de revisión y autorización. La bitácora consolidada está en ledger/all_capital_changes.csv y Parquet. Los 1.454 casos extremos restantes se guardan en tables/pending_capitals, con sus importes y motivos originales. Los retornos a escala habitual y todos los demás capitales conservan su valor.

La validación compara íntegramente esquema, filas, orden y todas las columnas ajenas a sum_insured; comprueba que el conjunto exacto de posiciones modificadas sea el aprobado, que cada importe sea old/1000, que la reversión recupere D32 y que no haya cambios en pendientes. Se comprueba el respaldo anterior contra datos de origen, la conservación de IDs/exposición, las copias de autos, los hashes de los once originales y los derivados previos, y los manifiestos D32/D34. El catálogo completo y la cobertura de test se validan antes de activar la capa.

Esta autorización aprueba la transformación de la cohorte; no confirma la unidad en el sistema generador ni acredita validación independiente. La decisión es una reparación inferida del proyecto y conserva los límites de D34. Cada corte temporal de modelado debe respetar la información disponible; no extender CAP01 mediante observaciones posteriores o por un nuevo score. La corrección del capital no modifica primas, siniestros o etiquetas ni implica dividir las predicciones por mil.

Referencias: D32, D34, solicitud explícita actual, Documentación IAA §2, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6. Codex genera y verifica el código; no hay llamadas externas de IA, entrenamiento, publicación o envíos por este flujo.
