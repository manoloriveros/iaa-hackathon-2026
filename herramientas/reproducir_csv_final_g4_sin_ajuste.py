"""Replay autónomo del CSV final desde objetos/entradas congelados; cero fit."""
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from datetime import datetime,timezone
import argparse,json,sys,socket
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from semana2 import modelo_final_g4_2023 as core,entradas_g4_2023 as ingress

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--receipt',required=True);args=p.parse_args()
    manifest_path=Path(args.manifest).resolve();receipt=Path(args.receipt).resolve()
    assert manifest_path.is_relative_to(ROOT) and receipt.is_relative_to(ROOT) and not receipt.exists()
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    for spec in manifest['files']:
        path=(ROOT/spec['path']).resolve();assert path.is_relative_to(ROOT) and ingress.sha(path)==spec['sha256'],spec['path']
    def blocked(*a,**kw):raise AssertionError('No fitting/C0/network during standalone replay')
    frames=[]
    with ExitStack() as stack:
        for owner,name in [(TweedieRegressor,'fit'),(Pipeline,'fit'),(ColumnTransformer,'fit_transform'),(SimpleImputer,'fit'),
            (StandardScaler,'fit'),(OneHotEncoder,'fit'),(core,'fit_c0_final'),(core,'fit_capital_final'),(socket.socket,'connect')]:
            stack.enter_context(patch.object(owner,name,blocked))
        for item in manifest['branches']:
            model=joblib.load(ROOT/item['model'])
            feature_path=ROOT/item['quotes']
            with pq.ParquetFile(feature_path) as pf:
                cols=pf.schema_arrow.names
                for i in range(pf.num_row_groups):
                    stat=pf.metadata.row_group(i).column(cols.index('year')).statistics
                    assert stat and stat.min==stat.max==2025
            quotes=pq.read_table(feature_path,columns=cols).to_pandas()
            with threadpool_limits(limits=2):prediction,_=core.predict_quotes(model,quotes)
            frames.append(prediction)
        joined=pd.concat(frames,ignore_index=True)
        original=pd.read_csv(ROOT/manifest['CSV'],dtype={'row_id':str},float_precision='round_trip')
        assert len(joined)==209063 and joined.row_id.is_unique
        ordered=original[['row_id']].merge(joined,on='row_id',how='left',sort=False,validate='one_to_one')
        assert original.row_id.equals(ordered.row_id) and np.array_equal(original.prediction,ordered.prediction)
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'success':True,'rows':len(ordered),
        'CSV':manifest['CSV'],'CSV_sha256':ingress.sha(ROOT/manifest['CSV']),'replay_exact':True,
        'model_fits':0,'C0_fits':0,'capital_parameter_estimates':0,'2024_policy_rows_read':0,'network_calls':0}
    with receipt.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=True))

if __name__=='__main__':main()
