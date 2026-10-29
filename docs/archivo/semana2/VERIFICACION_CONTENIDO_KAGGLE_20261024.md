# Contenido de los Parquet oficiales: comparación binaria

Los 24Parquet activos comprobados son idénticos byte por byte a los originales locales históricos. Coinciden sus SHA-256 y las huellas oficiales MD5 de los objetos recibidos. No se detectó un cambio de contenido en estas copias; el cambio observado de fecha no aporta datos nuevos de 2023.

Codex, publicación UTC 2026-10-24T14:38:13.257396+00:00. La descarga/comparación terminó a 2026-10-24T14:38:09.065100+00:00. Respuesta a la instrucción directa «verifica el contenido», posterior a la revisión de metadatos. Este resultado sustituye la incertidumbre de identidad binaria de F01 para las copias comprobadas; no altera la fecha o el alcance histórico de la revisión anterior.

| Grupo de archivos | Comprobados | Comparación directa de bytes | SHA-256 local/descargado | SHA-256 local/manifiesto histórico |
| --- | ---: | --- | --- | --- |
| developed | 11 | Todos iguales | Todos iguales | Todos iguales |
| emerging | 13 | Todos iguales | Todos iguales | Todos iguales |
| Total | 24 | Todos iguales | Todos iguales | Todos iguales |

## Cómo se comprobó

Se pidió una URL oficial por archivo a KaggleMCP y se descargaron copias en una carpeta privada aislada. Durante la descarga, cada bloque se comparó directamente con el bloque local del mismo tamaño; también se calcularon SHA-256 y MD5 de ambos flujos completos. Los 24recibos registran igualdad directa, tamaño, huellas completas y ausencia de un primer byte distinto. No se confía solo en nombres,tamaños o fechas.

Las huellas MD5 publicadas por Google Cloud Storage en las cabeceras coinciden con los bytes recibidos y con los locales. Cada recibo conserva la generación del objeto y cabeceras de integridad, sin guardar URLs firmadas o credenciales. Los SHA-256 locales coinciden además con los manifiestos anteriores de la descarga original: once archivos desarrollados y trece emergentes. El inventario de nombres/tamaños/fechas fue estable antes y después de la comprobación.

El primer intento completó cinco archivos y después sufrió fallos de conexión/transferencia. Se conservaron esos cinco resultados, los errores y las descargas parciales. Solo los diecinueve pendientes se recuperaron con peticiones de rangos pequeños y comprobación de generación del objeto. La recuperación no repitió los cinco archivos ya verificados. El resultado final completo no se presenta como un primer intento sin fallos; los recibos de ambos pasos están archivados.

Los originales se abrieron únicamente como bytes de lectura y no se sobrescribieron. Las copias nuevas están bajo privado/semana2/integridad_oficial, separadas de los datos activos y de las entradas del modelo. El programa no importa un lector Parquet, dataframe o modelo; no decodificó valores, años, IDs, etiquetas o predicciones. Identificó únicamente la firma del contenedor para no confundir un error HTML con el archivo solicitado.

La autorización de esta actuación es comprobar la integridad opaca de los 24contenedores, incluidos multiaño y test. No se abrió una validación de 2024 ni se interpretaron sus filas o las del test. No hubo entrenamiento, nuevas inferencias/scores,C0,remuestreo o diagnóstico predictivo. La exposición previa a métricas de un asunto ajeno sigue declarada; esta operación no añade una lectura semántica de esos resultados ni permite afirmar ceguera completa.

## Consecuencia para B20 y el plan de fuentes

F01 queda resuelta en cuanto a identidad de contenido: estos archivos oficiales reproducen los originales conservados. No hay por esta vía una cohorte 2023 adicional, un cambio de siniestros o una corrección material que permita modificar el soporte. No se atribuye una causa interna a la republicación o al cambio de metadatos.

No corresponde repetir los diagnósticos, bandas, entrenamiento o bootstrap por estas fechas. El plan F02 de definición/disponibilidad temporal de campos contractuales permanece como trabajo documental distinto; esta verificación no lo ejecuta. G1 continúa plausible/no establecido y G2 retenido sigue fallido; la igualdad de archivos no acredita calidad actuarial, reservas, último, calibración o capacidad predictiva.

B00 y todas las alternativas, T0/C0, folds, datos activos y recetas permanecen.2024 sigue cerrado para modelado/validación, sin apertura de ledger,actas o SEL01. La ventana y automatización nocturnas continúan cerradas; no se crea programación, remoto, mensajes externos o delegación. Verificación propia de integridad, sin revisión profesional independiente o aprobación humana.

## Recibos

La [tabla completa](../../../privado/semana2/integridad_oficial/contenido_20261024_v1/report.json) contiene un registro por archivo con SHA-256 local/descargado/histórico, MD5 oficial, tamaños, igualdad directa y generación del objeto. Los recibos individuales y las copias opacas están en la misma corrida privada; no se enlazan los Parquet para abrirlos como tablas. Los inventarios antes/después y los manifiestos de referencia quedan conservados.

[Índice de verificación](../../../registro/semana2_contenido_oficial_actual.json) y [plan de fuentes anterior](FUENTES_2023_Y_PLAN_REVISION_B20.md). La receta congelada de ese plan no se reescribe; su índice actual recibe el enlace a este resultado con evidencia.
