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
<p>Para los 209.063 periodos de 2025, la escasez de historia y el peso del negocio nuevo favorecieron transferir relaciones estimadas con variables comunes. En 2023, la comparación histórica por cliente dio D² de 0,068 para la tasa por ramo, 0,080 para el GLM emergente, 0,083 para boosting emergente y 0,121 para la transferencia; precede a la corrección de toda la cadena. En otro contraste, la apertura registrada de 2024 dio +0,049 de D² frente a la tasa por ramo (banda por seis comparaciones: +0,027 a +0,073). La regla inicial de protección de negocio nuevo falló y se modificó después de conocer el resultado. Las comparaciones posteriores sobre 2024 son desarrollo adaptativo.</p>
<h3>Cadena exacta del archivo F3c</h3>
<p>F3c combina T2b y A1: modelos LightGBM Tweedie 1,5 por ramo, entrenados en el desarrollado y ajustados al nivel emergente. T2b usa la curva de reporte del desarrollado; A1, la curva combinada. A1 incorpora historia previa F1 y promedia las predicciones logarítmicas de las semillas 11, 12 y 13; después recupera el total por ramo de su referencia sin F1. Cada base ya incluye la exposición del periodo.</p>
<table class="tight architecture">
<tr><th style="width:20%">Orden de aplicación</th><th style="width:48%">Transformación conservada en la entrega</th><th>Origen de los ajustes</th></tr>
<tr><td>1. Mezcla y nivel global</td><td>Promedio aritmético 50/50 de T2b y A1; multiplicador global g = 1,187658.</td><td>Bases fuente 2021–2024; nivel local 2023–2024 y calibración pública.</td></tr>
<tr><td>2. Historial local (F2)</td><td>Bonificación sin siniestros en autos → siniestros previos (0, 1, 2+) → exponente 0,9 en autos renovación → razón local de nivel.</td><td>Predicciones fuera de fold (OOF) de T2b 2023–2024; credibilidad n/(n + 300).</td></tr>
<tr><td>3. Nivel y dispersión</td><td>Exponentes contraídos en negocio nuevo y razones locales; nivel por ramo × nuevo/renovación, limitado por credibilidad. Produce la base final_creible.</td><td>Calibraciones controladas con respuesta pública; constantes históricas congeladas.</td></tr>
<tr><td>4. Factores propios</td><td>Género en autos y contenidos → teletrabajo en contenidos → segmento de marketing en contenidos; contracción logarítmica, K = 300.</td><td>Residuos locales T2b 2023–2024 tras F2 y su transformación de forma.</td></tr>
<tr><td>5. Nivel residual y salida</td><td>Razón del nivel Tweedie óptimo después/antes de los factores, con igual peso por año → F3c, 209.063 filas a seis decimales.</td><td>2023: T2b; 2024: promedio T2b, A1 y mezcla. Sin etiquetas de 2025.</td></tr>
</table>
<p class="cap">n cuenta periodos con coste positivo. Los factores y exponentes conservan el total previo de su celda antes de aplicar las razones de nivel; la normalización depende del lote. Se respeta este orden, sin volver a multiplicar la exposición. La tabla describe producción; la evaluación inferior reaprende otra receta. Código: reproduccion_cadena.py → construir_F2.py → construir_final.py → construir_F3c.py.</p>
<p>El nivel se obtuvo aplicando factores conocidos a las predicciones y resolviendo la curva Tweedie con los resultados públicos. De 0,15390 a 0,16914, la calibración aportó 0,01044 y los cambios de modelo 0,00480, en una descomposición dependiente del orden. Dos decisiones de estructura también usaron respuesta pública. El anexo B conserva ecuación y contrastes; el privado de la parte 2 sigue pendiente.</p>
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


"""

P4 = """
<h2>Validaciones: pregunta, comparación y alcance</h2>
<table class="tight validation-map">
<tr><th style="width:20%">Qué se comprueba</th><th style="width:43%">Diseño y referencia</th><th>Lectura del resultado</th></tr>
<tr><td>Elección del enfoque</td><td>Comparación histórica por cliente en 2023: transferencia frente a tasa, GLM y boosting emergentes.</td><td>Favorece transferir; no acredita la cadena final de F3c.</td></tr>
<tr><td>Aporte de factores</td><td>Aprendizaje con 2023; precios fijos en 2024. Tres bases, cada una con/sin factores, mismo tronco y preparación.</td><td>Mejora global; límites en negocio nuevo y concentración por grupos (págs. 3–4).</td></tr>
<tr><td>Alternativa F3c-R</td><td>26 ámbitos; comparación con F3c y con control de igual tronco/preprocesamiento. Criterios fijados antes del resultado.</td><td>No sostiene la estabilidad exigida; se conserva F3c.</td></tr>
<tr><td>Reproducción de entrega</td><td>Originales → preparación → modelos → calibraciones → CSV. Cotejo de huellas y métricas por otro cálculo.</td><td>Recupera el archivo final; acredita ejecución, no rendimiento privado.</td></tr>
</table>
<h3>Dos correcciones concretas apoyadas por IA</h3>
<div class="cols ai-cases"><div class="box">
<h4>Calibración: detectar y corregir una fórmula</h4>
<p>Una versión elevaba al cuadrado el factor de nivel. La revisión cruzada contrastó el código con la derivada de la devianza Tweedie y el mínimo numérico: para p = 1,5 corresponde el cociente k* de la página 2, sin ese cuadrado. Se corrigió antes del envío. La fórmula y el recálculo separado permitieron comprobar la corrección, sin atribuirle una ganancia de score aislada.</p>
</div><div class="box">
<h4>Validación: aislar todo el aprendizaje</h4>
<p>Revisar solo el modelo omitía que preparación y completitud aprendían fuera del ámbito permitido. La auditoría de dependencias llevó a rehacerlas por ámbito, junto con categorías, selección y ajustes. Se alteraron las etiquetas retenidas: el aprendizaje y sus predicciones no cambiaron. Una réplica incompleta se rechazó y sus controles se reescribieron: 45 pruebas, 35 adversas.</p>
</div></div>
<p class="cap">Claude y Codex apoyaron generación de código, derivaciones, revisiones cruzadas y controles, con seguimiento continuo del participante. Los casos documentan correcciones comprobables. Otros contrastes corrigieron el ruido público frente a todo el test (semana 1, mejor privado frente a la variante) y el nulo de cardinalidad insuficiente, que llevó a retirar aseguradora previa y ocupación. Registros, herramientas y código: anexos E–G.</p>
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
<p>En una aplicación sin tablero, el nivel requeriría experiencia comparable del bloque adquirido. La tarifa histórica sugería +13 %, pero su variación entre años empeoró el backtest; no sustituye por sí sola la calibración del concurso.</p>
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
