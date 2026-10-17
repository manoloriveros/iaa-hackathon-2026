"""Informe local REN00: gráficos, casos y explorador de la cohorte completa."""
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


def n(x, d=0):
    return f'{x:,.{d}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def table(f):
    f = f.copy()
    for col in f:
        if pd.api.types.is_float_dtype(f[col]):
            f[col] = f[col].map(lambda v: n(v, 2) if pd.notna(v) else '')
        elif pd.api.types.is_integer_dtype(f[col]):
            f[col] = f[col].map(n)
    return '<div class="scroll">' + f.to_html(index=False, border=0, escape=True, na_rep='') + '</div>'


def main(out):
    assert not (out / 'manifest.json').exists(), 'Closed immutable run; create an edition.'
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    data = json.loads((out / 'explorer_data.json').read_text('utf-8'))
    annual = pd.read_parquet(out / 'tables/decision_successors_all_years.parquet')
    d = annual.loc[annual.renewal_decision.eq('declined_by_insurer')].copy()
    profile = pd.read_parquet(out / 'tables/cohort_profile.parquet')
    total = profile.loc[profile.line.eq('ALL')].iloc[0]
    names = {'motor': 'Motor', 'buildings': 'Edificios', 'contents': 'Contenidos', 'ALL': 'Total'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), constrained_layout=True)
    for line, color in [('motor', '#00796b'), ('buildings', '#b66932'), ('contents', '#586fa3')]:
        x = d.loc[d.line.eq(line)].sort_values('year')
        ax[0].plot(x.year, x.successor_pct, marker='o', color=color, label=names[line])
    ax[0].set_xticks([2021, 2022, 2023, 2024]); ax[0].set_ylim(0, 105)
    ax[0].set_ylabel('% con periodo posterior observado'); ax[0].set_xlabel('Año de la fila marcada como rechazada')
    ax[0].set_title('La etiqueta no se comporta como baja definitiva', loc='left', fontsize=13)
    ax[0].legend(loc='lower left'); ax[0].grid(axis='y', alpha=.2)
    values = [total.preceding_row_count_share_pct, total.preceding_row_exposure_share_pct, total.preceding_row_cost_share_pct]
    bars = ax[1].barh(['Filas de 2024', 'Exposición de 2024', 'Coste neto observado de 2024'], values,
                     color=['#829aaa', '#829aaa', '#00796b'])
    for b, v in zip(bars, values):
        ax[1].text(v + .6, b.get_y() + b.get_height() / 2, n(v, 2) + ' %', va='center')
    ax[1].set_xlim(0, max(values) * 1.3); ax[1].set_xlabel('% del total 2024, tres ramos')
    ax[1].set_title('Qué se retiraría al borrar las 2.742 filas', loc='left', fontsize=13)
    ax[1].invert_yaxis()
    for a in ax:
        a.spines[['top', 'right']].set_visible(False)
    fig.savefig(out / 'figures/rechazos_continuidad_y_coste.png', dpi=150)
    fig.savefig(out / 'figures/rechazos_continuidad_y_coste.svg')
    plt.close(fig)
    p = profile[['line', 'policies', 'same_customer', 'changed_address', 'test_2025_rows', 'last_2024_net_CU', 'no_observed_claims_any_2024']].copy()
    p.line = p.line.map(names)
    p = p.rename(columns={'line': 'Ramo', 'policies': 'Pólizas', 'same_customer': 'Mismo cliente', 'changed_address': 'Cambia dirección',
        'test_2025_rows': 'Filas test 2025', 'last_2024_net_CU': 'Neto observado, último segmento CU', 'no_observed_claims_any_2024': 'Sin siniestro observado 2024'})
    dd = d[['line', 'year', 'rows', 'next_year', 'no_observed_successor', 'successor_pct']].copy()
    dd.line = dd.line.map(names)
    dd = dd.rename(columns={'line': 'Ramo', 'year': 'Año', 'rows': 'Filas declined', 'next_year': 'Con sucesor año siguiente',
        'no_observed_successor': 'Sin sucesor observado', 'successor_pct': 'Con sucesor, %'})
    sen = pd.read_parquet(out / 'tables/exclusion_sensitivity_NOT_APPLIED.parquet')
    st = sen[['hypothetical_scope', 'rows_excluded', 'observed_net_removed_CU', 'exposure_removed', 'observed_rate_change_pct']].rename(columns={
        'hypothetical_scope': 'Hipótesis de borrado, NO aplicada', 'rows_excluded': 'Filas retiradas', 'observed_net_removed_CU': 'Neto retirado CU',
        'exposure_removed': 'Exposición retirada', 'observed_rate_change_pct': 'Cambio en neto/exposición, %'})
    fields = pd.read_parquet(out / 'tables/endpoint_field_comparison.parquet')
    shown = fields.loc[fields.field.isin(['customer_id', 'address_id', 'voluntary_excess', 'compulsory_excess', 'make_model',
        'cover_type', 'vehicle_value_group', 'construction_type', 'sum_insured', 'occupancy', 'tenure', 'security_level'])].copy()
    shown.line = shown.line.map(names)
    shown = shown.rename(columns={'line': 'Ramo', 'field': 'Campo', 'policies': 'Pares', 'both_observed': 'Ambos informados',
        'same_when_observed': 'Iguales informados', 'different_when_observed': 'Diferentes informados', 'both_missing': 'Ambos ausentes',
        'missing_to_observed': 'Ausente→informado', 'observed_to_missing': 'Informado→ausente'})
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    opts = ''.join(f'<option value="{html.escape(x["policy_id"])}">{x["case"]}. {html.escape(x["label"])} · {x["policy_id"]}</option>' for x in data['cases'])
    template = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rechazos con continuidad · REN00</title><style>
*{box-sizing:border-box}:root{color-scheme:light}body{margin:0;background:#f2f5f7;color:#183243;font:16px/1.65 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:28px}header{background:#15374b;color:white;padding:30px;border-radius:14px}h1{font-size:32px;line-height:1.2}h2{font-size:24px;margin-top:0}h3{font-size:18px}.tag{background:#d6efe5;color:#165447;padding:5px 12px;border-radius:6px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin-top:20px}.card,section{background:white;border-radius:12px;padding:24px;margin-bottom:22px}.metric{font-size:29px;font-weight:650;color:#00796b}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:13px}th,td{padding:9px 11px;border-bottom:1px solid #dce5eb;text-align:left}th{background:#eaf0f4}.note{border-left:4px solid #b86930;background:#fff5e8;padding:13px 18px}.ok{border-left:4px solid #00796b;background:#eef8f3;padding:13px 18px}a{color:#006e62}img{width:100%;height:auto}input,select{padding:11px;width:100%;font:inherit;border:1px solid #9db2c1;background:white;margin-bottom:12px}button{padding:8px 15px;margin-right:8px;border:1px solid #9db2c1;background:#eaf0f4;cursor:pointer}code{background:#eaf0f4;padding:1px 4px}.declined{background:#fff0d5}.test{background:#edf6ff}.muted,footer{color:#516d7e;font-size:14px}li{margin-bottom:9px}
</style></head><body><main><header><span class="tag">REN00 · propuesta de tratamiento, sin cambios</span><h1>Pólizas rechazadas que siguen en cartera</h1><p>Se revisan las 2.742 pólizas identificadas en D43 y sus historiales completos. Las fechas quedan pendientes por instrucción del participante. El catálogo activo conserva DUP01.</p><p>La evidencia respalda conservar pólizas y siniestros y dejar la semántica de <code>declined_by_insurer</code> en revisión. No se ha corregido la etiqueta ni confirmado el motivo del rechazo.</p></header>
<div class="cards"><div class="card"><div class="metric">2.742</div>pólizas con rechazo 2024 y sucesor 2025</div><div class="card"><div class="metric">@@TESTROWS@@</div>filas de test de esas pólizas, incluidas sus divisiones intranuales</div><div class="card"><div class="metric">@@COST@@ CU</div>neto observado en sus últimos segmentos 2024</div><div class="card"><div class="metric">@@NOCLAIM@@</div>sin siniestros observados con ocurrencia en 2024</div></div>
<section><h2>Qué significa la contradicción</h2><p>El diccionario describe <code>declined_by_insurer</code> como rechazo del asegurador y define <code>renewal_count</code> como renovaciones previas. Sin embargo, estas 2.742 filas terminan el 30-12-2024 y tienen sucesor el 01-01-2025, conservan cliente, aumentan el contador en uno y tienen <code>new_business=false</code> en el sucesor. Existe continuidad de los registros; el día 31 sigue siendo un pendiente separado de calendario.</p>@@PROFILE@@<p>Hay 22 cambios de dirección, todos de motor. Los otros 2.720 pares conservan la dirección. Modelo, cobertura y grupo de valor de motor permanecen iguales en los pares informados comparados. Sin un identificador físico de vehículo no puede probarse identidad completa del riesgo. Los cambios de capital, franquicia y otros campos se muestran abajo y se conservan como publicados.</p><p>Se revisaron @@HP@@ periodos y @@HC@@ expedientes de estas pólizas, sobre seis tablas de pólizas/test y claims vigente después de DUP01. Se reconstruyó la cohorte desde las adyacencias de toda la cartera y coincide con los IDs congelados de D43.</p><div class="note">La existencia de un sucesor no permite sustituir automáticamente la etiqueta por renewed: podría haber una decisión preliminar, una reversión, otra oferta o un indicador generado sin efecto sobre la permanencia. Faltan motivos, fecha de decisión, ofertas y versiones para distinguir esas explicaciones.</div></section>
<section><h2>La incoherencia se repite en años anteriores</h2>@@ANNUAL@@<p>En 2024 hay @@DECLINED2024@@ filas declined_by_insurer: 2.742 tienen sucesor 2025 y @@NONEXT@@ no lo tienen en los archivos. Por tanto, la etiqueta no reproduce de forma consistente la salida de cartera. Dentro de la cohorte, @@REPEATED@@ pólizas tienen más de un rechazo registrado, y @@THREE@@ llegan a tres.</p><p>«Sin sucesor observado» describe los archivos disponibles; no acredita por sí mismo una baja contractual ni su causa. Las cohortes de cada año tienen su propia selección y exposición; estos porcentajes no son probabilidades estimadas de retención para una población externa.</p><img src="figures/rechazos_continuidad_y_coste.png" alt="Porcentajes de rechazos con sucesor por año y concentración de coste en la cohorte"><p class="muted">El panel derecho compara exclusivamente los 2.742 últimos segmentos de 2024 con todos los segmentos de 2024. El coste es incurrido neto aceptado observado al corte, sujeto a desarrollo y falta de reporte.</p></section>
<section><h2>Siniestros, severidad y selección de la muestra</h2><p>Los últimos segmentos 2024 contienen @@RECORDS@@ expedientes: @@ACCEPTED@@ aceptados (open/closed) y @@REPUDIATED@@ repudiated. Su incurrido neto aceptado es @@COST@@ CU. La reserva de caso de los expedientes abiertos de esos segmentos suma @@RESERVE@@ CU; está incluida en el incurrido, no se añade otra vez.</p><p>La cohorte representa @@ROWSHARE@@ % de las filas de 2024 y @@EXPSHARE@@ % de la exposición, pero @@COSTSHARE@@ % del coste neto observado. El campo está muy asociado a pérdidas elevadas en este snapshot. No se identifica una regla causal ni un umbral universal: hay @@NOCLAIM@@ pólizas sin siniestros observados en todo 2024 y también renewed con costes muy altos.</p><p><code>declined_by_insurer</code> pertenece a la póliza. <code>repudiated</code> pertenece al siniestro. El rechazo de renovación no revierte pagos o reservas de siniestros cubiertos del periodo anterior. El objetivo previsto sigue excluyendo los repudiated por su propio estado, preservándolos para conciliación.</p><p>La última ocurrencia disponible es el 29-12-2024 y el último reporte el 30-12-2024. «Sin siniestro observado» no equivale a ausencia de pérdidas últimas ni explica el motivo del rechazo. Los expedientes se asignan por ocurrencia dentro del intervalo inclusivo; los reportes posteriores se mantienen asociados al segmento de ocurrencia.</p>@@SENSITIVITY@@<p>Estas dos simulaciones de borrado muestran la selección que introduciría excluir contratos por una decisión asociada con pérdidas del propio periodo. Conservan un numerador observado al corte, no estiman el coste último, una tarifa correcta o rendimiento predictivo. Ninguna exclusión se aplicó.</p></section>
<section><h2>Comparación de los campos al renovar</h2>@@FIELDS@@<p>Se separa diferencia de valores informados de aparición/desaparición de un dato. Dos ausencias no acreditan estabilidad del riesgo. La tabla completa incluye edad, uso, telemática y otros campos; una variación de edad o capital entre años no es por sí sola un error.</p><p>La prima emitida y la exposición de cada segmento se muestran en los historiales. No se interpreta automáticamente la diferencia de prima como recargo por rechazo: pueden cambiar duración, riesgo y condiciones; la unidad exacta de prima y su prorrateo siguen pendientes. Los 1.454 capitales pendientes conservan sus valores y no se infiere un límite de cobertura desde estos ejemplos.</p><p><a href="tables/endpoint_field_comparison.csv">Comparación completa por campo</a> · <a href="tables/claim_cost_by_decision_year.csv">Coste y exposición por decisión y año</a></p></section>
<section id="historias"><h2>Doce casos y explorador de las 2.742 pólizas</h2><p>Los ejemplos se eligieron para contrastar interpretaciones, con dos controles fuera de la cohorte. Puede buscar cualquier policy_id del conjunto; cada vista muestra todo su historial publicado y todos sus expedientes disponibles. No hay siniestros de 2025 en la fuente.</p><label for="example">Casos explicados</label><select id="example">@@OPTIONS@@</select><label for="search">Buscar póliza de la cohorte</label><input id="search" placeholder="Por ejemplo B00134306 o motor" autocomplete="off"><select id="policy" aria-label="Póliza de la cohorte"></select><p id="matches" class="muted"></p><div id="caseBody"></div><noscript><p>El explorador requiere JavaScript. Los CSV siguientes permiten revisar los mismos historiales.</p></noscript><p><a href="tables/case_index.csv">Criterios de los doce ejemplos</a> · <a href="tables/cohort_and_control_source_histories.csv">Todos los periodos y controles</a> · <a href="tables/cohort_and_control_claim_histories.csv">Todos los expedientes y controles</a> · <a href="tables/frozen_cohort.csv">Lista congelada de los 2.742 pares</a></p></section>
<section><h2>Hipótesis que la evidencia permite evaluar</h2><div class="scroll"><table><thead><tr><th>Hipótesis</th><th>Evidencia y límite</th></tr></thead><tbody><tr><td>Rechazo definitivo con salida automática</td><td>No describe estos registros: hay sucesores en todos los años revisados, incluso rechazos repetidos.</td></tr><tr><td>Recomendación de suscripción o etiqueta generada sin propagación</td><td>Compatible con recurrencia y asociación con severidad. No se dispone del código generador o motivo para confirmarlo.</td></tr><tr><td>Decisión preliminar, revertida o nueva oferta</td><td>Posible, pero faltan fecha, versión y oferta. No se puede elegir entre estas lecturas.</td></tr><tr><td>Reciclaje de ID para otra persona</td><td>Los 2.742 pares mantienen cliente y contador de renovación; no se observa respaldo para esta explicación en la cohorte.</td></tr><tr><td>El rechazo significa que todos sus siniestros son repudiados</td><td>Son campos diferentes; la gran mayoría de expedientes de esos segmentos son aceptados.</td></tr></tbody></table></div></section>
<section><h2>Tratamiento propuesto REN00</h2><ol><li>Conservar pólizas train/test, fechas, exposición, primas y siniestros. Mantener el campo literal para auditoría, con estado semántico pendiente. Los 2.742 pares quedan congelados por IDs y hashes en esta evidencia; no se activa ninguna columna ni filtro.</li><li>Mantener <code>renewal_decision</code> fuera de los predictores de tarifa, como ya establece el protocolo 1.3: es un resultado del periodo y no está en test. También quedan fuera REN00, la presencia de sucesor y los diagnósticos de pérdidas. El uso de una decisión del año anterior requeriría acreditar significado y disponibilidad; no se incorpora por inferencia.</li><li>Conservar todas las @@TESTROWS@@ filas 2025 de estas pólizas para futuras predicciones. No imponer predicción cero por el rechazo 2024. Mantener la asignación de siniestros por loss_date y el tratamiento por estado del expediente; conservar componentes de pagado, reserva y recuperación.</li><li>Preguntar a la fuente qué significa el rechazo, cuándo queda firme, si admite reversión y si afecta la generación de periodos futuros. Sin respuesta, declarar la limitación de semántica. Las preguntas quedan guardadas; no se ha enviado ningún mensaje.</li><li>Si más adelante se autoriza una normalización, preferir una columna separada de auditoría con estado «contradictorio/no confirmado», conservando la decisión fuente. Una corrección a renewed necesitaría confirmación explícita, una cohorte aprobada y bitácora reversible. La continuidad observada podría servir para otra pregunta de retención con su propio corte, sin reemplazar el dato oficial.</li></ol><p>Para tarifa, la cartera observada incluye estos riesgos y sus pérdidas. Excluirlos por la etiqueta cambiaría la población de aprendizaje y retiraría desproporcionadamente siniestros graves. El coste último y la disponibilidad de información se tratan con el protocolo de desarrollo y F0/F1, no mediante un borrado de estas pólizas.</p><div class="ok">Las fechas permanecen pendientes. REN00 no extiende cobertura, no recalcula EXP01 y no resuelve CAL00.</div></section>
<section><h2>Evidencia y alcance real</h2><p>Revisión propia asistida por Codex. Se comparan fuentes, cohorte D43, adyacencias históricas, importes en céntimos, asignación temporal, historiales completos y conservación por hash. El explorador tiene una prueba de lógica para los doce ejemplos y cada una de las 2.742 pólizas; eso no acredita renderizado real en navegador ni validación independiente.</p><p>IAA Documentación §2 y §§4–6: recorrido y reproducción; Gobernanza §2.8: procedencia de la verificación; Consideraciones profesionales §3.2, §3.3 y §§3.5–3.6: interpretación, selección y responsabilidad humana. Son referencias educativas priorizadas por el proyecto.</p><p><a href="summary.json">Resumen</a> · <a href="proposal.json">REN00 y preguntas</a> · <a href="verification.json">Comprobaciones técnicas</a> · <a href="interface_verification.json">Lógica del explorador</a> · <a href="manifest.json">Manifiesto de evidencia</a></p></section><footer>@@RUN@@<p>Desde C:/dev/Hakaton: Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Revision_rechazos/review_declines.py" crea otra corrida. Pasar su ruta a render_declines.py y verify_declines.py. verify_report.js recibe informe.html y una ruta nueva para interface_verification.json. Cerrar con record_declines.py y --figure-inspected después de una inspección visual real. No sobrescribir una corrida cerrada.</p></footer>
<script id="reviewData" type="application/json">@@DATA@@</script><script>
const data=JSON.parse(document.getElementById('reviewData').textContent);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dates=new Set(['period_start','period_end','loss_date','report_date']);
function fmt(k,v){if(v==null)return '';if(dates.has(k))return esc(String(v).slice(0,10));if(typeof v==='number')return new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(v);return esc(v);}
function grid(rows,cols){if(!rows.length)return '<p>No hay expedientes observados en el archivo disponible para esta póliza. No implica ausencia de pérdidas últimas ni de siniestros 2025.</p>';return '<div class="scroll"><table><thead><tr>'+cols.map(([k,l])=>'<th>'+esc(l)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr class="'+(r.renewal_decision==='declined_by_insurer'?'declined':r.year===2025?'test':'')+'">'+cols.map(([k,l])=>'<td>'+fmt(k,r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function showPolicy(pid){const h=data.histories[pid];if(!h){document.getElementById('caseBody').innerHTML='<p>Sin coincidencias en la cohorte.</p>';return;}const example=data.cases.find(x=>x.policy_id===pid);const line=h.policies[0].line;let cols=[['year','Año'],['row_id','row_id'],['period_start','Inicio'],['period_end','Fin'],['covered_days','Días'],['exposure','Exposición'],['renewal_decision','Decisión publicada'],['renewal_count','Renovaciones'],['new_business','Nueva'],['customer_id','Cliente'],['address_id','Dirección'],['written_premium','Prima CU'],['voluntary_excess','Franquicia voluntaria'],['compulsory_excess','Franquicia obligatoria']];cols.push(...(line==='motor'?[['make_model','Modelo'],['cover_type','Cobertura'],['driver_age','Edad conductor']]:[['sum_insured','Capital CU'],['policyholder_age','Edad']]));document.getElementById('caseBody').innerHTML='<h3>'+esc(pid)+' · '+esc(line)+'</h3><p>'+(example?esc(example.interpretation):'Póliza de la cohorte congelada. Conservar registros y decisión literal; semántica pendiente.')+'</p><h3>Periodos publicados</h3>'+grid(h.policies,cols)+'<h3>Todos los siniestros disponibles</h3>'+grid(h.claims,[['claim_id','ID'],['peril','Peligro'],['loss_date','Ocurrencia'],['report_date','Reporte'],['status','Estado'],['paid_to_date','Pagado CU'],['incurred_to_date','Incurrido CU'],['recoveries','Recuperaciones CU'],['observed_net_CU','Neto aceptado CU'],['row_id','Periodo asignado'],['reported_after_period','Reportado después del fin']]);}
function filterPolicies(){const q=document.getElementById('search').value.trim().toLowerCase();const rows=data.index.filter(r=>(r.policy_id+' '+r.line).toLowerCase().includes(q));const select=document.getElementById('policy');select.innerHTML=rows.map(r=>'<option value="'+esc(r.policy_id)+'">'+esc(r.policy_id)+' · '+esc(r.line)+'</option>').join('');select.value=rows.length?rows[0].policy_id:'';document.getElementById('matches').textContent=rows.length+' de '+data.index.length+' pólizas';showPolicy(select.value);return rows;}
document.getElementById('search').addEventListener('input',filterPolicies);
document.getElementById('policy').addEventListener('change',()=>showPolicy(document.getElementById('policy').value));
document.getElementById('example').addEventListener('change',()=>showPolicy(document.getElementById('example').value));
filterPolicies();showPolicy(data.cases[0].policy_id);
</script></main></body></html>'''
    sub = {'TESTROWS': n(s['cohort_2025_rows']), 'COST': n(s['preceding_net_CU'], 2), 'NOCLAIM': n(s['2024_no_observed_claim_policies']),
        'PROFILE': table(p), 'HP': n(s['cohort_history_periods']), 'HC': n(s['cohort_history_claims']), 'ANNUAL': table(dd),
        'DECLINED2024': n(s['2024_declined_total']), 'NONEXT': n(s['2024_declined_without_successor']),
        'REPEATED': n(s['cohort_multiple_declines']), 'THREE': n(s['cohort_three_declines']),
        'RECORDS': n(s['preceding_claim_records']), 'ACCEPTED': n(s['preceding_accepted_claims']),
        'REPUDIATED': n(s['preceding_repudiated_claims']), 'RESERVE': n(s['preceding_open_reserve_CU'], 2),
        'ROWSHARE': n(s['preceding_row_share_2024_pct'], 4), 'EXPSHARE': n(s['preceding_exposure_share_2024_pct'], 4),
        'COSTSHARE': n(s['preceding_cost_share_2024_pct'], 4), 'SENSITIVITY': table(st), 'FIELDS': table(shown),
        'OPTIONS': opts, 'DATA': payload, 'RUN': html.escape(s['run'])}
    for k, v in sub.items():
        template = template.replace('@@' + k + '@@', str(v))
    assert '@@' not in template
    (out / 'informe.html').write_text(template, encoding='utf-8')
    print(json.dumps({'report': str(out / 'informe.html'), 'all_cohort_policies_inspectable': len(data['index']), 'cases': len(data['cases'])}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
