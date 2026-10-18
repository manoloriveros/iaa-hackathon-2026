import numpy as np
from comun import d2, to_model_frame
from experimentos import features, fit, load, predict
L7 = {"learning_rate": 0.02, "num_leaves": 7, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16}
plan = {"motor": (dict(L7, feature_fraction=0.6), 981, [15000.0, 10000.0]),
}
for line, (params, r, caps) in plan.items():
    df = load(line); feats = features(line, df, "F0124"); X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
    tr = df.year.isin([2021, 2022]).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    for cap in caps:
        p = dict(params)
        if cap: p["cap"] = cap
        b, base = fit(X[tr], y[tr], off[tr], rounds=r, early=None, params=p)
        mu = predict(b, base, X[sel], off[sel])
        f = y[sel].sum() / mu.sum()
        print(line, "cap", cap, "loading", round(b.loading, 4), "d2_sel", round(d2(y[sel], mu), 5), "d2_sel_mismo_nivel", round(d2(y[sel], mu * f), 5), "balance", round(mu.sum()/y[sel].sum(), 4), flush=True)
