"""Informe con casos, figuras e historial consultable sin conexión."""
import base64
import html
import json

import analyze_capitals as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROUTES = {
    'prior_supported': 'Apoyo de historia anterior comparable',
    'retrospective_support_only': 'Apoyo principal posterior, solo retrospectivo',
    'no_normal_same_policy_reference': 'Sin referencia normal en esta póliza',
    'context_or_continuity_review': 'Revisar contexto, faltantes o continuidad',
    'outside_extreme_screen': 'Fuera de la banda extrema'}
NOTES = {
 'E1': 'El capital de 2024 se interpone entre importes de la escala habitual de la misma dirección. Dividirlo por mil permite contrastar una trayectoria gradual. El periodo de 2025 es apoyo retrospectivo, no información disponible en enero de 2024. Las primas se muestran tal como figuran, sin anualizarlas.',
 'C1': 'La serie permite comparar ambos lados del pico. La hipótesis cambia solo la unidad aparente del capital de 2024; no implica cambiar sus siniestros o la prima. La fila posterior pertenece al test y se identifica como evidencia retrospectiva.',
 'E2': 'El salto está en 2025. Hay capitales anteriores de la misma dirección, de modo que puede estudiarse con historia conocida antes de 2025. No disponemos de un periodo 2026 que confirme una vuelta a escala. Mantener esta diferencia de evidencia.',
 'E3': 'Coinciden una mudanza y dos capitales altos consecutivos. Conservar 196.000 del domicilio anterior perdería un cambio material del objeto asegurado. La hipótesis /1000 daría 377.000 y 388.000 en la nueva dirección, que deben contrastarse con sus 400.000 y 412.000 posteriores. Una comparación que exige salto inmediato de 900–1100x puede perder el primer caso porque combina escala y mudanza.',
 'C2': 'Dos años consecutivos altos pueden dar un cociente entre ellos cercano a uno. Eso no confirma que la unidad sea correcta. Revisar todo el bloque contra el último capital anterior y el primero posterior de escala habitual, sin reemplazar ambos por el mismo valor.',
 'C3': 'El primer registro ya está en la banda extrema. La historia posterior ayuda a revisar la hipótesis, pero no prueba que ese apoyo existiera al cotizar el primer año. Para una regla retrospectiva de entrenamiento habría que declarar esta diferencia y evitar presentarla como validación temporal.',
 'C4': 'Hay un aumento temporal dentro de la banda no extrema y también una mudanza en el historial. El factor es muy inferior a mil. Puede ser una actualización del capital o un cambio de bienes, aunque no tenemos el endoso para confirmarlo. Dividirlo por mil carece de apoyo de escala.',
 'E4': 'Un capital superior a un millón CU no pertenece automáticamente a la banda extrema de edificios. La ausencia de historia impide validar el importe, pero tampoco autoriza recortarlo por ser alto. No existe un límite contractual general de un millón en los datos.'}


def table(frame):
    return frame.to_html(index=False, na_rep='Sin dato', float_format=lambda v: f'{v:,.3f}')


def image_tag(path, alt):
    return '<img alt="' + html.escape(alt) + '" src="data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode() + '">'


def main():
    out = a.ROOT / json.loads((a.BASE / 'current_run.json').read_text(encoding='utf-8'))['workspace_relative_run']
    summary = pd.read_csv(out / 'tables/summary.csv')
    cohorts = pd.read_csv(out / 'tables/cohorts.csv')
    fields = pd.read_csv(out / 'tables/field_changes.csv')
    growth = pd.read_csv(out / 'tables/growth_comparison.csv')
    sensitivity = pd.read_csv(out / 'tables/sensitivity.csv')
    cases = json.loads((out / 'cases.json').read_text(encoding='utf-8'))
    all_review, all_history = [], []
    plt.rcParams.update({'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for axis, line in zip(axes, a.THRESHOLDS):
        values = np.concatenate([pq.read_table(a.RAW / f'{p}_{line}.parquet', columns=['sum_insured']).column(0).to_numpy()
                                 for p in ['policies', 'test']])
        high = values > a.THRESHOLDS[line]
        bins = np.linspace(np.log10(values.min()), np.log10(values.max()), 100)
        axis.hist(np.log10(values), bins=bins, histtype='step', linewidth=1.5, label='Originales 2021–2025')
        axis.hist(np.log10(values[high]/1000), bins=bins, histtype='step', linewidth=1.5,
                  label='Solo banda extrema /1000 (hipótesis)')
        axis.set_yscale('log'); axis.set_xlabel('log10(capital CU)'); axis.set_ylabel('Filas, escala log')
        axis.set_title('Edificios' if line == 'buildings' else 'Contenidos'); axis.legend(fontsize=8)
        q = pq.read_table(out / 'tables' / f'extreme_review_{line}.parquet').to_pandas()
        h = pq.read_table(out / 'tables' / f'affected_policy_histories_{line}.parquet').to_pandas()
        all_review.append(q)
        display = ['line', 'policy_id', 'source_table', 'row_id', 'period_start', 'period_end', 'sum_insured',
            'what_if_div1000_CU', 'written_premium', 'customer_id', 'address_id'] + [v for v in a.FIELDS[line] if v not in ['customer_id', 'address_id']]
        all_history.append(h[display])
    fig.tight_layout(); fig.savefig(out / 'figures/bands.png', dpi=150); plt.close(fig)
    total = int(summary.rows.sum()); extremes = int(summary.extreme_rows.sum())
    parts = ['<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión de capitales</title>',
      '<style>body{font:16px/1.6 system-ui;color:#182b3c;max-width:1250px;padding:0 24px;margin:35px auto}h2{margin-top:2em}table{border-collapse:collapse;display:block;overflow:auto;font-size:13px;max-width:100%}td,th{padding:8px;border-bottom:1px solid #d7e0e7;text-align:right;white-space:nowrap}th{background:#edf3f8}img{max-width:100%}.note{padding:15px;background:#fff4db;border-left:4px solid #ba7c13}input,select,button{padding:8px;margin:5px;font:inherit}a{color:#075b9b}details{margin:12px 0}code{background:#edf1f4}nav{display:flex;flex-wrap:wrap;gap:18px}.case{border-top:1px solid #aac2d5;margin-top:36px;padding-top:16px}</style>',
      '<h1>Capitales: historia, casos y criterios para una posible corrección</h1>',
      f'<p>Se compararon {total:,} periodos de edificios y contenidos de 2021–2025. Hay {extremes:,} filas en la banda extrema ({100*extremes/total:.3f}%). Ningún capital se cambió. Las cifras monetarias son CU ficticias, no COP ni dólares.</p>',
      '<p class="note">La evidencia apoya investigar una escala multiplicada por mil. Cada valor /1000 es una hipótesis diagnóstica, pendiente de decisión. Las categorías de revisión no son probabilidades de error, correcciones aprobadas o etiquetas verificadas por el organizador.</p>',
      '<nav><a href="#overview">Panorama</a><a href="#criteria">Criterios</a><a href="#cases">Casos concretos</a><a href="#search">Consultar historias</a><a href="#limits">Límites y evidencia</a></nav>',
      '<h2 id="overview">Separación de escalas y recorrido temporal</h2>',
      table(summary[['table','rows','extreme_rows','extreme_pct','min_extreme_CU','max_non_extreme_CU','extreme_share_of_capital_sum_pct']]),
      '<p>La banda extrema se seleccionó con los umbrales diagnósticos previos: más de 10 millones CU en edificios y más de 1 millón en contenidos. Se muestran los mínimos de esa banda y los máximos del resto para comprobar la separación real. Esos umbrales no son límites de una póliza. La última columna indica cuánto pesan las filas extremas en la suma de capitales, que tampoco es una estimación de coste de siniestros.</p>',
      image_tag(out / 'figures/bands.png','Distribución de capitales originales e hipótesis de escala'),
      '<p>Que /1000 devuelva valores a una zona común de la distribución es evidencia de plausibilidad. No identifica por sí solo la intención de cada contrato. Una vivienda o un conjunto de bienes poco usual puede tener un capital alto; el diccionario no fija un máximo universal.</p>',
      '<h3>Continuidad con riesgo registrado comparable</h3>', table(growth),
      '<p>Los cocientes comparan la fila actual con la referencia anterior no extrema. Para el grupo normal se exige además que esa referencia sea la fila inmediatamente anterior; campos conocidos e iguales y separación de inicios de hasta 400 días. p50 es la mediana, no un factor oficial de indexación. En las filas extremas se presentan cocientes originales e hipotéticos. No se ha impuesto un incremento fijo del 2% o 3% a ninguna póliza.</p>',
      '<h3>Cuánto apoyo hay antes y después</h3>', table(cohorts.assign(route=cohorts.route.map(ROUTES))),
      '<p>La categoría de apoyo anterior exige todos los campos de contexto definidos conocidos e iguales y que el capital /1000 esté entre 0,90 y 1,10 de la referencia anterior. El apoyo posterior puede usar años posteriores o test: sirve para investigación retrospectiva, no como dato disponible al cotizar una fila anterior. Las demás categorías conservan carencias de contexto o de historia.</p>',
      '<h3>Sensibilidad de la propuesta</h3>',table(sensitivity),
      '<p>La tolerancia se aplica al cociente hipotético. No se ajustó usando siniestros o leaderboard. Si una propuesta cambia sustancialmente al pasar de 5% a 10% o 20%, revisar esos casos antes de fijar una regla. Los campos exigidos y las comparaciones están en protocol.json.</p>',
      '<details><summary>Cambios de contexto y campos no observados</summary>' + table(fields) + '<p>La comparación de construcción ignora únicamente mayúsculas y minúsculas. Una abreviatura no definida no se equipara a un material. Dos faltantes no cuentan como evidencia de un mismo riesgo confirmado.</p></details>']
    premium_rows = []
    for line in a.THRESHOLDS:
        values = json.loads((out / 'tables' / f'premium_corroboration_{line}.json').read_text(encoding='utf-8'))
        premium_rows.append({'line':line,**{k:v for k,v in values.items() if k!='note'}})
    parts += ['<h3>La prima como comprobación complementaria</h3>',table(pd.DataFrame(premium_rows)),
      '<p>Solo se comparan periodos de al menos 300 días, duración relativa entre 0,95 y 1,05 y contexto anterior comparable. La prima es la cobrada bajo la tarificación vigente según el diccionario; no es coste último. Su base temporal no está suficientemente documentada para anualizarla en este ejercicio. Un cambio moderado de prima frente a un salto de capital de mil veces refuerza investigar la unidad, pero no prueba que el capital sea incorrecto.</p>',
      '<h2 id="criteria">Cuándo tendría sentido corregir la escala</h2>',
      '<ol><li>Identificar un problema de unidad: confirmar en origen, o declarar expresamente una inferencia del proyecto respaldada por varias evidencias. El tamaño del capital por sí solo no basta.</li><li>Comprobar el mismo interés asegurado: cliente, dirección, cobertura, franquicias y características declaradas. Revisar por separado endosos, mudanzas y cambios en bienes. Si faltan datos, registrar esa carencia.</li><li>Contrastar la hipótesis /1000 con capitales comparables. Preferir una referencia anterior conocida. Si la evidencia decisiva es posterior, etiquetar la corrección como retrospectiva y diseñar aparte su uso temporal.</li><li>Revisar el bloque completo. Dos años consecutivos con la misma escala pueden ocultarse en una razón cercana a uno; una vuelta a la escala habitual no debe dividirse de nuevo.</li><li>Preservar el cambio real del capital. Dividir por mil no significa congelar en el valor anterior, imputar la mediana o imponer indexación. En una mudanza pueden coexistir aumento real y error de escala.</li><li>Antes de aplicar: aprobar filas y criterio, guardar valor anterior/nuevo, evidencia y motivo, comprobar idempotencia y reversión, y comparar resultados con/sin corrección. La decisión actual conserva todos los valores.</li></ol>',
      '<p>Para filas nuevas sin historia comparable, mantener la bandera y pedir evidencia del origen o usar una sensibilidad separada. No recortar a un percentil, dividir todos los importes altos o eliminar estas pólizas por defecto. Los siniestros y los scores quedan fuera de la decisión de unidad.</p>',
      '<p>El capital es un límite contractual y una variable de magnitud del riesgo. Una unidad equivocada puede distorsionar segmentación y aprendizaje de severidad. Dividir el capital por mil no implica dividir por mil la prima de riesgo, los pagos ni el coste último: ese efecto requiere un modelo y condiciones de cobertura que no se han evaluado aquí.</p>',
      '<h2 id="cases">Historias concretas</h2>']
    for case in cases:
        line = case['line']
        selected = pq.read_table(out / 'tables' / f'case_histories_{line}.parquet').to_pandas()
        h = selected[selected.policy_id.eq(case['policy_id'])].copy()
        h['start'] = h.period_start.dt.strftime('%Y-%m-%d')
        h['end'] = h.period_end.dt.strftime('%Y-%m-%d')
        h['ruta'] = h.review_route.map(ROUTES)
        fig, ax = plt.subplots(figsize=(10, 3.2))
        x = np.arange(len(h)); ax.plot(x, h.sum_insured, 'o-', color='#b14439', label='Capital original')
        high = h.extreme_band_screen
        if high.any():
            ax.scatter(x[high], h.loc[high,'what_if_div1000_CU'], marker='D', s=65, color='#286ab0',
                       label='Hipótesis /1000; no aplicada', zorder=4)
            ax.set_yscale('log')
        ax.set_xticks(x, h.start, rotation=20); ax.set_ylabel('Capital CU' + (' (escala log)' if high.any() else ''))
        ax.set_title(case['case'] + ': ' + case['policy_id']); ax.legend(fontsize=8)
        fig.tight_layout(); path=out/'figures'/f'{case["case"]}.png'; fig.savefig(path,dpi=140); plt.close(fig)
        parts += [f'<div class="case" id="case-{case["case"]}"><h3>{case["case"]}. {html.escape(case["title"])}: {case["policy_id"]}</h3>',
          '<p>'+html.escape(NOTES.get(case['case'], 'No hay ninguna referencia de escala habitual en esta póliza. La distribución puede hacer plausible una hipótesis /1000, pero la historia no puede confirmarla. Mantener el caso abierto y solicitar evidencia de unidad u objeto asegurado.'))+'</p>',
          image_tag(path,case['title']),
          table(h[['source_table','row_id','start','end','sum_insured','what_if_div1000_CU','address_id','written_premium','ruta']]),
          '<details><summary>Contexto del contrato y del inmueble, sin asumir estabilidad de campos no fechados</summary>',
          table(h[['row_id']+a.FIELDS[line]+['property_type','bedrooms','listed_building','year_built','region']]), '</details></div>']
    q = pd.concat(all_review,ignore_index=True)
    hist = pd.concat(all_history,ignore_index=True)
    protected = json.loads((out / 'protected_hashes_before.json').read_text(encoding='utf-8'))
    derived_path = next(a.ROOT / path for path in protected if '/Limpieza/runs/' in path)
    old_run = derived_path.parent.parent
    old_queues = pd.concat([pq.read_table(old_run / 'tables' / f'capital_review_{line}.parquet').to_pandas()
                            for line in a.THRESHOLDS],ignore_index=True)
    old_extreme_count = int(old_queues.high_amount_screen.sum())
    a.save(out / 'screening_reconciliation.json', {'previous_D32_review_rows':len(old_queues),
        'previous_review_rows_in_extreme_band':old_extreme_count,
        'previous_other_review_rows':len(old_queues)-old_extreme_count,
        'current_extreme_rows':len(q),
        'note':'Earlier queue also flagged later normal rows after an extreme capital; those are not additional capitals to divide.'})
    qcols = ['line','policy_id','row_id','source_table','sum_insured','what_if_div1000_CU','review_route']
    queue_json = q[qcols].to_json(orient='records').replace('<','\\u003c')
    history_json = hist.to_json(orient='records',date_format='iso').replace('<','\\u003c')
    parts += [f'<p class="note">Relación con la revisión D32: sus {len(old_queues):,} filas incluían {old_extreme_count:,} de banda extrema y {len(old_queues)-old_extreme_count:,} filas adicionales, principalmente vueltas a escala habitual. Este informe centra la posible escala incorrecta en {len(q):,} importes altos. Ninguno de los dos recuentos equivale a errores confirmados.</p>',
      '<h2 id="search">Consultar las pólizas de la banda extrema</h2>',
      '<p>Buscar por policy_id o row_id. Cada botón abre todos los periodos observados de la póliza. Las hipótesis no cambian los importes originales. La tabla presenta hasta 50 coincidencias; afinar la búsqueda para localizar una fila.</p>',
      '<input id="query" placeholder="Póliza o fila"><select id="line"><option value="">Ambos ramos</option><option>buildings</option><option>contents</option></select><select id="route"><option value="">Todas las categorías</option>'+''.join('<option value="'+k+'">'+v+'</option>' for k,v in ROUTES.items() if k!='outside_extreme_screen')+'</select><p id="count"></p><div id="queue"></div><h3 id="selectedTitle">Seleccionar una póliza</h3><div id="history"></div>',
      '<h2 id="limits">Evidencia, uso temporal y límites</h2><p>Los originales y los derivados D32 están protegidos por hashes antes y después. Este informe no escribe datasets de pólizas corregidas. La verificación técnica propia se guarda en verification.json después de generar el informe. La revisión humana sigue pendiente. No hubo llamadas a Jev, entrenamiento, envíos o publicación.</p>',
      '<p>Las direcciones describen un maestro sin vigencias históricas; no hay superficie, coste de reconstrucción, moneda alternativa o endosos documentales para confirmar la unidad. El indicador de construcción puede tener vocabulario pendiente. Una coincidencia de campos apoya comparabilidad del riesgo registrado, sin demostrar que todo el contrato real permaneció igual.</p>',
      '<p>Los apoyos posteriores y el test permiten inspección forense de X. No son una reproducción de lo que se sabía antes de cada año, ni etiquetas de verdad. Si se decide corregir más adelante, separar evidencia retrospectiva de una regla aplicable con datos disponibles al cotizar. No asumir que el patrón sintético será idéntico en la segunda semana.</p>',
      '<p>Revisar retrospectivamente 2021 con historia disponible hasta diciembre de 2024 puede ser compatible con preparar un pronóstico de 2025. Para simular un pronóstico anterior en validación temporal, reconstruir la revisión usando solo información hasta ese corte. Usar características del test 2025 para apoyar una reparación histórica es otra decisión, transductiva, que tendría que declararse y evaluarse por separado.</p>',
      '<p>Referencias: diccionario oficial archivado, D30–D32; IAA Documentación §2, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6. El análisis y la propuesta fueron generados por Codex con comprobaciones de código; no se presentan como validación independiente.</p>',
      '<p><a href="protocol.json">Protocolo</a> · <a href="verification.json">Verificación</a> · <a href="tables/extreme_review_buildings.csv">Cola edificios CSV</a> · <a href="tables/extreme_review_contents.csv">Cola contenidos CSV</a> · <a href="tables/case_histories_buildings.csv">Casos edificios CSV</a> · <a href="tables/case_histories_contents.csv">Casos contenidos CSV</a></p>',
      '<script>const rows='+queue_json+';const histories='+history_json+';const routes='+json.dumps(ROUTES,ensure_ascii=False)+';',
      '''const esc=v=>String(v??'Sin dato').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      const fmt=v=>typeof v==='number'?v.toLocaleString('es-CO',{maximumFractionDigits:4}):esc(v);
      function tab(data,cols){return '<table><thead><tr>'+cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+data.map(r=>'<tr>'+cols.map(c=>'<td>'+fmt(r[c])+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
      function show(policy,line){const h=histories.filter(r=>r.policy_id===policy&&r.line===line);document.getElementById('selectedTitle').textContent=line+' / '+policy;const cols=['source_table','row_id','period_start','period_end','sum_insured','what_if_div1000_CU','written_premium','address_id','customer_id'];const detail=[...new Set(h.flatMap(r=>Object.keys(r)))].filter(k=>!cols.includes(k)&&!['line','policy_id'].includes(k));document.getElementById('history').innerHTML=tab(h,cols)+ '<details><summary>Ver campos del riesgo</summary>'+tab(h,['row_id',...detail])+'</details>';}
      function update(){const s=document.getElementById('query').value.toLowerCase();const l=document.getElementById('line').value;const route=document.getElementById('route').value;const filtered=rows.filter(r=>(!l||r.line===l)&&(!route||r.review_route===route)&&(!s||(r.policy_id+' '+r.row_id).toLowerCase().includes(s)));document.getElementById('count').textContent=filtered.length+' filas; se muestran '+Math.min(50,filtered.length);const selected=filtered.slice(0,50).map(r=>({...r,categoria:routes[r.review_route]}));document.getElementById('queue').innerHTML=tab(selected,['line','policy_id','row_id','source_table','sum_insured','what_if_div1000_CU','categoria']);const trs=document.getElementById('queue').querySelectorAll('tbody tr');trs.forEach((tr,i)=>{const td=document.createElement('td');const b=document.createElement('button');b.textContent='Ver historial';b.addEventListener('click',()=>show(selected[i].policy_id,selected[i].line));td.appendChild(b);tr.appendChild(td)});}
      ['query','line','route'].forEach(id=>document.getElementById(id).addEventListener('input',update));update();
      </script></html>''']
    (out / 'informe.html').write_text('\n'.join(parts),encoding='utf-8')
    print(str(out/'informe.html'))


if __name__ == '__main__':
    main()
