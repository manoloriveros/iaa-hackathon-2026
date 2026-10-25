"""Adversos del guard nuevo y replay desde raw2025, sin ajustes."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import ExitStack
from unittest.mock import patch
import json,sys,socket
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from threadpoolctl import threadpool_limits
from semana2 import modelo_final_g4_2023 as core,entradas_g4_2023 as ingress
RUN=REPO/'privado/semana2/modelo_final_g4_2023/final_20261024_v1'

def main():
    result=json.loads((RUN/'ready_current.json').read_text(encoding='utf-8'));out=ROOT/result['out']
    plan=json.loads((REPO/'registro/semana2_g4_modelo_final_plan_v1.json').read_text(encoding='utf-8'))
    assert (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes().count(b'<!-- aporte:COD-S2-20261024-G4-FINAL-GUARD1 -->')==1
    snapshots=RUN/'guard1_sources';snapshots.mkdir()
    for p in [Path(core.__file__),Path(__file__)]:
        (snapshots/p.name).write_bytes(p.read_bytes())
    checks=[]
    def reject(name,fn):
        try:fn()
        except ValueError:checks.append({'check':name,'pass':True});return
        raise AssertionError('Accepted bad guard case:'+name)
    f=pd.DataFrame([{'market':'emerging','line':'buildings','row_id':'SYN-G4-GUARD','year':2025,'is_test':True}])
    raw=pd.DataFrame([{'row_id':'SYN-G4-GUARD','sum_insured':2000000.,'written_premium':2000.}])
    b=json.loads((out/'capital/buildings.json').read_text(encoding='utf-8'));c=json.loads((out/'capital/contents.json').read_text(encoding='utf-8'))
    def reseal(obj,**changes):
        p={**{k:v for k,v in obj.items() if k!='sha256'},**changes};p['sha256']=core.digest(p);return p
    reject('valid_other_branch_artifact',lambda:core.apply_capital(f,raw,c))
    reject('resealed_outer_as_final',lambda:core.apply_capital(f,raw,reseal(b,excluded_folds=[0])))
    reject('resealed_wrong_threshold',lambda:core.apply_capital(f,raw,reseal(b,threshold=1000000.)))
    bad=f.copy();bad['year']=2024
    reject('synthetic_nonadmissible_application_year',lambda:core.apply_capital(bad,raw,b))
    wrong_c0=json.loads((out/'C0/buildings.json').read_text(encoding='utf-8'));wrong_c0=reseal(wrong_c0,scope='outer_fold0')
    reject('resealed_outer_C0_as_final',lambda:core.training_c0(f,wrong_c0))
    original_csv=pd.read_csv(ROOT/result['CSV']['path'],dtype={'row_id':str},float_precision='round_trip')
    versions_before={line:ingress.sha(out/'models'/(line+'.joblib')) for line in core.LINES}
    def nofit(*a,**kw):raise AssertionError('Guard repair must not refit/C0/network')
    predictions=[]
    with ExitStack() as stack:
        for owner,name in [(TweedieRegressor,'fit'),(Pipeline,'fit'),(ColumnTransformer,'fit_transform'),(SimpleImputer,'fit'),
            (StandardScaler,'fit'),(OneHotEncoder,'fit'),(core,'fit_c0_final'),(core,'fit_capital_final'),(socket.socket,'connect')]:
            stack.enter_context(patch.object(owner,name,nofit))
        def read(name):
            spec=plan['sources'][name];p=ROOT/spec['path'];assert ingress.sha(p)==spec['sha256']
            return pq.read_table(p,columns=spec['columns']).to_pandas()
        addresses=read('addresses')
        for line in core.LINES:
            bundle=joblib.load(out/'models'/(line+'.joblib'))
            frame,_=core.quote_features(read('test_'+line),addresses,line,plan['recipe']['features_by_line'][line],bundle['capital'])
            saved=pq.read_table(out/'quotes'/(line+'_2025.parquet'),columns=list(frame.columns)).to_pandas()
            pd.testing.assert_frame_equal(frame,saved,check_dtype=False)
            with threadpool_limits(limits=2):pred,_=core.predict_quotes(bundle,frame)
            predictions.append(pred)
            checks.append({'check':'raw2025_features_identical_after_guard_'+line,'pass':True})
        joined=pd.concat(predictions,ignore_index=True)
        ordered=original_csv[['row_id']].merge(joined,on='row_id',how='left',sort=False,validate='one_to_one')
        assert np.array_equal(original_csv.prediction,ordered.prediction) and len(ordered)==209063
    assert versions_before=={line:ingress.sha(out/'models'/(line+'.joblib')) for line in core.LINES}
    assert ingress.sha(ROOT/result['CSV']['path'])==result['CSV']['sha256']
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'success':True,'checks':checks,
        'new_core_sha256':ingress.sha(Path(core.__file__)),'source_snapshots':str(snapshots.relative_to(ROOT)).replace('\\','/'),
        'raw_feature_tables_identical':True,'CSV_exact':True,'rows':209063,'model_files_unchanged':True,
        'new_model_fits':0,'new_C0_fits':0,'2024_policy_rows_read':0,'scope':'Only added guards changed,no learned numeric values or forecasts'}
    with (RUN/'guard1_verification.json').open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write('\n')
    print(json.dumps(receipt,ensure_ascii=True))

if __name__=='__main__':main()
