# Por qué elegimos S30 sobre S22 y qué debe cambiar

Codex, 23 de octubre de 2026. Revisión solicitada por el participante después del cierre de parte 1. Se reconstruye la decisión con documentos y resultados anteriores al privado, y se distingue esa evidencia del resultado revelado después. No se entrenaron modelos, repitieron bootstrap ni recalibraron predicciones. Esta es una revisión propia asistida por IA, sin revisión profesional independiente.

La elección de S30 tenía una razón predictiva plausible: mejoraba ligeramente el resultado local de los dos años y el público. Lo que falló fue promover esa señal débil a una decisión definitiva sin conservar una regla común para resolver la incertidumbre. Ya sabíamos antes del cierre que su ventaja sobre S22 no era robusta. La autorización del participante decidió el archivo, pero no añadió evidencia predictiva; la responsabilidad de presentar una recomendación proporcionada a la evidencia correspondía a los asistentes.

## Qué mostraban los resultados

| Comparación | Resultado disponible | Interpretación válida |
| --- | --- | --- |
| S30 menos S22, V23 completo | +0,000161583 | Mejora puntual en un corte reutilizado para desarrollo |
| S30 menos S22, V24 completo | +0,000138041 | Mejora puntual inferior al mínimo 0,0002 del protocolo N48 |
| IC95 pareado por cliente, V24 | [−0,000082361; +0,000369479] | Compatible con pérdida o ganancia; no demuestra superioridad ni equivalencia |
| Público de S22 / S30 | 0,12988 / 0,12996 | Ventaja pública de S30 de 0,00008, sin evidencia suficiente para extrapolarla al privado |
| Influencia, conocida desde D95 | Quitar 6 de 373.831 clientes invierte la ventaja V24; uno basta en V23 | La recomendación necesitaba considerar la fragilidad del resultado |
| Privado de S22 / S30 | 0,13876 / 0,13863 | Después del cierre, S30 perdió 0,00013 frente a S22 |
| Privado de S41 | 0,13864 | Recuperó 0,00001 frente a S30; quedó 0,00012 por debajo de S22 |

Los intervalos son condicionales a las predicciones y etiquetas guardadas; no incluyen toda la selección de variantes ni incertidumbre del futuro. Los privados son los cinco decimales que devolvió Kaggle, archivados en la auditoría de los 29 envíos. Con el resto del tablero fijo, S22 habría quedado segundo y S41 quedó cuarto. Eso mide el coste retrospectivo de la elección; no prueba que pudiéramos anticipar el orden privado.

## La secuencia de decisiones

El 18 de octubre, D88 propone S30 como evolución de S22. Cambia la severidad por peligro en autos y edificios, y los pesos y la elasticidad de contenidos. La regla de la línea B exigía mejorar el resultado completo y el cuerpo de la distribución en los dos cortes, admitiendo una cesión acotada en uno de ellos. El criterio del cuerpo surgió de observar cómo seis resultados locales ordenaban los scores públicos anteriores. Estaba fijado antes de construir S30, pero ya respondía a información del público.

Ese día, el comparador N48 de Codex usó las mismas filas, etiquetas y reservas para ambos modelos. S30 no pasó el mínimo de mejora, los límites inferiores de incertidumbre ni la ausencia de deterioros por ramo y semestre. La prueba regional exacta no se hizo porque los filtros anteriores habían fallado: su ausencia no debe contarse como una prueba regional realizada y adversa. El ensayo de envío N56 se autorizó después expresamente y mantuvo escrito que S30 no se promovía como mejora clara. El archivo se envió y ganó 0,00008 en público.

D89 eligió S30 como principal por el mejor punto local y público. S22 quedó como respaldo para errores de receta o problemas de reproducción. Se reconocía que no sabíamos cuál ganaría en el privado, pero la incertidumbre predictiva no quedó incorporada como un motivo operativo para conservar o recuperar S22.

El 19 de octubre, D95 midió la fragilidad: seis clientes invertían V24 y el informe hablaba de «empate práctico». También encontró que la tendencia solo podía evaluarse en V24 y que una parte de la ventaja era un efecto indirecto de la regla de nivel. La lectura correcta es «superioridad no acreditada»; la falta de significación no demuestra equivalencia estadística.

El 20, D99 dejó S30 como definitivo y S22 como historia. El registro explica que S30 se había reconstruido y que no se habían encontrado errores en el archivo. Eso cerraba un riesgo técnico, pero no resolvía la incertidumbre predictiva frente a S22. D99 reconoce esa limitación y aun así conserva como desempate los mejores puntos local y público. Más adelante S41, S42 y S43 ajustaron S30; el último cambio S43→S41 ayudó entre esos candidatos, pero no recuperó la pérdida frente a S22.

## Los fallos del criterio

### El filtro adverso no determinó la promoción

Había dos criterios distintos: la regla de cuerpo y completo de D88, y el filtro de mejora clara de N48. No existía una única jerarquía que dijera qué hacer cuando uno aceptaba y el otro rechazaba. La autorización para ensayar se mantuvo correctamente separada de la aprobación estadística en N56, pero la decisión definitiva se apoyó luego en un desempate más débil. No fue un envío sin autorización; fue una recomendación final con menos respaldo del que exigía el filtro de mejora clara.

Un protocolo escrito antes de calcular ayuda a evitar cambios oportunistas, pero debe tener consecuencias operativas. Si el resultado adverso solo se declara y no puede impedir la promoción, el control pierde su función. Tampoco corresponde copiar todos los filtros de N48 a semana 2: exigir que 72 puntos o cada segmento sean positivos puede ser demasiado restrictivo. Hay que distinguir el contraste principal de los diagnósticos y fijar antes qué deterioros son materiales.

### Reutilizamos la validación para construir y para justificar

Pesos, forma y alternativas ya habían usado V23 y V24. La tendencia añadida por S30 no ajustaba una recta en V23 por falta de años: allí usaba el último año. Su efecto de tendencia descansaba en V24, el mismo corte consultado para elegirla. Por tanto, mejorar los dos totales no constituía dos validaciones independientes de ese mecanismo.

Los bootstrap sobre predicciones congeladas describían variación muestral condicional, no corregían todas las decisiones previas tomadas al mirar esos cortes. Este mecanismo de optimismo por selección está descrito por [Cawley y Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) y en la [documentación de validación anidada de scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). Es un riesgo identificado en nuestro procedimiento; el privado por sí solo no demuestra cuánto de la pérdida causó.

### El público influyó en la definición de «robusto»

La correlación entre el cuerpo local y seis scores públicos motivó usar el cuerpo como criterio de adopción. Esto podía servir como hipótesis, pero la misma muestra pública ayudaba a diseñar el criterio y después a preferir S30 por su pequeño máximo. El cuerpo debe ser diagnóstico de influencia y estabilidad; la métrica principal sigue incluyendo toda la distribución. Además, las versiones de cuerpo reniveladas y las contribuciones con denominador completo no son el mismo estadístico y no deben intercambiarse.

No afirmamos que la pérdida privada esté causada únicamente por sobreajuste al público. Sí consta que el desempate usó información adaptativa del público sin una comprobación posterior intacta. La variabilidad de semillas tampoco mide el ruido del reparto público/privado.

### La mejora mezclaba mecanismos diferentes

D95 descompuso la ventaja V24: aproximadamente 62 % venía de la tendencia, 34 % del cambio en la composición de la referencia de nivel y 4 % de contenidos. La regla s17 cambiaba qué componente fijaba el nivel al superar un umbral. Un cambio presentado como mejora de severidad también podía alterar ese ancla. La tendencia tenía validación limitada y la regla de nivel introducía una discontinuidad. Había que comparar cada mecanismo con el ancla fija antes de recomendar el conjunto.

Reproducir el CSV no resuelve ese problema: confirma qué calculamos, no que debamos preferirlo. El resultado de D97 no era evidencia nueva de superioridad predictiva.

### El respaldo dejó de representar el riesgo predictivo

En D89, S22 servía para recuperar la entrega si S30 tenía un error técnico. En D99 se retiró tras reconstruir S30. Faltó conservarlo como referencia competitiva hasta el cierre, con una fila propia en la decisión final y una regla de desempate fijada antes de ver los scores. Debíamos distinguir «archivo reproducible», «alternativa técnicamente válida» y «alternativa con mejor evidencia predictiva».

## Lo que debemos hacer en semana 2

La adenda [Protocolo de selección para semana 2](semana2/PROTOCOLO_SELECCION.md) convierte esta revisión en un procedimiento propuesto. La base ya tiene folds agrupados dentro de 2023, un contraste 2023→2024 y pruebas de clientes y direcciones ausentes del ajuste. No hace falta reconstruir esas particiones ni entrenar para documentar el cambio.

| Cambio | Consecuencia concreta |
| --- | --- |
| Una sola regla para promover modelos | Una excepción para investigar o enviar no cambia el candidato principal |
| Mantener una referencia vigente | Si no hay mejora suficiente, se conserva; no se reemplaza por unas diezmilésimas públicas |
| Separar desarrollo y confirmación | Elegir pesos, calibración e hiperparámetros dentro de 2023; abrir 2024 para una lista corta y congelada |
| Contar cada consulta al bloque de confirmación | Si se vuelve a desarrollar mirando 2024, ese bloque deja de describirse como confirmación intacta |
| Representar población nueva | Evaluar clientes/direcciones ausentes del ajuste y distinguir renovación; el test emergente tiene mucho más negocio nuevo |
| Fijar ancla y cambiar una pieza cada vez | Medir por separado forma, nivel, reservas y transferencia; evitar saltos implícitos como s17 |
| Calibración subordinada a evidencia fuera del marcador | No transferir factores D100 ni el −10 % de la sonda ganadora al mercado emergente |
| Un acta final con todos los candidatos vigentes | Incluir la referencia, variantes y alternativas descartadas con el motivo; no comparar solo los últimos envíos |

La tolerancia de mejora y los límites de deterioro de semana 2 deben fijarse con la escala y la incertidumbre de su referencia, antes de ver ganancias de candidatos. El 0,0002 de N48, el piso de semillas y el 1 % de reservas no son intercambiables ni límites oficiales del concurso. Cuando no podamos distinguir candidatos con la evidencia disponible, la regla propuesta conserva la referencia, por prudencia y estabilidad de procedimiento; no garantiza que vaya a ganar en el privado.

El test emergente tiene cerca de 76 % de filas de clientes nuevos para su ramo, frente a alrededor del 15,3 % en 2024, según la preparación existente. Un buen resultado dominado por renovaciones no basta para adoptar transferencia. Cualquier ponderación para aproximar esa composición debe fijarse con covariables y comprobar solapamiento; no se promedian los D² de los subgrupos como si fueran el D² global.

## Alcance de la conclusión

El fallo comprobable es que elegimos con evidencia débil y controles que no gobernaron de manera uniforme la promoción. Era evitable recomendar esa elección con demasiada confianza. No es demostrable que cualquier regla conservadora hubiera encontrado siempre al mejor modelo ni que S22 fuera superior en la población completa.

La sonda S40_01 obtuvo el mejor privado, pero no autoriza a adoptar su reducción de autos como explicación verdadera ni como regla de semana 2. De igual modo, no se traslada S22 sin adaptar variables, mercado, maduración de siniestros y nivel. La revisión aporta controles de decisión, no una receta ganadora obtenida después de conocer las respuestas.

Las prácticas IAA priorizadas por el proyecto respaldan documentar límites, cambio y responsabilidad humana: Consideraciones profesionales §3.3; Gobernanza §2.8 y §§3.4–3.6; Documentación §3. Son guías educativas, no una certificación de esta revisión.

## Evidencia local

- Comparador previo: `Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01/S30_S31_review_N48/plan.json` y `S30/result.json`; este último registra explícitamente `passes_statistical_gate: false`.
- Ensayo autorizado: `verification/N56_human_authorization.md` y `S30_trial_N56/forum_result.md`, bajo la misma raíz N01.
- Propuesta D88: `Hackaton/Semana 1/Modelos_claude_b/foro/D88_DECISIONES.md`; D89 y D99 en la memoria de decisiones de Preparación.
- Sensibilidad anterior al cierre: [SENSIBILIDAD_S30_S22.md](SENSIBILIDAD_S30_S22.md) y sus resultados E01/E08 archivados en la corrida `sens_20261019T212700Z_b9e7aa92`.
- Elección definitiva: [decision_modelo_definitivo_20261020.json](../registro/decision_modelo_definitivo_20261020.json).
- Privados verificados: [auditoria_29_envios_privados_20261023.json](../registro/auditoria_29_envios_privados_20261023.json).
- Preparación emergente: [PREPARACION_BASE.md](semana2/PREPARACION_BASE.md) y [semana2_preparacion_plan.json](../registro/semana2_preparacion_plan.json).

El registro de esta revisión conserva las huellas de las fuentes y los cálculos aritméticos. No modifica decisiones, comentarios o corridas históricos ni comunica resultados a terceros.
