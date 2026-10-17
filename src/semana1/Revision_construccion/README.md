# Revisión de los códigos T y W

Esta revisión compara historias de edificios antes y después de 2023. La pregunta es si los códigos son alias temporales de una misma clase observada. El nombre físico del material requiere una confirmación separada: el diccionario enumera brick, stone, timber y non-standard, pero no define T o W.

La decisión técnica es proponer `t,w -> tw_code` en un campo adicional `construction_type_harmonized`, conservando `construction_type` y todos los demás campos. La copia candidata queda fuera del catálogo activo. Revisar una equivalencia y preparar una alternativa verificable no se registra como aprobación humana de su activación. No se entrenan modelos ni se corrigen otros datos.

Desde C:/dev/Hakaton:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_construccion\analyze_construction.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_construccion\verify_construction.py'
```

Cada ejecución crea una carpeta nueva. El primer comando produce tablas completas de pares, cohortes, excepciones y ejemplos, dos Parquet candidatos con el campo adicional, su catálogo de once tablas y bitácoras de las filas agrupadas. El segundo comprueba los pares con una unión por fechas distinta al algoritmo de secuencia del análisis; compara la propuesta con los códigos originales sin normalizar; verifica todos los valores previos, la reversión por eliminación del campo nuevo, los capitales pendientes, hashes, gráficos y enlaces locales. El informe HTML incluye las tablas y un explorador de seis pólizas reales.

La inferencia usa solo X de entrenamiento de 2021–2024. X de 2025 se examina como confirmación y no determina el mapa. No se leen valores de siniestros ni se estiman efectos sobre el coste. La correspondencia retrospectiva se congela con fecha de disponibilidad de referencia 31 de diciembre de 2024. En un backtest anterior a conocer el cambio de 2023, el mapa no puede declararse conocido por el actuario sin una fuente previa: debe conservarse una variante con código literal y registrar cualquier adaptación de esquema basada en X de validación como tal.

Los conteos distinguen filas, transiciones, pólizas y direcciones. Las direcciones están anidadas en las pólizas; los dos análisis no son muestras independientes. Cero contradicciones en estos archivos no certifica que dos materiales sean físicamente iguales. El maestro de direcciones carece de versiones históricas.

La trazabilidad responde a IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6. Son referencias educativas del proyecto, no una certificación. La revisión es propia asistida por IA; la revisión humana y la validación independiente no se presumen.
