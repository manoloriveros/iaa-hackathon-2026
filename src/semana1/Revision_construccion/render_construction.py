"""Informe autocontenido de la evidencia longitudinal CON01."""
import base64
import html
import json

import analyze_construction as a
import pandas as pd
import pyarrow.parquet as pq


def render(out, summary, verification):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    year = pd.read_csv(out / 'tables/codes_by_year.csv')
    pivot = year.pivot(index='year', columns='construction_type', values='row_share_pct').fillna(0)
    pairs = pq.read_table(out / 'tables/boundary_2022_2023.parquet').to_pandas()
    matrix = pd.crosstab(pairs.previous_construction_type, pairs.construction_type).reindex(
        index=['brick','non_standard','stone','t'], columns=['brick','non_standard','stone','w'], fill_value=0)
    fig, axes = plt.subplots(1,2,figsize=(12.8,4.7))
    axes[0].plot(pivot.index,pivot.t,'o-',label='T (antes de 2023)',color='#b65f00')
    axes[0].plot(pivot.index,pivot.w,'o-',label='W (desde 2023)',color='#007d86')
    axes[0].plot(pivot.index,pivot.t+pivot.w,':',label='T/W combinado',color='#4e426d',linewidth=2.4)
    axes[0].set_xticks(pivot.index);axes[0].set_ylabel('% de filas de edificios')
    axes[0].set_title('Sustitución de etiqueta en el corte de 2023')
    axes[0].axvspan(2024.5,2025.3,color='#e6eef2',alpha=.7)
    axes[0].text(2025,1.0,'Test X:\nconfirmación',ha='center',fontsize=8)
    axes[0].legend(fontsize=8,loc='lower left');axes[0].set_ylim(-.4,14)
    axes[1].imshow(np.where(matrix.to_numpy()>0,1,0),cmap='Blues',vmin=0,vmax=1,alpha=.7)
    for i in range(4):
        for j in range(4):
            axes[1].text(j,i,f'{matrix.iloc[i,j]:,}'.replace(',','.'),ha='center',va='center',
                         color='white' if matrix.iloc[i,j] else '#55616b',fontsize=10)
    axes[1].set_xticks(range(4),['brick','non_standard','stone','W'],fontsize=9)
    axes[1].set_yticks(range(4),['brick','non_standard','stone','T'],fontsize=9)
    axes[1].set_xlabel('Clase en 2023');axes[1].set_ylabel('Clase en 2022')
    axes[1].set_title('Misma póliza y dirección: 149.887 pares')
    fig.tight_layout();fig.savefig(out / 'figures/evidence.png',dpi=155);plt.close(fig)
    histories = pq.read_table(out / 'tables/case_histories.parquet').to_pandas()
    selection = json.loads((out / 'case_selection.json').read_text(encoding='utf-8'))
    fig, axes = plt.subplots(1,2,figsize=(12.8,4.6))
    for item, color in zip(selection[:3],['#007d86','#ac5f17','#705798']):
        rows = histories[histories.case_id.eq(item['case_id'])]
        years = pd.to_datetime(rows.period_start).dt.year
        axes[0].plot(years,rows.sum_insured/1000,'o-',label=item['policy_id'],color=color)
        for x,y,code in zip(years,rows.sum_insured/1000,rows.construction_type):
            axes[0].annotate(code.upper(),(x,y),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8,color=color)
    axes[0].set_xticks([2021,2022,2023,2024,2025]);axes[0].set_ylabel('Capital registrado derivado (miles CU)')
    axes[0].set_title('Tres historias reales con T,T,W,W,W');axes[0].legend(fontsize=8)
    stability = pd.read_csv(out / 'tables/paired_context_stability.csv')
    fields = ['customer_id','occupancy','accidental_damage_cover','mortgage','voluntary_excess','compulsory_excess','smoke_alarms','days_unoccupied']
    sub = stability[stability.cohort.eq('t_to_w')].set_index('field').loc[fields]
    labels = ['Tomador','Ocupación','Daño accidental','Hipoteca','Deducible voluntario','Deducible obligatorio','Alarma de humo','Días desocupado']
    axes[1].barh(labels[::-1],(100*sub.equal_including_both_missing/sub.pairs).to_numpy()[::-1],color='#007d86')
    axes[1].set_xlim(0,105);axes[1].set_xlabel('% de 18.218 pares con valor idéntico')
    axes[1].set_title('Contexto estable; algunos campos anuales varían')
    fig.tight_layout();fig.savefig(out / 'figures/cases_and_context.png',dpi=155);plt.close(fig)
    image = lambda name: base64.b64encode((out / 'figures' / name).read_bytes()).decode()
    table = lambda df: df.to_html(index=False,escape=True,border=0,float_format=lambda v:f'{v:,.4f}')
    display_year = year.pivot(index='year',columns='construction_type',values='rows').fillna(0).astype(int).reset_index()
    cohort = pd.read_csv(out / 'tables/cohort_reconciliation.csv')
    cohort['status'] = cohort.status.replace({
        'continues_2023_same_address_as_w':'Continúa en 2023, misma dirección, W',
        'no_later_observed_period':'Sin periodo posterior observado',
        'later_2022_new_address':'Siguiente periodo en 2022, dirección nueva',
        'continues_2022_same_address_from_t':'Anterior en 2022, misma dirección, T',
        'first_observed_policy':'Primera observación de la póliza',
        '2023_new_address':'Anterior en 2023, dirección distinta'})
    case_payload = []
    display_cols = ['row_id','address_id','period_start','period_end','construction_type','harmonized_code','occupancy','sum_insured',
                    'exposure','written_premium','smoke_alarms','days_unoccupied','voluntary_excess','compulsory_excess']
    for item in selection:
        rows = histories[histories.case_id.eq(item['case_id'])][display_cols]
        # A JSON string representation handles nulls and dates without NaN tokens.
        case_payload.append({**item,'rows':json.loads(rows.to_json(orient='records',date_format='iso'))})
    options = ''.join(f'<option value="{i}">{html.escape(x["policy_id"])}: {html.escape(x["reason"])}</option>' for i,x in enumerate(selection))
    stable_tw = stability[stability.cohort.eq('t_to_w')].drop(columns='cohort')
    ratios = pd.read_csv(out / 'tables/capital_ratios_descriptive.csv')
    s = summary
    sections = [
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Construcción T/W: revisión longitudinal</title>',
        '<style>body{font:16px/1.6 system-ui;max-width:1250px;margin:36px auto;padding:0 24px;color:#183041;background:#fafcfd}h1{line-height:1.2}h2{margin-top:2em;font-weight:600}.decision{padding:18px 22px;background:#e6f3f1;border-left:5px solid #007d86}.limit{padding:14px 20px;background:#fff3df}table{border-collapse:collapse;display:block;overflow:auto;font-size:13px;max-width:100%;background:white}td,th{padding:8px 10px;border-bottom:1px solid #d7e1e7;text-align:right;white-space:nowrap}th{background:#e9f0f4}img{max-width:100%;height:auto}a{color:#075f92}select{width:100%;padding:10px;font:inherit}code{background:#edf1f4;padding:1px 4px}details{margin:1em 0}</style></head><body>',
        '<h1>T y W: ¿dos construcciones o un cambio de código?</h1>',
        '<div class="decision"><p>La evidencia respalda agrupar T y W como alias temporales de una misma clase observada. La recomendación técnica es <code>t,w → tw_code</code>, conservando el código registrado. No se confirma todavía que el material físico sea madera o timber.</p>',
        '<p>Se preparó una copia candidata con <code>construction_type_harmonized</code>. La versión activa de limpieza permanece igual; no se registró una aprobación humana de activación. La candidata conserva cada campo anterior, sin corregir capitales, primas ni exposición.</p></div>',
        f'<p>Universo: {s["train_rows"]:,} filas de entrenamiento (2021–2024) y {s["test_rows"]:,} de test (2025), solo edificios. Una fila es un periodo de póliza; una póliza puede tener varios periodos y direcciones en un año. Se analizan {s["addresses"]:,} direcciones. La inferencia se obtiene de entrenamiento; 2025 es una comprobación adicional.</p>',
        '<h2>El cambio aparece en una fecha común</h2>',
        table(display_year),
        '<p>T no tiene cobertura después del 31 de diciembre de 2022. W no aparece antes del 1 de enero de 2023. La categoría representa aproximadamente el 12% de las filas en ambos regímenes. El porcentaje por sí solo sería evidencia débil; la continuidad de las mismas pólizas es la prueba más informativa.</p>',
        f'<img alt="Códigos T y W por año y matriz de continuidad 2022–2023" src="data:image/png;base64,{image("evidence.png")}">',
        '<h2>La comparación emparejada descarta una mezcla entre clases</h2>',
        '<p>Se ordenaron los periodos por póliza, fecha y row_id. En el cruce 2022→2023 se comparó el último periodo anterior con el siguiente, exigiendo la misma dirección. Los 149.887 pares se reconstruyeron también con una unión independiente de periodos terminados el 31-12-2022 e iniciados el 01-01-2023. No se cruzaron todas las filas de un año con todas las del otro, lo que duplicaría pólizas con cambios dentro del año.</p>',
        table(matrix.reset_index()),
        '<p>Las 18.218 transiciones T→W corresponden a 18.218 pólizas y direcciones distintas. Todas comienzan el 01-01-2023, sin hueco de cobertura. Ningún T que continúa en ese cruce con la misma dirección pasa a brick, stone o non_standard. Tampoco llega W desde otra clase en esa misma dirección.</p>',
        f'<p>En entrenamiento se revisaron {s["same_address_train_transitions"]:,} transiciones consecutivas en una misma dirección; con la confirmación de 2025, {s["same_address_all_transitions"]:,}. Después de agrupar T/W no queda ninguna contradicción de clase. Las otras tres clases permanecen iguales. Cada una de las {s["addresses"]:,} direcciones conserva una sola clase armonizada en toda su historia.</p>',
        '<p>Las direcciones pertenecen a una sola póliza en estos archivos. Por ello, la revisión por inmueble reexpresa la misma evidencia longitudinal y no constituye una segunda muestra independiente. Cero excepciones describe este universo observado; no es una certificación universal de materiales.</p>',
        '<h2>Qué pasa con las filas que no forman el par</h2>',
        table(cohort),
        '<p>Las 22.274 filas T de 2022 incluyen 18.218 continuaciones a 2023, 831 periodos seguidos de un cambio de dirección dentro de 2022 y 3.225 sin periodo posterior observado. Las 22.353 filas W de 2023 incluyen 18.218 continuaciones, 815 con dirección nueva dentro de 2023 y 3.320 primeras observaciones. Estas últimas heredan la hipótesis global de código; no se les inventa una historia T individual.</p>',
        '<p>Se encontraron cambios reales de clase cuando cambia la dirección. En 2023 hay 564 llegadas a W desde brick en otra dirección, 72 desde non_standard, 69 desde stone y 110 desde otro W. No contradicen la recodificación temporal y se conservan como cambios de riesgo. El emparejamiento por policy_id sin address_id produciría una conclusión errónea.</p>',
        '<h2>Qué permanece igual y qué cambia en los 18.218 pares</h2>',
        table(stable_tw),
        '<p>Son idénticos el tomador, dirección, ocupación, cobertura de daño accidental, hipoteca, ambos deducibles, canal y forma de pago. Los días desocupados y algunas alarmas sí varían, como también ocurre en los controles. No se exige que todos los campos del riesgo sean estáticos para reconocer el cambio sistemático de etiqueta.</p>',
        '<p>Los capitales y las primas cambian entre años. El cociente mediano de capital 2023/2022 es aproximadamente 1,03 en T→W y en las otras clases, excluyendo de esa descripción las filas del conjunto congelado de capitales pendientes. Esa semejanza aporta contexto, sin convertir el capital en prueba física de material. Ningún valor se ajusta aquí.</p>',
        '<details><summary>Cocientes descriptivos de capital y exclusiones exactas</summary>' + table(ratios) + '</details>',
        f'<img alt="Historias reales y estabilidad de atributos en los pares T a W" src="data:image/png;base64,{image("cases_and_context.png")}">',
        '<h2>Seis casos reales, con toda su historia</h2>',
        '<p>Los tres primeros son las primeras pólizas en orden de identificador que presentan exactamente una fila T,T,W,W,W de 2021 a 2025. Los otros muestran una mudanza a W, una salida de T a brick y una alta W sin historia T. La regla de selección queda archivada; estos ejemplos ilustran los resultados exhaustivos.</p>',
        f'<label for="case">Póliza</label><select id="case">{options}</select><p id="reason"></p><div id="history"></div>',
        '<p>El CSV de casos incluye además atributos del maestro de direcciones, como tipo de inmueble, año de construcción y techo. Ese maestro no está versionado y no prueba por sí mismo cómo era el inmueble en años anteriores. Las primas son las registradas por periodo: no se dividen por exposición ni se interpretan automáticamente como tarifa anual.</p>',
        '<noscript><p>El explorador requiere JavaScript. Todas las filas están disponibles en <a href="tables/case_histories.csv">el CSV de historias</a>.</p></noscript>',
        '<h2>Interpretación para el seguro y la tarifa</h2>',
        '<p>La construcción describe una característica del edificio que puede afectar su respuesta a incendio, agua u otros daños y el coste de reparación. Aquí solo se puede afirmar que T y W se comportan como la misma clase observada bajo dos etiquetas de calendario. El diccionario enumera cuatro materiales y los datos presentan cuatro clases en cada régimen, lo que hace plausible que la clase restante corresponda a timber. Falta una correspondencia explícita del organizador para asignarle ese nombre físico.</p>',
        '<p>Separar T y W al modelar puede mezclar cambios de calendario con una aparente diferencia de construcción: T identifica 2021–2022 y W identifica 2023–2024 en entrenamiento. Agruparlos permite que ambas épocas aporten experiencia al mismo segmento de construcción. Inflación y cambios de año deben tratarse por separado, si están justificados. No se ha estimado que esta clase merezca un recargo concreto ni que la agrupación mejore la métrica.</p>',
        '<p>Si se adopta la candidata, el modelo base debería recibir la construcción armonizada y excluir el código literal redundante. Debe conservarse una ablación con etiquetas originales para medir sensibilidad. Una explicación posterior del modelo tendrá que decir “clase T/W, material sin confirmar” hasta contar con la fuente que resuelva el nombre.</p>',
        '<div class="limit"><p>El mapa se deriva retrospectivamente de X de entrenamiento disponibles para preparar 2025 y queda congelado con fecha de referencia 31-12-2024. En una simulación anterior al cambio de 2023 no puede declararse conocido sin fuente previa. Inferir una correspondencia desde X del periodo de validación es una adaptación de esquema que debe declararse; no equivale a una decisión disponible al cotizar históricamente. No se usaron siniestros ni resultados de test para elegir el mapa.</p></div>',
        '<h2>Propuesta concreta y conservación de datos</h2>',
        '<p>El campo nuevo copia brick, stone y non_standard sin agruparlos. Para T o W escribe tw_code; construction_type conserva el código normalizado previo. La copia candidata comprende 891.881 filas y agrupa 107.817 (85.556 de entrenamiento y 22.261 de test). Añadir este campo no cambia ninguna celda preexistente. Eliminarlo revierte exactamente las dos tablas, incluidos sus metadatos anteriores.</p>',
        '<p>El catálogo candidato referencia las otras nueve tablas sin modificarlas. Se conservan las 2.073 correcciones CAP01 anteriores y todos los 1.454 capitales pendientes. Los once originales, las versiones anteriores y el índice preparado activo se verificaron por SHA-256.</p>',
        f'<p>Pasaron {verification["checks_count"]} controles específicos. Se usa un algoritmo adicional de emparejamiento para comprobar el análisis; sigue siendo verificación propia asistida por IA. No hubo validación independiente ni entrenamiento, aprobación de un modelo o estimación causal de tarifa. Las figuras se generan localmente y el HTML es autocontenido; una comprobación de enlaces no acredita renderizado en un navegador.</p>',
        '<p>Referencias aplicadas: diccionario oficial archivado, IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6. Los papers son educativos; el mapa es una inferencia documentada del proyecto.</p>',
        '<p><a href="candidate/dataset_catalog.json">Catálogo candidato sin activar</a> · <a href="rules.json">Mapa y límites temporales</a> · <a href="verification.json">Verificación completa</a> · <a href="summary.json">Resumen numérico</a> · <a href="tables/case_histories.csv">Historias CSV</a> · <a href="tables/transitions_by_year.csv">Todas las transiciones CSV</a> · <a href="tables/paired_context_stability.csv">Estabilidad de atributos</a> · <a href="tables/cohort_reconciliation.csv">Conciliación de cohortes</a> · <a href="evidence/official_data_description.md">Diccionario oficial conservado</a></p>',
        '<script>const cases=' + json.dumps(case_payload,ensure_ascii=False).replace('</','<\\/') + ';',
        'const fields=' + json.dumps(display_cols) + ';',
        '''const select=document.getElementById('case');function draw(){const c=cases[Number(select.value)];document.getElementById('reason').textContent=c.reason;const container=document.getElementById('history');container.replaceChildren();const table=document.createElement('table');const head=table.createTHead().insertRow();for(const field of fields){const th=document.createElement('th');th.textContent=field;head.appendChild(th);}const body=table.createTBody();for(const row of c.rows){const tr=body.insertRow();for(const field of fields){let value=row[field];if(field.startsWith('period_')&&value)value=value.slice(0,10);const td=tr.insertCell();td.textContent=value===null?'Sin dato':String(value);}}container.appendChild(table);}select.addEventListener('change',draw);draw();</script></body></html>'''
    ]
    (out / 'informe.html').write_text('\n'.join(sections),encoding='utf-8')
