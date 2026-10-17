# Memoria y guía de trabajo para el hackathon IAA 2026

Actualización de la guía: 16 de octubre de 2026. Verificación funcional de referencia: 12 de octubre de 2026. Espacio de trabajo: C:\dev\Hakaton. Entorno y memoria: C:\dev\Hakaton\Preparación. Zona de trabajo: America/Bogota.

Esta guía conserva la investigación, las decisiones y el procedimiento de trabajo para el AI Hackathon IAA 2026. Se consulta al retomar el proyecto y se actualiza cuando cambian las reglas, el código o la evidencia. Los informes de Antecedentes conservan el detalle de las fuentes; los artefactos de cada corrida conservan los resultados técnicos. Una propuesta escrita aquí no equivale a una mejora implementada ni a un resultado obtenido.

## Cómo usar esta memoria

Al comenzar una sesión, leer el estado actual, los pendientes y la etapa correspondiente. Antes de entrenar, comprobar el contrato de datos y la validación. Antes de redactar una afirmación, localizar su fuente o su corrida. Antes de entregar, recorrer la lista de comprobaciones de cierre.

La prioridad acordada es competir por el premio con un flujo actuarial útil, comprensible y confiable, dirigido por el participante mediante IA. La selección de propuestas atenderá al uso creativo de IA, reproducibilidad, adaptabilidad y consideraciones profesionales del anuncio 2026. El rendimiento predictivo se medirá según el contrato del reto. El participante es estudiante actuarial, conoce Python y ha construido modelos. Trabaja solo. No se impone un límite propio de horas, equipo o presupuesto de cómputo; sí deben respetarse los límites oficiales. Las propuestas iniciales de 20–30 horas y las recomendaciones condicionadas por un equipo limitado quedaron superadas por esta preferencia.

El anuncio sugiere 10–15 horas como oportunidad de aprendizaje. Esa cifra no es una estimación del esfuerzo necesario para ganar ni una restricción del proyecto.

Las etiquetas que deben acompañar las decisiones son:

| Estado | Significado |
| --- | --- |
| Confirmado por organizador | Lo afirma una fuente oficial vigente de esta edición |
| Antecedente de 2025 | Sirve para aprender; requiere nueva confirmación para 2026 |
| Declarado por autor | Describe su solución o resultado; no constituye reproducción independiente |
| Inspeccionado | Se revisó código o documentación; no implica haberlo ejecutado |
| Implementado | Existe en el proyecto y se puede localizar |
| Verificado localmente | Hay pruebas o corridas conservadas con su entorno |
| Propuesto | Hay una hipótesis; falta implementar, evaluar o ambas cosas |
| Pendiente | Falta una respuesta, una comprobación o una decisión |

Si una fuente se contradice con otra, conservar ambas, sus fechas y el punto concreto de desacuerdo. No resolverlo inventando una regla.

## Estrategia de validación y envíos acordada el 16 de octubre de 2026

El participante pidió conservar esta recomendación como criterio de trabajo (D29): aprovechar los envíos de Kaggle para contrastar nuestras mejores versiones cuando cada envío responda a una hipótesis concreta. Los cinco envíos diarios son un máximo provisional, no una cuota que debamos agotar. Las reglas específicas indican cinco y los metadatos de plataforma diez; se conserva la discrepancia de [las reglas operativas](../Hackaton/REGLAS_2026.md) hasta aclaración oficial.

1. Construir primero el objetivo actuarial, con tratamiento explícito del desarrollo y el IBNR, y una validación local que imite la predicción de 2025, respetando tiempo y entidades repetidas. Probar las variantes localmente antes de decidir un envío.
2. Preparar un modelo inicial sencillo y razonable para obtener una referencia en Kaggle una vez comprobados el objetivo, la métrica y el archivo de entrega.
3. Enviar variantes respaldadas por mejoras locales y una hipótesis documentada, por ejemplo, sobre desarrollo de siniestros, variables o modelo. Evitar archivos idénticos y versiones con problemas conocidos; no enviar solo para consumir el cupo diario.
4. Registrar para cada candidato la hipótesis, los cambios, la versión de código, los datos, los parámetros, el esquema de validación, el archivo exacto y las puntuaciones local y pública. Vincular el envío a su experimento para poder comparar y seleccionar la entrega final.

La puntuación pública aporta evidencia adicional. No ajustar ni seleccionar únicamente para subir en esa tabla: una mejora en su muestra puede no mantenerse en la evaluación privada. Elegir la entrega final con la validación local y la evidencia actuarial, considerando también la adaptación, la reproducibilidad y la rúbrica del jurado.

Tweedie D² con potencia 1,5 se maximiza; no es un porcentaje de predicciones acertadas. Se selecciona un único envío final por parte; si no se elige, las reglas específicas toman el de mejor puntuación pública. Al registrar esta decisión no hay modelos del reto entrenados ni envíos propios. La política queda documentada para aplicarse después; no constituye una autorización nueva para enviar archivos o iniciar cómputo remoto.

## Objetivo actuarial y validación para comenzar el modelado

El participante pidió una propuesta metodológica propia basada en ramos, productos e información verificada del proyecto. La [guía vigente](<../Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md>) y el [protocolo estructurado](<../Hackaton/Semana 1/Modelado/protocolo_metodologico.json>) fijan el estimando, las etiquetas observables, disponibilidad de predictores, comparaciones por ramo y cortes de validación. D35 registra esta definición; las propuestas analizadas antes quedan como antecedente y no gobiernan el método activo.

La primera etiqueta T0 es incurrido menos recuperaciones de abiertos/cerrados asignados una sola vez por póliza, ramo y fecha de ocurrencia. No volver a restar franquicias; rechazados fuera del coste; filas sin siniestros aceptados con cero. T0 es proxy al cierre de 2024, no último observado. La propuesta separa T1, perturbaciones declaradas de reservas, y T2, completitud de reporte condicionada a modelar truncamiento y validar notificaciones. Frecuencia-severidad se define con conteo de costes positivos y severidad positiva; conservar también conteo total aceptado. Desde D36, la capa preparada incorpora los 2.073 capitales CAP01 autorizados; los 1.454 extremos restantes se conservan pendientes. Reconstruir las reparaciones permitidas por la información de cada corte temporal.

V22 usa 2021 para ajustar inicialmente sobre 2022; V23 entrena 2021–2022 y usa 2023 para desarrollo con mitades de cliente separadas para calibración/selección; V24 entrena 2021–2023 y evalúa 2024 después de congelar candidatos. Su reutilización debe registrarse. La valoración posterior de las etiquetas y la ausencia de snapshots limitan el backtest histórico; no inventar importes o estados pasados. Conservar renovaciones y medir entidades conocidas/nuevas. Primera comparación: referencias por ramo, GLM Tweedie y boosting; frecuencia-severidad y separación de lesiones/hundimiento como alternativas actuariales. El catálogo inicial de 17 candidatos, ampliado a 22 en D37, sigue pendiente de ejecución y subordinado al protocolo.

El [diagnóstico descriptivo nuevo](<../Hackaton/Semana 1/Modelado/diagnosticos/actual.json>) usa siniestros originales, pólizas derivadas verificadas y la proxy EDA, con hashes y script conservados. No encontró costes netos negativos o no finitos entre aceptados; encontró uno con coste cero. Aproximadamente 84,75%–84,85% de filas de 2025 tienen cliente conocido en el mismo ramo. Lesiones de autos y hundimiento de edificios muestran abiertos antiguos y retrasos más largos; no se convierten sus estadísticas truncadas en desarrollo último. El diagnóstico no entrena, modifica originales ni materializa el nuevo objetivo operativo. Próximo trabajo: asignación y reconciliación, tabla T0, matriz contractual F0 y particiones persistentes, antes del primer piloto. Se mantiene D29 y las discrepancias oficiales.

## Investigación de técnicas por ramo, D37

La [investigación metodológica](<../Hackaton/Semana 1/Modelado/Investigacion_tecnicas/INFORME.md>) conecta los datos reales del proyecto con 23 fuentes primarias y deja un orden de pruebas. La [evidencia nueva](<../Hackaton/Semana 1/Modelado/Investigacion_tecnicas/actual.json>) corresponde a soporte_20261016T190621Z, actualizada sobre CAP01/CAT01/AGE01 de D38, y conserva hashes, script y agregados. La primera corrida CAP01 y el control que detectó el cambio de capa permanecen archivados; los agregados de costes, exposición y capital no cambiaron. Los costes de siniestros describen aceptados de ocurrencia 2021–2024 reportados al cierre; los ceros por periodo reutilizan la asignación descriptiva D30, sin sus claves/exposiciones antiguas. No se materializó T0 operativo.

Lesiones de autos representan 37,90% del incurrido neto del ramo, con reserva de caso equivalente al 31,41% de ese componente. En edificios, inundación e incendio suman 51,43% del coste; en contenidos, robo aporta 42,31%. Las proporciones de periodos con coste observado cero son 89,99%, 96,42% y 96,82%. La exposición inferior a medio año afecta al 20,08%, 16,76% y 18,41% del train preparado. Estas cifras justifican comparar componentes por peligro y proporcionalidad de duración, sin afirmar que hay inflación estructural de ceros o factores últimos ya estimados.

Prioridad: GLM/GAM, frecuencia–severidad y boosting por ramo; después corrección sobre base actuarial, credibilidad/historia causal y CANN. D37 incorpora TabM (M17), ANAM (M18), Credibility Transformer y extensión con contexto (M19), TabPFN con piloto de severidad (M20) y zero-inflated Tweedie condicionado al diagnóstico (M21). TabPFN-3 anuncia capacidad de un millón de filas y 200 variables, por lo que no se descarta por límites antiguos; el benchmark actuarial v3 del 9 de octubre de 2026 y los requisitos de exposición, pesos, licencia y coste respaldan una prueba acotada. Los resultados publicados no son resultados de nuestra cartera. Sin entrenamiento, instalación, descarga de pesos, proveedor contratado, envío o delegación. Revisión humana e implementación pendientes.

## Prioridad de diseño del hackathon 2026

Actualización del 16 de octubre: la evaluación oficial ya publica pesos y complementa los cuatro enfoques del anuncio: rendimiento y adaptación 40%, uso eficaz de IA 25%, confianza, validación y controles 20%, comunicación y documentación 15%. Consultar [REGLAS_2026.md](REGLAS_2026.md) y la evidencia oficial archivada antes de decidir. Las referencias posteriores a ausencia de pesos corresponden al anuncio previo, no a la rúbrica ahora publicada.

La prioridad confirmada por el participante el 13 de octubre parte del anuncio 2026: dirigir la IA para construir algo que otro actuario pueda usar, comprender y revisar para confiar en ello. Cada experimento, elección de arquitectura y entregable debe contribuir a ese objetivo. Los cuatro enfoques son el marco de diseño; el anuncio no proporciona pesos numéricos del jurado.

| Enfoque del anuncio | Pregunta para decidir | Evidencia que prepararemos |
| --- | --- | --- |
| Uso creativo de la IA | ¿Qué tarea actuarial concreta mejora y qué aporta la IA? | Intercambios reales, herramientas, referencia de comparación y decisiones humanas sobre propuestas aceptadas o rechazadas |
| Reproducibilidad de los resultados | ¿Puede otro actuario reconstruir la salida y rastrear su origen? | Datos autorizados, código y versiones, parámetros, contexto, trazas, comando de reproducción y prueba desde un entorno limpio |
| Adaptabilidad del flujo de trabajo | ¿Puede aplicarse a otra situación pertinente con cambios explícitos? | Separación de datos, configuración y núcleo; prueba en un escenario distinto y documentación de los cambios y supuestos |
| Consideraciones para la práctica profesional | ¿Qué necesita revisar un actuario antes de confiar en la salida? | Unidades, supuestos, fuentes, errores relevantes, límites, revisión humana y comportamiento cuando falta información o falla una herramienta |

Antes de añadir complejidad, identificar la tarea y decisión profesional, quién usaría el resultado y cómo comprobaría su corrección. Después definir qué parte puede hacer la IA y dónde hacen falta criterio, comprobación o responsabilidad humana. Conservar esas intervenciones con ejemplos reales del proyecto.

La decisión sobre una variante debe registrar su resultado técnico y su aportación a estos enfoques. Una mejora de score necesita validación pertinente; también deben medirse interpretación, adaptación o utilidad cuando sean la razón para elegir el cambio. La complejidad por sí sola no demuestra creatividad.

La demostración final mostrará un caso de uso actuarial, una salida rastreable, una adaptación y las comprobaciones humanas necesarias. Ajustar esos entregables al enunciado cuando se publique. Las 10–15 horas del anuncio orientan el aprendizaje y no sustituyen la preferencia del participante de dedicar los recursos necesarios para competir.

## Estado actual y siguientes decisiones

## Validación detallada e interpretación de datos, 16 de octubre

Por solicitud del participante se completó una primera revisión actuarial exploratoria: once tablas, 7.826.877 filas, 105 nombres de columna y 242 apariciones físicas, con 116 gráficos. El [informe interactivo local](<../Hackaton/Semana 1/Analisis/runs/eda_20261016T165629Z_ab2a8365/informe.html>) contiene un buscador por columna, fichas con definición, mecanismo asegurador propuesto, disponibilidad, tratamiento candidato, estadísticas y asociaciones observadas. La [guía de reproducción](<../Hackaton/Semana 1/Analisis/README.md>) enlaza los scripts y explica el alcance. D30 conserva la decisión.

La auditoría realizó 174 comprobaciones generales y diagnósticos dirigidos adicionales. La verificación del artefacto pasó trece identidades y controles técnicos, incluidos hashes de entrada, cobertura del diccionario y conservación de importes. No supone aprobación de los datos ni validación independiente. Se inspeccionaron gráficos seleccionados; el HTML se comprobó estáticamente y no se acreditó su interacción en navegador porque la herramienta bloqueó file. No se intentó un rodeo.

Hallazgos: exposición con cantidades de días y mezclas ACT/365 y ACT/360; capitales con saltos cercanos a mil veces; claves de cliente de autos sin ceros iniciales (relleno hasta ocho posiciones recupera 98.110 cruces históricos y 25.554 de test); variantes de construcción y abreviaturas pendientes; NCB superior a años de licencia que requiere interpretar reglas. Los 414 siniestros sin intervalo compatible son anteriores al primer periodo observado, no pólizas inexistentes; pueden ser antecedentes o cobertura fuera de ventana y no se fuerzan al objetivo actual.

Se conservó la experiencia con exposición original y se calculó una sensibilidad con días inclusivos / 365, convención predominante observada y coherente con test. Los gráficos de tasas usan esa sensibilidad y lo declaran. Los originales no se modificaron; la transformación no se presentó como corrección aprobada. Los atributos de cliente en asociaciones conservan el cruce literal auditado y su grupo faltante incluye el problema de claves; no es un segmento limpio.

Se construyó solo una proxy descriptiva: incurrido menos recuperaciones de siniestros aceptados y asignados una vez al periodo. No es coste último; reservas, IBNR y disponibilidad temporal siguen abiertos. Asociaciones por edad, zona, seguridad o cobertura no son efectos causales ni relatividades de tarifa. No se ajustó ni envió modelo. task_origin.json identifica la aportación asistida por IA y los límites del registro; no inventa una conversación API completa ni revisión humana. Las corridas y verificaciones anteriores se conservan.


## Reorganización y acceso comprobados el 16 de octubre

La raíz C:/dev/Hakaton contiene .agents, Preparación y Hackaton. RUTAS_PROYECTO.json, en la raíz, define las rutas operativas. Esta sigue siendo la memoria general; el estado y las decisiones permanecen junto a ella en Preparación. project_root del estado designa esta carpeta, base de sus rutas relativas. workspace_root designa la raíz común. Consultar también ../README.md.

Hackaton/REGLAS_2026.md es el contrato operativo único; el archivo homónimo de Preparación remite a él. Datos activos: ../Hackaton/Semana 1/Datos. La descarga anterior y el ZIP se conservan en data/raw/iaa_2026_part1_20261016; no se borró ninguna copia. Los once archivos activos coinciden por SHA-256 con el manifiesto oficial previo y con la copia archivada. Se decodificaron todas las filas y columnas con PyArrow 26.0.0. Los 626.639 row_id de los tres test coinciden exactamente con la plantilla, sin duplicados. Es acceso e integridad comprobados, no validación actuarial de los datos o del objetivo.

Evidencia nueva: artifacts/verification/workspace_layout_20261016T164312Z_e7327974/report.json, con esquemas, filas, hashes y alcance. PyArrow se instaló solo en .cache/parquet-reader; requirements.data-access.txt fija versión y hash del wheel Windows. No se cambiaron las versiones de los entornos de entrenamiento o integración. El script scripts/validate_workspace_layout.py permite repetir esta inspección sin entrenamiento.

La reubicación dejó lanzadores de consola, el kernel IAA y la configuración del lector MCP apuntando a las rutas viejas. Se regeneraron los lanzadores desde los entrypoints de las versiones ya instaladas, con respaldo; se corrigió el kernel y el comando MCP, manteniendo el token, servidor y herramientas de lectura. El diagnóstico de integraciones ahora localiza .agents/skills en la raíz. Las verificaciones específicas y sus límites se registran en relocation_checks.json. Los comandos del README de preparación requieren entrar primero en Preparación.

Los artefactos históricos conservan sus rutas absolutas originales: documentan dónde se produjeron, no son instrucciones vigentes. No se modificaron corridas, snapshots ni notebooks históricos. La evidencia de 37 pruebas sigue siendo del 12 de octubre y no certifica automáticamente estos cambios. No hubo entrenamiento, construcción de objetivo, envío, ejecución remota o reproducción independiente. D28 registra la reorganización. Siguen pendientes el contrato técnico del modelo, desarrollo/IBNR, validación temporal, Tweedie D² y las dudas oficiales y de elegibilidad ya registradas.


Después de la apertura del 16 de octubre, el participante informó que se inscribió personalmente en Kaggle y get_competition confirmó user_has_entered: true para la competición 172537, iaa-ai-assisted-hackathon-2026-part-1. Se archivaron los metadatos y las ocho páginas oficiales en artifacts/verification/iaa_launch_20261016. Se descargaron once archivos Parquet, 198.159.846 bytes sin comprimir, en data/raw/iaa_2026_part1_20261016/public, conservando el ZIP. data_manifest.json guarda tamaños y SHA-256, comprobación CRC del ZIP y firmas de los archivos; no acredita lectura de filas ni calidad actuarial. report.json conserva el alcance. D27 supera los pendientes de acceso e ingreso de D26, sin borrar su evidencia.

El objetivo es el coste último esperado por periodo de póliza en 2025, neto de franquicias y recuperaciones y excluyendo rechazados, para autos, edificios y contenidos. Las pólizas históricas son 2021–2024 y los siniestros están valorados al 31 de diciembre de 2024, con desarrollo e IBNR pendientes. Métrica: Tweedie D², potencia 1,5, maximizar. Cierre parte 1 según metadatos: 23 de octubre, 16:00 UTC = 11:00 a. m. Bogotá. La entrega final abarca ambas partes: predicciones, código con control de versiones, video (primeros cinco minutos) e informe (primeras cinco páginas). La rúbrica oficial ya tiene pesos; el anuncio previo sin pesos queda como antecedente.

Hay discrepancias y campos incompletos conservados en REGLAS_2026.md: cinco envíos diarios en reglas frente a diez en plataforma (límite provisional: cinco), premios CAD frente a USD en metadatos, calendario con marcadores y cláusulas de ganadores por leaderboard frente a evaluación híbrida. La parte 2 aún no tiene enlace ni cierre operativo confirmado. rules_confirmed sigue false; no significa que no se hayan leído las reglas. La elegibilidad al premio tampoco queda confirmada: el participante declara dos exámenes SOA y maestría actuarial; no se verificó afiliación vigente ni aceptación del organizador para su caso. Se preparó una consulta, sin enviarla ni inscribir al participante en otra asociación.

Próximo trabajo: lector Parquet documentado, inspección de esquema y cruces temporales, construcción de objetivo observable y tratamiento explícito del desarrollo, validación pertinente y adaptación a D². El núcleo preparado usa CSV, minimiza las métricas actuales y no implementa el nuevo contrato; no basta cambiar el nombre de métrica. No se cambiaron dependencias o código funcional, no hubo entrenamiento, envío ni ejecución remota. No se repitieron pruebas sintéticas por esta actualización documental. La carpeta sigue sin repositorio Git. El inicio del modelado y la evaluación propia se documentarán con evidencia nueva.

### Corte previo a la apertura del 16 de octubre

El 16 de octubre el participante aportó el correo de apertura, que agradece su registro IAA y anuncia modelos de predicción de costes de siniestros para una aseguradora, con dos etapas y nuevos datos y retos en la segunda semana. Se conserva la transcripción en Antecedentes/fuentes/correo_apertura_20261016.txt; no se inspeccionó el correo original. La apertura anunciada es a las 12:00 p. m. EDT, equivalentes a las 11:00 a. m. de Bogotá (16:00 UTC). El participante confirmó que aún no se ha unido en Kaggle. El enlace redirige a iaa-ai-assisted-hackathon-2026-part-1. A las 10:56 a. m. de Bogotá, antes de la apertura anunciada, Chrome mostró “We can't find that page” y el MCP denegó competitions.get; el perfil propio sí confirmó manoloriveros. Contrato parcial: [REGLAS_2026.md](REGLAS_2026.md). Evidencia: artifacts/verification/iaa_launch_20261016/pre_open_report.json. Reglas completas, métrica, archivos, plazo exacto de cierre y elegibilidad para premios siguen pendientes; rules_confirmed permanece false. D26 conserva el cambio de etapa sin atribuir entrenamiento, ingreso o aceptación de reglas.

Los párrafos siguientes conservan los cortes históricos y deben leerse con sus fechas; las afirmaciones de pendientes superadas no describen el estado vigente. El contrato actual está en REGLAS_2026.md.

MCP nativo confirmado desde este chat el 14 de octubre de 2026, a las 10:33 America/Bogota: llamadas directas `mcp__kaggle__get_accelerator_quota` y `mcp__kaggle__get_user_profile` devolvieron isError false. El perfil identificó `manoloriveros`, ID 704446, con can_edit true; la cuota devolvió 30 horas GPU y 20 TPU, sin consumo ni reservas. Las 25 herramientas de lectura ya están disponibles aquí. Se resuelve la activación pendiente de D24 y P08. Evidencia nueva, con argumentos y respuestas originales: artifacts/verification/kaggle_native_chat_20261014T153310Z/report.json. D25 registra el cierre. No se leyó ni registró el valor del token en esta comprobación; no hubo cambios de cuenta, envíos ni entrenamiento. Los reportes previos se conservan.

Autenticación MCP configurada el 14 de octubre: Codex lee el token existente mediante `scripts/kaggle_mcp_headers.py` y `http_headers_helper`; el secreto no se añadió a config.toml ni a los artefactos. El cliente MCP nativo de Codex (app-server, llamadas `mcpServer/tool/call`, sesiones técnicas efímeras sin chats guardados o inferencia) obtuvo cuota autenticada y perfil `manoloriveros`, ID 704446, con `can_edit: true`. El control nativo sin token devolvió `Unauthenticated` para la cuota. Se habilitaron 25 herramientas de lectura. Evidencia: artifacts/verification/kaggle_native_auth_20261014/report_final.json. Este chat conserva la conexión anterior: una llamada directa a search_notebooks aún devolvió Unauthenticated. Falta recargar el MCP en la app o reiniciar Codex y repetir la llamada directa aquí. D24 distingue la verificación del cliente nativo nuevo de la activación pendiente en la sesión actual. OAuth falló con ClientId too small: codex; la revisión automática rechazó el reintento por el alcance administrativo persistente. Se canceló ese flujo y se usó el token ya existente, sin registrar autorización OAuth nueva.

Token nuevo comprobado el 14 de octubre de 2026: la CLI oficial aceptó el archivo `~/.kaggle/access_token` y devolvió `manoloriveros`, la cuenta conservada. Pasaron `config view` y `quota` a través de `credentials --verify --json`. El diagnóstico confirmó las dependencias, conectividad a los tres hosts oficiales y catálogo MCP de 76 herramientas. Get-Acl mostró permisos para el usuario actual, SYSTEM y Administradores; la advertencia POSIX 666 del checker no representa las ACLs de Windows. Se preparó PATH solo en el proceso de prueba y se permitió acceso de red tras un intento restringido que no llegó a validar el token. Evidencia sin secreto: artifacts/verification/kaggle_auth_20261014T150057Z/report.json. D23 sustituye el pendiente de token de D22. No se modificaron credenciales, no hubo descargas de datos, publicaciones, envíos o notebooks alojados. La autenticación MCP nativa sigue pendiente.

Resolución de cuentas en Chrome el 14 de octubre: el participante recuperó `manoloriveros`, eligió conservarla y completó fuera del control del agente la eliminación de la duplicada `manoloriveros89`. Se observó la página Account Deleted con Your account has been deleted, y después los ajustes de `manoloriveros` (cuenta 704446), con teléfono Verified. Se comprobó que la cuenta conservada sigue accesible. Su verificación de identidad en Persona está pendiente. La autenticación CLI del 13 de octubre pertenece a la cuenta eliminada; todavía no se sustituyó el token ni se probó su validez posterior al borrado. D22 y su actualización registran el resultado. Evidencia: artifacts/verification/kaggle_account_resolution_20261014/report.json. La [ayuda oficial sobre teléfono duplicado](https://www.kaggle.com/contact#/account/activate/duplicatePhone) indica usar la cuenta previamente verificada. No se comprobó si la notificación histórica desapareció. Las capturas locales del 14 de octubre están excluidas de Git.

Autenticación comprobada el 13 de octubre a las 16:48 America/Bogota: el participante guardó el token moderno fuera del proyecto. Se corrigió el nombre añadido por Bloc de notas, `access_token.txt`, a `access_token`. La CLI oficial aceptó el token y sus consultas `config view` y `quota` identificaron la cuenta `manoloriveros89`. Evidencia sin token: artifacts/verification/kaggle_auth_20261013T214817Z/report.json. La conexión MCP nativa sigue verificada solo para lectura pública; no se configuró aún su autenticación. No se hicieron subidas, envíos ni ejecución alojada. Esta evidencia actualiza las afirmaciones históricas de ausencia de credenciales que se conservan debajo.

La [revisión frente a los papers IAA del 13 de octubre](Antecedentes/IAA_IA/REVISION_PROYECTO_20261013.md) encontró una base de trazabilidad y validación técnica, con evidencia profesional del caso aún pendiente. Los diez módulos del núcleo y ambos notebooks coinciden por hash con el snapshot de referencia; hay cambios documentales y de .gitignore. El registro de prompts de producción sigue vacío y el runner comprueba existencia de IDs sin imponer revisión final. Prioridades propuestas: contrato y fichas del caso, registro posterior de revisión humana, evaluación profesional y exterior, interpretación, adaptación y reproducción del paquete final. La [evidencia de inspección](Antecedentes/IAA_IA/EVIDENCIA_REVISION_20261013.json) conserva el corte. No se implementaron controles ni se repitió entrenamiento; D20 registra esta revisión, sin adoptar automáticamente sus propuestas.

El 13 de octubre el participante pidió priorizar los papers de IA de la IAA. Se archivaron tres PDF únicos en [Antecedentes/IAA_IA](Antecedentes/IAA_IA/README.md), con su catálogo y una [matriz de prácticas](Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md). Consultarla antes de diseñar, evaluar o documentar una propuesta. La decisión D19 registra su incorporación. Son referencias educativas; no confirman reglas 2026. La matriz identifica evidencia futura y carencias, sin afirmar que los controles ya estén implementados o verificados.

Comprobación posterior del 13 de octubre: una llamada nativa desde esta sesión a `mcp__kaggle__get_competition` obtuvo los metadatos públicos de Titanic. El diagnóstico local encontró Kaggle 2.2.4 y kagglehub 1.0.2 sin credenciales. La captura aportada muestra la sesión web iniciada; la inspección de ajustes en Chrome quedó bloqueada por `Unable to load browser request-header policy`. No se modificó la cuenta ni se inició un notebook. Evidencia: artifacts/verification/kaggle_account_20261013T212600Z/report.json. El acceso autenticado y la ejecución alojada siguen pendientes; esta comprobación resuelve el pendiente de lectura pública nativa del párrafo siguiente.

Actualización del 13 de octubre de 2026: se incorporaron el plugin NVIDIA Kaggle y los skills locales de shepsci y FrankS-IntelLab. El participante pidió acceso público porque aún no tiene token. El MCP oficial quedó registrado con 23 herramientas de lectura; una consulta HTTP real obtuvo 76 herramientas y los datos públicos de Titanic. Falta comprobar una llamada nativa desde una sesión de Codex que cargue el catálogo y el acceso autenticado. No hubo subidas, envíos o entrenamiento alojado. El análisis, versiones y evidencia están en Antecedentes/integraciones_kaggle_2026.md y su catálogo JSON. Las dependencias de integración usan .venv-kaggle; el entorno de entrenamiento y sus notebooks se conservaron.


El entorno y la trazabilidad v2 están implementados. La verificación conservada del 12 de octubre pasó 37 pruebas, Ruff y pip check. Se ejecutaron ambos notebooks desde kernels nuevos. La ejecución local y la simulación de Kaggle en Windows compararon seis modelos, repitieron entrenamiento y coincidieron en particiones, predicciones OOF y CSV. El modelo CatBoost guardado reprodujo el CSV de 140 filas sintéticas al recargarlo.

Estas comprobaciones pertenecen al ensayo sintético. No demuestran rendimiento en la competencia, portabilidad comprobada en Linux ni ejecución alojada en Kaggle. El estado de referencia está en [readiness_v2.json](artifacts/readiness_v2.json). Los reportes anteriores se conservan como historial.

| Capacidad | Estado al corte | Límite que no debe perderse |
| --- | --- | --- |
| Python local aislado | Verificado con Python 3.12.14 en Windows | No se ha probado toda la matriz de versiones soportadas |
| Regresión | Implementada con RMSLE, RMSE y MAE | Clasificación, NLP o aplicación requieren adaptación |
| Modelos | Dummy, Ridge, HistGradientBoosting, CatBoost, LightGBM y XGBoost | Los hiperparámetros actuales están fijados en código |
| Particiones | Kfold, grupos y tiempo | Grupos y tiempo simultáneos requieren un diseño específico |
| Registro de experimentos | Configuración, datos, folds, entorno, métricas, OOF, modelo y CSV | Una entrada en el registro no significa que se haya enviado a Kaggle |
| Conversaciones v2 | Mensajes completos, contexto, parámetros, respuestas y trazas | No se han hecho llamadas reales a un proveedor externo |
| Live y replay | Probados con transporte local y fixtures sintéticos | No hay despacho automático de herramientas de un agente |
| Snapshots | ZIP determinista con archivos reales y manifiesto | Datos originales y conversaciones privadas se conservan por otra vía |
| Notebook Kaggle | Autónomo, con bundle verificable y simulación Windows | Falta probarlo en Kaggle alojado |
| Docker de verificación | Archivo preparado | No se ejecutó: no había daemon Linux operativo y WSL falló |
| Investigación avanzada | 20 metodologías propuestas y casos comparados | No existe todavía un optimizador Optuna integrado, stacking ni modelos fundacionales |
| Reglas 2026 | Anuncio y fechas confirmados | Enunciado, rúbrica numérica, datos y condiciones completas pendientes |

No hay credenciales Kaggle configuradas en este entorno, envíos realizados por este proyecto ni conversaciones reales en el registro de producción. La inscripción del participante fuera de esta conversación debe comprobarse con su comprobante; no se deduce de estos archivos.

Los pendientes prioritarios son verificar inscripción y elegibilidad como estudiante, archivar las reglas de 2026 cuando se publiquen, probar el notebook en Kaggle real, adaptar el contrato al reto y empezar un registro de conversaciones reales con revisión humana. Después se elige el portafolio avanzado que justifiquen los datos.

## Qué sabemos de la edición 2026

La IAA anuncia un hackathon organizado por su comité de IA, Datos y Tecnologías Emergentes, del 16 al 30 de octubre de 2026, abierto a actuarios y estudiantes, con inscripción gratuita. El anuncio destaca uso creativo de IA, reproducibilidad, flujos adaptables y utilidad profesional. No publica ahí una métrica, pesos numéricos del jurado ni una hora exacta de cierre. Fuente: [anuncio oficial IAA](https://actuaries.org/news-post/38651-2/).

La apertura anunciada es el 16 de octubre de 2026. Los horarios de apertura y cierre, su zona horaria y el margen real de envío deben copiarse de la página oficial al publicarse.

El enlace de [inscripción](https://docs.google.com/forms/d/e/1FAIpQLSc-V_7nuXH8Wt-N2SUk-iuYrxe-wg0TseoBIe2n4qpeiws0KQ/viewform) y la [publicación de AI for Actuaries](https://www.aiforactuaries.org/posts/107347396) corresponden al anuncio. La investigación previa corroboró la relación institucional de Tim Bishop y revisó publicaciones de su perfil en Chrome; el historial está en el informe de antecedentes. Una publicación social orienta, pero las reglas oficiales deciden.

Crear al abrirse el reto un documento REGLAS_2026 con fecha de consulta, URL, texto o copia autorizada y respuestas a esta matriz:

| Tema | Respuesta necesaria | Acción antes de asumir |
| --- | --- | --- |
| Elegibilidad | Qué estudiantes pueden competir y optar a premios; membresía requerida | Contrastar situación personal con texto oficial |
| Equipo | Trabajo individual, tamaño permitido y reglas de colaboración | Confirmar aunque participemos solos |
| Objetivo | Predicción, herramienta, benchmark u otro producto; usuario y decisión | Redactar un contrato de éxito |
| Evaluación | Métrica, sentido de mejora, pesos del jurado y criterios | Implementar y comprobar cada cálculo |
| Entrega | CSV, notebook, informe, video, repositorio o archivos adicionales | Registrar canal, formato y acceso exigidos |
| Plazos | Hora y zona de apertura, cierre y posibles cierres separados | Convertir a America/Bogota y fijar margen interno |
| Envíos | Límite diario, número de selecciones finales y criterio de selección | Diseñar política de envíos |
| IA | Proveedores, herramientas, modelos, APIs y documentación exigida | Registrar permisos y restricciones |
| Datos | Fuentes externas, pseudoetiquetas, datos del test y licencias | Mantener inventario de procedencia |
| Cómputo | Internet, GPU, cuotas, dependencias y entorno de evaluación | Probar el entorno permitido |
| Publicidad | Qué debe hacerse público y cuándo; anonimato si aplica | Revisar datos, secretos y derechos |
| Premios | Importes, requisitos, verificaciones y exclusiones | No trasladar las condiciones de 2025 |

No cambiar rules_confirmed a true por haber leído un anuncio. Debe haber reglas suficientes para completar el contrato y resolver las decisiones que afectan al método. Una ambigüedad material se formula con cita y pregunta concreta al canal oficial; esta guía no autoriza enviar mensajes a terceros.

## Lo que enseñó la edición 2025

El reto de [IAA 2025](https://www.kaggle.com/competitions/ai-assisted-hackathon-1/overview) trabajó con Ames Housing y RMSLE, del 28 al 30 de noviembre. La rúbrica histórica asignaba 30% a predicción, 30% a uso creativo de IA, 20% a interpretabilidad y 20% a documentación, prompts y reproducibilidad. También había condiciones de equipos, envíos, elegibilidad y premios. Todo ello es antecedente, no regla vigente de 2026.

La [IAA anunció los ganadores en enero de 2026](https://actuaries.org/news-post/news-brief-january-21-2026/): Ryoichi Asashiba primero, Funky Turtles segundo, Tajmahal Ghaza Antoni tercero y Kohei Kudo con mención especial por su flujo de agentes. La selección tuvo cribado con IA, clasificación híbrida y revisión humana final.

| Premio 2025 | Puesto privado predictivo registrado | RMSLE histórico | Lectura para nuestra preparación |
| --- | --- | --- | --- |
| Ryoichi Asashiba, primero | 3 | 0.11372 | Explicación, razonamiento y uso de IA acompañaron al modelo |
| Funky Turtles, segundo | 10 | 0.11560 | El uso amplio y crítico de IA tuvo valor en la candidatura |
| Tajmahal Ghaza Antoni, tercero | 1 | 0.07722 | El mejor score privado no obtuvo el primer premio del jurado |
| Kohei Kudo, mención | 18 | 0.11789 | El flujo auditable de propuestas y evaluación mereció reconocimiento |

Los puestos y scores proceden del [leaderboard histórico](https://www.kaggle.com/competitions/ai-assisted-hackathon-1/leaderboard). No conocemos todas las notas individuales del jurado ni podemos atribuir causalmente cada premio a un componente. La lección operativa es preparar el modelo y la evidencia que permite evaluarlo.

La investigación catalogó 32 entradas de Code y examinó 11 notebooks. Las entradas pueden incluir versiones o ejemplos; no equivalen a 32 equipos ni representan todos los participantes. El [catálogo](Antecedentes/catalogo_notebooks_iaa_2025.csv) conserva las referencias. No se reprodujeron independientemente sus entrenamientos.


## Soluciones de 2025 que debemos recordar

| Proyecto inspeccionado | Enfoque observado | Aplicación y cautela |
| --- | --- | --- |
| [Ryoichi Asashiba](https://www.kaggle.com/code/negoto/iaa-hackathon-learning-from-black-box-ensemble?scriptVersionId=282987774) | Ensamble LGB/XGB/CatBoost; SHAP, PDP, permutation importance y aproximación interpretable | Medir por separado precisión y fidelidad del sustituto; revisar imputación antes de folds y distinguir ausencia de dato desconocido |
| [Funky Turtles](https://www.kaggle.com/code/immanuelalvaro/final-iaa-submission) | ChatGPT y Gemini para hipótesis, variables semánticas y revisión; correcciones sobre garajes y sótanos; stacking | Conservar propuestas rechazadas y correcciones humanas; los hiperparámetros sugeridos por un LLM no sustituyen una búsqueda medida |
| [Tajmahal Ghaza Antoni](https://www.kaggle.com/code/tajmahalghazaantoni/final-submission?scriptVersionId=283009883) | Ames externo, log1p, variables, imputación modelada de LotFrontage y XGBoost con Optuna | Auditar solapamientos externos; la narrativa de stacking y el código final no eran equivalentes; vincular el CSV exacto a su versión |
| [Kohei Kudo](https://www.kaggle.com/code/wideflat/kaggle-agent-submission) | Agente consulta diccionario y SHAP, propone variables, las evalúa y guarda memoria | Su mejora CV declarada no es mejora privada demostrada; evaluar cada propuesta y resolver discrepancias de licencia antes de reutilizar código |
| [Snorlax](https://www.kaggle.com/code/wendylow/snorlaxcode-final-notebook) | R, H2O AutoML y combinación jerárquica | Automatizar búsqueda conserva la obligación de conocer folds, pesos y selección |
| [SberIns](https://www.kaggle.com/code/artemkhakimov/sberins-team-notebook) | LightAutoML, Ames externo y análisis de drift | Comparar fuentes y cambio de distribución antes de mezclar datos |
| [Zky Fauzi](https://www.kaggle.com/code/zkyfauzi/iaa-hackathon-2025) | Box-Cox y stacking | Ajustar transformaciones dentro del entrenamiento y comprobar la inversa |
| [Kenta Ito](https://www.kaggle.com/code/tmon01/final-lgb-xgb-catboost-ensemble) | Target encoding por fold, boosting y semillas | Una fórmula final repetía predicciones LGB en el término de XGB: comprobar el vector realmente enviado |
| [Seleris](https://www.kaggle.com/code/selerisai/final-submission) | Pseudoetiquetas, stacking y cruces con Ames externo | No recuperar etiquetas del test ni tomar esa práctica como recomendación; aclarar reglas y procedencia antes de usar externos relacionados |
| [Attila G](https://www.kaggle.com/code/attiguyas/summary) | Cursor, variables derivadas de errores y restricciones monótonas | Las restricciones necesitan fundamento del dominio y validación |
| [Be_uec](https://www.kaggle.com/code/hibikiayabe/iaa-notebook) | LLM y CatBoost con Optuna | Separar la aportación de la IA del optimizador y del modelo |

El [repositorio del agente de Kohei](https://github.com/wideflat/kaggle-iaa-hackathon) ayuda a entender el ciclo de propuestas, pero las licencias se revisan en la versión concreta. Un proyecto premiado también puede contener un error, una dependencia móvil o una afirmación insuficientemente comprobada.

## Etapa previa a la apertura

La salida de esta etapa es poder empezar con los datos oficiales sin improvisar el entorno, el registro o el criterio de selección.

- [ ] Conservar comprobante de inscripción y aclarar elegibilidad de premios como estudiante.
- [x] Tener entorno Python aislado, notebooks de ensayo y registro de experimentos.
- [x] Conservar pruebas de repetición local y simulación Kaggle.
- [ ] Probar una versión privada del notebook en Kaggle alojado con datos sintéticos y guardar su salida.
- [ ] Confirmar qué proveedores de IA se podrán usar y preparar un primer registro real si las reglas lo permiten.
- [ ] Preparar un diccionario de datos vacío, matriz de requisitos y lista de preguntas pendientes.
- [ ] Comprobar que otra ejecución puede cargar el modelo y generar el archivo sin depender de celdas manuales.
- [ ] Reservar una entrega temprana de ensayo cuando la competencia y sus reglas lo permitan.

Comandos desde PowerShell en C:\dev\Hakaton\Preparación:

~~~powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
.\.venv\Scripts\python.exe scripts\start_lab.py
~~~

Seleccionar el kernel IAA Hackathon (Python 3.12) y abrir el notebook local. No hace falta activar el entorno ni modificar la política de PowerShell. Para una comprobación integral tras cambios funcionales:

~~~powershell
.\.venv\Scripts\python.exe scripts\verify_project.py
~~~

No repetir entrenamiento por una modificación exclusivamente editorial. Conservar la fecha de cada verificación; un reporte anterior no certifica código cambiado después.

La comunidad reúne material en [Learning ChatGPT Assisted Modelling](https://www.aiforactuaries.org/posts/learning-chatgpt-assisted-modelling), [Module 1](https://www.aiforactuaries.org/posts/learning-module-1-introduction) y [Course notes code and data](https://www.aiforactuaries.org/posts/learning-course-notes-code-and-data). Se verificaron enlaces de materiales, no todos sus archivos. Su lectura complementa las pruebas del proyecto.

Los anuncios de webinars ASTIN del [22 de octubre](https://actuaries.org/event/astin-webinar-understanding-modern-ai/) y [27 de octubre](https://actuaries.org/event/astin-webinar-ai-in-practice-building-real-actuarial-tools-from-prompts-to-production/) indicaban 08:00–09:00 EDT, equivalente a 07:00–08:00 en Bogotá. Confirmar horarios e inscripción cerca de la fecha. No hay recordatorios ni automatizaciones creadas.

## Etapa de apertura y contrato del reto

El primer día debe producir una definición verificable de qué vamos a construir, con qué información y cómo se juzgará. Descargar únicamente datos autorizados, guardar los originales sin modificar y calcular sus hashes. Archivar las reglas y el diccionario antes de diseñar variables.

Completar configs/competition.yaml con nombres reales de ID y objetivo, rutas, métrica, partición, modelos, hipótesis y reglas confirmadas. Conservar la configuración de cada variante. El runner rechaza campos pendientes relevantes; no eludir esa comprobación.

Si el reto es regresión tabular, aprovechar el runner actual. Si es clasificación, extracción, razonamiento o herramienta actuarial, adaptar objetivo, interfaces, métricas y pruebas antes de usarlo. RMSLE y Ames Housing pertenecieron a 2025; no deben convertirse por inercia en la solución de 2026.

El contrato escrito debe responder:

1. Quién usaría el resultado y qué decisión le ayudaría a tomar.
2. Qué datos existen al momento de esa decisión.
3. Qué entrada y salida exactas se requieren, con unidades y restricciones.
4. Qué significa mejorar según la métrica oficial y el juicio profesional.
5. Qué situaciones quedan fuera del alcance.
6. Qué evidencia permitirá a otro actuario revisar o adaptar la solución.

Asignar cada requisito a una comprobación y un artefacto. Por ejemplo, reproducir un CSV exige comando, configuración, modelo o entrenamiento, entorno y hash; demostrar utilidad de una extracción exige casos etiquetados, referencia correcta y revisión de errores. Una descripción persuasiva sin esas pruebas deja el requisito abierto.

## Datos y disponibilidad de la información

Preparar un diccionario por variable: significado, tipo, unidad, valores válidos, faltantes, fuente, momento de disponibilidad, entidad y posible dependencia del objetivo. Conservar las columnas originales cuando se creen representaciones derivadas.

Revisar IDs únicos, entidades repetidas, fechas, duplicados exactos y aproximados, rangos imposibles, categorías nuevas y cambios de distribución. Documentar cualquier descarte. Una variable disponible después del siniestro o del cierre contable puede ser una fuga aunque tenga excelente CV.

El código actual valida esquema de train/test, IDs únicos y disjuntos, ausencia del objetivo en test y correspondencia de filas y orden del sample_submission. Excluye ID, objetivo y columnas de grupo o tiempo de los predictores. Si una de estas columnas tiene señal legítima, incorporarla requiere una decisión explícita y una implementación adecuada; no está resuelto cambiando su nombre.

Distinguir ausencia estructural, cero real y dato desconocido. En vivienda, “sin garaje” no equivale a “tamaño de garaje no registrado”; en seguros, cero siniestros no equivale a exposición no informada. Ajustar imputación, escalado, codificaciones, selección y modelos auxiliares solamente con datos de entrenamiento del fold.

Para datos actuariales, comprobar exposición y denominadores: frecuencia por póliza o por unidad expuesta, severidad condicionada a siniestro, prima pura, importes nominales o reales y horizonte de observación. La descomposición frecuencia por severidad necesita definiciones compatibles y supuestos defendibles. No asumir independencia ni tratar una tasa como importe.

Inventariar cualquier fuente externa: URL, fecha, versión, licencia, acceso, contenido usado, duplicados, relación con train/test y autorización. No buscar etiquetas del test mediante cruces con una base conocida. Si hay ambigüedad sobre datos externos relacionados, resolverla antes de entrenar con ellos.

La salida de esta etapa es un diccionario, informe de calidad, inventario de fuentes y contrato de entrada que pueda verificarse automáticamente.


## Ingeniería relacional y señales de captura

Si el reto incluye varias tablas por póliza, cliente o siniestro, definir primero la granularidad de la predicción. Agregar los historiales al nivel de esa entidad antes de unirlos a la tabla principal. Comprobar cardinalidad de cada join, número de filas, claves sin correspondencia y duplicaciones que alteren exposiciones o importes.

Probar conteos, fechas de último evento, ventanas históricas, sumas, extremos, dispersión y tendencias que estén disponibles al origen de predicción. Los eventos posteriores al origen quedan fuera de esas agregaciones. Si se aprende una codificación, imputación o selección de variables, ajustarla dentro del fold.

DuckDB e Ibis permiten trabajar con tablas grandes sin cargar todos los intermedios en pandas. El [ejemplo del proyecto Ibis con Home Credit](https://ibis-project.org/posts/ibisml/) sirve como referencia de ingeniería, no como prueba de una arquitectura ganadora. Comparar su utilidad frente a pandas y documentar esquema, consulta, ventanas y versión.

Los IDs, nombres y metadatos de captura pueden representar entidad, cohorte o artefactos del generador. Conservarlos para el diagnóstico, pero incluirlos como predictores solo tras comprobar permiso, disponibilidad y generalización a entidades nuevas. El runner actual excluye el ID: estudiar una representación legítima requiere un cambio explícito.

En textos, conservar una copia sin normalización y contrastar cada limpieza. Saltos de línea, encabezados y estructura pueden ser señal; el tamaño de un archivo también puede reflejar el proceso de captura. Distinguir señal transferible de un atajo de la fuente.

OpenFE y xfeat son opciones por evaluar, no dependencias instaladas ni garantía de buenas variables. La selección automática debe respetar nuestros grupos y fechas aunque una biblioteca proponga un split predeterminado. No aceptar una afirmación general de incompatibilidad de GPU sin comprobar versión y operación.

La prueba de esta etapa compara variables básicas, agregaciones y señales de captura por separado, con las mismas particiones y errores por fuente o entidad nueva.

## Validación que permita elegir con confianza

Elegir la partición según cómo aparecerán los casos del test o del uso profesional.

| Situación | Validación candidata | Riesgo que debe comprobarse |
| --- | --- | --- |
| Filas independientes de la misma población | Kfold, con estratificación apropiada si aplica | Entidades repetidas o duplicados ocultos |
| Varias filas por póliza, persona, empresa o documento | Group split | Información compartida entre entrenamiento y validación |
| Predicción sobre periodos futuros | Backtests hacia adelante | Datos y etiquetas todavía no disponibles al origen |
| Nuevas entidades y nuevas fechas | Partición conjunta diseñada a medida | Resolver solo el tiempo o solo la entidad puede ser insuficiente |
| Extracción o NLP con fragmentos relacionados | Agrupar por documento y origen | Fragmentos del mismo documento en ambos lados |
| Datos externos o sintéticos | Evaluación final sobre casos reales reservados | El generador o la fuente externa pueden contaminar la evaluación |

La implementación temporal mantiene juntas las filas de una misma fecha. gap_periods cuenta periodos únicos, no días de calendario. Diseñar el embargo según el horizonte de las etiquetas y los solapamientos; un parámetro de gap no garantiza por sí solo causalidad temporal.

Separar el conjunto reservado final de la validación usada repetidamente para desarrollar. Congelar las decisiones que se van a comprobar antes de observar su resultado. Si usamos CV anidada, todo el proceso de selección debe ocurrir dentro del entrenamiento exterior: variables, imputación, tuning, pseudoetiquetas, generadores, modelos y combinador. Reservar un fold solamente para elegir pesos de OOF ya construidas no equivale a validar todo el pipeline anidado.

Conservar índices de folds, hashes, semillas y reglas de elegibilidad temporal. Cada comparación usa los mismos casos, escala del objetivo y métrica. Reportar resultado agregado, dispersión y diferencias por fold; una ganancia pequeña debe contrastarse con su estabilidad y su coste de complejidad.

No escoger arquitectura, pesos o umbrales mirando repetidamente el leaderboard. Una discrepancia grande con CV es una señal para revisar distribución, fuga y partición. Si hay pocos datos, equilibrar el coste de reservar casos con el riesgo de sobreselección y dejar documentado el diseño elegido.

La política completa está en [metodologías recientes](Antecedentes/metodologias_kaggle_2026.md). La CV anidada y el seguimiento de todos los ensayos avanzados son propuestas que todavía necesitan implementación.

## Validación por dominio y cambios de distribución

Cuando train mezcla fuentes, periodos o criterios de etiquetado, medir el resultado global y el del dominio al que se dirige la predicción. El segundo debe corresponder a un dominio identificable con información autorizada, no a etiquetas del test reconstruidas. Reportar tamaño y variabilidad de ambos.

En [Automated Essay Scoring 2.0](https://www.kaggle.com/competitions/learning-agency-lab-automated-essay-scoring-2/writeups/flg-1st-place-solution-trust-cv-and-lb-a-bit), el ganador separó preentrenamiento con ensayos antiguos y ajuste con los nuevos, además de pseudoetiquetado y umbrales. El texto aportado simplifica esa solución: también comparó rondas de pseudoetiquetas, promedió semillas y controló sobreajuste. No convierte su configuración de dropout en una regla general.

La validación adversarial puede ayudar a detectar variables que distinguen fuentes o train de test. No prueba por sí sola que ponderar observaciones o eliminar esas variables mejore la tarea. Toda decisión resultante necesita evaluación exterior y respeto de las reglas sobre uso del test.

Si se estratifica un objetivo continuo por cuantiles, usar una discretización apropiada: [pandas.qcut](https://pandas.pydata.org/docs/reference/api/pandas.qcut.html) forma grupos por cuantiles; [pandas.cut](https://pandas.pydata.org/docs/reference/api/pandas.cut.html), con un entero, crea intervalos de igual anchura. No son equivalentes. Elegir número de grupos según los casos disponibles; 25 no es un valor obligatorio.

La estratificación no sustituye agrupación ni orden temporal. Mantener un paciente, póliza o documento en un solo lado, aunque empeore el balance. En cada backtest, reconstruir estadísticas móviles con el estado histórico disponible y probar reinicios, primeras observaciones y categorías nuevas.

## Baseline y primer ciclo de experimentos

El primer baseline debe generar una salida válida y explicar qué aporta respecto de un predictor trivial. El proyecto compara seis regresores; no es obligatorio conservarlos todos en la candidatura.

El Dummy establece una referencia mínima. Ridge ayuda a detectar relaciones simples y problemas de escala. HistGradientBoosting ofrece una referencia local. CatBoost, LightGBM y XGBoost forman un portafolio de boosting que debe evaluarse con el mismo contrato. Los parámetros actuales están fijados en src/iaa_lab/models.py: escribir model_params en un YAML no habilita un optimizador que no existe. Optuna está instalado, pero su integración y persistencia de trials están pendientes.

Para RMSLE, el runner usa log1p y expm1 y declara el recorte no negativo. Para otras métricas, comprobar unidades, transformación inversa, tratamiento de ceros y dirección de mejora. Las métricas actuales son RMSLE, RMSE y MAE; añadir una métrica oficial distinta requiere implementación y pruebas sobre casos conocidos.

~~~powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --config configs\demo.yaml
~~~

Tras completar y validar las reglas, el mismo script puede leer configs/competition.yaml para regresión. Solo genera datos sintéticos cuando el modo es demo.

El ciclo de una variante es:

1. Escribir una hipótesis concreta, su fundamento y la información que requiere.
2. Definir de antemano el criterio de aceptación y los riesgos de fuga.
3. Registrar los prompts reales y enlazar sus prompt_ids en experiment.prompt_ids.
4. Guardar una configuración identificable y hacer la corrida.
5. Revisar OOF, métricas por fold, segmentos, tiempo y errores.
6. Comparar con el baseline y hacer la ablación que aísle el cambio.
7. Marcar aceptada, rechazada o pendiente con evidencia y explicación.
8. Actualizar memoria, sin borrar resultados desfavorables.

Una corrida crea artifacts/runs/<run_id> y registros en logs/experiments.csv y logs/experiments.jsonl. Conserva modelo, configuración, predicciones, particiones, hashes, entorno y snapshot. El runner comprueba que el código y los datos no cambien durante el entrenamiento. No editar esos archivos mientras una corrida está activa.

## Portafolio de metodologías recientes

Estas 20 familias proceden de la investigación de competiciones y literatura técnica. La decisión correcta depende del problema y de las reglas. Las familias avanzadas son candidatas, no ventajas demostradas en IAA 2026.

| ID | Método | Cuándo probarlo | Qué debe decidir su adopción |
| --- | --- | --- | --- |
| M01 | Validación parecida al test y evaluación anidada del pipeline | Siempre que haya selección repetida o estructura de entidades y tiempo | Rendimiento exterior y ausencia de información futura |
| M02 | Portafolio tabular de boosting, RealMLP, TabM, embeddings numéricos y AutoGluon | Tabular con señal que distintos inductivos puedan captar | Comparación común, errores complementarios y coste real |
| M03 | TabPFN y TabICL con checkpoint identificado | Datos tabulares compatibles con sus límites y licencia | Versión, procedencia, prueba exterior y ablación |
| M04 | Logs, ratios, diferencias, bins y copias categóricas; target encoding OOF | Variables con estructura o semántica que el baseline no aprovecha | Disponibilidad, estabilidad y transformación dentro del fold |
| M05 | Credibilidad, shrinkage y pooling jerárquico | Grupos pequeños, exposición desigual y entidades nuevas | Error por tamaño de grupo y comparación con referencia global |
| M06 | Imputación consistente y banderas de faltantes | Faltantes informativos o restricciones de dominio | Experimento de enmascaramiento y ausencia de ajuste global |
| M07 | Biblioteca de OOF y análisis de complementariedad | Hay varios candidatos estables | Ganancia marginal exterior, correlación de errores y deduplicación |
| M08 | Promedio, selección greedy, Ridge, logits y stacking de varias capas | OOF alineadas y suficientes casos | Evaluar el proceso completo; una capa adicional puede sobreajustar |
| M09 | Objetivo, transformación, calibración o umbral alineados con métrica | Métrica no equivalente a la pérdida estándar | Selección interna, unidades correctas y reserva final |
| M10 | Frecuencia y severidad, cero y positivo, ordinales o expertos | La estructura del objetivo lo justifica | Coherencia de definiciones y mejor resultado extremo a extremo |
| M11 | Backtests, drift, purging, ventanas y ponderación temporal | Mercado, siniestros o demanda que cambian | Múltiples orígenes temporales y disponibilidad de etiquetas |
| M12 | Fuentes externas y preentrenamiento permitido | Fuente legítima con información adicional | Licencia, deduplicación, permiso y ablación de la fuente |
| M13 | Pseudoetiquetas y destilación | Señal adicional sin etiquetas de evaluación | Teacher sin etiquetas exteriores; comparación con y sin pseudo |
| M14 | Simulación programática, SMOTE o CTGAN | Reglas o generador verificables; desequilibrio relevante | Generación solo en train; evaluación real con prevalencia natural |
| M15 | TF-IDF, encoders, ranking de candidatos y LLM ajustado | Texto y etiquetas o esquema suficientes | Split por documento, exactitud, coste y salida restringida |
| M16 | Reglas, cálculo Python, modelo tabular y LLM en un flujo híbrido | Tarea profesional con cálculos y explicación | Contratos de cada etapa y errores del flujo completo |
| M17 | IA para proponer, implementar y auditar cambios con registro común | Hipótesis o código que se pueden contrastar | Aportación medida, trazas y reserva final fuera del contexto |
| M18 | Optuna o AutoML sobre arquitectura, regularización y representación | Espacio de búsqueda definido | Todos los trials registrados y selección interna |
| M19 | Promedio por fold, refit completo y múltiples semillas | Variabilidad apreciable o modelo final distinto al CV | Comparación interna del procedimiento de inferencia |
| M20 | Referencia interpretable, SHAP, sustituto y dossier verificable | Se necesita entender y adaptar el resultado | Fidelidad independiente, errores por segmento y corrida limpia |

La novedad no es un criterio suficiente para incluir un modelo. Priorizar cambios con una hipótesis fuerte y medirlos. Añadir modelos porque aparecen en muchos writeups puede generar coste, redundancia y sesgo de selección sin mejorar la candidatura.

Las fuentes técnicas incluyen [TabM](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c1ba41c694834aeef91ae161711d4939-Abstract-Conference.html), [pytabkit](https://github.com/dholzmueller/pytabkit), [TabPFN](https://github.com/PriorLabs/TabPFN), [TabPFN 3.5](https://arxiv.org/abs/2609.17895), [TabICL](https://github.com/soda-inria/tabicl) y [AutoGluon](https://github.com/autogluon/autogluon). Verificar checkpoint y licencia en la fecha de uso, incluida la [licencia de pesos TabPFN 3.5](https://huggingface.co/Prior-Labs/tabpfn_3_5/blob/main/LICENSE). No se han instalado ni comparado todos esos modelos aquí.

## Ensambles y selección de OOF

Cada archivo OOF necesita ID de fila, fold, objetivo, predicción, escala, clases si aplica, run_id, hashes de datos y procedencia del modelo. Rechazar archivos con filas desalineadas, folds incompatibles o entrenamiento que incluya la etiqueta de la propia fila.

Comparar primero promedio simple y combinador regularizado. Evaluar mejora marginal de cada candidato y correlación de errores, especialmente en segmentos y extremos. Un modelo con score individual inferior puede aportar diversidad; uno mejor puede no añadir nada a un ensamble ya equivalente.

Ajustar pesos, umbrales y selección de candidatos dentro de la validación interna. Para stacking anidado, reconstruir las OOF internas dentro de cada entrenamiento exterior. No convertir una búsqueda sobre cientos de OOF en una única estimación supuestamente imparcial.

Antes del CSV, comprobar que cada término de la fórmula usa el vector previsto, que los pesos y transformaciones coinciden con el modelo seleccionado y que el orden de IDs es correcto. La repetición accidental de predicciones observada en 2025 justifica una prueba sobre los componentes reales.

El runner actual guarda OOF, pero no implementa biblioteca de ensambles ni stacking. Hay que construir y verificar esas capacidades antes de describirlas como parte de la solución.

## Selección de ensambles sin un umbral universal

La selección hacia adelante agrega el candidato que mejora el conjunto actual según el criterio interno. Compararla con promedio simple y combinador regularizado. Registrar modelos candidatos, pesos, orden de inclusión y punto de parada.

El umbral +0.0003 del texto aportado no es una regla de Kaggle ni sirve indistintamente para RMSE, AUC o QWK. Definir una diferencia relevante en las unidades de la métrica oficial y contrastarla con la variabilidad de la comparación. Si se calculan intervalos, respetar la dependencia entre entidades o periodos.

El [caso S4E8 de Optimistix](https://www.kaggle.com/competitions/playground-series-s4e8/writeups/optimistix-1st-place-solution-72-oofs-a-whole-lott) documenta una biblioteca extensa de OOF, AutoGluon, Ridge y selección iterativa. También relata costes de búsqueda y combinaciones guiadas por leaderboard. Sirve para estudiar diversidad, no para fijar una cantidad mínima de modelos ni adoptar todas sus decisiones.

Para capas sucesivas, cada predicción intermedia debe quedar fuera de muestra para la fila usada por el siguiente modelo. La selección de candidatos sobre esas OOF también debe estar dentro del proceso evaluado. Guardar 72 vectores no elimina el sesgo de elegir repetidamente sobre ellos.

La fusión de pesos requiere una evaluación diferente a la mezcla de predicciones. Comparar los artefactos resultantes, su score y su coste; no llamar ensamble equivalente a una operación que solo combina parámetros.

## Datos sintéticos y pseudoetiquetas

Estas técnicas solo se prueban si están permitidas y responden a una hipótesis. El teacher, el generador y su selección no deben ver etiquetas de la evaluación exterior. Conservar el conjunto real reservado y su prevalencia natural.

Comparar entrenar sin datos añadidos, con la fuente añadida y con variaciones de su peso. Auditar duplicados, distribución, casos extremos y errores por segmento. Un generador que replica el entrenamiento puede aparentar rendimiento sin aportar generalización.

En simulación actuarial, declarar supuestos, distribución, dependencias y restricciones. Validar invariantes y casos límite con cálculos conocidos. No presentar simulación como evidencia empírica de una población real.

Las particularidades de datasets Playground, como patrones de dígitos, no son automáticamente señal profesional transferible. Tampoco trasladar ajustes de offset basados en leaderboard ni recuperación de etiquetas del test. La documentación debe mostrar qué información autorizada produjo cada mejora.


## Recuperación documental y especialización de modelos

Si el reto exige localizar cláusulas, referencias o explicaciones, comparar una búsqueda léxica con recuperación por embeddings y un reordenador. Medir la recuperación del fragmento correcto entre los candidatos antes de evaluar la respuesta final. Un buen reordenador no puede recuperar un documento omitido por la primera etapa.

El [primer puesto de Eedi](https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics/writeups/mth-101-1st-place-detailed-solution) usó un esquema de recuperación y reordenamiento para identificar errores matemáticos. La transferencia candidata es un buscador que devuelve evidencia concreta y después evalúa su pertinencia, con documentos agrupados y referencias comprobadas.

Comparar salidas restringidas, clasificación de secuencia y generación cuando respondan al mismo contrato. En [LMSYS, BlackPearl](https://www.kaggle.com/competitions/lmsys-chatbot-arena/discussion/527629) declaró clasificación de secuencia, destilación de modelos grandes, combinación de LoRA y GPTQ. Ese caso contradice la supuesta superioridad universal de usar un modelo causal para clasificar. Sus arquitecturas históricas no sustituyen una comparación con modelos actuales.

El ajuste de dominio, los adaptadores y la destilación se prueban cuando el baseline deja un error concreto que resolver. Registrar corpus, licencias, tokenizer, checkpoint, módulos y parámetros entrenables. El teacher no debe usar las etiquetas de la evaluación exterior. Comparar teacher, student y student destilado con calidad, coste y latencia.

Si hay visión o documentos escaneados, probar localizar la región relevante, extraerla y después interpretar o clasificar. El [ganador RSNA 2024](https://www.kaggle.com/competitions/rsna-2024-lumbar-spine-degenerative-classification/writeups/avengers-1st-place-solution) describió dos etapas con localización y severidad. Para una herramienta documental, medir primero localización y OCR, después extracción y cálculo. Inyectar fallos realistas de la primera etapa en las pruebas de la segunda.

La integración de fuentes heterogéneas necesita contratos compatibles. [GOAlpha, en CAFA 6](https://www.kaggle.com/competitions/cafa-6-protein-function-prediction/writeups/1st-place-solution-for-the-cafa-6-protein-function), combinó evidencia de secuencia, estructura, redes, dominios y literatura con Learning-to-Rank. Usar ese patrón si la salida es ranking; para importes o probabilidades, elegir un combinador pertinente y medir cada fuente por ablación.

La misma disciplina se aplica a predicciones de texto o imagen añadidas a un modelo tabular: generar la señal fuera de muestra y evaluar la cadena completa. Las configuraciones médicas, porcentajes de prevalencia y scores de otras ediciones no describen una cartera actuarial.

## Uso creativo de IA que podamos demostrar

Diseñar la IA alrededor de una tarea actuarial concreta: revisar un diccionario, detectar una incoherencia, proponer una variable, extraer una condición contractual, ayudar a comparar escenarios o explicar un cálculo verificable. La aportación debe relacionarse con una necesidad y una prueba.

El patrón más defendible combina capacidades especializadas. Python calcula importes, unidades e invariantes; reglas verifican condiciones; un modelo estima; el LLM interpreta documentación y explica con referencias. Definir qué ocurre cuando falta información o una etapa falla. Un texto fluido no corrige un cálculo incorrecto.

Para cada componente de IA registrar entrada, salida, modelo, parámetros, contexto, herramientas, revisión humana y prueba. Comparar el flujo completo con una referencia simple y, cuando sea viable, retirando ese componente. Medir precisión, errores críticos, tiempo, estabilidad y utilidad para el usuario según la tarea. Una evaluación humana debe conservar criterios y ejemplos, sin inventar aprobación.

Los aprendizajes de otros hackathons son concretos:

| Caso y fuente | Qué aporta a la preparación | Qué no podemos asumir |
| --- | --- | --- |
| [Gemma Vision](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/gemma-vision), ganador Gemma 3n | OCR especializado antes de explicación multimodal; diseño accesible; [código](https://github.com/TGTech06/gemma-vision) y release | Su premio no demuestra exactitud en documentos actuariales; no se ejecutó su repo aquí |
| [G-RaR](https://www.kaggle.com/competitions/google-tunix-hackathon/writeups/new-writeup-1768107128907), ganador Tunix | Rúbricas y recompensa híbrida con SFT/GRPO; separar formato, exactitud y juicio semántico | Una traza de razonamiento no prueba una respuesta correcta; un juez LLM no es verdad de referencia |
| [GEM-4](https://github.com/takaki-maeda-99/GEM-4-VLA), primer premio Gemma 4 Good | Modelo mayor prepara anotaciones y un controlador especializado actúa; pesos y configuraciones identificados | Usar pesos publicados, ajustar y entrenar desde cero son procedimientos distintos; documentación incompleta limita reproducción |
| [TrueVoice](https://www.kaggle.com/competitions/gemma-4-good-hackathon/writeups/new-writeup-1776369081947), Safety and Trust | Codificador congelado, cabeza específica y degradaciones realistas de audio | Rama móvil, pesos main y diferencias de dtype afectan reproducción; un enlace de demo temporal no basta |
| [MEDLEY-BENCH](https://github.com/ki-smile/medley-bench), Grand Prize Measuring AGI | Evalúa presión, actualización apropiada y consistencia con conversaciones de varios pasos y resultados brutos | Un benchmark pequeño no demuestra seguridad general; discrepancias de scores deben documentarse |
| [Echoes of Interest](https://www.kaggle.com/competitions/meta-kaggle-hackathon/writeups/echoes-of-interest) | Recomendación con embeddings, votos, novedad y particiones de usuario y tiempo | La creatividad puede venir del diseño útil sin que GenAI sea el centro |

Los premios se contrastaron con anuncios oficiales, como [Tunix](https://developers.googleblog.com/en/how-the-community-trained-gemma-to-think-with-tunix-and-tpus/), [Gemma 3n](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/hackathon-winners), [Gemma 4 Good](https://www.kaggle.com/competitions/gemma-4-good-hackathon/hackathon-winners), [Measuring AGI](https://www.kaggle.com/competitions/kaggle-measuring-agi/discussion/724918) y [Meta Kaggle](https://www.kaggle.com/competitions/meta-kaggle-hackathon/discussion/598833). El informe detallado cubre ocho competiciones y seis casos; no se ejecutó código de terceros.

Gemma 3n y Gemma 4 Good usaron pesos de impacto, video y técnica propios; Tunix valoró notebook, modelo y video; Agents Intensive Capstone distinguió presentación e implementación. Esas rúbricas ayudan a pensar qué evidencia hace visible un proyecto, pero no fijan pesos ni entregables para IAA.

De [AI Agent Security](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/overview/prizes) interesa la evaluación con fixtures y replay verificable. De [FREUID 2026](https://freuid2026.microblink.com/reproducibility.html), fijar código, dependencias, pesos y salida para una verificación sin red. Docker obligatorio en esa competencia no implica Docker obligatorio aquí. El estándar [SIGMOD de reproducibilidad](https://reproducibility.sigmodconf.hosting.acm.org/index.html) distingue disponibilidad, reutilización y reproducción independiente; debemos usar esas palabras con precisión.

## Prompts y contexto completos

Conservar el intercambio exacto, no una reconstrucción posterior. Un registro incluye propósito, proveedor, identificador del modelo, revisión conocida o null, mensajes en orden con sus roles, parámetros, herramientas declaradas, respuesta cruda, uso reportado y decisión humana.

Los parámetros dependen del proveedor. Registrar los realmente enviados y los valores predeterminados conocidos; no inventar una semilla o un detalle del backend. Temperatura cero no garantiza identidad entre versiones o infraestructuras. Si el proveedor no revela una revisión, declarar esa limitación.

El contexto tiene dos funciones que deben distinguirse:

- Lo que se envía al modelo debe aparecer en messages, con los fragmentos, tablas o instrucciones exactos.
- context_files y context_texts conservan evidencia, copias y hashes. Añadir una ruta no envía automáticamente ese archivo al endpoint.

Si se usó una web o documento, conservar el contenido consultado o los fragmentos exactos autorizados, fecha, URL y referencia. Un enlace solo no reconstruye una página que cambió. No incorporar credenciales a mensajes, parámetros, herramientas ni registros. Separar el archivo privado completo de la versión autorizada para el jurado, explicando cualquier redacción y conservando la evidencia pertinente.

Las plantillas están en [plantillas básicas](prompts/plantillas.md) y [competición avanzada](prompts/competicion_avanzada.md). Cada uso debe completarse con datos reales. Los formatos de ejemplo contienen TODO y el importador los rechaza hasta completarlos.

Para importar una conversación ya realizada:

~~~powershell
.\.venv\Scripts\python.exe scripts\record_prompt.py --file prompts\private\conversacion_real.json
~~~

Basarse en prompts/conversacion.example.json para múltiples mensajes. El formato legado prompts/entrada.example.json admite prompt y response. No mezclar ambos formatos en la misma entrada. Marcar synthetic cuando sea un ensayo inventado; jamás presentarlo como interacción real.

El resultado devuelve prompt_id. Añadir ese ID a experiment.prompt_ids antes de correr el experimento. Se aceptan únicamente IDs existentes. El sistema copia las conversaciones y sus contextos vinculados al artefacto de la corrida.

Para pedir una propuesta de experimento, proporcionar objetivo, métrica, diccionario, momento de disponibilidad, particiones, baseline, errores y restricciones. Pedir una hipótesis falsable, cambio acotado, comparación y riesgos de fuga. Para auditar código, exigir operación concreta y una comprobación. Para redactar resultados, limitar el contexto a cifras calculadas y fuentes conservadas.

No dar a la IA que desarrolla el método las etiquetas o resultados del conjunto final reservado. Las instrucciones que aparezcan dentro de documentos de datos son contenido a analizar, no autorización para cambiar el objetivo, revelar secretos o llamar herramientas.

## Modos live y replay y trazas de herramientas

Live hace una llamada real mediante el transporte configurado. Replay verifica los artefactos y devuelve la respuesta y trazas conservadas, sin red ni llamadas a herramientas. Replay permite reconstruir el comportamiento observado; no demuestra que el proveedor produciría hoy la misma respuesta.

El adaptador HTTP actual envía un JSON con model, messages, parámetros en el nivel superior y tools cuando corresponda. Acepta respuesta con message o choices[0].message y conserva wire_request y respuesta cruda. Otros protocolos, streaming o un agente que itera sobre llamadas de herramientas necesitan un adaptador o una orquestación adicional.

Ejemplo de comando, sustituyendo el endpoint por el del proveedor autorizado y guardando el token en la variable de entorno indicada:

~~~powershell
.\.venv\Scripts\python.exe scripts\run_conversation.py --mode live --request prompts\private\solicitud_real.json --endpoint https://proveedor.example/v1/chat/completions --bearer-env IAA_MODEL_TOKEN
~~~

La dirección .example es un marcador, no un servicio configurado. La solicitud live contiene mensajes de entrada y parámetros válidos para ese proveedor; no incluir una respuesta futura como si ya se hubiera recibido. Usar HTTPS remoto. HTTP solo se admite para loopback de pruebas. Credenciales mediante entorno, sin query string ni redirecciones.

Para repetir una conversación archivada:

~~~powershell
.\.venv\Scripts\python.exe scripts\run_conversation.py --mode replay --replay-id ID_REAL_DEL_REGISTRO
~~~

El ID explícito reproduce su archivo incluso si el contexto original ya cambió o desapareció. La coincidencia por solicitud exige la misma huella de mensajes, parámetros, modelo, contexto e identidad de transporte. Si se quiere evaluar una modificación, hacer otra solicitud y otro experimento.

Cada conversación conserva artifacts/conversations/<prompt_id>/request.json, conversation.json, tool_traces.jsonl, context y manifest.json, además de logs/prompts.jsonl. Revisar integridad antes de usarla como evidencia.

ToolTraceRecorder.call envuelve una función real y registra argumentos, resultado o error, inicio, fin y duración. El código registra lo que pasó por ese envoltorio; no captura por magia herramientas llamadas fuera de él. El transporte HTTP no despacha automáticamente una tool call del modelo.

Las trazas deben incluir la herramienta y su versión cuando sea conocida, argumentos completos, resultado, error, identidad del recurso consultado y relación con la conversación. Registrar una operación fallida y su recuperación. No convertir una traza manual de ejemplo en una ejecución real.

Live y replay empiezan con revisión humana pendiente. Una revisión anterior pertenece al intercambio original; no debe aprobar automáticamente la nueva ejecución. En importación, human_review describe lo que realmente se comprobó, corrigió o rechazó. Mantener el registro original y conservar las revisiones o decisiones posteriores de forma identificable; no reescribir silenciosamente la evidencia.

## Interpretabilidad y criterio actuarial

Explicar el modelo en relación con la decisión, las unidades y los datos disponibles. Un ranking de importancia no basta para entender si el resultado es razonable.

Comprobar errores por magnitud del objetivo, extremos, exposición, grupo, periodo y faltantes. Revisar signos, monotonicidad y relaciones esperadas con hipótesis del dominio; una restricción monótona impuesta puede ser incorrecta si cambia el contexto.

SHAP, PDP y permutation importance describen propiedades predictivas sujetas a sus supuestos. Las variables correlacionadas complican su lectura. No presentar una asociación como efecto causal. La [documentación de SHAP sobre causalidad](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html) explica este límite.

Si usamos un GLM, GAM, MID u otro sustituto para explicar un ensamble, separar dos preguntas: cuánto predice el objetivo real y cuánto reproduce al modelo complejo. Medir fidelidad en datos independientes y mostrar dónde falla. Una explicación legible puede ser infiel.

Para seguros, comparar con una referencia actuarial pertinente y comprobar exposición, calibración agregada, colas y segmentos. Si usamos frecuencia/severidad o Tweedie, fundamentar distribuciones y unidades; el [ejemplo oficial scikit-learn](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html) es una referencia técnica, no una validación del caso de la competencia.

Revisar privacidad y posibles sesgos relevantes para el uso declarado. Cuando exista una comparación entre grupos, conservar denominadores, incertidumbre y criterio; no inferir equidad solo porque una variable sensible se excluyó. Los tres papers IAA aportados el 13 de octubre se archivaron y revisaron para preparar la [matriz de prácticas prioritarias](Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md). Consultar allí las secciones sobre responsabilidad, interpretación, datos y gobernanza. Esa revisión documental no certifica cumplimiento profesional del proyecto.

La contribución humana debe aparecer en decisiones concretas: corrigió una unidad, rechazó una variable posterior al evento, detectó una cita incorrecta o cambió un supuesto. No inventar esa intervención para completar una narrativa.

## Robustez de una herramienta o flujo con LLM

Si el reto permite una aplicación, preparar casos de referencia antes de refinar los prompts. Incluir entradas válidas, información insuficiente, inconsistencias, unidades distintas, documentos mal formados y errores de herramientas. Los casos deben provenir de datos autorizados o fixtures explícitamente sintéticos.

Probar invariantes: conservación de sumas, escala de moneda, orden temporal, coherencia de tasas y denominadores, estabilidad ante cambios irrelevantes y respuesta a cambios que sí alteran el cálculo. Un resultado generado se contrasta con Python o una referencia independiente.

Para extracción, separar localización del fragmento, interpretación y cálculo. Verificar que la cita existe y sostiene la afirmación; encontrar una cadena en un documento no prueba que sea la cláusula aplicable.

En conversaciones de varios pasos, evaluar si el sistema actualiza su respuesta cuando cambia evidencia válida y si conserva conclusiones ante presión sin nueva evidencia. No premiar solo la firmeza ni solo la complacencia. Registrar cada paso y el estado utilizado.

Si una entrada contiene instrucciones incrustadas, tratarlas como material no confiable. Las herramientas operan con contratos definidos y deben fallar de forma visible cuando no hay información o autorización suficiente. Una abstención debe explicar qué dato falta; no esconder errores con texto genérico.

No declarar un flujo “seguro” o apto para producción por pasar un conjunto pequeño de pruebas. Describir qué fallos se evaluaron y qué uso está realmente respaldado.


## Cálculo verificado y búsqueda durante la inferencia

Cuando una respuesta requiere matemática exacta, permitir que el LLM proponga el planteamiento y contrastar el cálculo con funciones Python de contrato definido. Conservar entradas, unidades, resultado y errores. Evitar que código generado se ejecute con permisos amplios o acceso innecesario a archivos y red.

[Numina, ganador AIMO 1](https://huggingface.co/blog/winning-aimo-progress-prize), combinó entrenamiento de razonamiento y herramientas con ejecución de código y selección entre respuestas. La aplicación candidata para IAA es comprobar cálculos y corregir fallos con evidencia; una votación entre respuestas no prueba que la mayoría sea correcta.

Definir un máximo de intentos, criterio de parada y respuesta cuando el cálculo no puede verificarse. Si se asigna más esfuerzo a casos difíciles, medir el resultado por tipo de caso y el coste total. No descartar ceros o importes pequeños por heurísticas matemáticas de otro concurso.

La aumentación de inferencia solo debe usar transformaciones que preserven la respuesta: reformulaciones controladas, cambios de unidades con su inversa o vistas equivalentes de un documento. Verificar esa invariancia antes de promediar. Una transformación espacial útil en ARC puede alterar una cifra o cláusula en un documento.

[ARC Prize 2024](https://arcprize.org/competitions/2024) y su [informe técnico](https://arcprize.org/media/arc-prize-2024-technical-report.pdf) documentan el valor de la adaptación por tarea. En nuestro proyecto, cualquier actualización de pesos o estado durante inferencia necesita datos permitidos, aislamiento entre casos y replay del procedimiento. No usar etiquetas ocultas ni trasladar un resultado de ARC como mejora actuarial.

## Reproducibilidad y snapshots de código

Separar cuatro niveles de reproducción:

| Nivel | Evidencia necesaria |
| --- | --- |
| Inferencia | Modelo o pesos exactos, preprocesamiento, entradas, entorno, comando y salida |
| Entrenamiento | Datos autorizados, particiones, configuración, dependencias, semillas, hilos y criterio de selección |
| Interacción con IA | Mensajes y contexto completos, parámetros, versión conocida, respuesta cruda, herramientas y replay |
| Entrega completa | Notebook limpio que reconstruye tablas, gráficos, archivos y afirmaciones del informe |

El proyecto guarda source.zip y code_snapshot.json con contenido real y hashes. Incluye código, scripts, configuraciones, pruebas, notebooks y plantillas, además de archivos técnicos enumerados en snapshots.py. No depende de Git; actualmente este directorio no tiene repositorio Git.

Los datos originales quedan fuera del snapshot de código. Deben conservarse por una vía autorizada y recuperable; un hash prueba identidad si existe el archivo, pero no permite reconstruirlo. Las conversaciones se archivan aparte y se copian a las corridas que las vinculan.

Esta guía y AGENTS.md no entran automáticamente en la lista actual del snapshot. Si una decisión del experimento depende de esta memoria, incluirla como context_file o adjuntarla al dossier con su versión y hash. No afirmar que está en un ZIP sin revisar su inventario.

Para verificar un snapshot conservado:

~~~powershell
.\.venv\Scripts\python.exe scripts\restore_snapshot.py --manifest artifacts\runs\ID_CORRIDA\code_snapshot.json
~~~

Para restaurarlo, indicar una carpeta nueva:

~~~powershell
.\.venv\Scripts\python.exe scripts\restore_snapshot.py --manifest artifacts\runs\ID_CORRIDA\code_snapshot.json --destination artifacts\restaurado_nuevo
~~~

Sin destination el script verifica; con destination restaura. No sobrescribir el proyecto activo. Después reconstruir el entorno y aportar los datos y artefactos que no están dentro del código.

environment.json y requirements.observed.txt registran plataforma, runtime, versiones y ajustes de hilos. requirements.lock.txt corresponde al entorno local probado. Un lock de Windows no debe instalarse ciegamente en Linux. Las semillas no garantizan igualdad entre dispositivos o versiones; incluso [PyTorch lo documenta](https://docs.pytorch.org/docs/2.14/notes/randomness.html). Distinguir reproducción exacta de una reproducción dentro de tolerancias predefinidas.

El resultado ideal es que otra persona pueda seguir instrucciones desde un entorno limpio sin archivos ocultos ni celdas manuales. Hasta que lo haga, denominarlo verificación propia, no reproducción independiente.

## Notebook autónomo y ejecución en Kaggle

El archivo [02_kaggle_reproducible.ipynb](notebooks/02_kaggle_reproducible.ipynb) incorpora un ZIP de código y un inventario verificable. No lleva el entorno .venv ni las conversaciones privadas. El bootstrap valida el bundle y rechaza un núcleo modificado en un destino existente.

Se regenera con:

~~~powershell
.\.venv\Scripts\python.exe scripts\build_kaggle_notebook.py
~~~

Regenerar cambia el artefacto que debe verificarse si cambió su contenido. El reporte del 12 de octubre certifica la versión de esa corrida, no cualquier notebook reconstruido después.

Para la competencia alojada:

1. Importar el notebook y adjuntar el dataset autorizado.
2. Confirmar que las entradas están en /kaggle/input, que es de lectura, y las salidas en /kaggle/working.
3. Cambiar CONFIG_NAME de demo a la configuración de competencia.
4. Definir COMPETITION_INPUT_DIR con el directorio exacto de los CSV.
5. Completar COMPETITION_OVERRIDES con columnas, métrica, split y reglas confirmadas.
6. Reiniciar el kernel y correr todas las celdas en orden.
7. Revisar versiones, runtime, manifiestos y errores.
8. Comprobar /kaggle/working/submission.csv e iaa_execution.json.
9. Guardar la versión ejecutada y recuperar artefactos antes de cerrar.

configure_inputs fuerza el modo competition para entradas de competencia; no debe eludirse la comprobación de reglas con un override de modo. No editar el código embebido para arreglar algo informalmente: corregir el proyecto, reconstruir y verificar una versión identificable.

INSTALL_PINNED=False usa el runtime disponible y registra versiones y diferencias. INSTALL_PINNED=True exige las dependencias directas fijadas en requirements.kaggle.txt; aportar wheels Linux compatibles para instalación sin índice o permitir PyPI cuando las reglas y conexión lo admitan. Ese archivo no fija toda la imagen ni todas sus dependencias transitivas. El guard de runtime exige Python al menos 3.11 y scikit-learn al menos 1.5.

La simulación local corre con:

~~~powershell
.\.venv\Scripts\python.exe scripts\execute_notebook.py --notebook notebooks\02_kaggle_reproducible.ipynb --kaggle-simulated
~~~

Esta prueba debe identificarse como kaggle_simulated y hosted_kaggle_verified=false. Una corrida real debe conservar el runtime observado de Kaggle y sus salidas; no modificar a mano la bandera de un reporte simulado.

El notebook contiene un ensayo live/replay con calculador local, marcado sintético y separado del registro real. No presentarlo al jurado como uso real de un LLM.

Dockerfile.verify prepara una verificación Linux, todavía pendiente de ejecución en este equipo. Usarla cuando haya un motor operativo puede detectar problemas de portabilidad; no sustituye la comprobación en la imagen alojada. No instalar WSL o Docker como requisito de la candidatura si las reglas no lo exigen.

## Entrenamiento e inferencia como artefactos distintos

Si las reglas admiten entrenamiento externo y entrega de pesos, separar la construcción del modelo de su inferencia final. Conservar ambos procedimientos: datos, particiones, teacher si existe, conversión de pesos, tokenizer, configuración, dependencias y hashes. La entrega debe arrancar sin descargas cuando se exija ejecución sin red.

El límite de 12 horas y la desconexión no son condiciones universales que debamos imponer a IAA. [NVIDIA describe cinco horas en AIMO 2](https://blogs.nvidia.com/blog/reasoning-ai-math-olympiad/). El tiempo, la memoria, la GPU y las conexiones válidas para nosotros se copian de las reglas de 2026.

Antes de adoptar cuantización o un motor de serving, medir carga, inferencia, memoria máxima y calidad con entradas representativas. Fijar versiones y validar compatibilidad de dispositivo, kernels y checkpoint. Que un modelo esté en AWQ o GPTQ no demuestra que quepa o conserve precisión.

Como estimación propia, 72.000 millones de parámetros a cuatro bits requieren unos 36 GB decimales solo para esos pesos, antes de escalas, otros tensores, KV cache y buffers. CPU offload cambia dónde reside parte de la memoria y puede aumentar la latencia; no garantiza por sí solo ejecutar un modelo en dos T4.

La [documentación vLLM](https://docs.vllm.ai/en/latest/configuration/conserving_memory/) explica paralelismo, cuantización y control de contexto y lotes. Probar las opciones de la versión instalada y registrar las efectivas. Prefix caching solo reutiliza prefijos coincidentes; limitar contexto puede ahorrar memoria y también perder evidencia.

Para combinar LoRA, conservar base, tokenizer, rango, escala, módulos y método de fusión. La [documentación PEFT](https://huggingface.co/docs/peft/developer_guides/model_merging) ofrece métodos distintos. Como comprobación algebraica, promediar por separado factores A y B no equivale en general a promediar sus productos BA. Incluso promediar los deltas efectivos no garantiza la predicción media de una red no lineal.

Comparar modelo individual, promedio de predicciones y modelo fusionado; después evaluar la cuantización de cada candidato. No fusionar adaptadores para crear la predicción OOF de una fila si algún componente se entrenó con su etiqueta. La fusión final puede usar todo train una vez seleccionado el procedimiento.

En AIMO 2, [NVIDIA identifica Qwen2.5-14B como base de su modelo ganador](https://huggingface.co/nvidia/OpenMath-Nemotron-14B-Kaggle). Su [descripción de inferencia](https://developer.nvidia.com/blog/how-to-achieve-4x-faster-inference-for-math-problem-solving/) presenta FP8 y speculative decoding, por lo que AWQ de cuatro bits no debe describirse como requisito de esa victoria.

Estas capacidades son propuestas. El proyecto actual no incluye fine-tuning de LLM, fusión de adaptadores, cuantización ni vLLM.

## Adaptabilidad con una prueba real

Un flujo adaptable debe soportar una variación útil sin perder su contrato. Elegir una variación permitida: otra cartera, otro periodo, cambio de exposición, esquema documental distinto o una actualización de una regla. Conservar qué configuración cambia y qué pruebas vuelven a pasar.

Separar núcleo, configuración, datos y prompts. Las suposiciones deben ser explícitas y la salida debe mantener unidades, fuentes y límites. Si una variación requiere código nuevo, documentar cuánto y por qué; no presentarla como adaptación automática.

La ejecución local y simulada del mismo fixture demuestra parte de la portabilidad del entorno. No demuestra adaptación a un nuevo problema. Preparar una segunda prueba con cambio material autorizado y medir el resultado.

La demostración debe incluir al menos un caso habitual y un caso difícil seleccionado antes de ajustar la presentación. Si mostramos una aplicación, mantener una vía reproducible aunque un enlace de demo deje de funcionar.

## Selección final y entrega

Definir una fecha interna de congelación anterior al cierre oficial. Como propuesta, el 29 puede dedicarse a la reconstrucción final y el 30 al margen de entrega, pero las horas oficiales de 2026 deciden el calendario.

La selección final se basa en el procedimiento registrado, la validación pertinente y los criterios oficiales. Si hay varias entregas permitidas, documentar la razón de cada una. No seleccionar una versión imposible de reconstruir porque dio un buen score público.

Antes de enviar:

- [ ] Todos los requisitos oficiales tienen evidencia y canal de entrega identificado.
- [ ] Se congelaron código, configuración, modelo, prompts y fuentes con versión y hash.
- [ ] El notebook completo terminó desde un kernel limpio en el entorno de destino.
- [ ] El archivo final tiene nombre, columnas, tipos, filas y orden de IDs correctos.
- [ ] No hay NaN, infinito, valores fuera de dominio ni transformaciones inversas pendientes.
- [ ] El CSV generado coincide con el modelo y la fórmula descritos.
- [ ] Las cifras del informe proceden de artefactos de esa versión.
- [ ] Se cumplen reglas de datos externos, modelos, licencias y colaboración.
- [ ] El jurado puede acceder a los recursos necesarios con las condiciones exigidas.
- [ ] No se publicaron credenciales, datos restringidos ni conversaciones no autorizadas.
- [ ] Se enviaron todos los componentes obligatorios, no solo el CSV.
- [ ] Se guardaron recibo, versión, score disponible y selección final.
- [ ] Se verificó que la plataforma marcó la entrega como válida antes del cierre.

Enviar implica una acción en la plataforma; no inferirla porque existe submission.csv. Tampoco inferir acceso del jurado porque el autor puede abrir un enlace. Publicar datos o recursos requiere cumplir sus permisos y las reglas.

## Narrativa para el jurado

Abrir con el problema profesional y el resultado comprobado. Explicar el flujo, qué hizo la IA, qué revisó el actuario y qué cambió frente a una referencia. El informe debe entenderse sin esta conversación.

Una estructura candidata, ajustada a los entregables oficiales, incluye problema y usuario, datos y validación, baseline, variantes, contribución de IA, revisión humana, interpretación, adaptación, limitaciones y reproducción. Si se pide video, mostrar entradas, funcionamiento y resultados reales; no trasladar automáticamente la duración de tres minutos de otro hackathon.

Cada cifra necesita run_id y artefacto. Cada afirmación sobre una fuente necesita URL y versión o fecha. Cada contribución atribuida a la IA necesita prompt_id y comparación, o una descripción honesta si no se pudo aislar cuantitativamente.

Mostrar una propuesta aceptada, una rechazada y una corrección humana cuando existan. Lo valioso es el criterio, no llenar una lista artificial. Una ablación puede mostrar que un componente no ayudó; conservarla mejora la credibilidad y puede justificar retirarlo.

Distinguir score CV, leaderboard público, privado si se conoce y resultado del jurado. No mezclarlos en una comparación. Distinguir inspección de código, repetición propia y reproducción independiente.

No describir como “desplegado”, “seguro”, “robusto” o “adaptable” aquello que solo se ha narrado. Precisar la prueba realizada y su límite. El premio de un caso externo tampoco demuestra utilidad profesional en nuestra tarea.

## Experimentos candidatos del material incorporado

Elegir entre estos experimentos después de conocer el contrato. Cada uno debe tener configuración, particiones, artefactos y criterio de decisión. No es una lista de implementaciones terminadas.

| Experimento | Comparación | Evidencia necesaria para adoptarlo |
| --- | --- | --- |
| Agregaciones relacionales | Baseline frente a ventanas y agregados por entidad | Mejora exterior y joins sin duplicaciones ni información futura |
| Señales de captura | Con y sin metadatos, formato textual o representaciones legítimas de ID | Estabilidad entre fuentes y entidades nuevas |
| Dominio objetivo | Entrenamiento conjunto frente a preentrenamiento y ajuste al dominio | Resultado global y del dominio reservado, sin selección por test |
| Pseudoetiquetas de alineación | Sin pseudo frente a teacher entrenado dentro de cada partición | Ablación en datos reales con etiquetas exteriores protegidas |
| Selección OOF | Promedio frente a Ridge y selección hacia adelante | Ganancia marginal estable y selección interna |
| Recuperación documental | Búsqueda léxica frente a embeddings y reordenador | Recall de candidatos, pertinencia y citas correctas |
| Destilación | Teacher frente a student básico y destilado | Calidad, coste y procedencia de supervisión |
| Localizar e interpretar | Documento completo frente a región detectada y extracción | Errores de cada etapa y tolerancia a fallos previos |
| Fusión multimodal | Tabular frente a señales OOF de texto o imagen | Aportación independiente de cada fuente |
| Cálculo con herramientas | Respuesta directa frente a cálculo verificado | Exactitud, unidades, trazas y comportamiento ante errores |
| Aumentación o adaptación | Inferencia fija frente a vistas válidas o adaptación permitida | Invariancia, aislamiento y mejora por casos |
| Fusión y cuantización | Modelos individuales, mezcla de predicciones y pesos fusionados | Calidad y memoria medidas en el destino |

Una rama sin mejora predictiva puede justificar su inclusión si aporta interpretación o adaptación demostrada y la rúbrica lo valora. Registrar ese motivo y su coste; no inventar una ganancia de score para defenderla.

## Calendario por hitos

Este calendario orienta el trabajo, sin imponer un máximo de horas o recursos. Reordenarlo según la naturaleza del reto.

| Periodo | Hito | Evidencia para avanzar |
| --- | --- | --- |
| 12–15 de octubre | Inscripción, entorno, ensayo Kaggle y preparación de registros | Comprobante y corrida alojada de ensayo |
| 16 | Reglas, contrato, datos y baseline válido | Matriz de requisitos, hashes y primera corrida |
| 17–19 | Calidad de datos, validación y referencias | Diccionario, folds y diagnóstico de errores |
| 20–23 | Hipótesis avanzadas y aportación creativa de IA | Variantes comparables, conversaciones reales y ablaciones |
| 24–26 | Complementariedad, robustez, interpretación y adaptación | Evaluación exterior, casos difíciles y segunda situación |
| 27–28 | Selección y dossier | Criterios congelados, versión candidata y cifras enlazadas |
| 29 | Reconstrucción final limpia | Entregables desde cero y comprobaciones completas |
| 30 | Margen y cierre oficial | Recepción válida y selección final guardadas |

No posponer una entrega mínima válida hasta el último día si la plataforma permite ensayar antes. Las pruebas de cierre requieren tiempo propio; no usar todo el margen para una última búsqueda.

## Riesgos y respuesta operativa

| Señal | Qué revisar | Qué conservar |
| --- | --- | --- |
| CV excelente y resultado externo cae | Duplicados, fuente relacionada con test, split y drift | Comparación por segmentos y decisión sobre partición |
| Mejora desaparece al cambiar seed | Variabilidad y sobreselección | Repeticiones justificadas y diferencias por fold |
| Feature parece disponible pero proviene del futuro | Fecha de origen y horizonte del objetivo | Diccionario y regla de disponibilidad |
| LLM propone cálculo convincente pero incorrecto | Unidades, fórmula y caso conocido | Respuesta original, corrección y prueba |
| Ensamble descrito no coincide con CSV | Vector, pesos, inversa y versión | Fórmula real y hashes de componentes |
| Reducción de dtype cambia resultado | Pérdida de señal, desbordamiento o redondeo | Comparación de representaciones |
| Hiperparámetros no aparecen en la corrida | Configuración efectiva y código | Valores aplicados y snapshot |
| Dependencias del notebook cambian | Imagen, paquetes observados y checkpoints | Entorno y procedimiento de reconstrucción |
| Replay falla | Huella de solicitud, contexto e integridad | Manifiesto y causa; no sustituir respuesta silenciosamente |
| Proveedor no responde | Error y recuperación prevista | Intentos, estado y resultado; no fingir éxito |
| Cita no respalda afirmación | Fragmento, versión y alcance | Corrección y referencia válida |
| Contexto archivado difiere del enviado | messages frente a context_files | Petición real y copias de procedencia |
| Dataset o repositorio no tiene licencia clara | Derechos y permisos exactos | Versión consultada y decisión de uso |
| Demo exige cuenta o enlace temporal | Acceso exigido al jurado y vía alternativa | Prueba de acceso y artefacto reproducible |
| Reporte dice aprobado sin revisión real | Estado y evidencia de la persona | Revisión pendiente o decisión realmente tomada |

## Procedimiento para retomar y mantener la memoria

Al retomar el proyecto, leer AGENTS.md, esta guía, configs/competition.yaml y el último reporte de estado pertinente. Comprobar qué archivos cambiaron después del último snapshot. No repetir investigación o entrenamiento completados sin una razón nueva.

Al cerrar cada bloque, añadir una entrada fechada al registro de decisiones con problema, alternativas, decisión, evidencia, motivo y siguiente condición de revisión. Marcar propuestas implementadas solo cuando exista código; marcar verificadas solo cuando exista una corrida correspondiente.

Actualizar reglas y preguntas abiertas cuando el organizador responda. Si cambia una condición, identificar qué experimentos y afirmaciones quedan afectados. Mantener los resultados históricos intactos.

Plantilla de decisión:

~~~text
Fecha y zona:
Pregunta o hipótesis:
Regla o supuesto pertinente:
Alternativas consideradas:
Decisión y estado:
Evidencia: URL/version, run_id, prompt_id, archivo y hash cuando corresponda
Motivo:
Limitación conocida:
Qué haría revisar la decisión:
Siguiente acción:
~~~

La memoria del proyecto se apoya en archivos y artefactos, no en que una conversación conserve todo su contexto. Esta guía es la referencia local. La copia en Page sirve para lectura; cambios futuros deben sincronizarse de forma explícita. Los enlaces locales en la Page no suben sus archivos ni dan acceso a otras personas.

## Decisiones que ya no deben reabrirse sin nueva evidencia

| Decisión | Estado y motivo | Cuándo revisarla |
| --- | --- | --- |
| Competir como estudiante con Python y modelos | Perfil declarado; trabajo individual | Si cambian equipo o elegibilidad |
| Priorizar capacidad de ganar sin límite propio de tiempo o equipo | Preferencia explícita del participante | Solo si cambia esa preferencia o hay límites oficiales |
| No asumir reglas de 2025 para 2026 | Edición nueva y enunciado pendiente | Al obtener las reglas oficiales |
| Mantener datos originales y entrenamiento dentro del fold | Necesario para comparaciones interpretables y sin fuga | Adaptar su implementación al contrato, no eliminar el principio |
| Guardar prompts completos y contexto | Trazabilidad v2 implementada | Si reglas o permisos exigen una forma particular de entrega |
| Separar live, replay y fixtures | Evita atribuir evidencia sintética a uso real | Si cambia el protocolo, conservar la distinción |
| Guardar código real en snapshots | No basta un hash sin contenido | Extender alcance cuando la entrega lo necesite |
| No llamar verificada a Kaggle alojada por simular rutas | La prueba actual fue Windows | Tras una corrida real conservada |
| Evaluar métodos avanzados antes de adoptarlos | La investigación no demuestra mejora en el reto | Cuando haya datos y comparaciones válidas |
| Mantener rendimientos y criterios del jurado por separado | Los premios 2025 no coincidieron con el ranking predictivo | Según rúbrica oficial, sin mezclar medidas |

## Glosario de trabajo

| Término | Uso en este proyecto |
| --- | --- |
| CV | Validación cruzada utilizada para comparar variantes |
| OOF | Predicción de una fila realizada sin entrenar con su propia etiqueta |
| Holdout reservado | Datos separados del ciclo de desarrollo, usados con criterio predefinido |
| Ablación | Comparación que retira o cambia un componente para medir su aportación |
| CV anidada | Selección completa dentro de entrenamiento exterior y evaluación fuera de él |
| Fuga | Información del objetivo o del futuro indebidamente disponible al entrenar o validar |
| Checkpoint | Estado concreto de pesos de un modelo, con versión y procedencia |
| Shrinkage | Ajuste de estimaciones de grupos pequeños hacia una referencia para reducir variabilidad |
| Live | Llamada real a un transporte configurado y registro del resultado |
| Replay | Reproducción de evidencia conservada sin volver a llamar al modelo o herramientas |
| Fixture sintético | Caso artificial de prueba, identificado como tal |
| Snapshot | Copia de archivos de código con inventario y hashes |
| Reproducción independiente | Una persona o entorno independiente reconstruye el resultado con la evidencia entregada |


## Índice de fuentes y archivos

La guía resume decisiones y procedimientos. Para verificar un detalle o actualizar la investigación, consultar el material de origen.

| Recurso | Qué conserva |
| --- | --- |
| [Investigación IAA 2026](Antecedentes/investigacion_iaa_2026.md) | Legitimidad, publicaciones, edición 2025, ganadores y auditoría de notebooks |
| [Catálogo IAA 2025](Antecedentes/catalogo_notebooks_iaa_2025.csv) | 32 entradas de Code con sus referencias |
| [Metodologías recientes](Antecedentes/metodologias_kaggle_2026.md) | 18 competiciones, 19 casos, 20 métodos y cautelas |
| [Catálogo de metodologías](Antecedentes/metodologias_kaggle_2026.json) | Casos, URLs, estado de evidencia y política de validación |
| [IA creativa y reproducibilidad](Antecedentes/ia_creativa_reproducibilidad_kaggle_2026.md) | Ocho competiciones, seis casos y observaciones de artefactos |
| [Catálogo de creatividad](Antecedentes/ia_creativa_reproducibilidad_kaggle_2026.json) | Fuentes, premios, artefactos inspeccionados y propuestas |
| [README](README.md) | Uso técnico y comandos actuales |
| [Estado del proyecto](ESTADO_PROYECTO.json) | Corte de memoria, pendientes y referencias de verificación |
| [Registro de decisiones](DECISIONES.md) | Decisiones persistentes y plantilla para añadir cambios |
| [Configuración de competencia](configs/competition.yaml) | Contrato pendiente de completar con las reglas |
| [Notebook local](notebooks/01_preparacion_reproducible.ipynb) | Ensayo reproducible |
| [Notebook Kaggle](notebooks/02_kaggle_reproducible.ipynb) | Bundle autónomo y ensayo de rutas |
| [Verificación v2](artifacts/readiness_v2.json) | Pruebas y ejecuciones conservadas del 12 de octubre |
| [Contraste del material aportado](Antecedentes/analisis_texto_aportado_20261013.md) | 32 afirmaciones revisadas, fuentes y decisiones de incorporación |
| [Texto original aportado](Antecedentes/fuentes/texto_aportado_kaggle_2024_2026_recibido_20261013.txt) | Archivo íntegro recibido el 13 de octubre, con procedencia y hash en el contraste |

Las [Pages de metodologías](https://chatgpt.com/space/page_4dc5c1f2b1448191b109e60cb04caddb) y de [IA creativa](https://chatgpt.com/space/page_6ac69aba33a88191ad3f4e45da34ba98) contienen las investigaciones previas. Un vínculo no concede acceso a archivos locales o recursos privados.

Las referencias primarias de la institución son el anuncio 2026, las reglas y resultados 2025 y las condiciones 2026 cuando se publiquen. Los writeups de participantes sirven para estudiar métodos declarados. Las observaciones del código sirven para contrastar narrativa y artefactos. Ninguna de esas categorías sustituye una prueba propia sobre el reto.

## Criterios corregidos del material aportado

El [análisis del texto recibido](Antecedentes/analisis_texto_aportado_20261013.md) conserva el contraste detallado y el [original archivado](Antecedentes/fuentes/texto_aportado_kaggle_2024_2026_recibido_20261013.txt) permite rastrear las afirmaciones. Las nuevas técnicas se incorporan a las etapas correspondientes; el calendario sigue siendo el de IAA y no se impone un presupuesto propio de 48 horas.

| Afirmación del texto | Criterio que usaremos |
| --- | --- |
| Ganar exige siempre pipelines grandes o muchos modelos | Comparar con un baseline sólido y exigir aportación a cada etapa |
| Toda competencia tiene 12 horas e Internet desactivado | Confirmar las condiciones específicas de IAA 2026 |
| pd.cut produce cuantiles y hay que usar 25 grupos | Distinguir intervalos y cuantiles; priorizar grupos y tiempo |
| Toda mejora debe superar +0.0003 | Definir relevancia en la métrica oficial y su variabilidad |
| Fusionar cinco LoRA reproduce un ensamble de cinco modelos | Evaluar la fusión como un candidato distinto |
| Clasificación causal siempre supera clasificación de secuencia | Comparar formulaciones; el ganador LMSYS usó clasificación de secuencia |
| Normalizar inflación o ingresos nunca ayuda | Probar el supuesto y la calidad de las variables en nuestro dominio |
| Dropout cero, contexto corto o CNN pequeña son reglas generales | Tratar cada configuración como hipótesis específica |
| Debemos copiar alteraciones diseñadas para engañar jueces | Mejorar utilidad real y comprobar respuestas, no confundir al evaluador |
| Hace falta dedicar una cantidad fija de cómputo por categoría | Medir nuestro flujo y sus límites oficiales; no trasladar tiempos sin hardware comparable |

La cifra de fechas recuperadas de Home Credit se atribuye en la fuente al [writeup Public 8th Private 253](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/writeups/evgeniia-grigoreva-public-8th-private-253-solution), no a una receta integral del primer puesto. El [ganador](https://www.kaggle.com/c/home-credit-credit-risk-model-stability/discussion/508337) describió otro portafolio y una alteración de la métrica que él mismo diferenció de la calidad del modelo. Conservar este caso como advertencia sobre atajos y evaluación.

En [ISIC 2024](https://www.kaggle.com/competitions/isic-2024-challenge/overview/description), la métrica principal era pAUC sobre el tramo de TPR superior al 80%; no sustituirla por la fórmula de eficiencia del texto. Los rangos de pacientes, imágenes o equipos sin fuente y las cifras de otras ediciones quedan pendientes de corroboración.

Los resultados y detalles históricos de Bank Churn, PII, algunas soluciones de ISIC y Jane Street que no se pudieron corroborar en fuentes primarias quedan como referencias por investigar. No se usan para decidir arquitectura ni se presentan como hechos verificados.

## Anexo de competiciones recientes

Este catálogo resume los 19 casos de 18 competiciones examinados. Las posiciones indicadas en el informe proceden principalmente de writeups de sus autores; el caso MedGemma se contrastó con anuncio del organizador. No se presenta toda esta muestra como soluciones ganadoras ni como reproducción independiente. El enlace de cada caso permite revisar su método y su limitación antes de transferirlo.


| Caso | Competición y fuente | Métodos observados | Límite para transferirlos |
| --- | --- | --- | --- |
| K01 | [Predicting Smartphone Addiction (PS S6E8)](https://www.kaggle.com/competitions/playground-series-s6e8/writeups/1st-place-distributed-intelligence-nvidia-infe) | Agentes de IA para investigación y experimentación; RealMLP; XGBoost; Ensamble diverso | El relato no demuestra que el mismo sistema gane en otros datos ni aporta una ablación completa del efecto de cada agente. |
| K02 | [Predicting Smartphone Addiction (PS S6E8)](https://www.kaggle.com/competitions/playground-series-s6e8/writeups/14th-place-278-shared-oof-sets-36-own-models) | Selección de ensamble con fold reservado; Lookup-Transformer; Imputación con restricciones; Copias categóricas de números; Auditoría de OOF | El autor aclara que su evaluación del combinador no es doble CV completa y no elimina sesgo o contaminación previa en OOF ajenas. |
| K03 | [Data Science Osaka Summer 2026](https://www.kaggle.com/competitions/data-science-osaka-summer-2026/writeups/1st-place-solution) | Validación temporal y regional; Simulación de entidades nuevas; Promedios con shrinkage; Clasificación ordinal; Boosting y modelo aditivo | Los agregados del periodo de test usan información disponible en ese concurso; no equivalen a variables disponibles en un pronóstico actuarial futuro. |
| K04 | [SecurePay Biometric Risk Challenge](https://www.kaggle.com/competitions/secure-pay-biometric-risk-challenge/writeups/risk-aware-feature-engineering-for-biometric-fraud) | CatBoost; Interacciones de riesgo; Diferencias entre indicadores; Variables horarias cíclicas; Promedio de probabilidades por fold | La caída entre público y privado impide tomar su score público como evidencia de robustez. La métrica no se presume comparable con otras competencias. |
| K05 | [Predicting Stellar Class (PS S6E6)](https://www.kaggle.com/competitions/playground-series-s6e6/writeups/24th-place-solution) | Stacking logístico; TabPFN-3 como combinador; Ensamble de 32 modelos | Es evidencia de una solución en puesto 24 y mejora OOF; no prueba que TabPFN-3 ganara la competencia o que su stacking fuese plenamente anidado. |
| K06 | [Predicting F1 Pit Stops (PS S6E5)](https://www.kaggle.com/competitions/playground-series-s6e5/writeups/1st-place-by-the-skin-of-my-teeth) | RealMLP; TabM; Boosting; AutoGluon; Combinación en logits; OOF de múltiples modelos | La cantidad de modelos y la última mejora del leaderboard no constituyen un requisito general para ganar; cada capa necesita evaluación independiente. |
| K07 | [Predicting Irrigation Need (PS S6E4)](https://www.kaggle.com/competitions/playground-series-s6e4/writeups/1st-place-one-vs-rest-approach) | Clasificación jerárquica; XGBoost; RealMLP; TabM; Stacking logístico de logits; Umbrales para balanced accuracy | La descomposición depende de esa estructura concreta de clases; no reemplaza automáticamente una clasificación multiclase. |
| K08 | [Stock Pledge Financing Default Prediction 2026](https://www.kaggle.com/competitions/stock-pledge-financing-default-prediction-2026/discussion/679558) | TabICL v1.1; SMOTE; CTGAN; Variables financieras | El texto no documenta suficientemente una validación independiente del generador y del remuestreo; se clasifica como candidato experimental, no receta validada. |
| K09 | [Predicting Heart Disease (PS S6E2)](https://www.kaggle.com/competitions/playground-series-s6e2/writeups/1st-place-solution-diversity-selection-and-t) | Múltiples representaciones de variables; RealMLP; AutoGluon; Boosting; Selección con Optuna; Ridge stacking | La búsqueda repetida sobre una misma OOF puede sobreajustar; el propio autor distingue la práctica de una CV completamente anidada. |
| K10 | [MITSUI&CO. Commodity Prediction Challenge](https://www.kaggle.com/competitions/mitsui-commodity-prediction-challenge/writeups/26th-place-mitsui-and-co-commodity-prediction) | Formato largo multobjetivo; LightGBM; Estabilidad temporal de variables; Clustering de targets | Es puesto 26, no la solución ganadora. Un único holdout y correlaciones históricas estables no garantizan estabilidad futura. |
| K11 | [Predicting Loan Payback (PS S5E11)](https://www.kaggle.com/competitions/playground-series-s5e11/writeups/1st-place-a-lot-of-features-a-lot-of-models-an) | Target y count encoding; Interacciones; Representaciones de dígitos; RealMLP; TabM; Ridge y hill climbing | Las variables de dígitos y estadísticas de datos originales pueden explotar estructura del generador Playground; hay que probar su transferencia. |
| K12 | [DRW - Crypto Market Prediction](https://www.kaggle.com/competitions/drw-crypto-market-prediction/writeups/drw-solution-1st) | MLP de tres capas; XGBoost; Purged group temporal CV; Selección de variables correlacionadas; Autoencoder; Loss alineada con correlación | La purga evita proximidad entre bloques, pero no convierte una validación con futuro en entrenamiento en un backtest causal. La selección debe quedar dentro de cada partición. |
| K13 | [CIBMTR - Equity in post-HCT Survival Predictions](https://www.kaggle.com/competitions/equity-post-HCT-survival-predictions/writeups/minerppdy-1st-place-solution-2-targets-and-ensembl) | Descomposición clasificación y ranking; Árboles; TabM; GNN; Estratificación por evento y grupo; Combinación regularizada | La receta responde a una métrica y datos sintéticos de competición; no debe interpretarse como estimador clínico de supervivencia o trasladar el evento observado como predictor disponible. |
| K14 | [MAP - Charting Student Math Misunderstandings](https://www.kaggle.com/competitions/map-charting-student-math-misunderstandings/writeups/1st-place-solution) | Ranking de sufijos candidatos; Qwen3-32B; GLM-Z1-32B; Fine-tuning completo; Multisemilla; Cuantización; FlexAttention | Las ventajas de modelos grandes y varias semillas se observaron en ese texto; no son una ley general para tareas tabulares o cualquier NLP. |
| K15 | [NeurIPS - Open Polymer Prediction 2025](https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025/writeups/1st-place-solution) | BERT; AutoGluon; Uni-Mol; Datos externos; Preentrenamiento con pseudoetiquetas; Aumentación válida; Deduplicación | La corrección final se obtuvo sondeando el leaderboard y una anomalía del test. El pilar transferible es el diseño de representaciones y validación, no ese offset. |
| K16 | [BirdCLEF+ 2026](https://www.kaggle.com/competitions/birdclef-2026/writeups/1st-place-solution-noisy-student-meets-distillati) | Destilación de embeddings; Noisy Student; Especialistas por taxonomía; Rank blending; Validación por sitio | La evidencia es acústica y depende de dominio y etiquetado; su uso actuarial requeriría texto, imágenes o un caso de transferencia equivalente. |
| K17 | [NVIDIA Nemotron Model Reasoning Challenge](https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge/writeups/1st-place-solution) | Problemas sintéticos programáticos; Trazas de solvers; SFT; LoRA; Diseño de representación; Verificación exacta | El autor reconoce contaminación en una tabla de diagnóstico por haber diseñado reglas mirando todo train.csv. Esa tabla no es validación independiente. |
| K18 | [Make Data Count - Finding Data References](https://www.kaggle.com/competitions/make-data-count-finding-data-references/writeups/1st-place-solution) | Fuentes estructuradas; Extracción de texto; CatBoost de metadatos; Qwen para contexto; Salidas restringidas; Validación por documento | La solución explota también la forma de crear etiquetas del concurso. Que una referencia aparezca en texto no demuestra por sí solo su interpretación. |
| K19 | [The MedGemma Impact Challenge](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/685002) | Fine-tuning especializado; Flujo de trabajo concreto; Multimodalidad; Salidas estructuradas; Demostración para jurado | El premio y las demos no equivalen a validación clínica. La lección para IAA es demostrar utilidad profesional y un flujo verificable. |


## Actualización D31–D32: Jev y primera limpieza derivada, 16 de octubre de 2026

El participante pidió evaluar Jev / TypeSafe antes de añadir fondos y limpiar identificadores de clientes y exposición sin alterar originales; los capitales deben revisarse antes de corregirlos. La [evaluación de Jev](../Hackaton/Semana 1/Validacion_IA/jev_20261016/evaluacion.html) conserva fuentes oficiales, la solicitud acotada y evidencia de Chrome. La consola tenía saldo cero. El intento devolvió Out of funds, sin decisión del modelo. No hubo compra, clave API nueva ni carga de archivos. Se prepararon 18 casos de desarrollo, sin ejecutar y con referencias propuestas por Codex pendientes de revisión humana. Recomendación: no recargar ni integrar por ahora; el posible piloto sería clasificación semántica para dirigir revisiones. Mantener cálculos, fechas y correcciones exactas en Python. No se atribuye a Jev una validación exitosa ni una mejora de rendimiento.

La [limpieza v1](../Hackaton/Semana 1/Limpieza/README.md) genera seis tablas derivadas y un catálogo que referencia además cinco originales intactos. Corrida vigente: `clean_20261016T175335Z_a6412ce0`; [informe](../Hackaton/Semana 1/Limpieza/runs/clean_20261016T175335Z_a6412ce0/informe.html). RUTAS_PROYECTO.json conserva Datos como capa original y añade el índice de limpieza. Las bitácoras registran source_row, row_id, old, new y regla por cada cambio, con reversión exacta verificada.

ID01 rellenó customer_id a ocho dígitos ASCII como texto: 98.110 filas de entrenamiento de autos y 25.554 de test. Todos los cruces fallidos se recuperaron contra el maestro único; las otras ramas no cambiaron claves. EXP01 reconstruyó exposición con días inclusivos / 365 a cuatro decimales: 14.229 cambios de entrenamiento (11.910 ACT360 y 2.319 cantidades en días). Todo el test conservó exposición. La exposición total del entrenamiento pasó de 2.658.636,1771 a 1.968.577,0591 años. Es una convención del proyecto respaldada por el patrón de datos y test; el organizador no la ha confirmado. Se conserva un año bisiesto completo como 1,0027, sin recortar a uno.

Pasaron 83 controles técnicos completos y 12 de artefactos: hashes de los once originales, esquema, filas, orden, columnas restantes, cada bitácora, reversión, aritmética independiente de fechas y cobertura de la plantilla. El primer intento de verificación falló por cargar pandas antes de activar la ruta aislada de PyArrow; se corrigió el orden y se conserva el código inicial y el registro del fallo. No se recalcularon los derivados para resolver ese fallo del verificador. Se inspeccionaron la figura y la captura de Chrome. Es verificación propia asistida por IA; revisión humana pendiente, sin independencia ni aprobación para modelar.

Los capitales conservan todos sus valores. La cola contiene 5.913 filas por umbrales diagnósticos de importe o saltos de 900–1100 veces entre periodos consecutivos, en ambos sentidos. Incluye casos de vuelta a una escala habitual, por lo que la cola no equivale a 5.913 capitales incorrectos. Revisar unidad, endosos, objeto asegurado y continuidad antes de decidir; no se divide por mil automáticamente. El cálculo comprueba que el periodo de comparación es anterior y no usa siniestros. Los capitales, la definición de último/IBNR, las 414 reclamaciones anteriores al primer periodo observado y la disponibilidad temporal de variables siguen pendientes. No se entrenó, envió o publicó ningún modelo y no hubo delegación.


## D34: revisión de capitales sin corregirlos, 16 de octubre de 2026

[Informe con diez casos e historias consultables](../Hackaton/Semana 1/Revision_capitales/runs/capital_20261016T180903Z_bceb990c/informe.html), [guía de reproducción](../Hackaton/Semana 1/Revision_capitales/README.md). Se estudiaron 1.800.996 filas de edificios y contenidos, 2021–2025. Hay 3.527 capitales en la banda extrema, distintos de las 5.913 filas de la cola D32, que también incluía retornos a escala habitual. No se modificaron capitales ni originales ni las seis tablas derivadas.

La evidencia apoya investigar una escala ×1000, sin afirmar verdad del generador. La propuesta de referencia previa comparable, contexto conocido e igual, separación hasta 400 días y continuidad hipotética ±10% clasifica 2.073 filas con apoyo anterior, 879 con apoyo principal posterior, 467 con contexto o continuidad pendientes y 108 sin referencia normal. Son criterios de revisión, no correcciones aprobadas. Las tolerancias de 5% y 10% producen las mismas 2.073. En la póliza B19256617 coexisten mudanza y salto de escala: /1000 conservaría un aumento de 196.000 a 377.000 CU, mientras copiar el capital anterior lo borraría. La historia muestra después 388.000 hipotéticos, 400.000 y 412.000 originales en el nuevo domicilio. No dividir filas normales que siguen a una alta ni interpretar dos altos consecutivos como confirmación de unidad.

El uso retrospectivo de historia anterior a diciembre de 2024 puede ser coherente con preparar 2025; cada corte de validación temporal necesita su propia información disponible. El apoyo de características de test es otra decisión transductiva a declarar. No usar siniestros o scores para decidir la unidad ni presumir que la prima cambia proporcionalmente. Se conservan límites por maestros sin vigencias, endosos no observados y falta de confirmación de unidad.

Pasaron 31 controles de datos y seis de lógica del informe en Node con DOM mínimo; no se verificó renderizado en navegador. Se inspeccionaron las figuras seleccionadas. Se preservó el fallo inicial de enlace autorreferente del verificador y su reparación; los controles completos posteriores pasaron. Los diecisiete archivos protegidos mantienen hashes. Sigue pendiente la revisión humana; no hay validación independiente, capital corregido, dataset listo para modelar, entrenamiento o envío. Consultar D34 y ESTADO_PROYECTO.json.


## D36: CAP01 aplicado en derivados por autorización del participante, 16 de octubre de 2026

La capa preparada vigente está en [current_dataset.json](../Hackaton/Semana 1/Limpieza/current_dataset.json). [Informe de corrección](../Hackaton/Semana 1/Limpieza/runs/capfix_20261016T184904Z_099a22b1/informe.html), [bitácora CSV](../Hackaton/Semana 1/Limpieza/runs/capfix_20261016T184904Z_099a22b1/ledger/all_capital_changes.csv), [guía CAP01](../Hackaton/Semana 1/Limpieza/CAPITALES.md). D32 y D34 permanecen como evidencia histórica; current_run.json sigue identificando el flujo D32.

Se dividió sum_insured por mil exactamente en las 2.073 filas prior_supported congeladas de D34: 802 y 272 de edificios train/test, 731 y 268 de contenidos train/test. Total: 1.533 train y 540 test. Se heredaron claves y exposición de D32, sin modificarlas. Hay cuatro tablas de hogar nuevas, autos copiados byte a byte y cinco referencias a originales. Las bitácoras registran old/new, posición, clave, regla, evidencia anterior, hash y autorización. Pasaron 63 controles técnicos y nueve de integración del lector. Se acreditaron reversión e idempotencia, conservación de todas las demás columnas y de los diecisiete archivos protegidos, catálogo completo y cobertura de test.

Los 1.454 capitales extremos no aprobados siguen pendientes y sin cambios; no se expande la lista al corregir una referencia. En C67134620, 2023 queda en 43.500 CU y 2024 conserva 44.400.000 CU pendiente. El participante autorizó esta reparación inferida; no hay confirmación de unidades del origen ni validación independiente. Las demás carencias de datos y modelado siguen abiertas.

Metodología/protocolo 1.1 y lector activo apuntan al índice preparado; sus versiones anteriores y el diagnóstico D35 permanecen archivados. La comprobación de integración leyó IDs y hashes, sin repetir el diagnóstico ni construir etiquetas. No hubo entrenamiento, envíos, publicación o delegación. Consultar D36, lineage.json, verification.json e integration_verification.json de la corrida.


## D38: CAT01/AGE01 y nueva auditoría de calidad, 16 de octubre de 2026

Capa activa: [current_dataset.json](../Hackaton/Semana 1/Limpieza/current_dataset.json). [Informe](../Hackaton/Semana 1/Limpieza/runs/refine_20261016T190025Z_6751bba4/informe.html), [reglas y reproducción](../Hackaton/Semana 1/Limpieza/REFINAMIENTO.md), [pendientes](../Hackaton/Semana 1/Limpieza/runs/refine_20261016T190025Z_6751bba4/open_issues.json). La continuación autorizada unificó 700.210 etiquetas de construcción por mayúscula/minúscula y recalculó 2.936 edades de tomadores de hogar desde el nacimiento hasta el inicio de cobertura. El maestro de nacimiento se adopta como referencia explícita, sin confirmación independiente; las edades anteriores quedan en bitácora. driver_age, capitales, siniestros, exposición, primas y nulos se conservan.

La revisión de once tablas y 7.826.877 filas produjo 375 comprobaciones, sin fallos estrictos. Pasaron 76 controles específicos y diez de integración del lector. Se verificaron reversión, calendario por aniversario, idempotencia de categorías, tipos, esquema, orden, cobertura de test, hashes y todos los valores ajenos a los campos modificados. Los seis derivados CAP01 y once originales permanecen intactos. Las versiones previas no se reescribieron. Metodología/protocolo 1.2 describen la nueva capa; sus versiones 1.1 están archivadas. No se entrenó ni se repitió el diagnóstico T0.

Los códigos t/w permanecen separados y sin material confirmado: hay 107.817 filas y 18.218 transiciones t→w en la misma póliza/dirección, concentradas en el cambio de 2022 a 2023. No mapearlos automáticamente a timber. Los 161.822 NCB superiores a la antigüedad de licencia no se recortaron. Los 414 siniestros previos a la primera cobertura observada quedan separados tras una nueva asignación diagnóstica, sin cambiar fechas. La falta de telemática coincide con no optar por el dispositivo; no imputar cero. Los 1.454 capitales restantes siguen pendientes y CAP01 no se amplió.

El registro consolidado tiene 703.146 celdas modificadas, no ese número de clientes. AGE01 cambia 1.122/300 filas de edificios train/test y 1.209/305 de contenidos; CAT01 cambia 555.824/144.386 de edificios. La revisión es propia asistida por IA, sin independencia ni aprobación completa para modelar. Siguen pendientes semántica, temporalidad, disponibilidad, último/IBNR y materialización operativa del objetivo. Consultar D38 para criterios, límites y evidencia.


## D39: T/W como alias temporales, candidata sin activar, 16 de octubre de 2026

La [revisión longitudinal](../Hackaton/Semana 1/Revision_construccion/runs/construction_20261016T192514Z_779b361e/informe.html) respalda t,w→tw_code como clase común observada, con material físico aún sin confirmar. [Reproducción y límites](../Hackaton/Semana 1/Revision_construccion/README.md). Se compararon las 891.881 filas de edificios, 149.887 pares en la misma dirección al cruzar 2022→2023 y 18.218 T→W, todos el 1 de enero sin hueco. Las otras tres clases permanecen iguales. No hay contradicción después de agrupar en 449.658 transiciones de entrenamiento o 599.769 con confirmación de test, ni en 292.112 direcciones. Direcciones e historias están anidadas, no son evidencia independiente adicional.

Se concilian altas, bajas y mudanzas, con seis casos reales. B00002966 muestra T,T,W,W,W en A4975624; B00122195 cambia de brick a W con otra dirección en abril de 2023. El diccionario enumera timber pero no explica T/W; no asignarle ese nombre como confirmado. La propuesta usa solo X de entrenamiento de 2021–2024; 2025 es confirmación. No usar el mapa como conocimiento anterior a 2023 en backtests sin fuente previa; conservar una variante literal y declarar adaptaciones desde X de validación.

El [catálogo candidato](../Hackaton/Semana 1/Revision_construccion/runs/construction_20261016T192514Z_779b361e/candidate/dataset_catalog.json) añade construction_type_harmonized en dos tablas, con 107.817 filas agrupadas (85.556 train y 22.261 test), sin modificar ningún campo anterior. construction_type conserva t o w. El índice activo sigue en D38; la candidata está aislada y no se atribuye aprobación humana de activación. Los 2.073 CAP01, los 1.454 pendientes y todos los originales mantienen sus valores. Pasaron 100 comprobaciones específicas y ocho de lógica del informe con DOM mínimo; ambas figuras se inspeccionaron. No hubo navegador verificado, revisión independiente, entrenamiento ni efecto sobre tarifa medido. Consultar D39 y construction_review en el estado. El significado físico y las otras limitaciones del proyecto siguen abiertos.

Ampliación de D39: el [informe con desglose de faltantes](../Hackaton/Semana 1/Revision_construccion/editions/clarified_20261016T192928Z/informe.html) distingue estabilidad física de ausencia de registro. smoke_alarms coincide en los 17.346 pares informados en ambos años; las 856 diferencias del campo son 408 ausente→informado y 448 informado→ausente; otros 16 faltan en ambos. days_unoccupied sí difiere en 16.273 de 17.330 pares informados. No se imputa nada ni cambia el mapa. La edición nueva conserva el informe y los 48 archivos de la corrida original por hash; el índice de revisión señala esta ampliación.


## D40: pendientes exhaustivos de validación y nuevos hallazgos, 16 de octubre de 2026

El [informe](../Hackaton/Semana 1/Validacion_datos/runs/gaps_20261016T193906Z_70462cf9/informe.html) conserva 58 controles/decisiones y un inventario de 105 nombres de columna (242 apariciones). D38 sigue activo; D39 no se activó. La revisión de cobertura no certifica una base para modelar ni afirma haber cerrado todos los controles. El primer trabajo será decidir el tratamiento de duplicados semánticos, construir T0 con conciliación, aplicar F0 por disponibilidad y persistir particiones. Ver [matriz estructurada](../Hackaton/Semana 1/Validacion_datos/runs/gaps_20261016T193906Z_70462cf9/review_controls.json).

Hay 604 pares de siniestros idénticos salvo claim_id, con 1.208 filas implicadas. Si se confirmara una sola fila por par, la sensibilidad sería 3174167.49 CU de neto aceptado observado total, 3173808.61 CU dentro de periodos observados. No se deduplicó ni se declara sobrecoste confirmado. También hay 500.245 continuidades que omiten 31-12-2024 (200.063 motor, 150.111 edificios, 150.071 contenidos); ni periodos ni siniestros cubren ese día. EXP01 coincide con las fechas existentes; no corregirlas por inferencia.

Cuatro own_damage aceptados están fuera de comprehensive; 506/1.090 accidental_damage de edificios/contenidos tienen opción falsa; ocho/tres netos de hogar superan capital. Revisar alcance, clasificación, escala y límites, sin borrar pagos ni imponer ceros o topes. En eléctricos hay 96.843 cilindradas positivas de 99.376 filas (resto ausente), y 3.717 edades implícitas de licencia inferiores a 16 como cribado sin supuesto legal. Los conjuntos se solapan y no se suman como errores independientes.

Se conservan los 1.454 capitales pendientes y 161.822 NCB en revisión. Faltan disponibilidad por predictor, maestros históricos, nulos por cohorte, preparación dentro de folds, deriva actualizada y soporte/dependencia, desarrollo/IBNR y entrega. No se puede identificar completamente el último o la información financiera histórica con una única valoración; usar límites y sensibilidades. Un piloto T0 puede empezar con decisiones trazables y bloques dudosos excluidos sin esperar perfección. Catorce controles del sondeo y siete del informe pasaron; no son aprobación de toda la data ni revisión independiente. No cambió ningún dato, fecha, capital o catálogo preparado. Consultar D40 y el estado nuevo.


## D41: DUP01 propuesto para 604 parejas, sin aplicar, 16 de octubre de 2026

La [revisión de historiales](../Hackaton/Semana 1/Revision_duplicados/editions/explorer_fix_20261016T195247Z/informe.html) cubre 604 pares en 601 pólizas y once casos, con explorador para cualquier pareja. [Regla estructurada](../Hackaton/Semana 1/Revision_duplicados/runs/duplicates_20261016T194858Z_9bbf501d/proposed_rule.json) y [propuesta por fila](../Hackaton/Semana 1/Revision_duplicados/runs/duplicates_20261016T194858Z_9bbf501d/tables/proposed_pair_actions.csv). Se recomienda una copia por igualdad exacta de los once campos salvo claim_id, con mismo periodo o misma prehistoria. Cada pareja contiene CL+8 y CL+9 dígitos; todos los 604 IDs largos están en las parejas. Conservar el corto es una elección determinista de representante, no prueba de antigüedad. Nunca depurar por longitud sola o solo por póliza/fechas; no se aplicó ninguna exclusión.

Hay 411 pares motor, 109 edificios y 84 contenidos; 586 cerrados, 12 abiertos y seis rechazados. 600 ocurren en 2022, tres en 2021 y una en 2020. Los 603 pares asignables afectarían 600 periodos; 597 copias aceptadas asignables afectan 594 periodos. El efecto hipotético es 3.174.167,49 CU total observado y 3.173.808,61 CU dentro de periodos actuales; el resto, 358,88 CU, está antes de la historia. Mantener pago, reserva y recuperación conciliados; rechazados no reducen coste aceptado. No presentar esa sensibilidad como último o mejora predictiva.

Existen 57 parejas no idénticas con misma póliza/ocurrencia, 17 también con mismo peligro y una con ambas fechas. M83268515 muestra la necesidad de conservar dos expedientes con distintos importes/estado/reparador; M63592395 tiene terceros distintos. Las tres pólizas con dos pares mantienen dos eventos, no uno. Los 462 otros siniestros de las pólizas afectadas se conservan. La identificación no dispone de event_id/factura ni confirmación externa: evidencia fuerte para regla operativa, sin verdad física absoluta.

Pasaron 50 comprobaciones propias y 19 de lógica del informe que recorren las 604 parejas; figura inspeccionada, sin navegador ni revisor independiente acreditado. La capa D38, la candidata D39, los 1.454 capitales pendientes y todos los originales permanecen intactos. No hay claims depurado, activación o T0 nuevo. Consultar D41 y duplicate_claim_review para una futura decisión humana de aplicación.


## D42: DUP01 aplicado por autorización expresa, 16 de octubre de 2026

Capa activa: [current_dataset.json](../Hackaton/Semana 1/Limpieza/current_dataset.json). [Informe DUP01](../Hackaton/Semana 1/Limpieza/runs/dupfix_20261016T195843Z_fc0bb423/informe.html), [bitácora](../Hackaton/Semana 1/Limpieza/runs/dupfix_20261016T195843Z_fc0bb423/ledger/exclusion_ledger.csv) y [alias](../Hackaton/Semana 1/Limpieza/runs/dupfix_20261016T195843Z_fc0bb423/ledger/claim_id_aliases.csv). Se excluyeron únicamente las 604 copias congeladas de D41 y se conservaron los representantes de ocho dígitos. claims pasa de 163.150 a 162.546 filas; los 161.942 registros ajenos a los pares y cada valor retenido permanecen iguales, incluido orden y esquema. Excluded_rows tipado y posiciones permiten reversión exacta; alias no son observaciones adicionales.

La diferencia del neto aceptado observado es 3.174.167,49 CU, 3.173.808,61 en periodos actuales y 358,88 fuera de historia. Quedan 413 registros anteriores al primer periodo, frente a 414 previos a quitar esa copia, sin cambiar fechas. Los 57 grupos no idénticos se conservan. Pasaron 76 controles propios, incluidos reconstrucción, idempotencia, conflictos, componentes monetarios y hashes. Los otros diez archivos del catálogo no cambian; CAP01 y los 1.454 capitales pendientes se conservan; CON01 sigue sin activar. Los originales e informes anteriores siguen intactos.

El protocolo 1.3 incorpora claims derivado. El lector descriptivo se corrigió para dejar de mezclar claims vigente con agregados D30 y se ejecutó una vez sobre DUP01. [Evidencia del diagnóstico actual](../Hackaton/Semana 1/Modelado/diagnosticos/objetivo_20261016T200359Z/evidencia.json); 15 controles del consumidor concilian conteos/coste y preservación de entidades/productos. La versión 1.2 y lector previo están archivados. Estadísticas de investigaciones previas conservan su alcance anterior a DUP01. No hay tabla T0 operativa, entrenamiento, validación independiente o aprobación global para modelar. Próximo: integrar conciliación/asignación en T0, disponibilidad F0 y particiones; mantener las demás incidencias. Consultar D42 y duplicate_application.

Revisión de calendario D43: 500.245 brechas del 31-12-2024, todas de un día y con el mismo cliente; hay 3.153 cambios de dirección de motor. 497.503 renewed y 2.742 declined_by_insurer pese a sucesor. Cierres en día 365; existen 90 siniestros en 29 de febrero. Última ocurrencia 29-12 y reporte 30-12, con retraso mínimo un día: no inferir riesgo cero en fechas finales. CAL00 deja fechas y EXP01 pendientes de confirmación, sin activar marca de modelado ni ampliar cobertura. Historiales completos y trece casos en [informe](../Hackaton/Semana 1/Revision_calendario/runs/calendar_20261016T201406Z_01c55c49/informe.html); 101 controles de datos y 18 de interfaz. No se cambia el catálogo DUP01 ni los 1.454 capitales pendientes. Consultar calendar_review y la decisión para condiciones de una corrección futura.

Revisión de rechazos D44: las 2.742 pólizas D43 (1.513/1.010/219) conservan cliente y contador, con 22 mudanzas de motor; suman 2.931 filas test que deben conservarse. 83 tienen rechazos repetidos y 372 no tienen siniestro observado de ocurrencia 2024. Los últimos segmentos concentran 58.932.110,98 CU y 33,5725 % del neto observado 2024: no borrarlas por la etiqueta. REN00 conserva la decisión literal pendiente; renewal_decision ya está fuera de predictores según protocolo 1.3. No recodificar a renewed ni confundir rechazo de póliza con repudiated. Fechas pendientes por instrucción expresa, sin cambios de datos/catálogo. [Informe con doce casos y explorador completo](../Hackaton/Semana 1/Revision_rechazos/runs/renewals_20261016T202736Z_b0ddd9b5/informe.html); 88 controles de datos y 20 de interfaz. Ver declined_renewal_review y D44.

REN00 aplicado por autorización, D45: [catálogo activo](../Hackaton/Semana 1/Limpieza/current_dataset.json), [informe](../Hackaton/Semana 1/Limpieza/runs/renaudit_20261016T203904Z_657dd741/informe.html). audit_ren00 identifica las 2.742 pólizas D44 en 12.041 periodos (9.110 train, 2.931 test), sin cambiar ningún dato previo. Se conservan los 3.035.950 periodos y 162.546 siniestros DUP01. renewal_decision, sus derivados identificables y audit_* se excluyen en el selector real del runner; protocolo 1.4. Pasaron 94 controles de datos, 36 del selector y 12 pruebas del núcleo. Fechas y semántica siguen pendientes; marca futura de cohorte es solo auditoría, nunca predictor. No hay F0 completo, T0 operativo ni entrenamiento. Ver renewal_audit_application y D45.

Prehistoria D46: revisión de 413 expedientes (296/67/50), un cliente/póliza por expediente. 244 renovaciones al inicio 2021 son compatibles con historia truncada; 169 pérdidas anteriores al negocio nuevo requieren aclaración. No hay reportes estrictamente anteriores al primer inicio. Los 409 aceptados suman 1.721.459,84 CU, conservados en conciliación separada fuera del objetivo de los periodos suministrados. PRE00 es propuesta sin activar: no mover fechas, asignar al primer periodo, inventar exposición ni borrar. [Informe con doce casos y explorador completo](../Hackaton/Semana 1/Revision_prehistoria/runs/prehistory_20261016T210357Z_13161fac/informe.html); 92 controles de datos y 19 de interfaz. Catálogo REN00 y protocolo 1.4 permanecen iguales; fechas/capitales pendientes. Ver prehistory_claim_review y D46.

PRE00 aplicado por autorización, D47: [catálogo activo](../Hackaton/Semana 1/Limpieza/current_dataset.json), [informe y bitácora](../Hackaton/Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/informe.html). Solo se añade audit_pre00 a los 413 IDs D46; se conservan los 162.546 siniestros y todas las celdas previas. Los 409 aceptados mantienen 1.721.459,84 CU separados del objetivo actual; los asignados conservan 741.156.868,43 CU. Las diez referencias restantes, REN00 y DUP01 permanecen iguales. Pasaron 102 controles; asignación reconstruida por otro algoritmo y consumidor real idéntico en 3.035.950 periodos. Control PRE00 rechaza asignaciones incompatibles antes de sumar; audit_* queda fuera de predictores. Protocolo 1.5, sin T0 operativo ni entrenamiento. Cobertura histórica, fechas y demás pendientes conservados. Ver prehistory_audit_application y D47.

Capitales pendientes revisados, D48: [informe y explorador](../Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248/informe.html), [propuesta sin aplicar](../Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248/proposal.json). Lista CAP01 intacta: 1.454 filas/1.452 pólizas, 691 edificios y 763 contenidos; 5.587 periodos y 128 siniestros. Ningún respaldo anterior próximo original más reciente pasa el criterio. Hay 879 retrospectivos D34 y 109 apoyos posteriores con cambio de contexto previo; 108 sin referencia original habitual. Dependencias, T/W, faltantes y otras contradicciones quedan separadas. Dentro de los 879 hay 12 discrepancias numéricas anteriores adicionales: primer escenario retrospectivo propuesto de 867 filas, 111 con ancla 2025, sin aplicar ni autorizar. Tres apoyos anteriores dependen de CAP01; veinte referencias antiguas favorables contradicen el capital más reciente. No ampliar CAP01 ni elegir solo anclas convenientes. Pasaron 59 controles de datos y 20 de lógica; dos figuras inspeccionadas, sin revisión independiente. Catálogo PRE00/REN00, importes, fechas y todos los pendientes permanecen iguales; protocolo 1.5 sin cambios. Ver pending_capital_review y D48.

CAP02R aplicado por autorización, D49: [informe](../Hackaton/Semana 1/Limpieza/runs/capretro_20261016T213644Z_9b52ecc4/informe.html), [catálogo retrospectivo](../Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json). Se dividen por mil 867 filas D48 (430 edificios, 437 contenidos); 111 usan respaldo posterior test 2025 (50/61), señaladas en bitácora y extracción propia. Las tablas test no cambian. Se conservan originales, todos los campos ajenos al capital, 2.073 CAP01 y 587 pendientes en esta rama. Total retrospectivo: 2.940 capitales corregidos. La base current_dataset.json permanece idéntica, con sus 1.454 pendientes, para no adoptar reconstrucción futura como preparación por corte. 62 controles propios, reversión e idempotencia verificadas. Protocolo 1.6; no aprobación para backtests por fecha, T0/F0 o entrenamiento. Consultar retrospective_capital_application y D49.


## D50: diagnóstico independiente de Claude y técnicas por ramo, 16 de octubre de 2026

[Informe](../Hackaton/Semana 1/Modelado/Investigacion_tecnicas_claude/INFORME.md), [evidencia](../Hackaton/Semana 1/Modelado/Investigacion_tecnicas_claude/runs/diag_20261016T210304Z_df57908a/evidencia.json), [fuentes](../Hackaton/Semana 1/Modelado/Investigacion_tecnicas_claude/fuentes.json) y [verificación](../Hackaton/Semana 1/Modelado/Investigacion_tecnicas_claude/verification.json). A petición del participante, Claude repitió de forma independiente los diagnósticos sobre el catálogo DUP01 (asignación de 110.496/26.266/23.670 aceptados únicos, igual que D42; 413 expedientes fuera de historia, los mismos de PRE00) y reunió 28 fuentes primarias nuevas (C01–C28) sobre GLM/GAM Tweedie, calibración, frecuencia–severidad, boosting con offsets y restricciones, credibilidad, colas, reporte y redes. Solo diagnósticos descriptivos: sin entrenar, sin T0 operativo, sin cambiar datos. Complementa D37 y conserva su primera ola.

Lo que decide: customer_service_contacts es un indicador del siniestro del propio periodo (frecuencia 0,0003 con cero contactos y 1,081 con tres o más en autos; D² one-way 0,43 frente a 0,04 del resto; 7,2 % del train con tres o más contactos frente a 0,8 % del test) y debe excluirse por contrato, como ya ocurre con renewal_decision y audit_*. Los conteos son casi Poisson con exposición (dispersión 1,14/1,05/1,03), así que zero-inflated no es primera opción. La severidad por peligro es gamma con p implícita 1,50–1,63, pero mezclar peligros lleva la p del ramo a 1,74–1,99: comparar potencia de ajuste 1,5 y 1,9 evaluando en 1,5, y separar lesiones (CV 6,52, Hill 2,02, máximo 11,9 millones CU). No hay eventos catastróficos; el clima del año anterior ordena la frecuencia como el contemporáneo; la historia propia multiplica la frecuencia por 1,5–2,7 y la de otros ramos no aporta; frecuencia plana 2021–2024 y severidad de hogar al alza 2–5 % anual; el desarrollo pendiente se concentra en lesiones y hundimiento. Ninguna variable legítima supera 0,04 de D² one-way.

Propuesta: primera ola D37 con dos potencias; después componentes por peligro, Poisson–gamma, duración e historia con contracción; calibración (balance, factor, isotónica C02, autocalibración C01) y sensibilidades T1 acotadas; EBM/GAM interpretable y SHAP para el informe; contenidos como ramo de comparación inicial. Candidatos a catálogo: EBM (C27), HistGradientBoosting Poisson/gamma (C26), recalibración isotónica, splicing de lesiones (C10) y corrección de reporte por mes. Verificación propia 11/11 con el catálogo PRE00 activo (las capas REN00/PRE00 no cambian valores usados); sin revisión independiente ni consulta de notebooks de Kaggle. Ver D50 y technique_research_claude.

Doce discrepancias numéricas revisadas, D51: [informe con todos los casos](../Hackaton/Semana 1/Revision_discrepancias_capital/runs/discrepancies_20261016T214010Z_fd80a8ba/informe.html), [propuesta sin aplicar](../Hackaton/Semana 1/Revision_discrepancias_capital/runs/discrepancies_20261016T214010Z_fd80a8ba/proposal.json). Son doce pólizas de contenidos, 63 periodos y cero siniestros observados. La hipótesis /1000 encaja con el nivel previo a ampliación (+1,69–2,42%) aunque baja 16,24–34,53% frente al último capital ampliado. En 9.909 secuencias de 9.702 otras pólizas con capitales originales normales y contexto completo se repite la vuelta al nivel inicial, con mediana +2,00%; patrón descriptivo, no confirmación contractual. Se propone un escenario de once con contexto completo; C48613718 queda condicionado por security_level faltante en el segmento inicial. C21091984 usa test 2025. No reparar el nivel normal intermedio ni anualizar capital por exposición. Pasaron 62 controles de datos, 17 de lógica y cuatro de propuesta/enlaces. Ambos catálogos intactos: 587 pendientes en retrospectiva y 1.454 en la base. Los otros 575 quedan inventariados sin adjudicación nueva; próximo grupo sugerido 109 con cambios de contexto. Protocolo 1.6 sin cambios, sin entrenamiento ni revisión independiente. Ver numeric_capital_discrepancy_review y D51.

CAP03R aplicado por autorización, D52: [informe](../Hackaton/Semana 1/Limpieza/runs/capnumeric_20261016T215017Z_75a1fda5/informe.html), [once cambios](../Hackaton/Semana 1/Limpieza/runs/capnumeric_20261016T215017Z_75a1fda5/ledger/all_capital_changes.csv). Solo once capitales de contenidos /1000 sobre CAP02R; C21091984/C02362784 usa ancla test 2025 y pasa de 26.200.000 a 26.200 CU. Quedan 576 pendientes, incluido C48613718 con 29.300.000 CU y su referencia inicial nula intacta. Se conservan los capitales normales intermedios, 2.073 CAP01, 867 CAP02R y todas las demás celdas. Acumulado de 878 reparaciones retrospectivas, 112 con ancla 2025 y 2.951 correcciones totales. current_retrospective_dataset.json avanza a CAP03R; la base current_dataset.json sigue idéntica con 1.454 pendientes. 100 controles propios, reversión e idempotencia verificadas; protocolo 1.7. Sin confirmación de unidad o nivel contractual, preparación causal aprobada, entrenamiento o validación independiente. Ver numeric_capital_application y D52.

Revisión de 109 capitales con cambio de contexto, D53: [informe con doce casos y explorador completo](../Hackaton/Semana 1/Revision_contexto_capital/runs/context_20261016T215509Z_0cb0ff53/informe.html), [lista propuesta sin aplicar](../Hackaton/Semana 1/Revision_contexto_capital/runs/context_20261016T215509Z_0cb0ff53/tables/proposed_scale_changes_NOT_APPLIED.csv). Son 75 edificios y 34 contenidos, 571 periodos y ocho siniestros. 31 casos muestran solo T→W; otros 78 cambian de dirección. Los 109 tienen referencia inmediatamente posterior original, contexto D34 completo e igual y escala /1000 plausible. Se propone una operación retrospectiva separada para esos 109, sin autorización o aplicación. 17 usan test 2025 (6/11); los demás también tienen información posterior. Conservar los límites propios de cada inmueble/bienes y los nulos anteriores de tres casos. En B19256617, la fila 2023 de 388.000.000 tiene ancla 400.000; el otro capital de 377.000.000 sigue pendiente fuera del grupo, sin cascada. La igualdad se limita al criterio, no a todos los factores tarifarios: days_unoccupied cambia en 68 pares informados y otro tiene faltante. Pasaron 1295 controles propios y 131 de lógica, dos figuras inspeccionadas, sin revisión independiente o navegador acreditados. Ambos catálogos y todos sus datos intactos: 576 pendientes en retrospectiva y 1.454 en la base. Los otros 467 quedan inventariados sin nueva adjudicación. Protocolo 1.7, fechas y CON01 sin cambios, sin entrenamiento. Ver context_capital_review y D53.

D54, CAP04R autorizado: 109 filas D53 /1000 sobre CAP03R (75 edificios y 34 contenidos), 17 respaldos posteriores de test 2025 (6/11) y 467 pendientes preservados. B19256617/B00962235 mantiene 377.000.000 CU y C48613718/C01596694, 29.300.000. La nueva capa conserva los demás campos, T/W y las reparaciones anteriores. Acumulado de 987 correcciones retrospectivas, 129 respaldos test 2025 y 3.060 correcciones contando CAP01. La base sigue intacta con 1.454 pendientes. Protocolo 1.8; reconstrucción retrospectiva sin aprobación causal por corte. [Informe](../Hackaton/Semana 1/Limpieza/runs/capcontext_20261016T220924Z_4b397220/informe.html), [109 cambios](../Hackaton/Semana 1/Limpieza/runs/capcontext_20261016T220924Z_4b397220/ledger/all_capital_changes.csv). 602 controles propios, reversión e idempotencia verificadas. Los 17 respaldos test tienen extracción propia y señal solo en bitácora. current_retrospective_dataset.json avanza a CAP04R; current_context_capital_correction.json conserva la operación. Sin cambios en fechas, siniestros o CON01, sin entrenamiento o validación independiente. Ver context_capital_application y D54.
