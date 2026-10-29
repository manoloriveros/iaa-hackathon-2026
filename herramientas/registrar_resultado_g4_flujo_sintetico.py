"""Cierra el paquete local de evidencia G4; no ajusta ni aplica modelos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess,sys,zipfile,importlib.metadata as md
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'
DOC=REPO/'docs/archivo/semana2/G4_FLUJO_COMPLETO_SINTETICO_2023.md'
INDEX=REPO/'registro/semana2_g4_flujo_sintetico_actual.json'
PRIORITY=REPO/'registro/semana2_b20_prioridades_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
PLAN=REPO/'registro/semana2_g4_flujo_sintetico_plan_v2_reparacion.json'
IDENT='S2-G4-FLUJO-SINTETICO2023-FINAL-v1-20261024';FID='COD-S2-20261024-060'
STATEKEY='week_2_G4_full_synthetic_flow2023_v1_20261024'
G4STATUS='full_software_flow_synthetic_verified_real_2023_inputs_and_objects_pending'
now=lambda:datetime.now(timezone.utc).isoformat()
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,val):
    v=json.dumps(val,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+v+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+v+raw[m.end()+end:]

def main():
    assert not INDEX.exists()
    v=read(RUN/'verification.json');first=read(RUN/'attempt1_verification.json');debug=read(RUN/'attempt1_failure_investigation.json');replay=read(RUN/'disk_replay_receipt.json');plan=read(PLAN)
    assert v['success'] and v['attempt']==2 and v['tests']==9 and v['errors']==v['failures']==0
    assert v['details']['outer_poison_cases']==5 and v['details']['ordered_inner_poison_cases']==20
    assert all(v['details']['whole_object_serialization_equal']) and v['unexpected_data_or_network_attempts']==0
    assert replay['success'] and replay['synthetic_rows']==88 and not any(replay['fit_calls'].values())
    for item in plan['frozen_sources']:assert sha(ROOT/item['path'])==item['sha256']
    original_code_checks=[{'path':x['path'],'sha256':sha(ROOT/x['path'])} for x in plan['frozen_sources']]
    totals={key:first['synthetic_work'][key]+debug['synthetic_work'][key]+v['synthetic_work'][key] for key in v['synthetic_work']}
    assert totals['scope_attempts']<=180 and totals['GLM_fits']<=120 and totals['C0_fits']<=120 and totals['calibration_fits']<=80
    assert 6*totals['C0_fits']<=720
    dump(RUN/'cumulative_synthetic_work.json',{'author':'Codex','utc':now(),'attempts':[1,2],'focused_failure_investigation_scopes':2,'work':totals,'reporting_peril_calls':6*totals['C0_fits'],'joint_reference_solves':{'attempt1':2,'investigation':3,'attempt2':3},'all_competition_fit_counts':0,'within_repaired_budget':True})
    versions={k:md.version(k) for k in ['numpy','pandas','scipy','scikit-learn','joblib','threadpoolctl','pyarrow']}
    env={'python':sys.version,'platform':sys.platform,'packages':versions,'CPU_threads':2,'hosted_Kaggle_or_Linux_verified':False}
    dump(RUN/'environment.json',env)
    (RUN/'requirements_synthetic.txt').write_text('\n'.join(k+'=='+x for k,x in versions.items())+'\n',encoding='utf-8')
    current=read(PRIORITY);matrix=read(ROOT/current['matrix']['path'])
    for card in matrix['cards']:
        if card['gate']=='G4':
            card.update(status=G4STATUS,what_changed='Flujo completo preprocesado/C0/GLM/calibrador comprobado con fixtures,invariancia de objetos y replay sin fit; fallos/repación preservados.',
                required_evidence='Entradas y objetos interiores reales2023 con procedencia y ámbito admisible; pruebas del flujo con esas entradas solo cuando corresponda. No aportados por fixtures.',
                boundary='Verificación sintética de software,no validez actuarial o resolución de G1/G2. No se ejecuta ensayo del concurso bajo este encargo.')
    matrix.update(id=IDENT,utc=now(),author='Codex',source_previous_matrix=current['matrix'],verification_scope='Synthetic full software flow only')
    dump(RUN/'gate_matrix_updated_G4.json',matrix)
    decisions=[('G4F-01','Integrar y verificar flujo sintético completo con pertenencias aprendidas excluyendo exterior e interior; calibración aprende legítimamente datos internos.'),('G4F-02','Conservar intento1 fallido y sus fuentes; correcciones canónicas de fecha y devianza estable,sin cambiar modelos,fixture o tolerancias.'),('G4F-03','Reconocer pruebas finales9/9,invariancia5exteriores/20pares,replay disco sin fit y controles de aprendizaje/ámbitos; cero datos reales.'),('G4F-04','Actualizar G4 solo como software completo verificado sintéticamente; entradas/artefactos reales y validez estadística no cerrados.'),('G4F-05','Preparar paquete local con whitelist de fuentes,planes,entorno,fallos y fixture serializado; sin datos/estimadores del concurso o publicación.'),('G4F-06','B00/alternativas,T0/C0/folds/catálogo/contadores reales conservados;2024cerrado,sin promoción o nueva aprobación humana.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':x} for k,x in decisions]})
    files=[DOC,PLAN,REPO/'registro/semana2_g4_flujo_sintetico_plan_v1.json',REPO/'herramientas/replay_g4_sintetico_sin_ajuste.py']
    files += [ROOT/x['path'] for x in plan['frozen_sources']]
    files += [RUN/x for x in ['plan_snapshot.json','repair1_plan_snapshot.json','forum_059_pre.md','forum_prior_receipt.json','forum_repair1.md','forum_repair1_receipt.json','attempt1_verification.json','attempt1_test_output.txt','attempt1_failure_investigation.json','attempt2_verification.json','attempt2_test_output.txt','verification.json','disk_replay_receipt.json','synthetic_outer0.joblib','synthetic_outer0_manifest.json','cumulative_synthetic_work.json','environment.json','requirements_synthetic.txt','decision_journal.json']]
    for folder in ['preregistered_sources','repair1_frozen_sources','attempt1_sources','attempt2_sources']:files += list((RUN/folder).glob('*.py'))
    files=list(dict.fromkeys(files))
    packet_manifest={'id':IDENT,'utc':now(),'scope':'Local review evidence only; no contest data/models,submission,private forum corpus or shared state exports.','synthetic_model_marker':True,'files':[{'path':rel(p),'sha256':sha(p)} for p in files]}
    dump(RUN/'packet_content_manifest.json',packet_manifest)
    packet=RUN/'paquete_G4_sintetico_revision_local.zip'
    with zipfile.ZipFile(packet,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files+[RUN/'packet_content_manifest.json']:z.write(p,arcname=rel(p))
    with zipfile.ZipFile(packet) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256'] for x in packet_manifest['files'])
    fp=RUN/'forum_060_result.md'
    fp.write_text(f'''Codex, resultado del flujo G4 preinscrito en foro059 y reparación G4-FLOW-REPAIR1. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Paquete local: {rel(packet)} (SHA256 {sha(packet)}).

Segundo intento:9pruebas de integración pasaron,0fallos/errores. Flujo real del fixture:preprocesado,C0,GLM,calibradores L/S y aplicación. Objetos aprendidos y serializados idénticos ante cinco alteraciones exteriores y veinte pares exterior/interior; las consultas de aplicación permanecen fijas. Dos controles positivos demuestran aprendizaje desde coste/predictor permitidos. El calibrador aprende legítimamente las etiquetas internas del ajuste exterior, nunca las del exterior. Motor/contenidos sintéticos pasan exactamente sin cambio.

Predicción manual exp(Xbeta+intercepto) con discrepancia máxima0; devianza contrastada con API externa y equivalencia de pesos sqrt(C0). Perfil y optimización conjunta difieren como máximo5,96e-19en objetivo,con criterios previos intactos. Ocho adversos de ámbito/corrupción rechazados. Replay desde modelo sintético guardado:88filas,con todos los fit bloqueados y cero ajustes. Lectores y red bloqueados en ejecución:0intentos inesperados; una sonda deliberada sobre ruta falsa rechazada. Cero filas o estimadores del concurso.

Se conservan los tres fallos del intento1,sus fuentes y diagnóstico focal. La invariancia fallaba solo por formato fecha/Timestamp en la clave; se normaliza ISO/centavos de ajuste. La devianza cerca de cero sufría cancelación; se usa la identidad algebraica estable. Mismos modelos,fixture,semilla y tolerancias; reparación congelada antes de repetir la integración. No se repitieron suites históricas o diagnósticos reales.

Trabajo final:72GLM/72C0 sintéticos y29llamadas a calibración. Acumulado con fallos/investigación:107GLM/107C0,642reportes por peril,137llamadas de ámbito y47calibraciones,dentro del presupuesto de reparación. Se cuentan aparte,no aumentan precios reales ni crean candidatos. Manifiesto del paquete releído y SHA comprobados; solo fuentes/fixtures/planes/entorno/recibos propios,sin volcar foro o memoria común.

G4 avanza a software completo verificado con datos sintéticos. Faltan entradas/artefactos interiores reales2023 y procedencia; no se conecta el módulo sintético al concurso. G1/G2 no se resuelven con estos datos,ni se acredita último,rendimiento o uso actuarial. El paquete prepara revisión local,sin CSV de envío,publicación o acción remota. Verificado en Windows,no Kaggle alojado/Linux o reproducción profesional independiente.

G4F-01 a G4F-06,autor Codex. B00 y alternativas,T0/C0/exposición/folds/catálogo/contadores reales conservados.2024/test/ledger/actas/SEL01 cerrados. Sin datos reales entrenados,predichos o puntuados. Ventana nocturna cerrada,sin contactos externos,otros chats,delegación o automatizaciones. No promoción,retirada o aprobación humana inventada.
''',encoding='utf-8')
    out=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','G4: flujo completo sintético verificado, fallos conservados y paquete local preparado','--cuerpo',str(fp)],capture_output=True,text=True)
    assert out.returncode==0,out.stderr;dump(RUN/'forum_result_receipt.json',json.loads(out.stdout))
    result={'id':IDENT,'author':'Codex','utc':now(),'status':'full_software_flow_synthetic_verified_real_data_eligibility_not_established',
        'G4_software_status':G4STATUS,'G4_full_flow_synthetic_verified':True,'G4_real_full_flow_validated':False,'G4_real_gate_closed':False,
        'G1_G2_resolved_by_this_work':False,'scope':'Generated synthetic fixture only; preparation of local evidence packet, no external submission.',
        'reference':'W2-B00','all_alternatives_preserved':True,'competition_rows_read':0,'competition_C0_fits':0,'competition_pricing_fits':0,
        'competition_predictions':0,'competition_scores':0,'old_diagnostics_repeated':False,'final_tests':9,'final_failures':0,'final_errors':0,
        'outer_poison_cases':5,'ordered_inner_poison_cases':20,'failed_attempts_preserved':1,'synthetic_cumulative_work':totals,
        'reference_or_selection_changed':False,'2024_test_closed':True,'night_window_reopened':False,'submission':False,'remote_training':False,
        'professional_independent_validation':False,'path_base':'workspace_root','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),
        'forum_prior':'COD-S2-20261024-059','forum_repair':'COD-S2-20261024-G4-FLOW-REPAIR1','forum_result':FID,
        'verification':{'path':rel(RUN/'verification.json'),'sha256':sha(RUN/'verification.json')},
        'replay':{'path':rel(RUN/'disk_replay_receipt.json'),'sha256':sha(RUN/'disk_replay_receipt.json')},
        'packet':{'path':rel(packet),'sha256':sha(packet),'files':len(packet_manifest['files'])+1,'private_local_review_only':True},
        'matrix':{'path':rel(RUN/'gate_matrix_updated_G4.json'),'sha256':sha(RUN/'gate_matrix_updated_G4.json')},
        'decisions':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')}}
    dump(INDEX,result);changes=[]
    preserve_paths=[REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_continuidad_nocturna.json']+[ROOT/x['path'] for x in plan['frozen_sources']]
    preserved={rel(p):sha(p) for p in preserve_paths}
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.G4flow.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def priority_update(raw):
        d=json.loads(raw);g=d['current_gate_statuses'];g['G4']=G4STATUS
        blockers=[('G4: synthetic full software verified; real2023 inputs and nested artifacts pending' if str(x).startswith('G4:') else x) for x in d.get('current_blockers',[])]
        vals={'current_gate_statuses':g,'current_blockers':blockers,'G4_software_update_index':rel(INDEX),'G4_software_updated_utc':now(),'previous_G4_matrix':d['matrix'],'matrix':result['matrix']}
        for k,vv in vals.items():raw=top(raw,k,vv)
        return raw
    change(PRIORITY,priority_update)
    def source_update(raw):
        d=json.loads(raw);g=d.get('current_B20_gate_statuses',{});g['G4']=G4STATUS
        for k,vv in {'current_B20_gate_statuses':g,'G4_software_update_index':rel(INDEX),'G4_full_flow_synthetic_verified':True,'G4_real_full_flow_validated':False}.items():raw=top(raw,k,vv)
        return raw
    change(SOURCE,source_update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,result))
    section=f'''\n\n## G4: flujo completo verificado con fixtures sintéticos

Codex, UTC {now()}, preinscripción059,reparación G4-FLOW-REPAIR1,resultado060; decisiones G4F-01 a G4F-06. Informe {rel(DOC)}, índice {rel(INDEX)}, paquete local y recibos en {rel(RUN)}. Flujo integrado preprocesado/C0/GLM/calibración anidada/aplicación/replay,sin filas del concurso. Final9pruebas pasadas,0fallos/errores; cinco invariancias exteriores y veinte pares interiores incluyen estado completo y objetos serializados. Dos controles positivos,ocho adversos,referencia matemática externa y replay de disco88filas sin fit. Cero intentos inesperados de datos/red; sonda deliberada de ruta falsa bloqueada.

Intento1 con3fallos conservado con fuentes/log/investigación. Correcciones preinscritas:fechas ISO y centavos canónicos para hash tras promoción dtype protegida,devianza estable equivalente cerca de y=mu. Mismo fixture/semilla/modelos/criterios. Final72GLM/72C0 sintéticos; acumulados107cada uno,642reportes,137llamadas de ámbito,47calibradores más referencias identificadas,dentro de presupuesto de reparación. No contarlos como modelos reales o experimentos independientes. No se repitió suite C0 aislada/diagnósticos reales.

G4 actualizado solo a software completo verificado sintéticamente; entradas/procedencia/objetos interiores reales pendientes. No conecta automáticamente al concurso ni resuelve G1/G2 o prueba rendimiento/último. Paquete whitelist local con código,planes,entorno,fallos,recibos y artefacto sintético,CRC/SHA releídos; no foro/memoria común o datos/modelos reales. Windows comprobado,no Kaggle/Linux o reproducción independiente. Preparación para revisión local,sin envío externo. B00/alternativas,T0/C0/folds/catálogo/contadores reales conservados;2024/test/ledger/actas/SEL01 cerrados. Ventana nocturna cerrada,sin contactos,nuevos chats,delegación o automatizaciones; no promoción o aprobación humana inventada.\n'''
    section=re.sub(r',(?=\S)',', ',section)
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    def routes_update(raw):
        for k,vv in {'week_2_G4_full_synthetic_flow_index':rel(INDEX),'week_2_G4_full_synthetic_flow_report':rel(DOC),'week_2_G4_local_review_packet':rel(packet)}.items():raw=top(raw,k,vv)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes_update)
    integrity={'id':IDENT,'utc':now(),'frozen_numeric_sources_still_match':all(sha(ROOT/x['path'])==x['sha256'] for x in plan['frozen_sources']),
        'counter_catalog_night_and_code_unchanged_during_registration':all(sha(ROOT/p)==h for p,h in preserved.items()),
        'packet_readback_hashes_verified':True,'scope':'Integration/packaging checks only; no further model fit or diagnostics.',
        'preserved_hashes':preserved}
    assert integrity['frozen_numeric_sources_still_match'] and integrity['counter_catalog_night_and_code_unchanged_during_registration']
    dump(RUN/'closure_integrity_receipt.json',integrity)
    dump(RUN/'registration.json',{'changes':changes,'competition_data_writes':0,'price_catalog_mutations':0,'real_counter_mutations':0,'original_C0_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/replay_g4_sintetico_sin_ajuste.py']
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'final_tests':9,'synthetic_full_flow_verified':True,'real_G4_gate_closed':False,'packet':rel(packet),'packet_files':result['packet']['files'],'competition_fits':0,'integrity':True},ensure_ascii=True))

if __name__=='__main__':main()
