import numpy as np
from comun import d2, to_model_frame
from experimentos import features, fit, load, predict
L7 = {"learning_rate": 0.02, "num_leaves": 7, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16}
plan = {"motor": (dict(L7, feature_fraction=0.6), 981, [50000.0, 25000.0]),
        "buildings": (dict(L7, num_leaves=5), 350, [None, 200000.0, 100000.0]),
        "contents": (dict(L7, min_data_in_leaf=4000), 303, [None, 50000.0, 25000.0])}
for line, (params, r, caps) in plan.items():
    df = load(line); feats = features(line, df, "F0124"); X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
    tr = (df.year <= 2023).values; ev = (df.year == 2024).values
    for cap in caps:
        p = dict(params)
        if cap: p["cap"] = cap
        b, base = fit(X[tr], y[tr], off[tr], rounds=int(round(r * 1.15)), early=None, params=p)
        mu = predict(b, base, X[ev], off[ev])
        print(line, "cap", cap, "loading", round(b.loading, 4), "d2_v24", round(d2(y[ev], mu), 5), "balance", round(mu.sum()/y[ev].sum(), 4), flush=True)
