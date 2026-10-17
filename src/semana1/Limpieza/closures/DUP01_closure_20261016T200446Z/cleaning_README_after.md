# Limpieza trazable de identificadores y exposición

La capa preparada vigente se identifica en [current_dataset.json](current_dataset.json). Incluye ID01/EXP01 de D32, la [corrección CAP01 de 2.073 capitales](CAPITALES.md) el [refinamiento CAT01/AGE01](REFINAMIENTO.md) de etiquetas y edad del tomador de hogar, y DUP01 en claims, identificado por [current_duplicate_application.json](current_duplicate_application.json). Los 1.454 capitales restantes siguen pendientes. El índice `current_run.json` y el procedimiento siguiente corresponden al flujo histórico D32; se conservan para reproducirlo y no activan por sí solos una versión posterior.

Los originales permanecen en `../Datos`. Cada ejecución crea una carpeta nueva en `runs`, seis tablas de pólizas derivadas, bitácoras de cambios por fila, un catálogo de las once tablas y una revisión de capitales sin correcciones. No usar una corrida sin `verification.json` satisfactorio. La revisión humana sigue pendiente.

Desde `C:\dev\Hakaton`, en PowerShell:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\clean_data.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\verify_cleaning.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\render_report.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\verify_artifacts.py'
```

Se usa PyArrow 26.0.0 de la caché aislada documentada en `Preparación/requirements.data-access.txt`. Las versiones efectivas quedan en `run.json`; el código se copia en `source_snapshot`. Las rutas del catálogo se resuelven desde la raíz del espacio de trabajo. Las tablas auxiliares y las bitácoras son evidencia, no predictores de una tarifa.

`ID01` rellena ceros a la izquierda hasta ocho posiciones. Rechaza claves ausentes, caracteres distintos de dígitos ASCII y longitudes mayores. El maestro debe ser único y todas las claves normalizadas deben existir en él. Varias representaciones del mismo código pueden converger en la misma entidad del maestro; no se fusionan dos claves distintas de este último.

`EXP01` reconstruye años de exposición como días cubiertos inclusivos / 365, redondeados a cuatro decimales, igual que el test. Es una decisión de preparación respaldada por la convención dominante, pendiente de confirmación del organizador. Un año completo de 366 días equivale a 1,0027; no se recorta a uno ni se divide ciegamente toda exposición por 365. Las fechas no cambian. Las bitácoras conservan los importes originales y la convención detectada. Para cada fila cambiada se acredita valor anterior, nuevo, clave, posición y regla. Los datos derivados no añaden campos que puedan confundirse con variables originales.

Los capitales se conservan. Los umbrales de 10 millones CU en edificios y 1 millón en contenidos solo seleccionan casos para revisar. También se señalan saltos de 900–1100 veces entre periodos consecutivos de una póliza, en ambas direcciones. La comparación exige que el periodo anterior termine antes del actual. La cola incluye test contra historia anterior; no usa siniestros ni futuras etiquetas. Una coincidencia de dirección o un salto cercano a mil no demuestra una unidad incorrecta. Revisar cambios de cobertura, dirección, objeto asegurado y el origen de la moneda antes de decidir.

Las verificaciones comparan íntegramente las columnas restantes, esquema, filas, orden, bitácoras y reversión; reconstruyen cada exposición mediante aritmética de fechas de Python; comprueban cobertura de la plantilla y hashes de los once originales. Son controles técnicos propios asistidos por IA. No certifican el objetivo último, IBNR, disponibilidad temporal de variables ni aprobación para modelar. Referencias: D30, Documentación IAA §2 y Gobernanza §§2.8–2.10.


DUP01 conserva 162.546 siniestros y excluye exactamente los 604 IDs autorizados, manteniendo sus representantes de ocho dígitos y todos los valores restantes. La nueva corrida guarda exclusion_ledger CSV/Parquet, claim_id_aliases CSV/Parquet y excluded_rows.parquet con los tipos originales para revertir. Se aplica con apply_duplicates.py y se verifica/publica con verify_duplicate_application.py. La segunda llamada al aplicador sobre la capa verificada es un no-op. Las otras diez referencias del catálogo, todos los originales y los capitales se conservan.
