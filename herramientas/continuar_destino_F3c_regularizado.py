"""Continuación local acotada: espera fuentes, aprende destino y deja evaluación pendiente.

No envía, no genera2025 y no compara scores2024. Un proceso con lease, hashes y
salida ante fallos. Las fuentes nativas siguen siendo responsabilidad de su cola.
"""
from pathlib import Path
import argparse
import copy
import json
import os
import sys
import time
import traceback
from unittest.mock import patch
import psutil

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import preparar_destino_F3c_regularizado as p
import entradas_F3c_regularizado as inp
import calibrador_F3c_regularizado as model

BASE=R/'privado/semana2/F3c_regularizado_20261028'
OUT=BASE/'target_real';SOURCE=BASE/'source_scoped'
PLAN=R/'registro/semana2_F3c_regularizado_ejecucion_plan.json'
SYNTHETIC=p.OUT/'corrected_numeric_types/synthetic.json'


def write_status(state,**kw):
    path=OUT/'status.json';tmp=OUT/'status.tmp'
    value={'author':'Codex','utc':p.utc(),'pid':os.getpid(),'state':state,**kw}
    with tmp.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def scope_records(name):
    folder=SOURCE/name
    paths=[folder/line/f'{family}_{seed}/complete.json' for line in inp.LINES for family in ['N0','F1'] for seed in [11,12,13]]
    return paths,[p.read(cp) for cp in paths]


def validate_scope(name,admission,marker,records,expected_digest):
    assert marker['scope']==name and marker['model_pairs']==18 and marker['scores']==0
    expected_folds=[] if name=='all' else list(map(int,name.removeprefix('exclude_')))
    assert admission['scope']=={'scope':name,'excluded_folds':expected_folds}
    assert admission['target_ids_digest']==expected_digest
    assert admission['poison_before_actual_filter_exact'] is True
    assert len(records)==18 and all(rec['scope']==name for rec in records)
    assert all(all(k in rec for k in ['arguments_sha256','model','raw','model_sha256','raw_sha256']) for rec in records)


class StrictSource(inp.RealSource):
    def __init__(self,frame):
        super().__init__(SOURCE);self.all_ids=set(frame.row_id);self.manifests={};self.consumed={}

    def get(self,excluded,train):
        name=inp.scope_name(excluded);folder=SOURCE/name
        paths,records=scope_records(name)
        admission=p.read(folder/'curves_admission.json');marker=p.read(folder/'source_complete.json')
        validate_scope(name,admission,marker,records,p.io.digest(train.row_id.tolist()))
        manifest={str(cp):p.sha(cp) for cp in paths+[folder/'curves_admission.json',folder/'source_complete.json']}
        if name in self.manifests:assert self.manifests[name]==manifest,'Recibo fuente cambió durante destino'
        out=super().get(excluded,train)
        assert all(s.index.is_unique and set(s.index)==self.all_ids and np.isfinite(s).all() for s in out['raws'].values())
        for rec in records:
            for kind in ['raw','model']:
                key=rec[kind];path=ROOT/key;st=path.stat()
                if key not in self.consumed:self.consumed[key]={'sha256':rec[kind+'_sha256'],'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
        self.manifests[name]=manifest
        return out

    def verify_consumed(self):
        for manifest in self.manifests.values():
            for path,digest in manifest.items():assert p.sha(path)==digest,'Recibo fuente modificado'
        for path,item in self.consumed.items():
            st=(ROOT/path).stat()
            if st.st_size!=item['bytes'] or st.st_mtime_ns!=item['mtime_ns']:
                assert p.sha(ROOT/path)==item['sha256'],'Fuente modificada durante destino'


def register():
    p.guard();assert p.read(SYNTHETIC)['all_passed']
    assert not PLAN.exists() and not OUT.exists()
    OUT.mkdir()
    deps=[Path(__file__),Path(inp.__file__),Path(p.__file__),Path(model.__file__),p.PLAN,
        p.OUT/'numeric_types_amendment.json',SYNTHETIC,R/'registro/semana2_F3c_regularizado_fuente_plan.json',
        inp.f.PARENT/'baseline_parameters.json']
    deps += [inp.f.ACTIVE/'prepared'/f'emerging_{line}.parquet' for line in inp.LINES]
    deps += [inp.f.PARENT/'models/baseline'/f'{line}_raw.parquet' for line in inp.LINES]
    plan={'author':'Codex','utc':p.utc(),'candidate':'F3c-R','phase':'source_gated_target_production',
        'hypothesis':'Misma contracción preinscrita, sin cambiar variables ni parámetros después de resultados.',
        'configuration':p.read(p.PLAN)['configuration'],
        'comparators':p.read(p.PLAN)['comparators_clarified_before_new_fit_or_score'],
        'start_gate':'26ámbitos fuente completos; hashes y metadatos exactos; pruebas sintéticas aprobadas y preflight real de lectura aprobado.',
        'primary_budget':{'calibrator_fits':16,'base_analytical_levels':234,'C1_levels':48,'recipe_scopes':16,'native_source_fits':0,'RKM_fits':0},
        'verification_budget':{'held2024_calibrator_fits':16,'five_outer_fold_input_checks_no_calibrator_refit':5,
            'positive_training_calibrator_fit':1,'independent_optimizer_fit':1,'total_calibrator_calls':34,
            'target_analytical': 'Dosbundles completos, cinco ramas exteriores y un positivo. Contar llamadas reales en recibo separado; cota por receta del plan destino vigente.'},
        'new_orchestration_smoke_budget':{'synthetic_calibrator_fits':34,'real_source_fits':0,
            'reason':'Probar el nuevo ejecutor completo, sus estados, serialización, contadores y bloqueo de replay antes de conectarlo a datos reales.'},
        'payload':'Etiquetas2024 y de cadafold2023 protegido se reemplazan antes del selector por texto no convertible; igualdad exacta de toda rama, receta y calibrador cuando proceda.',
        'source_replay_limit':'Raw y modelos fuente se leen por hashes/ámbito. No vuelve a ajustar árboles con payload alterado; controles de curvas y argumentos fuente pertenecen a sus recibos previos.',
        'stop':'Cualquier error detiene la continuación y conserva parciales. Termina con predicciones2024 y controles sellados; evaluación temporal, sensibilidad y eventual envío quedan pendientes.',
        'scores2024':0,'new2025_predictions':0,'submissions':0,
        'dependencies':[{'path':p.io.rel(q),'sha256':p.sha(q)} for q in deps]}
    p.dump(PLAN,plan)
    body=('Codex. El flujo sintético corregido pasó sus controles. Registro la continuación local para aprender F3c-R únicamente cuando terminen los26ámbitos fuente y coincidan sus hashes. '
        'Serán16ajustes primarios de calibrador y18de verificación separados; ninguna nueva receta ni cambio de umbral. Comprueba las5ramas retenidas, altera2024 antes del selector, reproduce parámetros guardados y contrasta el optimizador por otro método. '
        'El ejecutor nuevo pasará primero su recorrido con fixture,34ajustes sintéticos separados para verificar estados/serialización/contadores. La lectura de fuentes conservadas no es un nuevo replay de entrenamiento nativo. La continuación termina antes de puntuar2024, producir2025 o enviar. '
        'Conservo F3c/R1/B00, adversos y el fallo sintético anterior. Plan: '+p.io.rel(PLAN)+'; SHA256 '+p.sha(PLAN)+'.')
    forum=p.io.post(body,'COD-S2-20261028-F3CR-DESTINO-REAL-PREVIO','F3c-R: continuación destino condicionada a26fuentes y controles')
    p.dump(OUT/'registration.json',{'utc':p.utc(),'plan_sha256':p.sha(PLAN),'forum':forum})
    write_status('REGISTERED_NOT_STARTED')
    print(json.dumps({'registered':True,'plan_sha256':p.sha(PLAN)}),flush=True)


def guard():
    p.guard();assert p.read(OUT/'registration.json')['plan_sha256']==p.sha(PLAN)
    amendment=p.read(OUT/'execution_reader_amendment.json') if (OUT/'execution_reader_amendment.json').exists() else {}
    for d in p.read(PLAN)['dependencies']:
        expected=amendment.get('corrected_dependencies',{}).get(d['path'],d['sha256'])
        assert p.sha(ROOT/d['path'])==expected,d['path']
    assert p.read(SYNTHETIC)['all_passed']


def admit_reader():
    assert not (OUT/'execution_reader_amendment.json').exists()
    corrected={d['path']:p.sha(ROOT/d['path']) for d in p.read(PLAN)['dependencies'] if p.sha(ROOT/d['path'])!=d['sha256']}
    assert set(corrected)=={p.io.rel(Path(__file__))}
    smokeout=OUT/'orchestration_smoke';calls=[json.loads(x) for x in (smokeout/'calibrator_attempts.jsonl').read_text().splitlines()]
    assert len(calls)==16 and all(x['role']=='primary' for x in calls) and (smokeout/'primary_parameters.json').exists()
    assert not psutil.pid_exists(25592)
    body=('Codex. La lectura real se detuvo antes de ajustar por un error de esquema: curves_admission.scope contiene un objeto con nombre y folds, no texto. Corrijo su lectura estricta sin relajar digest, hashes ni reglas. '
        'La ejecución local se interrumpió alrededor de19:45UTC; procesos fuente y fixture ausentes, evidencia y leases archivados. La fuente retoma sus checkpoints con el mismo código:4ámbitos completos y etapa inner guardada del siguiente; el intento full interrumpido queda contado. '
        'La prueba del ejecutor conserva16calibradores sintéticos primarios terminados y se reanuda desde sus parámetros/Parquet, sin repetirlos. No había ajuste adverso de calibrador iniciado. La contabilidad analítica de esa prueba interrumpida se declara parcial; no invento total. '
        'No hubo nuevo ajuste real destino, score2024,2025 ni envío. Esquema y recuperación registrados antes de reanudar.')
    forum=p.io.post(body,'COD-S2-20261028-F3CR-LECTOR-RECUPERACION','F3c-R: lectura de ámbito y recuperación de ejecución interrumpida')
    p.dump(OUT/'execution_reader_amendment.json',{'author':'Codex','utc':p.utc(),'corrected_dependencies':corrected,
        'preserved_synthetic_primary_fits':16,'remaining_synthetic_fits':18,'new_candidate_recipe':False,'forum':forum,
        'reconciliation':'Hackaton/Repositorio_IAA2026/privado/corte_f3cr_20261028_2022/reconciliation.json'})
    print(json.dumps({'reader_recovery_admitted':True}),flush=True)


def preflight():
    guard();assert not (OUT/'read_admission.json').exists()
    frame=inp.e.load_em();tr=inp.train_frame(frame,());provider=StrictSource(frame)
    src=provider.get((),tr)
    paths,records=scope_records('all');adm=p.read(SOURCE/'all/curves_admission.json');marker=p.read(SOURCE/'all/source_complete.json')
    checks={'all_source_keys_match_2023_2024':all(set(z.index)==set(frame.row_id) for z in src['raws'].values()),
        'selected2023_50094':len(tr)==50094,'held2024_59202':int(frame.year.eq(2024).sum())==59202}
    for label,where,key,value in [('scope','record','scope','exclude_0'),('count','marker','model_pairs',17),
                                  ('digest','admission','target_ids_digest','wrong')]:
        rr=copy.deepcopy(records);aa=copy.deepcopy(adm);mm=copy.deepcopy(marker)
        target=rr[0] if where=='record' else mm if where=='marker' else aa;target[key]=value
        try:validate_scope('all',aa,mm,rr,p.io.digest(tr.row_id.tolist()));checks['reject_'+label]=False
        except AssertionError:checks['reject_'+label]=True
    # Sin invocar productores, optimizadores o nuevos cálculos C0.
    result={'author':'Codex','utc':p.utc(),'checks':checks,'all_passed':all(checks.values()),
        'source_scope_checked':'all','model_and_raw_hashes_checked':18,'native_source_inferences':0,'fits':0,
        'source_manifest':provider.manifests,'code_sha256':p.sha(Path(__file__)),'plan_sha256':p.sha(PLAN)}
    p.dump(OUT/'read_admission.json',result);assert result['all_passed']
    print(json.dumps({'read_admission_passed':True,'checks':checks}),flush=True)


def run_target(resume_primary=False):
    guard();assert p.read(OUT/'read_admission.json')['all_passed']
    assert resume_primary or not (OUT/'primary_parameters.json').exists(),'Ya hay un resultado primario; conciliar, no repetir'
    frame=inp.e.load_em();provider=StrictSource(frame);adapter=inp.Adapter(frame,provider)
    original_fit=model.fit;calls=[];role='primary';analytic_start=sum(inp.e.COUNTS.values())
    if resume_primary:
        calls=[json.loads(x) for x in (OUT/'calibrator_attempts.jsonl').read_text().splitlines()]
        assert len(calls)==16 and all(x['role']=='primary' for x in calls)
    def counted_fit(*args,**kwargs):
        entry={'utc':p.utc(),'role':role,'call':len(calls)+1,'independent':kwargs.get('independent',False)}
        with (OUT/'calibrator_attempts.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\n');f.flush();os.fsync(f.fileno())
        calls.append(entry)
        return original_fit(*args,**kwargs)
    with patch.object(model,'fit',counted_fit):
        if resume_primary:
            saved=p.read(OUT/'primary_parameters.json');primary=saved['calibrator']
            adapter.base_parameters=saved['adapter']['base'];adapter.recipes=saved['adapter']['recipes'];adapter.counts=saved['counts']
            tr=pd.read_parquet(OUT/'calibration_training2023.parquet');va=pd.read_parquet(OUT/'predictions2024.parquet');mu=va.pop('F3c_R').to_numpy()
            assert np.array_equal(mu,p.forward(va,primary['final']))
            branches={fold:p.protected_branch(adapter,fold) for fold in range(5)}
            assert len(adapter.base_parameters)==26 and len(adapter.recipes)==16
            write_status('PRIMARY_RECOVERED_WITHOUT_REFIT',preserved_calibrator_calls=16)
        else:
            write_status('TARGET_PRIMARY_RUNNING')
            primary,tr,va,mu,branches=p.bundle(adapter)
            p.dump(OUT/'primary_parameters.json',{'adapter':p.state(adapter),'calibrator':primary,'counts':adapter.counts})
            tr.to_parquet(OUT/'calibration_training2023.parquet',index=False)
            va.assign(F3c_R=mu).to_parquet(OUT/'predictions2024.parquet',index=False)
            frame.loc[frame.year.eq(2024),['row_id','y']].to_parquet(OUT/'labels2024.parquet',index=False)
        role='held2024_poison';write_status('TARGET_HELD2024_CONTROL')
        cols=['y']+[c for c in frame if c.startswith('y_')];poison=frame.copy()
        for c in cols:
            poison[c]=poison[c].astype(object);poison.loc[poison.year.eq(2024),c]='FORBIDDEN_2024'
        pa=inp.Adapter(poison,provider);pb,_,pv,pmu,_=p.bundle(pa)
        checks={'held2024_parameters_exact':p.signature(adapter)==p.signature(pa) and p.canonical(primary)==p.canonical(pb),
                'held2024_features_prices_exact':va.equals(pv) and np.array_equal(mu,pmu)}
        assert all(checks.values()),checks
        del pa,poison,pb,pv,pmu
        role='held2023_fold_inputs';fold_checks=[]
        for fold in range(5):
            write_status('TARGET_HELD2023_CONTROL',fold=fold)
            poisoned=frame.copy()
            for c in cols:
                poisoned[c]=poisoned[c].astype(object);poisoned.loc[poisoned.year.eq(2023)&poisoned.fold.eq(fold),c]='FORBIDDEN_FOLD'
            aa=inp.Adapter(poisoned,provider);tt,vv=p.protected_branch(aa,fold)
            same=tt.equals(branches[fold][0]) and vv.equals(branches[fold][1])
            same &= all(p.canonical(v)==p.canonical(p.state(adapter)[key][name]) for key,part in p.state(aa).items() for name,v in part.items())
            fold_checks.append({'fold':fold,'entire_branch_exact':bool(same)})
            assert same,fold
        checks['five_held_fold_branches_exact']=all(x['entire_branch_exact'] for x in fold_checks)
        role='positive_training';positive=frame.copy();mask=positive.year.eq(2023)&(np.arange(len(frame))%7==0)
        for c in cols:positive.loc[mask,c]*=2
        aa=inp.Adapter(positive,provider);tt=inp.crossfit_features(aa,());mm=p.estimate(tt,primary['selection']['lambda'])
        checks['positive_target_parameters_change']=p.signature(aa)!=p.signature(adapter) and mm['beta']!=primary['final']['beta']
        # Este control positivo condiciona las fuentes: no reestima RKM/árboles.
        role='independent_optimizer';independent=model.fit(tr.base,tr.signal,tr.cell,tr.y,primary['selection']['lambda'],independent=True)
        checks['independent_objective']=abs(independent['loss']-primary['final']['loss'])<1e-10
    saved=p.read(OUT/'primary_parameters.json');source=provider.get((),inp.train_frame(frame,()))
    def forbidden(*a,**k):raise AssertionError('Estimador invocado durante replay')
    with patch.object(model,'fit',forbidden),patch.object(inp.e,'kopt',forbidden),patch.object(inp.e,'learn_recipe',forbidden),patch.object(inp.a,'completion',forbidden),patch.object(inp.e.v,'factor_train',forbidden):
        replay=inp.apply_features(frame[frame.year.eq(2024)].drop(columns=cols),source,saved['adapter']['base']['all'],saved['adapter']['recipes']['all']).sort_values('row_id').reset_index(drop=True)
        replay_mu=p.forward(replay,saved['calibrator']['final'])
    checks['replay_no_learning_exact']=replay.equals(va) and np.array_equal(replay_mu,mu)
    checks['expected_call_count34']=len(calls)==34
    checks['scopes26_and16']=len(adapter.base_parameters)==26 and len(adapter.recipes)==16
    provider.verify_consumed()
    result={'author':'Codex','utc':p.utc(),'checks':checks,'all_passed':all(checks.values()),'fold_controls':fold_checks,
        'calibrator_calls':len(calls),'call_roles':{r:sum(x['role']==r for x in calls) for r in sorted(set(x['role'] for x in calls))},
        'target_kopt_calls':sum(inp.e.COUNTS.values())-analytic_start,'primary_adapter_counts':adapter.counts,
        'analytical_counter_scope':'since_resume_only; interrupted analytical calls not fully journaled' if resume_primary else 'current_run_complete',
        'selected_lambda':primary['selection']['lambda'],'independent_objective_difference':abs(independent['loss']-primary['final']['loss']),
        'source_manifests':provider.manifests,'consumed_source_files':provider.consumed,'scores2024':0,'predictions2025':0,'submissions':0,
        'limits':['2024es desarrollo adaptativo, no confirmación virgen.','Fuente nativa por recibos; no nuevo refit adverso.','Normalización por lote heredada e historia pública A_M1 permanecen.','No demuestra mejora privada.']}
    guard();p.dump(OUT/'controls.json',result);assert result['all_passed'],checks
    p.dump(OUT/'artifact_seal.json',{'utc':p.utc(),'files':{n:p.sha(OUT/n) for n in ['primary_parameters.json','calibration_training2023.parquet','predictions2024.parquet','labels2024.parquet','controls.json']}})
    write_status('TARGET_COMPLETE_EVALUATION_PENDING',controls=str(OUT/'controls.json'),calibrator_calls=34,scores2024=0,new_submissions=0)


def wait_and_run():
    guard();assert p.read(OUT/'read_admission.json')['all_passed']
    assert p.read(OUT/'orchestration_smoke/controls.json')['all_passed']
    lease=OUT/'lease.json'
    with lease.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'process_created':psutil.Process().create_time(),'utc':p.utc()},f)
    try:
        while True:
            queue=p.read(SOURCE/'queue_status.json')
            if queue['state'].startswith('STOPPED'):raise RuntimeError('Cola fuente detenida; no iniciar destino')
            pending=[s['scope'] for s in p.read(R/'registro/semana2_F3c_regularizado_fuente_plan.json')['scopes'] if not (SOURCE/s['scope']/'source_complete.json').exists()]
            if not pending and queue['state']=='SOURCE_COMPLETE_TARGET_ADAPTER_PENDING':break
            write_status('WAITING_FOR_SOURCE',source_state=queue['state'],source_scope=queue.get('scope'),pending_scope_count=len(pending))
            time.sleep(30)
        with threadpool_limits(limits=2):run_target()
    finally:
        # El lease conserva PID/fecha y permite reconciliar la terminación.
        pass


def smoke(resume=False):
    global OUT
    guard();assert resume or not (OUT/'orchestration_smoke').exists()
    class FixtureSource(p.SyntheticSource):
        def __init__(self,frame):
            super().__init__(frame);self.manifests={};self.consumed={}
        def verify_consumed(self):pass
    original=OUT;OUT=original/'orchestration_smoke';OUT.mkdir(exist_ok=resume)
    if not resume:p.dump(OUT/'read_admission.json',{'all_passed':True,'synthetic_fixture_only':True})
    try:
        with patch.object(sys.modules[__name__],'guard',lambda:None),patch.object(inp.e,'load_em',p.fixture),patch.object(sys.modules[__name__],'StrictSource',FixtureSource):
            run_target(resume_primary=resume)
        result=p.read(OUT/'controls.json');assert result['calibrator_calls']==34 and result['all_passed']
        print(json.dumps({'orchestration_smoke_passed':True,'synthetic_calibrator_calls':34}),flush=True)
    finally:OUT=original


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['register','preflight','smoke','smoke-resume','admit-reader','wait']);arg=ap.parse_args()
    try:
        with threadpool_limits(limits=2):{'register':register,'preflight':preflight,'smoke':smoke,'smoke-resume':lambda:smoke(True),'admit-reader':admit_reader,'wait':wait_and_run}[arg.mode]()
    except Exception:
        if OUT.exists():
            stamp=p.utc().replace(':','').replace('.','')
            (OUT/('failure_'+stamp+'.txt')).write_text(traceback.format_exc(),encoding='utf-8')
            write_status('STOPPED_REQUIRES_RECONCILIATION',error=traceback.format_exc())
        raise
