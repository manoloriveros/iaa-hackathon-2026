# C0 aislado por ámbito: implementación y prueba sintética

Codex, 24 de octubre de 2026. Continuación solicitada por el participante: «continua con esto». El [preflight de C0](PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md) había conciliado pertenencias, pero dejaba pendiente el cálculo numérico aislado. Ahora existe un núcleo para esa etapa y sus pruebas sintéticas. El contraste de B20 conserva el soporte fallido y no se ha entrenado con los datos del concurso.

## Qué cambió

[c0_estricto2023.py](../../src/semana2/c0_estricto2023.py) recibe periodos y notificaciones ya preparados en memoria. Exige mercado emergente, cohorte 2023, indicador test falso y pertenencias compuestas `(market, line, row_id)`. Comprueba que componentes, clientes y direcciones respetan los folds originales. El mismo row_id de otro ramo no incorpora sus etiquetas al ajuste de edificios.

La selección de los tres folds permitidos ocurre antes de interpretar costes, fechas o perils de las notificaciones y antes de usar la exposición de ajuste. Las curvas de conteos y costes, los pesos por notificación, las marcas medias, las frecuencias y la mezcla se aprenden en ese mismo ámbito. La aplicación usa únicamente el objeto congelado y los atributos del periodo, y rechaza un objeto exterior cuando se solicita el ámbito interior.

Se mantiene la receta base de C0: T0 observado, valoración al 31 de diciembre de 2024, factor de reservas rho=1 y masa adicional de cola cero. Esa fecha de valoración no requiere abrir filas de 2024. La pendiente de una futura calibración no es un argumento de este núcleo y no puede confundirse con el factor de reservas. No se añadieron escenarios, un calibrador o un modelo de precios.

Cada objeto registra la pertenencia de ajuste, las notificaciones que recibieron pesos, la receta, la valoración y las versiones fuente aportadas por el llamador. Su clave incorpora el contenido de entrenamiento seleccionado y los metadatos de pertenencia; una huella adicional detecta cambios del objeto. El llamador sigue siendo responsable de aportar versiones fuente honestas y comprobar las puertas de ejecución. Estos hashes acreditan identidad, no la calidad actuarial del dato.

## Qué se comprobó

La [suite](../../herramientas/probar_c0_estricto2023.py) construye todos los datos en memoria y bloquea aperturas de archivos CSV, Parquet o estimadores durante las pruebas. No carga el ejecutor histórico ni lee filas del concurso. Importa sus rutinas puras para contrastar exclusivamente la receta base en los ejemplos sintéticos.

| Comprobación | Resultado |
| --- | --- |
| Pruebas de comportamiento y contratos | 13 pasaron, sin fallos ni errores finales |
| Pares ordenados de fold exterior/interior | 20 de 20 invariantes |
| Alteración de ambos folds protegidos | Objeto completo y aplicación idénticos; incluye curvas, marcas, frecuencias, mezcla, pesos y clave |
| Control positivo: cambiar el coste de entrenamiento | Cambian curvas, mezcla, clave y C0 aplicado |
| Compatibilidad con la receta histórica rho=1 | Curvas, marcas y pesos coinciden exactamente; C0 dentro de 1e-15 absoluto |
| Caché de ámbito incorrecto, objeto modificado, 2024/test y uniones inválidas | Rechazados |
| Faltan notificaciones de un peril | Se detiene, sin recurrir a los folds protegidos |
| Lecturas de datos o estimadores del concurso | Cero; tampoco hubo intentos de apertura bloqueados |

Se hicieron 79 invocaciones sintéticas del adaptador, incluidas las que debían rechazarse. No son ajustes sobre datos del concurso ni incrementan el contador de modelos de precios. Entorno comprobado: Python 3.12.14, NumPy 2.3.5 y pandas 3.0.1.

El primer intento dejó tres errores al construir datos adversos: pandas 3 impidió insertar booleanos o fracciones en columnas enteras antes de que llegaran al adaptador. Se conservaron sus fuentes, salida y recibo. Las columnas de esos casos se prepararon como objetos para que la prueba alcanzara la validación prevista. También se reforzó la comprobación de que el fold de una notificación sea un entero y se registraron las claves compuestas junto a sus pesos. La suite final pasó sin relajar sus condiciones.

## Qué sigue abierto

Esta evidencia cubre C0. No acredita la invariancia conjunta del preprocesado, GLM y calibrador, ni crea los objetos interiores sobre datos reales. Tampoco añade componentes positivos, reduce la concentración de pérdidas o demuestra el mecanismo de compresión de relatividades. G1 y G2 conservan su estado; G4 tiene una dependencia técnica comprobada y sigue incompleto como flujo total.

El núcleo no tiene lectores de archivos, comando de entrenamiento real o conexión automática al ejecutor histórico. Antes de conectarlo a datos del concurso hacen falta entradas estrictas de 2023, procedencia comprobada y las puertas del ensayo correspondiente. Para el contraste de B20 ya diseñado, con los mismos componentes y costes, continúa vigente la decisión de no arrancar. No se cambian umbrales, bandas, T0/C0 guardados, folds, catálogo o referencia.

El coste previsto de esta etapa para diez ámbitos internos únicos sería sesenta ajustes de reporte, sesenta constantes de frecuencia y diez mezclas de seis perils. Las sesenta marcas medias salen de esos ajustes de reporte; no son modelos Gamma adicionales. Ese presupuesto no se ejecutó y no incluye los modelos de precios o calibradores.

La implementación y las comprobaciones son propias de Codex. No constituyen revisión humana o profesional independiente. Su alcance y limitaciones siguen las prácticas de documentación y gobernanza IAA adoptadas por el proyecto, sin atribuir a esos documentos nuestros umbrales estadísticos.

[Plan previo](../../registro/semana2_b20_c0_adaptador_sintetico_plan_v1.json) e [índice de evidencia](../../registro/semana2_b20_c0_adaptador_sintetico_actual.json). Las fuentes congeladas, el primer intento y los recibos completos están en `privado/semana2/desarrollo2023/c0_adapter_sintetico_20261024_v1`, fuera de Git.
