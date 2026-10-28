"""Última auditoría de archivo y admisión; no entrena ni vuelve a buscar modelos.

Reutiliza controles previos solamente si sus fuentes y código siguen iguales.
El sello del CSV y una recomendación predictiva definitiva son decisiones distintas.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import argparse,csv,hashlib,importlib.util,json,math,os,subprocess,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
f=module('final_F3c_provenance',R/'herramientas/validar_F3c_completo.py');w=f.w
OLD=f.OUT;OUT=R/'privado/semana2/cierre_F3c_20261028'
PLAN=R/'registro/semana2_cierre_F3c_plan.json';INDEX=R/'registro/semana2_cierre_F3c_actual.json';DOC=R/'docs/semana2/F3C_REVISION_FINAL_20261028.md'
OFFICIAL=ROOT/'Hackaton/Semana 2/Datos/emerging'
REPRO=f.LEGACY/'ml/datos/emerging'
EXPECTED='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
read=f.read;sha=f.sha;dump=f.dump
def utc():return datetime.now(timezone.utc).isoformat()

def post(body,identifier,subject):
    path=OUT/(identifier+'.md');path.write_text(body,encoding='utf8')
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(path)],capture_output=True,text=True,encoding='utf8',check=True)
    return json.loads(result.stdout)

def decision(technical,predictive):
    # Fail closed: parsing/reproduction never turns failed predictive gates green.
    return {'reference_file_can_be_sealed':bool(technical),'definitive_private_robustness_supported':bool(technical and predictive),'formal_promotion':False,'new_submission_allowed_by_this_audit':False}

def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists();OUT.mkdir()
    current=R/'registro/semana2_F3c_completo_validacion_actual.json';snapshot=OUT/'inherited_index_snapshot.json';snapshot.write_bytes(current.read_bytes())
    inherited=read(snapshot);assert inherited['execution'] is None
    paths=[Path(__file__),snapshot,f.ORIGINAL,f.LEGACY/'m017/exp26/F3c_2025.csv',f.LEGACY/'m017/exp26/F3c_info.json',f.LEGACY/'chain_receipts/m017_F3c.json',f.LEGACY.parent/'comparacion_final.json',f.PLAN,
        R/'herramientas/evaluar_F3c_completo.py',R/'herramientas/verificar_F3c_completo.py',Path(f.__file__),f.HISTORY_ADMISSION,f.EXECUTION_RECONCILIATION,
        ROOT/'Hackaton/Semana 2/CONTRATO_SEMANA2.md']
    paths += [OLD/name for name in ['results.json','verification.json','target_controls.json','closed.json','final_integrity_receipt.json','bootstrap.npz','fixed_price_stresses.json','parameters.json','target_started.json','original_history_preflight.json','feature_value_parity_corrected_metadata.json','methodological_clarifications.json']]
    paths += [p for p in OFFICIAL.glob('*.parquet')]
    paths += [REPRO/p.name for p in OFFICIAL.glob('*.parquet') if (REPRO/p.name).exists()]
    plan={'author':'Codex','utc':utc(),'request':'Last complete validation before definitive closure; private robustness remains primary.',
        'candidate':'Existing F3c2025 exact bytes; no changes to predictions or model parameters.',
        'criteria':{'CSV':'209063 unique IDs, exact official template and test-union order, precisely row_id/prediction, finite strictly positive values, standard-library and pandas parser agreement.',
            'lineage':'Unchanged candidate/retrained file SHA, full-source and scalar verification code/receipts pinned, same current inputs and model objects; inherit rather than rerun native fits or old suites.',
            'arithmetic':'Decimal sums vs reproduction metadata within theoretical six-decimal CSV rounding plus cents rounding; all six line/business cells.',
            'predictive':'Reconcile all stored CI bands and registered gates from cached10000draws, all50stress receipts and cells; no resampling, no new scores, no threshold change.',
            'closure':'File may be sealed as preserved incumbent if technical checks pass. Definitive private robustness cannot be asserted while the registered predictive admission is false and temporal/support limitations remain. Incremental gate failure does not prove the incumbent is worse than an untested alternative.',
            'controls':'Synthetic corrupt CSV headers/IDs/order/NaN/infinity/nonpositive and false-approval mutation must be rejected. Wrong file must not inherit candidate receipt.'},
        'scope':{'native_fits':0,'C0_fits':0,'calibration_fits':0,'new_model_inferences':0,'new_resampling':0,'new_predictive_scores':0,'new_submissions':0,'manual_Kaggle_selection':False,'external_publication':False,'delegation':False},
        'preserve':'F3c,R1,B00, all alternatives and failed receipts.2024alreadyadaptive; no full-blinding or professional-independent-validation claim.',
        'sources':{w.rel(p):sha(p) for p in paths}}
    dump(PLAN,plan)
    forum=post('Codex. Registro la ultima auditoria antes del cierre: cotejo del CSV F3c2025 y todos sus IDs con originales oficiales, datos activos frente a la copia de reproduccion, aritmetica por celda, integridad y version del codigo/evidencia, y correspondencia de los criterios predictivos con sus intervalos guardados. Reutilizo controles solo si fuentes/codigo coinciden. No reentrenar, recalcularC0,nuevas inferencias, nuevos scores, remuestreo, otro envio o seleccion manual. El sello del archivo no prueba robustez privada; no se cambian fallos a aprobaciones por pedir cierre. Registro salidas adversas y decision separada de integridad/admision; conserva F3c,R1,B00. Plan '+w.rel(PLAN)+' SHA '+sha(PLAN),'COD-S2-20261028-F3C-CIERRE-FINAL-PREVIO','F3c: ultima auditoria de archivo, linaje y admision antes del cierre')
    dump(OUT/'registration.json',{'utc':utc(),'plan_sha256':sha(PLAN),'forum':forum});dump(INDEX,{'author':'Codex','utc':utc(),'status':'final_audit_registered','plan':w.rel(PLAN),'plan_sha256':sha(PLAN),'output':w.rel(OUT),'execution':None,'forum':forum,'new_submissions':0})
    print(json.dumps({'registered':True,'plan_sha256':sha(PLAN),'new_fits':0}),flush=True)

def guard():
    assert sha(PLAN)==read(OUT/'registration.json')['plan_sha256']
    for path,digest in read(PLAN)['sources'].items():assert sha(ROOT/path)==digest,path

def parse_csv(path,expected_ids):
    ids=[];prices=[];exact=[]
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.reader(stream);assert next(reader)==['row_id','prediction'],'CSV columns'
        for row in reader:
            assert len(row)==2,'CSV width';key,value=row;dec=Decimal(value)
            assert key and key==key.strip(),'Malformed ID'
            assert dec.is_finite() and dec>0,'Nonpositive or nonfinite price'
            price=float(dec);assert math.isfinite(price) and price>0,'Floating-point overflow'
            ids.append(key);prices.append(price);exact.append(dec)
    assert ids==list(expected_ids),'Wrong IDs or order';assert len(set(ids))==len(ids),'Duplicate IDs'
    return ids,np.asarray(prices),exact

def controls():
    folder=OUT/'synthetic';folder.mkdir();checks={};good='row_id,prediction\na,1.250000\nb,2.500000\n'
    for label,content in {'wrong_header':good.replace('prediction','premium'),'wrong_ID':good.replace('a,','x,'),'wrong_order':'row_id,prediction\nb,2.5\na,1.25\n','duplicate':'row_id,prediction\na,1.25\na,2.5\n',
                          'nan':good.replace('1.250000','NaN'),'infinity':good.replace('1.250000','Infinity'),'zero':good.replace('1.250000','0'),'negative':good.replace('1.250000','-1')}.items():
        p=folder/(label+'.csv');p.write_text(content,encoding='utf8')
        try:parse_csv(p,['a','b'])
        except (AssertionError,ValueError,ArithmeticError):checks['reject_'+label]=True
        else:checks['reject_'+label]=False
    p=folder/'valid.csv';p.write_text(good,encoding='utf8');ids,prices,_=parse_csv(p,['a','b']);checks['valid_fixture']=ids==['a','b'] and np.array_equal(prices,[1.25,2.5])
    checks['technical_pass_cannot_approve_predictive_failure']=not decision(True,False)['definitive_private_robustness_supported']
    checks['failed_technical_cannot_seal']=not decision(False,True)['reference_file_can_be_sealed']
    checks['no_automatic_upload_even_both_pass']=not decision(True,True)['new_submission_allowed_by_this_audit']
    checks['wrong_hash_cannot_inherit_receipt']=sha(p)!=EXPECTED
    assert all(checks.values());return checks

def audit():
    guard();assert not (OUT/'audit.json').exists();preflight=controls();checks={};inherited=read(OUT/'inherited_index_snapshot.json')
    for field,hashfield in [('report','report_sha256'),('results','results_sha256'),('verification','verification_sha256')]:assert sha(ROOT/inherited[field])==inherited[hashfield]
    f.guard();checks['prior_all_inputs_and_source_code_unchanged']=True
    verification=read(OLD/'verification.json');assert verification['checks']['all_passed']
    assert sha(R/'herramientas/verificar_F3c_completo.py')==verification['verifier_code_sha256']
    assert sha(R/'herramientas/evaluar_F3c_completo.py')==read(OLD/'target_started.json')['evaluator_sha256']
    assert read(OLD/'target_controls.json')['checks']['all_passed'];checks['prior_controls_inherited_with_current_hashes']=True
    for line in f.LINES:
        assert read(f.source_marker(line))['source2024_poison_replay_exact']
        for family in ['N0','F1']:
            for seed in f.SEEDS:
                for tag in ['baseline','poison2024']:
                    rec=read(f.source_folder(line,tag,family,seed)/'complete.json')
                    assert sha(ROOT/rec['model'])==rec['model_sha256'] and sha(ROOT/rec['raw'])==rec['raw_sha256']
    checks['36_source_model_and_raw_objects_unchanged']=True
    official_compare=[]
    for p in OFFICIAL.glob('*.parquet'):
        copy=REPRO/p.name
        if copy.exists():official_compare.append({'name':p.name,'same_bytes':sha(p)==sha(copy)})
    assert official_compare and all(x['same_bytes'] for x in official_compare);checks['official_data_match_reproduced_inputs']=True
    expected=pd.read_parquet(OFFICIAL/'sample_submission.parquet',columns=['row_id']).row_id.astype(str).tolist();assert len(expected)==209063 and len(set(expected))==209063
    meta=[]
    for line in f.LINES:
        t=pd.read_parquet(OFFICIAL/f'test_{line}.parquet',columns=['row_id','new_business']);assert t.new_business.notna().all() and t.new_business.isin([0,1,False,True]).all()
        t['cell']=line+'_'+t.new_business.astype(int).astype(str);meta.append(t[['row_id','cell']])
    test=pd.concat(meta,ignore_index=True);assert test.row_id.astype(str).tolist()==expected and test.row_id.is_unique;checks['exact_official_template_and_three_test_order']=True
    ids,prices,exact=parse_csv(f.ORIGINAL,expected);pandas=pd.read_csv(f.ORIGINAL,dtype={'row_id':str},float_precision='round_trip')
    assert pandas.row_id.tolist()==ids and np.array_equal(pandas.prediction.to_numpy(),prices);checks['two_independent_CSV_parsers_agree']=True
    assert sha(f.ORIGINAL)==sha(f.LEGACY/'m017/exp26/F3c_2025.csv')==EXPECTED;checks['original_and_retrained_CSV_exact']=True
    info=read(f.LEGACY/'m017/exp26/F3c_info.json');assert info['sha256']==EXPECTED;totals={}
    cells=test.cell.to_numpy()
    for cell in sorted(set(cells)):
        ix=np.flatnonzero(cells==cell);total=sum((exact[i] for i in ix),Decimal(0));limit=Decimal(len(ix))*Decimal('.0000005')+Decimal('.005')
        discrepancy=abs(total-Decimal(str(info['total_celda'][cell])));assert discrepancy<=limit
        totals[cell]={'rows':len(ix),'sum_CSV':str(total),'reproduction_sum':info['total_celda'][cell],'rounding_bound':str(limit),'absolute_difference':str(discrepancy)}
    total=sum(exact,Decimal(0));bound=Decimal(len(exact))*Decimal('.0000005')+Decimal('.005');assert abs(total-Decimal(str(info['total'])))<=bound
    checks['exact_decimal_totals_match_six_cells_with_rounding_bound']=True
    chain=read(f.LEGACY/'chain_receipts/m017_F3c.json');assert chain['exit_code']==0 and any(x['sha256']==EXPECTED for x in chain['outputs']);checks['successful_existing_full_retraining_receipt']=True
    result=read(OLD/'results.json');stress=read(OLD/'fixed_price_stresses.json');pack=np.load(OLD/'bootstrap.npz');names=pack['segments'].tolist();comps=pack['comparisons'].tolist();draws=pack['delta']
    assert draws.shape==(10000,len(names),3) and len(stress['scenarios'])==50;reconciled={}
    for si,name in enumerate(names):
        for j,comp in enumerate(comps):
            assert np.allclose(result['metrics'][name]['CI95'][comp],np.quantile(draws[:,si,j],[.025,.975]),rtol=0,atol=1e-15)
            assert np.allclose(result['metrics'][name]['family18'][comp],np.quantile(draws[:,si,j],[.05/36,1-.05/36]),rtol=0,atol=1e-15)
    for comp in comps:
        worst=min(z['deltas'][n][comp] for z in stress['scenarios'] for n in ['new_business','renewal']+f.LINES)
        assert math.isclose(worst,stress['worst_broad_delta'][comp],abs_tol=1e-15)
        m=result['metrics'];gates={'global_family18_lower_above_margin':m['global']['family18'][comp][0]>.0005,'NB_nonnegative_and_lower95_floor':m['new_business']['deltas'][comp]>=0 and m['new_business']['CI95'][comp][0]>=-.001,
            'broad_and_sixcell_floor':all(m[n]['deltas'][comp]>=-.001 for n in ['new_business','renewal']+f.LINES+[line+'_'+str(b) for line in f.LINES for b in [0,1]]),
            'four_savedfolds_positive':sum(m['saved_fold_'+str(k)]['deltas'][comp]>0 for k in range(5))>=4,'top_favorable_group_removal_nonnegative':result['influence'][comp]['delta_after_removal']>=0,'50_fixed_price_stress_broad_floor':worst>=-.001}
        assert gates==result['gates'][comp] and all(gates.values())==result['all_gates_pass'][comp];reconciled[comp]={'all_passed':all(gates.values()),'failed':[k for k,x in gates.items() if not x]}
    checks['all_cached_intervals_stresses_and_gates_reconcile']=True
    before=read(OLD/'final_integrity_receipt.json');assert before['new_submissions']==0 and before['predictive_all_gates_pass']==any(result['all_gates_pass'].values())
    technical=all(checks.values()) and all(preflight.values());predictive=any(result['all_gates_pass'].values());verdict=decision(technical,predictive)
    profile={'rows':len(prices),'min':float(prices.min()),'max':float(prices.max()),'median':float(np.median(prices)),'quantiles':{str(q):float(np.quantile(prices,q)) for q in [.01,.1,.9,.99,.999]},'total_CSV_exact':str(total),'cells':totals,'descriptive_only_no_target_truth':True}
    guard();output={'author':'Codex','utc':utc(),'candidate':w.rel(f.ORIGINAL),'candidate_sha256':EXPECTED,'checks':checks,'synthetic_negative_controls':preflight,'CSV_profile':profile,'official_input_copies':official_compare,'predictive_gates':reconciled,'decision':verdict,
        'interpretation':'Preserve incumbent. Failed incremental comparisons do not establish an absolute ranking of all candidates, and good file integrity does not establish private superiority. No new training, resampling,2024scores or2025inference.',
        'scope':read(PLAN)['scope'],'source_code_sha256':sha(Path(__file__))};dump(OUT/'audit.json',output)
    assert technical;print(json.dumps({'technical':technical,'rows':len(prices),'gate_passes':{k:v['all_passed'] for k,v in reconciled.items()},'decision':verdict}),flush=True)

def close():
    guard();a=read(OUT/'audit.json');assert a['decision']['reference_file_can_be_sealed'];assert not (OUT/'closed.json').exists()
    old=read(OLD/'results.json');m=old['metrics'];comp='public_full_vs_public_noown';lev='public_full_vs_trainlevel_full'
    text='# F3c: revisión final y sello del archivo conservado\n\nCodex, '+utc()+'. Se completó la última revisión local solicitada. El CSV conservado pasa integridad, contrato de entrega, trazabilidad y conciliación de controles. Las reservas predictivas siguen vigentes; esta revisión no acredita superioridad privada ni cambia la selección manual de Kaggle.\n\n'
    text+='## Archivo y reproducción\n\nSe cotejaron los 209.063 IDs únicos y su orden con la plantilla oficial y los tres test emergentes. Los dos lectores CSV coinciden; todos los precios son finitos y estrictamente positivos. Las copias de datos oficiales presentes en la reproducción siguen idénticas. Los totales por las seis celdas concuerdan con el recibo de reproducción dentro del límite matemático de redondeo.\n\n'
    text+='El CSV conserva SHA '+EXPECTED+'. Es idéntico al producido por el reentrenamiento integral ya realizado. Se verificaron sus objetos y recibos por hash, sin repetir entrenamiento o suites numéricas de fuentes iguales.\n\n'
    text+='## Evidencia de robustez y decisión\n\nLos intervalos guardados, los 50 escenarios y todos los criterios se conciliaron sin nuevos sorteos ni scores. Ninguna de las tres comparaciones incrementales pasa todos los criterios. Ese resultado impide presentar esta revisión como nueva evidencia de mejora privada, y tampoco demuestra que retirar F3c en favor de una alternativa no admitida sea mejor.\n\n'
    text+='| Pendiente | Evidencia local 2024, exploratoria |\n|---|---|\n'
    text+=f'| Negocio nuevo de autos | Bloque propio frente a omitirlo: ΔD² {m["motor_1"]["deltas"][comp]:+.6f}. |\n'
    text+=f'| Niveles de edificios nuevos | Bloques públicos frente a nivel aprendido en 2023: ΔD² {m["buildings_1"]["deltas"][lev]:+.6f}; diagnóstico puntual, sin confirmación independiente por celda. |\n'
    text+=f'| Concentración de la mejora | Tras retirar los 37 grupos más favorables, el bloque propio en estructura pública da ΔD² {old["influence"][comp]["delta_after_removal"]:+.6f}. |\n\n'
    text+='Se sella la identidad del archivo de referencia y se cierra esta auditoría. No se declara resuelta la robustez en negocio nuevo, reservas/valoración o disponibilidad temporal, ni se convierte un fallo en aprobación. F3c, R1, B00 y todas las versiones se conservan; no hay receta nueva, envío, publicación externa o selección manual. La decisión definitiva de generalización privada sigue sin respaldo suficiente.\n\n'
    text+='2024 ya es desarrollo adaptativo. Los bloques públicos conservan su condicionamiento histórico; el corte de valoración y los maestros sin versiones temporales impiden reconstruir una predicción prospectiva completa. Las bandas condicionan los modelos aprendidos y no cubren toda la búsqueda adaptativa o la incertidumbre de entrenamiento. Los controles propios de IA no constituyen validación profesional independiente ni aprobación humana.\n\n'
    text+='## Evidencia\n\n'
    for path in [PLAN,OUT/'audit.json',R/'docs/semana2/F3C_VALIDACION_COMPLETA_20261027.md',OLD/'verification.json',OLD/'results.json']:text+='- '+w.rel(path)+'; SHA '+sha(path)+'\n'
    DOC.write_text(text,encoding='utf8');forum=post(text,'COD-S2-20261028-F3C-CIERRE-FINAL-RESULTADO','F3c: ultima revision terminada, archivo sellado y reservas predictivas conservadas')
    receipt={'author':'Codex','utc':utc(),'status':'final_audit_complete_reference_file_sealed_with_predictive_reservations','execution':None,'plan':w.rel(PLAN),'plan_sha256':sha(PLAN),'report':w.rel(DOC),'report_sha256':sha(DOC),'audit':w.rel(OUT/'audit.json'),'audit_sha256':sha(OUT/'audit.json'),'candidate':w.rel(f.ORIGINAL),'candidate_sha256':EXPECTED,'decision':a['decision'],'forum':forum,'new_fits':0,'new_C0_fits':0,'new_submissions':0,'formal_promotion':False,'manual_Kaggle_selection':False,'private_superiority_established':False}
    archive=R/'privado/corte_F3c_final_audit_20261028';archive.mkdir(exist_ok=True);w.update(INDEX,receipt,archive)
    current=R/'registro/semana2_F3c_completo_validacion_actual.json';v=read(current);v.update(final_audit=receipt)
    w.update(current,{'final_audit':receipt},archive);phase=R/'registro/semana2_mision017_fase2_actual.json';w.update(phase,{'utc':utc(),'current_batch':v},archive)
    w.update(R/'registro/semana2_mision_privada_actual.json',{'utc':utc(),'last_final_F3c_audit':receipt},archive)
    w.update(ROOT/'Preparación/ESTADO_PROYECTO.json',{'week_2_mission017_phase2_20261025':v},archive)
    note='\n\n## Última auditoría de F3c, 28 de octubre de 2026\n\nCodex, '+utc()+'. CSV209063IDs y contrato oficial correctos, identidad y reproducción exactas, evidencia y criterios guardados conciliados sin nuevos ajustes, scores o remuestreo. Sello del archivo de referencia, con reservas predictivas: las tres comparaciones siguen sin admisión completa y la superioridad privada no está establecida. No se cambia el envío ni la selección manual. F3c/R1/B00 y alternativas intactos. Informe '+w.rel(DOC)+'. Foro '+forum['id']+'.\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_F3c_final_audit_index':w.rel(INDEX),'week_2_F3c_final_audit_report':w.rel(DOC)},archive)
    dump(OUT/'closed.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','audit','close']);args=parser.parse_args();globals()[args.mode]()
