# Validación e interpretación actuarial de datos

El [informe completo](runs/eda_20261016T165629Z_ab2a8365/informe.html) reúne las once tablas, 105 nombres de columna, 242 apariciones físicas, 116 gráficos y las comprobaciones de calidad. Incluye un buscador por columna o concepto, fichas desplegables y tablas con denominadores.

La ejecución es una revisión propia asistida por IA, con revisión humana pendiente. No es validación independiente ni aprobación del conjunto para entrenar. Los originales permanecen intactos; las transformaciones y proxies son derivadas.

## Qué cambió al entender los datos

- La exposición registrada combina convenciones y cantidades con escala de días. Se conserva el cálculo original y se contrasta con duración inclusiva / 365. Esta segunda base se usa como escenario de sensibilidad en los gráficos; no es una corrección aprobada ni se alteró el test.
- Un relleno de ceros iniciales hasta ocho posiciones recupera los cruces de clientes fallidos de autos: 98.110 filas históricas y 25.554 del test. La comprobación es contra claves únicas del maestro; la transformación sigue identificada como candidata.
- Hay capitales con saltos cercanos a 1.000 veces la mediana de la misma póliza, y variantes o abreviaturas de construcción. Se conservan ejemplos reales y la diferencia entre equivalencias claras y códigos sin confirmar.
- Los 414 siniestros que no entran en un periodo observado son anteriores al primer periodo de su póliza. No se fuerzan dentro del objetivo actual. Pueden ser antecedentes o cobertura fuera de la ventana disponible; falta aclarar su papel.
- Incurrido al corte no equivale a último. Las asociaciones mostradas no ajustan confusión, selección o desarrollo y no deben usarse directamente como factores de tarifa.

## Evidencia y reproducción

Las entradas se identifican por SHA-256 en input_hashes.json. Las tablas CSV están dentro de tables; claims_diagnostic y observed_proxy son Parquet derivados. La proxy agrega incurrido neto de recuperaciones de siniestros aceptados asignados a un único periodo. No contiene etiquetas últimas observadas ni predicciones ajustadas.

Desde la raíz C:/dev/Hakaton, con el lector aislado y las dependencias de Preparación disponibles:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/audit_data.py'
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/additional_checks.py'
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/join_focus.py'
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/calendar_sensitivity.py'
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/render_report.py'
& '.\Preparación\.venv\Scripts\python.exe' 'Hackaton/Semana 1/Analisis/verify_analysis.py'
```

audit_data crea una carpeta nueva y actualiza current_run.json. Los demás pasos completan esa ejecución. Para cambiar solo la presentación, IAA_REUSE_FIGURES=1 permite reutilizar las figuras por columna; no usar esa opción después de modificar datos o cálculos. No repetir el cálculo pesado por cambios exclusivamente editoriales.

analysis_verification.json comprueba hashes de entrada contra el manifiesto previo, cobertura de columnas, conservación de importes, identidades de frecuencia y severidad, reconciliación de segmentos y estructura de HTML e imágenes. No prueba causalidad ni calidad del objetivo último. Se inspeccionaron visualmente gráficos seleccionados. La interacción del HTML en navegador no se verificó: la política de la herramienta bloqueó el protocolo file y no se buscó un rodeo.

Los archivos de runs contienen datos y resultados derivados del concurso y quedan excluidos de Git. La política del proyecto exige comprobar permisos antes de compartirlos. No se publicó el informe ni se hicieron envíos.
