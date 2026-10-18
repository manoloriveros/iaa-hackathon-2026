import json, numpy as np, pandas as pd
from comun import d2, to_model_frame
from experimentos import features, fit, load, predict
cfg = json.load(open('/home/claude/work/cfg_total.json'))['motor']['params']
df = load('motor'); base_feats = features('motor', df, 'F0124')
groups = {"telematica": ["telematics_opt_in", "telematics_score"],
          "cliente": ["occupation", "marital_status", "household_size", "credit_band", "prior_claims_5y", "licence_points", "years_at_address"],
          "comercial": ["email_domain", "marketing_consent", "document_preference", "previous_insurer", "campaign_code", "branch_id", "missed_payments_12m"]}
y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
res = {}
for g, cols in groups.items():
    feats = base_feats + cols
    X = to_model_frame(df, feats)
    b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg))
    best = b.best_iteration or b.current_iteration()
    mu = predict(b, base, X[sel], off[sel], best)
    imp = pd.Series(b.feature_importance("gain"), index=feats)
    res[g] = {"d2_sel": round(d2(y[sel], mu), 5), "best": best, "gain_share": {c: round(float(imp[c] / imp.sum()), 4) for c in cols}}
    print(g, res[g], flush=True)
json.dump(res, open('/home/claude/work/ablacion_f3_motor.json', 'w'), indent=1)
