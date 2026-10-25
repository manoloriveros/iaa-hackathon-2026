"""Consumidor final autorizado:3GLM de todo2023 y CSV propio2025."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import ExitStack
from unittest.mock import patch
import json,sys,traceback,socket,warnings
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(REPO/'herramientas'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import joblib
from threadpoolctl import threadpool_limits
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from semana2 import modelo_final_g4_2023 as core,entradas_g4_2023 as ingress
from probar_modelo_final_g4_2023 import verify
PLAN=REPO/'registro/semana2_g4_modelo_final_plan_v1.json'
RUN=REPO/'privado/semana2/modelo_final_g4_2023/final_20261024_v1'
rel=lambda p:p.relative_to(ROOT).as_posix()
now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def prove_source(path,spec):
    if spec['kind'] in ['prepared','raw_periods']:return ingress.footer_proof(path,spec['columns'],spec['kind'])
    with pq.ParquetFile(path) as pf:
        names=pf.schema_arrow.names
        assert set(spec['columns'])<=set(names)
        if spec['kind']=='quotes2025':
            for i in range(pf.num_row_groups):
                rg=pf.metadata.row_group(i)
                for name in ['period_start','period_end']:
                    stat=rg.column(names.index(name)).statistics
                    assert stat and stat.has_min_max and stat.null_count==0
                    assert pd.Timestamp(stat.min).year==pd.Timestamp(stat.max).year==2025
        return {'rows':pf.metadata.num_rows,'columns':spec['columns'],'kind':spec['kind']}

def main():
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    assert (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes().count(('<!-- aporte:'+plan['forum_prior']+' -->').encode())==1
    for it in plan['frozen_code']:assert ingress.sha(ROOT/it['path'])==it['sha256']
    attempt=1
    while (RUN/f'attempt{attempt}').exists():attempt+=1
    out=RUN/f'attempt{attempt}';out.mkdir()
    for it in plan['frozen_code']:(out/Path(it['path']).name).write_bytes((ROOT/it['path']).read_bytes())
    phase=['synthetic'];fits=[];source_events=[];forbidden=[]
    def event(name,**kw):
        x={'utc':now(),'event':name,**kw}
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(x)+'\n')
        print(json.dumps(x),flush=True)
    by_path={str((ROOT/s['path']).resolve()):(k,s) for k,s in plan['sources'].items()}
    real_reader=pq.read_table
    def guarded_read(path,*a,**kw):
        p=Path(path).resolve();cols=kw.get('columns');assert cols is not None,'Explicit projection required'
        if str(p) in by_path:
            name,spec=by_path[str(p)]
            assert phase[0] in (['predict'] if spec['kind'] in ['quotes2025','address_master','sample'] else ['train'])
            assert set(cols)<=set(spec['columns'])
            source_events.append({'phase':phase[0],'source':name,'path':rel(p),'columns':cols})
        else:assert p.is_relative_to(out),'Undeclared reader'
        return real_reader(path,*a,**kw)
    def no_network(*a,**kw):forbidden.append('network');raise AssertionError('Network not part of local fit')
    def read(name):
        spec=plan['sources'][name];p=ROOT/spec['path']
        assert ingress.sha(p)==spec['sha256'],name
        prove_source(p,spec)
        f=pq.read_table(p,columns=spec['columns']).to_pandas()
        if spec['kind']=='prepared':assert f.year.eq(2023).all()
        for col in ['period_start','period_end','loss_date','report_date']:
            if col in f:f[col]=pd.to_datetime(f[col])
        return f
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(socket.socket,'connect',no_network))
            stack.enter_context(patch.object(pq,'read_table',guarded_read))
            with threadpool_limits(limits=2):synthetic=verify(out/'synthetic_checks',plan['recipe'])
            dump(out/'synthetic_verification.json',synthetic)
            assert synthetic['success'] and len(synthetic['checks'])==8
            event('synthetic_verified',checks=len(synthetic['checks']),synthetic_GLM_fits=3,synthetic_reporting_fits=15)
            phase[0]='train';bundles={};receipts=[];training_stats=[]
            for line in core.LINES:
                event('training_started',line=line)
                frame,claims=core.assemble_training(read('static_'+line),read('coverage_'+line),read('claims_'+line),line,plan['recipe']['features_by_line'][line])
                versions={k:s['sha256'] for k,s in plan['sources'].items() if k.endswith('_'+line) and s['kind']!='quotes2025'}
                capital=None
                if line!='motor':
                    raw=read('raw_'+line)
                    capital,population=core.fit_capital_final(frame,raw,line,versions)
                    frame,capital_check=core.apply_capital(frame,raw,capital)
                    dump(out/f'capital/{line}.json',capital)
                    path=out/f'capital/{line}_population.parquet';pq.write_table(pa.Table.from_pandas(population,preserve_index=False),path)
                else:capital_check=None
                c0=core.fit_c0_final(frame,claims,line,versions)
                e,c0check=core.training_c0(frame,c0)
                dump(out/f'C0/{line}.json',c0)
                with threadpool_limits(limits=2):bundle,receipt=core.fit_glm_final(frame,e,plan['recipe'],line,capital,c0)
                fits.append({'line':line,'kind':'real_full2023_GLM','rows':len(frame)})
                folder=out/'models';folder.mkdir(exist_ok=True)
                joblib.dump(bundle,folder/(line+'.joblib'),compress=3)
                dump(folder/(line+'_receipt.json'),receipt)
                bundles[line]=bundle;receipts.append(receipt)
                path=out/f'training/{line}_2023.parquet';path.parent.mkdir(exist_ok=True)
                training=frame.copy();training['C0']=e
                pq.write_table(pa.Table.from_pandas(training,preserve_index=False),path)
                training_stats.append({'line':line,'rows':len(frame),'claims':len(claims),'reporting_fits':len(c0['curves']),
                    'capital':capital_check,'C0':c0check,'model_state_sha256':core.learned_state_digest(bundle)})
                event('training_completed',line=line,real_GLM_fits=len(fits),rows=len(frame),gradient=receipt['max_abs_penalized_gradient'])
            assert len(fits)==3
            phase[0]='predict';addresses=read('addresses');predictions=[];quote_checks=[];quote_frames={};states={line:core.learned_state_digest(b) for line,b in bundles.items()}
            for line in core.LINES:
                raw=read('test_'+line)
                frame,audit=core.quote_features(raw,addresses,line,plan['recipe']['features_by_line'][line],bundles[line]['capital'])
                with threadpool_limits(limits=2):pred,check=core.predict_quotes(bundles[line],frame)
                assert states[line]==core.learned_state_digest(bundles[line]),'Prediction mutated fitted state'
                quote_frames[line]=frame;pred['line']=line;predictions.append(pred)
                quote_checks.append({'line':line,**check,'input_audit':audit})
                path=out/f'quotes/{line}_2025.parquet';path.parent.mkdir(exist_ok=True)
                pq.write_table(pa.Table.from_pandas(frame,preserve_index=False),path)
                event('prediction_completed',line=line,rows=len(pred))
            combined=pd.concat(predictions,ignore_index=True)
            assert len(combined)==209063 and not combined.row_id.duplicated().any()
            sample=read('sample')
            assert len(sample)==209063 and sample.row_id.is_unique and set(sample.row_id)==set(combined.row_id)
            ordered=sample[['row_id']].merge(combined[['row_id','prediction']],on='row_id',how='left',sort=False,validate='one_to_one')
            assert ordered.row_id.equals(sample.row_id) and np.isfinite(ordered.prediction).all() and ordered.prediction.gt(0).all()
            csvpath=out/'submission_g4_glm_2023_2025.csv';ordered.to_csv(csvpath,index=False,float_format='%.17g')
            loaded=pd.read_csv(csvpath,dtype={'row_id':str},float_precision='round_trip')
            assert list(loaded)==['row_id','prediction'] and loaded.row_id.equals(ordered.row_id)
            assert np.array_equal(loaded.prediction,ordered.prediction)
            # Replay de todos los modelos desde disco; ningún aprendizaje permitido.
            phase[0]='replay';replays=[]
            def no_fit(*a,**kw):raise AssertionError('Replay must not learn')
            with ExitStack() as replay_stack:
                for owner,name in [(TweedieRegressor,'fit'),(Pipeline,'fit'),(ColumnTransformer,'fit_transform'),(SimpleImputer,'fit'),
                    (StandardScaler,'fit'),(OneHotEncoder,'fit'),(core,'fit_c0_final'),(core,'fit_capital_final')]:
                    replay_stack.enter_context(patch.object(owner,name,no_fit))
                for line in core.LINES:
                    bundle=joblib.load(out/'models'/(line+'.joblib'))
                    assert core.learned_state_digest(bundle)==states[line]
                    with threadpool_limits(limits=2):replay,_=core.predict_quotes(bundle,quote_frames[line])
                    original=combined.loc[combined.line.eq(line),['row_id','prediction']].reset_index(drop=True)
                    assert replay.reset_index(drop=True).equals(original)
                    replays.append({'line':line,'rows':len(replay),'exact':True,'new_fits':0})
            assert all(e['phase']=='predict' for e in source_events if e['source'].startswith('test_'))
        for it in plan['frozen_code']:assert ingress.sha(ROOT/it['path'])==it['sha256']
        for name,s in plan['sources'].items():assert ingress.sha(ROOT/s['path'])==s['sha256'],name
        assert not forbidden
        dump(out/'training_receipts.json',{'GLM':receipts,'scope':core.SCOPE,'training_only_not_validation':True})
        dump(out/'validation.json',{'success':True,'synthetic':{'checks':8,'GLM_fits':3,'reporting_fits':15},
            'training':training_stats,'quotes':quote_checks,'disk_replays':replays,'source_reader_events':source_events,
            'test_decoders_only_after_all_three_fits':True,'learned_state_unchanged_during_prediction':True,
            'csv_roundtrip_exact':True,'2024_policy_rows_read':0,'2024_scores_consulted':False,'network_calls':0})
        result={'id':plan['id'],'author':'Codex','utc':now(),'success':True,'attempt':attempt,'out':rel(out),
            'scope':core.SCOPE,'model_id':'G4-GLM2023-FINAL-v1','real_price_GLM_fits':3,'real_reporting_fits':15,
            'real_frequency_constants':15,'synthetic_GLM_fits':3,'synthetic_reporting_fits':15,
            'training_rows':sum(r['rows'] for r in training_stats),'prediction_rows':len(ordered),
            'CSV':{'path':rel(csvpath),'sha256':ingress.sha(csvpath),'rows':len(ordered),'columns':['row_id','prediction']},
            'replay_exact':True,'2024_closed':True,'reference':'W2-B00','B00_preserved':True,
            'promotion':False,'manual_final_selection':False,'submission_sent':False,'professional_independent_validation':False}
        dump(out/'result.json',result);dump(RUN/'ready_current.json',result)
        event('completed',CSV=rel(csvpath),rows=len(ordered),real_price_fits=3)
        return 0
    except Exception as exc:
        dump(out/'failure.json',{'id':plan['id'],'utc':now(),'phase':phase[0],'exception':type(exc).__name__,'message':str(exc),
            'traceback':traceback.format_exc(),'completed_real_price_fits':fits,'reader_events':source_events,'forbidden_calls':forbidden})
        event('failed',exception=type(exc).__name__,message=str(exc),failure=rel(out/'failure.json'))
        return 1

if __name__=='__main__':raise SystemExit(main())
