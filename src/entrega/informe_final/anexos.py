"""Anexos del informe final (fuera de las cinco páginas calificadas)."""

EXPERIMENTOS = [
    ("1", "Tasa constante por ramo y LightGBM Tweedie regularizado", "Público 0,07118 y 0,12321", "alt", "Referencias de partida"),
    ("1", "Mezcla por peligro: coste total Tweedie más frecuencia × severidad por peligro", "D² de 2024 fuera de muestra 0,138, frente a 0,071 de la tasa constante, con mejora en cada ramo", "ok", "Entró (S30 y después S41)"),
    ("1", "Tendencia de severidad acotada a ±15 %", "Aporta +0,000086 de la ventaja de S30 sobre S22 en 2024", "ok", "Entró"),
    ("1", "IBNR llevado a la exposición efectiva", "Backtesting en tres cortes; lesiones corporales con el 56 % reportado al cierre de 2024", "ok", "Entró"),
    ("1", "Calibración de nivel por ramo", "Óptimos del público ×0,977, ×1,075 y ×1,084", "ok", "Entró con credibilidad: ×0,9962, ×1,0260 y ×1,0126"),
    ("1", "Contraste de forma por ramo (S43)", "En autos, S43 comprimía la forma un 4,5 % cuando la validación local pedía +1,7 % y +2,3 %; restaba 0,000127 de D² en 2023", "no", "Descartada"),
    ("2", "Modelos solo emergentes frente a la transferencia del desarrollado", "2023: GLM 0,080, GBM 0,083, transferido 0,121. 2024: +0,0486 sobre la referencia (99,17 %: +0,0265 a +0,0733)", "ok", "Entró la transferencia"),
    ("2", "FT-Transformer preentrenado en el desarrollado", "+0,0387 sobre el mismo modelo entrenado desde cero en 2024, por debajo del LightGBM transferido", "alt", "Contraste"),
    ("2", "CatBoost, marca y modelo, modelos por peligro, modelo conjunto y tope de siniestros a 100.000 CU", "CatBoost −0,0110 en 2023; marca y modelo −0,0093 en autos; el resto no pasó la regla fijada antes de entrenar", "no", "Descartados"),
    ("2", "Componente GBM regularizado (mezcla robusta)", "+0,0009 en 2024 y +0,0011 en DES24; −0,00043 en el público", "alt", "Alternativa"),
    ("2", "Nivel de 2025 desde la siniestralidad de la tarifa", "Pedía +13,0 %, con credibilidad de 0,02 a 0,34; su backtest bajó el D² de 0,1260 a 0,1248", "no", "Descartado"),
    ("2", "Nivel global: dos factores de contraste", "Óptimo ×1,2231; la regla aplicó ×1,1877; +0,00558 en el público", "ok", "Entró (F)"),
    ("2", "Siniestros declarados y bonificación por años sin siniestros", "+0,0030 a +0,0033 fuera de tiempo; +0,00085 en el público", "ok", "Entró (F2)"),
    ("2", "Nivel por celda y forma de autos de nuevo negocio", "El público pedía entre ×0,63 y ×1,08 del nivel global según la celda; +0,00486 en el público", "ok", "Entró (final_creible)"),
    ("2", "Factores propios: género, teletrabajo y segmento de marketing", "Nulos por permutación con p de 0,0005 a 0,028; +0,00395 en el público", "ok", "Entró (F3c)"),
    ("2", "Frecuencia × severidad por peligro (FSp)", "Ganancia de ensamblado, estable en renovación y ruidosa en nuevo negocio", "alt", "Alternativa (F4c)"),
    ("2", "Aseguradora previa, ocupación, clima del mismo año, factores por quintil de tasa y contracción ridge", "No superan el nulo; el granizo explica las lunas (z 7,9) sin mover el D²; los factores por quintil cambian de signo sin los 20 siniestros mayores; en la contracción, un solo incendio aporta el 35,8 % de la ganancia", "no", "Descartados"),
    ("2", "Regularización F3c-R con flujo completo: 26 ámbitos", "D² local 0,126662 frente a 0,126806 de F3c; mejora agregada de negocio nuevo sin estabilidad suficiente", "alt", "Se conserva F3c; alternativa documentada"),
]

CRONO = [
    ("28 oct", "Comparación completa de F3c-R y cierre de F3c como definitivo", "Sin evidencia suficiente para sustituir F3c; se conserva el archivo enviado"),
    ("27 oct", "Cadena protegida T2b, A1 y mezcla; 50 escenarios", "Ganancia global favorable; falla protección de negocio nuevo. F3c intacto; páginas 3–5"),
    ("26 oct", "Batería de sensibilidad de la semana 2 y sensibilidad de reservas recalculada para F3c; F3d y F4c preparados", "F3c conserva en el privado esperado entre el 58 % y el 95 % de su ganancia pública; reglas de lectura fijadas antes de puntuar"),
    ("26 oct", "F3c: factores propios del emergente sobre final_creible", "0,16914 en el público, segundo puesto; previsión 0,1666 (0,1647 a 0,1682)"),
    ("25 oct", "final_creible: nivel por celda con credibilidad y forma corregida", "0,16519, dentro de la previsión de la auditoría (0,16511 a 0,16522)"),
    ("25 oct", "F2: siniestros declarados y bonificación; calibración por celda y forma", "0,16033"),
    ("24 oct", "F: nivel global ×1,188 por la regla de credibilidad", "0,15948, el valor que daba la fórmula cerrada"),
    ("24 oct", "Factores de nivel global ×0,85 y ×1,20", "0,14095 y 0,15955; óptimo del público en ×1,223"),
    ("24 oct", "Mezcla robusta", "0,15347, por debajo de la primera mezcla; no se eligió"),
    ("24 oct", "Primer envío de la parte 2: mezcla 50/50 de las dos líneas transferidas", "0,15390"),
    ("24 oct", "Enmienda de la salvaguarda de cliente nuevo (política v2), decidida conociendo el acta de 2024", "La transferencia pasa a titular; no hay confirmación intacta de 2024 para esa regla"),
    ("23 oct", "Apertura de 2024 por la línea de validación, con la lista de candidatos congelada", "La transferencia supera a la referencia en +0,049; falla la salvaguarda de cliente nuevo"),
    ("23 oct", "Validación de los datos emergentes (74 controles) y decisiones sobre capital, clima, nivel del negocio nuevo y gasto fijo", "Reglas de datos fijadas antes de modelar"),
    ("23 oct", "Marca final de la parte 1: S41, elegida por su esperanza en el privado aunque S43 puntuaba más en el público", "Público 0,13016; privado 0,13864, cuarto de 54"),
    ("22 oct", "Calibración de nivel y forma: S41, S42 y S43", "0,13016, 0,13033 y 0,13048, los valores previstos"),
    ("20 oct", "Mezcla por peligro como modelo definitivo y réplica desde los estimadores guardados", "436 estimadores cargados, 194 salidas y los dos CSV repetidos bit a bit"),
    ("18 oct", "S22 y S30", "0,12988 y 0,12996; cada uno tomó el primer puesto del público al enviarse"),
    ("17 oct", "Primeros envíos: tasa por ramo y LightGBM regularizado", "0,07118 y 0,12321"),
    ("16 oct", "Apertura del reto, auditoría de datos y reglas reversibles", "Base de todo lo anterior"),
]

HERRAMIENTAS = [
    ("Claude (Cowork), en sesiones separadas por función", "Auditoría de datos, código Python, validaciones, revisiones encargadas a subagentes, sensibilidad, reservas, documentos y aportes al foro", "Hipótesis y criterio publicados antes de calcular; resultado publicado también cuando fue adverso"),
    ("Codex", "Base de modelado, recetas, rondas periódicas de validación y envíos a Kaggle", "Ningún envío sin mi autorización directa"),
    ("Subagentes revisores", "Rehacer con código propio cada hallazgo que iba a cambiar una entrega", "Sin acceso a las conclusiones del autor"),
    ("Gemini", "Una propuesta metodológica al inicio de la semana 1", "Contrastada con la literatura; se descartaron sus afirmaciones sin fuente"),
    ("Kaggle: conexión MCP de solo lectura y CLI oficial", "Leer reglas, metadatos y puntuaciones; subir archivos desde Codex", "La marca final la decido yo"),
    ("Python: pandas, PyArrow, NumPy, scikit-learn, LightGBM, CatBoost, statsmodels, PyTorch", "Datos, modelos Tweedie, GLM residuales y un FT-Transformer de contraste", "La métrica propia se comparó con d2_tweedie_score de scikit-learn"),
    ("Git y GitHub, repositorio privado; SHA-256 y manifiestos", "Versionado de código, registro de decisiones y huella de cada archivo", "Datos y predicciones fuera de Git; huella comprobada antes de cada envío"),
    ("Foro en Markdown con escritura bloqueada y recibos", "Comunicación entre líneas con autor, hora UTC e identificador", "Un recibo por aporte y numeración sin saltos"),
]

SHAS = [
    ("S41, marca final de la parte 1", "d8661c2874e9…", "herramientas/regenerar_s41.py desde S30, con diez controles"),
    ("final_creible, parte 2", "1a003d868…", "construir_final.py con los recibos de calibración"),
    ("F3c, modelo definitivo de la parte 2", "5ab5e4e34290…", "construir_F3c.py sobre final_creible"),
    ("F3d, variante no incluida", "5103f6fd9cf2…", "construir_F3d.py (K = 60 en contenidos)"),
]

REFERENCIAS = [
    'International Actuarial Association. AI-Assisted Hackathon 2026, partes 1 y 2. Kaggle, 2026. <a href="https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1">kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1</a> y <a href="https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2">…-part-2</a>.',
    'IAA, Artificial Intelligence Task Force. <i>Professional Considerations for Actuaries Interacting with Artificial Intelligence</i>. Septiembre de 2026. <a href="https://actuaries.org/app/uploads/2026/10/AITF_Professional_Considerations_Paper_Final_Approved.pdf">actuaries.org</a>.',
    'IAA, Artificial Intelligence Task Force. <i>Artificial Intelligence Governance Framework</i>. Noviembre de 2025. <a href="https://actuaries.org/app/uploads/2025/12/AITF_Governance_Framework_Paper_Final_Approved.pdf">actuaries.org</a>.',
    'IAA, Artificial Intelligence Task Force. <i>Documentation of Artificial Intelligence Models or Systems</i>. Noviembre de 2025. <a href="https://actuaries.org/app/uploads/2025/12/AITF_Documentation_AI_Models_Paper_Final_Approved.pdf">actuaries.org</a>.',
    'scikit-learn. <i>sklearn.metrics.d2_tweedie_score</i>. <a href="https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html">scikit-learn.org</a>.',
    'Bühlmann, H. y Gisler, A. (2005). <i>A Course in Credibility Theory and its Applications</i>. Springer.',
    'Jørgensen, B. (1997). <i>The Theory of Dispersion Models</i>. Chapman &amp; Hall.',
    'Ke, G. y otros (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. <i>Advances in Neural Information Processing Systems</i> 30.',
    'Gorishniy, Y., Rubachev, I., Khrulkov, V. y Babenko, A. (2021). Revisiting Deep Learning Models for Tabular Data. <i>Advances in Neural Information Processing Systems</i> 34.',
    'Tribunal de Justicia de la Unión Europea. Sentencia de 1 de marzo de 2011, asunto C-236/09, Association Belge des Consommateurs Test-Achats.',
]


def tabla_experimentos():
    filas = "".join(
        f'<tr><td>{s}</td><td>{e}</td><td>{r}</td><td><span class="chip {c}">{d}</span></td></tr>'
        for s, e, r, c, d in EXPERIMENTOS)
    return ('<table class="tight"><tr><th style="width:6%">Sem.</th><th style="width:31%">Experimento</th>'
            '<th>Resultado medido</th><th style="width:20%">Decisión</th></tr>' + filas + '</table>')


def tabla_crono():
    filas = "".join(f'<tr><td>{f}</td><td>{h}</td><td>{r}</td></tr>' for f, h, r in CRONO)
    return ('<table class="tight"><tr><th style="width:9%">Fecha</th><th style="width:48%">Hito</th><th>Resultado y lectura</th></tr>'
            + filas + '</table>')


def tabla_herramientas():
    filas = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in HERRAMIENTAS)
    return ('<table class="tight"><tr><th style="width:27%">Herramienta</th><th style="width:38%">Uso concreto</th><th>Control que la acompañó</th></tr>'
            + filas + '</table>')


def tabla_shas():
    filas = "".join(f'<tr><td>{a}</td><td class="mono">{b}</td><td>{c}</td></tr>' for a, b, c in SHAS)
    return ('<table class="tight"><tr><th style="width:32%">Entrega</th><th style="width:18%">SHA-256 (inicio)</th><th>Cómo se regenera</th></tr>'
            + filas + '</table>')


PAGINAS = [
"""
<h1>Anexos</h1>
<p class="small">Material de apoyo fuera de las cinco páginas calificadas. Cada cifra remite a un archivo o a un envío registrado en el repositorio.</p>
<p class="small">En los archivos y en el foro se usan estos códigos. S41: entrega final de la parte 1 (Mezcla por peligro calibrada). B0: mezcla inicial de dos modelos transferidos. F: nivel global. F2: siniestros declarados y bonificación. final_creible: nivel por celda y forma. F3c: factores propios del emergente, modelo definitivo de la parte 2. F3d y F4c: variantes no incluidas en este informe.</p>
<h2>Anexo A. Experimentos: qué se probó y qué quedó</h2>
<p>Cada experimento se declaró antes de correr, con su hipótesis, sus datos y su criterio de aceptación. La tabla recoge 18 experimentos de las dos semanas, seis de la primera y doce de la segunda; detrás de la fila de la transferencia están los catorce modelos y tres mezclas que comparó la segunda línea de modelado (validación cruzada de 2023 por cliente y 2024 abierto una vez). El color resume la decisión: verde si entró en la tarifa, gris si quedó como referencia o alternativa y rojo si se descartó.</p>
{{TABLA:experimentos}}
<p>Casi todo lo descartado cayó en la validación local, antes de gastar un envío; las dos que se enviaron antes de descartarse, la forma de S43 y la mezcla robusta, se juzgaron después con validación local y con el ruido del tablero corregido. Los factores propios entraron con la regla pública; su respaldo local es el de la tabla de la página 3, y la entrega anterior sin factores (final_creible) sigue como referencia.</p>
""",
"""
<h2>Anexo B. Sensibilidad y reservas</h2>
<p>Un análisis de sensibilidad dice cuánto se mueve el resultado si falla un supuesto. En la semana 1 fijé la materialidad en el 1 % del nivel de 2025 de cada ramo, y leí las pruebas sobre el nivel contra ese umbral.</p>
<h3>Calibración analítica del nivel</h3>
<p>La desviación de cada fila con potencia 1,5 es d(y, μ) = 4y/√μ + 4√μ − 8√y, y el D² es uno menos el cociente entre la desviación del modelo y la de la prima única. Si se multiplican todas las predicciones por un factor c, el D² público sigue una curva exacta que depende de dos cantidades desconocidas de las filas públicas:</p>
<math display="block"><msup><mi>D</mi><mn>2</mn></msup><mo stretchy="false">(</mo><mi>c</mi><mo stretchy="false">)</mo><mo>−</mo><msup><mi>D</mi><mn>2</mn></msup><mo stretchy="false">(</mo><mn>1</mn><mo stretchy="false">)</mo><mo>=</mo><mo>−</mo><mfrac><mn>4</mn><msub><mi>D</mi><mn>0</mn></msub></mfrac><mo>[</mo><msub><mi>S</mi><mn>1</mn></msub><mo stretchy="false">(</mo><msup><mi>c</mi><mrow><mo>−</mo><mn>1</mn><mo>/</mo><mn>2</mn></mrow></msup><mo>−</mo><mn>1</mn><mo stretchy="false">)</mo><mo>+</mo><msub><mi>S</mi><mn>2</mn></msub><mo stretchy="false">(</mo><msup><mi>c</mi><mrow><mn>1</mn><mo>/</mo><mn>2</mn></mrow></msup><mo>−</mo><mn>1</mn><mo stretchy="false">)</mo><mo>]</mo></math>
<p>con S₁ = Σ y/√μ, S₂ = Σ √μ y D₀ la desviación de la prima única. Dos evaluaciones con factores multiplicativos conocidos permiten despejar la curva; la credibilidad modera el ajuste según el ruido del tablero. Las previsiones de nivel y forma de la figura B4 se derivan de esa relación, con información de evaluaciones públicas previas.</p>
<div class="cols">
<div>
{{FIG:tornado_s1}}
<p class="cap"><b>Figura B1.</b> Semana 1: efecto de cada supuesto sobre el nivel de 2025 del ramo, frente a la materialidad del 1 %. Batería D95, 102 cifras verificadas. El privado confirmó la dirección: el nivel de autos estaba un 6,5 % alto y los de hogar casi exactos.</p>
</div>
<div>
{{FIG:cadena_privado}}
<p class="cap"><b>Figura B2.</b> Análisis histórico del público y del privado esperado, anterior a la corrección de cadena. El rango depende de nueve supuestos, no es un intervalo de confianza. El público de final_creible mide nivel y forma juntos (+0,00486). La concentración actual se evalúa con la receta protegida de las páginas 3 y 4, que sustituye las cifras locales anteriores.</p>
</div>
</div>
<h3>Reservas e IBNR con los datos de la semana 2</h3>
<p>Con una sola valoración de siniestros no se puede saber si una reserva es exacta. Sí se puede medir cuánto tendría que equivocarse para mover la tarifa más del 1 %, y comparar ese umbral con lo que estiman los datos. Dos multiplicadores lo ordenan: b escala la reserva de los siniestros abiertos (b = 0,75 quiere decir que faltaba por pagar un 25 % menos de lo reservado) y k escala el coste aún no reportado. La clase es «acotado» si el intervalo de la estimación cabe en el rango que tolera la tarifa e «incertidumbre material» si lo cruza.</p>
{{FIG:reservas}}
<p class="cap"><b>Figura B3.</b> Sensibilidad histórica de reservas e IBNR para F3c, con 390 cifras cotejadas. La salida «acotada» recalcula los óptimos públicos: es un contrafactual condicionado, no absorción comprobada por la calibración de la entrega congelada. No demuestra suficiencia del ajuste original.</p>
<p>La reserva de caso suma 4.995.797,64 CU sobre 27.997.991,57 CU observados (17,8 %): 9,3 % en 2023 y 28,1 % en 2024. Lesiones corporales concentra el 49,0 % de la reserva. Su coste tardío superó en 42,7 % al previsto. Los 50 escenarios nuevos conservan ganancia global positiva, pero congelan árboles y curvas fuente; no reemplazan evolución posterior ni prueban suficiencia (página 4).</p>

""",
"""
<h2>Anexo B, continuación. Previsiones y credibilidad de los factores propios</h2>
<div class="cols">
<div>
{{FIG:prevision_medido}}
<p class="cap"><b>Figura B4.</b> Público medido menos previsto antes de cada envío; franja clara, intervalo previsto. Los ajustes de calibración quedaron dentro; los dos cambios de modelo, fuera.</p>
</div>
<div>
<p>La credibilidad usa n/(n + K), con K = 300 en F3c. F3d (K = 60 en contenidos) no es la selección. La receta protegida aprendida en 2023 mejora entre +0,0023317 y +0,0024318 en 2024 según la base; renovación explica el 98,09–99,39 %. Ninguna banda con composición de 2025 separa la mejora de cero al 95 %. La protección de negocio nuevo falla en las tres bases. La evidencia histórica entre años se contradice y no se rehízo esa prueba inversa en esta corrida. Retirar 37/42/39 grupos favorables anula la ganancia de T2b/A1/mezcla. Estas cifras sustituyen el contraste anterior de +0,00239 y 38 grupos.</p>
</div>
</div>

<h2>Anexo C. Supuestos principales</h2>
<table class="tight">
 <tr><th style="width:21%">Supuesto</th><th style="width:44%">Valor o regla</th><th>Respaldo</th></tr>
 <tr><td>Exposición</td><td>Días cubiertos entre 365</td><td>Convención de 2025 en los datos</td></tr>
 <tr><td>Siniestros no reportados</td><td>Conteos en semana 1; coste T2b del desarrollado y A1 de ambos mercados, por ámbito</td><td>Backtesting en tres cortes; cohorte 2023</td></tr>
 <tr><td>Reserva de caso</td><td>Valor al 31 de diciembre de 2024, sin ajuste (b = 1)</td><td>Limitación declarada; umbrales de la figura B3</td></tr>
 <tr><td>Tendencia a 2025</td><td>Semana 1: severidad por peligro acotada a ±15 %. Semana 2: sin tendencia; nivel por calibración controlada</td><td>La tendencia del desarrollado empeoró 2024 (−0,0016)</td></tr>
 <tr><td>Credibilidad del tablero</td><td>Z global 0,854; Z por celda entre 0,36 y 0,866</td><td>Ruido medido contra la parte no vista del test</td></tr>
 <tr><td>Credibilidad de los factores</td><td>n/(n + K) con K = 300 en F3c (K = 60 en contenidos en F3d)</td><td>Nulos por permutación; figura B4</td></tr>
 <tr><td>Información al cotizar</td><td>Tablas maestras sin fecha conocidas al cotizar; fuera el clima de 2025 y los contactos con el cliente</td><td>Diseño de datos de la página 2; disponibilidad histórica no demostrada</td></tr>
 <tr><td>Gasto fijo</td><td>85 CU completos por póliza</td><td>Mi decisión del 26 oct; prorrateado daría 20.304,23 CU en vez de 20.800,02</td></tr>
 <tr><td>Género</td><td>Tarifable en el emergente</td><td>Diccionario del concurso; en una tarifa real, revisión legal (Test-Achats)</td></tr>
</table>


<h2>Anexo D. Criterios de control y decisiones metodológicas</h2>
<p class="small">Reglas documentadas del proceso; su registro no acredita por sí solo bloqueos automáticos implementados.</p>
<table class="tight">
 <tr><th style="width:22%">Momento</th><th style="width:44%">Regla escrita antes</th><th>Qué pasa si se cumple</th></tr>
 <tr><td>Calibración global</td><td>Factor óptimo no identificable o fuera de 0,67 a 1,49</td><td>El cálculo se detiene</td></tr>
 <tr><td>Calibración por celda</td><td>La base no reproduce su puntuación, un factor negativo o una celda a más de max(0,7; 3σ)</td><td>El cálculo se detiene</td></tr>
 <tr><td>Factores propios</td><td>Entran si ganan al menos 0,0005 en el público; más de 0,003 obliga a revisar</td><td>Revisar el cálculo antes de seleccionar</td></tr>
 <tr><td>Entrega final de la parte 1</td><td>Otro candidato gana en esperanza en el privado por más de 0,00003</td><td>Aviso; se cumplió y la entrega cambió</td></tr>
 <tr><td>Reservas</td><td>Un error plausible mueve el nivel de un ramo más del 1 %</td><td>Incertidumbre material declarada</td></tr>
</table>
<table class="tight">
 <tr><th style="width:12%">Fecha</th><th style="width:62%">Decisión metodológica (hora de Bogotá)</th><th>Tipo</th></tr>
 <tr><td>17 oct</td><td>Criterios para corregir capitales unas mil veces mayores</td><td>Delegada, registrada</td></tr>
 <tr><td>19 oct</td><td>Materialidad del 1 % del nivel de 2025 por ramo para juzgar reservas</td><td>Propia</td></tr>
 <tr><td>20 oct</td><td>Cierre de la parte 1 con la Mezcla por peligro, sin pasar todos los filtros internos</td><td>Propia</td></tr>
 <tr><td>23 oct</td><td>Acepto la alarma de sensibilidad y cambio la entrega final de la parte 1</td><td>Propia, a propuesta de la IA</td></tr>
 <tr><td>23 oct</td><td>Reglas de datos del emergente (capitales, clima, nivel del negocio nuevo); gasto fijo por exposición</td><td>Delegadas, salvo el gasto fijo</td></tr>
 <tr><td>24 oct</td><td>Enmiendo la salvaguarda de cliente nuevo conociendo el resultado de 2024</td><td>Propia, registrada</td></tr>
 <tr><td>24 oct</td><td>Se prioriza robustez del modelo antes de incorporar la calibración de nivel</td><td>Revisión del enfoque</td></tr>
 <tr><td>25 y 26 oct</td><td>Plan de mejora y reglas para leer los últimos candidatos</td><td>Delegadas («me quedo con tus recomendaciones»)</td></tr>
 <tr><td>26 oct</td><td>Gasto fijo completo por póliza (85 CU) en vez del prorrateo; se conserva F3c</td><td>Propia</td></tr>
</table>
""",
"""
<h2>Anexo E. Cronología de decisiones y envíos</h2>
<p class="small">De lo más reciente a lo más antiguo, en hora de Bogotá. Los envíos tuvieron mi autorización escrita; la revisión del 27 no produjo envíos.</p>
{{TABLA:crono}}
<p class="small">Evidencia de la revisión del 27: <span class="mono">docs/semana2/F3C_A1_MEZCLA_PROTEGIDAS_Y_ESCENARIOS.md</span> y <span class="mono">registro/validacion_cadena_f3c_A1_mezcla_actual.json</span>, dentro del repositorio común.</p>
<h2>Anexo F. Herramientas y cómo se usaron</h2>
{{TABLA:herramientas}}
""",
"""
<h2>Anexo G. Reproducción y trazabilidad</h2>
<p>El código, el registro de decisiones y el foro viven en un repositorio privado de GitHub. Los datos de Kaggle y las predicciones no se suben, porque las reglas del concurso no permiten redistribuirlos: quedan en una carpeta privada fuera de Git, con su huella SHA-256 en manifiestos.</p>
<ul class="lim">
 <li>Antes de nada se comprobaron los datos: los 24 Parquet oficiales se compararon byte a byte con las copias originales cuando Kaggle cambió su fecha de publicación, sin diferencias.</li>
 <li>Para la parte 1, <span class="mono">reproducir.py</span> rehace la cadena completa desde los once Parquet originales: el reajuste de los 436 estimadores (unas once horas con dos núcleos) devolvió los dos CSV con su SHA registrado, con 19 de 181 huellas intermedias distintas en el último bit porque LightGBM elige por cronómetro el modo de cálculo (fijar <span class="mono">force_row_wise</span> devolvió el histórico); la réplica sin ajustes, con los estimadores guardados, repitió las 194 salidas y los dos CSV en 34 minutos.</li>
 <li>Para la parte 2, los scripts construyen cada entrega desde la anterior. La batería de sensibilidad, en otra sesión, reprodujo F2, final_creible, F3c y F3d sin diferencias desde los Parquet originales y las predicciones guardadas de los modelos base, sin reentrenarlos. Tuvo que reconstruir la cabecera del módulo <span class="mono">f3_eval.py</span>, que faltaba en las copias del equipo; el módulo original se incorporó a esas copias el 26 de octubre. F4c no se reprodujo porque sus predicciones de producción tampoco estaban en las copias.</li>
 <li>El reentrenamiento completo de la parte 2 desde los Parquet originales terminó el 26 de octubre en un entorno nuevo (registro REENTRENO-ORIGINALES-20261026): 57 etapas, 87 modelos finales, originales intactos, sin leer predicciones anteriores ni consultar Kaggle; los CSV de F, F2, final_creible, F3c, F3d y F4c salieron idénticos a los históricos, con diferencias internas de hasta 4,4e-16 relativo. Sus límites, declarados en el registro: reproducción propia, dos tramos de código restaurados y cotejados (no recuperados), constantes del tablero congeladas y Python 3.12.14 frente al 3.13 declarado. La reproducción por otra persona sigue pendiente, con acta y guía preparadas.</li>
</ul>
{{TABLA:shas}}

<h2>Anexo H. Composición del coste por peligro en los dos mercados</h2>
{{FIG:mezcla_peligros}}
<p class="cap"><b>Figura H1.</b> Cuota del coste de cada peligro dentro de su ramo, 2023–2024. En edificios el incendio pesa el doble en el emergente; en autos las cuotas casi coinciden. Cálculo propio desde los Parquet oficiales.</p>

<h2>Anexo I. Referencias</h2>
<div class="refs small">{{REFS}}</div>
"""
]
