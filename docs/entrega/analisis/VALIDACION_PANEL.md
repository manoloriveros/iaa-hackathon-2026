# Validación del panel de datos de ambas semanas

Codex, 26 de octubre de 2026. Revisión propia asistida por IA; no constituye validación profesional independiente.

El panel reconstruye cifras descriptivas desde los originales de ambos mercados. No ajusta modelos, no modifica recetas o selecciones y no consulta Kaggle. La valoración es el cierre de 2024; el último reporte registrado en ambos archivos es el 30 de diciembre de ese año.

## Resultados de los controles

| Bloque | Comprobación | Resultado |
| --- | --- | --- |
| Productor | SHA-256 de originales y copia de referencia; claves, fechas, estados, intervalos, test y objetivos previos | 136 controles conformes |
| Comprobación separada | Sumas escalares, dinero original con Decimal, asignación por búsqueda binaria, percentiles y nulos recalculados | 1.927 controles conformes |
| Clima | Unicidad dirección/año, cobertura de todas las cohortes y nulos mediante Arrow | 196 controles conformes |
| Navegador | 96 combinaciones de filtros, tablas, exportación, teclado, impresión, cuatro anchos y enlaces; panel previo en español, inglés y oscuro | 231 comprobaciones conformes; cero errores JavaScript y cero solicitudes de red |
| Anexo PDF | Cuatro páginas, texto extraíble, sin texto fuera de página; revisión visual de todas las páginas | Conforme en el corte final; fuentes y recibo identificados |

Estos bloques ejercen condiciones distintas y algunos se solapan. No se suman para anunciar un total de validaciones independientes.

## Conciliación material

El coste reconstruido coincide en cada fila con los objetivos preparados de ambas semanas: 741.156.868,43 CU desarrolladas y 27.997.991,57 CU emergentes. El dinero se conserva en centavos enteros. La exposición coincide con las capas previas y el test mantiene sus etiquetas ausentes, nunca objetivos cero inventados.

Los 163.150 siniestros originales desarrollados se concilian como 604 copias, 413 anteriores a cobertura, 1.701 rechazados asignados y 160.432 aceptados asignados. Los 9.258 emergentes se concilian como 36 anteriores a cobertura, 120 rechazados asignados y 9.102 aceptados asignados. Las exclusiones son disjuntas. El control por búsqueda binaria se contrasta con el join relacional del productor y con el objetivo histórico por fila.

Las tasas se construyen como cocientes de sumas. El numerador es incurrido menos recuperaciones; las franquicias no se vuelven a descontar. La frecuencia de todos los aceptados se distingue de la frecuencia de costes positivos usada en la identidad frecuencia por severidad. El primer año observable se omite del gráfico de clientes sin historia anterior para no presentarlo como adquisición comercial.

## Evidencia y reproducción

El índice es `registro/panel_analisis_actual.json`. La corrida privada se guarda en `privado/panel_analisis/20261026T200025005471Z/`. Sus archivos principales son:

- `controles_productor.json` y `agregados.json`, resultado original del productor.
- `validacion_separada.json`, revisión de cifras por otro método.
- `datos_antes_clima.json`, `agregados_con_clima.json` y `validacion_clima.json`, ampliación trazable sin reescribir el agregado base.
- `validacion_ui.json` y `ui/`, pruebas del navegador y capturas.
- `pdf/`, las cuatro páginas rasterizadas y el recibo del PDF.

La huella base de `validacion_separada.json` coincide con `base_data_sha256` de la ampliación climática. El archivo final conserva ambos cortes; esa relación se comprueba al cerrar. No se afirma que el verificador base hubiera visto una ampliación posterior. El manifiesto de figuras vincula los PNG/SVG al agregado final.

Los comandos y las dependencias están en `docs/entrega/README.md`. El productor y la revisión de datos usaron el Python del proyecto con PyArrow de su caché. El PDF se creó con el runtime documental y se rasterizó con pypdfium2. La UI se probó en Chrome instalado, sin tráfico de red de la página.

## Intentos conservados y correcciones

El primer lanzamiento de Playwright no encontró su navegador empaquetado; Edge se cerró dentro del aislamiento. Chrome abrió el panel y pasó las combinaciones de filtros, pero el aislamiento canceló la escritura de descargas. La exportación real se comprobó después desde Chrome fuera de ese aislamiento, sobre archivos locales. No se declara que los intentos cancelados fueran pruebas satisfactorias. El CSV agregado conserva vacíos los costes de 2025.

La primera revisión separada se interrumpió por ordenar cada póliza de forma repetida. Se conserva su código en `intento_validacion_agrupacion_lenta.py`. La versión final ordena los intervalos una sola vez y mantiene el mismo cotejo por búsqueda binaria. Terminó con 1.927 controles conformes. No se interrumpió entrenamiento ni se cambió el resultado para hacer pasar un control.

La revisión visual del PDF detectó una leyenda sobre las barras del volumen; se movió al espacio superior y se volvió a generar. Las páginas finales no tienen solapamientos o recortes visibles. Los recibos de la corrida se conservan por separado de los documentos históricos del proyecto.

## Límites de interpretación

T0 no es coste último observado. Reservas, retrasos e IBNR requieren hipótesis distintas; el panel no acredita suficiencia. Los retrasos están truncados por el cierre y las diferencias entre mercados reúnen composición y cobertura. Los nulos de atributos se ponderan por periodos enlazados. El clima de 2025 está en el archivo, pero su disponibilidad al cotizar sigue pendiente.

El EDA no restaura la condición confirmatoria de 2024, ya usado adaptativamente. La comisión emergente de `comparison_site` permanece vacía. El anexo no sustituye la selección final de la segunda semana ni su conversión de prima de riesgo a prima comercial.

La validación y la inspección visual son de Codex. La aceptación del informe por el participante y la revisión profesional independiente no se firman por inferencia. Los archivos son para uso local; esta tarea no publica agregados, datos, código o modelos.
