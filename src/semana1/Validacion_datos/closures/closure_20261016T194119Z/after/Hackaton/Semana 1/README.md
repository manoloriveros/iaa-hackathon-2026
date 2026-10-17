# Datos de la primera semana

Los once archivos originales están en Datos. La revisión del 16 de octubre comprobó que sus SHA-256 coinciden con la descarga oficial archivada en ../../Preparación/data/raw/iaa_2026_part1_20261016 y que pueden leerse por completo con PyArrow 26.0.0. El [contrato del reto](../REGLAS_2026.md) define el objetivo y los límites de uso.

Las rutas se consultan desde [el mapa del proyecto](../../RUTAS_PROYECTO.json). No modificar los originales. Guardar transformaciones, objetivos construidos y resultados en ubicaciones distintas, con su propia configuración y evidencia.

La plantilla contiene 626.639 filas, correspondientes a 254.986 de autos, 184.155 de edificios y 187.498 de contenidos. La revisión comprobó igualdad de conjuntos de row_id y ausencia de duplicados en los test y en la plantilla. Esto no acredita aún la asignación de siniestros a periodos, el desarrollo a último ni la calidad actuarial de las variables.

La [validación detallada y el diccionario actuarial](Analisis/README.md) añaden la revisión semántica de D30; se conservan los originales y se identifican propuestas de preparación pendientes.

La [limpieza trazable de claves y exposición](Limpieza/README.md) conserva seis tablas derivadas y un catálogo para leer las once tablas sin sustituir los originales. Cada cambio tiene bitácora por fila y verificación de reversión. La [corrección CAP01](Limpieza/CAPITALES.md) añade /1000 en las 2.073 filas autorizadas y conserva 1.454 capitales extremos pendientes. El índice preparado vigente es `Limpieza/current_dataset.json`; `current_run.json` conserva la referencia al flujo D32.

La [evaluación de Jev / TypeSafe](Validacion_IA/jev_20261016/evaluacion.html) registra una prueba en Chrome bloqueada por saldo cero, fuentes oficiales y un piloto preparado sin ejecutar. La recomendación es no recargar por ahora. Jev no intervino en las correcciones de los datos.

El [refinamiento de categorías y edades](Limpieza/REFINAMIENTO.md) unifica mayúsculas/minúsculas de construcción y recalcula años cumplidos del tomador de hogar desde su nacimiento al inicio de cobertura. La revisión multitabla conserva faltantes, los códigos de construcción sin definir y las demás incidencias semánticas; no añade correcciones de capitales.

La [revisión detallada de capitales](Revision_capitales/README.md) compara las historias de edificios y contenidos, presenta diez casos reales y define criterios propuestos para evaluar la escala. El informe permite buscar pólizas y consultar sus periodos. Distingue evidencia anterior, apoyo retrospectivo y carencias de contexto; no cambia capitales ni crea pólizas corregidas.

La [metodología actuarial de modelado](Modelado/METODOLOGIA_ACTUARIAL.md) define el coste observado y el objetivo último, las propuestas específicas para autos, edificios y contenidos, la disponibilidad de predictores y la validación temporal. El [protocolo estructurado](Modelado/protocolo_metodologico.json) fija la primera ronda de comparación y el [diagnóstico de soporte](Modelado/diagnosticos/actual.json) conserva evidencia sobre abiertos, retrasos y entidades conocidas. El catálogo de modelos sigue pendiente de ejecución.


La [revisión longitudinal de construcción T/W](Revision_construccion/README.md) respalda una clase común de código, sin confirmar el material físico. Su informe compara continuidades y mudanzas; añade una copia candidata con construction_type_harmonized, conservando los códigos anteriores. La candidata permanece fuera del catálogo activo de limpieza.


La revisión exhaustiva de validación se consulta en `Validacion_datos/current_run.json`: conserva 58 controles/decisiones, inventario de las 105 columnas y nuevos sondeos de duplicados semánticos de siniestros, calendario 2024–2025, coberturas y atributos de riesgo. Es una revisión con criterios de cierre; no modifica datos ni aprueba el conjunto para modelar.
