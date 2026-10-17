# Revisión de capitales antes de decidir

Tras esta revisión, el participante autorizó CAP01 para las 2.073 filas con respaldo anterior. La [nueva capa y sus bitácoras](../Limpieza/CAPITALES.md) conservan D34 íntegro y dejan los demás capitales pendientes. El informe de esta carpeta sigue describiendo la evidencia y los valores anteriores a la corrección.

Este análisis compara las cuatro tablas de edificios y contenidos, 2021–2025. No cambia `sum_insured`, no genera una capa de pólizas corregidas y no modifica la limpieza D32. Los valores divididos por mil aparecen solo en campos `what_if` y figuras diagnósticas.

Desde la raíz del proyecto:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_capitales\analyze_capitals.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_capitales\render_capitals.py'
node '.\Hackaton\Semana 1\Revision_capitales\verify_report.js'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Revision_capitales\verify_capitals.py'
```

Cada ejecución del análisis crea una corrida nueva. `current_run.json` identifica la vigente. El análisis protege con hashes los once originales y las seis tablas derivadas de D32. Se conserva el código, el protocolo, la solicitud, las versiones y los resultados. La verificación es propia asistida por IA; la revisión humana sigue pendiente.

La comprobación JavaScript usa Node y un DOM mínimo para probar búsquedas, filtros y conservación de valores al consultar historias. No acredita renderizado real en navegador. Las figuras seleccionadas se inspeccionaron por separado. El índice vigente señala `capital_20261016T180903Z_bceb990c`: 31 controles de datos y seis de lógica del informe satisfactorios. El primer intento del verificador detectó que el informe enlazaba su resultado antes de crearlo; se corrigió la inicialización del resultado pendiente y se preservó el intento fallido. No se repitió el análisis de datos por ese ajuste.

Los filtros iniciales son más de 10 millones CU en edificios y más de 1 millón en contenidos. Son señales de revisión, no límites contractuales. Dentro de ese grupo se compara el capital con la referencia no extrema más cercana anterior y posterior de la misma póliza. Se comprueba identidad del cliente, dirección y campos declarados del riesgo y contrato. Para construcción solo se equipara mayúscula y minúscula; una abreviatura no definida no se interpreta como un material.

La propuesta de evidencia anterior exige campos comparables conocidos, contexto igual, periodo de referencia estrictamente previo, separación de inicios de hasta 400 días y continuidad del capital hipotético tras dividir por mil entre 0,90 y 1,10 de la referencia. Se muestran sensibilidades de 5%, 10% y 20%. Estas tolerancias son decisiones de diagnóstico, no probabilidades de error o normas del organizador. Tener evidencia anterior no equivale a aprobar una corrección.

Las filas posteriores permiten revisar retrospectivamente un pico. Deben distinguirse de la información disponible al cotizar esa fila. El informe identifica apoyos que cruzan de entrenamiento al test y no los convierte en validación temporal ni en variables predictivas. Las pólizas sin referencia normal y las que cambian de dirección o características requieren otra evidencia. Una subida con dos efectos (mudanza y escala) no justifica copiar el capital anterior. Dos capitales altos consecutivos tampoco se validan entre sí solo por tener un cociente cercano a uno.

La prima registrada se compara solo entre periodos largos de duración parecida y actúa como evidencia complementaria. Su base temporal no está especificada con suficiente detalle en el diccionario. No se anualiza ni se presume proporcionalidad con el capital. No se usan siniestros, predicciones o leaderboard para elegir qué capital cambiar.

El informe incluye casos reales y sus historias completas, una cola de revisión de cada fila extrema y las historias de las pólizas afectadas. Los ejemplos sin bandera extrema muestran por qué un capital alto o una variación legítimamente posible no bastan para dividir por mil. Las tablas auxiliares son evidencia de revisión; no son datos listos para entrenamiento.

Fuentes: diccionario oficial archivado en `Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md`, D30 y D32, y prácticas IAA priorizadas de Documentación §2, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6. No se declara confirmación del generador de datos, certificación profesional o validación independiente.
