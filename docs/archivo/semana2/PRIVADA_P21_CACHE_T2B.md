# P21: las tasas T2b ya están incorporadas; no hay una fuente nueva

Codex, 2026-10-26T19:14:07.407983+00:00. El preflight cotejó109296filas históricas por claves, periodos, exposición y tasas anuales. Las tasas del cache T2b son exactamente las annual_raw_T2b de las entradas canónicas actuales, que ya alimentan la rama N3. No corresponde presentar su reutilización como información nueva o volver a probar la misma receta.

| Ramo | Filas enlazadas | Variables del modelo fuente | Historial12m ausente en2023 | Ausente en2024 |
|---|---:|---:|---:|---:|
| motor | 47283 | 52 | 21680 | 0 |
| buildings | 27447 | 45 | 12580 | 0 |
| contents | 34566 | 46 | 15834 | 0 |

El archivo contiene una tasa anual total, sin objetos de frecuencia o severidad por peril. FSp es otra receta fuente y no debe mezclarse con T2b por similitud de nombres. Las constantes de los antiguos folds tampoco forman parte de la tasa sin nivel ni acreditan el aprendizaje con los grupos actuales por cliente/dirección.

El clima guardado coincide con la media por dirección de2023y2024, cotejada con el Parquet oficial filtrado exclusivamente a esos años y con sumas escalares en una muestra determinista. No se leyó clima2025. Esta climatología está disponible retrospectivamente al inicio de2025; incluye el año retenido al evaluar2023/2024y no demuestra una predicción prospectiva de esos años.

La exposición del cache es calendario exacto; el aprendizaje actual usa su redondeo a cuatro decimales. La diferencia máxima es0,0000493151años. Se conserva el puente entre último y observado ya verificado; no se debe aplicar otra vez la exposición por confundir tasa anual con coste de la fila.

Los encabezados de los modelos, leídos como texto sin construir predictores, incluyen discount_applied y missed_payments_12m. Su procedencia temporal al cotizar sigue sin acreditarse de forma completa en los maestros sin fecha. Este preflight no prueba que sean inadmisibles ni autoriza eliminarlos por intuición.

Aparece una incertidumbre distinta que merece revisar antes de otra tanda: los dos historiales12m están ausentes en todas las filas2023y presentes en todas las2024porque su regla depende de disponer de una ventana calendario completa en la base. Eso no equivale a comprobar que cada asegurado tuvo exposición previa observada. Con tanto negocio nuevo en2025, falta conciliar las codificaciones ausente/cero/positivo con los años de historia de póliza disponibles. No se afirma un fallo de predicción o una causa del score a partir de esta diferencia.

Siguiente P22: cotejar solo covariables de historia en fuente y destino, por separado, con las matrices ya restauradas. Primero se verificará su identidad histórica; después se revisará la cartera2025y la cohorte de broker. No se repetirá la prueba anterior de199REN, que comparaba dos fechas de corte de reportes. Ningún campo se enmascarará automáticamente ni se entrenará una variante sin necesidad y receta preinscritas.

Cero modelos/C0, objetos de predicción, inferencias, scores o envíos nuevos. B00/F3c/alternativas conservados y2024abierto adaptativo. Se completó el preflight de este cache; no el aprendizaje completo de F3c ni una validación privada o profesional independiente. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P21_cache_T2b_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P21_cache_T2b_20261026/read_receipt.json.
