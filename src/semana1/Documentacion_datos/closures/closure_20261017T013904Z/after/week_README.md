# Datos y documentación de la primera semana

La [documentación consolidada](Documentacion_datos/README.md) explica todo el recorrido de los datos hasta D61. Incluye [dossier de lectura](Documentacion_datos/runs/dossier_20261017T013104Z_47591209/informe.html), [versión editable](Documentacion_datos/runs/dossier_20261017T013104Z_47591209/DOCUMENTACION_DATOS.md), [diccionario de 107 campos](Documentacion_datos/runs/dossier_20261017T013104Z_47591209/diccionario.html), [58 controles de seguimiento](Documentacion_datos/runs/dossier_20261017T013104Z_47591209/validaciones.html) y fuentes con hashes.

## Entradas vigentes

Los once Parquet originales están en Datos, y la descarga/ZIP se conservan en Preparación/data/raw/iaa_2026_part1_20261016. Las rutas se resuelven con [RUTAS_PROYECTO.json](../../RUTAS_PROYECTO.json) desde C: /dev/Hakaton. No se reescriben originales o corridas cerradas.

| Entrada | Contenido | Pendientes de capital |
| --- | --- | --- |
| [Base preparada](Limpieza/current_dataset.json) | ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00 | 1.454 |
| [Rama retrospectiva](Limpieza/current_retrospective_dataset.json) | Base más CAP02R a CAP06R; 3.108 capitales corregidos totales | 419 |

Los índices de datos apuntan a catálogos con rutas y SHA256. Los demás current_* identifican operaciones o revisiones concretas. La rama retrospectiva no está aprobada para backtests causales; ninguna entrada marca aprobación completa para modelar. Protocolo 1.10; T0/F0 y particiones operativas siguen pendientes.

## Evidencia por tema

| Tema | Referencia |
| --- | --- |
| Contrato archivado del reto | [Reglas](../REGLAS_2026.md) |
| EDA y diccionario inicial D30 | [Análisis de originales](Analisis/README.md) |
| Claves, exposición y catálogo base | [Limpieza](Limpieza/README.md) |
| Capitales y bitácoras | [CAP01 e historial posterior](Limpieza/CAPITALES.md) |
| Categorías y definición de edad | [CAT01 y AGE01](Limpieza/REFINAMIENTO.md) |
| Construcción T/W | [Revisión y candidata CON01 fuera de catálogo](Revision_construccion/README.md) |
| Siniestros duplicados | [Revisión](Revision_duplicados/current_run.json) y [DUP01 aplicado](Limpieza/current_duplicate_application.json) |
| Calendario y 31-12-2024 | [Revisión con fechas pendientes](Revision_calendario/current_run.json) |
| Rechazos con continuidad | [Revisión](Revision_rechazos/current_run.json) y [REN00 aplicado](Limpieza/current_renewal_audit_application.json) |
| Siniestros anteriores a la primera cobertura observada | [Revisión](Revision_prehistoria/current_run.json) y [PRE00 aplicado](Limpieza/current_prehistory_audit_application.json) |
| Dos ampliaciones y renovaciones | [Revisión D60](Revision_ampliaciones_capital/current_run.json) y [CAP06R aplicado](Limpieza/current_endorsement_capital_correction.json) |
| Riesgos de datos y pendientes | [Auditoría histórica D40](Validacion_datos/current_run.json) y [registro al cierre](Documentacion_datos/runs/dossier_20261017T013104Z_47591209/validaciones.html) |
| Jev/TypeSafe | [Evaluación sin financiación ni decisiones recibidas](Validacion_IA/jev_20261016/evaluacion.html) |
| Objetivo, predictores y validación | [Metodología](Modelado/METODOLOGIA_ACTUARIAL.md) y [protocolo](Modelado/protocolo_metodologico.json) |
| Investigación D50 de Claude | [Diagnósticos y fuentes](Modelado/Investigacion_tecnicas_claude/INFORME.md) |
| Segunda implementación D59 | [Informe histórico hasta CAP05R](Validacion_ajustes_claude/INFORME.md) y [dashboard bilingüe](Validacion_ajustes_claude/dashboard.html) |

## Cómo interpretar los estados

AGE01 fija edad al inicio de cobertura; no demuestra que todas las edades originales fueran errores. D59 explica 2.934 de 2.936 diferencias y deja dos sin explicar. CAT01 normaliza caja sin unificar T/W. DUP01 está aplicado a 604 pares; los 57 grupos no idénticos se conservaron. REN00 y PRE00 son marcas de auditoría, nunca predictores.

D30/D40 usan sus catálogos históricos; D56 reconcilia estados sin repetir todos los controles; D59 es una segunda implementación asistida por IA hasta CAP05R, sin revisión humana independiente. CAP06R tiene su propia verificación posterior. customer_service_contacts debe excluirse antes de entrenar y aún pasa el guard 1.0. No se consideran cerradas las brechas por documentarlas.
