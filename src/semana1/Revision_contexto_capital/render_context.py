"""Informe con doce casos, figuras y explorador íntegro de los 109 pendientes."""
from pathlib import Path
import html
import json
import sys

import review_context as a
import clean_data as c
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

LABELS={'buildings_TW_only':'Edificios: solo T/W',
 'buildings_address_id':'Edificios: dirección',
 'buildings_address_id_construction_type':'Edificios: dirección y construcción',
 'buildings_address_id_smoke_alarms':'Edificios: dirección y alarmas',
 'buildings_address_id_construction_type_smoke_alarms':'Edificios: dirección, construcción y alarmas',
 'contents_address_change':'Contenidos: dirección'}


def records(frame):return json.loads(frame.to_json(orient='records',date_format='iso',date_unit='ms'))


def n(x,d=0):return f'{float(x):,.{d}f}'.replace(',','_').replace('.',',').replace('_','.')


def main(out):
    assert not (out/'manifest.json').exists()
    f=pd.read_parquet(out/'tables/context_assessment.parquet');h=pd.read_parquet(out/'tables/all_policy_histories.parquet')
    claims=pd.read_parquet(out/'tables/all_claim_histories.parquet');addresses=pd.read_parquet(out/'tables/address_context.parquet')
    summary=json.loads((out/'summary.json').read_text('utf-8'))
    # The D34 scale criterion is a specified subset, not constancy of every tariff field.
    lookup=h.set_index('row_id');outside=[]
    fields=['policyholder_age','days_unoccupied','exposure','channel','payment_method','missed_payments_12m',
        'new_business','renewal_count','days_quote_to_inception','discount_applied','written_premium',
        'customer_service_contacts','renewal_decision']
    for row in f.itertuples():
        for field in fields:
            if field=='days_unoccupied' and row.line=='contents':continue
            x,y=lookup.loc[row.row_id,field],lookup.loc[row.later_row_id,field]
            outside.append({'focus_row_id':row.row_id,'later_row_id':row.later_row_id,'line':row.line,'field':field,
                'focus_value':str(x),'later_value':str(y),'pair_missing':bool(pd.isna(x) or pd.isna(y)),
                'changed_when_both_known':bool(not (pd.isna(x) or pd.isna(y)) and x!=y)})
    outside=pd.DataFrame(outside);a.save(outside,out,'noncriterion_later_comparisons')
    outside_counts=outside.groupby(['line','field'],sort=False).agg(pairs=('focus_row_id','size'),
        missing_pairs=('pair_missing','sum'),changed_known_pairs=('changed_when_both_known','sum')).reset_index()
    a.save(outside_counts,out,'noncriterion_later_counts')
    criterion_table=pd.DataFrame([{'Ramo':line,'Campos completos e iguales con el ancla posterior':', '.join(fields)}
        for line,fields in a.cap.FIELDS.items()]).to_html(index=False,border=0)
    counts=f.review_pattern.value_counts().reindex(LABELS)
    fig,axes=plt.subplots(1,2,figsize=(16,6),gridspec_kw={'width_ratios':[1.35,1]})
    axes[0].barh(np.arange(len(counts)),counts,color=['#176477']*5+['#ba7128'])
    axes[0].set_yticks(np.arange(len(counts)),list(LABELS.values()));axes[0].invert_yaxis();axes[0].set_xlim(0,40)
    for i,value in enumerate(counts):axes[0].text(value+.5,i,str(value),va='center')
    axes[0].set_xlabel('Filas pendientes');axes[0].set_title('Qué diferencia describe el contexto anterior')
    for line,color,label in [('buildings','#176477','Edificios'),('contents','#ba7128','Contenidos')]:
        axes[1].hist(f.loc[f.line.eq(line),'later_vs_hypothetical_pct'],bins=12,color=color,alpha=.7,label=label)
    axes[1].set_title('Continuidad con el siguiente periodo del mismo contexto');axes[1].set_xlabel('Capital posterior frente a /1000 hipotético (%)')
    axes[1].set_ylabel('Filas');axes[1].legend(frameon=False)
    for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='x' if ax==axes[0] else 'y',alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('109 comparaciones retrospectivas; no se aplica ninguna corrección',fontsize=16)
    fig.tight_layout();fig.savefig(out/'figures/context_patterns.png',dpi=150,bbox_inches='tight');plt.close(fig)
    pids=['B00723804','B13523069','B03817872','B12373596','C04555093','C09729229','B18335664','B19256617']
    fig,axes=plt.subplots(2,4,figsize=(18,9))
    for ax,pid in zip(axes.flat,pids):
        g=h.loc[h.policy_id.eq(pid)].sort_values('period_start');x=np.arange(len(g));focus=g.focus_109.to_numpy()
        ax.plot(x,g.sum_insured,'o-',color='#176477',linewidth=1.3,label='Capital vigente')
        ax.scatter(x[focus],g.loc[focus,'sum_insured']/1000,marker='D',s=55,facecolors='none',edgecolors='#bd7127',linewidths=1.6,label='/1000 propuesto, sin aplicar')
        ax.set_yscale('log');ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'.replace(',','.')))
        ax.set_xticks(x,[d.strftime('%Y-%m-%d') for d in g.period_start],rotation=40,ha='right',fontsize=7)
        ax.set_title(pid,fontsize=12);ax.set_ylabel('Capital CU, log',fontsize=9);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False)
    fig.suptitle('Historias completas: cambio de riesgo y escala monetaria se revisan por separado',fontsize=16)
    fig.tight_layout(rect=[0,.07,1,.95]);fig.savefig(out/'figures/case_histories.png',dpi=150,bbox_inches='tight');plt.close(fig)
    cases=[]
    def case(pid,title,text):
        q=f.loc[f.policy_id.eq(pid)];assert len(q)==1,pid
        cases.append({'policy_id':pid,'focus_row_id':q.iloc[0].row_id,'title':title,'interpretation':text})
    case('B00723804','Una escala que se puede contrastar sin unificar T/W',
        '2022: 230.000 CU con T; 2023: 237.000.000 con W; 2024: 244.000 con W. /1000 daría 237.000. La comparación W→W posterior es completa: no exige traducir T a W ni confirmar su material físico.')
    case('B13523069','El nuevo inmueble tiene un límite mayor',
        'La dirección cambia en agosto de 2021. El límite anterior es 105.000 CU; la nueva fila registra 382.000.000 y el siguiente periodo en la nueva dirección tiene 393.000. /1000 daría 382.000. Copiar 105.000 eliminaría el cambio real de nivel registrado para el nuevo riesgo.')
    case('B03817872','La mudanza también puede reducir el capital',
        'La póliza pasa de 301.000 CU en una dirección a 185.000.000 en otra; el siguiente periodo conserva la nueva dirección y registra 191.000. La hipótesis de 185.000 preserva el menor límite, sin forzarlo al del inmueble anterior.')
    case('B12373596','Dirección y construcción cambian juntas',
        'En 2021 pasa de brick/272.000 CU a otra dirección con stone/148.000.000; 2022 conserva stone y la nueva dirección con 152.000. No se cambia brick a stone: ambas observaciones se conservan y la hipótesis de escala afecta solo a la fila nueva.')
    case('B12711055','Cambio de inmueble, construcción y alarmas',
        'La referencia anterior tiene non_standard, smoke_alarms=true y 178.000 CU. El riesgo nuevo tiene brick, smoke_alarms=false y 358.000.000; luego aparece 369.000 bajo ese mismo contexto nuevo. Son diferencias de riesgo observadas, no campos que deban igualarse para reparar la escala.')
    case('B28556862','Una alarma distinta no equivale a un error de capital',
        'La dirección cambia, smoke_alarms pasa de false a true y el importe de 249.000 CU se compara con 99.000.000 en el nuevo riesgo. La siguiente fila mantiene la nueva dirección y true con 102.000. /1000 daría 99.000, conservando el cambio de contexto.')
    case('C04555093','Los bienes pueden conservar su capital al mudarse',
        'En contenidos figuran 24.400 CU antes de la mudanza, 24.400.000 después y 24.900 al renovar en la nueva dirección. /1000 conserva 24.400. La ubicación cambia el riesgo, pero el límite sobre los bienes no tiene que aumentar o disminuir por ese solo hecho.')
    case('C09729229','Un respaldo de test 2025 y un tramo anterior de tres días',
        'El primer segmento observado va del 10 al 12 de noviembre de 2024 con 51.600 CU; después cambia la dirección y aparece 51.600.000. Test 2025 conserva el nuevo contexto y 52.600. /1000 sería 51.600. El capital no se anualiza por tres días de exposición y el dato 2025 solo aporta evidencia retrospectiva.')
    case('B18335664','El nulo pertenece al riesgo anterior',
        'La referencia de 381.000 CU en otra dirección tiene smoke_alarms nulo. La fila pendiente tiene 300.000.000, nueva dirección y contexto completo; test 2025 conserva ese contexto con 310.000. /1000 daría 300.000. No se rellena el nulo anterior: la referencia de unidad es la fila posterior del riesgo nuevo.')
    case('B19256617','Dos importes altos, una sola fila en esta propuesta',
        'La mudanza de julio 2022 registra 377.000.000 CU y sigue pendiente fuera de este grupo. La fila 2023 de 388.000.000 es la que revisamos, con respaldo original de 400.000 en 2024. Proponer 388.000 no autoriza dividir los 377.000.000 anteriores ni usar la nueva cifra para una cascada.')
    case('B27457202','Un siniestro observado no decide la corrección',
        'La fila pendiente B00368527 tiene un siniestro cerrado CL83963478 por 4.446,52 CU de incurrido. La hipótesis de capital es 73.000 CU. El expediente se conserva y se presenta como diagnóstico separado: no fija el capital ni confirma su unidad.')
    case('B71840966','El capital propuesto y el coste del expediente son magnitudes distintas',
        'CL25718230 tiene incurrido observado de 29.100,65 CU en la fila pendiente B01424275. /1000 daría un capital de 208.000 CU. No se divide el siniestro, no se recorta al capital hipotético y no se usa su importe para seleccionar la propuesta.')
    c.dump(out/'cases.json',cases);a.save(pd.DataFrame(cases),out,'case_index')
    data={'index':records(f),'cases':cases,'histories':{pid:{'policies':records(g),
        'claims':records(claims.loc[claims.policy_id.eq(pid)]),
        'addresses':records(addresses.loc[addresses.address_id.isin(g.address_id)])} for pid,g in h.groupby('policy_id',sort=False)}}
    c.dump(out/'explorer_data.json',data)
    options=''.join(f'<option value="{html.escape(row["focus_row_id"])}">{html.escape(row["policy_id"]+" · "+row["title"])}</option>' for row in cases)
    pattern_table=pd.DataFrame([{'Patrón':label,'Filas':int(f.review_pattern.eq(key).sum()),
        'Con ancla test 2025':int((f.review_pattern.eq(key)&f.test2025_reference).sum())} for key,label in LABELS.items()]).to_html(index=False,border=0)
    signal_table=f.loc[f.test2025_reference,['row_id','policy_id','line','sum_insured','hypothetical_div1000_CU','later_row_id','later_capital_CU']].to_html(index=False,border=0,float_format=lambda x:n(x,2))
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    report='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>109 capitales: apoyo posterior y contexto anterior distinto</title><style>body{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#193448;margin:0}main{max-width:1450px;margin:auto;padding:25px}header,section{padding:25px;background:white;border-radius:12px;margin-bottom:18px}header{background:#17394d;color:white}h1{font-size:31px;line-height:1.3}h2{font-size:23px}h3{font-size:19px}.scroll{overflow:auto;max-height:650px}table{border-collapse:collapse;font-size:13px;width:100%}th,td{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}th{position:sticky;top:0;background:#eff4f7}.focus{background:#fff0d8}.pending{background:#fff8eb}.test{color:#425b75}img{max-width:100%;height:auto}select,input{font:inherit;padding:9px;border:1px solid #adbdc7;border-radius:6px;width:100%;max-width:1050px;margin:6px 0 12px;box-sizing:border-box}label{display:block;margin-top:10px}a{color:#007d72}.note{border-left:4px solid #b77424;padding:12px 18px;background:#fff5e2}.ok{border-left:4px solid #178070;padding:12px 18px;background:#edf8f3}code{background:#eef3f6;color:#193448;padding:2px 4px}li{margin-bottom:8px}</style></head><body><main>
<header><h1>Los 109 capitales con contexto anterior distinto</h1><p>75 edificios · 34 contenidos · 109 pólizas · 571 periodos completos</p><p>Revisión sobre CAP03R. Los 576 pendientes y ambos catálogos permanecen iguales.</p></header>
<section><h2>Qué cambió y qué respalda la escala</h2><p>En 31 filas de edificios cambia únicamente construction_type de T a W frente a la referencia anterior habitual, sin cambio de dirección. En otras 78 cambia la dirección: 44 edificios y 34 contenidos. En edificios la mudanza puede ir acompañada de construcción y alarmas distintas.</p><div class="scroll">@@PATTERNS@@</div><p>Los 109 tienen como referencia el periodo inmediatamente posterior de su propia póliza y ramo. Allí los campos de riesgo exigidos están completos e iguales a los de la fila pendiente, y el capital es un valor original sin CAP01, CAP02R o CAP03R. El intervalo posterior no se solapa, comienza después del final de la fila y queda a 3–365 días entre inicios. La hipótesis (capital/1000)/referencia pasa la banda 0,90–1,10 en todos.</p><img src="figures/context_patterns.png" alt="Tipos de cambio de contexto y continuidad del capital posterior"><p>Los capitales posteriores están entre 2,22% y 3,90% por encima de la hipótesis en edificios, y entre 1,63% y 2,48% en contenidos. Es evidencia de una escala plausible bajo el contexto nuevo, no una confirmación de unidad o contrato por la fuente.</p></section>
<section><h2>El riesgo anterior no determina el límite del nuevo</h2><p>En edificios con mudanza, /1000 puede dejar un límite muy distinto al anterior. B13523069 pasa de 105.000 CU en un inmueble a un registro de 382.000.000 en otro; el periodo posterior de ese nuevo inmueble tiene 393.000. La hipótesis 382.000 conserva ese cambio de nivel. B03817872 muestra el sentido contrario: 301.000→185.000.000→191.000, con cambio de dirección al entrar el importe alto.</p><p>En los 34 contenidos con mudanza, el capital /1000 coincide exactamente con el anterior. Es coherente con conservar el valor declarado de los bienes al cambiar de ubicación; no demuestra que los bienes fueran idénticos. La ubicación sigue afectando el riesgo de robo, inundación u otros peligros.</p><p>En los 31 T/W, el contraste de unidad se hace entre W de la fila pendiente y W del periodo posterior. No exige unir T con W y no activa CON01. Las etiquetas siguen intactas y su significado físico continúa pendiente.</p><p>La dirección identifica la ubicación; construction_type describe el material declarado; smoke_alarms informa una protección contra incendio. Cambiarlos puede afectar frecuencia o severidad y por tanto la tarifa. El capital limita el importe cubierto y puede influir en severidad, pero no tiene que variar proporcionalmente a prima, exposición o cada atributo del inmueble.</p><p>El maestro de direcciones muestra tipo de inmueble, dormitorios, año de construcción y riesgo de inundación para ambos IDs. Carece de fechas históricas de vigencia: sirve como contexto, sin demostrar el estado físico exacto al cotizar ni el capital contractual.</p></section>
<section><h2>Tres faltantes anteriores y una secuencia de dos importes altos</h2><p>B18335664, B31552770 y B43866315 tienen smoke_alarms nulo en el riesgo anterior. En las tres, el riesgo de la fila pendiente y el de su ancla posterior tienen los campos exigidos completos e iguales. La propuesta no necesita imputar el dato del inmueble anterior ni afirmar que aquel riesgo era equivalente al nuevo.</p><p>B19256617 tiene 196.000 CU en la dirección anterior, 377.000.000 tras mudarse en julio 2022, 388.000.000 en 2023 y 400.000 en 2024 bajo la nueva dirección. Este grupo contiene solo la fila de 388.000.000, cuya hipótesis es 388.000. El importe de 377.000.000 continúa pendiente dentro de los otros 467. Su presencia no es una segunda confirmación independiente de unidad.</p><div class="note">No copiar capitales del inmueble anterior, no rellenar faltantes para pasar una regla y no ampliar la propuesta usando las referencias nuevas que una corrección futura pudiera crear.</div></section>
<section><h2>Qué significa contexto igual en esta propuesta</h2><p>La igualdad se limita a los campos del criterio de escala D34, enumerados aquí. No implica que todos los factores tarifarios, las circunstancias de cada año o el riesgo físico completo sean constantes.</p><div class="scroll">@@CRITERIA@@</div><p>Por ejemplo, days_unoccupied cambia en 68 pares informados de las 75 comparaciones posteriores de edificios; otro par tiene un faltante. La edad, la exposición, la renovación y la prima también pueden cambiar. Los días desocupados pueden afectar el riesgo y la tarifa; por sí solos no determinan la unidad monetaria del límite. Esta revisión conserva esas variaciones y no interpreta la continuidad del capital como una tarifa constante.</p><div class="scroll">@@OUTSIDE@@</div><p>La tabla cuenta diferencias solo entre valores informados y separa pares con faltantes. customer_service_contacts y renewal_decision son diagnósticos, no predictores autorizados. <a href="tables/noncriterion_later_comparisons.csv">Cada comparación fuera del criterio</a>.</p></section>
<section><h2>Ocho historias en escala logarítmica</h2><img src="figures/case_histories.png" alt="Ocho historiales completos con la división hipotética marcada en naranja"><p>Azul: capital vigente, sin modificar. Rombo naranja: /1000 de la fila de este grupo, todavía hipotético. En B19256617 el otro importe alto permanece sin rombo porque no pertenece a esta propuesta. Los ejes son logarítmicos y cada panel conserva su rango.</p></section>
<section id="casos"><h2>Doce casos explicados y explorador de las 109 filas</h2><label for="example">Casos explicados</label><select id="example">@@OPTIONS@@</select><label for="search">Buscar fila, póliza, ramo o patrón</label><input id="search" placeholder="B19256617, C09729229 o buildings_TW_only" autocomplete="off"><select id="focus" aria-label="Capital pendiente"></select><p id="matches"></p><div id="caseBody"></div><noscript><p>Los mismos datos están en los CSV.</p></noscript><p><a href="tables/context_assessment.csv">Las 109 evaluaciones</a> · <a href="tables/all_policy_histories.csv">Los 571 periodos completos</a> · <a href="tables/comparison_stages.csv">Referencia habitual, segmento inmediato, fila y ancla posterior</a> · <a href="tables/address_context.csv">Contexto de direcciones</a> · <a href="tables/all_claim_histories.csv">Los ocho siniestros observados</a></p></section>
<section><h2>Los 17 respaldos de test 2025</h2><p>Son seis edificios y once contenidos. Los otros 92 respaldos pertenecen a train posterior. Las 109 comparaciones son retrospectivas: el ancla no era conocida al inicio del periodo de la fila pendiente. Las 17 de test 2025 se señalan explícitamente en el inventario y en la lista propuesta.</p><div class="scroll">@@TESTSIGNALS@@</div><p>El caso C09729229 tiene un primer segmento de solo tres días en noviembre 2024 con 51.600 CU; luego cambia la dirección y registra 51.600.000; test 2025 muestra 52.600. La hipótesis es 51.600. Un límite de capital no se anualiza por la duración del primer segmento.</p></section>
<section><h2>Primas y siniestros como diagnósticos separados</h2><p>Las primas registradas, descuentos, duraciones y cambios de dirección se muestran en cada historial. La base de prorrateo de written_premium no está confirmada; una prima mayor o menor no resuelve por sí sola la unidad del capital. No se usa su valor para seleccionar ni ajustar esta propuesta.</p><p>Hay ocho siniestros observados en estas 109 pólizas, todos de edificios. Dos pertenecen a periodos pendientes del grupo: CL83963478 con 4.446,52 CU de incurrido y CL25718230 con 29.100,65 CU. Ninguno supera individualmente el capital hipotético de su fila; la muestra es demasiado pequeña para confirmar límites o una escala. No se divide el coste, no se recorta por un límite hipotético y no se redefine el objetivo.</p><p>La clasificación de candidatos se calcula antes de este diagnóstico. Los estados, fechas e importes de los expedientes se conservan. No hay observación de siniestros de ocurrencia 2025: ausencia de expedientes no es riesgo cero para test.</p></section>
<section><h2>Propuesta sin aplicar</h2><ol><li>Proponer la lista congelada de 109 filas como una operación retrospectiva separada de /1000, respaldada por el siguiente periodo original del mismo contexto. La lista y los criterios están guardados; no se ha autorizado o aplicado una corrección nueva.</li><li>Conservar todas las diferencias anteriores de dirección, construcción y alarmas, los nulos y los capitales normales. La reparación de escala no afirma que el contexto anterior fuera incorrecto ni que el nivel nuevo deba igualar al viejo.</li><li>Señalar los 17 apoyos de test 2025, mantener el carácter retrospectivo de los otros 92 y no usar esta reconstrucción como disponibilidad causal en backtests históricos.</li><li>Conservar el resto de 467 pendientes, incluido C48613718 y el tramo de 377.000.000 de B19256617. Cualquier revisión posterior requiere su propia evidencia; no hay cascada automática.</li></ol><p><a href="tables/proposed_scale_changes_NOT_APPLIED.csv">Lista propuesta de 109, sin aplicar</a> · <a href="tables/proposed_scale_changes_NOT_APPLIED.parquet">Lista tipada</a> · <a href="proposal.json">Tratamiento y preguntas de fuente</a> · <a href="tables/other_467_inventory.csv">Los otros 467 sin adjudicación nueva</a></p><div class="ok">Siguen 576 capitales pendientes en CAP03R y 1.454 en la base. No se modifica ningún dato, esquema, marca, fecha, importe o índice de datos. CON01 sigue sin activar y no hubo entrenamiento.</div></section>
<section><h2>Evidencia y límites</h2><p>Se comprueban fuentes por hash, cohorte exacta, todos los historiales completos, comparaciones de contexto, 109 referencias originales posteriores, asignación de siniestros y contenido del explorador. La inspección de PNG y la prueba lógica no equivalen a renderizado real en navegador o revisión independiente.</p><p><a href="summary.json">Resumen</a> · <a href="protocol.json">Criterios exactos</a> · <a href="request.json">Solicitud completa</a> · <a href="verification.json">Verificación de datos</a> · <a href="interface_verification.json">Lógica del explorador</a> · <a href="manifest.json">Manifiesto SHA256</a></p><p>La IA preparó código, diagnóstico y comprobaciones propias. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad, sin certificar el contrato. No hay proveedor externo, publicación o contacto a terceros en esta revisión.</p><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe y review_context.py; pasar la carpeta nueva a render_context.py y verify_context.py. verify_report.js comprueba la lógica y record_context.py cierra después de inspeccionar las figuras. Los scripts y el intento fallido previo se conservan como evidencia.</p></section>
<script id="reviewData" type="application/json">@@DATA@@</script><script>
const data=JSON.parse(document.getElementById('reviewData').textContent);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dates=new Set(['period_start','period_end','loss_date','report_date','later_period_start']);
function fmt(k,v){if(v==null)return '';if(dates.has(k))return esc(String(v).slice(0,10));if(typeof v==='number')return new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(v);return esc(v);}
function grid(rows,cols,focus){if(!rows.length)return '<p>Sin expedientes observados en este bloque.</p>';return '<div class="scroll"><table><thead><tr>'+cols.map(([k,l])=>'<th>'+esc(l)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr class="'+(focus!=null&&r.row_id===focus?'focus':r.pending_576?'pending':r.year===2025?'test':'')+'">'+cols.map(([k,l])=>'<td>'+fmt(k,r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function differences(raw){const values=JSON.parse(raw);return '<ul>'+Object.entries(values).map(([key,value])=>'<li>'+esc(key)+': '+esc(value.reference)+' → '+esc(value.focus)+'</li>').join('')+'</ul>';}
function showRow(rid){const q=data.index.find(r=>r.row_id===rid);if(!q){document.getElementById('caseBody').innerHTML='<p>Sin coincidencias.</p>';return;}const h=data.histories[q.policy_id],e=data.cases.find(r=>r.focus_row_id===rid);let body='<h3>'+esc(q.policy_id)+' · '+esc(rid)+'</h3><p>'+esc(e?.interpretation||'Contexto previo distinto; conservarlo y contrastar la unidad con la referencia original posterior del mismo riesgo. Propuesta retrospectiva sin aplicar.')+'</p><p>Patrón: '+esc(q.review_pattern)+'. Capital vigente '+fmt('sum_insured',q.sum_insured)+' CU; /1000 hipotético '+fmt('hypothetical_div1000_CU',q.hypothetical_div1000_CU)+' CU. Ancla posterior '+esc(q.later_row_id)+'; test 2025: '+esc(q.test2025_reference)+'.</p><h3>Diferencias frente a la referencia anterior habitual</h3>'+differences(q.prior_differences_json)+'<p>Faltantes del par anterior: '+esc(q.prior_missing_fields||'ninguno')+'. Referencia anterior habitual '+esc(q.prior_row_id)+'; fila inmediatamente anterior '+esc(q.immediate_prior_row_id)+'.</p><p>El par posterior es completo e igual: '+esc(q.later_same_known_context)+'. Ancla original sin reparación: '+esc(q.later_original_unrepaired)+'. Días entre inicios: '+fmt('days',q.later_start_gap_days)+'.</p>';
const extra=q.line==='buildings'?[['construction_type','Construcción'],['occupancy','Ocupación'],['days_unoccupied','Días desocupado'],['smoke_alarms','Alarmas humo'],['mortgage','Hipoteca']]:[['tenure','Tenencia'],['security_level','Seguridad'],['high_value_items','Bienes de valor'],['works_from_home','Trabajo casa'],['lodgers','Huéspedes'],['bicycle_cover','Bicicleta']];
body+='<h3>Todos los periodos publicados</h3>'+grid(h.policies,[['row_id','Fila'],['period_start','Inicio'],['period_end','Fin'],['exposure','Exposición'],['original_capital_CU','Capital original CU'],['sum_insured','Capital vigente CU'],['pending_576','Pendiente'],['written_premium','Prima CU'],['discount_applied','Descuento'],['customer_id','Cliente'],['address_id','Dirección'],...extra,['accidental_damage_cover','Daño accidental'],['voluntary_excess','Franquicia voluntaria'],['compulsory_excess','Franquicia obligatoria'],['new_business','Alta'],['renewal_count','Renovaciones'],['renewal_decision','Decisión literal'],['audit_ren00','REN00']],rid);
body+='<h3>Todos los siniestros disponibles</h3>'+grid(h.claims,[['claim_id','Siniestro'],['loss_date','Ocurrencia'],['report_date','Reporte'],['status','Estado'],['peril','Peligro'],['paid_to_date','Pagado CU'],['incurred_to_date','Incurrido CU'],['recoveries','Recuperaciones CU'],['row_id','Periodo'],['audit_pre00','PRE00']],null);
body+='<h3>Direcciones (maestro sin vigencia histórica)</h3>'+grid(h.addresses,[['address_id','Dirección'],['property_type','Inmueble'],['bedrooms','Dormitorios'],['year_built','Año construcción'],['region','Región'],['flood_zone','Inundación'],['listed_building','Protegido']],null);document.getElementById('caseBody').innerHTML=body;}
function filterRows(){const q=document.getElementById('search').value.trim().toLowerCase();const rows=data.index.filter(r=>(r.row_id+' '+r.policy_id+' '+r.line+' '+r.review_pattern).toLowerCase().includes(q));const select=document.getElementById('focus');select.innerHTML=rows.map(r=>'<option value="'+esc(r.row_id)+'">'+esc(r.row_id)+' · '+esc(r.policy_id)+' · '+esc(r.review_pattern)+'</option>').join('');select.value=rows.length?rows[0].row_id:'';document.getElementById('matches').textContent=rows.length+' de '+data.index.length+' filas';showRow(select.value);return rows;}
document.getElementById('search').addEventListener('input',filterRows);document.getElementById('focus').addEventListener('change',()=>showRow(document.getElementById('focus').value));document.getElementById('example').addEventListener('change',()=>showRow(document.getElementById('example').value));filterRows();showRow(data.cases[0].focus_row_id);
</script></main></body></html>'''
    for key,value in {'PATTERNS':pattern_table,'TESTSIGNALS':signal_table,'OPTIONS':options,'DATA':payload,
        'CRITERIA':criterion_table,'OUTSIDE':outside_counts.to_html(index=False,border=0)}.items():report=report.replace('@@'+key+'@@',value)
    assert '@@' not in report
    (out/'informe.html').write_text(report,encoding='utf-8')
    print(json.dumps({'report':str(out/'informe.html'),'cases':len(cases),'explorer_rows':len(f),'figures':2},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
