# Aplicación de las referencias IAA al proyecto

Fecha: 13 de octubre de 2026, America/Bogota. Esta matriz adapta las referencias a la preparación individual del hackathon. Es una decisión de trabajo del participante, no una lista que certifique cumplimiento profesional. Cada caso requiere justificar qué consideraciones aplican y por qué.

Las páginas citadas son las impresas en el cuerpo del documento. Para estos tres PDF, sumar 3 para encontrar la página del visor: la página impresa 1 es la página PDF 4. La declaración editorial está en la página PDF 2.

| Referencia y localización | Práctica que priorizamos | Evidencia que prepararemos en este proyecto |
| --- | --- | --- |
| [Consideraciones profesionales](AITF_Professional_Considerations_Paper_Final_Approved.pdf), §3.1, pp. 4–6 | Delimitar propósito, usuarios, complejidad y límites. | Contrato del reto con decisión actuarial, entradas, unidades, alcance y situaciones fuera de uso. |
| Consideraciones profesionales, §3.2, pp. 7–8 | Comprobar que el destinatario entiende las salidas. | Explicación de una salida real y comprobación de comprensión cuando exista un revisor. SHAP por sí solo no acredita esa comprensión. |
| Consideraciones profesionales, §3.3, pp. 8–10 | Examinar sesgos, resultados desiguales y variables que actúan como proxies. | Comparaciones por segmentos pertinentes, tamaños de muestra, incertidumbre y decisión sobre mitigación. Declarar límites si faltan datos. |
| Consideraciones profesionales, §3.4, pp. 10–11 | Proteger datos y revisar el uso de proveedores. | Inventario de información enviada a IA, permisos, restricciones y controles aplicables; secretos fuera de prompts y entregables. |
| Consideraciones profesionales, §§3.5–3.6, pp. 11–14 | Mantener responsabilidad humana y comunicar el uso de IA. | Prompts vinculados a decisiones, correcciones y revisión real; explicar al jurado qué hizo la IA y qué comprobó el participante. |
| Consideraciones profesionales, §§3.7–3.8, pp. 14–16 | Reconocer la competencia necesaria y sus límites. | Registrar las partes que requieren conocimiento especializado, formación o revisión adicional; evitar atribuir al estudiante acreditaciones no comprobadas. |
| [Gobernanza](AITF_Governance_Framework_Paper_Final_Approved.pdf), §§2.5–2.7, pp. 7–9 | Definir responsables y graduar controles según impacto. | Registro de riesgo por componente con consecuencia, responsable, control y evidencia; justificar la clasificación sin inventar umbrales IAA. |
| Gobernanza, §2.8, pp. 9–11 | Distinguir validación propia de validación independiente. | Informe de validación con criterios, resultados y limitaciones. Las comprobaciones del autor y de IA se etiquetan según su procedencia. |
| Gobernanza, §§2.9–2.10, pp. 11–12 | Evaluar dependencias externas y supervisión humana. | Versión y condiciones del proveedor, pruebas de sus salidas, puntos de intervención y respuesta ante una salida inválida. |
| Gobernanza, §§3.3.2, 3.4–3.6, pp. 19–24 | Validar el flujo y planear revisión, cambios y retirada. | Casos difíciles, sensibilidad y criterios de aceptación; plan de seguimiento con desencadenantes y alternativa de recuperación antes de un uso real. |
| [Documentación](AITF_Documentation_AI_Models_Paper_Final_Approved.pdf), §2, pp. 1–3 | Mantener una ficha de datos y su recorrido. | Fuente, periodo, diccionario, propietario conocido, permisos, transformaciones, calidad, representatividad y limitaciones, enlazados a archivos identificables. |
| Documentación, §3, pp. 3–5 | Mantener una ficha del modelo con decisiones y evidencia. | Propósito, dependencias, aportación de IA, algoritmos, parámetros efectivos, folds, comparación, supuestos, interpretación y cambios con sus motivos. |
| Documentación, §§4–6, pp. 5–8 | Documentar operación, uso y riesgos para el destinatario. | Entorno, comandos, entradas y salidas de referencia, fallos conocidos, instrucciones de adaptación, versiones y estado real de revisión o aprobación. |

## Cómo se incorpora al trabajo

Antes de aceptar una propuesta, registrar la tarea que mejora, la referencia pertinente y la evidencia necesaria para evaluarla. Si una práctica no aplica, explicar el motivo. Mantener abierta una carencia material hasta resolverla o limitar el alcance respaldado.

El dossier candidato incluirá una ficha de datos, una ficha del modelo o sistema, la evaluación de riesgos y una guía de reproducción y uso. Su contenido dependerá del reto oficial. Estos entregables están planificados; este archivo no los presenta como terminados.

El participante trabaja solo. No se trasladan al proyecto comités corporativos ficticios ni se declara una revisión independiente inexistente. Una revisión externa necesitaría una persona competente, evidencia conservada y compatibilidad con las reglas de colaboración. Este acuerdo tampoco autoriza contactar a terceros ni delegar trabajo.

## Evidencia disponible y carencias

La trazabilidad v2 conserva configuraciones, folds, OOF, modelos, snapshots y conversaciones. La referencia histórica `artifacts/readiness_v2.json` acredita un ensayo sintético en Windows con 37 pruebas y notebooks local y Kaggle simulado. No acredita cumplimiento de esta matriz, rendimiento competitivo, revisión humana de un modelo final ni reproducción independiente.

Faltan las reglas completas y los datos de 2026, las fichas específicas del caso, pruebas profesionales sobre el candidato y un plan de seguimiento ajustado al uso. La prioridad documental quedó incorporada; la aplicación efectiva se acreditará con artefactos futuros.

Conservar las referencias originales. Al usarlas como contexto, incluir los fragmentos efectivamente enviados en `messages` y archivar la versión correspondiente; `context_files` por sí solo no envía un PDF al modelo.
