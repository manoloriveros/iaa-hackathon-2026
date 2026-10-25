"""Balance de recibos existentes y cierre administrativo; no ejecuta experimentos."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/balance_nocturno_20261024_cierre_v1'
DOC=REPO/'docs/semana2/BALANCE_NOCTURNO_20261024.md'
INDEX=REPO/'registro/semana2_balance_nocturno_final_actual.json'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
IDENT='S2-BALANCE-NOCHE20261024-v1'
STATEKEY='week_2_night_final_balance20261024'
AUTOMATION='iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna'
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

def prepare():
    assert datetime.now(timezone.utc)>=datetime(2026,10,24,12,tzinfo=timezone.utc)
    RUN.mkdir(parents=True,exist_ok=False)
    t=DOC.read_text(encoding='utf-8')
    replacements={'ocurrencia2023':'ocurrencia 2023','ocurrencias2023':'ocurrencias 2023','pólizas2024':'pólizas 2024','de2023':'de 2023','de209':'de 209','los626':'los 626','los31':'los 31','a31':'a 31','cuatrofolds':'cuatro folds','quinceparejas':'quince parejas','banda1':'banda 1','banda5':'banda 5','fold0':'fold 0','fold1':'fold 1','fold2':'fold 2','fold3':'fold 3','fold4':'fold 4','23unidades':'23 unidades','23modelos':'23 modelos','23validaciones':'23 validaciones','195ajustes':'195 ajustes','285constantes':'285 constantes','60llamadas':'60 llamadas','31grupos':'31 grupos','Tweedie1,5':'Tweedie 1,5','exploratorio95%':'exploratorio 95%','el93,9%':'el 93,9%','el35,8%':'el 35,8%','el7,2%':'el 7,2%','supone91':'supone 91','es91':'es 91','626.639de':'626.639 de'}
    for a,b in replacements.items():t=t.replace(a,b)
    DOC.write_text(t,encoding='utf-8')
    names=['semana2_desarrollo2023_actual.json','semana2_contadores_propios_actual.json','semana2_b20_prioridades_actual.json','semana2_b20_mecanismo_soporte_revision_actual.json','semana2_b20_soporte_folds_actual.json','semana2_b20_preflight_c0_actual.json','semana2_b20_sintesis_actual.json','semana2_b20_incendio_AD_actual.json','semana2_b20_contraccion_actual.json','semana2_incidencia_kaggle_752144.json']
    paths=[NIGHT]+[REPO/'registro'/x for x in names]
    for f in ['DESARROLLO_2023_MODELOS_ESTANDAR.md','CAPITAL_CLIMA_CREDIBILIDAD_2023.md','CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md','SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md','PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md','SOPORTE_B20_POR_FOLD_2023.md']:
        paths.append(REPO/'docs/semana2'/f)
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'mutable_shared_index':p==NIGHT})
    n=read(NIGHT);d=read(REPO/'registro'/names[0]);c=read(REPO/'registro'/names[1]);receipts=[]
    for unit in n['completed_units']:
        ref=unit.get('verification');item={'id':unit['id'],'run':unit.get('run'),'documentation':unit.get('documentation'),'forum_result':unit.get('forum_result')}
        if ref:
            p=ROOT/ref['path'];assert p.is_relative_to(REPO/'privado/semana2/desarrollo2023')
            exists=p.exists();item.update(receipt=ref['path'],exists=exists,expected_sha256=ref.get('sha256'))
            if exists:
                v=read(p);item.update(actual_sha256=sha(p),sha256_matches=sha(p)==ref.get('sha256'),recorded_passed=v.get('passed'),recorded_failed=v.get('failed'))
        else:item['receipt_note']='No verification pointer in night entry; documentary unit not reclassified as numerical verification.'
        receipts.append(item)
    config=Path('C:/Users/manol/.codex/automations')/AUTOMATION/'automation.toml'
    if config.exists():
        with (RUN/'automation_before_closure.toml').open('xb') as f:f.write(config.read_bytes())
    dump(RUN/'sources.json',{'author':'Codex','utc':now(),'sources':sources})
    dump(RUN/'existing_receipt_inventory.json',{'author':'Codex','utc':now(),'receipt_only_no_suite_execution':True,'units':receipts,'unresolved_receipt_discrepancies':[x for x in receipts if x.get('exists') is False or x.get('sha256_matches') is False]})
    meta={'id':IDENT,'author':'Codex','prepared_utc':now(),'prepared_bogota':datetime.now(timezone(timedelta(hours=-5))).isoformat(),'first_clock_read_utc':'2026-10-24T12:27:30Z','authorized_window_end_utc':'2026-10-24T12:00:00Z','balance_prepared_after_deadline':True,'delivery_at0700_not_evidenced':True,'new_experiments_after_window':0,'night_entries_before_balance':len(n['completed_units']),'entries_are_mixed_historical_and_documentary_not_models':True,'registered_current_unit_at_cut':n.get('current_unit'),'development_id':d['id'],'saved2023_summary':d['summary'],'saved2023_pairs':d['pairs'],'cumulative_own_price_fits':c['cumulative_price_base_fits'],'cumulative_own_constants':c['cumulative_closed_form_constants'],'counters_are_not_night_or_balance_fit_counts':True,'last_existing_kaggle_check':n['latest_kaggle_752144_check'],'new_post_window_kaggle_poll':False,'reference':'W2-B00','all_alternatives_preserved':True,'models_preserved':d['models_consulted'],'promotion':False,'final_roster_frozen':False,'2024_test_closed':True,'new_fits':0,'new_inference':0,'new_C0_values':0,'new_scores':0,'new_bootstrap':0,'new_numerical_diagnostics':0,'new_recipes':0,'new_model_loads':0,'professional_independent_validation':False,'prior_external2024_subject_exposure_disclosed':True,'complete_blindness_claim_allowed':False,'mechanism':'plausible_not_established','heldout_support':'measured_failed_five_of_ten_cells_four_folds','inner_support':'unknown','whole_numeric_pipeline_isolation':'not_implemented_or_verified','sources':sources}
    dump(RUN/'balance.json',meta)
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'BAL-01','decision':'Entregar balance retrospectivo con hora real posterior al límite; no atribuir publicación a07:00 o seguimiento posterior al último recibo.'},
      {'id':'BAL-02','decision':'Reutilizar resultados/recibos2023; cero nuevos diagnósticos, entrenamiento o consultas externas tras el límite.'},
      {'id':'BAL-03','decision':'Mantener mecanismo abierto y soporte incumplido para el contraste; metadatos no prueban invariancia del flujo numérico.'},
      {'id':'BAL-04','decision':'Para retomar: evidencia legítima nueva o corrección real, necesidad/soporte, aislamiento y receta previa; no alterar casos o reglas para pasar.'},
      {'id':'BAL-05','decision':'Conservar B00/B01-B20 y2024cerrado; no promoción, retiro o roster por puntos2023.'},
      {'id':'BAL-06','decision':'Cerrar solo la automatización nocturna agotada por herramienta nativa; preservar otras conversaciones/automatizaciones.'},
      {'id':'BAL-07','decision':'Preservar adversos, autores y límites de revisión propia; el saldo documental no es validación profesional independiente.'}]})
    print(json.dumps({'stage':'prepared','run':rel(RUN),'report':rel(DOC),'historical_entries':len(receipts),'receipt_discrepancies':sum(x.get('exists') is False or x.get('sha256_matches') is False for x in receipts),'new_fits':0,'new_diagnostics':0},ensure_ascii=True))

def register():
    meta=read(RUN/'balance.json');closure=read(RUN/'automation_closure_receipt.json');assert closure['confirmed_deleted'] and closure['automation_id']==AUTOMATION
    tail=f"\n\n## Cierre operativo de esta ventana\n\nCodex, registro UTC {now()}. La herramienta nativa confirmó la eliminación de la automatización nocturna {AUTOMATION}, ya terminada su ventana. Solo se cerró esa continuación; no se modificaron otras automatizaciones o chats. El recibo conserva la respuesta de la herramienta y la existencia de configuración después del cierre. No se programó una prórroga. Este cierre administrativo y publicación se registran después de las07:00, sin nuevas pruebas.\n"
    with DOC.open('a',encoding='utf-8') as f:f.write(tail)
    fid='COD-S2-20261024-050';fp=RUN/'forum_050.md'
    fp.write_text(f'''Codex, balance solicitado por el participante. Informe:{rel(DOC)}; fuentes/recibos/decisiones:{rel(RUN)}. BAL-01 aBAL-07. Ventana prevista23oct19:00–24oct07:00Bogotá. Primera lectura actual07:27:30Bogotá; este balance se publica después del límite, no a07:00. Solo lectura de recibos guardados, sin nuevas pruebas, modelos, inferencias, C0, scores, bootstrap o consultas externas. Última consulta propia Kaggle guardada09:58:39UTC, sin inventar cobertura posterior.

Comprobado: referencias estándar B12/B13, capital/credibilidad/clima y sensibilidad de cola/reservas/mezcla con límites documentados; B19 adverso, traza seleccionada conciliada; B20ridge, atribución, contracción, bandas, incendio/AD, soporte y preflightC0 guardados. Los {meta['night_entries_before_balance']} registros de continuidad incluyen ensayos preparatorios y documentación, no ese número de modelos o validaciones independientes. Contador195ajustes/285constantes es acumulado propio, no trabajo nuevo de esta noche/balance. No se suman controles solapados.

B20 sigue como alternativa: mecanismo plausible/no establecido;5/10celdas de soporte fallan por concentración en4folds aunque cumplen positivos; interno desconocido. CincoC0exteriores coherentes en su ámbito,20reutilizaciones internas incompatibles. Selector de metadatos no demuestra aislamiento del flujo numérico completo; adaptador2023, objetos internos y perturbación de etiquetas protegidas siguen pendientes. Ventaja OOF frente aB14 incierta y se invierte bajo los31grupos favorables. No retirar datos o rebajar reglas para pasar.

Para retomar hacen falta evidencia2023 nueva legítima o corrección material real documentada y sustento del mecanismo/soporte. Después, única modificación estándar justificada, flujo sin fuga y receta/comparador/criterio/coste/parada congelados con comentario previo antes de cualquier ajuste o score dentro de la instrucción humana aplicable. Último, promoción y revisión competente no se inventan como resueltos por esta investigación.

La herramienta confirmó eliminada solo esta automatización nocturna al agotarse la ventana; sin prórroga u otros cambios de programación. B00/B01-B20/T0/C0/folds/versiones fallidas conservados, sin promoción/retirada/roster.2024/test/SEL01/actas/ledgercerrados aquí. Exposición previa de asunto externo declarada sin usar métricas o afirmar ceguera completa. AnuncioHOST de arreglo archivado; causa interna y recepción/scoring propios no verificados, sin envío. Revisión propia exploratoria, sin aprobación humana o validación profesional independiente.''',encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','Balance nocturno: B20 pendiente, evidencia necesaria y cierre de esta ventana','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;receipt=json.loads(proc.stdout);dump(RUN/'forum_receipt.json',receipt)
    idx={**{k:v for k,v in meta.items() if k not in ['saved2023_summary','saved2023_pairs']},'path_base':'workspace_root','status':'window_closed_balance_published_after_deadline_no_new_experiments','administrative_closure_recorded_utc':now(),'forum_result':fid,'forum_publication_utc':receipt['utc'],'documentation':rel(DOC),'documentation_sha256':sha(DOC),'run':rel(RUN),'automation_status':'DELETED','automation_id':AUTOMATION,'other_automations_changed_by_this_unit':False,'balance_data':{'path':rel(RUN/'balance.json'),'sha256':sha(RUN/'balance.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')},'automation_closure_receipt':{'path':rel(RUN/'automation_closure_receipt.json'),'sha256':sha(RUN/'automation_closure_receipt.json')}}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.balanceNocheFinal.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
        with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(changes[-1])+'\n')
    def night(raw):
        n=json.loads(raw);vals={'status':'window_closed_balance_published_after_deadline','final_balance':{'id':IDENT,'index':rel(INDEX),'documentation':rel(DOC),'forum_result':fid,'published_utc':receipt['utc'],'published_after_window':True},'authorized_window_ended_utc':'2026-10-24T12:00:00Z','administrative_closure_recorded_utc':now(),'automation_status_verified':'DELETED','automation_closure_receipt':idx['automation_closure_receipt'],'other_automations_changed':False,'next_unit_before_final_balance':n.get('next_unit'),'next_unit':'This overnight window has ended. No automatic continuation or new experiments. B20 contrast remains non executable; evidence and resumption requirements are in final balance. Preserve B00/all alternatives and own2024/test closed.','queue_before_final_balance':n.get('queue'),'queue':[],'updated_utc':now()}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(NIGHT,night)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## Balance nocturno final y cierre administrativo del24deoctubre

Codex, UTC {now()}, foro050, decisiones BAL-01 aBAL-07. Informe {rel(DOC)} e índice {rel(INDEX)}. Ventana terminada24oct07:00Bogotá/12:00UTC; primera lectura de este encargo07:27:30Bogotá, balance publicado después del límite con hora real en recibo. No constó entrega a07:00 ni se inventa; no se iniciaron nuevas pruebas o consultas externas tras la ventana. Los {meta['night_entries_before_balance']} registros previos mezclan preparaciones/ensayos/diagnósticos/documentación, no equivalen a ese número de modelos. Contador195/285acumulado propio, sin incremento en este balance.

B20: G1plausible/no establecido; G2retenido medido/fallido5/10celdas en4folds,interno desconocido; G4metadatos/exterior conciliados,20reutilizaciones internas incompatibles,flujo numérico completo no implementado/verificado. Para retomar: información2023 adicional legítima o corrección real documentada, mecanismo/soporte admisibles, necesidad estándar mínima, ámbito/ancestros/C0internos y presupuesto real, receta/criterio/comentario previos. No alterar casos o límites para pasar. Último/promoción/revisión competente siguen condicionados o no evaluados aquí.

Solo esta automatización nocturna fue eliminada mediante herramienta nativa, con recibo privado; no prórroga, otros chats/automatizaciones conservados. B00/B01-B20,T0/C0/folds y adversos conservados;2024/test/SEL01/actas/ledgercerrados aquí. Exposición previa de asunto externo declarada sin usar métricas o afirmar ceguera completa. Último seguimiento propio Kaggle guardado09:58:39UTC, sin consulta nueva o envío para este balance; anuncioHOST no acredita scoring propio. Revisión propia exploratoria, sin aprobación humana o validación profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+f"\n\n## Ventana concluida: balance final publicado\n\nCodex, UTC {now()}. [Balance final](BALANCE_NOCTURNO_20261024.md), foro050. Preparado/publicado después del límite07:00Bogotá, con primera lectura07:27:30y hora real conservada. No nuevas pruebas o entrenamiento. Esta automatización nocturna fue eliminada por herramienta nativa; sin prórroga u otras automatizaciones modificadas. G1/G2/G4pendientes, B00/alternativas conservados,2024cerrado. El balance delimita evidencia para retomar sin dar por resuelta promoción o último.\n")
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_night_final_balance_index',rel(INDEX)),'week_2_night_final_balance_report',rel(DOC)))
    before=read(RUN/'registration_cuts/before'/NIGHT.relative_to(ROOT));after=read(RUN/'registration_cuts/after'/NIGHT.relative_to(ROOT))
    observation={'id':IDENT,'utc':now(),'scope':'Administrative/documentary preservation only; no scientific suite or numerical diagnostic executed.','completed_history_preserved':before['completed_units']==after['completed_units'],'current_unit_preserved':before.get('current_unit')==after.get('current_unit'),'window_end_preserved':before['window_end']==after['window_end'],'own2024closed':after['confirmation_2024_open'] is False,'own_automation_deleted':closure['confirmed_deleted'],'frozen_source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in meta['sources']),'source_indices_changed_after_cut_excluding_own_night':[x['path'] for x in meta['sources'] if not x['mutable_shared_index'] and sha(ROOT/x['path'])!=x['sha256']]}
    dump(RUN/'administrative_integrity_receipt.json',observation)
    dump(RUN/'registration.json',{'changes':changes,'active_catalog_mutations':0,'counter_mutations':0,'new_experiments':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'stage':'registered','report':rel(DOC),'forum_result':fid,'published_utc':receipt['utc'],'after_deadline':True,'own_automation_deleted':True,'new_experiments':0,'source_indices_changed_after_cut':observation['source_indices_changed_after_cut_excluding_own_night']},ensure_ascii=True))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='register':register()
    else:raise ValueError('prepare or register required')
