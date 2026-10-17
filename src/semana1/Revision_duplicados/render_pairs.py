"""Informe con los 604 pares, once casos seleccionados y controles que deben conservarse."""
import base64
import json
from html import escape

import review_pairs as a
import pandas as pd
import pyarrow.parquet as pq


def render(out,verification):
    s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    selection=json.loads((out/'case_selection.json').read_text(encoding='utf-8'))
    proposed=pq.read_table(out/'tables/proposed_pair_actions.parquet').to_pandas()
    pair_members=pq.read_table(out/'tables/frozen_pair_members.parquet').to_pandas()
    policies=pq.read_table(out/'tables/affected_policy_histories.parquet').to_pandas()
    claims=pq.read_table(out/'tables/affected_claim_histories.parquet').to_pandas()
    materiality=json.loads((out/'tables/materiality.json').read_text(encoding='utf-8'))
    money_by_line=pd.DataFrame([r for r in materiality if r['dimension']=='line'])[
        ['line','groups','hypothetical_paid_reduction_CU','hypothetical_reserve_reduction_CU',
         'hypothetical_recovery_reduction_CU','hypothetical_net_reduction_CU']]
    year=pd.DataFrame([r for r in materiality if r['dimension']=='loss_year'])[
        ['loss_year','groups','hypothetical_net_reduction_CU']]
    table=lambda f:f.to_html(index=False,border=0,escape=True,na_rep='Sin dato')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12.3,4.5))
    axes[0].bar(money_by_line.line,money_by_line.hypothetical_net_reduction_CU.astype(float)/1000,color=['#007b83','#41678e','#956b36'])
    axes[0].set_ylabel('Miles de CU, neto aceptado observado')
    axes[0].set_title('Efecto hipotético de conservar una copia por par')
    for i,row in money_by_line.reset_index().iterrows():axes[0].text(i,float(row.hypothetical_net_reduction_CU)/1000+25,str(int(row.groups))+' pares',ha='center',fontsize=9)
    axes[1].bar(['Coinciden todas\nlas 11 variables','Mismo peligro\ny ambas fechas','Mismo peligro\ny ocurrencia','Misma póliza\ny ocurrencia'],[604,605,621,661],color=['#007b83','#8197a7','#b6a17c','#c28148'])
    axes[1].set_ylim(0,735);axes[1].set_ylabel('Grupos de dos registros en todo claims')
    axes[1].set_title('Una clave demasiado corta ampliaría la depuración')
    for i,value in enumerate([604,605,621,661]):axes[1].text(i,value+8,str(value),ha='center')
    axes[1].tick_params(axis='x',labelsize=8)
    fig.tight_layout();fig.savefig(out/'figures/duplicate_evidence.png',dpi=145);plt.close(fig)
    image=base64.b64encode((out/'figures/duplicate_evidence.png').read_bytes()).decode()
    policy_cols=['row_id','period_start','period_end','address_id','exposure','cover_type','sum_insured',
                 'accidental_damage_cover','voluntary_excess','compulsory_excess','renewal_count','renewal_decision']
    claim_cols=['source_row','claim_id','duplicate_group','proposed_role','peril','loss_date','report_date','status',
                'paid_to_date','incurred_to_date','recoveries','observed_net_CU','repairer_id','third_party_id','row_id','assignment_status']
    claim_role=dict(zip(pair_members.claim_id,pair_members.proposed_role))
    claims['proposed_role']=claims.claim_id.map(claim_role).fillna('preserve_other_record')
    claims=claims.sort_values(['line','policy_id','loss_date','report_date','duplicate_group','claim_id'],na_position='last')
    policies=policies.sort_values(['line','policy_id','period_start','period_end'])
    def records(frame):return json.loads(frame.to_json(orient='records',date_format='iso'))
    grouped={}
    for (line,policy),g in claims.groupby(['line','policy_id']):
        p=policies[policies.line.eq(line)&policies.policy_id.eq(policy)]
        grouped[line+'|'+policy]={'claims':records(g[claim_cols]),'periods':records(p[policy_cols])}
    options=''.join('<option value="'+str(i)+'">'+escape(r['case_id']+': '+r['policy_id']+' · '+r['reason'])+'</option>' for i,r in enumerate(selection))
    proposal_cols=['duplicate_group','line','policy_id','proposed_keep_claim_id','proposed_exclude_claim_id','peril','loss_date','status','observed_net_CU','assignment_status']
    rules=json.loads((out/'proposed_rule.json').read_text(encoding='utf-8'))
    html=[
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>604 pares de siniestros: historia y propuesta DUP01</title>',
        '<style>body{font:16px/1.65 system-ui;color:#193344;background:#fafcfd;max-width:1350px;margin:36px auto;padding:0 24px}h1{line-height:1.2}h2{margin-top:2em}table{border-collapse:collapse;display:block;overflow:auto;max-width:100%;font-size:13px;background:white}th,td{padding:8px 10px;border-bottom:1px solid #d8e1e6;text-align:left;white-space:nowrap}th{background:#e7eff3}a{color:#05628f}.decision{padding:18px 24px;background:#e6f3ef;border-left:5px solid #007b83}.limit{padding:15px 22px;background:#fff0d9}img{max-width:100%}code{background:#eaf0f3;padding:1px 4px}input,select{font:inherit;padding:9px;max-width:100%;margin-bottom:12px}select{width:100%}input{width:420px}.proposed-exclude{background:#fff2dd}.preserve{background:#f4f7fa}details{margin:1em 0}summary{cursor:pointer}li{margin:.6em 0}</style></head><body>',
        '<h1>Revisión de los 604 pares potencialmente duplicados</h1>',
        '<div class="decision"><p>La evidencia respalda proponer una copia por cada pareja exacta de este conjunto congelado. La regla DUP01 exigiría igualdad de los once campos distintos de claim_id y conservaría el identificador CL con ocho dígitos, guardando el ID de nueve como alias excluido en una futura capa derivada.</p>',
        '<p>Esta revisión no aplica la regla. No crea claims depurado, cambia el catálogo activo ni elimina registros. Los 163.150 siniestros originales siguen disponibles. La selección y todos los efectos monetarios son propuestas para revisión humana.</p></div>',
        f'<p>Se revisaron los 604 grupos, sus 1.208 miembros y las historias completas de {s["affected_policies"]} pólizas afectadas. Se conservaron {s["policy_history_rows"]} periodos de entrenamiento y {s["claim_history_rows"]} siniestros de esas historias más dos pólizas de control. No se usaron datos de test para decidir la regla.</p>',
        '<h2>Qué coincide y qué patrón identifica la duplicación</h2>',
        '<p>Cada pareja coincide exactamente en policy_id, line, peril, loss_date, report_date, status, paid_to_date, incurred_to_date, recoveries, repairer_id y third_party_id. No se redondean importes, aproximan fechas, normalizan textos o rellenan datos. Dos ausencias se tratan como iguales para comparar registros; no prueban que el tercero o reparador no existiera.</p>',
        '<p>Los 604 grupos tienen exactamente dos miembros, uno CL+8 dígitos y otro CL+9 dígitos. Los 604 identificadores largos del fichero pertenecen a estas parejas; no hay identificadores largos independientes. El resto de los 162.546 identificadores tiene el formato corto. Es una señal muy consistente de copia de registro, aunque el diccionario solo exige IDs de texto y no confirma un formato oficial.</p>',
        '<p>296 parejas incluyen reparador, 159 un tercero identificado y 59 recuperaciones positivas: también coinciden esos datos. 600 ocurrencias son de 2022; tres de 2021 y una de 2020. Las notificaciones son de 2022 o 2023. Esta concentración apunta a un artefacto de preparación, sin permitir atribuir su causa real al organizador.</p>',
        '<p>La posición del fichero no es una fecha de creación: el ID corto aparece primero en 303 pares y el largo en 301. “Conservar el primero” no identifica una versión anterior. Preferimos el formato dominante como elección determinista de alias después de demostrar igualdad; no porque se haya probado que se creó antes.</p>',
        '<h2>Efecto hipotético y alcance actuarial</h2>',table(money_by_line),
        '<p>Hay 586 parejas cerradas, 12 abiertas y seis rechazadas. Si se aceptara la depuración, se conservarían 162.546 siniestros y se excluirían 604 copias en una versión derivada: 598 aceptadas y seis rechazadas. El coste neto aceptado observado cambiaría en '+s['hypothetical_accepted_net_reduction_all_CU']+' CU en todo el fichero. No es una estimación de pérdida última ni mejora de modelo.</p>',
        '<p>603 parejas corresponden a periodos observados y una queda antes de la primera cobertura disponible. El cambio hipotético de coste de los periodos actuales sería '+s['hypothetical_accepted_net_reduction_assigned_CU']+' CU; los '+s['hypothetical_accepted_net_reduction_prehistory_CU']+' CU restantes quedarían en la conciliación fuera de historia. Hay '+str(s['accepted_assigned_groups'])+' copias aceptadas asignables, distribuidas en '+str(s['accepted_assigned_periods'])+' periodos. Las seis rechazadas no reducen coste ni frecuencia aceptada.</p>',
        '<p>En abiertos, la copia duplica pago y reserva. En casos con recuperación, el efecto se calcula como incurrido menos recuperación una sola vez. No se resta otra franquicia. En tres pólizas hay dos parejas de eventos diferentes; depurar no significa conservar un solo siniestro por póliza.</p>',
        table(year),
        f'<img alt="Materialidad por ramo y riesgo de depurar con claves demasiado cortas" src="data:image/png;base64,{image}">',
        '<h2>Regla propuesta y límites de aplicación</h2>',
        '<ol><li>Trabajar sobre el snapshot de claims valorado a 31-12-2024 y la cohorte exacta de D40. Verificar hashes y esquema; no descubrir automáticamente nuevos grupos al aplicar la decisión.</li>',
        '<li>Exigir dos miembros con claim_id distintos e igualdad de los once campos restantes, incluidos estado, los tres importes e identificadores de reparador y tercero. Tolerancia numérica cero.</li>',
        '<li>Verificar que ambos se asignan al mismo row_id, o que ambos tienen el mismo estado explícito anterior a la historia. Una ambigüedad de cobertura bloquea el tratamiento de esa pareja.</li>',
        '<li>Para esta cohorte, conservar CL+8 dígitos y proponer excluir su gemelo CL+9. La longitud del ID sirve solo para elegir el representante tras comprobar igualdad. No truncar el ID largo ni convertirlo a número para reconstruir otro.</li>',
        '<li>Si se aprueba, crear otra capa derivada, una bitácora de las 604 exclusiones y un mapa ID excluido→ID conservado. Mantener ambos registros originales, su posición, huella de contenido, importes y asignación. No reescribir los historiales o informes previos.</li>',
        '<li>Enviar a revisión cualquier diferencia de valor, presente frente a ausente, grupo de tamaño distinto de dos, conflicto de asignación, nuevo formato o cambio de esquema. No fusionar versiones abiertas/cerradas ni escoger automáticamente la de mayor importe.</li></ol>',
        '<p>Los once campos de igualdad, hashes, posiciones, representante y efecto hipotético quedan en <a href="tables/proposed_pair_actions.csv">la propuesta por pareja</a>. La regla estructurada está en <a href="proposed_rule.json">proposed_rule.json</a>. No existe una tabla depurada en esta carpeta.</p>',
        '<h2>Controles que impiden una depuración demasiado amplia</h2>',
        '<p>Después de distinguir los gemelos exactos en una vista diagnóstica, siguen existiendo 57 parejas de registros no idénticos con igual póliza y fecha de ocurrencia. De ellas, 17 comparten también peligro; una comparte además report_date. La regla propuesta conserva todos esos registros: sus diferencias no se resuelven por suposición.</p>',
        '<p>M83268515 contiene dos own_damage ocurridos el 01-10-2024 y reportados el 22-10-2024. CL19172982 está abierto, con pago 290,31 CU, incurrido 1.503,24 CU y reparador RP0051. CL75369456 está cerrado, con pago/incurrido 3.177,35 CU y reparador RP0487. Podrían requerir investigación de evento o versión, pero DUP01 no autoriza fusionarlos.</p>',
        '<p>M63592395 tiene dos third_party_prop del 16-04-2022 con terceros TP8386915 y TP2577127, distintos reportes e importes. Varios perjudicados son una explicación posible, no confirmada. Conservarlos evita asumir que una fecha identifica un único expediente.</p>',
        '<p>Una regla por póliza+peligro+ambas fechas alcanzaría 605 grupos en lugar de 604; por póliza+peligro+ocurrencia, 621; por póliza+ocurrencia, 661. Coincidir en menos campos no basta para eliminar esos casos adicionales.</p>',
        '<h2>Once casos seleccionados y sus historias completas</h2>',
        '<p>Los ejemplos cubren los tres ramos, mayor importe, reserva abierta, recuperación, rechazado, fuera de historia, dos eventos duplicados en la misma póliza y dos controles no idénticos. Los casos extremos se eligen con criterio documentado; la revisión cubre toda la cohorte, no solo los ejemplos.</p>',
        '<label for="case">Caso</label><select id="case">'+options+'</select><p id="reason"></p><div id="pair"></div>',
        '<h3>Periodos de póliza de entrenamiento</h3><div id="periods"></div><h3>Todos los siniestros proporcionados de esta póliza</h3><div id="claims"></div>',
        '<p>La historia conserva también los otros '+str(s['other_claim_records_on_affected_policies'])+' registros de siniestro de las 601 pólizas afectadas. No se borran eventos adicionales por pertenecer a una póliza revisada. Los controles tienen todos sus expedientes visibles. “exclude_if_approved” es un rol propuesto, no una exclusión aplicada.</p>',
        '<h2>Explorar las 604 parejas</h2><p>Buscar por póliza, ID de cualquiera de los miembros, grupo o peligro. Elegir una pareja muestra toda su historia, no solo el evento duplicado.</p>',
        '<input id="search" aria-label="Buscar pareja" placeholder="Buscar póliza, claim_id, peligro…"><select id="group" aria-label="Pareja para explorar"></select><p id="groupcount"></p>',
        '<details><summary>Todos los grupos y propuesta de representación</summary>'+table(proposed[proposal_cols])+'</details>',
        '<div class="limit"><p>La evidencia es fuerte para una regla operativa de depuración de este snapshot, pero no hay event_id, número de factura, timestamps de creación/revisión o confirmación externa que prueben que cada pareja representa un único evento real. La recomendación es una inferencia del proyecto y requiere decisión humana antes de aplicarse.</p>',
        '<p>Las reglas no se eligen por score, magnitud del coste o número deseado de filas. El snapshot financiero es de 2024; no se atribuye este conocimiento a un corte histórico anterior. No se usa ID largo/corto como predictor de riesgo.</p></div>',
        '<h2>Evidencia y reproducción</h2>',
        f'<p>Pasaron {verification["checks_count"]} controles propios de datos y propuesta, con reconstrucción de pares por un algoritmo de tuplas, asignación por fechas, consistencia exacta de importes y conservación de todos los inputs. Son verificaciones propias asistidas por IA; no validación independiente. La comprobación del explorador con DOM mínimo y enlaces se conserva aparte y no acredita renderizado en navegador.</p>',
        '<p>Desde C:/dev/Hakaton: <code>Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Revision_duplicados/review_pairs.py"</code>, seguido de <code>Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Revision_duplicados/verify_pairs.py"</code>. Cada análisis crea una versión nueva. No hay comandos de aplicación o depuración en esta revisión.</p>',
        '<p><a href="summary.json">Resumen</a> · <a href="verification.json">Verificación</a> · <a href="tables/frozen_pair_members.csv">Los 1.208 registros</a> · <a href="tables/proposed_pair_actions.csv">Propuesta de las 604 parejas</a> · <a href="tables/materiality.csv">Materialidad por ramo/año/estado</a> · <a href="tables/all_affected_policy_summary.csv">Resumen de las 601 pólizas</a> · <a href="tables/nonidentical_collision_controls.csv">Controles no idénticos</a> · <a href="tables/affected_claim_histories.parquet">Historias de siniestros</a> · <a href="tables/affected_policy_histories.parquet">Historias de pólizas</a> · <a href="evidence/official_data_description.md">Diccionario archivado</a></p>',
        '<p>IAA Documentación §2 y §§4–6: fuente, linaje, decisión y reproducción. Gobernanza §2.8: alcance de verificación propia. Consideraciones profesionales §3.2 y §§3.5–3.6: explicación de casos y responsabilidad humana. Referencias educativas, sin certificación. No hubo correcciones, entrenamiento, llamadas a proveedores, envíos o delegación.</p>',
        '<noscript><p>El explorador requiere JavaScript; los datos completos permanecen disponibles en los CSV y Parquet enlazados.</p></noscript>',
        '<script>const examples='+json.dumps(selection,ensure_ascii=False).replace('</','<\\/')+';',
        'const proposal='+proposed.to_json(orient='records',date_format='iso').replace('</','<\\/')+';',
        'const histories='+json.dumps(grouped,ensure_ascii=False).replace('</','<\\/')+';',
        'const policyFields='+json.dumps(policy_cols)+';const claimFields='+json.dumps(claim_cols)+';',
        '''function putTable(id,rows,fields){const node=document.getElementById(id);node.replaceChildren();const table=document.createElement('table');const head=table.createTHead().insertRow();for(const field of fields){const th=document.createElement('th');th.textContent=field;head.appendChild(th);}const body=table.createTBody();for(const row of rows){const tr=body.insertRow();if(row.proposed_role==='exclude_if_approved')tr.className='proposed-exclude';for(const field of fields){let value=row[field];if(['loss_date','report_date','period_start','period_end'].includes(field)&&value)value=value.slice(0,10);tr.insertCell().textContent=value===null||value===undefined?'Sin dato':String(value);}}node.appendChild(table);}function show(line,policy,group,reason){document.getElementById('reason').textContent=reason;const h=histories[line+'|'+policy];const p=proposal.filter(x=>x.line===line&&x.policy_id===policy);putTable('pair',p,['duplicate_group','proposed_keep_claim_id','proposed_exclude_claim_id','peril','loss_date','status','observed_net_CU','assignment_status']);putTable('periods',h.periods,policyFields);putTable('claims',h.claims,claimFields);}const caseSelect=document.getElementById('case');function showExample(){const c=examples[Number(caseSelect.value)];show(c.line,c.policy_id,c.duplicate_group,c.reason);}caseSelect.addEventListener('change',showExample);showExample();const search=document.getElementById('search'),groupSelect=document.getElementById('group');function filterGroups(){const q=search.value.toLocaleLowerCase('es');groupSelect.replaceChildren();let n=0;for(const p of proposal){const text=[p.duplicate_group,p.policy_id,p.proposed_keep_claim_id,p.proposed_exclude_claim_id,p.peril].join(' ');if(text.toLocaleLowerCase('es').includes(q)){const option=document.createElement('option');option.value=p.duplicate_group;option.textContent=text;groupSelect.appendChild(option);n++;}}document.getElementById('groupcount').textContent=n+' de '+proposal.length+' parejas';}function showGroup(){const p=proposal.find(x=>x.duplicate_group===groupSelect.value);if(p)show(p.line,p.policy_id,p.duplicate_group,'Pareja '+p.duplicate_group+': historia completa de la póliza. El papel de cada ID es una propuesta sin aplicar.');}search.addEventListener('input',filterGroups);groupSelect.addEventListener('change',showGroup);filterGroups();</script></body></html>''']
    (out/'informe.html').write_text('\n'.join(html),encoding='utf-8')
