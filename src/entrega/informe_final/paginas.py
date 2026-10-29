"""Informe final, edición 28 de octubre de 2026. Voz de Manuel Rodríguez.
Codex: metodología y elección, salvaguarda explicada y limitaciones observadas.
Diagramas nativos adaptados del panel histórico; cifras y F3c intactos."""

RUNHEAD = 'AI Hackathon IAA 2026 · Informe final, partes 1 y 2'

P1 = """
<h1>Prima de riesgo asistida por IA en dos mercados</h1>
<p class="sub">Construcción y adaptación de modelos de prima de riesgo para autos, edificios y contenidos, con apoyo de IA y una separación explícita entre validación histórica y calibración con el tablero público</p>
<p class="byline">AI Hackathon IAA 2026 · Partes 1 y 2 · Manuel Rodríguez, equipo individual (Kaggle: manoloriveros) · Edición del 28 de octubre de 2026 · Datos sintéticos; importes en la unidad ficticia CU</p>

<h2>Qué conseguí y con qué evidencia</h2>
<p class="lead">El reto pidió estimar, para cada periodo de póliza de 2025 en autos, edificios y contenidos del hogar, el coste último esperado de los siniestros: la prima de riesgo, antes de gastos y márgenes, medida con el D² Tweedie de potencia 1,5. La semana 1 trajo un mercado con cuatro años de historia. La semana 2, un mercado emergente con dos años de datos y una cartera de 2025 en la que el 76 % de las pólizas es negocio nuevo, porque la aseguradora compró el bloque de un corredor.</p>

<div class="kpis kpis3">
 <div class="kpi"><div class="v">0,13864</div><div class="l">D² privado de la parte 1. Cuarto puesto entre 54 equipos.</div></div>
 <div class="kpi"><div class="v">0,16914</div><div class="l">D² público de la parte 2 al 26 de octubre. El resultado privado sigue pendiente.</div></div>
 <div class="kpi"><div class="v">0,121 frente a 0,083</div><div class="l">D² en validación cruzada por cliente sobre 2023: modelo transferido frente al mejor modelo entrenado solo en el emergente.</div></div>
</div>

<p>En el mercado establecido combiné modelos de coste total con modelos de frecuencia y severidad por peligro. En el emergente reutilicé un modelo entrenado con las variables comunes de los dos mercados y ajusté componentes con la experiencia local; la comparación sobre 2023 favoreció la transferencia frente a entrenar solo con los dos años del emergente (página 3). El resultado final también depende de las sondas que envié a Kaggle, que aportaron información sobre el nivel de 2025 ausente en los datos históricos. Por eso separo el desempeño del modelo, la mejora obtenida con el tablero y las limitaciones de trasladar el proceso a una aseguradora.</p>

<div class="flow">
 <div></div>
 <div class="st">1. Definir<span>objetivo y métrica</span></div>
 <div class="st">2. Validar datos<span>antes de usarlos</span></div>
 <div class="st">3. Coste último<span>siniestros no reportados</span></div>
 <div class="st">4. Modelo<span>estructura del riesgo</span></div>
 <div class="st">5. Nivel de 2025<span>con credibilidad</span></div>
 <div class="st">6. Validar y gobernar<span>antes y después</span></div>
 <div class="rl">Semana 1<br><span class="small">establecido</span></div>
 <div class="c1">Contrato escrito: qué se predice y cómo se mide</div>
 <div class="c1">58 controles; ocho reglas reversibles</div>
 <div class="c1">Retraso de reporte por peligro, en la exposición</div>
 <div class="c1">Mezcla por peligro: coste total y frecuencia × severidad</div>
 <div class="c1">Sondas por ramo y regla de credibilidad</div>
 <div class="c1">12 experimentos preinscritos; reconstrucción desde originales</div>
 <div class="rl">Semana 2<br><span class="small">emergente</span></div>
 <div class="c2">Mismas definiciones; prima comercial de 20 pólizas</div>
 <div class="c2">74 controles nuevos; 12 hallazgos</div>
 <div class="c2">Curva del desarrollado, contrastada en 2023</div>
 <div class="c2">Modelo transferido más factores propios</div>
 <div class="c2">Sondas global y por celda; sin tablero, experiencia del corredor</div>
 <div class="c2">Sensibilidad, reservas y revisiones cruzadas con IA</div>
</div>
<p class="cap"><b>Figura 1.</b> El mismo flujo en los dos mercados. La etapa 5 es la única que calibró con el tablero público; dos decisiones de estructura de la etapa 4 también usaron su respuesta (página 3).</p>

<p>Con Claude y Codex conecté preparación de datos, modelado, validación y comunicación en un flujo actuarial. Sus revisiones detectaron errores que cambiaron cálculos y decisiones (página 4). La traducción y los tableros ampliaron el apoyo de la IA. Mis autorizaciones quedaron registradas; las verificaciones entre asistentes no son revisión profesional independiente.</p>

<div class="gloss">
 <div><b>Sonda</b> Envío de prueba con las predicciones de un grupo multiplicadas por un factor conocido; su puntuación revela el nivel que prefiere el tablero.</div>
 <div><b>Celda y forma</b> Celda: combinación de ramo y tipo de negocio (nuevo o renovación), seis en total. Forma: exponente que estira o comprime las diferencias dentro de una celda.</div>
 <div><b>Credibilidad</b> Peso que recibe una señal con ruido frente a lo que ya se sabía; crece con los datos y baja con el ruido.</div>
 <div><b>Fuera de tiempo</b> Ajustar con un año y medir en otro posterior. El corte temporal no prueba que todos los atributos estuvieran disponibles al cotizar.</div>
 <div><b>Tablero público</b> Puntuación de Kaggle sobre una parte del test; el privado da la evaluación cuantitativa final. El jurado valora además método, adaptación, IA y controles.</div>
</div>

<h3>Qué decido y bajo qué límites</h3>
<p>El 28 de octubre confirmé F3c como modelo definitivo de la parte 2, conservando el CSV ya enviado y priorizando la robustez para el privado. Completé la alternativa regularizada F3c-R en 26 ámbitos: su D² local fue 0,126662 frente a 0,126806 de F3c. Mejoró el agregado de negocio nuevo, pero no superó los criterios de estabilidad, segmentos e influencia; no justifica sustituir F3c. Conservo las alternativas y los resultados adversos. La decisión es mía; 2024 sigue siendo desarrollo adaptativo y no acredita superioridad privada, revisión profesional independiente ni aprobación de una tarifa operativa. La página 4 conserva las limitaciones de los contrastes anteriores.</p>
"""

P2 = """
<h2>Las definiciones antes que el modelo</h2>
<p>Antes de entrenar escribí qué se predice, cómo se mide, con qué información y cómo se valida.</p>
<div class="defs">
 <div class="def"><h4>Objetivo</h4><p>Para cada fila del test, la suma del coste último de los siniestros del periodo, neta de franquicia y recobros, sin rechazados e incluido lo no reportado aún. Se predice el total del periodo, sin anualizar.</p></div>
 <div class="def"><h4>Métrica</h4><p>El D² Tweedie compara la desviación del modelo con la de cobrar a todos el coste medio. Con potencia 1,5 castiga menos que un error cuadrático los siniestros enormes; la fórmula por fila está en el anexo B.</p></div>
 <div class="def"><h4>Información al cotizar</h4><p>Excluí los contactos con atención al cliente (delatan el siniestro del periodo), la decisión de renovación y el clima observado de 2025. Traté las tablas maestras sin fecha como conocidas al cotizar; es un supuesto: los archivos no permiten reconstruir el estado histórico de todos sus campos.</p></div>
 <div class="def"><h4>Validación</h4><p>Las comparaciones temporales ajustan con años anteriores y miden sobre un año posterior; las pruebas en sentido inverso examinan la estabilidad entre años. Documento aparte la calibración con el tablero público, porque incorpora información adicional del test de 2025.</p></div>
</div>
<div class="box"><h4>Una consecuencia de la métrica que guió todo el proyecto</h4>
<p>El factor que, multiplicado por todas las predicciones de un grupo, minimiza la desviación Tweedie 1,5 es</p>
<math display="block"><msup><mi>k</mi><mo>*</mo></msup><mo>=</mo><mfrac><mrow><mo>∑</mo><mo stretchy="false">(</mo><mi>y</mi><mo>/</mo><msqrt><mi>μ</mi></msqrt><mo stretchy="false">)</mo></mrow><mrow><mo>∑</mo><msqrt><mi>μ</mi></msqrt></mrow></mfrac></math>
<p>Optimiza la desviación para unas predicciones dadas y puede diferir del cociente entre costes y predicciones totales. Con él fijé los niveles por ramo y por celda. Las revisiones cruzadas con IA detectaron un script que lo elevaba al cuadrado; lo corregí antes del envío.</p></div>

<h2>Datos: lo que corregí y lo que quedó como incertidumbre</h2>
<p>Conservé los originales intactos (huella SHA-256) y cada corrección vive en una capa derivada y reversible. Un segundo asistente recalculó las reglas de la semana 1 con código propio (41 de 41 comprobaciones), y en la semana 2 rehice la validación con 74 controles nuevos.</p>
<table class="tight">
 <tr><th style="width:7%">Semana</th><th style="width:40%">Hallazgo</th><th class="r" style="width:13%">Filas</th><th>Tratamiento</th></tr>
 <tr><td>1</td><td>Identificadores de cliente de autos sin ceros iniciales</td><td class="r">123.664</td><td>Relleno a ocho dígitos; recupera el cruce con el maestro</td></tr>
 <tr><td>1 y 2</td><td>Exposición guardada en días o en base 360</td><td class="r">14.229 y 609</td><td>Días cubiertos entre 365, la convención de 2025</td></tr>
 <tr><td>1 y 2</td><td>Capitales asegurados unas mil veces mayores</td><td class="r">3.527 y 349</td><td>División entre mil si la historia o una prueba de prima lo respalda; 149 casos quedan como incertidumbre</td></tr>
 <tr><td>2</td><td>Ocupación escrita de 80 formas para 20 categorías; marca y modelo con 300 niveles sin coherencia física</td><td class="r">toda la tabla</td><td>Unificación de la ocupación; marca y modelo fuera del boosting</td></tr>
</table>

<div class="cols-6535">
<div>
<h3>Del coste observado al coste último</h3>
<p>Los siniestros están valorados al cierre de 2024: el incurrido observado incluye reservas de caso y excluye lo aún no reportado. Ese objetivo observado (T0) no es el coste último. Para el retraso de reporte reduje la exposición de entrenamiento según la proporción reportada de cada peligro (56 % en lesiones corporales de 2024). En semana 1 usé curvas de conteos (figura 2): trasladarlas al coste supone igual severidad media en tardíos y reportados. En las bases emergentes revisadas, una base usa curvas de coste del desarrollado y otra las estima con ambos mercados, excluyendo cada ámbito retenido antes de aprender. Su traslado conserva supuestos de desarrollo y composición.</p>
<p>En la cohorte emergente de 2023, el coste tardío observado de lesiones corporales superó un 42,7 % al previsto (IC90: +2 % a +102 %). Mantengo esa alarma y los fallos del backtest de conteos. La aparente amortiguación con sondas del análisis anterior recalculaba óptimos públicos: es un contrafactual, no absorción comprobada por F3c congelado. Una sola valoración no acredita coste último ni suficiencia de reservas de caso, el 28,1 % del coste observado de 2024. Los escenarios nuevos siguen siendo condicionales (página 4).</p>
</div>
<div>
{{FIG:completitud}}
<p class="cap"><b>Figura 2.</b> Proporción estimada de siniestros reportados al cierre de 2024 por peligro (semana 1, chain-ladder de conteos), usada como exposición efectiva; no dice qué parte del coste estaba reportada.</p>
</div>
</div>
"""

P3 = """
<h2>Semana 1: un modelo por peligro</h2>
<p>Combiné por ramo diez componentes de coste total y de frecuencia por severidad. Los árboles LightGBM y CatBoost con objetivo Tweedie admiten ceros y costes positivos y captan interacciones; separar frecuencia y severidad por causa distingue mecanismos como incendio y fuga de agua. Ningún modelo dominaba en todos los ramos. Acoté la tendencia a ±15 % anual; aportó +0,000086 de D² en 2024. La mezcla alcanzó 0,138 frente a 0,071 de una tasa por ramo; la entrega calibrada, 0,13864 en el privado, cuarta entre 54 equipos. Durante la semana 1 hubo envíos en primer puesto público. Dos excepciones usaron el tablero: descarté la mezcla robusta y admití factores propios por una regla pública predeclarada.</p>
{{FIG:esquema_modelo}}
<h2>Semana 2: por qué elegí transferencia</h2>
<p>El emergente tenía dos años y 209.063 periodos que predecir; el negocio nuevo pasó del 14 % histórico al 76 % en 2025. Preferí transferir relaciones del mercado con más historia usando variables comunes, en vez de aprender todo desde cero con experiencia escasa. Combiné predicciones transferidas y ajustes locales con credibilidad limitada donde había poca información. La apertura registrada de 2024 dio +0,049 de D² sobre la tasa por ramo (banda por seis comparaciones: +0,027 a +0,073). Otra línea obtuvo 0,125 frente a 0,099 del mejor modelo solo local. Falló la salvaguarda de negocio nuevo y la modifiqué tras conocer el resultado. Después reutilicé 2024 para factores y mezcla: conserva carácter adaptativo.</p>
<h3>Qué aportó el tablero y qué respalda la nueva validación</h3>
<div class="cols"><div>
{{FIG:escalera_2023}}
<p class="cap"><b>Figura 3.</b> Comparación histórica en 2023 por cliente, anterior a corregir toda la cadena. No es el contraste protegido del 27 de octubre.</p>
<p>De la mezcla inicial a F3c, el público pasó de 0,15390 a 0,16914: los pasos de calibración sumaron 0,01044 y los del modelo, 0,00480. El reparto depende del orden y de sus interacciones.</p>
<p>Sin calibración ni exponentes públicos, el contrafactual histórico estima 0,15821; con el nivel de la tarifa histórica, 0,16376 (28 % y 65 % de la ganancia). Supone trasladar la respuesta al nivel de la mezcla inicial: no son envíos observados ni la validación nueva.</p>
</div><div>
{{FIG:escalera_publico}}
<p class="cap"><b>Figura 4.</b> Resultados públicos observados. Gris: calibración; azul: modelo. Franja clara: previsión anterior al envío.</p>
<p>F3c supera +0,00395 en el público a la entrega sin factores. La nueva comparación reaprende la receta con 2023 y evalúa 59.202 filas de 2024, sin niveles ni exponentes públicos. La referencia conserva los ajustes por siniestralidad y bonificación y la transformación común de autos renovación: retiro solo el bloque propio.</p>
<p>Completitud, categorías, grupos cliente–dirección, selección interna, árboles y ajustes excluyen el ámbito retenido. Las pruebas adversas de año y fold conservan modelos y precios. Es protección computacional; no demuestra disponibilidad al cotizar.</p>
</div></div>
<table class="tight">
<tr><th>Base protegida</th><th>D² sin / con factores</th><th>ΔD² global</th><th>Banda condicional, familia 6</th></tr>
<tr><td>Curva del desarrollado</td><td>0,12332 / 0,12566</td><td>+0,00233</td><td>[+0,00058; +0,00425]</td></tr>
<tr><td>Curva de ambos mercados</td><td>0,12092 / 0,12335</td><td>+0,00243</td><td>[+0,00072; +0,00429]</td></tr>
<tr><td>Mezcla fija 50/50</td><td>0,12353 / 0,12590</td><td>+0,00237</td><td>[+0,00066; +0,00423]</td></tr>
</table>
<p class="cap">Valores redondeados; precisión completa en el registro. Bandas al 99,17 % por contraste, familia de seis; 10.000 réplicas por grupos condicionadas a modelos aprendidos: no repiten aprendizaje ni búsqueda histórica. Las tres bases comparten etiquetas, sin confirmación independiente. La receta de curva combinada evalúa una semilla y menos variables; no valida la configuración íntegra de producción de tres semillas.</p>
<p>El límite inferior supera +0,0005 en las tres bases. Renovación explica el 98,09–99,39 % del aporte. Con composición de 2025, la mezcla mejora +0,00099 (IC95: −0,00290 a +0,00476); las tres bandas cruzan cero. No acredito mejora futura ni estabilidad del negocio nuevo.</p>
<div class="box"><h4>Cómo fijaría el nivel sin tablero</h4>
<p>El tablero pidió subir el nivel global un 22 %. La tarifa histórica apuntaba a +13 %, pero varía entre años y empeoró su backtest. La experiencia comparable del bloque del corredor no queda identificada por esos escenarios. Las sondas informan del test del concurso, sin acreditar una tarifa aplicable fuera de él.</p></div>
"""

P4 = """
<h2>La IA como herramienta del actuario</h2>
<p>Usé IA para modelar, programar y diseñar contrastes; los tableros apoyaron la revisión. Preparé traducciones, guiones y materiales audiovisuales, incluida la narración en inglés cotejada con la española. Otros textos y láminas conservan sus fechas. Busqué reducir barreras de idioma y tareas de presentación; no medí ahorro de tiempo. La comprobación entre asistentes no es revisión profesional independiente.</p>
{{FIG:flujo_ia}}
<p class="cap"><b>Figura 5.</b> Flujo adaptado del panel construido con IA. La revisión entre asistentes es propia; mi autorización no acredita todos los supuestos.</p>
<table class="tight">
<tr><th style="width:43%">Error o límite detectado</th><th style="width:22%">Comprobación</th><th>Consecuencia</th></tr>
<tr><td>Preparación y completitud usaban información fuera del ámbito permitido</td><td>Auditoría de la cadena</td><td>Rehice preparación y ajuste por ámbito</td></tr>
<tr><td>Una réplica incompleta se daba por válida</td><td>Revisión integral</td><td>Controles reescritos; 45 pruebas, 35 adversas</td></tr>
<tr><td>Ruido público medido contra todo el test</td><td>Batería de sensibilidad</td><td>Cambió la selección; mejoró el privado frente a la variante contrastada</td></tr>
<tr><td>Un nulo de pocos niveles validaba variables falsas</td><td>Revisor de factores</td><td>Retiré aseguradora previa y ocupación</td></tr>
</table>
<h3>La salvaguarda y el significado de su excepción</h3>
<p>Una salvaguarda es una condición de aceptación fijada antes de comparar. Exigí una diferencia no negativa en negocio nuevo y límite inferior IC95 ≥ −0,001. La transferencia dio +0,013, pero el límite fue −0,011: falló. Tras verlo, autoricé aceptar la mejora puntual sin aquel veto del intervalo. Levantar esa exigencia fue una excepción de decisión; no acreditó protección del segmento. Fijé además materialidad del 1 % por ramo y gasto fijo completo de 85 CU por póliza.</p>
<table class="tight">
<tr><th>Factores, receta protegida</th><th>Negocio nuevo: Δ / IC95</th><th>Δ autos nuevo</th><th>Δ al retirar 37 grupos favorables</th></tr>
<tr><td>Curva del desarrollado</td><td>+0,00011<br>[−0,00370; +0,00398]</td><td>−0,00122</td><td>−0,00001</td></tr>
<tr><td>Curva de ambos mercados</td><td>+0,00037<br>[−0,00300; +0,00392]</td><td>−0,00088</td><td>+0,00013</td></tr>
<tr><td>Mezcla 50/50</td><td>+0,00027<br>[−0,00327; +0,00393]</td><td>−0,00103</td><td>+0,00006</td></tr>
</table>
<p class="cap">Protección: Δ de negocio nuevo ≥ 0 y límite inferior IC95 ≥ −0,001; la protección falla en las tres bases por el límite inferior. El piso puntual de autos nuevo es −0,001: solo la curva de ambos mercados lo cumple, sin acreditar estabilidad entre años. La ganancia se anula retirando retrospectivamente 37, 42 y 39 de 36.408 grupos, respectivamente. Negocio nuevo significa primer año de póliza, no dirección nunca vista. Los umbrales son del proyecto; la IAA no fija estos valores.</p>
<h3>Sensibilidad y reproducción: qué queda comprobado</h3>
<p>Los 50 escenarios (45 de coste/reservas/cola y cinco de completitud) mantienen Δ global positivo en las tres bases, con precios fijos y con la capa destino reaprendida solo en 2023. En esta última, el peor Δ es +0,00218, +0,00224 y +0,00220. Los árboles y curvas fuente quedan congelados por ámbito: el alcance no incluye reaprenderlos bajo cada tensión. Son escenarios deterministas, no probabilidades, intervalos ni prueba de suficiencia de reservas o del beneficio del 8 %.</p>



<h3>Limitaciones observadas y alcance de las conclusiones</h3>
<table class="tight">
<tr><th style="width:26%">Evidencia o límite</th><th style="width:33%">Lectura que sostengo</th><th>Alcance</th></tr>
<tr><td>Negocio nuevo sin protección; ganancia concentrada.</td><td>La mejora global se apoya sobre todo en renovación.</td><td>No demuestra estabilidad en negocio nuevo ni mejora futura de la cartera.</td></tr>
<tr><td>Receta histórica comparada distinta de producción íntegra.</td><td>El aislamiento se acredita en esas recetas de comparación.</td><td>No extiendo ese cierre a toda la configuración entregada.</td></tr>
<tr><td>Atributos sin versión histórica fechada.</td><td>El corte temporal no prueba disponibilidad al cotizar.</td><td>Maestros, clima y duración observada conservan ese supuesto.</td></tr>
<tr><td>Una valoración; fuente congelada en escenarios.</td><td>Sensibilidad condicional, con diferencia global positiva.</td><td>No prueba coste último, reservas suficientes ni suficiencia del 8 %.</td></tr>
<tr><td>Reproducción y revisión propias con IA.</td><td>La coincidencia de archivos acredita reconstrucción técnica.</td><td>No es revisión profesional independiente ni aprobación operativa.</td></tr>
</table>
<p class="cap">La continuidad de F3c en el concurso no convierte estas limitaciones en controles satisfechos. Las condiciones documentadas tampoco equivalen a bloqueos automáticos o contingencias probadas.</p>
"""

P5 = """
<h2>Prima comercial de las 20 pólizas de referencia</h2>
<div class="cols-6535">
<div>
<p>Calculé la prima comercial de las veinte pólizas desde la prima de riesgo de la entrega F3c y los supuestos de gastos del archivo del emergente. Sumo el reaseguro catastrófico de hogar (12 % de la prima de riesgo) y el gasto fijo; los porcentajes sobre prima (gasto variable 15 %, comisión, impuesto 8 % y margen 8 %) entran por el denominador. Cobro completo el gasto fijo, 85 CU por póliza en el archivo; el prorrateo por exposición (85·e) de la versión anterior daría 20.304,23 CU en vez de 20.800,02 y lo conservo como alternativa.</p>
</div>
<div class="box" style="margin-top:0">
<math display="block"><mi>P</mi><mo>=</mo><mfrac><mrow><mi>R</mi><mo>+</mo><mn>0,12</mn><mo>·</mo><msub><mi>R</mi><mtext>hogar</mtext></msub><mo>+</mo><mn>85</mn></mrow><mrow><mn>1</mn><mo>−</mo><mn>0,15</mn><mo>−</mo><mi>c</mi><mo>−</mo><mn>0,08</mn><mo>−</mo><mn>0,08</mn></mrow></mfrac></math>
<p class="small">Comisión c = 0,20 con corredor y 0 en venta directa; el denominador vale 0,49 o 0,69. Ejemplo, C00302985 (contenidos, corredor): (54,08 + 6,49 + 85) / 0,49 = 297,08 CU.</p>
</div>
</div>
{{TABLA:primas}}
<p class="cap">Importes del periodo en CU; el cociente divide la prima comercial completa, incluidos los 85 CU fijos, por la exposición exacta, por eso crece en las pólizas cortas. Cálculo: fuente/prima_comercial_20ref.py.</p>
<p>Las veinte primas suman 20.800,02 CU. El cociente anualizado agregado de 3,63 no se extrapola a la cartera ni es una subida recomendada: anualiza también el gasto fijo de pólizas cortas. La siniestralidad estimada a coste último de 2023–2024 fue 0,85 por CU de prima devengada (edificios: 1,17), frente a recargos proporcionales del 51 % con corredor. Separado el gasto fijo, el riesgo anualizado con catástrofe equivale a 1,40 veces la prima escrita. Revisar precio, comisión y aumentos exige analizar retención y condiciones comparables.</p>

<h2>Limitaciones e incertidumbre que queda</h2>
<p>La prima comercial hereda la incertidumbre del riesgo calibrado con sondas. El beneficio del 8 % procede del archivo de gastos: no prueba suficiencia. Aunque la comparación histórica está protegida, 2024 ya es adaptativo, la protección de negocio nuevo falla y las bandas con composición de 2025 cruzan cero. La configuración histórica evaluada no equivale a toda la producción. La estabilidad entre años, el escaso soporte de negocio nuevo de hogar y la severidad tardía limitan la generalización. Los maestros sin fecha, la versión del clima y la duración observada no reconstruyen toda la información conocida al cotizar; duración realizada e inicialmente contratada son conceptos distintos. Las comprobaciones son propias con IA y no constituyen revisión profesional independiente ni aprobación operativa.</p>
<p>La reejecución desde originales recuperó los CSV históricos: semana 1, 436 estimadores; semana 2, 57 etapas y 87 modelos, con diferencias internas y dos restauraciones documentadas. La nueva revisión no regenera F3c ni predice 2025. Reconstruir archivos no añade validación predictiva; los intervalos no repiten aprendizaje ni búsqueda histórica.</p>
<div class="box"><h4>Estado al 28 de octubre</h4>
<p>La entrega de la parte 1 obtuvo 0,13864 en el privado. El 28 de octubre confirmé F3c como definitivo de la parte 2, con su archivo y predicciones intactos. Su D² público de 0,16914 no acredita desempeño privado. F3c-R queda documentado como alternativa que no superó los criterios registrados. Esta elección expresa del participante cierra la selección del modelo para la entrega; no cambia esos criterios ni acredita una promoción estadística. No hice otro envío.</p></div>
"""
