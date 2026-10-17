"""Informe CAL00 y figuras, construidos solo con la evidencia de esta revisión."""
from pathlib import Path
import html
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def n(x, decimals=0):
    return f'{x:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def table(f, cols=None):
    f = f.copy() if cols is None else f[cols].copy()
    for col in f:
        if pd.api.types.is_datetime64_any_dtype(f[col]):
            f[col] = f[col].dt.strftime('%Y-%m-%d')
        elif pd.api.types.is_float_dtype(f[col]):
            f[col] = f[col].map(lambda v: n(v, 4) if pd.notna(v) else '')
        elif pd.api.types.is_integer_dtype(f[col]):
            f[col] = f[col].map(n)
    return '<div class="scroll">' + f.to_html(index=False, escape=True, border=0, na_rep='') + '</div>'


def main(out):
    if (out / 'manifest.json').exists():
        raise RuntimeError('Closed immutable run: render a new edition, never overwrite its report.')
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    daily = pd.read_parquet(out / 'tables/daily_calendar.parquet')
    totals = daily.groupby('date')[['covered_policy_rows', 'loss_records', 'report_records']].sum()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(3, 1, figsize=(14, 11), constrained_layout=True)
    for year, color in [(2023, '#7889a0'), (2024, '#00796b')]:
        dates = pd.date_range(f'{year}-12-26', f'{year+1}-01-05')
        y = totals.reindex(dates).covered_policy_rows
        ax[0].plot(range(-5, 6), y, marker='o', color=color, label=f'Cierre de {year}')
    ax[0].axvline(0, color='#d27735', ls=':', label='31 de diciembre')
    ax[0].set_xticks(range(-5, 6), ['26 dic', '27 dic', '28 dic', '29 dic', '30 dic', '31 dic', '1 ene', '2 ene', '3 ene', '4 ene', '5 ene'])
    ax[0].set_ylabel('Pólizas cubiertas por fecha')
    ax[0].set_title('El hueco existe en los intervalos publicados: cero cobertura el 31-12-2024', loc='left')
    ax[0].legend(loc='lower left')
    for year, color in [(2021, '#abb7c5'), (2022, '#8b9eb6'), (2023, '#566d8d'), (2024, '#00796b')]:
        dates = pd.date_range(f'{year}-12-15', f'{year}-12-31')
        for a, col in [(ax[1], 'loss_records'), (ax[2], 'report_records')]:
            a.plot(range(15, 32), totals.reindex(dates)[col], marker='o', color=color, label=str(year))
    for a in ax:
        a.spines[['top', 'right']].set_visible(False)
        a.grid(axis='y', alpha=.2)
    ax[1].set_title('Siniestros por ocurrencia: el final de 2024 está truncado', loc='left')
    ax[2].set_title('Siniestros por reporte: hay 111 el 30-12-2024 y ninguno el 31', loc='left')
    for a in ax[1:]:
        a.set_xticks(range(15, 32)); a.set_xlabel('Día de diciembre'); a.set_ylabel('Expedientes observados'); a.legend(ncol=4, loc='lower left')
    fig.savefig(out / 'figures/calendario_y_siniestros.png', dpi=150)
    fig.savefig(out / 'figures/calendario_y_siniestros.svg')
    plt.close(fig)
    profile = pd.read_parquet(out / 'tables/cohort_profile.parquet')
    counts = profile[['line', 'continuities', 'consistent_renewed', 'same_customer', 'same_address', 'multiple_periods_2024']].rename(columns={
        'line': 'Ramo', 'continuities': 'Brechas', 'consistent_renewed': 'Etiqueta renewed', 'same_customer': 'Mismo cliente',
        'same_address': 'Misma dirección', 'multiple_periods_2024': 'Más de un segmento en 2024'})
    counts['Rechazo con continuidad'] = profile.continuities - profile.consistent_renewed
    scenarios = pd.read_parquet(out / 'tables/hypothetical_exposure_scenarios.parquet')
    sens = scenarios.loc[scenarios.scenario == 'bridge_all', ['line', 'rows', 'ACT365_unrounded_extra_years',
        'ACT365_row_rounded_extra_years', 'base_2024_all_row_exposure', 'denominator_increase_pct', 'fixed_observed_cost_rate_change_pct']].rename(columns={
        'line': 'Ramo', 'rows': 'Días añadidos, hipotéticos', 'ACT365_unrounded_extra_years': 'Años exactos extra',
        'ACT365_row_rounded_extra_years': 'Años extra, EXP01 a 4 decimales', 'base_2024_all_row_exposure': 'Exposición 2024 base',
        'denominator_increase_pct': 'Aumento del denominador, %', 'fixed_observed_cost_rate_change_pct': 'Cambio en coste/exposición fijo, %'})
    yearpattern = pd.read_parquet(out / 'tables/day365_pattern.parquet').rename(columns={'year': 'Año', 'day_365_date': 'Fecha del día 365',
        'rows_ending_day365': 'Filas que terminan el día 365', 'rows_ending_calendar_dec31': 'Filas con fin 31 dic', 'rows_ending_day366': 'Filas con fin en día 366'})
    annual = pd.read_parquet(out / 'tables/annual_calendar.parquet')
    summary_annual = annual.groupby('year').agg(rows=('rows', 'sum'), exposure=('exposure', 'sum'), full365=('full365', 'sum'), full366=('full366', 'sum')).reset_index()
    cases = json.loads((out / 'cases.json').read_text('utf-8'))
    payload = json.dumps(cases, ensure_ascii=False).replace('<', '\\u003c')
    opts = ''.join(f'<option value="{i}">{x["case"]["case"]}. {html.escape(x["case"]["label"])} · {x["case"]["policy_id"]}</option>' for i, x in enumerate(cases))
    all_sens = scenarios.loc[(scenarios.line == 'ALL') & (scenarios.scenario == 'bridge_all')].iloc[0]
    strict_sens = scenarios.loc[(scenarios.line == 'ALL') & (scenarios.scenario == 'bridge_consistent_renewed')].iloc[0]
    document = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión del calendario 2024 · CAL00</title><style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f2f5f7;color:#182e40;font:16px/1.65 system-ui,sans-serif}main{max-width:1350px;margin:auto;padding:28px}header{padding:28px;background:#132e41;color:white;border-radius:16px}h1{font-size:32px;line-height:1.2}h2{font-size:24px;margin:0 0 15px}h3{font-size:18px}.tag{display:inline-block;background:#cceddf;color:#124d40;border-radius:6px;padding:3px 10px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px;margin:20px 0}.card,section{background:white;padding:24px;border-radius:12px;margin-bottom:20px}.metric{font-size:30px;color:#00796b;font-weight:650}.note{border-left:4px solid #d88d47;padding:12px 18px;background:#fff6eb}.ok{border-left:4px solid #00796b;padding:12px 18px;background:#edf8f3}.scroll{overflow:auto}table{border-collapse:collapse;white-space:nowrap;width:100%;font-size:13px}th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #dbe2e8}th{background:#e9f0f4}img{width:100%;height:auto}select{width:100%;padding:12px;border:1px solid #a4b8c6;font:inherit}button{padding:9px 15px;margin:10px 8px 0 0;background:#e9f0f4;border:1px solid #a4b8c6;cursor:pointer}.muted{color:#536d7c}a{color:#006d62}code{background:#e9f0f4;padding:1px 4px}.gap{background:#fff0d6}footer{font-size:13px;color:#536d7c}li{margin-bottom:8px}
</style></head><body><main><header><span class="tag">Revisión CAL00 · ninguna corrección aplicada</span><h1>El día que falta entre 2024 y 2025</h1><p>500.245 pólizas terminan el 30 de diciembre de 2024 y continúan el 1 de enero de 2025. La evidencia favorece una convención de 365 posiciones por año; falta confirmar qué cobertura y ventana de observación pretendía el organizador.</p><p>Fuente: catálogo vigente después de DUP01. Revisión propia asistida por Codex; no es validación independiente.</p></header>
<div class="cards"><div class="card"><div class="metric">500.245</div>brechas de exactamente un día</div><div class="card"><div class="metric">497.503</div>con etiqueta de renovación coherente</div><div class="card"><div class="metric">2.742</div>declined_by_insurer con sucesor 2025</div><div class="card"><div class="metric">30 dic</div>último reporte observado; valoración descrita: 31 dic</div></div>
<section><h2>Qué se comprobó y qué sigue siendo una hipótesis</h2><p>Se reconstruyeron las adyacencias de los @@ALLROWS@@ periodos train y test, sin usar siniestros de 2025, que no están disponibles. La cohorte coincide exactamente con los IDs de la revisión D40. Se conservaron los historiales completos de estas pólizas: @@HIST@@ periodos y @@CLAIMS@@ expedientes tras DUP01.</p>@@COUNTS@@<p>No hay otras brechas positivas ni solapamientos entre filas adyacentes de una misma póliza y ramo. Las @@ENDROWS@@ filas de 2024 que terminan el 30 de diciembre tienen sucesor 2025: aquí no aparece un conjunto adicional con ese cierre sin continuidad. Las cancelaciones y bajas previas terminan antes y permanecen fuera de esta cohorte.</p><p>El cliente es el mismo en los 500.245 pares. La dirección coincide en 497.092; cambia en 3.153 pólizas de motor (3.131 con renewed y 22 con declined_by_insurer). En motor, modelo, tipo de cobertura y grupo de valor son iguales en los 200.063 pares comparados; no hay VIN para confirmar identidad física del vehículo. La continuidad del identificador puede coexistir con un cambio territorial de riesgo. Si se confirmara el día adicional, correspondería al segmento final de 2024 y su dirección, no automáticamente a la residencia de 2025. En los 500.245 pares, el contador de renovaciones aumenta en uno y new_business es falso en 2025. Los campos de cliente/dirección son datos publicados, no comprobación contra contratos.</p><div class="note">La etiqueta <code>declined_by_insurer</code> contradice el sucesor en 2.742 casos (1.513 motor, 1.010 edificios, 219 contenidos). El patrón de calendario existe también en ellos, pero su lectura contractual requiere una revisión adicional. No los convierto en renewed.</div></section>
<section><h2>El 29 de febrero existe; el corte ocurre al final del año</h2>@@PATTERN@@<p>En los cinco años, los cierres se acumulan en el día 365 desde el 1 de enero. En años comunes coincide con el 31 de diciembre; en 2024 coincide con el 30. El máximo inicio de segmento es el 29 de diciembre en 2024 y el 30 en los otros años. Es un patrón compatible con una generación limitada a 365 días, sin demostrar su código ni la intención de cobertura.</p><p>Hay @@LEAP@@ siniestros ocurridos el 29-02-2024 y cobertura en esa fecha. Por tanto, no basta explicar la base diciendo que se eliminó el día bisiesto. Un calendario de 365 días debe aclarar qué fecha representa cada posición.</p>@@ANNUAL@@<p>EXP01 calcula días inclusivos/365 y redondea por fila a cuatro decimales. Una fila 01-01-2024 a 30-12-2024 tiene 365 días y exposición 1. Eso concilia la columna con las fechas, pero deja sin resolver la omisión del día 366 del año civil.</p><img src="figures/calendario_y_siniestros.png" alt="Comparación de cobertura diaria y siniestros por ocurrencia y reporte alrededor del cierre de año"><p class="muted">En el primer panel, el punto del 31-12-2024 vale cero según los intervalos publicados. En 2025 se muestra solo cobertura, sin afirmar disponibilidad de siniestros. Los paneles inferiores cuentan expedientes observados en cada snapshot, incluidos repudiados; no son frecuencia última.</p></section>
<section><h2>Por qué los siniestros no permiten cerrar la duda</h2><p>El máximo <code>report_date</code> es @@REPORTMAX@@ y el máximo <code>loss_date</code> es @@LOSSMAX@@. Hay 111 reportes el 30 de diciembre y ninguno el 31. La ocurrencia tiene 25 expedientes el 28, 12 el 29 y cero los días 30 y 31. El retraso mínimo observado entre ocurrencia y reporte es @@MINDELAY@@ día(s).</p><p>Con retraso mínimo de un día y reportes truncados el 30, resulta compatible que las últimas ocurrencias visibles sean del 29. Esto explica por qué también falta el 30 en las ocurrencias, aun cuando ese día sí tenga cobertura publicada. No permite decidir si el día 31 fue excluido por el generador, si solo falta observación o si existió una suspensión real de cobertura.</p><p>La descripción oficial archivada dice valoración al 31-12-2024 y advierte que hay siniestros no reportados y abiertos sujetos a desarrollo. Deben distinguirse fecha de valoración, última fecha de reporte observada y horizonte de generación. La falta de una fila de siniestro no es un cero actuarial definitivo. Tampoco la presencia de reportes al día 30 prueba acceso a pérdidas del día 31.</p><p>Se volvió a asignar cada siniestro por <code>line + policy_id + loss_date dentro de [period_start, period_end]</code>; la asignación coincide con la capa DUP01. Los reportes posteriores al periodo se conservan en su periodo de ocurrencia. Los 413 expedientes anteriores a la historia no se desplazan para hacerlos encajar.</p><p><a href="tables/address_changes_summary.csv">Cambios de dirección</a> · <a href="tables/year_end_daily.csv">Conteos diarios, 2021–2024</a> · <a href="tables/last_reports.csv">Últimos reportes y sus ocurrencias</a> · <a href="evidence/official_data_description.md">Descripción oficial archivada</a></p></section>
<section id="casos"><h2>Trece historias reales para revisar la interpretación</h2><p>Se seleccionaron por su utilidad para contrastar hipótesis, sin entrenar ni consultar scores. Las trece incluyen continuidad ordinaria en cada ramo, ocurrencias del 29 de diciembre, cambios de segmento, la contradicción de renovación, un reporte tardío, el día bisiesto, una cancelación de control y un cambio de dirección de motor en la renovación. Se muestran todas sus filas y expedientes disponibles, sin completar 2025 con ceros.</p><select id="caseSelect" aria-label="Elegir historial">@@OPTIONS@@</select><div><button id="previousCase" type="button">Anterior</button><button id="nextCase" type="button">Siguiente</button></div><div id="caseBody"></div><p><a href="tables/case_index.csv">Índice y criterio de selección</a> · <a href="tables/case_policy_histories.csv">Periodos de los ejemplos</a> · <a href="tables/case_claim_histories.csv">Siniestros de los ejemplos</a></p></section>
<section><h2>Efecto hipotético sobre exposición y tarifa</h2><p>Añadir un día al último segmento de las 500.245 pólizas sumaría @@EXACT@@ años de exposición bajo ACT/365, antes de redondear por fila, o @@ROUNDED@@ según el redondeo actual EXP01. Es una sensibilidad matemática: las fechas y la exposición guardadas conservan sus valores.</p>@@SCENARIOS@@<p>Al limitar la hipótesis a los 497.503 casos con etiqueta renewed, el incremento exacto sería @@STRICT@@ años. La etiqueta por sí sola tampoco confirma cobertura. Se mantiene visible la diferencia de alcance y la contradicción de los otros 2.742 casos.</p><p>Con el mismo coste observado, aumentar el denominador total de 2024 en @@PCT@@ % reduciría coste/exposición en @@RATE@@ %. Ese movimiento aritmético no cuantifica una tarifa correcta ni la pérdida del día ausente: habría que resolver cobertura, retrasos de reporte, desarrollo, estacionalidad y el objetivo por periodo.</p><div class="note">En una fila de solo dos días, la exposición publicada es 0,0055. Tres días serían 0,0082 con EXP01, cerca de un 49,1 % más. El impacto relativo por fila puede ser grande aunque el efecto agregado sea pequeño. En una fila anual de 365 días, 366/365 redondea a 1,0027.</div><p>La base del denominador es una segunda decisión: con ACT/ACT, 366 días de 2024 representan 1 año; con ACT/365 representan 1,0027 tras redondeo. Cambiar la fecha y cambiar la base son operaciones distintas. No se debe imponer un tope de 1 manteniendo ACT/365 ni mezclar bases entre filas. La sensibilidad ACT/366 guardada es ilustrativa y no sustituye EXP01.</p><p>En frecuencia o modelos de coste con exposición como offset, el supuesto afecta la tasa por año. Para predecir coste de cada periodo de test, debe mantenerse la misma definición temporal entre entrenamiento y predicción. La prima emitida no se recalcula mecánicamente al ampliar un intervalo: faltan condiciones contractuales y reglas de prorrateo.</p><p><a href="tables/hypothetical_exposure_scenarios.csv">Escenarios aritméticos completos</a> · <a href="tables/day_count_conventions.csv">Cruce entre fechas y base anual</a></p></section>
<section><h2>Tratamiento propuesto antes de cualquier corrección</h2><ol><li>Conservar las fechas publicadas y EXP01 para el escenario base por periodo. Mantener CAL00 como marca de diagnóstico fuera del catálogo de modelado. La brecha queda abierta, no resuelta por la conciliación de exposición.</li><li>Separar los 497.503 casos de renovación coherente de los 2.742 con rechazo y continuidad. Mantener ambos conjuntos congelados por IDs y hashes, con historiales revisables; no borrar el sucesor ni alterar su etiqueta.</li><li>Antes de extender fechas, aclarar el uso de 365 posiciones, el día omitido, la última fecha de reporte, la base de exposición y las contradicciones de renovación. La lista de preguntas queda preparada; no se ha contactado al organizador.</li><li>Si se confirma cobertura hasta el 31, proponer otra capa derivada que extienda únicamente el último segmento de 2024, recalcule exposición desde fechas y guarde bitácora reversible. Comprobar cohortes, solapamientos, asignación de siniestros y consistencia de la base de años. La confirmación del calendario no valida automáticamente los rechazos contradictorios.</li></ol><p>No desplazar fechas de siniestros, inventar siniestros, introducir ceros por falta de reporte, extender bajas tempranas, repartir el día entre todos los segmentos ni recalcular prima emitida sin respaldo. Una corrección de exposición no resuelve IBNR.</p><p>Con la evidencia actual recomiendo dejar las fechas pendientes y tratar la base como periodos publicados bajo una posible convención de simulación de 365 días. La extensión al año civil completo es un escenario condicionado a la fuente, no una limpieza automáticamente justificada por la continuidad.</p></section>
<section><h2>Trazabilidad y límites de esta revisión</h2><p>Se verifican fuentes, cohorte congelada D40, adyacencias, asignación de siniestros y aritmética con un verificador separado. Las comprobaciones son propias. La revisión no certifica una interpretación contractual ni una mejora de predicción. La interfaz se verifica por su lógica; el renderizado completo en navegador solo se afirmará si existe evidencia.</p><p>Los once originales, seis tablas preparadas, claims DUP01 y el puntero activo conservan hashes. Los 2.073 ajustes CAP01, los 1.454 capitales pendientes y la propuesta CON01 conservan su estado. No hay cambios en fechas, exposición, prima, siniestros o el catálogo de datos; tampoco entrenamiento o llamadas a proveedores externos.</p><p>IAA: Documentación §2 y §§4–6 para fuente y recorrido; Gobernanza §2.8 para distinguir verificación propia; Consideraciones profesionales §3.2 y §§3.5–3.6 para explicar incertidumbre y responsabilidad. Estas referencias educativas no son certificación ni reglas del concurso.</p><p><a href="summary.json">Resumen estructurado</a> · <a href="proposal.json">CAL00 y preguntas a la fuente</a> · <a href="verification.json">Comprobaciones técnicas</a> · <a href="manifest.json">Manifiesto SHA256</a> · <a href="tables/gap_cohort.parquet">500.245 pares, evidencia Parquet</a> · <a href="tables/all_affected_policy_histories.parquet">Todos los periodos de la cohorte</a> · <a href="tables/all_affected_claim_histories.parquet">Todos sus expedientes</a></p></section>
<footer>@@RUN@@ · Comando de reproducción desde C:/dev/Hakaton: Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Revision_calendario/review_calendar.py". Cada reproducción crea otra corrida; nunca sobrescribe esta evidencia. Después, pasar la ruta de la corrida abierta a add_continuity_context.py, render_calendar.py y verify_calendar.py, en ese orden. verify_report.js recibe informe.html y una ruta nueva para interface_verification.json. El cierre requiere inspección visual real y record_calendar.py --figure-inspected; una corrida cerrada no se reescribe.</footer>
<script id="caseData" type="application/json">@@PAYLOAD@@</script><script>
const cases=JSON.parse(document.getElementById('caseData').textContent);
const select=document.getElementById('caseSelect');
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateCols=new Set(['period_start','period_end','loss_date','report_date']);
function format(k,v){if(v==null)return '';if(dateCols.has(k))return esc(String(v).slice(0,10));if(typeof v==='number')return new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(v);return esc(v);}
function grid(rows,cols){if(!rows.length)return '<p>No hay expedientes observados para esta póliza en el archivo disponible. No implica cero siniestros en 2025.</p>';return '<div class="scroll"><table><thead><tr>'+cols.map(([k,l])=>'<th>'+esc(l)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr class="'+(r.year===2024?'gap':'')+'">'+cols.map(([k,l])=>'<td>'+format(k,r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function renderCase(){const item=cases[Number(select.value)||0],c=item.case;let pcols=[['year','Año'],['row_id','row_id'],['period_start','Inicio'],['period_end','Fin'],['covered_days','Días'],['exposure','Exposición'],['renewal_decision','Decisión'],['renewal_count','Renovaciones'],['new_business','Nueva'],['customer_id','Cliente'],['address_id','Dirección'],['written_premium','Prima CU']];pcols.push(...(c.line==='motor'?[['make_model','Modelo'],['cover_type','Cobertura']]:[['sum_insured','Capital CU']]));document.getElementById('caseBody').innerHTML='<h3>'+esc(c.policy_id)+' · '+esc(c.label)+'</h3><p>'+esc(c.interpretation)+'</p><h3>Historial de periodos</h3>'+grid(item.policies,pcols)+'<h3>Siniestros disponibles</h3>'+grid(item.claims,[['claim_id','ID'],['peril','Peligro'],['loss_date','Ocurrencia'],['report_date','Reporte'],['status','Estado'],['paid_to_date','Pagado CU'],['incurred_to_date','Incurrido CU'],['recoveries','Recuperaciones CU'],['observed_net_CU','Neto observado CU'],['row_id','Periodo asignado']]);}
select.addEventListener('change',renderCase);
document.getElementById('previousCase').addEventListener('click',()=>{select.value=String((Number(select.value)+cases.length-1)%cases.length);renderCase();});
document.getElementById('nextCase').addEventListener('click',()=>{select.value=String((Number(select.value)+1)%cases.length);renderCase();});
renderCase();
</script></main></body></html>'''
    subs = {'ALLROWS': n(s['all_policy_rows']), 'HIST': n(s['all_affected_history_rows']), 'CLAIMS': n(s['all_affected_claim_rows']),
        'COUNTS': table(counts), 'ENDROWS': n(s['end_dec30_2024_rows']), 'DELTAS': html.escape(str(s['renewal_delta_counts'])),
        'PATTERN': table(yearpattern), 'ANNUAL': table(summary_annual.rename(columns={'year':'Año','rows':'Filas','exposure':'Exposición EXP01','full365':'Filas de 365 días','full366':'Filas de 366 días'})),
        'LEAP': n(s['loss_leapday_2024']), 'REPORTMAX': s['claim_max_report_date'], 'LOSSMAX': s['claim_max_loss_date'],
        'MINDELAY': n(s['claim_min_report_delay_days']), 'OPTIONS': opts, 'PAYLOAD': payload, 'SCENARIOS': table(sens),
        'EXACT': n(all_sens.ACT365_unrounded_extra_years, 6), 'ROUNDED': n(all_sens.ACT365_row_rounded_extra_years, 4),
        'STRICT': n(strict_sens.ACT365_unrounded_extra_years, 6), 'PCT': n(all_sens.denominator_increase_pct, 4),
        'RATE': n(all_sens.fixed_observed_cost_rate_change_pct, 4), 'RUN': html.escape(s['run'])}
    for token, value in subs.items():
        document = document.replace('@@' + token + '@@', str(value))
    assert '@@' not in document
    (out / 'informe.html').write_text(document, encoding='utf-8')
    print(json.dumps({'report': str(out / 'informe.html'), 'cases': len(cases), 'figure': str(out / 'figures/calendario_y_siniestros.png')}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
