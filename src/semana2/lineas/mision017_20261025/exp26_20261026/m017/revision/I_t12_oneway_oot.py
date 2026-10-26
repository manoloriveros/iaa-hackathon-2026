"""Tareas 1 y 2: A/E y factores Tweedie-óptimos por año y NB/REN; ganancias fuera de tiempo una a una y secuenciales."""
import sys, json
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

df = cargar()
OUT = "/home/claude/m017/revision"
rows, summ = [], {}
for line, vs in VARS.items():
    L = Linea(df, line)
    for yr in (2023, 2024):
        B = L.yr[yr]
        w = np.ones(len(B["y"]))
        mlev = nivel(B["y"], B["m"], B["cell"], w)
        # A/E clásico relativo a la celda: m escalado para que Σm = Σy en cada celda
        ae_s = np.bincount(B["cell"], B["y"], 2) / np.bincount(B["cell"], B["m"], 2)
        m_ae = B["m"] * ae_s[B["cell"]]
        for v in vs:
            cd = L.code(v, yr)
            for g, sel in (("ALL", np.ones(len(cd), bool)), ("REN", B["cell"] == 0), ("NB", B["cell"] == 1)):
                for j, lev in enumerate(L.levels[v]):
                    s = sel & (cd == j)
                    if s.sum() == 0:
                        continue
                    y, m1, m2 = B["y"][s], m_ae[s], mlev[s]
                    rows.append(dict(line=line, var=v, year=yr, grp=g, level=lev, rows=int(s.sum()),
                                     claims=int((y > 0).sum()), AE=y.sum() / m1.sum(),
                                     k_tw=np.sum(y / np.sqrt(m2)) / np.sum(np.sqrt(m2))))
t1 = pd.DataFrame(rows)
t1.to_csv(f"{OUT}/I_t1_oneway.csv", index=False)

# estabilidad entre años de los factores por nivel (ALL), correlación ponderada de log k_tw
stab = {}
for (line, v), g in t1[t1.grp == "ALL"].groupby(["line", "var"]):
    p = g.pivot_table(index="level", columns="year", values=["k_tw", "claims"])
    ok = (p["claims"][2023] >= 5) & (p["claims"][2024] >= 5)
    a, b = np.log(p["k_tw"][2023][ok]), np.log(p["k_tw"][2024][ok])
    w = np.minimum(p["claims"][2023][ok], p["claims"][2024][ok])
    wc = np.cov(a, b, aweights=w)
    stab[f"{line}|{v}"] = dict(levels=int(ok.sum()), corr_logk_w=float(wc[0, 1] / np.sqrt(wc[0, 0] * wc[1, 1])),
                               corr_logk=float(np.corrcoef(a, b)[0, 1]))
summ["estabilidad_niveles"] = stab
print(json.dumps(stab, indent=1))

# tablas compactas para variables de pocos niveles
for line, v in (("motor", "gender"), ("contents", "gender"), ("contents", "works_from_home"), ("contents", "marketing_segment")):
    s = t1[(t1.line == line) & (t1["var"] == v)]
    print(line, v)
    print(s.pivot_table(index="level", columns=["grp", "year"], values=["AE"]).round(3).to_string())
    print(s.pivot_table(index="level", columns=["grp", "year"], values=["claims"]).to_string())

# ---------------------------------------------------------------- tarea 2: ganancias fuera de tiempo
res = []
for line, vs in VARS.items():
    L = Linea(df, line)
    for K in (150, 300, 600):
        for tr, te in ((2023, 2024), (2024, 2023)):
            for v in vs:
                g = oot(L, tr, te, [v], K)
                res.append(dict(line=line, K=K, dir=f"{tr}->{te}", step=f"oneway:{v}", **{k: g[k] for k in ("all", "nb", "ren")}))
            gs = oot(L, tr, te, vs, K, steps=True)
            for i, g in enumerate(gs):
                res.append(dict(line=line, K=K, dir=f"{tr}->{te}", step=f"seq{i + 1}:+{vs[i]}", **{k: g[k] for k in ("all", "nb", "ren")}))
t2 = pd.DataFrame(res)
t2.to_csv(f"{OUT}/I_t2_oot.csv", index=False)
pd.set_option("display.width", 200)
print((t2.set_index(["line", "K", "step", "dir"])[["all", "nb", "ren"]] * 1e4).round(1).unstack("dir").to_string())
summ["oot_K300"] = {f"{r.line}|{r.step}|{r.dir}": dict(all=round(r.all, 5), nb=round(r.nb, 5), ren=round(r.ren, 5))
                    for r in t2[t2.K == 300].itertuples()}
json.dump(summ, open(f"{OUT}/I_t12.json", "w"), indent=1)
