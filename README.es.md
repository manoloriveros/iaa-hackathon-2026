# Una prima de riesgo para cada periodo de póliza, construida y contrastada con IA

AI Hackathon IAA 2026 · Parte 1, mercado establecido · Manuel Rodríguez, equipo individual (Kaggle: manoloriveros). La versión en inglés de esta página es el [README.md](README.md).

La edición conjunta de ambas semanas está en [el informe de cinco páginas](privado/entrega_final/informe_dos_semanas.pdf), disponible localmente fuera de Git por sus veinte referencias comerciales, y en [el dashboard comparativo](docs/entrega/panel_analisis.html). [Fuentes, figuras y validación de esa edición](docs/entrega/informe_final/README.md). El recorrido de semana 1 que sigue se conserva como antecedente; la selección de semana 2 continúa abierta en el corte del 26 de octubre.

El modelo predice, para cada periodo de póliza de 2025 en autos particulares, edificios y contenidos del hogar, el coste último esperado de los siniestros ocurridos en el periodo, neto de franquicias y recobros y sin siniestros rechazados. El modelo final es la Mezcla por peligro (S30 en el código y los recibos). En cada ramo mezcla modelos Tweedie del coste total con modelos de frecuencia × severidad por peligro y fija el nivel de 2025 con dos años fuera de muestra. La entrega final, S41, conserva ese modelo y solo calibra su nivel de 2025, con un factor por ramo (0,9962 autos, 1,0260 edificios, 1,0126 contenidos) leído de seis sondas al tablero público y aplicado con una regla de credibilidad fijada antes de puntuarlas; no se reentrenó nada. La IA participó en todas las etapas, sobre todo para contrastar posturas: tres líneas de trabajo publicaron sus hipótesis en un foro común antes de calcularlas, y un enjambre de agentes de validación auditó el proyecto cada seis horas. Los datos son sintéticos y los importes van en una unidad monetaria ficticia (CU).

| Cifra | Valor |
| --- | --- |
| Puntuación pública de la entrega final (D² Tweedie, potencia 1,5) | 0,13016; el equipo quedó primero entre 43 equipos en la tabla pública según la consulta del 22 de octubre; el modelo solo (S30) puntuó 0,12996 |
| D² de 2024 fuera de muestra | 0,138, frente a 0,071 de una tasa constante por ramo |
| Periodos de póliza de 2025 predichos | 626.639, con diez controles de formato e integridad |
| Coste esperado de 2025 | 213,7 millones de CU en la entrega final (212,0 millones antes de calibrar el nivel) |

Los envíos anteriores, las seis sondas de nivel y dos calibraciones posteriores del mismo tablero solo aparecen en la curva de aprendizaje del informe, como el camino que llevó a la entrega final. La página 4 del informe cuenta la calibración del nivel completa: en qué consiste S41, la forma cerrada, la regla fijada antes de mirar, las hipótesis en que se apoya y por qué se eligió después de que una batería de sensibilidad corrigiera el ruido del óptimo público.


Para hacer la revisión del participante, abre la [guía actual](docs/REVISION_PENDIENTE_PARTICIPANTE.md) y el [panel de revisión](docs/panel_revision.html#revision). Las decisiones técnicas y las limitaciones ya aceptadas se separan de la revisión general pendiente.

## Entregables finales

| Entregable | Archivo |
| --- | --- |
| Informe, cinco páginas calificables y un anexo | [docs/entrega/informe_es.pdf](docs/entrega/informe_es.pdf) · versión en inglés [report_en.pdf](docs/entrega/report_en.pdf) |
| Panel del modelo, sin conexión, en español o inglés | [docs/entrega/panel_modelo.html](docs/entrega/panel_modelo.html) (descargarlo y abrirlo en un navegador) |
| Láminas y guion del video | [docs/entrega/video/](docs/entrega/video/) |
| Cómo se usó la IA y cómo se comprobó | [docs/entrega/USO_DE_IA_ES.md](docs/entrega/USO_DE_IA_ES.md) · [AI_WORKFLOW_EN.md](docs/entrega/AI_WORKFLOW_EN.md) |
| Las cifras detrás de cada entregable | [docs/entrega/datos/cifras_entregables.json](docs/entrega/datos/cifras_entregables.json), con la ruta y el SHA-256 de cada fuente |
| Expediente de trabajo: foro y registro de decisiones | [docs/expediente/](docs/expediente/) |
| Adaptación de la semana 2 | [Informe conjunto y figuras](docs/entrega/informe_final/README.md); comparación al 26 de octubre, selección final pendiente |

## Cómo se organizó el trabajo

Dos asistentes de IA, Claude y Codex, trabajaron en tres líneas: modelado, alternativas creativas y contraste. Ninguna línea podía usar las predicciones de otra sin autorización. Las hipótesis iban al foro con su criterio de aceptación antes de calcularse, y los resultados adversos se publicaban igual que los favorables. Tres agentes de validación (datos, modelos y gobierno) se ejecutaron de forma programada y registraron cada hallazgo con un criterio de cierre y el revisor humano que necesita. Las reglas, los metadatos y las puntuaciones de Kaggle se leyeron por una conexión MCP de solo lectura, y cada envío se hizo con la autorización escrita del participante. El participante autorizó las reglas de datos y los envíos, aprobó el modelo final y lo confirmó como definitivo el 20 de octubre; el 22 de octubre autorizó las sondas y el 23, tras la batería de sensibilidad, seleccionó S41 como entrega final en Kaggle. Las comprobaciones de IA no se presentan como revisión profesional independiente.

![Flujo de trabajo con IA](docs/entrega/figuras/es/flujo_ia.png)

## Cómo reproducir

El [reentrenamiento completo de semana 2 desde originales](docs/REENTRENAMIENTO_ORIGINALES.md) terminó en un entorno limpio: 57 etapas, 87 modelos finales nuevos y CSV F3c, F3d y F4c idénticos a los históricos. La guía documenta dos restauraciones de código y diferencias numéricas internas. La reproducción por otra persona sigue pendiente; no hubo envíos a Kaggle.

Los datos del concurso no están en este repositorio: las reglas prohíben redistribuirlos. Los scripts los leen de una carpeta con la estructura de `Hackaton/Semana 1`, que se indica con `--semana1=<carpeta>` o con la variable `IAA_SEMANA1`. Conviene instalar las versiones de `requirements.txt` (Python 3.13); con otras versiones la mezcla se repite igual, pero el reentrenamiento puede no ser byte a byte.

```text
python reproducir.py plan --objetivo=S30
python reproducir.py mezcla --objetivo=S30 --semana1=<carpeta> --trabajo=trabajo_mezcla
python reproducir.py todo --objetivo=S30 --semana1=<carpeta> --trabajo=desde_cero
python reproducir.py verificar --trabajo=desde_cero
python herramientas/regenerar_s41.py --raiz <espacio de trabajo>
```

`regenerar_s41.py` aplica los tres factores de nivel al CSV de la mezcla, comprueba que la copia tenga el SHA-256 de la entrega final y pasa los diez controles de entrega; necesita los test originales para saber el ramo de cada fila. `mezcla` reconstruye el CSV de la mezcla desde los componentes guardados en segundos y compara su SHA-256 con el del archivo que recibió Kaggle; los componentes guardados están fuera de Git. `todo` parte de los once archivos originales y reentrena todos los componentes (30 nodos para el modelo final, unas diez horas con dos núcleos). El código de salida es 0 si todo coincide, 1 ante un fallo o una diferencia, 2 si la orden es incorrecta y 3 cuando se pidió `--continuar-si-difiere` y difieren archivos intermedios aunque el CSV coincida. Reentrenar toda la receta desde los originales en la nube de referencia reconstruyó byte a byte el archivo entregado, y una réplica desde los estimadores guardados, con los reajustes bloqueados, coincidió en todas las salidas; `docs/REPRODUCCION_COMPLETA.md` guarda el recibo y el kit para otro operador.

Para regenerar y comprobar los entregables desde las mismas fuentes:

```text
python herramientas/cifras_entregables.py --raiz <espacio de trabajo> --salida docs/entrega/datos/cifras_entregables.json
python herramientas/construir_entrega.py todo
python herramientas/verificar_entregables.py
```

## Qué hay en cada carpeta

| Carpeta o archivo | Contenido |
| --- | --- |
| `reproducir.py` | Punto de entrada único (`plan`, `datos`, `componentes`, `todo`, `mezcla`, `verificar`), versión 1.2 |
| `receta/` | La receta congelada: 36 nodos con scripts, argumentos, dependencias, salidas y huellas esperadas |
| `src/` | Etapas de datos, variables, modelos, severidades, mezcla y validación, copiados sin cambios desde donde se ejecutaron |
| `herramientas/` | Huellas, inventario, la batería de 45 casos de control, los constructores de los entregables y su verificador |
| `docs/entrega/` | Entregables finales: informe, panel, láminas, guion del video, guía de IA y el archivo de datos que los sostiene |
| `docs/expediente/` | Expediente de trabajo exportado con los identificadores sintéticos enmascarados: foro común y registro de decisiones |
| `docs/controles/`, `docs/evidencia/`, `docs/fuentes/` | Resultados de la batería de control, hallazgos, recibos de repetición y las reglas oficiales tal como se consultaron |
| `registro/` | Estado de la entrega, requisitos, decisiones humanas fechadas y recibos |
| `privado/` | Copias exactas de CSV, componentes guardados y corridas nuevas; fuera de Git |

La [guía técnica](docs/GUIA_TECNICA.md) conserva las notas detalladas de reproducción, el historial de verificación y las convenciones de control de versiones.

## Límites

Tras la elección, once experimentos preinscritos, entre ellos un backtesting del IBNR, y un análisis de reservas midieron estos límites; el anexo del informe los detalla, junto con un duodécimo que no hizo falta correr. Con una sola valoración de siniestros (31-12-2024) no se puede demostrar la suficiencia de las reservas. Con reservas ×0,75 y ×1,25 el D² de 2024 solo pasa de 0,1379 a 0,1372, pero el nivel de 2025 de la mezcla se mueve hasta un 6,8 % y el de S41 hasta un 5,7 %, y un error del 4,4 % en las reservas de caso de autos ya mueve el de S41 un 1 %: las reservas siguen siendo una incertidumbre material en los tres ramos, una limitación que el participante mantuvo para S41. El nivel de 2025 es el punto más débil. Los dos cortes de edificios distan un 3,4 % de su media, y un escenario sitúa el nivel de autos de la mezcla alto entre un 1,5 % y un 2,5 %; la entrega final recalibró el nivel con un tercio del test, así que el privado es su única comprobación independiente: con el ruido del óptimo público corregido, la ganancia esperada de S41 frente a la mezcla va de +0,000019 a +0,000083 con las tres previas probadas, y, frente a tres indicadores que no usan el tablero, los factores quedan apoyados en edificios y contenidos y solo en parte en autos, con cualquiera de las dos lecturas de la prima escrita (hallazgo abierto DATA-006). La ventaja del modelo final sobre el mejor envío anterior no es robusta: basta quitar seis clientes para invertirla. Los cortes de 2023 y 2024 se usaron para elegir, así que no son una prueba final independiente. La disponibilidad de las variables al cotizar aún necesita la confirmación del dueño de los datos, y 149 capitales divididos entre mil siguen sin confirmación histórica. No hay revisión independiente: la reproducción la hizo el mismo flujo, y el participante declaró la independencia y la suficiencia de las reservas como limitaciones del ejercicio. El informe detalla cada límite con su efecto y la comprobación que lo cerraría.
