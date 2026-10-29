# Revisión cruzada del dictamen de Codex

Autor: Claude. 19 de octubre de 2026, a petición del participante. Contrasta el dictamen de Codex del mismo día ([REVISION_DESDE_EL_PARTICIPANTE.md](REVISION_DESDE_EL_PARTICIPANTE.md)) con los archivos del proyecto. Recalculé las cifras que sostienen sus conclusiones con un script propio y leí el código de la mezcla. No hubo entrenamiento, inferencia, mezcla nueva ni envío. Es una revisión de IA; no sustituye la revisión humana ni la aceptación de los supuestos.

## Conclusión

Comparto lo esencial del dictamen. S30 y S22 son técnicamente consistentes, la ventaja de S30 es pequeña y no concluyente, y el modelo todavía no está acreditado como tarificador para cotizar pólizas reales. Las cifras que pude recalcular coinciden con las de Codex.

Cambiaría el planteamiento de la decisión en cuatro puntos. La parte 1 se cierra con una única elección en Kaggle, que puede hacerse ya y no depende de la reproducción ni de las reservas. Elegir entre S30 y S22 mueve muy poco, porque los dos archivos son casi la misma predicción. La incertidumbre cuantitativa más grande está en el nivel de 2025, que el dictamen trata de pasada. Y el argumento de influencia por cliente está contado por un solo lado; leído de forma simétrica, la ganancia de S30 no depende de unos pocos clientes.

Además, una parte del dictamen quedó respondida una hora después por CLA-20261019-004, lo que cambia la acción recomendada sobre la reproducción.

## Lo que comprobé y coincide

| Afirmación del dictamen | Mi comprobación |
| --- | --- |
| D² V24 de S22 0,13774159 y de S30 0,13787963; ganancia 0,000138 | Mismo resultado. La etiqueta T0 del archivo de predicciones alineadas es idéntica a la de las bases actuariales en todas las filas |
| Ganancia con reservas −25 % y +25 % | +0,000105 y +0,000169; S30 sigue por delante en ambos escenarios (el dictamen no lo menciona) |
| Diez clientes más favorables aportan 0,000173 | Mismo resultado |
| 1.454 capitales ajustados, 149 sin confirmar, 123 en test (77 edificios, 46 contenidos), 24.667,97 CU en S30 (0,01164 %) | Mismas cifras, calculadas desde las marcas de auditoría de F0 y el CSV de S30 |
| La receta tiene 36 nodos; S30 usa 30 y S22, 32; 13 salidas fuera del cotejo | Mismo conteo en `receta/receta.json` |
| La frase del README sobre 2025 es demasiado amplia | Correcto. `comun.py` divide la prima de cada fila por la media de su año, también en 2025, y la regla de nivel compara totales predichos de 2025 con V24 |
| La forma depende del lote | Correcto. `shape` y `shape_rate` en `mezcla3.py` usan la media geométrica de todas las filas que se predicen juntas |
| `requirements.txt` promete una reconstrucción byte a byte | Correcto; la frase está en la línea 2 y esa igualdad no está acreditada |
| Cierre el 23 de octubre a las 11:00 de Bogotá, diez envíos diarios, rúbrica 40/25/20/15 | Coincide con la consulta oficial archivada |

Una limitación de mi comprobación: las predicciones de V23 y V24 de ambos candidatos salen del archivo alineado que Codex preparó para N48. Verifiqué su etiqueta contra las bases, pero no reconstruí esas predicciones desde los componentes.

## Dónde discrepo o añado

### La parte 1 se cierra con una sola elección

Las reglas permiten seleccionar una única predicción final por parte. Si no se selecciona ninguna, Kaggle usa la de mejor puntuación pública. Según el registro del proyecto, esa es hoy S30 (0,12996 frente a 0,12988 de S22, y los demás envíos están por debajo). En términos del concurso, S22 no puede funcionar como respaldo de la parte 1: es una alternativa documentada que solo se usaría si se elige de forma activa en su lugar.

El dictamen dice que no daría por cerrada la entrega. Ahí mezcla dos entregas con fechas distintas. La parte 1 solo exige el CSV seleccionado antes del viernes a las 11:00. El informe, el video y el código se entregan al final de la parte 2, y es a esa entrega a la que pertenecen la reproducción completa, las reservas, los prompts y la elegibilidad. Separarlas permite cerrar ya lo que puede cerrarse.

Recomiendo seleccionar S30 en Kaggle de forma explícita esta semana y guardar el comprobante. El resultado sería el mismo que el valor por defecto, pero la elección queda trazable y deja de depender de que nadie suba antes del viernes un envío con mejor puntuación pública.

### Elegir entre S30 y S22 cambia poco

| Ramo | Total 2025 S22 (M CU) | Total 2025 S30 (M CU) | Correlación de los logaritmos | Filas que difieren más de 5 % |
| --- | ---: | ---: | ---: | ---: |
| Autos | 118,89 | 118,90 | 0,9998 | 1,2 % |
| Edificios | 73,93 | 74,37 | 0,9999 | 0,0 % |
| Contenidos | 18,86 | 18,69 | 0,9993 | 19,9 % |
| Cartera | 211,69 | 211,96 | 0,9997 | 6,4 % |

Los dos archivos predicen prácticamente lo mismo; solo contenidos tiene diferencias apreciables fila a fila. En la cartera, todas las estimaciones puntuales favorecen a S30: V24 (+0,000138), V24 con reservas al −25 % y al +25 %, V23 (+0,000162) y la puntuación pública (+0,00008). Ninguna es concluyente y V23 y V24 ya se usaron para elegir pesos, así que no son evidencia independiente. Por ramo el signo no siempre se mantiene: en edificios V23, S30 queda por debajo.

Sobre el criterio N48, discrepo en el encuadre. N48 se diseñó como filtro para promover un retador, es decir, para decidir si valía la pena gastar un envío y sustituir al candidato vigente. Ahora los dos ya están puntuados y la pregunta es cuál tiene mayor puntuación esperada. Que S30 no supere el filtro no convierte a S22 en mejor opción. Con todas las estimaciones de cartera del lado de S30 y sin un motivo concreto en su contra, elegirlo es razonable y no hace falta presentarlo como excepción a un criterio estadístico. La razón que registraría es esta: estimación puntual favorable en todos los cortes de cartera, diferencia no concluyente y consecuencia pequeña si la elección resultara equivocada.

### La lectura de influencia está contada por un solo lado

El dictamen dice que los diez clientes más favorables a S30 aportan 0,000173, más que la ganancia neta de 0,000138, y concluye que el resultado depende de pocos casos. El mismo registro de Codex tiene la otra mitad del dato, que el texto no muestra: los diez clientes más adversos restan 0,000135.

| Diagnóstico sobre V24 (373.831 clientes) | Aporte a la ganancia de D² |
| --- | ---: |
| Ganancia total | 0,000138 |
| Diez clientes más favorables | +0,000173 |
| Diez clientes más adversos | −0,000135 |
| Resto, sin los diez de cada extremo | +0,000100 |
| Filas con el 1 % de siniestros más costosos | +0,000047 |
| Demás filas | +0,000091 |

Al quitar los diez clientes de cada extremo queda el 72 % de la ganancia, y dos tercios vienen de filas sin siniestros grandes. En una suma de casi 374.000 aportes con un neto pequeño, es normal que los diez mayores de un lado superen al neto; por sí solo, ese dato no muestra concentración. La conclusión no cambia (la diferencia sigue sin ser concluyente), pero el motivo es otro: la ventaja es pequeña frente al ruido que generan las pérdidas grandes en ambos sentidos.

### El nivel de 2025 pesa más que la elección de candidato

La mezcla fija el nivel de 2025 con un factor de escala por ramo. Ese factor es el promedio de dos: el que mejor ajusta la métrica en 2023 (f23) y el que mejor la ajusta en 2024 (f24). En S30, los dos factores son:

| Ramo | f23 | f24 | Cambio de f23 a f24 | Factor usado en 2025 |
| --- | ---: | ---: | ---: | ---: |
| Autos | 0,9864 | 1,0047 | +1,9 % | 0,9955 |
| Edificios | 1,0589 | 1,1343 | +7,1 % | 1,0966 |
| Contenidos | 1,0776 | 1,0924 | +1,4 % | 1,0850 |

El dictamen cita que en edificios V24 el coste observado es 1,099 veces la predicción, y advierte con razón que no hay que multiplicar 2025 por ese cociente. Ese 1,099 es el cociente monetario. El factor que maximiza la métrica en V24 es 1,071 (coincide con f24/f23), y el nivel de 2025 ya incorpora la mitad de ese ajuste a través del promedio. Lo que el dictamen no recoge es lo que sí importa: el factor subió entre los dos cortes en los tres ramos, y promediar supone que esa subida no continúa en 2025. El proyecto ya había documentado (D67) que la prima escrita por año expuesto del generador crece entre 2,7 % y 3,4 % al año en autos y entre 5,0 % y 5,5 % en hogar.

Para dimensionarlo, medí en V24 cuánto cambia D² si se mueve el nivel de S30. Es un diagnóstico con las etiquetas de 2024, no una propuesta de escala.

| Cambio de nivel en V24 | Efecto en D² de la cartera |
| --- | ---: |
| Edificios −3,5 % | −0,00029 |
| Edificios +3,5 % | +0,00016 |
| Toda la cartera −3 % | −0,00041 |
| Toda la cartera +3 % | +0,00016 |
| Factor óptimo por ramo con las etiquetas de 2024 (referencia, no alcanzable) | +0,00025 |
| Diferencia entre S30 y S22, como comparación | +0,00014 |

Un error de nivel de pocos puntos porcentuales cuesta tanto o más que toda la diferencia entre candidatos. La desviación Tweedie es simétrica en escala logarítmica alrededor del nivel óptimo, así que el coste es parecido si el error es por exceso o por defecto; la asimetría de la tabla se debe a que el nivel de V24 quedó por debajo del óptimo.

No cambiaría el nivel para la parte 1. Dos cortes no distinguen una tendencia de un mal año de edificios (clima, hundimientos), el participante ya decidió no usar sondas de nivel en el leaderboard y un CSV nuevo a cuatro días del cierre añadiría una decisión sin validar. Sí lo pondría en la tabla de decisiones como la principal incertidumbre cuantitativa, lo explicaría en el informe y lo trataría como primera pregunta de diseño en la parte 2, donde el nivel y la tendencia hacia el periodo tarifado deberían proyectarse de forma explícita.

Para el uso como tarificador hay una consecuencia adicional. Con el nivel aprendido en 2023, el coste observado de 2024 supera a la predicción en un 4,3 % en la cartera y en un 9,9 % en edificios. El escalado que maximiza la métrica no garantiza que la prima de riesgo total cubra el coste total. Una herramienta real necesitaría un paso de balance monetario aparte; el informe debería decirlo así.

### La métrica oficial describe otra línea base

La página oficial define el D² Tweedie «relative to a constant-rate baseline». La implementación de scikit-learn usa como base la media de la variable, sin exposición. Recalculé V24 con una base proporcional a la exposición: D² de S30 baja de 0,1379 a 0,1065, pero la ganancia frente a S22 apenas cambia (0,000143 frente a 0,000138). La elección entre candidatos no depende de esa ambigüedad, porque la base es común a ambos. Las comparaciones absolutas entre cifras locales y públicas sí dependen de ella, incluida la fórmula de «público esperado» de `mezcla3.py`. El informe debería decir qué base usan sus cifras locales.

### Parte del dictamen ya tiene respuesta

El dictamen se escribió a las 20:03 UTC. A las 20:14, CLA-20261019-004 respondió tres de sus puntos abiertos:

| Punto del dictamen | Respuesta posterior |
| --- | --- |
| La búsqueda no encontró modelos guardados, aunque podrían existir en otro sitio | Ningún script guarda el estimador ajustado; 31 nodos (24 de ajuste y 7 GLM) exigen volver a ajustar |
| Recuperar recibos de la cadena completa | La corrida completa histórica no es recuperable; quedó en el contenedor de nube de otra sesión, fuera del alcance actual |
| Las 13 salidas fuera del cotejo obligan a delimitar el contrato | Diez son partes de `CFS_motor` que nunca existieron y tres son archivos en float64 de las corridas CFS de autos, excluidos con nota en la receta |

Eso cambia la acción recomendada. Recuperar piezas antiguas ya no es posible, así que la única forma de acreditar la cadena completa es una corrida nueva de `reproducir.py todo` (unas diez horas con dos núcleos y 8 GB de memoria, según el README), con su recibo y una comparación por tolerancia donde la igualdad byte a byte no se consiga. Las reglas piden al ganador código de entrenamiento e inferencia capaz de generar el envío ganador, documentación y una descripción del entorno; no piden modelos guardados. Esa corrida implica volver a ajustar, algo que la coordinación vigente excluye, de modo que la decisión de autorizarla antes del 30 de octubre corresponde al participante.

### Precisiones documentales

Comparto las correcciones al README sobre los datos de 2025 y a `requirements.txt`. La de «resultados equivalentes» en el informe me parece menor: la frase dice que la incertidumbre admite resultados equivalentes, es decir, que no descarta la igualdad, y eso es correcto. La redacción de Codex es más clara para un lector con formación estadística, y se puede adoptar sin más.

Añado dos. El README abre ahora con el enlace a esta revisión de IA, escrita en segunda persona para el participante. El repositorio llegará al jurado con la parte 2, y la comunicación pesa un 15 %; el README debería abrir con la solución y llevar las revisiones a una sección de gobierno y control. Por otro lado, el dictamen usa en el texto principal nombres internos (N48, N56, D67, GOV-007, s17, F3) sin explicarlos, contra el criterio editorial de `AGENTS.md`. Si va a quedar como documento de referencia, convendría un glosario breve o mover esos nombres a un anexo.

## Decisiones que propondría

| Decisión | Propuesta de Claude | Quién y cuándo |
| --- | --- | --- |
| Selección final de la parte 1 | Seleccionar S30 en Kaggle y guardar el comprobante | Participante, antes del viernes 23 a las 11:00 |
| Razón de la elección | Estimación puntual favorable en todos los cortes de cartera, diferencia no concluyente, archivos casi idénticos | Participante, al registrar la decisión |
| Nivel de 2025 | Mantener el promedio de factores en la parte 1; documentarlo como la principal incertidumbre; proyectar la tendencia de forma explícita en la parte 2 | Participante; informe y diseño de la parte 2 |
| Uso como tarificador | Limitarlo al concurso. Para un uso real faltan balance monetario, constantes de normalización fijas y fechas de disponibilidad de variables | Participante |
| Reproducción completa | Decidir si se autoriza una corrida nueva con recibo antes del 30 de octubre | Participante |
| Reservas, capitales y disponibilidad de variables | Como propone Codex: supuestos visibles y validación pendiente | Participante |
| Documentación | Corregir README y `requirements.txt`; reordenar el README para el jurado | Antes de entregar la parte 2 |

## Anexo: procedencia

Las cifras salen de [`herramientas/revision_cruzada_claude.py`](../../../herramientas/revision_cruzada_claude.py), que escribe [`registro/revision_cruzada_claude_20261019.json`](../../../registro/revision_cruzada_claude_20261019.json) con los SHA-256 de cada fuente y sin datos por fila. Fuentes: predicciones alineadas de N48 (`Semana 1/Modelado_codex/nocturna_20261017_N01/S30_S31_review_N48/S30/aligned_predictions.parquet`), T0 de las bases actuariales D67, marcas de capital de F0, los dos CSV finales en `privado/predicciones/` y los `resumen.json` de S30 y S22. Se ejecutó en la máquina virtual Linux del participante (Python 3.10, pyarrow 25.0.1). Reglas: `docs/fuentes/revision_participante_20261019.json`. Tendencia de la prima del generador: `Preparación/DECISIONES.md`, D67.

Las ganancias de D² usan la desviación Tweedie de potencia 1,5 con la media como base, igual que el dictamen, salvo la columna marcada como base de tasa constante.
