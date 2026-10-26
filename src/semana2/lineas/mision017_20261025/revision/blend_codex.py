import numpy as np, pandas as pd, json
exec(open("forma_v2.py").read().split("out = {}")[0])
cx = pd.read_parquet("codex/new_oof_2023.parquet"); print(cx.model_id.value_counts().to_dict())
t = sets["DEV23_T2b"].copy(); w = pesos(t); res = {}
for mid in sorted(cx.model_id.unique()):
    r = cx[cx.model_id == mid].set_index("row_id").prediction.reindex(t.index)
    assert r.notna().all()
    base = d2w(t, nivel_celda(t, t.m.values), w); out = {"T2b_solo": round(base, 5), "codex_solo": round(d2w(t, nivel_celda(t, r.values), w), 5)}
    for a in (0.1, 0.2, 0.3, 0.5):
        g = np.exp((1 - a) * np.log(t.m.values) + a * np.log(r.values))
        out[f"geo_{a}"] = round(d2w(t, nivel_celda(t, g), w) - base, 5)
    corr = np.corrcoef(np.log(t.m.values), np.log(r.values))[0, 1]; out["corr_log"] = round(corr, 3); res[mid] = out
print(json.dumps(res, indent=1)); json.dump(res, open("blend_codex.json", "w"), indent=1)
