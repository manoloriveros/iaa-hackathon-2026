# F02: construcción, uso, desocupación, alarmas y franquicias en 2023

Codex, corte UTC 2026-10-24T14:52:28.670443+00:00. La revisión no acredita por sí sola que ninguno de los seis valores estuviera disponible en una cotización concreta. Cinco campos tienen significado físico/contractual definido y podrían conocerse al declarar o aceptar el riesgo, bajo condiciones que deben quedar explícitas. days_unoccupied además carece de ventana de medición documentada: se retiene para cualquier nueva admisión prospectiva hasta aclararla. No se detectó ni se afirma una fuga realizada a partir de sus valores.

Se consultó el [diccionario oficial de Kaggle](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data), sin cambios respecto al archivado, el contrato de disponibilidad y el código fuente. Del Parquet original de edificios se inspeccionaron solo nombres/tipos de columnas. No se cargaron filas, calcularon distribuciones o cruzaron siniestros, costes, predicciones, grupos o bandas; tampoco se repitieron diagnósticos.

## Hallazgos por campo

| Campo | Significado comprobado en documentación/esquema | Disponibilidad para una cotización 2023 |
| --- | --- | --- |
| construction_type | Material/tipo de construcción; distinto de la tipología de inmueble property_type. | Condicional, sin sello temporal probado |
| occupancy | Uso de la vivienda: habitada por propietario o arrendada; no profesión del cliente. | Condicional, sin sello temporal probado |
| days_unoccupied | Duración máxima de desocupación; el diccionario no delimita ventana de referencia o fecha de medición. | Retenido para uso prospectivo |
| smoke_alarms | Indicador booleano de alarmas de humo instaladas; no número de alarmas. | Condicional, sin sello temporal probado |
| voluntary_excess | Franquicia elegida por el cliente, en CU; el diccionario enumera0,250,500,1000. | Condicional, sin sello temporal probado |
| compulsory_excess | Franquicia fijada por la aseguradora, en CU. | Condicional, sin sello temporal probado |

Construcción distingue BRK/STN/WOD/MIX, transformados por un mapa fijo a material. Es distinto de property_type (tipología de inmueble), que sí forma parte de B20. La transformación fija de códigos no prueba que la declaración corresponda a la fecha de cotización; hace falta su versión y vigencia para la vivienda del subperiodo.

occupancy describe propietario ocupante o arrendamiento. No es customers.occupation, que describe profesión del cliente y tiene otra clasificación de disponibilidad. El término «ocupación» de un resumen general no debe confundirse con una autorización o exclusión común de ambos campos. Un uso de vivienda conocido para un periodo tampoco demuestra el uso en toda la anualidad o en una cotización anterior.

days_unoccupied se describe como el máximo de desocupación, sin precisar historial anterior, periodo asegurado, ventana móvil, previsión o experiencia realizada. El esquema es numérico y el código lo copia sin una comprobación de ventana temporal. La etiqueta inicial F0_contractual era una clasificación de trabajo, no evidencia de disponibilidad. No se justifica asignarlo al pasado a partir de su nombre, ni truncarlo a 365días o a la exposición para fabricar esa interpretación.

smoke_alarms es booleano, no un recuento de detectores. Puede ser una característica declarada antes del riesgo, pero no hay fecha de instalación, declaración o comprobación del estado en la tabla. La plausibilidad de conocer una característica física no certifica que este valor sea una fotografía de la cotización.

Las dos franquicias son términos contractuales: una elegida por el cliente y otra fijada por la aseguradora. Es una inferencia razonable que el término aceptado sea conocido al contratar; no prueba cuál era la selección en la primera cotización o antes de un endoso. No consta una regla completa de suma, prelación o aplicación conjunta por peril. El diccionario define pagos ya netos de franquicia y su aplicación a todos los perils: no se altera T0 o descuenta de nuevo la retención.

## Fechas disponibles y lo que no demuestran

En el esquema suministrado las únicas columnas de tipo fecha/timestamp son period_start y period_end. Describen cobertura, no captura de cada atributo. También existe el número days_quote_to_inception. La convención actual deriva:

    quote_date_proxy = period_start - days_quote_to_inception

Esa resta no crea un registro de la cotización ni fecha de conocimiento de cada respuesta. Los cambios a mitad del año pueden generar subperiodos; no basta situar una fecha derivada para asegurar que todas las características se declararon en ella. Se necesitan fecha efectiva y fecha de captura/versión, vinculadas a la fila y, cuando corresponda, al endoso.

La inspección estática de make_features muestra copias de las columnas de póliza y codificación fija de construcción. No hay un as-of join o filtro por timestamp del atributo para estos campos. No se ejecutó el constructor ni el runner histórico, que recorre otros años. No se atribuye a esta revisión una prueba funcional del flujo completo o invariancia de objetos ajustados.

El reto condiciona la predicción al periodo y atributos suministrados. Esa investigación condicional no equivale a un backtest de tarifa cotizada con información históricamente disponible. Esta distinción evita tanto certificar prospectividad sin evidencia como declarar inválidos automáticamente todos los modelos anteriores. La revisión no decide una nueva admisión o cambia el contrato congelado.

## Evidencia concreta que falta

| Bloque | Documento o registro necesario | Qué permitiría resolver |
| --- | --- | --- |
| Los seis campos | Cuestionario/registro de declaración versionado, fecha de captura y vigencia para la fila 2023; propuesta aceptada y endosos | Si el valor estaba disponible al momento de decisión elegido |
| Desocupación | Definición exacta de la ventana, fecha de referencia y naturaleza declarada/realizada | Si el máximo pertenece al pasado conocido o incorpora experiencia posterior |
| Construcción, uso y alarmas | Declaración o constatación fechada y cambios relevantes de estado | Si el dato representa ese riesgo/subperiodo y no un maestro posterior |
| Franquicias | Condiciones aplicables y versión aceptada; regla conjunta y por peril | Interpretación contractual y temporal, sin recalcular el coste neto ya observado |

No se localizaron esos historiales o condiciones completas en los archivos/documentos examinados; no es una afirmación sobre todos los registros que pudiera poseer el organizador. No se envían consultas a terceros bajo este encargo. Una distribución o asociación con el coste no puede sustituir la evidencia de cuándo se conoció el dato, por lo que no se hacen nuevas tablas de rendimiento o correlación.

## Consecuencia y continuidad

F02 queda revisada documentalmente con condiciones abiertas: cinco campos definidos pero sin acreditación de captura en cotización y desocupación retenida hasta aclarar ventana/procedencia temporal. Ninguno de los seis está en la receta de siete efectos de B20; su presencia en el F0 amplio no es una nueva orden humana o aprobación. Se conserva el contrato F0 histórico, código y artefactos entrenados, sin reescribirlos para hacer desaparecer el hallazgo. Esta ficha será la referencia de disponibilidad para una eventual propuesta posterior; no añade variables al modelo actual.

Puede orientar una hipótesis más precisa sobre heterogeneidad, pero no demuestra el mecanismo residual de B20, efectos causales o ganancia predictiva. No añade componentes o costes independientes y no resuelve el soporte retenido fallido. G1/G2 continúan abiertas. F01 ya acreditó igualdad binaria; no se repite ese cotejo.

B00 y todas las alternativas, T0/C0, exposición y folds se conservan.2024/test/SEL01/actas/ledger siguen cerrados para datos/resultados de modelado; de la tabla de pólizas solo se consultó el esquema común. Cero entrenamiento,cargas de modelos,inferencias,scores o remuestreos. La ventana/automatización nocturna permanecen cerradas y no se crea otra. Exposición previa de un asunto externo declarada sin usar métricas o afirmar ceguera completa. Codex firma revisión propia documental, no validación profesional independiente o aprobación humana. Las prácticas IAA de propósito, procedencia y documentación orientan la separación de hecho, inferencia y supuesto, sin certificar aptitud actuarial.

[Índice F02](../../../registro/semana2_F02_disponibilidad2023_actual.json), [plan de fuentes](FUENTES_2023_Y_PLAN_REVISION_B20.md), [disponibilidad inicial histórica](VARIABLES_Y_ULTIMO.md) y [verificación binaria](VERIFICACION_CONTENIDO_KAGGLE_20261024.md). Matriz por campo, esquema,recibo documental,fuentes/SHA y decisiones en Hackaton/Repositorio_IAA2026/privado/semana2/revision_F02_2023/f02_20261024_v1.
