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

La [investigación independiente de Claude](Investigacion_tecnicas_claude/INFORME.md), D50, contrasta D37 con diagnósticos nuevos sobre DUP01 (dispersión de conteos, potencia Tweedie implícita por peligro, colas, retrasos, clima rezagado, historia propia, señal por bloque y deriva train/test) y 28 fuentes C01–C28. Mantiene la primera ola y propone comparar p=1,5 con p=1,9, componentes por peligro, calibración isotónica o autocalibración y EBM como GAM interpretable; recomienda excluir `customer_service_contacts` por contrato. Reproducción y verificación: `Investigacion_tecnicas_claude/diagnosticos_tecnicas.py` y `verificar_entrega.py` (11 de 11 controles con el catálogo PRE00 activo). Sin entrenamiento ni T0 operativo.

D52, CAP03R autorizado: once filas de contenidos /1000 sobre CAP02R, un nuevo respaldo test 2025 y 576 pendientes conservados, incluido C48613718 sin cambios. El índice retrospectivo apunta a la nueva capa; current_dataset.json permanece igual. Acumulado: 878 correcciones retrospectivas, 112 respaldadas por test 2025 y 2.951 capitales corregidos contando CAP01. [Informe y bitácora](../Limpieza/runs/capnumeric_20261016T215017Z_75a1fda5/informe.html). Aplicar/verificar/cerrar con apply_numeric_capitals.py, verify_numeric_capitals.py y finalize_numeric_capitals.py. Protocolo 1.7; solo escala, sin cambios en límites normales intermedios ni aprobación de backtest causal.

D54, CAP04R autorizado: 109 filas D53 /1000 sobre CAP03R (75 edificios y 34 contenidos), 17 respaldos posteriores de test 2025 (6/11) y 467 pendientes preservados. B19256617/B00962235 mantiene 377.000.000 CU y C48613718/C01596694, 29.300.000. La nueva capa conserva los demás campos, T/W y las reparaciones anteriores. Acumulado de 987 correcciones retrospectivas, 129 respaldos test 2025 y 3.060 correcciones contando CAP01. La base sigue intacta con 1.454 pendientes. Protocolo 1.8; reconstrucción retrospectiva sin aprobación causal por corte. [Informe y bitácora](../Limpieza/runs/capcontext_20261016T220924Z_4b397220/informe.html). Scripts: apply_context_capitals.py, verify_context_capitals.py y finalize_context_capitals.py; índice de operación current_context_capital_correction.json.
