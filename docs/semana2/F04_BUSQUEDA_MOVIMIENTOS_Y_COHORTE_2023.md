# F04: búsqueda de movimientos y cohorte emergente de 2023

Codex, corte UTC 2026-10-24T15:48:43.104538+00:00. No se localizó un historial de movimientos, otro corte de valoración de siniestros de ocurrencia 2023 o una cohorte emergente adicional con procedencia acreditada. F04 queda buscada en las fuentes delimitadas y pendiente de disponibilidad. Esto no demuestra que el organizador carezca de otros registros; tampoco modifica los bloqueos de B20.

## Búsqueda y hallazgos

| Fuente examinada | Evidencia del corte | Resultado para F04 |
| --- | --- | --- |
| Catálogo oficial completo, Kaggle MCP, página de hasta 200 entradas sin continuación | 24 archivos; mismos nombres, tamaños y fechas que la consulta anterior | No se anuncia un archivo de movimientos, un segundo corte o una cohorte adicional |
| [Diccionario oficial](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data) | Texto idéntico al archivado; claims sigue descrito como un registro por siniestro al 31-12-2024 | Un único snapshot, sin historial de transacciones documentado |
| Discusiones de la competencia, orden reciente | La respuesta devuelve dos temas y total_count=2; uno de descarga y otro de formato de envío | No aparece una publicación de datos suplementarios en esa lista |
| [Tema de descarga 752091](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752091) | HOST, mensaje 3543802 del 24 a las 03:12:10.750 UTC: retiró una carpeta antigua que duplicaba el mercado desarrollado para intentar resolver la descarga conjunta | Aclaración de empaquetado; no anuncia nuevos siniestros, movimientos o cohortes |
| Dos búsquedas públicas de datasets en Kaggle | Consulta exacta del hackathon devuelve objeto vacío; IAA 2026 devuelve siete metadatos sin vínculo acreditado con esta cartera | Ningún candidato admisible identificado; relevancia y resultados de búsqueda no son un censo universal |
| Directorios locales Semana 2/Datos y Datos/emerging | Inventario de nombres/tamaños; 13 archivos en emerging y archivos históricos en la raíz | No hay un fichero adicional identificado como movimientos/cohorte |
| Cuatro archivos locales de siniestros y pólizas fuera de emerging | SHA256 binario coincide con el manifiesto histórico desarrollado para claims y las tres pólizas | Son alias históricos desarrollados, no una cartera emergente nueva |

El conector integrado no expone el catálogo de archivos. Se usó el cliente MCP local existente con acceso de red aprobado para una sola petición de metadatos, sin instalar dependencias o descargar tablas. No se repitió la descarga/comparación binaria de los 24 originales de F01. La igualdad binaria de aquella revisión conserva su fecha y alcance; metadatos iguales por sí solos no son una prueba nueva de bytes. Los cuatro hashes locales resuelven una ambigüedad distinta, los alias de la raíz, sin decodificar filas o consultar estadísticas de Parquet.

El aviso del HOST se conserva con autor, fecha y mensaje. Es una explicación publicada de la retirada de duplicados, no una verificación interna de la causa de todos los cambios ni una certificación de que ya funcione la descarga conjunta. No se reabre la incidencia de envío ni se hacen sondas, envíos o cotejos de test. Los datasets homónimos no se descargan ni se admiten por semejanza del título. La cartera y geografía son sintéticas; no hay enlace documentado a siniestros reales externos de 2023.

## Por qué claims no permite reconstruir movimientos

Se reutilizó el esquema de siniestros de F03, sin volver a leer el Parquet. Hay fechas de ocurrencia y reporte, estado, paid_to_date, incurred_to_date y recoveries. No aparecen fecha/identificador de transacción, fecha de cada revisión de reserva, pagos individuales, reaperturas o varios cortes de valoración por claim_id. La fecha de reporte no fecha cada cambio de los importes.

Pago acumulado e incurrido al mismo corte no son dos valoraciones independientes. La diferencia entre incurrido y pago representa la reserva del corte bajo la definición del diccionario; no revela su trayectoria, suficiencia o coste final. Tampoco se reconstruyen reportes aún no observados. No se calculó esa diferencia ni se fabricaron movimientos interpolando importes, simulando colas o remuestreando los mismos siniestros.

## Qué tendría que traer una fuente útil

Para movimientos o cortes sucesivos se necesitan procedencia legítima y versión, fechas de disponibilidad/valoración, claves del mismo mercado y definición acumulada o incremental de pagos, reservas y recuperos. Deben identificarse reversiones, reaperturas y cambios de estado y poder conciliarse importes entre cortes, sin descontar dos veces franquicias o recuperaciones. La recepción se limitaría a ocurrencias de 2023 y a su cobertura; no abriría precios, actas o resultados de la cohorte 2024.

Esa fuente podría separar maduración de siniestros y cambios de reservas del riesgo que intenta captar B20. Varias observaciones del mismo claim_id mejorarían información de desarrollo, pero no serían nuevos siniestros o componentes independientes. No demostrarían por sí solas el último ni un fallo de dispersión del modelo.

Una cohorte emergente adicional necesitaría pólizas y periodos/exposiciones, incluidos los casos sin siniestros, junto con siniestros y vínculos de cliente/dirección. Un listado de pérdidas por sí solo no aporta el denominador del riesgo. Debe acreditarse que es información realmente distinta, conservando solapamientos de siniestro, póliza y componente entre fuentes; identificadores nuevos no garantizan independencia. Fecha de disponibilidad, valoración, cobertura, unidad y objetivo también deben documentarse.

Una cohorte legítima podría aportar componentes o información adicional, pero no garantiza superar el criterio de soporte. Una corrección material de costes podría cambiar la evidencia de los mismos grupos sin añadir grupos nuevos. Cualquier análisis posterior mantendría versiones y criterios previos, con hipótesis, comparador estándar y ámbito autorizado antes de ajustar o puntuar. Este registro de recepción no autoriza una nueva prueba.

## Decisión y continuidad

F04 sigue no disponible en las superficies consultadas. No se abre una prueba por ausencia de información ni se relajan bandas, umbrales o reglas; no se excluyen siniestros. G1 permanece plausible y no establecido; G2 conserva el incumplimiento ya medido. No se reejecutaron esos diagnósticos, C0, replays, suites o remuestreos. Tampoco se mezcló desarrollado con emergente.

El siguiente paso depende de una publicación legítima o corrección material documentada. Entonces correspondería revisar primero su procedencia, fechas, claves y diferencias, con extracción estricta de 2023 antes de analizar valores. No se programa vigilancia nueva, contacta al organizador o prolonga la ventana nocturna.

B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores se conservan. Cero filas decodificadas, entrenamiento, cargas de modelos, inferencias, precios o scores nuevos. 2024/test/ledger/actas/SEL01 siguen cerrados para modelado y confirmación. La exposición histórica de un asunto externo permanece declarada, sin repetir o usar métricas. Revisión de procedencia propia de Codex, no aprobación humana ni validación profesional independiente. Las prácticas IAA de documentación §2 y gobernanza §2.8 orientan esta delimitación de fuente y alcance.

El [índice F04](../../registro/semana2_F04_fuentes2023_actual.json) enlaza recibos de consulta, búsqueda y requisitos de recepción, fuentes con SHA y decisiones. Se conservan [F01](VERIFICACION_CONTENIDO_KAGGLE_20261024.md), [F03](F03_DESARROLLADO_2023_Y_MECANISMO_B20.md) y el [plan histórico](FUENTES_2023_Y_PLAN_REVISION_B20.md) sin reescribirlos.
