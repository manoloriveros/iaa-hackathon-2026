# Mi proyecto para el AI Hackathon IAA 2026

Soy Manuel Rodríguez y participo de forma individual. En estas dos semanas construí una cadena de tarificación para un mercado desarrollado y la adapté a un mercado emergente con menos historia y una entrada fuerte de negocio nuevo. Usé Claude y Codex para explorar los datos, programar alternativas, contrastar decisiones y preparar la documentación. Las decisiones de entrega son mías; las comprobaciones realizadas por IA conservan esa atribución.

Mi objetivo es estimar el coste último esperado de los siniestros de cada periodo de póliza de 2025, neto de franquicias y recuperaciones y sin siniestros rechazados. Predigo el importe del periodo cubierto. La prima comercial de las veinte pólizas de referencia se calcula después, con los gastos y recargos suministrados por el concurso.

## Cómo reproduzco las dos entregas

He reunido el código y la configuración en dos notebooks autocontenidos. Para ejecutarlos necesito los datos oficiales de la competición; los notebooks crean un espacio de trabajo nuevo y no descargan mi repositorio ni cargan modelos o predicciones anteriores.

| Semana | Notebook | Entrega que reconstruyo |
| --- | --- | --- |
| Mercado desarrollado | [week1_developed_market.ipynb](notebooks/week1_developed_market.ipynb) | Mezcla S30 y calibración de nivel S41 |
| Mercado emergente | [week2_emerging_market.ipynb](notebooks/week2_emerging_market.ipynb) | Cadena F3c y primas comerciales de las veinte referencias |

Empiezo por la [guía de los notebooks](notebooks/README.md), donde explico entradas, entorno, recursos y verificaciones. En Kaggle adjunto los datos de la semana correspondiente, uso una sesión CPU y sigo el orden de las celdas. También puedo indicar carpetas locales mediante las variables de entorno descritas en la guía. Los datos, modelos y registros intermedios se guardan en una carpeta temporal; las salidas por fila siguen siendo restringidas.

Mis recetas reconstruyeron los CSV históricos en ejecuciones locales reanudadas. En semana 1 quedaron diferencias intermedias, incluidas tres huellas de tablas de variables cuya causa no se estableció. En semana 2 se recuperó el CSV F3c exacto. No he acreditado una ejecución alojada en Kaggle ni un Run All ininterrumpido de ambos notebooks. Conservo esas diferencias y las interrupciones en el [registro de reproducción](registro/notebooks_kaggle_actual.json); no presento este trabajo asistido como revisión profesional independiente.

## Mi video de entrega

Presento mi [video en inglés de 4:59](https://www.youtube.com/watch?v=AYLkpDmZfZo) como enlace del formulario. En el [registro del video](registro/video_entrega_actual.json) conservo la versión local elegida y el alcance de la comprobación del enlace.

## Qué elegí y por qué

Para la primera semana elegí S41. Mantengo la mezcla por peligro S30 y ajusto su nivel de 2025 con una regla de credibilidad documentada. Esa decisión conserva los ensayos posteriores y sus resultados adversos; no depende de elegir el mayor marcador público. Explico la arquitectura en [MODELO_FINAL_S41.md](docs/MODELO_FINAL_S41.md) y la elección en [DECISION_FINAL_S41.md](docs/DECISION_FINAL_S41.md).

Para la segunda semana confirmé F3c como definitivo el 28 de octubre. Combino la transferencia del mercado desarrollado con la información disponible en el emergente y una calibración residual documentada. La comparación posterior con F3c-R no cumplió los criterios conjuntos registrados, por lo que mantuve F3c. La [decisión](registro/semana2_decision_final_F3c_20261028.json) y el [cierre de la comparación](docs/semana2/F3C_REGULARIZADO_CIERRE_20261028.md) conservan el alcance de esa elección. No la interpreto como garantía de superioridad privada o aprobación de una tarifa operativa.

## Cómo trabajé con IA

Usé los asistentes para proponer reglas de datos, escribir código, cuestionar la disponibilidad temporal de variables, comparar recetas y construir verificadores. Conservé hipótesis, fuentes, cambios y resultados adversos en el expediente. También usé IA para explicar el método, traducir y preparar materiales audiovisuales. No medí un ahorro de horas que pueda atribuirle.

Distingo una decisión mía, una comprobación automática y una revisión independiente. Que otra sesión de IA repita un cálculo aporta evidencia técnica, pero no la convierto en una revisión humana. En [mi flujo de trabajo con IA](docs/entrega/USO_DE_IA_ES.md) detallo las aportaciones y cómo las contrasté en el proyecto.

## Dónde está cada parte

| Consulta | Entrada |
| --- | --- |
| Métodos, decisiones y documentación vigente | [Guía documental](docs/README.md) |
| Archivos locales, video y comprobaciones de acceso | [Guía del formulario](docs/entrega/FORMULARIO_FINAL.md) |
| Reproducción de las recetas originales | [Semana 1](docs/REPRODUCCION_COMPLETA.md) y [semana 2](docs/REENTRENAMIENTO_ORIGINALES.md) |
| Uso de IA en inglés | [AI_WORKFLOW_EN.md](docs/entrega/AI_WORKFLOW_EN.md) |
| Versiones y acceso al código | [Control de versiones](docs/CONTROL_DE_VERSIONES.md) |
| Propuestas y revisiones anteriores | [Archivo documental](docs/archivo/README.md) |

En mi espacio local, `Hackaton/Entrega_final` reúne el informe español vigente, los dos CSV, los notebooks y el video inglés de solo voz. El PDF con primas por póliza, los datos y las salidas individuales se mantienen fuera de Git. La licencia MIT del código y la documentación se explica en [NOTICE.md](NOTICE.md).

Identifico este paquete de código con la etiqueta `entrega-codigo-20261029`. El [registro de sincronización](registro/sincronizacion_github_actual.json) conserva las comprobaciones y la confirmación remota. Mantengo el repositorio privado hasta la apertura prevista después del cierre; debo confirmar el acceso del jurado. La [revisión de entrega](registro/revision_entrega_actual.json) conserva los límites de reproducción y la traducción inglesa pendiente del informe.
