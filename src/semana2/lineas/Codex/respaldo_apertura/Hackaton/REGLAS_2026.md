# Contrato y reglas del reto IAA 2026

Revisión del 16 de octubre de 2026, America/Bogota. Fuentes oficiales leídas mediante MCP nativo después de la apertura. Esta síntesis conserva discrepancias; no constituye una determinación jurídica de elegibilidad.

Consulta vigente del 19 de octubre: reglas y metadatos confirmados de nuevo mediante Kaggle MCP y archivados en `Repositorio_IAA2026/docs/fuentes/reglas_kaggle_20261019.json`. Diez envíos diarios; cierre parte 1 el 23oct a las 16:00 UTC/11:00 Bogotá. Esta semana se entrega el CSV; informe de cinco páginas, video de cinco minutos, ambos CSV y repositorio versionado se entregan al finalizar parte 2. El proyecto ya tiene S30/S22 puntuados y Git/GitHub privado; las frases de ausencia de objetivos/modelos/envíos de las secciones iniciales conservan el corte del 16 de octubre. La carpeta común, matriz de requisitos y estado actual están en `Repositorio_IAA2026`. Siguen pendientes selección manual final, elegibilidad documental, formulario de parte 2, revisión humana y reproducción completa.

## Acceso y evidencia

El participante informó que se unió personalmente. La respuesta oficial de Kaggle confirmó user_has_entered: true en la competición 172537, cuenta autenticada manoloriveros. El agente no pulsó Join ni aceptó reglas.

- [Competición](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1).
- [Reglas](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/rules).
- [Datos](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/data).
- [Respuestas originales y manifiestos](../Preparación/artifacts/verification/iaa_launch_20261016/): competition_response.json, pages_response.json, file_listing.json, report.json y data_manifest.json. Las ocho páginas se conservaron por separado en pages/.
- [Correo transcrito aportado por el participante](../Preparación/Antecedentes/fuentes/correo_apertura_20261016.txt). No se inspeccionaron cabeceras ni el correo original.

El intento de las 10:56 a. m. de Bogotá falló antes de la apertura y se conserva en pre_open_report.json. Al llegar las 11:00 a. m., Chrome mostró la competición. Después del ingreso personal del participante, MCP confirmó el acceso. No se atribuye una causa única al fallo previo.

## Objetivo actuarial y datos

Predecir el coste último esperado de los siniestros de cada periodo de póliza de 2025, en unidades monetarias ficticias (CU), neto de franquicias y recuperaciones, excluyendo siniestros rechazados. Es la prima de riesgo del periodo cubierto. La prima comercial escrita no es el objetivo.

La primera semana usa un mercado desarrollado sintético, con autos particulares, edificios y contenidos del hogar. Las pólizas de entrenamiento cubren 2021–2024; cada fila es un periodo o subperiodo de póliza, con exposición en años. Una póliza puede cambiar a mitad de año y conservar policy_id entre años.

Hay once archivos Parquet: clientes, direcciones, clima, siniestros, tres tablas de pólizas, tres de test y sample_submission. La ruta activa es Semana 1/Datos. La descarga y el ZIP se conservan en ../Preparación/data/raw/iaa_2026_part1_20261016. El diccionario está en ../Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md. Tras reorganizar, se leyeron completamente los once Parquet y se comprobó que sus hashes coinciden con la descarga oficial. El informe nuevo está enlazado en la memoria. No se han construido objetivos ni entrenado modelos.

Las claves son texto. customer_id vincula clientes; address_id, direcciones y clima; los siniestros deben vincularse por policy_id, ramo y fecha de ocurrencia al periodo cubierto. Unir solo por policy_id multiplicaría o asignaría incorrectamente los costes. Clima tiene granularidad dirección-año.

Los siniestros están valorados al 31 de diciembre de 2024. Hay siniestros aún no reportados y abiertos cuyo coste cambiará. Los importes paid_to_date e incurred_to_date son observaciones a esa fecha, no etiquetas últimas completas. Cualquier proxy, ajuste de desarrollo o tratamiento de IBNR debe justificar supuestos, sensibilidad y límites. No se ha construido todavía ese objetivo.

## Evaluación y entregas

| Componente oficial | Peso |
| --- | ---: |
| Rendimiento de tarificación y adaptación | 40% |
| Uso eficaz de IA | 25% |
| Confianza, validación y controles | 20% |
| Comunicación y documentación | 15% |

Dentro del primer componente se combinan con igual peso los scores privados de ambas partes y la valoración del jurado sobre métodos, adaptación, calidad de datos e incertidumbre. No se publica una descomposición numérica adicional entre score y juicio.

La precisión usa Tweedie D², potencia 1,5, mayor es mejor. La página no publica código completo del scorer, pesos por exposición ni tratamiento numérico de ceros. La implementación de [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html) exige predicciones estrictamente positivas para esa potencia. La entrega admite valores no negativos; conviene mantener predicciones positivas y documentar cualquier piso numérico, sin afirmar que se ha reproducido el scorer oficial.

Cada parte recibe un CSV con columnas row_id,prediction, que cubra todas las filas de los tres test. La referencia descargada es sample_submission.parquet, aunque la página menciona sample_submission.csv. No se entrega una tarifa anual sin multiplicar por la exposición pertinente.

Al final de la parte 2 se entregan datos del equipo, ambos archivos de predicciones, video, informe y código con control de versiones. Solo se califican los primeros cinco minutos del video y las primeras cinco páginas del informe. El formulario y detalles se publicarán en la parte 2. La revisión inicial podrá usar IA; la decisión final corresponde al jurado.

## Plazos, equipo y envíos

| Punto | Evidencia |
| --- | --- |
| Apertura parte 1 | 16 de octubre de 2026, 16:00 UTC = 11:00 a. m. Bogotá |
| Cierre parte 1 | Metadatos: 23 de octubre de 2026, 16:00 UTC = 11:00 a. m. Bogotá |
| Parte 2 | Otra competición; las reglas dicen que abre al cerrar la primera. Falta el enlace y el calendario operativo |
| Cierre global | Anuncio previo: 30 de octubre; hora exacta pendiente |
| Equipo | Hasta tres personas; mantener el mismo equipo entre partes. El participante sigue solo |
| Selección final | Reglas específicas: una predicción final por parte; si no se elige, se usa la de mejor leaderboard público |
| Límite diario | Actualización verificada18octubre2026: diez (10) en regla específica §2.2.a y plataforma. Reemplaza el límite provisionalcinco del corte inicial; evidencia N30 |

La sección de calendario de las reglas conserva marcadores [DATE, TIME UTC], incluido el plazo de fusión. El cierre de la primera parte proviene de los metadatos, no de esos marcadores. No crear alarmas ni mensajes por esta revisión.

## Uso de IA, datos y derechos

Las reglas específicas §2.5 permiten procesar los datos sintéticos con servicios IA y LLM alojados para participar. Es un permiso del concurso, no evidencia de que se hayan realizado llamadas externas o de que cualquier herramienta cumpla automáticamente las demás condiciones.

Restringir el acceso a los datos a los usos permitidos; no redistribuirlos fuera de los participantes salvo el procesamiento IA indicado. Los metadatos muestran CC BY-NC 4.0, pero no sustituyen las restricciones de uso y difusión de las reglas. No adoptar CC0 ni publicar los originales por defecto.

Las reglas permiten datos externos accesibles de forma razonable a todos y herramientas de coste mínimo; aceptan una pequeña suscripción a un asistente o entorno ampliamente usado y AutoML con licencia apropiada. No asumir permiso ilimitado para herramientas propietarias inaccesibles. Conservar procedencia, condiciones, versiones y coste de cada recurso propuesto.

No compartir código en privado entre equipos. La publicación voluntaria de código debe estar disponible en los foros o notebooks de esta competición y con licencia OSI compatible. El ganador debe entregar código de entrenamiento e inferencia, entorno y documentación reproducible y conceder la licencia indicada en §2.6 y §2.9. Esta revisión no autoriza publicar, subir datos, enviar predicciones, iniciar cómputo remoto ni contactar a terceros.

## Premios y elegibilidad pendiente

Las reglas y la página de premios indican CAD 500, CAD 100 y CAD 50. El resumen de plataforma muestra 500 USD; se conserva la discrepancia y se usa CAD al describir los premios según el texto específico del organizador.

Para optar a premio se exige ser miembro o estudiante de una asociación miembro plena o asociada de la IAA. El participante declara dos exámenes SOA aprobados y una maestría actuarial en curso, con posible afiliación futura en Colombia. No se han verificado documentos, afiliación vigente ni la interpretación del organizador para este caso. No se declara elegibilidad confirmada ni exclusión.

La [SOA describe la afiliación](https://www.soa.org/about/membership/default/) como abierta a estudiantes y candidatos, sin cuotas, mediante un formulario; la [IAA incluye la SOA entre sus asociaciones plenas](https://actuaries.org/council/strategic-planning/). Esto es una vía que puede comprobarse, no garantía de elegibilidad al premio ni autorización para inscribir al participante en otra asociación.

Borrador de consulta al organizador, pendiente de envío por el participante: «Soy estudiante de maestría en actuaría en Colombia y tengo dos exámenes SOA aprobados. ¿Cumplo el requisito de estudiante de una asociación miembro de la IAA para optar a premio? ¿Qué constancia requieren y cuenta una afiliación SOA Affiliate vigente?».

## Ambigüedades conservadas y trabajo siguiente

Además del límite diario, divisa y calendario incompleto, las reglas fundacionales afirman prioridad ante conflictos y describen ganadores por leaderboard privado, mientras las específicas y la rúbrica establecen evaluación híbrida de dos partes. Conservar ambos textos y pedir aclaración del organizador; no decidir unilateralmente que una cláusula desaparece.

El siguiente trabajo técnico es profundizar en cardinalidades, periodos, exposición y cobertura de cruces; construir y auditar el objetivo observable y sus ajustes; definir validación temporal que refleje 2025 y diagnosticar dependencia entre clientes, pólizas y direcciones. Comprobar disponibilidad real al tarificar de clima anual, prima vigente, contactos de servicio, telemática y otros campos. renewal_decision solo existe en entrenamiento según el diccionario.

El runner preparado acepta CSV y RMSLE/RMSE/MAE; no implementa todavía este contrato multitabla ni Tweedie D². PyArrow 26.0.0 ya permite leer los datos desde una caché aislada de validación. Su disponibilidad no integra automáticamente Parquet en el runner de entrenamiento. El espacio de trabajo aún no es un repositorio Git según la comprobación local. Son adaptaciones pendientes, no resultados verificados.

Priorizar [las prácticas IAA](../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md): propósito y límites (§3.1 de Consideraciones profesionales), ficha de datos (§2 de Documentación), explicación y responsabilidad humana (§§3.2 y 3.5–3.6 de Consideraciones profesionales), y distinción entre evaluación propia e independiente (§2.8 de Gobernanza). Registrar qué parte hace la IA y qué revisa el participante.

../Preparación/configs/competition.yaml conserva rules_confirmed: false por las discrepancias materiales y la falta de contrato técnico operativo completo. El acceso y la lectura de reglas sí están comprobados. La descarga no es un entrenamiento, ni un envío, ni una validación de un modelo.

## Actualización18octubre: diez envíos y prueba inmediata autorizada

Corte UTC 2026-10-18T19:20:32+00:00. La regla oficial específica §2.2.a ahora permite diez (10) diarios, comprobado mediante Kaggle MCP. Cuota viva 2026-10-18T19:17:47Z: cinco usados, cinco disponibles, ningún pendiente. El participante autoriza probar ahora la mejor propuesta preparada de esta línea y la entrega actual de la otra, con nombres neutrales. No se espera a19Bogotá para esos ensayos; el reinicio diario no cambia. Los cortes anteriores que adoptaban cinco se conservan como historia, no como regla vigente. Evidencia ../Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01/verification/N30_submission_policy.json y su respuesta oficial archivada. Sin selección final manual, mezcla nueva, código/datos/modelos publicados o remoto.
