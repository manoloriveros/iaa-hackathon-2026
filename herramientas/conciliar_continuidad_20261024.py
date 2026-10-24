"""Conciliación incremental de cortes y anuncio público; sin datos por fila ni modelos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/continuidad_20261024T0310Z_v1'
PLAN = REPO / 'registro/semana2_conciliacion_nocturna_plan_v1.json'
INDEX = REPO / 'registro/semana2_conciliacion_nocturna_actual.json'
DOC = REPO / 'docs/semana2/VIGENCIA_B20_E_INCIDENCIA_20261024.md'
NIGHT = REPO / 'registro/semana2_continuidad_nocturna.json'
ARCHIVE = REPO / 'docs/fuentes/kaggle_discusion_752144_20261024T0307Z.json'
IDENT = 'S2-CONTINUIDAD-INCIDENCIA2023-v1-20261024'
STATEKEY = 'week_2_continuity_incident2023_v1_20261024'
NOW = lambda: datetime.now(timezone.utc).isoformat()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
checks, changes = [], []

def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')

def textfile(p, value):
    with p.open('x', encoding='utf-8') as f: f.write(value)

def check(label, condition):
    checks.append({'check': label, 'passed': bool(condition)})
    if not condition:
        dump(RUN/'failure.json', {'utc': NOW(), 'checks': checks})
        raise AssertionError(label)

def top(raw, key, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    if key not in json.loads(raw):
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'
    m = re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*', raw)
    assert m, key
    _, end = json.JSONDecoder().raw_decode(raw[m.end():])
    return raw[:m.end()]+encoded+raw[m.end()+end:]

def change(path, fn):
    before = path.read_bytes()
    after = fn(before.decode('utf-8-sig')).encode('utf-8')
    if before.startswith(b'\xef\xbb\xbf'): after = b'\xef\xbb\xbf'+after
    for folder, data in [('before', before), ('after', after)]:
        p = RUN/'registration_cuts'/folder/path.relative_to(ROOT)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f: f.write(data)
    tmp = path.with_name(path.name+'.continuidad0310.tmp')
    with tmp.open('xb') as f: f.write(after); f.flush(); os.fsync(f.fileno())
    assert path.read_bytes() == before, 'Concurrent change: '+rel(path)
    os.replace(tmp, path)
    item = {'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': sha(path)}
    changes.append(item)
    with (RUN/'registration_steps.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(item)+'\n')

def forum(ident, subject, body):
    p = RUN/(ident+'.md'); textfile(p, body)
    proc = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', ident, '--asunto', subject, '--cuerpo', str(p)], capture_output=True, text=True)
    if proc.returncode: raise RuntimeError(proc.stderr)
    receipt = json.loads(proc.stdout); dump(RUN/(ident+'.receipt.json'), receipt)
    return receipt

def main():
    assert datetime.now(timezone.utc) < datetime(2026,10,24,12,tzinfo=timezone.utc)
    resume = '--resume-reader-fix' in sys.argv
    RUN.mkdir(parents=True, exist_ok=resume)
    paths = [REPO/'registro'/name for name in [
        'semana2_b20_sintesis_actual.json', 'semana2_b20_incendio_AD_actual.json',
        'semana2_incidencia_kaggle_752144.json', 'semana2_desarrollo2023_actual.json',
        'semana2_contadores_propios_actual.json']]
    synth, fire, oldincident, dev, counters = map(read, paths)
    paths += [ROOT/synth['evidence_gaps']['path'], ROOT/synth['report']['path'],
              ROOT/fire['report']['path'], ROOT/fire['verification']['path'], ARCHIVE,
              ROOT/synth['documentation'], ROOT/fire['documentation']]
    frozen=[]
    if resume:
        frozen = read(PLAN)['frozen_sources']
    else:
        for i,p in enumerate(paths):
            snap=RUN/'sources'/f'{i:02d}_{p.name}'; snap.parent.mkdir(exist_ok=True)
            with snap.open('xb') as f: f.write(p.read_bytes())
            frozen.append({'path':rel(p),'sha256':sha(p),'snapshot':rel(snap)})
    plan={'id':IDENT,'author':'Codex','utc':NOW(),'purpose':'Conciliar la síntesis anterior con incendio/AD ya terminado y registrar el anuncio HOST nuevo; corregir la cola obsoleta sin repetir diagnósticos.',
          'scope':'JSON/Markdown agregados2023 y discusión pública752144; ninguna lectura de OOF, modelos, originales,2024,test,ledger,SEL01 o actas.',
          'hypothesis':'El nuevo corte de incendio/AD acota la concentración sin cerrar los seis requisitos pendientes; un anuncio HOST de arreglo no prueba recepción/scoring propio.',
          'acceptance':['Cortes y SHA íntegros; el corte anterior excluía incendio/AD','Cotejar solo recibos y conclusiones nuevas, sin repetir matemática ya verificada','HOST, fecha y mensaje nuevos cotejados contra archivo previo','No cerrar G1-G6 ni certificar scoring por anuncio','Preservar catálogo, contadores, fuentes históricas y trabajo concurrente'],
          'frozen_sources':frozen,'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_bootstrap':0,'new_recipes':0,
          'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,
          'forum_prior':'COD-S2-20261024-045','forum_result':'COD-S2-20261024-046','stop':'Una conciliación documental finita; no seleccionar B21, alpha o calibrador.'}
    if resume:
        plan=read(PLAN)
        prior=read(RUN/(plan['forum_prior']+'.receipt.json'))
        p=ROOT/fire['readout']['path']; snap=RUN/'sources/12_readout.json'
        with snap.open('xb') as f: f.write(p.read_bytes())
        added={'path':rel(p),'sha256':sha(p),'snapshot':rel(snap)}
        amendment={'id':IDENT+'-reader-fix','utc':NOW(),'base_plan_sha256':sha(PLAN),'added_source':added,'reason':'First attempt stopped with KeyError findings before shared writes; findings live in readout.json, not the index. No previous numerical result changed.','reader_change':'Read explicit readout reference with SHA validation; preserve original plan/cut.','first_failure':'KeyError: findings at reader line101; exit1 observed at03:13UTC','new_model_or_score':False}
        dump(RUN/'reader_amendment.json',amendment)
        dump(RUN/'first_attempt_failure.json',{'utc_observed':'2026-10-24T03:13:13Z','exception':'KeyError: findings','stage':'after preregistration and source/receipt checks; before result/forum/shared registration','shared_writes':False,'new_fits':0,'resolution':rel(RUN/'reader_amendment.json')})
        forum('COD-S2-20261024-045A','Enmienda del lector de conciliación antes de continuar',f"Codex. El intento de045 se detuvo por KeyError:findings: los hallazgos están en readout.json, no en el índice. Sin cambios compartidos, cálculo numérico, ajuste o score. Conservo plan y corte; enmienda {rel(RUN/'reader_amendment.json')}, SHA{sha(RUN/'reader_amendment.json')}, añade únicamente el recibo readout existente con SHA congelado. Continúan criterios, seis carencias abiertas y2024/testcerrados; no cambia una receta o resultado previo.")
        frozen=frozen+[added]
    else:
        dump(PLAN,plan)
        prior=forum(plan['forum_prior'],'Conciliación incremental2023 y anuncio de corrección Kaggle, sin estimación',
            f"Codex. Plan {IDENT}, SHA {sha(PLAN)}. Responde a 044 y B20-SYNTH-RESULT. Conciliaré únicamente los cortes ya guardados y el anuncio nuevo de HOST752144; la síntesis existente excluía incendio/AD. Criterio: fuentes exactas, fechas/alcance compatibles, seis carencias abiertas, anuncio separado de recepción/scoring propio. No OOF, modelos, replays, ajustes, scores, remuestreo o nuevas recetas. B00 y todas las alternativas conservados;2024/test/SEL01/actas/ledger cerrados. Se corregirá la cola obsoleta preservando concurrencia, sin tocar automatizaciones. Plan: {rel(PLAN)}.")
    gaps=read(ROOT/synth['evidence_gaps']['path'])
    check('preregistration before reconciliation', prior['utc'] < NOW())
    check('source snapshots exact',all(sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256'] for x in frozen))
    for obj,field in [(synth,'evidence_gaps'),(synth,'report'),(fire,'report'),(fire,'verification')]:
        check('index receipt '+obj['id']+' '+field,sha(ROOT/obj[field]['path'])==obj[field]['sha256'])
    check('six original gates retained', [x['id'] for x in gaps['gaps']]==['G1','G2','G3','G4','G5','G6'])
    check('prior synthesis excluded fire source', 'fixedfire' not in synth['source_indices'] and 'fire' not in synth['source_indices'])
    check('fire receipt has no failures',read(ROOT/fire['verification']['path'])['failed']==0)
    check('readout reference exact',sha(ROOT/fire['readout']['path'])==fire['readout']['sha256'])
    findings=read(ROOT/fire['readout']['path'])
    check('AD descriptive only retained',findings['data_composition_is_not_causal_identification'] and findings['same_AD_target_all_perils'])
    check('fire net and gross denominators explicit', {'fire_row_of_selected_net','fire_row_of_global_net','fire_component_of_global_gross_positive_groups'} <= findings['explicit_shares'].keys())
    oldraw=read(ROOT/oldincident['source']['path']); newraw=read(ARCHIVE)
    topic=lambda x:json.loads(next(c['text'] for c in x['response']['content'] if c['type']=='text'))['forum_topic']
    ot,nt=topic(oldraw),topic(newraw)
    oldids={x['id'] for x in [ot['first_message']]+ot['comments']}
    msg=next(x for x in nt['comments'] if x['id']==3543798)
    check('topic identity',nt['id']==ot['id']==752144)
    check('new host message exact',msg['id'] not in oldids and msg['author_type']=='HOST' and msg['post_date']=='2026-10-24T02:57:36.893Z' and msg['raw_markdown']=='Hi Everyone,\n\nThis issue has been resolved and you should now be able to submit against the leaderboard.')
    check('older thread text retained',all(any(y['id']==x['id'] and y['raw_markdown']==x['raw_markdown'] for y in [nt['first_message']]+nt['comments']) for x in [ot['first_message']]+ot['comments']))
    updates=[
      {'gate':g['id'],'original_status':g['status'],'status_after_new_cut':g['status'],'closure':False,
       'incremental_evidence':{'G1':'Concentración y composición AD descriptivas; no mecanismo causal exclusivo.',
       'G2':'No nueva evidencia prospectiva o soporte para factores por banda.',
       'G3':'AD cruza uno aun con ridge; cambiar capacidad no queda justificado.',
       'G4':'Omitir un incendio en evaluación no crea validación nueva; advertencia31grupos intacta.',
       'G5':'No promoción, retiros, roster o acta evaluados.',
       'G6':'Traza confirma siniestros válidos, no último o suficiencia de reservas.'}[g['id']]} for g in gaps['gaps']]
    dump(RUN/'gate_delta.json',{'source':rel(ROOT/synth['evidence_gaps']['path']),'updates':updates})
    report={'id':IDENT,'author':'Codex','utc':NOW(),'scope':'incremental document reconciliation only',
        'old_synthesis':synth['id'],'new_saved_diagnostic':fire['id'],'gates':updates,
        'host_announcement':{'topic':752144,'id':msg['id'],'utc':msg['post_date'],'role':msg['author_type'],'announces_fix':True,'source':rel(ARCHIVE),'source_sha256':sha(ARCHIVE)},
        'platform_fix_verified':False,'own_submission_attempt':False,'acceptance_scoring_verified':False,
        'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_bootstrap':0,'new_recipes':0,
        'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,
        'professional_independent_validation':False,'prior_external2024_header_exposure_disclosed':True}
    dump(RUN/'report.json',report)
    rows='\n'.join('| '+u['gate']+' | '+u['incremental_evidence']+' | Abierta |' for u in updates)
    doc=f'''# Vigencia de las decisiones de B20 y novedad de Kaggle

Codex, corte UTC {report['utc']}. La [síntesis anterior](SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md) ya estaba terminada y dejó seis requisitos pendientes. Su corte excluía el diagnóstico concurrente de [incendio y AD](INCENDIO_Y_AD_B20_2023.md), terminado después como unidad registrada. Esta conciliación añade ese alcance y corrige una cola que todavía pedía repetir la síntesis. No repite cálculos, suites, modelos o remuestreo.

## Qué cambia con el último diagnóstico

El incendio fijado explica el 93,9% de la ganancia neta de los doce grupos seleccionados previamente, el 35,8% de la global neta y el 7,2% de la mejora bruta positiva global por componente. Son denominadores distintos. El punto global sin ese incendio sigue positivo, pero no resuelve la sensibilidad anterior a 31 grupos elegidos por sus resultados. No se borra un siniestro ni cambia el objetivo.

AD es negativo en el fold3 de B19 y B20. Los dos incendios fijados no pertenecen al ajuste de ese fold. Esa composición es compatible con sensibilidad a pocos costes grandes, sin identificar causa única ni justificar restricciones de signo, máscaras, nuevos efectos o reajuste. El objetivo conserva todos los perils. Las influencias locales reutilizadas son aproximaciones de B19; no se atribuyen a B20.

| Requisito anterior | Consecuencia de la evidencia añadida | Estado |
| --- | --- | --- |
{rows}

Los estados originales se conservan literalmente en gate_delta.json. No se propone B21, otro alpha, normalización, eliminación de casos o una recalibración por quintiles. B00 sigue como referencia y permanecen todas las alternativas. Las advertencias de edificios y autos nuevos siguen abiertas. El siguiente trabajo de estimación requiere evidencia distinta de un mecanismo material, diseño finito y preinscripción; repetir los scores de2023 no aporta esa evidencia.

## Corrección anunciada por el organizador

En la [discusión752144](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752144), HOST anunció el 24 de octubre a las 02:57:36 UTC que el problema estaba resuelto y que los participantes podían enviar. Mensaje3543798, observado mediante Kaggle MCP y conservado en una [fuente nueva](../fuentes/{ARCHIVE.name}). La fuente anterior se preserva. La identidad de HOST, texto, fecha y permanencia de los mensajes anteriores se cotejan en este ciclo.

El estado pasa a corrección anunciada, con recepción/scoring propios sin verificar. No hubo envío propio, acceso al evaluador o verificación de la causa interna. El contrato emergente sigue en209.063 filas y row_id,prediction, según el cotejo histórico, que no se repite. El anuncio no autoriza enviar, abrir2024/test o modificar la política de selección.

## Continuación y límites

No hay tareas de entrenamiento pendientes en estos cortes ni procesos Python visibles en la comprobación local. La consulta CIM no estuvo disponible; ese límite se conserva y no prueba ausencia de procesos ocultos o de trabajo ajeno. El índice de desarrollo y el contador propio no cambian:195 ajustes de precio y285 constantes en el corte. Ningún ajuste o suite anterior se repite.

Próximo corte nocturno: comprobar novedades reales y conciliar una ejecución registrada si apareciera; con fuentes iguales, conservar los diagnósticos terminados y preparar el balance de las07:00 Bogotá. Para más estimación sigue faltando un mecanismo y diseño que cumplan los requisitos abiertos. La autorización nocturna permite avanzar ante evidencia nueva; esta unidad no la sustituye por otra autorización.

2024/test/SEL01/actas/ledger permanecen cerrados aquí. Se conserva la exposición previa a métricas en un asunto externo, sin repetirlas o usarlas. Las conclusiones son exploratorias tras búsqueda adaptativa y comprobaciones propias de Codex, no revisión profesional independiente o aprobación humana. Las prácticas IAA de documentación§3 y gobernanza§2.8 se aplican al alcance y la procedencia, sin certificar la aptitud actuarial. No se cambian otras automatizaciones, frecuencia o ventana.

El primer intento del lector se detuvo por KeyError al buscar findings en el índice. Los hallazgos estaban en readout.json. Se conserva el fallo, plan y corte originales; la enmienda045A congeló ese recibo antes de continuar. No se cambió ningún resultado anterior.

[Plan](../../registro/{PLAN.name}), [índice de conciliación](../../registro/{INDEX.name}) y [estado de la incidencia](../../registro/semana2_incidencia_kaggle_752144.json). Recibos, cortes, enmienda del lector y registro de decisiones en {rel(RUN)}.
'''
    textfile(DOC,doc)
    decisions=[{'id':'CONT-01','decision':'Reutilizar síntesis terminada; añadir solo el alcance incendio/AD y corregir cola obsoleta.','evidence':[synth['id'],fire['id']]},
               {'id':'CONT-02','decision':'Mantener G1-G6 abiertas; no nueva receta o promoción por este corte.','evidence':rel(RUN/'gate_delta.json')},
               {'id':'CONT-03','decision':'Registrar anuncio HOST; recepción/scoring propios no verificados y sin autorización nueva.','evidence':[rel(ARCHIVE),3543798]},
               {'id':'CONT-04','decision':'Conservar B00, catálogo, contadores y restricciones; no repetir suites iguales.','evidence':rel(PLAN)}]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':NOW(),'decisions':decisions})
    result=forum(plan['forum_result'],'Cortes B20 conciliados; HOST anuncia arreglo, scoring propio sin verificar',
        f"Codex. Resultado del plan {IDENT}, preinscrito en045. La síntesis existente se reutiliza; se incorpora solo el alcance posterior de incendio/AD (044) y se mantienen G1-G6 abiertas. El incendio pesa93,9% del neto de12grupos,35,8% del global neto y7,2% del bruto positivo global por componente; no intercambiar denominadores. ADfold3 es composición descriptiva, sin causa única o restricción de signo adoptada. No B21, alpha, calibración o promoción nuevos. HOST3543798 anunció a02:57:36UTC el arreglo en752144; fuente nueva archivada, mensajes anteriores cotejados. Solo anuncio: no recepción/scoring propios, causa confirmada o autorización de envío. No se repite cotejo de filas/test. Cero ajustes, cargas, inferencias, scores o bootstrap. Conservados B00, todas las alternativas y2024/test/SEL01/actas/ledger cerrados. Informe:{rel(DOC)}. Se corrige continuidad para no repetir síntesis y preparar balance07:00Bogotá ante fuentes sin novedades. La consulta CIM no estuvo disponible; Get-Process no mostró Python. Revisiones propias exploratorias, sin aprobación humana o revisión profesional independiente.")
    entry={'id':IDENT,'author':'Codex','completed_utc':NOW(),'run':rel(RUN),'documentation':rel(DOC),'index':rel(INDEX),'forum_result':result['id'],'new_fits':0,'new_scores':0,'new_bootstrap':0}
    index={**report,'path_base':'workspace_root','status':'incremental_cuts_reconciled_gates_open_host_fix_announced_not_scoring_verified','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'plan':rel(PLAN),'plan_sha256':sha(PLAN),'forum_prior':prior['id'],'forum_result':result['id'],'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')},'report':{'path':rel(RUN/'report.json'),'sha256':sha(RUN/'report.json')}}
    dump(INDEX,index)
    incidentpath=paths[2]
    def incident_update(raw):
        obj=json.loads(raw)
        history=obj.get('history',[])
        history.append({'status':obj['status'],'source':obj['source'],'host_response':obj['host_response'],'superseded_utc':NOW()})
        vals={'history':history,'status':'host_fix_announced_acceptance_scoring_not_verified',
              'source':{'path':rel(ARCHIVE),'sha256':sha(ARCHIVE),'retrieved_after_utc':newraw['retrieved_after_utc'],'retrieved_before_utc':newraw['retrieved_before_utc']},
              'host_response':report['host_announcement'],'host_fix_announced':True,'platform_fix_verified':False,'acceptance_scoring_verified':False,'own_submission_attempt':False,
              'latest_forum_update':result['id'],'updated_utc':NOW()}
        for k,v in vals.items(): raw=top(raw,k,v)
        return raw
    change(incidentpath,incident_update)
    nextstep='Reuse completed synthesis plus fixedfire/AD reconciliation. Monitor genuine source changes and pending registered runs; prepare07:00Bogota balance. No repeated diagnostics, fit or new complexity without distinct documented mechanism and preregistration. Own2024/test/ledger closed.'
    def night_update(raw):
        n=json.loads(raw); oldqueue=n.get('next_unit'); n['completed_units'].append(entry)
        vals={'completed_units':n['completed_units'],'latest_completed_unit':entry,'latest_continuity_reconciliation_index':rel(INDEX),'updated_utc':NOW(),
              'latest_kaggle_752144_check':{'utc':NOW(),'semantic_content_unchanged':False,'new_host_message':3543798,'announces_fix':True,'source':rel(ARCHIVE),'acceptance_scoring_verified':False,'submission_attempt':False,'test_row_check_repeated':False},
              'submission_platform_incident':{**n.get('submission_platform_incident',{}),'status':'host_fix_announced_acceptance_scoring_not_verified','latest_host_message':3543798,'effect':'Record announcement only; no authorized submission or verified scoring. Continue local2023 scope.'}}
        if n.get('current_unit') is None:
            vals.update(next_unit_before_continuity_reconciliation=oldqueue,next_unit=nextstep,status='scheduled_'+str(len(n['completed_units']))+'_units_reconciled_conditions_open',queue=[nextstep,'Preserve B00/all alternatives and all open actuarial/predictive gates.','Existing automation window unchanged; honest final balance07:00Bogota.'])
        for k,v in vals.items(): raw=top(raw,k,v)
        return raw
    change(NIGHT,night_update)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,index))
    section=f"\n\n## Conciliación de cortes nocturnos y anuncio HOST752144\n\nCodex, UTC{NOW()}. Unidad {IDENT}, foro045 previo y046 resultado. Se reutilizó la síntesis B20 terminada, añadiendo solo el corte de incendio/AD que estaba fuera: G1-G6 y advertencias permanecen abiertas. Cola obsoleta corregida, sin reentrenar o repetir matemática, suites, OOF o bootstrap. B00 y todas las alternativas conservados; contador propio195/285 sin escritura. Informe {rel(DOC)}; índice {rel(INDEX)} y decisiones CONT-01 aCONT-04 en el registro privado.\n\nHOST3543798,2026-10-24T02:57:36.893Z, anunció arreglo en752144. Nueva fuente pública archivada con SHA, anteriores preservadas. Estado: corrección anunciada; recepción/scoring propios y causa interna sin verificar. Sin envío o autorización nueva, padding o nuevo cotejo de test. La consulta CIM estuvo indisponible; Get-Process no mostró Python. No evidencia de corrida propia pendiente en el índice, sin afirmar ausencia global de trabajo ajeno.\n\n2024/test/SEL01/actas/ledger permanecen cerrados aquí; exposición previa de asunto externo declarada, sin usar métricas o afirmar ceguera completa. Cero ajustes, modelos, inferencias, scores, recetas y remuestreos. Son comprobaciones propias exploratorias, no revisión profesional independiente o aprobación humana. Siguiente corte: novedades reales/ejecución registrada y balance07:00Bogotá; ante fuentes iguales no repetir diagnósticos. Ventana y demás automatizaciones sin cambios.\n"
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    supplement=f"\n\n## Actualización UTC{NOW()}: corrección anunciada\n\nHOST3543798 anunció a las02:57:36.893UTC que la incidencia estaba resuelta. La [consulta nueva](../fuentes/{ARCHIVE.name}) conserva la respuesta Kaggle MCP y el corte anterior permanece archivado. Se cotejaron mensaje nuevo, rol HOST, fecha y mensajes previos; no se repitió el cotejo de archivos. Estado actualizado: corrección anunciada, sin verificación propia de recepción/scoring ni causa interna. No hubo envío propio; el anuncio no autoriza uno. Se mantienen contrato emergente, selección y restricciones2024/test. Foro046 e [informe de conciliación](VIGENCIA_B20_E_INCIDENCIA_20261024.md).\n"
    change(REPO/'docs/semana2/INCIDENCIA_KAGGLE_752144.md',lambda raw:raw+supplement)
    change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+f"\n\n## Conciliación incremental de cortes e incidencia\n\nCodex,{NOW()}. La [conciliación](VIGENCIA_B20_E_INCIDENCIA_20261024.md) reutiliza síntesis y añade incendio/AD sin repetirlos. G1-G6 continúan abiertas. HOST anunció arreglo752144; recepción/scoring propios sin verificar, sin envío o nuevo cotejo. La cola obsoleta se sustituye por novedades reales y balance07:00Bogotá; sin fuentes nuevas no repetir diagnósticos o añadir modelos. B00 y alternativas conservados,2024/testcerrados,195/285 al corte y cero ajustes nuevos. Ventana/frecuencia/otras automatizaciones sin cambios.\n")
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_continuity_reconciliation_index',rel(INDEX)),'week_2_continuity_reconciliation_report',rel(DOC)))
    for p in paths[:2]+paths[3:5]: check('unmodified source '+p.name,sha(p)==next(x['sha256'] for x in frozen if x['path']==rel(p)))
    after=read(NIGHT)
    check('completion recorded exactly once',sum(x['id']==IDENT for x in after['completed_units'])==1)
    check('schedule window preserved',after['window_end']=='2026-10-24T07:00:00-05:00' and after['automation_id']=='iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna')
    check('own2024 stays closed',after['confirmation_2024_open'] is False)
    check('incident announcement only',read(incidentpath)['host_fix_announced'] and not read(incidentpath)['acceptance_scoring_verified'] and not read(incidentpath)['own_submission_attempt'])
    oldnight=read(RUN/'registration_cuts/before'/NIGHT.relative_to(ROOT))
    check('previous completed units retained',after['completed_units'][:-1]==oldnight['completed_units'])
    check('foreign current unit preserved',after.get('current_unit')==oldnight.get('current_unit'))
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/('Preparaci'+chr(243)+'n')/name; b=RUN/'registration_cuts/before'/p.relative_to(ROOT); a=RUN/'registration_cuts/after'/p.relative_to(ROOT)
        check('append preserved '+name,a.read_bytes().startswith(b.read_bytes()))
    check('new source and original source retained',sha(ARCHIVE)==report['host_announcement']['source_sha256'] and sha(ROOT/oldincident['source']['path'])==oldincident['source']['sha256'])
    verification={'id':IDENT,'author':'Codex','utc':NOW(),'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'checks':checks,'scope':'Focused new integration checks; earlier suites not repeated. Shared before/after cuts distinguish later legitimate changes.'}
    dump(RUN/'verification.json',verification)
    dump(RUN/'registration.json',{'id':IDENT,'utc':NOW(),'changes':changes,'new_fits':0,'new_scores':0,'counter_mutations':0,'active_catalog_mutations':0})
    # Only this unit's index receives its final receipt; no source index is rewritten.
    raw=INDEX.read_text(encoding='utf-8'); raw=top(raw,'verification',{'path':rel(RUN/'verification.json'),'sha256':sha(RUN/'verification.json'),'passed':verification['passed'],'failed':verification['failed']}); INDEX.write_text(raw,encoding='utf-8')
    files=[p for p in RUN.rglob('*') if p.is_file()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':NOW(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]+[{'path':rel(PLAN),'sha256':sha(PLAN)},{'path':rel(DOC),'sha256':sha(DOC)},{'path':rel(INDEX),'sha256':sha(INDEX)}]})
    print(json.dumps({'id':IDENT,'checks':verification['passed'],'failed':verification['failed'],'index':rel(INDEX),'forum_result':result['id'],'new_fits':0,'new_scores':0,'status':index['status']},ensure_ascii=True))

if __name__=='__main__': main()
