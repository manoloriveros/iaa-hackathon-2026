import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
exec(open("G_predq.py").read().split("out = {}")[0])
def sin_top(t, n=20):
    i = np.where(t.cel.values == "motor_1")[0]; top = i[np.argsort(-t.y.values[i])[:n]]
    keep = np.ones(len(t), bool); keep[top] = False; return t[keep].reset_index(drop=True) if isinstance(t.index, pd.RangeIndex) else t[keep]
cp = [0.2, 0.4, 0.6, 0.8]; out = {}
for k in (100, 300):
    for modo in ("eval_sin_top", "estim_sin_top"):
        r = {}
        for a, bb in (("T2b_2023", "mezcla_2024"), ("mezcla_2024", "T2b_2023")):
            tr, te = SS[a], SS[bb]
            if modo == "eval_sin_top": te = sin_top(te)
            else: tr = sin_top(tr)
            w = pesos(te); f = factores(tr, lab_q(tr, cp), ["motor_1"], k)
            r[f"{a[-4:]}->{bb[-4:]}"] = round(d2w(te, nivel(te, aplica(te, lab_q(te, cp), f)), w) - d2w(te, nivel(te, te.m.values), w), 5)
        out[f"k{k}_{modo}"] = r
# bootstrap por cliente de la ganancia 2023->2024 (k=300)
rng = np.random.default_rng(1); tr, te = SS["T2b_2023"], SS["mezcla_2024"]; f = factores(tr, lab_q(tr, cp), ["motor_1"], 300)
w = pesos(te); m1 = nivel(te, aplica(te, lab_q(te, cp), f)); m0 = nivel(te, te.m.values); y = te.y.values
dd = (dev(y, m0) - dev(y, m1)) * w; mu0 = np.average(y, weights=w); nul = dev(y, np.full(len(y), mu0)) * w
cid = te.customer_id.values; u, inv = np.unique(cid, return_inverse=True); sd = np.bincount(inv, dd); sn = np.bincount(inv, nul)
g = [ (lambda s: sd[s].sum() / sn[s].sum())(rng.integers(0, len(u), len(u))) for _ in range(1000)]
out["bootstrap_23_24_k300_p05_p50_p95"] = [round(float(np.percentile(g, q)), 5) for q in (5, 50, 95)]
print(json.dumps(out, indent=1)); json.dump(out, open("/home/claude/m017/revision/G_predq_rob.json", "w"), indent=1)
