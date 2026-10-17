# Modelado actuarial de la primera semana

La guía vigente es [Objetivo actuarial y validación para la tarificación multirramo](METODOLOGIA_ACTUARIAL.md). Define qué predecimos, cómo construir la referencia observable, qué supuestos requiere estimar el último y cómo comparar modelos en autos, edificios y contenidos.

El [protocolo metodológico](protocolo_metodologico.json) fija T0, las sensibilidades de reservas y reporte, los bloques de predictores y los cortes V22, V23 y V24. El [catálogo de candidatos](experimentos.json) organiza familias de modelos; no es una configuración ejecutable del runner.

La [investigación por ramo y peligro](Investigacion_tecnicas/INFORME.md), D37, amplía la comparación de métodos tradicionales, aprendizaje automático e híbridos con 23 fuentes primarias y un diagnóstico actualizado sobre CAP01/CAT01/AGE01, D38. Justifica prioridades, incorpora duración y componentes por peligro, y amplía el catálogo de 17 a 22 candidatos propuestos. Incluye tablas de concentración de costes, reservas, ceros, exposición y campos disponibles; no presenta un ranking medido de modelos.

La [evidencia del diagnóstico](diagnosticos/actual.json) resume datos de los originales y derivados verificados. Para repetir la inspección sin entrenar, desde C:/dev/Hakaton:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Modelado\diagnostico_objetivo.py'
```

Cada ejecución guarda una carpeta nueva con estadísticas agregadas, procedencia por hash y copia del script. El índice actual corresponde a la corrida revisada; repetir el comando no lo sustituye automáticamente.

El siguiente trabajo es materializar la asignación, la tabla T0, la matriz contractual y las particiones. La documentación no acredita que esos artefactos de entrenamiento ya estén construidos ni que exista un modelo puntuado.


El protocolo 1.3 lee claims DUP01 desde el catálogo preparado. El diagnóstico recalcula asignación y agregados con esa misma capa, sin reutilizar importes de las proxies D30. Conserva los diagnósticos anteriores y distingue 413 registros fuera de historia en la capa actual frente a 414 antes de DUP01. El cambio no entrena modelos ni materializa T0 operativo.

REN00, D45: protocolo 1.4 y marca audit_ren00 en seis derivados. renewal_decision y audit_* quedan excluidos por el selector real iaa_lab.data.feature_frames y el guard de predictores. [Verificación e informe](../Limpieza/runs/renaudit_20261016T203904Z_657dd741/informe.html). No se completa F0/T0 ni se entrena. El diagnóstico anterior conserva su snapshot DUP01; no se repite porque ninguna columna previa cambió.

PRE00, D47, protocolo 1.5: audit_pre00 en claims conserva 413 expedientes y separa su coste de los periodos actuales. El diagnóstico real aplica target_scope.assert_prehistory_excluded antes de agregar costes y se verificó igualdad exacta de todos los periodos; no se materializa T0 ni se entrena. [Informe y conciliación](../Limpieza/runs/preaudit_20261016T211816Z_817285a5/informe.html). El índice del diagnóstico histórico D42 conserva su snapshot y no se atribuye a esta capa; las nuevas pruebas del consumidor están en el informe PRE00.

D49, CAP02R autorizado en una capa retrospectiva separada: 867 capitales /1000, 111 con ancla test 2025 y 587 pendientes conservados. Consultar ../Limpieza/current_retrospective_dataset.json para esa versión. current_dataset.json conserva la base anterior (1.454 pendientes), sin adoptar información futura de forma automática. [Informe y bitácora](../Limpieza/runs/capretro_20261016T213644Z_9b52ecc4/informe.html). Protocolo 1.6; no se aprueba uso en backtests por fecha ni se entrena.
