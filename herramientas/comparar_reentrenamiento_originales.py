"""Coteja una corrida terminada o parcial, sin entrenar ni puntuar modelos.

Los históricos se abren únicamente aquí, fuera del cálculo aislado de la receta.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PRIVATE = REPO / 'privado/semana2'
LINES = ('motor', 'buildings', 'contents')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def frame(p):
    return pd.read_csv(p,dtype={'row_id':str}) if p.suffix=='.csv' else pd.read_parquet(p)


def compare(a,b,cols=None):
    x,y=frame(a),frame(b)
    out={'new_sha256':sha(a),'historical_sha256':sha(b),'bytes_exact':sha(a)==sha(b),
         'rows_new':len(x),'rows_historical':len(y),'unique_new':bool(x.row_id.is_unique),
         'unique_historical':bool(y.row_id.is_unique),'columns_new':list(x.columns),'columns_historical':list(y.columns)}
    out['same_keys']=set(x.row_id)==set(y.row_id)
    if not (out['same_keys'] and out['unique_new'] and out['unique_historical']):return out
    out['same_order']=x.row_id.tolist()==y.row_id.tolist()
    x=x.set_index('row_id');y=y.set_index('row_id').loc[x.index]
    cols=cols or [c for c in x if c in y and pd.api.types.is_numeric_dtype(x[c])]
    out['columns']={}
    for col in cols:
        u,v=x[col].to_numpy(dtype=float),y[col].to_numpy(dtype=float)
        same_nan=np.array_equal(np.isnan(u),np.isnan(v));mask=np.isfinite(u)&np.isfinite(v)
        delta=np.abs(u[mask]-v[mask]);relative=delta/np.maximum(np.abs(v[mask]),1e-12)
        out['columns'][col]={'same_nan':same_nan,'exact_values':bool(np.array_equal(u,v,equal_nan=True)),
          'different_values':int((u[mask]!=v[mask]).sum()),'max_abs':float(delta.max(initial=0)),
          'max_rel':float(relative.max(initial=0)),'close_1e10_1e9':bool(np.allclose(u,v,rtol=1e-10,atol=1e-9,equal_nan=True))}
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--trabajo',type=Path,required=True);ap.add_argument('--salida',type=Path,required=True);a=ap.parse_args()
    work=a.trabajo.resolve();assert REPO/'privado' in work.parents
    assert not a.salida.exists(),'Usar un recibo nuevo para conservar los cortes anteriores'
    result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','training':False,'new_scores':False,
            'comparisons':{},'model_text':{},'missing_outputs':[]}
    reference=PRIVATE/'mision017_fase2/linaje_T2b_v1'
    for phase in ('dev','hold','pcv'):
        for line in LINES:
            name=f'T2b_{phase}_{line}';new=work/f'ml/trabajo/pred/{phase}/T2b_{line}.parquet';old=reference/f'pred/{phase}/T2b_{line}.parquet'
            if new.exists() and old.exists():result['comparisons'][name]=compare(new,old,['mu'])
            else:result['missing_outputs'].append(name)
    for scope in ('dev','prod'):
        for line in LINES:
            new=work/f'ml/trabajo/modelos/{scope}/T2b_{line}.txt';old=reference/f'modelos/{scope}/T2b_{line}.txt'
            if new.exists() and old.exists():
                u,v=new.read_text(encoding='utf-8'),old.read_text(encoding='utf-8')
                result['model_text'][f'{scope}_{line}']={'new_sha256':sha(new),'historical_sha256':sha(old),'bytes_exact':sha(new)==sha(old),'new_trees':u.count('Tree='),'historical_trees':v.count('Tree=')}
    pairs={
      'ML_C1':(work/'ml/privado/prediccion_2025_mlind.csv',PRIVATE/'claude_ml_independiente_20261023/prediccion_2025_mlind.csv'),
      'A1fixb3':(work/'noche/salidas/correccion/A1fixb3_2025.csv',PRIVATE/'claude_validacion_nocturna_20261023/A1fixb3_2025.csv'),
      'A1fixF1b3n':(work/'noche/salidas/correccion/A1fixF1b3n_2025.csv',PRIVATE/'claude_validacion_nocturna_20261023/A1fixF1b3n_2025.csv'),
      'A1_hold':(work/'noche/salidas/correccion/predicciones_2024.parquet',PRIVATE/'claude_validacion_nocturna_20261023/predicciones_2024.parquet'),
      'F':(work/'m017/in/final_sonda_global_2025.csv',PRIVATE/'claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv'),
      'F2':(work/'m017/F2_ncb_previos_2025.csv',PRIVATE/'claude_mision017_20261025/F2_ncb_previos_2025.csv'),
      'final_creible':(work/'m017/final_creible_2025.csv',PRIVATE/'mision017_fase2/calibracion_F2_creible_20261025_v1/final_creible_2025.csv'),
      **{name:(work/f'm017/exp26/{name}_2025.csv',PRIVATE/f'claude_mision017_20261025/{name}_2025.csv') for name in ('F3c','F3d','F4c')},
    }
    for name,(new,old) in pairs.items():
        if new.exists() and old.exists():result['comparisons'][name]=compare(new,old,['A1','R0'] if name=='A1_hold' else ['prediction'])
        else:result['missing_outputs'].append(name)
    a.salida.parent.mkdir(parents=True,exist_ok=True);a.salida.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'compared':len(result['comparisons']),'models':len(result['model_text']),'missing':result['missing_outputs'],'output':str(a.salida)},ensure_ascii=False))


if __name__=='__main__':main()
