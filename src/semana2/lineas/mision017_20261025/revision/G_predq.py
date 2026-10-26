"""Factores por quintil de tasa predicha en motor_1 (sobre series ya transformadas como F2): por año, juntos, y prueba fuera de tiempo con
quintiles 2023->2024, 2024->2023, también con 10 tramos y con k distinto."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
exec(open("E_gratis.py").read().split("res = []")[0])
def lab_q(t, cortes_p):
    r = t.m.values / (t.exposure.values * t.c_fila.values); out = np.full(len(t), "x", object)
    i = t.cel.values == "motor_1"; q = np.quantile(r[i], cortes_p); out[i] = np.digitize(r[i], q).astype(str); return out
out = {}
for nombre, cp in (("q5", [0.2, 0.4, 0.6, 0.8]), ("q10", list(np.arange(0.1, 0.95, 0.1))), ("q3", [1/3, 2/3])):
    for k in (100, 300, 1000):
        r = {}
        for a, bb in (("T2b_2023", "mezcla_2024"), ("mezcla_2024", "T2b_2023")):
            tr, te = SS[a], SS[bb]; w = pesos(te); f = factores(tr, lab_q(tr, cp), ["motor_1"], k)
            r[f"{a[-4:]}->{bb[-4:]}"] = round(d2w(te, nivel(te, aplica(te, lab_q(te, cp), f)), w) - d2w(te, nivel(te, te.m.values), w), 5)
            r[f"factores_{a[-4:]}"] = {v: round(x, 3) for (c, v), x in sorted(f.items())}
        out[f"{nombre}_k{k}"] = r
for k, v in out.items(): print(k, {kk: vv for kk, vv in v.items() if not kk.startswith("fact")}, v["factores_2023"] if "q5" in k and "300" in k else "")
print(out["q5_k300"]["factores_2024"])
json.dump(out, open("/home/claude/m017/revision/G_predq.json", "w"), indent=1)
