"""Doce historiales completos, contraste poblacional y escenarios sin aplicar."""
from pathlib import Path
import html
import json
import sys

import review_discrepancies as a
import clean_data as c
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def records(frame):return json.loads(frame.to_json(orient='records',date_format='iso',date_unit='ms'))


def n(x,d=0):return f'{float(x):,.{d}f}'.replace(',','_').replace('.',',').replace('_','.')


def main(out):
    assert not (out/'manifest.json').exists()
    f=pd.read_parquet(out/'tables/twelve_assessment.parquet');h=pd.read_parquet(out/'tables/all_12_policy_histories.parquet')
    controls=pd.read_parquet(out/'tables/independent_normal_control_sequences.parquet')
    s=json.loads((out/'summary.json').read_text('utf-8'))
    byyear=controls.groupby('year').agg(sequences=('row_id','size'),median_renewal_vs_initial_pct=('renewal_vs_initial_pct','median'),
        median_renewal_vs_midterm_pct=('renewal_vs_midterm_pct','median'),closer_to_initial=('closer_to_initial_than_midterm','sum')).reset_index()
    a.save(byyear,out,'controls_by_year')
    fig,axes=plt.subplots(1,2,figsize=(14,5.8))
    axes[0].hist(controls.renewal_vs_initial_pct,bins=45,color='#176477',alpha=.85,label='9909 controles: renovación / nivel inicial')
    for value in f.hypothetical_vs_initial_pct:axes[0].axvline(value,color='#c77423',alpha=.5,linewidth=1.2)
    axes[0].set_xlabel('Cambio porcentual frente al nivel anterior a la ampliación');axes[0].set_ylabel('Secuencias de control')
    axes[0].set_title('Los 12 valores /1000 encajan en la continuidad habitual')
    axes[0].legend(frameon=False,fontsize=9)
    axes[1].scatter(controls.midterm_increase_pct,controls.renewal_vs_midterm_pct,s=9,alpha=.1,color='#176477',label='Controles originales habituales')
    axes[1].scatter(f.midterm_increase_pct,f.hypothetical_vs_midterm_pct,s=58,facecolors='none',edgecolors='#c77423',linewidth=1.6,label='12 casos: /1000 hipotético')
    axes[1].set_xlabel('Ampliación durante el año (%)');axes[1].set_ylabel('Renovación frente al último capital ampliado (%)')
    axes[1].set_title('La bajada al renovar también aparece en los controles');axes[1].legend(frameon=False,fontsize=9)
    for ax in axes:ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True)
    fig.suptitle('Comparación descriptiva: no confirma condiciones contractuales',fontsize=15)
    fig.tight_layout();fig.savefig(out/'figures/controls.png',dpi=155,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(3,4,figsize=(18,12))
    for ax,row in zip(axes.flat,f.itertuples(index=False)):
        g=h.loc[h.policy_id.eq(row.policy_id)].sort_values('period_start');x=np.arange(len(g));focus=g.row_id.eq(row.row_id).to_numpy()
        ax.plot(x,g.sum_insured,'o-',color='#176477',label='Capital vigente',linewidth=1.3)
        ax.scatter(x[focus],g.loc[focus,'sum_insured']/1000,marker='D',s=50,facecolors='none',edgecolors='#c77423',linewidths=1.6,label='/1000 hipotético')
        ax.set_yscale('log');ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'.replace(',','.')))
        ax.set_xticks(x,[d.strftime('%Y-%m-%d') for d in g.period_start],rotation=40,ha='right',fontsize=7)
        ax.set_title(row.policy_id+(' · ancla 2025' if row.test2025_reference else ''),fontsize=11)
        ax.set_ylabel('Capital CU, log',fontsize=9);ax.grid(axis='y',alpha=.16);ax.spines[['top','right']].set_visible(False)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False)
    fig.suptitle('Los 12 casos: capitales conservados y una hipótesis de escala separada',fontsize=16)
    fig.tight_layout(rect=[0,.055,1,.96]);fig.savefig(out/'figures/twelve_histories.png',dpi=155,bbox_inches='tight');plt.close(fig)
    table=f[['policy_id','initial_capital_CU','midterm_capital_CU','reported_capital_CU','hypothetical_div1000_CU','later_capital_CU',
             'hypothetical_vs_initial_pct','hypothetical_vs_midterm_pct','test2025_reference','review_tier']].rename(columns={
        'policy_id':'Póliza','initial_capital_CU':'Antes de ampliar CU','midterm_capital_CU':'Último capital previo CU',
        'reported_capital_CU':'Pendiente CU','hypothetical_div1000_CU':'/1000 hipotético CU','later_capital_CU':'Posterior CU',
        'hypothetical_vs_initial_pct':'Hipótesis / inicial (%)','hypothetical_vs_midterm_pct':'Hipótesis / último previo (%)',
        'test2025_reference':'Ancla test 2025','review_tier':'Nivel de evidencia'}).to_html(index=False,border=0,float_format=lambda x:n(x,2))
    years=byyear.to_html(index=False,border=0,float_format=lambda x:n(x,2))
    all_cases=[]
    for row in f.itertuples(index=False):
        text=(f'El nivel anterior a la ampliación es {n(row.initial_capital_CU)} CU y el siguiente segmento sube a {n(row.midterm_capital_CU)} '
              f'({n(row.midterm_increase_pct,2)}%). El registro pendiente es {n(row.reported_capital_CU)} CU. /1000 daría '
              f'{n(row.hypothetical_div1000_CU)}, {n(row.hypothetical_vs_initial_pct,2)}% sobre el nivel inicial y '
              f'{n(row.hypothetical_vs_midterm_pct,2)}% frente al capital ampliado. El periodo posterior registra {n(row.later_capital_CU)} CU. ')
        if row.policy_id=='C48613718':text+='La referencia inicial tiene security_level nulo. En 2021 había 28.200 CU y locks, pero queda a 730 días del periodo pendiente. Esa referencia más lejana no sustituye el dato faltante del segmento de 2022.'
        elif row.test2025_reference:text+='El respaldo posterior es test 2025 y no era información conocida al inicio de 2024.'
        elif row.policy_id=='C49279780':text+='El tramo de 101.000 CU dura siete días: el capital sigue siendo un límite, no un flujo que deba anualizarse. Su prima de 253,24 CU tampoco confirma una base de prorrateo.'
        else:text+='Los campos de riesgo exigidos están completos e iguales entre el segmento inicial, el ampliado, la fila pendiente y el ancla posterior.'
        all_cases.append({'policy_id':row.policy_id,'focus_row_id':row.row_id,'interpretation':text})
    c.dump(out/'cases.json',all_cases)
    data={'index':records(f),'cases':all_cases,'histories':{pid:records(g) for pid,g in h.groupby('policy_id',sort=False)}}
    c.dump(out/'explorer_data.json',data)
    options=''.join(f'<option value="{html.escape(x["focus_row_id"])}">{html.escape(x["policy_id"])}</option>' for x in all_cases)
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    report='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Los 12 capitales con discrepancias numéricas</title><style>body{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#193448;margin:0}main{max-width:1450px;margin:auto;padding:25px}header,section{background:white;border-radius:12px;padding:25px;margin-bottom:18px}header{background:#17394d;color:white}h1{font-size:32px;line-height:1.3}h2{font-size:24px}h3{font-size:19px}.scroll{overflow:auto;max-height:650px}table{border-collapse:collapse;font-size:13px;width:100%}td,th{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}th{position:sticky;top:0;background:#f0f5f7}.focus{background:#fff0d8}.test{color:#425b75}img{max-width:100%;height:auto}select{font:inherit;padding:9px;max-width:600px;width:100%;margin:10px 0}a{color:#007d72}.note{border-left:4px solid #b77424;padding:12px 18px;background:#fff5e2}.ok{border-left:4px solid #178070;padding:12px 18px;background:#edf8f3}code{background:#eef3f6;color:#193448;padding:2px 4px}li{margin-bottom:9px}</style></head><body><main>
<header><h1>Los 12 pendientes con discrepancias numéricas</h1><p>Revisión de los 587 restantes de CAP02R, empezando por doce pólizas de contenidos.</p><p>63 periodos completos · cero siniestros observados en estas doce pólizas · ningún dato modificado</p></header>
<section><h2>La discrepancia reúne dos cuestiones distintas</h2><p>En los doce historiales hay una ampliación del capital durante el año, seguida de una renovación el 1 de enero cuyo importe está en la banda de millones. Dividir esa renovación por mil la acerca al nivel anterior a la ampliación y al periodo posterior. Sigue quedando por debajo del último capital ampliado.</p><p>La hipótesis de escala y la reversión del nivel al renovar deben registrarse por separado. Corregir una unidad no obliga a copiar el último capital ni a corregir el segmento normal intermedio. Los datos no aportan un historial contractual que confirme por qué ese nivel vuelve a bajar.</p><div class="scroll">@@TABLE@@</div><p>Las ampliaciones previas son de 21,98–55,83%. La división hipotética deja las renovaciones entre 1,69% y 2,42% sobre el nivel inicial, y entre 16,24% y 34,53% por debajo del último capital ampliado. Los periodos posteriores están entre 1,57% y 2,16% por encima de la hipótesis /1000. Estos porcentajes describen observaciones concretas; no son probabilidades de error.</p></section>
<section><h2>Comparación con 9.909 secuencias ajenas al grupo</h2><p>Se buscaron otras pólizas de contenidos con dos segmentos consecutivos en el año, etiqueta mid_term_change al terminar el primero, renovación el 1 de enero y campos de riesgo especificados completos e iguales. Los tres capitales debían ser originales, positivos y de escala habitual (hasta un millón CU). Se excluyeron las doce pólizas completas. La selección no usó el resultado de sus siniestros ni exigió de antemano que el capital volviera al nivel inicial.</p><p>Aparecen 9.909 secuencias de 9.702 pólizas. En las 9.909, la renovación queda más cerca del capital anterior a la ampliación que del último capital ampliado. La mediana del cambio frente al nivel inicial es +2,00%; los percentiles 5 y 95 son +1,78% y +2,22%. La mediana frente al nivel ampliado es −27,09%. Hay 9.892 secuencias con ampliación superior al 20%; conservan el mismo patrón.</p><img src="figures/controls.png" alt="Comparación de los doce capitales hipotéticos con 9909 secuencias de otras pólizas"><div class="scroll">@@YEARS@@</div><p>Es una comparación descriptiva sobre la selección indicada, con posibles observaciones repetidas de una póliza; no son 9.909 ensayos independientes ni una muestra de todos los contratos. Incluye renovaciones de test 2025, identificadas en la tabla por año. El patrón es compatible con una regla del generador o con cambios contractuales omitidos. Sin código o endosos no podemos distinguirlos ni certificar el valor correcto.</p></section>
<section><h2>Los doce historiales completos</h2><img src="figures/twelve_histories.png" alt="Capitales vigentes e hipótesis por mil en las doce pólizas"><p>Azul: capital vigente, sin modificar. Rombo naranja: división hipotética por mil. Los ejes verticales son logarítmicos. Todos los periodos reales y sus campos están en el explorador.</p><label for="case">Elegir una de las doce pólizas</label><select id="case">@@OPTIONS@@</select><div id="caseBody"></div><noscript><p>Puede consultar los mismos datos en los CSV.</p></noscript><p><a href="tables/twelve_assessment.csv">Doce evaluaciones</a> · <a href="tables/all_12_policy_histories.csv">Los 63 periodos completos</a> · <a href="tables/four_stage_comparisons.csv">Las cuatro etapas de cada comparación</a></p></section>
<section><h2>Propuesta de tratamiento</h2><p>Para once filas, propondría una nueva lista congelada retrospectiva de reparación exclusiva de escala (/1000), conservando el capital ampliado normal y documentando su posterior bajada como incidencia separada. El contexto de las cuatro etapas está completo e igual en los campos exigidos, y el patrón también aparece en los controles. La operación requiere una autorización nueva y no se aplica en este informe.</p><p>C48613718 (fila C01596694) queda condicionado: /1000 daría 29.300 CU, frente a 28.800 antes de ampliar, 40.500 después de ampliar y 29.900 en 2024. Falta security_level en el segmento de 28.800. La continuidad numérica es fuerte, pero no rellenamos ese nulo ni declaramos igualdad completa. La observación 2021 de 28.200 CU con locks está a 730 días y aporta contexto más lejano.</p><p>C21091984 (fila C02362784) pertenece a los once, con respaldo posterior de test 2025: 25.700→31.900→26.200.000→26.700 CU. La hipotética cifra de 26.200 quedaría cerca del nivel previo a la ampliación. Debe mantenerse señalada la dependencia de 2025; no usarla como información disponible al inicio de 2024.</p><div class="note">Propuesta: once posibles reparaciones retrospectivas de escala y un caso condicionado por contexto faltante. Se conservan los 587 pendientes, incluidos estos doce. No se ajusta el nivel contractual, no se activa una corrección nueva ni se amplía CAP02R automáticamente.</div><p>Las doce filas tienen algún respaldo posterior, que no estaba disponible al inicio de su periodo. Este análisis no habilita una preparación causal de backtests. La evidencia anterior que pudiera justificar otra regla debe evaluarse por corte y con criterios propios; tampoco se usa el conjunto de control como una tabla de valores contractuales.</p></section>
<section><h2>Primas, exposición y siniestros</h2><p>Los aumentos de capital durante el año tienen primas registradas mayores en estos doce pares, pero la base de prorrateo no está confirmada. C49279780 pasa de 66.000 a 101.000 CU durante los últimos siete días de 2021; las primas registradas son 169,47 y 253,24 CU. El límite de 101.000 no se anualiza por durar siete días. Su renovación 2022 figura en 67.300.000; /1000 daría 67.300, y 2023 registra 68.700.</p><p>Descuentos, edad, número de renovaciones y campos operativos también pueden cambiar. La igualdad solo cubre los campos exigidos; no significa que todos los factores de tarifa sean idénticos. En C10934421 y C21091984 cambia el descuento al renovar, visible en el historial. No se deduce el capital mediante una ecuación lineal de prima o duración.</p><p>No hay siniestros observados en ninguna de estas doce pólizas. Esa ausencia no valida una escala, un límite o una prima y no demuestra riesgo cero en 2025. Se conservan las marcas REN00/PRE00 y los siniestros de todo el catálogo.</p></section>
<section><h2>Qué queda de los otros 575</h2><p>El inventario conserva 109 casos con apoyo posterior y cambio previo de contexto, 108 sin capital original habitual en la póliza, 2 residuales dependientes de CAP01, 16 de T/W, 202 con faltantes y 138 con otras discrepancias. Esta revisión profundiza en los doce; los otros 575 no reciben una adjudicación individual nueva. El siguiente grupo propuesto son los 109 con diferencias de riesgo, revisando mudanzas y la cronología de cada cambio.</p><p><a href="tables/remaining_587_inventory.csv">Inventario exacto de los 587</a> · <a href="tables/other_575_inventory.csv">Los otros 575</a> · <a href="tables/remaining_587_groups.csv">Distribución por grupo y tabla</a></p><div class="ok">Se conservaron los originales, la base PRE00/REN00 y la capa retrospectiva CAP02R. Siguen 587 capitales pendientes en la capa retrospectiva y 1.454 en la base. No se cambia ningún importe, fecha, estado, marca, esquema o índice de datos. No hubo entrenamiento.</div></section>
<section><h2>Evidencia y límites</h2><p><a href="summary.json">Resumen</a> · <a href="protocol.json">Definiciones de selección y comparación</a> · <a href="proposal.json">Propuesta sin aplicar</a> · <a href="control_comparison.json">Estadísticos de control</a> · <a href="tables/independent_normal_control_sequences.csv">Las 9.909 secuencias de control</a> · <a href="verification.json">Comprobaciones de datos</a> · <a href="interface_verification.json">Lógica del explorador</a> · <a href="manifest.json">Manifiesto SHA256</a></p><p>Verificación propia asistida por IA. Las figuras se inspeccionan por separado; la prueba lógica no acredita renderizado real de navegador ni validación independiente. La investigación preserva el papel del participante en la decisión. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan recorrido del dato, comunicación y responsabilidad. Las preguntas de fuente quedan guardadas sin contactar a terceros.</p><p>Reproducir desde C:/dev/Hakaton con Preparación/.venv/Scripts/python.exe y review_discrepancies.py; pasar la carpeta generada a render_discrepancies.py y verify_discrepancies.py. verify_report.js recibe informe.html y una ruta nueva para interface_verification.json. record_discrepancies.py cierra tras inspeccionar las figuras. Los scripts se conservan en source_snapshot.</p></section>
<script id="reviewData" type="application/json">@@DATA@@</script><script>
const data=JSON.parse(document.getElementById('reviewData').textContent);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function fmt(k,v){if(v==null)return '';if(k==='period_start'||k==='period_end')return esc(String(v).slice(0,10));if(typeof v==='number')return new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(v);return esc(v);}
function showCase(rid){const q=data.index.find(r=>r.row_id===rid);if(!q){document.getElementById('caseBody').innerHTML='<p>Sin coincidencias.</p>';return;}const rows=data.histories[q.policy_id],ex=data.cases.find(r=>r.focus_row_id===rid);const cols=[['row_id','Fila'],['period_start','Inicio'],['period_end','Fin'],['covered_days','Días'],['exposure','Exposición'],['sum_insured','Capital vigente CU'],['written_premium','Prima CU'],['discount_applied','Descuento'],['customer_id','Cliente'],['address_id','Dirección'],['tenure','Tenencia'],['security_level','Seguridad'],['high_value_items','Bienes valiosos'],['accidental_damage_cover','Daño accidental'],['works_from_home','Trabajo casa'],['lodgers','Huéspedes'],['bicycle_cover','Bicicleta'],['voluntary_excess','Franquicia voluntaria'],['compulsory_excess','Franquicia obligatoria'],['new_business','Alta'],['renewal_count','Renovaciones'],['renewal_decision','Decisión literal'],['audit_ren00','REN00']];document.getElementById('caseBody').innerHTML='<h3>'+esc(q.policy_id)+' · '+esc(rid)+'</h3><p>'+esc(ex.interpretation)+'</p><p>Nivel de revisión: '+esc(q.review_tier)+'. /1000 sigue siendo hipotético. Tratamiento propuesto: '+esc(q.proposed_treatment)+'</p><div class="scroll"><table><thead><tr>'+cols.map(([k,l])=>'<th>'+esc(l)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr class="'+(r.row_id===rid?'focus':r.year===2025?'test':'')+'">'+cols.map(([k,l])=>'<td>'+fmt(k,r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
document.getElementById('case').addEventListener('change',()=>showCase(document.getElementById('case').value));document.getElementById('case').value=data.index[0].row_id;showCase(data.index[0].row_id);
</script></main></body></html>'''
    for key,value in {'TABLE':table,'YEARS':years,'OPTIONS':options,'DATA':payload}.items():report=report.replace('@@'+key+'@@',value)
    assert '@@' not in report
    (out/'informe.html').write_text(report,encoding='utf-8')
    print(json.dumps({'report':str(out/'informe.html'),'figures':2,'cases':12},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
