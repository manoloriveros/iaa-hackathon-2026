"""Ordena evidencia pendiente con recibos agregados existentes; no calcula nuevos diagnósticos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, sys

ROOT=Path(__file__).resolve().parents[3]; REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/prioridades_b20_20261024_v1'
INDEX=REPO/'registro/semana2_b20_prioridades_actual.json'
DOC=REPO/'docs/archivo/semana2/PRIORIDADES_Y_EVIDENCIA_PENDIENTE_B20_2023.md'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
IDENT='S2-B20-PRIORIDADES2023-v1-20261024'; STATEKEY='week_2_B20_priorities2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    RUN.mkdir(parents=True,exist_ok=False); checks=[]; changes=[]
    request='Dale, prioriza las seis carencias de B20 y concreta qué evidencia falta antes de otra prueba en 2023, sin repetir diagnósticos. Conserva B00, deja las decisiones en el foro y mantén 2024 cerrado.'
    (RUN/'user_request.txt').write_text(request+'\n',encoding='utf-8')
    si=REPO/'registro/semana2_b20_sintesis_actual.json';di=REPO/'registro/semana2_b20_contraste_minimo_actual.json'
    synth,design=read(si),read(di); gaps=read(ROOT/synth['evidence_gaps']['path']); readiness=read(ROOT/design['readiness']['path'])
    sourcepaths=[si,di,ROOT/synth['evidence_gaps']['path'],ROOT/design['readiness']['path'],ROOT/design['documentation'],ROOT/design['verification']['path'],REPO/'registro/semana2_conciliacion_nocturna_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json']
    sources=[]
    for i,p in enumerate(sourcepaths):
        snap=RUN/'sources'/f'{i:02d}_{p.name}';snap.parent.mkdir(exist_ok=True);snap.write_bytes(p.read_bytes())
        sources.append({'path':rel(p),'sha256':sha(p),'snapshot':rel(snap)})
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        assert ok,name
    for obj,key in [(synth,'evidence_gaps'),(design,'readiness'),(design,'documentation'),(design,'verification')]:
        if isinstance(obj[key],str):expected=obj['documentation_sha256'];p=ROOT/obj[key]
        else:expected=obj[key]['sha256'];p=ROOT/obj[key]['path']
        check('source reference '+obj['id']+' '+key,sha(p)==expected)
    check('six original gates', {x['id'] for x in gaps['gaps']}=={'G1','G2','G3','G4','G5','G6'})
    check('existing design remains non executable',design['can_execute'] is False and design['support_gate']=='failed')
    check('readiness has no fitted parameters',readiness['parameters_estimated']==0)
    cards=[
      {'priority':1,'gate':'G6','title':'Fijar el alcance del objetivo','before_2023_trial':'Mantener explícito el estimando observado T0 con exposición efectiva C0, unidades, corte de valoración y disponibilidad por fold. Ese encuadre ya existe y se conserva; no se necesita certificar último para una exploración limitada a ese estimando.',
       'missing_evidence':'Para hablar de último o suficiencia: desarrollo longitudinal de siniestros de ocurrencia2023, pagos/reservas/reaperturas/recuperos a cortes comparables, soporte de reporte, semántica de coberturas/capital y revisión competente del uso previsto. No existe esa acreditación en los recibos consultados.',
       'required_deliverable':'Ficha de alcance: estimando, exposición, fechas de información, uso permitido y supuestos de último separados de hechos observados; cualquier ampliación requiere fuentes y revisión identificadas.',
       'condition':'Encuadre local conservado; carencia actuarial sigue conditional. No convertirla en obligación de abrir2024 ni en veto absoluto a toda investigación2023.',
       'status':'local_conditional_scope_preserved_ultimate_not_established','dependencies':[]},
      {'priority':2,'gate':'G1','title':'Establecer un fallo residual concreto','before_2023_trial':'Una sola hipótesis material, con población, signo esperado y explicación comprobable, separada de nivel, concentración, perils, maduración y reservas.',
       'missing_evidence':'El diseño de compresión de relatividades de edificios es plausible; A/E extremos y AD inestable no establecen que la dispersión de riesgo sea el mecanismo. Falta evidencia pertinente distinta de volver a puntuar las mismas bandas o retirar casos.',
       'required_deliverable':'Nota de admisibilidad del mecanismo con afirmación refutable, fuente/fecha, alternativas explicativas y qué hecho nuevo permite distinguirlas. Si no hay ese hecho, registrar no establecido.',
       'condition':'No seleccionar otro modelo o calibrador solo por un score/A/E. Reutilizar los diagnósticos ya terminados, sin producirlos otra vez.',
       'status':'plausible_not_established','dependencies':['G6']},
      {'priority':3,'gate':'G2','title':'Resolver el soporte insuficiente del diseño propuesto','before_2023_trial':'El contraste de pendiente ya propuesto requiere soporte en ambas colas, por fold y en los futuros ámbitos internos, bajo sus reglas registradas.',
       'missing_evidence':'La banda baja tiene69 grupos positivos,31,65% del coste en el mayor y6,09 grupos equivalentes; un fold llega a91,82%. El recibo ya falla. Falta evidencia nueva legítima que cambie el soporte, no código que recalcule esas cifras. También falta el soporte de los ámbitos internos, que no se calcula ahora.',
       'required_deliverable':'Registro de procedencia de cualquier información2023 adicional o corrección material real y su efecto esperado; si existe, versión nueva de la propuesta conservando fallo y fuentes previos. No se ha establecido tal información/corrección.',
       'condition':'Con los mismos componentes y costes, no arrancar este diseño. No relajar límites, agrupar bandas, cambiar cortes o borrar siniestros para pasar. Sus umbrales son prudenciales del diseño, no reglas IAA/Kaggle ni umbrales universales para cualquier ensayo.',
       'status':'failed_for_current_slope_design','dependencies':['G1']},
      {'priority':4,'gate':'G3','title':'Justificar una modificación mínima estándar','before_2023_trial':'Vincular un único cambio al mecanismo admisible y conservar un control sencillo que separe nivel de forma. El diseño existente compara pendiente con control de nivel; no lo volvemos a diseñar.',
       'missing_evidence':'Falta necesidad sustentada y soporte para ejecutar esa modificación. No hay evidencia que exija árboles, interacciones, segmentación adicional, otro alpha o búsqueda de recetas.',
       'required_deliverable':'Ficha de necesidad/coste incremental enlazada al mecanismo y soporte, comparador, parámetros fijos, daños que se vigilan y regla de parada. Reutilizar la propuesta actual si llega a ser admisible.',
       'condition':'Más capacidad solo tras fallo material del estándar bajo objetivo/exposición correctos. La propuesta actual añade una pendiente, pero sigue no ejecutable; no se crea B21 o una receta nueva en esta revisión.',
       'status':'added_complexity_not_justified','dependencies':['G1','G2']},
      {'priority':5,'gate':'G4','title':'Cerrar el flujo de validación local sin fuga','before_2023_trial':'Tras resolver necesidad y soporte, congelar implementación solo2023, ancestría y presupuesto antes de ajustar. No se entrena un calibrador sobre toda OOF para puntuar esas mismas filas.',
       'missing_evidence':'Faltan adaptador de ámbito2023 y manifiesto de todos los objetos aprendidos, incluidos C0, curvas, mezclas, transformaciones y calibración. Para el contraste existente, cada pareja interna debe excluir fold exterior e interior. La propuesta prevé10 conjuntos internos de tres folds para edificios y10 flujos C0, pero el coste auxiliar completo sigue pendiente.',
       'required_deliverable':'Manifiesto de ámbitos/ancestros, lista de rutas y claves2023, hashes, caché por conjunto de entrenamiento, inventario de cada ajuste auxiliar, recursos y límite de parada. Preflight del flujo real con rechazo de año/IDs ajenos y perturbación de etiquetas excluidas antes de datos reales. No se implementa ni repite una suite ahora.',
       'condition':'Una futura preinscripción debe fijar comparador, métrica primaria, salvaguardas por fold/negocio/ramo, nivel e influencia y coste antes de fit. Sería exploratoria; cinco folds compartidos o bootstrap OOF no restauran confirmación independiente.2024/test siguen cerrados.',
       'status':'scoped_preflight_and_learning_uncertainty_open','dependencies':['G1','G2','G3']},
      {'priority':6,'gate':'G5','title':'Separar prueba exploratoria de promoción','before_2023_trial':'Dejar B00 como referencia y todas las alternativas. Una investigación2023 no necesita fingir que ya pasó promoción; tampoco puede promover al terminar por su punto de score.',
       'missing_evidence':'Para promoción/uso posterior faltan los recibos aplicables de la política común: mejora útil e intervalo simultáneo admisible, escenarios, población nueva, segmentos, influencia, advertencias y acta del procedimiento autorizado. Esta tarea no los consulta o genera.',
       'required_deliverable':'Registro de elegibilidad local separado de acta/recibos de promoción y de revisión humana real para uso actuarial. Ningún estado documental equivale a aprobación.',
       'condition':'No abrir2024, ledger,actas oSEL01; no fijar roster ni retirar candidatos. La falta de promoción no es por sí sola un bloqueo a un ensayo2023 que cumpla sus condiciones propias.',
       'status':'promotion_not_evaluated_no_change','dependencies':['G4']}
    ]
    check('all six priorities mapped once',len(cards)==6 and {x['gate'] for x in cards}=={x['id'] for x in gaps['gaps']})
    check('dependency order valid',all(next(z['priority'] for z in cards if z['gate']==dep)<x['priority'] for x in cards for dep in x['dependencies']))
    matrix={'id':IDENT,'author':'Codex','utc':now(),'priority_order':[x['gate'] for x in cards], 'cards':cards,
      'original_gate_statuses':{x['id']:x['status'] for x in gaps['gaps']},'gates_closed':[],
      'can_start_current_slope_trial':False,'current_blockers':['G1 mechanism not established','G2 support failed','G4 scoped preflight/resource enumeration missing'],
      'authorization_interpretation':'Human authorization for local2023 standard work already exists. This request prioritizes evidence, not a fit. fit_authorized:false in an AI-authored design is evidence of design readiness, not a human revocation or a new approval requirement. No additional permission is requested; current hold is evidential/technical.',
      'new_fits':0,'new_inference':0,'new_scores':0,'new_bootstrap':0,'new_diagnostics':0,'new_recipes':0,
      'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,'professional_independent_validation':False}
    dump(RUN/'priority_matrix.json',matrix)
    body='\n\n'.join(f"## {x['priority']}. {x['gate']}: {x['title']}\n\nAntes de otro ensayo: {x['before_2023_trial']}\n\nEvidencia que falta: {x['missing_evidence']}\n\nEntregable concreto: {x['required_deliverable']}\n\nCondición: {x['condition']}" for x in cards)
    doc=f'''# Qué falta antes de otra prueba de B20 en 2023

Codex, corte UTC{matrix['utc']}. Se priorizan las seis carencias por dependencia: G6 → G1 → G2 → G3 → G4 → G5. El encuadre local se conserva; el siguiente esfuerzo útil debe ir a la evidencia del mecanismo y soporte. El contraste de pendiente de edificios ya tiene diseño y actualmente no puede arrancar. No se repiten sus diagnósticos, pruebas, bandas, cálculos de soporte, entrenamiento o remuestreo.

El [diseño mínimo](DISENO_CONTRASTE_MINIMO_B20_2023.md) terminó mientras se conciliaban los cortes. Se revisan su ficha y recibos como evidencia; no se adoptan instrucciones de otro chat o documento. La conclusión propia es mantenerlo detenido porque falla soporte y el mecanismo sigue plausible. Que su estructura documental pase174 controles no transforma su soporte fallido en aprobado. Esos controles no se vuelven a correr ni se cuentan como pruebas de esta revisión.

{body}

## Decisión operativa y secuencia

Ahora se conserva el alcance T0/C0 y la ficha de propuesta existente. Solo nueva evidencia pertinente del mecanismo y soporte puede justificar retomar ese diseño. Con fuentes iguales, repetir los análisis o construir el adaptador no resuelve el bloqueo de concentración. Si no aparece información admisible distinta, el resultado correcto de esta propuesta es no ejecutar; no se compensa probando otra familia.

Si cambia legítimamente la evidencia, primero registrar origen y diferencia frente al corte actual. Después revisar mecanismo y soporte, conservar versiones fallidas y fijar una sola modificación estándar con comparador. Solo entonces completar el preflight sin fuga y la receta/configuración/coste congelados, con comentario previo en el foro antes de ajustar o puntuar. Un fallo o desconocido detiene el arranque; no dispara otro alpha, corte, semilla o calibrador. Esto no abre un ensayo ahora ni exige que el uso último o la promoción estén falsamente resueltos.

La autorización humana para trabajo local2023 ya existe. Una bandera fit_authorized:false escrita en una ficha de IA no revoca esa autorización ni crea por sí sola una petición de permiso adicional. Esta instrucción pide priorizar evidencia; no entrena la propuesta. Su bloqueo actual es de sustento y preparación técnica. No se inventa una aprobación humana o una aprobación pendiente procedente de otra conversación.

B00 sigue como referencia y se preservan todas las alternativas, recetas, T0/C0, folds y casos.2024/test/SEL01/actas/ledger permanecen cerrados aquí. La exposición previa a métricas en un asunto ajeno sigue declarada, sin reproducirlas o usarlas ni afirmar ceguera completa. No remoto, envíos, mensajes externos, delegación o cambios a automatizaciones. Las conclusiones son exploratorias tras búsqueda adaptativa; revisión propia de Codex, sin revisión profesional independiente. Se aplican las prácticas IAA de propósito§3.1, gobernanza§2.8 y documentación§3 al alcance y trazabilidad, sin atribuirles nuestros umbrales.

[Síntesis](SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md), [última conciliación](VIGENCIA_B20_E_INCIDENCIA_20261024.md), [incendio/AD](INCENDIO_Y_AD_B20_2023.md) e [índice de prioridades](../../registro/{INDEX.name}). Matriz con dependencias, fuentes congeladas, decisiones y recibos en {rel(RUN)}. Ninguna carencia se cierra por esta priorización.
'''
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    journal={'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'PRIO-01','decision':'Ordenar G6/G1/G2/G3/G4/G5 por dependencia, conservando los seis estados abiertos.'},
      {'id':'PRIO-02','decision':'Mantener el encuadre condicional2023; no exigir prueba completa de último para todo ensayo exploratorio.'},
      {'id':'PRIO-03','decision':'No repetir diagnósticos ni entrenamiento para resolver soporte que ya falla; no alterar umbrales o casos.'},
      {'id':'PRIO-04','decision':'Reutilizar diseño pendiente; preflight detallado solo después de mecanismo y soporte admisibles.'},
      {'id':'PRIO-05','decision':'La validación exploratoria2023 no sustituye confirmación, promoción o revisión actuarial.'},
      {'id':'PRIO-06','decision':'Preservar B00/alternativas y2024cerrado; ningún cambio de modelo o automatización.'},
      {'id':'PRIO-07','decision':'No convertir banderas de un documento de IA en autoridad humana o permiso adicional. Autorización local vigente; no arranque por carencias de evidencia.'}]}
    dump(RUN/'decision_journal.json',journal)
    forum_id='COD-S2-20261024-047'
    forum_body=f'''Codex, respuesta a la instrucción directa de priorizar las seis carencias, a046 y B20-DESIGN-RESULT. Orden por dependencia:G6 alcance →G1 mecanismo →G2 soporte →G3 modificación mínima →G4 flujo sin fuga →G5 promoción. Se conserva el alcance local T0/C0; último y promoción no se declaran resueltos ni son requisitos fingidos de toda exploración2023.

El contraste de pendiente ya diseñado sigue no ejecutable: mecanismo plausible, soporte fallido y preflight/recursos incompletos. Reutilizo el recibo: banda baja edificios69grupos positivos,31,65% mayor componente y6,09 equivalentes; un fold91,82%. No nuevos cálculos, diagnósticos o suites. Falta evidencia2023 nueva legítima que cambie mecanismo/soporte; con los mismos costes/componentes, código adicional no resuelve el incumplimiento. No se relajan reglas del diseño o borran casos para pasar; esos límites no son reglas IAA/Kaggle universales.

Cada G tiene evidencia faltante, entregable y condición en {rel(DOC)} y matriz {rel(RUN/'priority_matrix.json')}. Después de mecanismo/soporte admisibles, faltan adaptador estricto2023, ancestros que excluyan fold externo/interno también enC0, inventario de auxiliares/coste, preflight del flujo y receta congelada con comentario previo a fit/score. No calibrar sobre toda OOF ni crearB21, otroalpha o más capacidad por puntos2023. La bandera de una ficha deIA no es una nueva orden humana: autorizaciónlocal2023 existe; la detención actual responde a evidencia/técnica, sin pedir otra aprobación por inferencia.

PRIO-01 aPRIO-07 conservan G1-G6 abiertas. Cero ajustes, modelos, inferencias, scores, remuestreos o recetas. B00 y todas las alternativas conservados;2024/test/SEL01/actas/ledger cerrados. Exposición previa de un asunto externo declarada, sin usar métricas ni afirmar ceguera completa. Revisión propia exploratoria, sin aprobación humana o revisión profesional independiente. Sin cambios a automatizaciones, otros chats o mensajes externos.'''
    fp=RUN/'forum_047.md';fp.write_text(forum_body,encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',forum_id,'--asunto','Prioridad de seis carencias B20 y evidencia antes de otro ensayo2023','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;receipt=json.loads(proc.stdout);dump(RUN/'forum_receipt.json',receipt)
    index={**{k:v for k,v in matrix.items() if k!='cards'},'status':'prioritized_six_open_gaps_current_trial_blocked_no_new_diagnostics','path_base':'workspace_root','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'matrix':{'path':rel(RUN/'priority_matrix.json'),'sha256':sha(RUN/'priority_matrix.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')},'forum_result':forum_id,'sources':sources}
    dump(INDEX,index)
    def change(path,fn):
        before=path.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,data in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/path.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
        tmp=path.with_name(path.name+'.prioridadesB20.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert path.read_bytes()==before,'Concurrent change '+rel(path);os.replace(tmp,path)
        changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path)})
        with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(changes[-1])+'\n')
    entry={'id':IDENT,'author':'Codex','completed_utc':now(),'run':rel(RUN),'documentation':rel(DOC),'index':rel(INDEX),'forum_result':forum_id,'new_fits':0,'new_diagnostics':0,'new_scores':0}
    nextstep='Read prioritized six-gap evidence matrix. Current slope design remains blocked by mechanism/support and missing scoped preflight. Reuse completed diagnostics; no fit, recalibration, alpha or source-identical repeats. Await/assess genuine relevant2023 evidence before a frozen standard recipe; own2024/test closed. Existing overnight window and07:00Bogota balance retained.'
    def night(raw):
        n=json.loads(raw);assert not any(x['id']==IDENT for x in n['completed_units']);completed=n['completed_units']+[entry]
        vals={'completed_units':completed,'latest_completed_unit':entry,'latest_b20_priorities_index':rel(INDEX),'updated_utc':now()}
        if n.get('current_unit') is None:vals.update(next_unit_before_B20_priorities=n.get('next_unit'),next_unit=nextstep,queue=[nextstep,'No new confirmation, promotion, roster or external actions.'])
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(NIGHT,night)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,index))
    section=f'''\n\n## Prioridad de las seis carencias de B20 antes de otra prueba2023

Codex, UTC{now()}. Instrucción directa del participante y decisiones PRIO-01 aPRIO-07, foro047. Orden por dependencia:G6 alcance,T0/C0 condicional;G1 mecanismo;G2 soporte;G3 cambio mínimo estándar;G4 flujo sin fuga;G5 promoción. Informe {rel(DOC)}, índice {rel(INDEX)} y matriz privada con evidencia faltante/entregable/condición por cada G. Se conserva el diseño mínimo terminado simultáneamente: su mecanismo sigue plausible, soporte falla y preflight/coste están incompletos. No se repitieron diagnósticos, suites, scores, OOF, cálculos de soporte o entrenamientos. Ninguna G se cierra.

La falta de sustento de último y promoción se mantiene, separada del encuadre suficiente para investigación condicional2023. No calibrar sobre toda OOF o forzar bandas/casos/umbrales para pasar; el bloqueo actual de soporte no se resuelve con código o nuevas consultas a las mismas filas. Primero evidencia nueva pertinente del mecanismo/soporte; solo después preflight2023, ancestros/C0 internos, presupuesto completo y receta/comentario previos. La autorización local humana existe; una bandera de fichaIA no crea aprobación humana pendiente. No se solicita permiso adicional por inferencia y no se inicia fit.

B00 y alternativas conservados; cero nuevas estimaciones, predicciones, scores, remuestreos o recetas.2024/test/SEL01/actas/ledger cerrados aquí; exposición previa de asunto externo declarada, sin usar cifras o afirmar ceguera completa. Comprobación propia exploratoria, no revisión profesional independiente. Otras conversaciones/automatizaciones y ventana nocturna sin cambios.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(REPO/'docs/archivo/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+f"\n\n## Priorización de carencias por instrucción del participante\n\nCodex,{now()}. [Seis carencias y evidencia pendiente](PRIORIDADES_Y_EVIDENCIA_PENDIENTE_B20_2023.md), foro047. Orden G6/G1/G2/G3/G4/G5, alcance local separado de último/promoción. El contraste mínimo existente permanece no ejecutable por mecanismo/soporte/preflight. No se repiten diagnósticos o entrenamiento, no se relajan límites para pasar. B00 y alternativas conservados,2024cerrado. Ventana/automatizaciones sin cambios.\n")
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_b20_priorities_index',rel(INDEX)),'week_2_b20_priorities_report',rel(DOC)))
    check('frozen source snapshots exact',all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources))
    for x in sources:check('source unchanged '+Path(x['path']).name,sha(ROOT/x['path'])==x['sha256'])
    before=read(RUN/'registration_cuts/before'/NIGHT.relative_to(ROOT));after=read(RUN/'registration_cuts/after'/NIGHT.relative_to(ROOT))
    check('prior completions preserved',after['completed_units'][:-1]==before['completed_units'])
    check('current unit preserved',after.get('current_unit')==before.get('current_unit'))
    check('schedule and closure preserved',after['window_end']==before['window_end'] and after['automation_id']==before['automation_id'] and after['confirmation_2024_open'] is False)
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/('Preparaci'+chr(243)+'n')/name
        check('append prefix '+name,(RUN/'registration_cuts/after'/p.relative_to(ROOT)).read_bytes().startswith((RUN/'registration_cuts/before'/p.relative_to(ROOT)).read_bytes()))
    verification={'id':IDENT,'author':'Codex','utc':now(),'passed':len(checks),'failed':0,'checks':checks,'scope':'Document/reference/registration integrity only. No model, numerical diagnostic or prior test suite rerun.'}
    dump(RUN/'verification.json',verification);dump(RUN/'registration.json',{'changes':changes,'active_catalog_mutations':0,'counter_mutations':0,'new_fits':0})
    with INDEX.open('w',encoding='utf-8') as f:json.dump({**index,'verification':{'path':rel(RUN/'verification.json'),'sha256':sha(RUN/'verification.json'),'passed':len(checks),'failed':0}},f,ensure_ascii=False,indent=2)
    files=[q for q in RUN.rglob('*') if q.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(q),'sha256':sha(q)} for q in files]})
    print(json.dumps({'id':IDENT,'forum':forum_id,'document':rel(DOC),'priority_order':matrix['priority_order'],'integrity_checks':len(checks),'failed':0,'new_diagnostics':0,'new_fits':0},ensure_ascii=True))

if __name__=='__main__':main()
