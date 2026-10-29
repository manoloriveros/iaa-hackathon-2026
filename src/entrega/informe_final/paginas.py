"""Informe técnico, edición 29 de octubre de 2026.
Revisión editorial de Codex según comentarios del participante; modelo y cifras preservados.
"""

RUNHEAD = 'AI Hackathon IAA 2026 · Informe final, partes 1 y 2'

P1 = """
<h1>Modelización de la prima de riesgo en dos mercados con apoyo de IA</h1>
<p class="sub">De la experiencia de siniestros a la tarifa: modelos por peligro, transferencia de aprendizaje y validación actuarial</p>
<p class="byline">AI Hackathon IAA 2026 · Partes 1 y 2 · Manuel Rodríguez (Kaggle: manoloriveros) · Edición del 29 de octubre de 2026 · Datos sintéticos; importes en CU</p>
<h2>Problema actuarial y enfoque de solución</h2>
<p class="lead">Me propuse estimar el coste último esperado de los siniestros de cada periodo de póliza de 2025 en autos, edificios y contenidos del hogar, antes de gastos y márgenes. El mercado establecido ofrecía cuatro años de historia. El emergente, solo dos y un cambio fuerte de composición: el negocio nuevo pasaba del 14 % histórico al 76 % de la cartera de 2025 tras la adquisición del bloque de un corredor. La solución debía combinar señal predictiva, tratamiento del desarrollo de siniestros y estabilidad ante ese cambio.</p>
<div class="kpis kpis3">
 <div class="kpi"><div class="v">0,13864</div><div class="l">D² privado de la parte 1. Cuarto puesto entre 54 equipos.</div></div>
 <div class="kpi"><div class="v">0,16914</div><div class="l">D² público de F3c, modelo definitivo de la parte 2. Resultado privado pendiente.</div></div>
 <div class="kpi"><div class="v">0,121 frente a 0,083</div><div class="l">Contraste histórico por cliente en 2023: modelo transferido frente al mejor modelo solo local.</div></div>
</div>
<p>En el mercado establecido combiné coste total Tweedie con frecuencia × severidad por peligro. Esta descomposición permite recoger mecanismos distintos, como incendio, fuga de agua y lesiones corporales, y combinar componentes que no rinden igual en todos los ramos. Para el emergente transferí relaciones aprendidas con variables comunes y añadí ajustes locales con credibilidad. Así aproveché la historia disponible sin exigir que una muestra pequeña estime toda la estructura desde cero.</p>
<div class="flow">
 <div></div>
 <div class="st">1. Definir<span>objetivo y métrica</span></div>
 <div class="st">2. Validar datos<span>antes de usarlos</span></div>
 <div class="st">3. Coste último<span>siniestros no reportados</span></div>
 <div class="st">4. Modelo<span>estructura del riesgo</span></div>
 <div class="st">5. Nivel de 2025<span>con credibilidad</span></div>
 <div class="st">6. Contrastar<span>estabilidad y reproducción</span></div>
 <div class="rl">Semana 1<br><span class="small">establecido</span></div>
 <div class="c1">Contrato escrito: qué se predice y cómo se mide</div>
 <div class="c1">58 controles; ocho reglas reversibles</div>
 <div class="c1">Retraso de reporte por peligro, en la exposición</div>
 <div class="c1">Mezcla por peligro: coste total y frecuencia × severidad</div>
 <div class="c1">Calibración por ramo con credibilidad</div>
 <div class="c1">12 experimentos preinscritos; reconstrucción desde originales</div>
 <div class="rl">Semana 2<br><span class="small">emergente</span></div>
 <div class="c2">Mismas definiciones; prima comercial de 20 pólizas</div>
 <div class="c2">74 controles nuevos; 12 hallazgos</div>
 <div class="c2">Curva del desarrollado, contrastada en 2023</div>
 <div class="c2">Modelo transferido más factores propios</div>
 <div class="c2">Nivel global y por celda, con credibilidad</div>
 <div class="c2">Sensibilidad, reservas y revisiones cruzadas con IA</div>
</div>
<p class="cap"><b>Figura 1.</b> Cadena de estimación común y adaptación al mercado emergente. La calibración incorpora información del tablero público; su alcance se distingue de la validación histórica.</p>
<h3>Decisiones que dieron forma al modelo</h3>
<p>Concilié la exposición antes de estimar tasas e incorporé el retraso de reporte por peligro, contrastado con cohortes observadas. Excluí variables capaces de revelar el siniestro del periodo. Comparé la transferencia con modelos locales y revisé los ajustes por ramo y tipo de negocio. Calibré el nivel final mediante variaciones multiplicativas controladas y la respuesta analítica de la métrica, moderada por credibilidad. Esta etapa usa información del tablero de 2025 y se evalúa separadamente del ajuste histórico.</p>
<h3>Validación orientada a la cartera futura</h3>
<p>Organicé la revisión con particiones por cliente y dirección, contrastes temporales, pruebas adversas de fuga, sensibilidad de reservas e influencia de grupos. La ganancia agregada de los factores se concentra en renovaciones; su traslado al negocio nuevo conserva incertidumbre. La alternativa regularizada F3c-R también se evaluó con el flujo completo y no aportó estabilidad suficiente para sustituir F3c (página 4). Conservo F3c y sus predicciones originales como solución final.</p>
<p>Fijé ΔD² de negocio nuevo ≥ 0 y límite inferior IC95 ≥ −0,001. La transferencia dio +0,013, con límite −0,011: falló. Acepté la mejora puntual tras modificar el veto; eso no demuestra protección del segmento.</p>
<p>Claude y Codex apoyaron la construcción de código y el diseño de contrastes. Bajo mi seguimiento continuo, se revisaron resultados con distintos modelos y agentes, se recalcularon controles con implementaciones separadas y se corrigieron fallos de datos, fórmulas y aislamiento. Ese trabajo permitió sostener una revisión iterativa dentro del plazo del concurso. Las páginas siguientes presentan el método y la evidencia que respalda cada decisión.</p>
"""

P2 = """
<h2>Objetivo de estimación y diseño de los datos</h2>
<p>Modelo el coste total del periodo, neto de franquicia y recobros, sin siniestros rechazados e incluido el coste aún no reportado. La exposición se expresa en días cubiertos / 365. La evaluación usa D² Tweedie con potencia 1,5; las predicciones entregadas corresponden al periodo completo, sin anualizar.</p>
<p>Para reducir fuga excluí contactos con atención al cliente, decisión de renovación y clima observado de 2025. Traté los maestros sin fecha como disponibles al cotizar, supuesto que los archivos no permiten comprobar para todos sus campos. La validación separa años y grupos de cliente–dirección; los contrastes inversos examinan estabilidad, mientras la calibración pública incorpora información adicional de 2025.</p>
<div class="box"><h4>Una consecuencia de la métrica que guió todo el proyecto</h4>
<p>El factor que, multiplicado por todas las predicciones de un grupo, minimiza la desviación Tweedie 1,5 es</p>
<math display="block"><msup><mi>k</mi><mo>*</mo></msup><mo>=</mo><mfrac><mrow><mo>∑</mo><mo stretchy="false">(</mo><mi>y</mi><mo>/</mo><msqrt><mi>μ</mi></msqrt><mo stretchy="false">)</mo></mrow><mrow><mo>∑</mo><msqrt><mi>μ</mi></msqrt></mrow></mfrac></math>
<p>Optimiza la desviación para unas predicciones dadas y puede diferir del cociente entre costes y predicciones totales. Lo apliqué por ramo y por celda. El recálculo con una implementación separada detectó y corrigió un script que elevaba el factor al cuadrado antes del envío.</p><p>Fuera del concurso necesitaría experiencia comparable del bloque adquirido para fijar el nivel. La tarifa histórica sugería +13 %, pero empeoró el backtest entre años; no la considero sustituto de la calibración.</p></div><h2>Preparación y controles de calidad</h2>
<p>Conservé los originales con huellas SHA-256 y apliqué las correcciones en capas derivadas reversibles. La preparación de la primera semana se contrastó con código separado: 41 de 41 comprobaciones. En la segunda se añadieron 74 controles. Las correcciones siguientes afectan directamente a los cruces, las tasas o las variables del modelo.</p>
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
<p>Los siniestros están valorados al cierre de 2024: el incurrido observado incluye reservas de caso y excluye lo aún no reportado. Ese objetivo observado (T0) no es el coste último. Incorporo el retraso de reporte reduciendo la exposición de entrenamiento según la proporción reportada de cada peligro (56 % en lesiones corporales de 2024). En la primera semana usé curvas de conteos (figura 2): trasladarlas al coste supone igual severidad media en tardíos y reportados. En las bases emergentes revisadas, una base usa curvas de coste del desarrollado y otra las estima con ambos mercados, excluyendo cada ámbito retenido antes de aprender. Su traslado conserva supuestos de desarrollo y composición.</p>
<p>En la cohorte emergente de 2023, el coste tardío observado de lesiones corporales superó un 42,7 % al previsto (IC90: +2 % a +102 %). Ese resultado y los fallos del backtest de conteos motivan el análisis de sensibilidad de cola y reservas. Las reservas de caso representan el 28,1 % del coste observado de 2024 y solo hay una valoración disponible. Los escenarios evalúan el efecto de esos supuestos; recalibrar el nivel en un escenario es un contrafactual y no prueba que el F3c entregado absorba ese deterioro.</p>
</div>
<div>
{{FIG:completitud}}
<p class="cap"><b>Figura 2.</b> Proporción estimada de siniestros reportados al cierre de 2024 por peligro (semana 1, chain-ladder de conteos), usada como exposición efectiva; no dice qué parte del coste estaba reportada.</p>
</div>
</div>
"""

P3 = """
<h2>Cómo construí y adapté el modelo</h2>
<p>En el mercado establecido combiné diez componentes de coste total y frecuencia × severidad. Usé LightGBM y CatBoost Tweedie para captar ceros, costes positivos e interacciones, y combiné por ramo porque ningún componente dominaba toda la cartera. Acoté la tendencia de severidad a ±15 % anual: aportó +0,000086 de D² en 2024. La mezcla alcanzó 0,138 frente a 0,071 de la tasa por ramo.</p>
{{FIG:esquema_modelo}}
<h3>Por qué transferí el aprendizaje</h3>
<p>Para los 209.063 periodos emergentes de 2025, aproveché las variables comunes y la mayor historia del desarrollado. En 2023, el contraste por cliente dio D² de 0,068 (tasa por ramo), 0,080 (GLM local), 0,083 (boosting local) y 0,121 (transferencia). Es evidencia histórica, anterior a corregir toda la cadena.</p>
<p>En la apertura registrada de 2024, la transferencia ganó +0,049 frente a la tasa por ramo (banda por seis comparaciones: +0,027 a +0,073). Modifiqué la salvaguarda de negocio nuevo después de conocer su fallo (pág. 1); trato los contrastes posteriores de 2024 como desarrollo adaptativo.</p>
<h3>F3c: dos bases y cinco pasos de ajuste</h3>
<p>Combino T2b y A1, modelos LightGBM Tweedie 1,5 por ramo. T2b usa la curva de reporte del desarrollado; A1, la de ambos mercados. A1 incorpora historia previa F1, promedia predicciones logarítmicas de las semillas 11, 12 y 13 y recupera el total por ramo de su referencia sin F1. Ambas bases ya incluyen la exposición del periodo.</p>
<table class="tight architecture">
<tr><th style="width:19%">Orden</th><th style="width:49%">Qué aplico a la predicción</th><th>Con qué información</th></tr>
<tr><td>1. Mezcla y nivel</td><td>Promedio aritmético T2b/A1, 50/50; factor global g = 1,187658.</td><td>Fuente 2021–2024; nivel local 2023–2024 y calibración pública.</td></tr>
<tr><td>2. Historial (F2)</td><td>Bonificación de autos → siniestros previos (0, 1, 2+) → exponente 0,9 en autos renovación → razón local de nivel.</td><td>T2b fuera de fold (OOF), 2023–2024; credibilidad n/(n + 300).</td></tr>
<tr><td>3. Nivel y dispersión</td><td>Exponentes contraídos en negocio nuevo y razones locales; nivel por ramo × nuevo/renovación. Base final_creible.</td><td>Respuesta pública, moderada por credibilidad; constantes congeladas.</td></tr>
<tr><td>4. Factores propios</td><td>Género en autos/contenidos → teletrabajo en contenidos → marketing en contenidos. Contracción logarítmica, K = 300.</td><td>Residuos T2b 2023–2024 tras F2 y su transformación de forma.</td></tr>
<tr><td>5. Nivel residual</td><td>Razón del óptimo Tweedie después/antes de factores, igual peso por año → F3c: 209.063 filas, seis decimales.</td><td>2023: T2b; 2024: promedio T2b/A1/mezcla. Sin etiquetas de 2025.</td></tr>
</table>
<p class="cap">n cuenta periodos con coste positivo. Factores y exponentes conservan el total previo de su celda antes de las razones de nivel; la normalización depende del lote. Respeto el orden y no multiplico otra vez por exposición. Código: reproduccion_cadena.py → construir_F2.py → construir_final.py → construir_F3c.py.</p>
<p>Calibré el nivel con factores conocidos y la curva Tweedie de los resultados públicos. De 0,15390 a 0,16914, atribuyo 0,01044 a calibración y 0,00480 a cambios de modelo, según ese orden. Dos decisiones de estructura también usaron respuesta pública. Conservo la ecuación y los contrastes en el anexo B; el privado sigue pendiente.</p>
<h3>Qué aportan los factores en una comparación protegida</h3>
<p>Comparé con/sin factores propios: aprendizaje con 2023 y precios fijos en 59.202 periodos de 2024, sin niveles ni exponentes públicos. Completitud, categorías, grupos, selección, árboles y ajustes excluyen el ámbito retenido. Ambos lados conservan bonificación, siniestralidad previa y forma de autos renovación.</p>
<table class="tight result-table">
<tr><th>Base protegida</th><th>D² sin / con factores</th><th>ΔD² global</th><th>Banda, familia 6</th></tr>
<tr><td>Curva del desarrollado</td><td>0,12332 / 0,12566</td><td>+0,00233</td><td>[+0,00058; +0,00425]</td></tr>
<tr><td>Curva de ambos mercados</td><td>0,12092 / 0,12335</td><td>+0,00243</td><td>[+0,00072; +0,00429]</td></tr>
<tr><td>Mezcla fija 50/50</td><td>0,12353 / 0,12590</td><td>+0,00237</td><td>[+0,00066; +0,00423]</td></tr>
</table>
<p class="cap">Bandas al 99,17 %, familia de seis; 10.000 réplicas por grupos, condicionadas a modelos aprendidos, sin repetir ajuste ni búsqueda. Las bases comparten etiquetas; no son confirmaciones independientes. La curva combinada usa una semilla y menos variables: no equivale a toda la producción de tres semillas. Precisión completa en el registro.</p>
<p>El límite inferior supera +0,0005, pero renovación explica el 98,09–99,39 % del aporte. Con composición de 2025, la mezcla gana +0,00099 (IC95: −0,00290 a +0,00476); las tres bandas cruzan cero. Concluyo mejora histórica global, con estabilidad de negocio nuevo aún incierta.</p>
"""

P4 = """
<h2>Cómo validé la solución</h2>
<table class="tight validation-map">
<tr><th style="width:20%">Qué contrasté</th><th style="width:43%">Diseño y referencia</th><th>Qué concluyo</th></tr>
<tr><td>Enfoque</td><td>2023, por cliente: transferencia frente a tasa, GLM y boosting locales.</td><td>Favorece transferir; no valida la cadena final.</td></tr>
<tr><td>Factores propios</td><td>Aprendizaje 2023 → precios fijos 2024. Tres bases con/sin factores; igual tronco y preparación.</td><td>Mejora global, concentrada en grupos y renovación.</td></tr>
<tr><td>F3c-R</td><td>26 ámbitos; comparación con F3c y control del mismo tronco/preprocesamiento. Criterios previos.</td><td>No sostiene la estabilidad exigida. Conservo F3c.</td></tr>
<tr><td>Reproducción</td><td>Originales → preparación → modelos → calibraciones → CSV. Huellas y métricas por otro cálculo.</td><td>Recupera la entrega; prueba ejecución, no rendimiento privado.</td></tr>
</table>
<h3>Dos problemas que resolví con apoyo de IA</h3>
<div class="cols ai-cases"><div class="box">
<h4>Fórmula de calibración</h4>
<p>Una versión elevaba al cuadrado el factor de nivel. La revisión cruzada de IA contrastó código, derivada Tweedie y mínimo numérico: para p = 1,5 corresponde k* de la página 2, sin cuadrado. Incorporé la corrección antes del envío, respaldada por un recálculo separado. No le atribuyo una ganancia de score aislada.</p>
</div><div class="box">
<h4>Aislamiento del aprendizaje</h4>
<p>La auditoría de IA detectó aprendizaje fuera de ámbito en preparación y completitud. Incorporé su reconstrucción por ámbito, con categorías, selección y ajustes. Alterar etiquetas retenidas no cambió aprendizaje ni predicciones. La revisión rechazó una réplica incompleta y rehízo sus controles: 45 pruebas, 35 adversas.</p>
</div></div>
<p class="cap">Con Claude y Codex contrasté código, derivaciones y resultados bajo mi seguimiento continuo. Otros controles corrigieron el ruido público frente a todo el test (semana 1, mejor privado frente a la variante) y el nulo de cardinalidad insuficiente: retiré aseguradora previa y ocupación. Registros, herramientas y código: anexos E–G.</p>
<h3>Negocio nuevo e influencia de pocos grupos</h3>
<p>La comparación de factores muestra qué ocurre en negocio nuevo y al retirar grupos favorables:</p>
<table class="tight result-table">
<tr><th>Receta protegida</th><th>Negocio nuevo: Δ / IC95</th><th>Δ autos nuevo</th><th>Δ sin 37 grupos favorables</th></tr>
<tr><td>Curva del desarrollado</td><td>+0,00011<br>[−0,00370; +0,00398]</td><td>−0,00122</td><td>−0,00001</td></tr>
<tr><td>Curva de ambos mercados</td><td>+0,00037<br>[−0,00300; +0,00392]</td><td>−0,00088</td><td>+0,00013</td></tr>
<tr><td>Mezcla 50/50</td><td>+0,00027<br>[−0,00327; +0,00393]</td><td>−0,00103</td><td>+0,00006</td></tr>
</table>
<p class="cap">Las tres bases fallan por el límite inferior; solo la curva combinada cumple el piso puntual de autos nuevo (−0,001). Retirar retrospectivamente 37, 42 y 39 de 36.408 grupos favorables anula sus ganancias. Negocio nuevo es el primer año de póliza, no una dirección nunca vista. Los umbrales son del proyecto.</p>
<h3>Qué cambia al tensar reservas y cola</h3>
<p>Revisé 50 escenarios: 45 de coste, reservas y cola, y cinco de completitud. Δ global sigue positivo tanto con precios fijos como reaprendiendo el destino solo en 2023. En este último caso, los peores Δ son +0,00218, +0,00224 y +0,00220. Árboles y curvas fuente quedan congelados por ámbito: son sensibilidades condicionales, sin probabilidades; no certifican reservas ni el margen del 8 %.</p>
<h3>Por qué conservé F3c frente a F3c-R</h3>
<p>Tras completar los 26 ámbitos, comparé F3c-R con F3c y con un control del mismo tronco y preprocesamiento. El D² global fue 0,126662 frente a 0,126806 de F3c. Negocio nuevo ganó 0,005464, pero contenidos nuevos perdió 0,014658.</p>
<p>Los 10.000 remuestreos por grupos, 50 escenarios y cinco omisiones completas de folds no sostuvieron la estabilidad exigida. Sin 37 grupos favorables, Δ global cae a −0,003676. Conservé F3c sin escoger después un segmento o fold ganador.</p>
<p class="cap">En el flujo real se alteraron etiquetas retenidas, se reprodujeron resultados sin aprendizaje y se usó otro optimizador. Las bandas condicionan modelos ajustados, sin cubrir toda la búsqueda adaptativa. Este contraste usa referencias distintas de la tabla de factores, identificadas en el registro.</p>

"""

P5 = """
<h2>Prima comercial de las 20 pólizas de referencia</h2>
<div class="cols-6535">
<div>
<p>Calculo la prima comercial a partir de la prima de riesgo F3c y los supuestos del archivo de gastos. Al riesgo sumo el reaseguro catastrófico de hogar (12 %) y el gasto fijo. El gasto variable del 15 %, la comisión, el impuesto del 8 % y el margen del 8 % se incorporan mediante el denominador. Aplico 85 CU completos por póliza; el prorrateo por exposición (85·e), conservado como alternativa, daría 20.304,23 CU frente a los 20.800,02 de la solución final.</p>
</div>
<div class="box" style="margin-top:0">
<math display="block"><mi>P</mi><mo>=</mo><mfrac><mrow><mi>R</mi><mo>+</mo><mn>0,12</mn><mo>·</mo><msub><mi>R</mi><mtext>hogar</mtext></msub><mo>+</mo><mn>85</mn></mrow><mrow><mn>1</mn><mo>−</mo><mn>0,15</mn><mo>−</mo><mi>c</mi><mo>−</mo><mn>0,08</mn><mo>−</mo><mn>0,08</mn></mrow></mfrac></math>
<p class="small">Comisión c = 0,20 con corredor y 0 en venta directa; el denominador vale 0,49 o 0,69. Ejemplo, C00302985 (contenidos, corredor): (54,08 + 6,49 + 85) / 0,49 = 297,08 CU.</p>
</div>
</div>
{{TABLA:primas}}
<p class="cap">Importes del periodo en CU; el cociente divide la prima comercial completa, incluidos los 85 CU fijos, por la exposición exacta, por eso crece en las pólizas cortas. Cálculo: fuente/prima_comercial_20ref.py.</p>
<p>Las veinte primas suman 20.800,02 CU. No extrapolo a la cartera el cociente anualizado agregado de 3,63 ni lo propongo como subida: anualiza también el gasto fijo de pólizas cortas. La siniestralidad estimada a coste último de 2023–2024 fue 0,85 por CU de prima devengada (edificios: 1,17), frente a recargos proporcionales del 51 % con corredor. Separado el gasto fijo, el riesgo anualizado con catástrofe equivale a 1,40 veces la prima escrita. Revisar precio, comisión y aumentos exige analizar retención y condiciones comparables.</p>


<h2>Interpretación actuarial y alcance</h2>
<p>La prima comercial conserva la incertidumbre de la prima de riesgo y del nivel calibrado. El 8 % es un supuesto del archivo de gastos, no una estimación de suficiencia. La revisión histórica muestra mejora global de los factores, concentrada en renovación; las bandas con composición de 2025 cruzan cero y el soporte de negocio nuevo de hogar es escaso. La valoración única de siniestros y la severidad tardía mantienen incertidumbre sobre el coste último.</p>
<p>El aislamiento por año y grupo controla el uso de observaciones retenidas. La disponibilidad histórica de maestros, clima y duración no puede reconstruirse por completo. Algunas comparaciones usan una receta distinta de la producción y 2024 es desarrollo adaptativo; sus resultados deben interpretarse con ese alcance.</p>
<h3>Reproducción y solución final</h3>
<p>La reconstrucción desde originales recuperó los CSV históricos: 436 estimadores en la primera semana; 57 etapas y 87 modelos en la segunda. Conservo las diferencias internas y dos restauraciones de código documentadas. El cotejo de huellas, el recálculo de métricas y los controles adversos respaldan la integridad de la ejecución; la generalización se evalúa con los contrastes temporales y de sensibilidad.</p>
<div class="box"><h4>Resultado del trabajo</h4>
<p>La solución combina modelos por peligro en el mercado establecido y transferencia con ajustes locales en el emergente. Mantengo F3c como modelo definitivo de la parte 2: D² público 0,16914 y veinte primas comerciales por 20.800,02 CU. El contraste de F3c-R respalda conservar el archivo enviado. La evaluación privada sigue pendiente.</p></div>
"""
