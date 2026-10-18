import sys, numpy as np
from comun import d2, to_model_frame
from experimentos import features, fit, load, predict
L7 = {"learning_rate": 0.02, "num_leaves": 7, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16, "feature_fraction": 0.6}
df = load("motor"); feats = features("motor", df, "F0124"); X = to_model_frame(df, feats)
y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
tr = (df.year <= 2023).values; ev = (df.year == 2024).values
for cap in [None, 300000.0, 100000.0]:
    p = dict(L7); 
    if cap: p["cap"] = cap
    b, base = fit(X[tr], y[tr], off[tr], rounds=1128, early=None, params=p)
    mu = predict(b, base, X[ev], off[ev])
    print("cap", cap, "loading", round(b.loading, 4), "d2_v24", round(d2(y[ev], mu), 5), "balance", round(mu.sum()/y[ev].sum(), 4), flush=True)
