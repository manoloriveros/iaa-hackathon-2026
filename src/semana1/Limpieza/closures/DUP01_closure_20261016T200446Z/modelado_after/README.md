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
