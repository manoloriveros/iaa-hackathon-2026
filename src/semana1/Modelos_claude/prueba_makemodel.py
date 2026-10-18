import json, numpy as np, pandas as pd
from comun import WORK, d2, to_model_frame
from experimentos import features, fit, load, predict
cfg = json.load(open('/home/claude/work/cfg_total.json'))['motor']['params']
df = load('motor'); print('niveles make_model', df.make_model.nunique())
inter = pd.read_parquet(WORK / 'inter_motor.parquet'); df['row_id_s'] = df.row_id.astype(str)
df = df.merge(inter[['row_id','mm_frec_suav','mm_expuestos_previos']].rename(columns={'row_id':'row_id_s'}), on='row_id_s', how='left')
base = features('motor', df, 'F01234')
y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
for tag, feats in [("sin_make_model", [f for f in base if f != "make_model"]), ("mm_codificado_en_lugar", [f for f in base if f != "make_model"] + ["mm_frec_suav", "mm_expuestos_previos"])]:
    X = to_model_frame(df, feats)
    b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg))
    print(tag, round(d2(y[sel], predict(b, s, X[sel], off[sel], b.best_iteration)), 5), b.best_iteration, flush=True)
