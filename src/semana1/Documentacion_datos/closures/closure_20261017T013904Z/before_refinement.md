# Categorías, edad y revisión de calidad después de CAP01

Se parte de la capa CAP01, sin cambiar sus capitales, claves o exposiciones. Cada ejecución crea una versión nueva, conserva los once originales y los seis derivados anteriores por hash y activa el catálogo solo tras verificarlo. La instrucción del participante es continuar el análisis y ajuste de datos; la restricción de dejar los otros capitales pendientes se conserva.

CAT01 unifica variantes de mayúsculas/minúsculas de construction_type: Brick y BRICK a brick, NON_STANDARD a non_standard, STONE a stone, T a t y W a w. Los códigos t/w se conservan como distintos y sin significado material confirmado. La normalización no los convierte en timber ni supone una equivalencia física entre ambos.

AGE01 recalcula policyholder_age de hogar como años naturales cumplidos desde customers.date_of_birth hasta period_start. Es una variable derivada con definición explícita en el diccionario. El maestro único y completo de nacimiento se adopta como referencia del proyecto; esto no es una confirmación externa de cada nacimiento. El campo anterior queda en la bitácora. Se rechazan fechas faltantes/futuras y diferencias mayores a un año. No se cambia driver_age de autos, pues puede corresponder a otra persona. Una fecha de inicio 28 de febrero de año no bisiesto para un nacimiento 29 de febrero exigiría revisar la convención; no se encontró ese caso en esta versión.

No se rellenan nulos ni se recortan NCB, edades de conductor, capitales o siniestros por reglas no confirmadas. Se revisan vocabularios, rangos documentados, valores no finitos, cardinalidades, periodos, fechas, telemática, coherencia de new_business, edad y asignación de siniestros. Los resultados separan fallos estrictos de la revisión semántica y los faltantes esperados. Las bitácoras y tablas de excepciones no son predictores.

Desde la raíz:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\refine_data.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\verify_refinement.py'
```

La ejecución guarda tablas nuevas, bitácoras tipadas por campo y una bitácora consolidada (old/new como texto, con value_type), diagnósticos, fuente oficial, código y hashes. La reversión se valida con la bitácora tipada. Los análisis no entrenan, imputan, publican o llaman a proveedores de IA. La revisión es propia asistida por IA, sin validación independiente. Las referencias IAA aplicadas son Documentación §2, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6.
