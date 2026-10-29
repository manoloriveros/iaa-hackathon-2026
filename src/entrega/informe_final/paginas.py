"""Informe técnico, edición 29 de octubre de 2026.
Revisión editorial de Codex según comentarios del participante; modelo y cifras preservados.
"""

RUNHEAD = 'AI Hackathon IAA 2026 · Informe final, partes 1 y 2'

P1 = """
<h1>Modelización de la prima de riesgo en dos mercados con apoyo de IA</h1>
<p class="sub">De la experiencia de siniestros a la tarifa: modelos por peligro, transferencia de aprendizaje y validación actuarial</p>
<p class="byline">AI Hackathon IAA 2026 · Partes 1 y 2 · Manuel Rodríguez (Kaggle: manoloriveros) · Edición del 29 de octubre de 2026 · Datos sintéticos; importes en CU</p>
<h2>Problema actuarial y enfoque de solución</h2>
<p class="lead">El objetivo fue estimar el coste último esperado de los siniestros de cada periodo de póliza de 2025 en autos, edificios y contenidos del hogar, antes de gastos y márgenes. El mercado establecido ofrecía cuatro años de historia. El emergente, solo dos y un cambio fuerte de composición: el negocio nuevo pasaba del 14 % histórico al 76 % de la cartera de 2025 tras la adquisición del bloque de un corredor. La solución debía combinar señal predictiva, tratamiento del desarrollo de siniestros y estabilidad ante ese cambio.</p>
<div class="kpis kpis3">
 <div class="kpi"><div class="v">0,13864</div><div class="l">D² privado de la parte 1. Cuarto puesto entre 54 equipos.</div></div>
 <div class="kpi"><div class="v">0,16914</div><div class="l">D² público de F3c, modelo definitivo de la parte 2. Resultado privado pendiente.</div></div>
 <div class="kpi"><div class="v">0,121 frente a 0,083</div><div class="l">Contraste histórico por cliente en 2023: modelo transferido frente al mejor modelo solo local.</div></div>
</div>
<p>El modelo del mercado establecido combina coste total Tweedie con frecuencia × severidad por peligro. Esta descomposición permite recoger mecanismos distintos, como incendio, fuga de agua y lesiones corporales, y combinar componentes que no rinden igual en todos los ramos. Para el emergente se transfieren relaciones aprendidas con variables comunes y se añaden ajustes locales con credibilidad. Así se aprovecha la historia disponible sin exigir que una muestra pequeña estime toda la estructura desde cero.</p>
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
<p>La exposición se concilió antes de estimar tasas; el retraso de reporte se incorporó por peligro y se contrastó con cohortes observadas. Las variables capaces de revelar el siniestro del periodo se excluyeron. La transferencia se comparó con modelos locales, y los ajustes del emergente se revisaron por ramo y tipo de negocio. El nivel final se calibró mediante variaciones multiplicativas controladas y la respuesta analítica de la métrica, moderada por credibilidad. Esta etapa usa información del tablero de 2025 y se evalúa separadamente del ajuste histórico.</p>
<h3>Validación orientada a la cartera futura</h3>
<p>La revisión combinó particiones por cliente y dirección, contrastes temporales, pruebas adversas de fuga, sensibilidad de reservas e influencia de grupos. La ganancia agregada de los factores se concentra en renovaciones; su traslado al negocio nuevo conserva incertidumbre. La alternativa regularizada F3c-R también se evaluó con el flujo completo y no aportó estabilidad suficiente para sustituir F3c (página 4). La selección final conserva F3c y sus predicciones originales.</p>
<p>Claude y Codex apoyaron la construcción de código y el diseño de contrastes. Bajo mi seguimiento continuo, se revisaron resultados con distintos modelos y agentes, se recalcularon controles con implementaciones separadas y se corrigieron fallos de datos, fórmulas y aislamiento. Ese trabajo permitió sostener una revisión iterativa dentro del plazo del concurso. Las páginas siguientes presentan el método y la evidencia que respalda cada decisión.</p>
"""

P2 = """
<h2>Objetivo de estimación y diseño de los datos</h2>
<p>Se modela el coste total del periodo, neto de franquicia y recobros, sin siniestros rechazados e incluido el coste aún no reportado. La exposición se expresa en días cubiertos / 365. La evaluación usa D² Tweedie con potencia 1,5; las predicciones entregadas corresponden al periodo completo, sin anualizar.</p>
<p>Para reducir fuga se excluyeron contactos con atención al cliente, decisión de renovación y clima observado de 2025. Los maestros sin fecha se trataron como disponibles al cotizar, supuesto que los archivos no permiten comprobar para todos sus campos. La validación separa años y grupos de cliente–dirección; los contrastes inversos examinan estabilidad, mientras la calibración pública incorpora información adicional de 2025.</p>
<div class="box"><h4>Una consecuencia de la métrica que guió todo el proyecto</h4>
<p>El factor que, multiplicado por todas las predicciones de un grupo, minimiza la desviación Tweedie 1,5 es</p>
<math display="block"><msup><mi>k</mi><mo>*</mo></msup><mo>=</mo><mfrac><mrow><mo>∑</mo><mo stretchy="false">(</mo><mi>y</mi><mo>/</mo><msqrt><mi>μ</mi></msqrt><mo stretchy="false">)</mo></mrow><mrow><mo>∑</mo><msqrt><mi>μ</mi></msqrt></mrow></mfrac></math>
<p>Optimiza la desviación para unas predicciones dadas y puede diferir del cociente entre costes y predicciones totales. Se aplicó por ramo y por celda. El recálculo con una implementación separada detectó y corrigió un script que elevaba el factor al cuadrado antes del envío.</p></div><h2>Preparación y controles de calidad</h2>
<p>Los originales se conservaron con huellas SHA-256 y las correcciones se aplicaron en capas derivadas reversibles. La preparación de la primera semana se contrastó con código separado: 41 de 41 comprobaciones. En la segunda se añadieron 74 controles. Las correcciones siguientes afectan directamente a los cruces, las tasas o las variables del modelo.</p>
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
<p>Los siniestros están valorados al cierre de 2024: el incurrido observado incluye reservas de caso y excluye lo aún no reportado. Ese objetivo observado (T0) no es el coste último. El retraso de reporte se incorpora reduciendo la exposición de entrenamiento según la proporción reportada de cada peligro (56 % en lesiones corporales de 2024). En la primera semana se usaron curvas de conteos (figura 2): trasladarlas al coste supone igual severidad media en tardíos y reportados. En las bases emergentes revisadas, una base usa curvas de coste del desarrollado y otra las estima con ambos mercados, excluyendo cada ámbito retenido antes de aprender. Su traslado conserva supuestos de desarrollo y composición.</p>
<p>En la cohorte emergente de 2023, el coste tardío observado de lesiones corporales superó un 42,7 % al previsto (IC90: +2 % a +102 %). Ese resultado y los fallos del backtest de conteos motivan el análisis de sensibilidad de cola y reservas. Las reservas de caso representan el 28,1 % del coste observado de 2024 y solo hay una valoración disponible. Los escenarios evalúan el efecto de esos supuestos; recalibrar el nivel en un escenario es un contrafactual y no prueba que el F3c entregado absorba ese deterioro.</p>
</div>
<div>
{{FIG:completitud}}
<p class="cap"><b>Figura 2.</b> Proporción estimada de siniestros reportados al cierre de 2024 por peligro (semana 1, chain-ladder de conteos), usada como exposición efectiva; no dice qué parte del coste estaba reportada.</p>
</div>
</div>
"""

P3 = """
<h2>Arquitectura: combinación por peligro y ramo</h2>
<p>En el mercado establecido se combinaron diez componentes de coste total y de frecuencia × severidad. LightGBM y CatBoost con objetivo Tweedie captan ceros, costes positivos e interacciones; la descomposición por peligro distingue mecanismos de siniestro. La combinación por ramo responde a que ningún componente dominaba en toda la cartera. La tendencia de severidad se acotó a ±15 % anual y aportó +0,000086 de D² en 2024. La mezcla alcanzó 0,138 frente a 0,071 de una tasa por ramo.</p>
{{FIG:esquema_modelo}}
<h2>Adaptación al mercado emergente</h2>
<p>Para los 209.063 periodos de 2025, la escasez de historia y el peso del negocio nuevo favorecieron transferir relaciones estimadas con variables comunes. La evidencia de 2023 por cliente se resume en la figura 3. En otro contraste, la apertura registrada de 2024 dio +0,049 de D² frente a la tasa por ramo (banda por seis comparaciones: +0,027 a +0,073). La regla inicial de protección de negocio nuevo falló y se modificó después de conocer el resultado. Las comparaciones posteriores sobre 2024 son desarrollo adaptativo.</p>
<div class="cols"><div>
{{FIG:escalera_2023}}
<p class="cap"><b>Figura 3.</b> Comparación histórica por cliente en 2023, anterior a corregir toda la cadena. Se distingue del contraste con aislamiento completo de la tabla inferior.</p>
</div><div>
<h3>Ajustes locales y calibración</h3>
<p>Los factores propios complementan la señal transferida con credibilidad n/(n + K), K = 300 en F3c. El nivel y la dispersión dentro de las seis celdas de ramo × tipo de negocio se calibraron por separado. Para el nivel se aplicaron factores conocidos a las predicciones y se resolvió la curva Tweedie a partir de los resultados públicos; la credibilidad limitó el desplazamiento según el ruido estimado.</p>
<p>De 0,15390 a 0,16914, los pasos de calibración aportaron 0,01044 y los cambios de modelo 0,00480. Es una descomposición secuencial, dependiente del orden y las interacciones. Dos decisiones de estructura también usaron respuesta pública. El anexo B conserva la ecuación y los contrastes; el resultado privado de la parte 2 sigue pendiente.</p>
</div></div>
<h3>Comparación con aislamiento del aprendizaje</h3>
<p>El contraste posterior reaprende con 2023 y evalúa 59.202 periodos de 2024, sin niveles ni exponentes públicos. Completitud, categorías, grupos, selección interna, árboles y ajustes excluyen el ámbito retenido. La referencia mantiene siniestralidad, bonificación y la transformación común de autos renovación: se retira solo el bloque de factores propios. Alterar etiquetas retenidas no cambia el aprendizaje ni sus predicciones.</p>
<table class="tight">
<tr><th>Base protegida</th><th>D² sin / con factores</th><th>ΔD² global</th><th>Banda condicional, familia 6</th></tr>
<tr><td>Curva del desarrollado</td><td>0,12332 / 0,12566</td><td>+0,00233</td><td>[+0,00058; +0,00425]</td></tr>
<tr><td>Curva de ambos mercados</td><td>0,12092 / 0,12335</td><td>+0,00243</td><td>[+0,00072; +0,00429]</td></tr>
<tr><td>Mezcla fija 50/50</td><td>0,12353 / 0,12590</td><td>+0,00237</td><td>[+0,00066; +0,00423]</td></tr>
</table>
<p class="cap">Valores redondeados; precisión completa en el registro. Bandas al 99,17 % por contraste, familia de seis; 10.000 réplicas por grupos condicionadas a modelos aprendidos: no repiten aprendizaje ni búsqueda histórica. Las tres bases comparten etiquetas, sin confirmación independiente. La receta de curva combinada evalúa una semilla y menos variables; no valida la configuración íntegra de producción de tres semillas.</p>
<p>El límite inferior supera +0,0005 en las tres bases. Renovación explica el 98,09–99,39 % del aporte. Con composición de 2025, la mezcla mejora +0,00099 (IC95: −0,00290 a +0,00476); las tres bandas cruzan cero. El contraste respalda una ganancia histórica global, pero no resuelve la estabilidad del negocio nuevo.</p>

<p>En una aplicación sin tablero, el nivel requeriría experiencia comparable del bloque adquirido. La tarifa histórica sugería +13 %, pero su variación entre años empeoró el backtest; no sustituye por sí sola la calibración del concurso.</p>
"""

P4 = """
<h2>Validación y uso de IA para contrastar la solución</h2>
<p>Claude y Codex se integraron en un ciclo de hipótesis, código, contraste y corrección. Los modelos y agentes revisores cuestionaron supuestos y recalcularon resultados; los tableros reunieron métricas, alertas y trazabilidad para el seguimiento continuo. La IA también apoyó traducción y comunicación técnica. Su aporte al modelado se observa en las correcciones verificables de la tabla, no solo en la generación de código.</p>
{{FIG:flujo_ia}}
<p class="cap"><b>Figura 4.</b> Ciclo de desarrollo y contraste bajo supervisión del participante, con criterios previos y conservación de resultados adversos.</p>
<table class="tight">
<tr><th style="width:43%">Error o límite detectado</th><th style="width:22%">Comprobación</th><th>Consecuencia</th></tr>
<tr><td>Preparación y completitud usaban información fuera del ámbito permitido</td><td>Auditoría de la cadena</td><td>Preparación y ajuste rehechos por ámbito</td></tr>
<tr><td>Una réplica incompleta se daba por válida</td><td>Revisión integral</td><td>Controles reescritos; 45 pruebas, 35 adversas</td></tr>
<tr><td>Ruido público medido contra todo el test</td><td>Batería de sensibilidad</td><td>Cambió la selección; mejoró el privado frente a la variante contrastada</td></tr>
<tr><td>Un nulo de pocos niveles validaba variables falsas</td><td>Revisor de factores</td><td>Aseguradora previa y ocupación retiradas</td></tr>
</table>
<h3>Estabilidad por segmento e influencia</h3>
<p>El criterio inicial exigía ΔD² de negocio nuevo ≥ 0 y límite inferior IC95 ≥ −0,001. La transferencia mejoró +0,013, con límite −0,011: la regla no se cumplió. Se aceptó la mejora puntual tras modificar ese veto; el cambio no constituye evidencia de protección del segmento. La revisión posterior de factores separa su ganancia global del resultado por negocio:</p>
<table class="tight">
<tr><th>Factores, receta protegida</th><th>Negocio nuevo: Δ / IC95</th><th>Δ autos nuevo</th><th>Δ al retirar 37 grupos favorables</th></tr>
<tr><td>Curva del desarrollado</td><td>+0,00011<br>[−0,00370; +0,00398]</td><td>−0,00122</td><td>−0,00001</td></tr>
<tr><td>Curva de ambos mercados</td><td>+0,00037<br>[−0,00300; +0,00392]</td><td>−0,00088</td><td>+0,00013</td></tr>
<tr><td>Mezcla 50/50</td><td>+0,00027<br>[−0,00327; +0,00393]</td><td>−0,00103</td><td>+0,00006</td></tr>
</table>
<p class="cap">La protección de negocio nuevo falla en las tres bases por el límite inferior. El piso puntual de autos nuevo, −0,001, solo se cumple con la curva de ambos mercados. Al retirar retrospectivamente 37, 42 y 39 de 36.408 grupos favorables, respectivamente, se anula la ganancia. Negocio nuevo identifica primer año de póliza, no dirección nunca vista. Los umbrales pertenecen al proyecto.</p>
<h3>Reservas, cola y repetición del flujo</h3>
<p>Los 50 escenarios (45 de coste, reservas y cola; cinco de completitud) mantienen Δ global positivo con precios fijos y con la capa destino reaprendida solo en 2023. En esta última, los peores Δ son +0,00218, +0,00224 y +0,00220 para las tres bases. Árboles y curvas fuente permanecen congelados por ámbito: son sensibilidades condicionales, sin probabilidades asignadas, y no certifican reservas ni el margen del 8 %.</p>
<h3>Contraste final de una alternativa regularizada</h3>
<p>F3c-R se completó en 26 ámbitos y se comparó con F3c y con un control del mismo tronco y preprocesamiento. El D² local global fue 0,126662 frente a 0,126806 de F3c; negocio nuevo mejoró 0,005464, pero contenidos nuevos perdió 0,014658. Los 10.000 remuestreos por grupos, 50 escenarios y cinco omisiones completas de folds no sostuvieron la estabilidad requerida. Al retirar 37 grupos favorables, Δ global cae a −0,003676. Estos resultados sustentan conservar F3c, sin escoger retrospectivamente un segmento o fold ganador.</p>
<p class="cap">Los controles del flujo real incluyeron alteración de etiquetas retenidas, replay sin aprendizaje y un optimizador alternativo. Los intervalos son condicionales a modelos ajustados; no cubren toda la búsqueda adaptativa. Las cifras de F3c-R corresponden a una comparación distinta de la tabla de factores, con referencias explícitas en el registro.</p>
"""

P5 = """
<h2>Prima comercial de las 20 pólizas de referencia</h2>
<div class="cols-6535">
<div>
<p>La prima comercial se obtiene de la prima de riesgo F3c y los supuestos del archivo de gastos. Al riesgo se suman el reaseguro catastrófico de hogar (12 %) y el gasto fijo. El gasto variable del 15 %, la comisión, el impuesto del 8 % y el margen del 8 % se incorporan mediante el denominador. Se aplican 85 CU completos por póliza; el prorrateo por exposición (85·e), conservado como alternativa, daría 20.304,23 CU frente a los 20.800,02 de la solución final.</p>
</div>
<div class="box" style="margin-top:0">
<math display="block"><mi>P</mi><mo>=</mo><mfrac><mrow><mi>R</mi><mo>+</mo><mn>0,12</mn><mo>·</mo><msub><mi>R</mi><mtext>hogar</mtext></msub><mo>+</mo><mn>85</mn></mrow><mrow><mn>1</mn><mo>−</mo><mn>0,15</mn><mo>−</mo><mi>c</mi><mo>−</mo><mn>0,08</mn><mo>−</mo><mn>0,08</mn></mrow></mfrac></math>
<p class="small">Comisión c = 0,20 con corredor y 0 en venta directa; el denominador vale 0,49 o 0,69. Ejemplo, C00302985 (contenidos, corredor): (54,08 + 6,49 + 85) / 0,49 = 297,08 CU.</p>
</div>
</div>
{{TABLA:primas}}
<p class="cap">Importes del periodo en CU; el cociente divide la prima comercial completa, incluidos los 85 CU fijos, por la exposición exacta, por eso crece en las pólizas cortas. Cálculo: fuente/prima_comercial_20ref.py.</p>
<p>Las veinte primas suman 20.800,02 CU. El cociente anualizado agregado de 3,63 no se extrapola a la cartera ni es una subida recomendada: anualiza también el gasto fijo de pólizas cortas. La siniestralidad estimada a coste último de 2023–2024 fue 0,85 por CU de prima devengada (edificios: 1,17), frente a recargos proporcionales del 51 % con corredor. Separado el gasto fijo, el riesgo anualizado con catástrofe equivale a 1,40 veces la prima escrita. Revisar precio, comisión y aumentos exige analizar retención y condiciones comparables.</p>


<h2>Interpretación actuarial y alcance</h2>
<p>La prima comercial conserva la incertidumbre de la prima de riesgo y del nivel calibrado. El 8 % es un supuesto del archivo de gastos, no una estimación de suficiencia. La revisión histórica muestra mejora global de los factores, concentrada en renovación; las bandas con composición de 2025 cruzan cero y el soporte de negocio nuevo de hogar es escaso. La valoración única de siniestros y la severidad tardía mantienen incertidumbre sobre el coste último.</p>
<p>El aislamiento por año y grupo controla el uso de observaciones retenidas. La disponibilidad histórica de maestros, clima y duración no puede reconstruirse por completo. Algunas comparaciones usan una receta distinta de la producción y 2024 es desarrollo adaptativo; sus resultados deben interpretarse con ese alcance.</p>
<h3>Reproducción y solución final</h3>
<p>La reconstrucción desde originales recuperó los CSV históricos: 436 estimadores en la primera semana; 57 etapas y 87 modelos en la segunda. Se conservaron las diferencias internas y dos restauraciones de código documentadas. El cotejo de huellas, el recálculo de métricas y los controles adversos respaldan la integridad de la ejecución; la generalización se evalúa con los contrastes temporales y de sensibilidad.</p>
<div class="box"><h4>Resultado del trabajo</h4>
<p>La solución combina modelos por peligro en el mercado establecido y transferencia con ajustes locales en el emergente. F3c queda como modelo definitivo de la parte 2: D² público 0,16914 y veinte primas comerciales por 20.800,02 CU. El contraste de F3c-R respalda conservar el archivo enviado. La evaluación privada sigue pendiente.</p></div>
"""
