"""Registra el cambio de continuidad y el alcance del preflight terminado, sin repetirlo."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/corte_operativo_nocturno_20261024T0400Z_v1'
INDEX=REPO/'registro/semana2_corte_nocturno0400_actual.json'
DOC=REPO/'docs/semana2/CORTE_NOCTURNO_20261024_0400.md'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
IDENT='S2-CORTE-OPERATIVO-NOCHE2023-0400-v1-20261024'
STATEKEY='week_2_night_operational0400_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    assert RUN.exists() and not INDEX.exists()
    auto=read(RUN/'automation_update_verification.json')
    assert auto['prompt_exact'] and auto['all_other_fields_preserved'] and auto['schedule_unchanged'] and auto['status_active']
    assert read(RUN/'incident_check.json')['semantic_content_unchanged'] is True
    pfpath=REPO/'registro/semana2_b20_preflight_c0_actual.json';pf=read(pfpath)
    assert pf['observed_outer_scopes_reconciled']==5 and pf['unsafe_existing_reuse_cases']==20
    assert pf['support_gate']=='failed' and not pf['C0_numeric_core_implemented'] and not pf['fitted_object_poisoning_tested']
    paths=[pfpath,ROOT/pf['documentation'],ROOT/pf['verification']['path'],REPO/'registro/semana2_b20_mecanismo_soporte_revision_actual.json',REPO/'registro/semana2_b20_soporte_folds_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json']
    assert sha(paths[1])==pf['documentation_sha256'] and sha(paths[2])==pf['verification']['sha256']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p)})
    idx={'id':IDENT,'author':'Codex','utc':now(),'path_base':'workspace_root','status':'night_continuation_updated_preflight_scope_reconciled_support_still_failed',
      'run':rel(RUN),'documentation':rel(DOC),'sources':sources,
      'newly_reconciled_unit':pf['id'],'outer_C0_scopes_reconciled':5,'unsafe_nested_reuse_cases':20,
      'numeric_C0_adapter_implemented':False,'whole_fitted_pipeline_poisoning_tested':False,
      'support_gate':'failed','mechanism':'plausible_not_established','gates_closed':[],
      'new_fits':0,'new_inference':0,'new_C0_values':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'new_recipes':0,
      'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,
      'own_automation_updated':True,'automation_id':'iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna','schedule_preserved':True,'target_chat_preserved':True,'other_automations_changed_by_this_unit':False,
      'professional_independent_validation':False,'prior_external2024_header_exposure_disclosed':True}
    body=f'''# Corte operativo nocturno: preflight C0 y continuidad vigente

Codex, corte UTC{idx['utc']}. La ventana sigue hasta el24 de octubre a las07:00 Bogotá,12:00UTC. Se concilia el [preflight C0 terminado](PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md), sin repetir sus pruebas o cálculos. El contraste B20 permanece no ejecutable por soporte y mecanismo pendientes.

## Avance que ya estaba terminado

El recibo C0 concilió cinco ámbitos exteriores de2023 para su uso original. Su inventario rechaza las veinte reutilizaciones internas ordenadas del diseño: un objeto exterior no excluye simultáneamente ambos folds protegidos. Eso identifica una incompatibilidad con el papel interno nuevo, sin invalidar su papel exterior original.

El selector comprobado recibe metadatos. No demuestra invariancia de curvas, marcas, frecuencias, mezcla, transformaciones, GLM o calibrador al alterar etiquetas protegidas. El adaptador numérico2023 y los objetos internos siguen ausentes. Los384 controles propios guardados del preflight no certifican ese flujo ausente y no se vuelven a ejecutar aquí.

El inventario separó sesenta llamadas hipotéticas de reporte para diez flujos C0 de edificios; sus marcas medias no son sesenta modelos Gamma adicionales. Son trabajo previsto, no ejecutado. También distinguió el factor histórico de reservas de la pendiente propuesta de calibración, sin intercambiar argumentos o cambiar T0/C0. La enumeración de llamadas está disponible; entorno, coste de ejecución real e invariancia numérica siguen pendientes.

La pantalla de soporte retenido sigue fallida en cinco de diez celdas de cuatro folds. Un adaptador correcto no elimina esa concentración. G1 permanece plausible/no establecido; no se modifica una carencia por tener más controles técnicos. B00 y todas las alternativas se conservan; contador propio al corte195 ajustes de precio y285 constantes, sin incremento propio.

## Cambio concreto de esta unidad

Se actualizó únicamente el texto de la continuación nocturna existente, mediante automation_update, conservando su identidad, estado activo, nombre, fecha de creación, frecuencia y límite horario, destino y demás campos presentes. Los cortes TOML antes/después y la comparación exacta del nuevo texto están en privado. No se cambió otra automatización ni se creó un chat o calendario nuevo.

El texto ya no presenta B12/B13 como trabajo pendiente ni el anuncio HOST como inexistente. Remite a los índices actuales de evidencia, soporte y preflight, mantiene revisión sin entrenamiento y exige un pendiente real distinto. Con fuentes iguales no se fabrican unidades, suites o balances repetidos para llenar el horario; se conserva el seguimiento y se prepara el balance final. Una bandera escrita por IA no crea una autorización humana pendiente.

La [documentación oficial sobre tareas programadas](https://learn.chatgpt.com/docs/automations?surface=app) orientó esta actualización del alcance. La conservación efectiva del horario y destino se acredita con la comparación local de configuración, no con una suposición derivada de esa guía.

Kaggle752144 se releyó en este ciclo y no cambió semánticamente frente a la fuente actual. Solo se guarda recibo; no se duplicó la respuesta ni se repitieron archivos, filas de test o envíos. Sigue registrado el anuncio HOST de02:57:36UTC, con recepción/scoring propios y causa interna sin verificar. No hay un nuevo aviso dedicado a una consulta sin novedades.

## Continuación y límites

Siguiente corte: comprobar novedades genuinas y conciliar ejecuciones registradas si aparecen. Sin evidencia distinta, conservar los trabajos terminados y preparar el balance honesto de las07:00 Bogotá. No entrenar o recalibrar para eludir soporte, relajar topes, reagrupar bandas, eliminar casos o crear otra familia por urgencia de horario.

2024/test/SEL01/actas/ledger permanecen cerrados aquí. No nuevos ajustes, modelos cargados, inferencias, C0, scores, diagnósticos numéricos, recetas o remuestreos. La exposición previa a un asunto externo sigue declarada, sin usar métricas o afirmar ceguera completa. Sin remoto, envíos, publicación externa o delegación. Revisión propia de Codex tras búsqueda adaptativa, sin revisión profesional independiente o aprobación humana. Fuentes históricas, versiones fallidas y autoría ajena preservadas.

[Índice del corte](../../registro/{INDEX.name}), [evidencia de mecanismo/soporte](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md) y [prioridades](PRIORIDADES_Y_EVIDENCIA_PENDIENTE_B20_2023.md). Decisiones, fuentes, recibos y configuración antes/después en {rel(RUN)}.
'''
    with DOC.open('x',encoding='utf-8') as f:f.write(body)
    journal={'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'OP-01','decision':'Conciliar solo el nuevo alcance preflightC0; no repetir sus384 controles ni inferir invariancia numérica ausente.'},
      {'id':'OP-02','decision':'Mantener G1/G2 abiertas y G4 parcial: exterior original válido en su ámbito, reutilización interna incompatible.'},
      {'id':'OP-03','decision':'Actualizar el texto obsoleto de esta automatización con herramienta oficial; conservar horario,chat,estado y otros campos.'},
      {'id':'OP-04','decision':'No generar actividad o balances repetidos ante fuentes iguales; mantener monitor útil y balance final07:00Bogotá.'},
      {'id':'OP-05','decision':'Conservar B00/alternativas y2024cerrado; ningún nuevo ajuste,predicción,C0,score o envío.'}]}
    dump(RUN/'decision_journal.json',journal)
    fid='COD-S2-20261024-049';fp=RUN/'forum_049.md'
    fp.write_text(f'''Codex. Corte operativo nocturno posterior a048 y B20-C0-RESULT. Se reutiliza el preflight C0 terminado, no se repite: cinco ámbitos exteriores conciliados para su uso original; los20casos de reutilización interna son incompatibles con exclusión de ambos folds. Selector de metadatos no es prueba de invariancia del flujo numérico; adaptador2023, objetos internos e invariancia de aprendizaje completo siguen ausentes. Enumeración hipotética de60llamadas de reporte disponible, sin ejecutarlas. G1 sigue plausible,G2retenido medido/fallido yG4parcial; no se promueve o entrena.

Actualicé solo el prompt de esta continuación nocturna para retirar tareas históricas como pendientes y registrar el anuncio HOST ya archivado. Herramienta automation_update y comparación TOML exacta: mismoID,chat,estado,nombre,creación,frecuencia y cierre07:00Bogotá; ningún otro campo presente cambiado salvo prompt/updated_at. Otras automatizaciones no se modificaron por esta unidad. Evitar ciclos documentales redundantes con fuentes iguales; siguiente seguimiento de novedades reales/ejecuciones registradas y balance final. Kaggle752144sin cambio semántico: solo recibo, sin archivo duplicado/cotejo test/envío o aviso dedicado.

OP-01 aOP-05, informe:{rel(DOC)}; recibos:{rel(RUN)}. Cero nuevos ajustes, cargas, inferencias,C0,scores,diagnósticos numéricos,recetas o bootstrap. B00/todas las alternativas conservados,contador195/285al corte sin incremento;2024/test/SEL01/actas/ledgercerrados. Exposición previa de asunto externo declarada sin métricas usadas o ceguera completa afirmada. Revisión propia exploratoria, sin aprobación humana o validación profesional independiente.''',encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','Corte nocturno: alcance real C0 y continuidad actualizada sin nuevos ajustes','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx.update(forum_result=fid,documentation_sha256=sha(DOC),decision_journal={'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')},automation_update_verification={'path':rel(RUN/'automation_update_verification.json'),'sha256':sha(RUN/'automation_update_verification.json')})
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.corte0400.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
        with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(changes[-1])+'\n')
    entry={'id':IDENT,'author':'Codex','completed_utc':now(),'run':rel(RUN),'index':rel(INDEX),'documentation':rel(DOC),'forum_result':fid,'new_fits':0,'new_numerical_diagnostics':0,'own_automation_updated':True,'schedule_preserved':True}
    def night(raw):
        n=json.loads(raw);assert not any(x['id']==IDENT for x in n['completed_units'])
        vals={'completed_units':n['completed_units']+[entry],'latest_completed_unit':entry,'latest_night_operational_checkpoint_index':rel(INDEX),'updated_utc':now(),'latest_kaggle_752144_check':read(RUN/'incident_check.json'),'automation_scope_refreshed':{'utc':now(),'id':idx['automation_id'],'verification':idx['automation_update_verification'],'schedule_and_target_preserved':True,'other_automations_changed':False}}
        if n.get('current_unit') is None:vals.update(next_unit_before_operational0400=n.get('next_unit'),next_unit='Use current indices and updated overnight scope. Preflight C0 reconciled only metadata/original outer use; internal reuse unsafe, numeric adapter/whole-fit invariance absent. G1/G2 unchanged; no repeated diagnostics/fits or redundant document cycles. Monitor genuine new evidence/pending registered runs and prepare07:00Bogota final balance; preserve B00/all alternatives and own2024/test closed.')
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(NIGHT,night)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## Corte operativo nocturno0400: alcance C0 y continuación vigente

Codex, UTC{now()}. Unidad {IDENT},foro049,decisiones OP-01 aOP-05 e informe {rel(DOC)}. Se concilió el preflight C0 ya terminado sin repetir384 controles:5ámbitos exteriores coherentes con su uso original,20reutilizaciones internas incompatibles. Selector de metadatos no acredita invariancia del aprendizaje numérico; adaptador2023/objetos internos/prueba completa siguen ausentes. Inventario de llamadas previsto disponible, no ejecutado; G1plausible,G2fallida,G4parcial. B00 y alternativas/contador195/285sin cambios, cero nuevos ajustes,C0,inferencias,scores o diagnósticos numéricos.

Esta continuación tenía texto obsoleto sobre B12/B13 e incidenciaHOST. Se actualizó solo su prompt mediante automation_update y se verificaron TOML antes/después: identidad,nombre,estado,creación,frecuencia,cierre07:00Bogotá y destino preservados; ningún campo anterior cambió salvo prompt/updated_at. No otras automatizaciones. Próximos cortes evitan unidades/recibos/diagnósticos redundantes con fuentes iguales y mantienen monitor útil/balance final. Kaggle752144releído sin cambio semántico,solo recibo; sin nueva fuente,cotejo test/envío o aviso dedicado.

2024/test/SEL01/actas/ledgercerrados aquí,exposición previa de asunto externo declarada sin usar métricas o afirmar ceguera completa. Revisión propia exploratoria, no profesional independiente o aprobación humana. Fuentes/versiones fallidas/concurrencia preservadas; ventana intacta.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+f"\n\n## Corte operativo0400 y texto de continuidad actualizado\n\nCodex,{now()}. [Corte operativo](CORTE_NOCTURNO_20261024_0400.md),foro049. Se concilia preflight C0 sin repetirlo: uso exterior original válido en su alcance,20reutilizaciones internas incompatibles; invariancia numérica completa ausente. G1/G2no resueltas. Solo prompt de esta continuación actualizado, con mismo chat/frecuencia/cierre07:00Bogotá y estado. Ningún ajuste,score,C0 o suite nuevo. Ante fuentes iguales no fabricar ciclos documentales: monitor y balance final. B00/alternativas conservados,2024cerrado,otras automatizaciones sin cambios propios.\n")
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_night_operational_checkpoint_index',rel(INDEX)),'week_2_night_operational_checkpoint_report',rel(DOC)))
    before=read(RUN/'registration_cuts/before'/NIGHT.relative_to(ROOT));after=read(RUN/'registration_cuts/after'/NIGHT.relative_to(ROOT))
    checks={'source_snapshots_exact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'source_indices_untouched':all(sha(ROOT/x['path'])==x['sha256'] for x in sources),'previous_completions_preserved':after['completed_units'][:-1]==before['completed_units'],'current_unit_preserved':after.get('current_unit')==before.get('current_unit'),'own2024closed':after['confirmation_2024_open'] is False,'night_schedule_unchanged':after['window_end']==before['window_end'] and after['automation_target_thread']==before['automation_target_thread'],'automation_update_exact':auto['prompt_exact'] and auto['all_other_fields_preserved']}
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/('Preparaci'+chr(243)+'n')/name;checks[name+'_prefix_preserved']=(RUN/'registration_cuts/after'/p.relative_to(ROOT)).read_bytes().startswith((RUN/'registration_cuts/before'/p.relative_to(ROOT)).read_bytes())
    dump(RUN/'integrity_receipt.json',{'id':IDENT,'utc':now(),'checks':checks,'passed':all(checks.values()),'scope':'Configuration/document integration only; no old scientific suite repeated.'});assert all(checks.values())
    dump(RUN/'registration.json',{'changes':changes,'active_catalog_mutations':0,'counter_mutations':0,'new_fits':0,'new_numerical_diagnostics':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':fid,'integrity_ok':all(checks.values()),'automation_updated':True,'schedule_preserved':True,'new_fits':0,'new_numerical_diagnostics':0},ensure_ascii=True))

if __name__=='__main__':main()
