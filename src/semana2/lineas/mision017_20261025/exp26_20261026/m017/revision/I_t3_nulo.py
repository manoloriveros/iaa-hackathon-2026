"""Tarea 3: nulo por permutación de la variable entre clientes (cada cliente conserva un valor fijo en ambos años;
mismos niveles y mismos tamaños de nivel). K = 300. Estadísticos: ganancia 23->24, 24->23, mínimo de ambas;
para cada variable una a una (sobre la base T2b) y como incremento dentro de la secuencia del autor."""
import sys, json, time
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
K = 300
df = cargar()
OUT = "/home/claude/m017/revision"
rng = np.random.default_rng(20261026)
DIRS = ((2023, 2024), (2024, 2023))
rows, real = [], {}
t0 = time.time()
for line, vs in VARS.items():
    L = Linea(df, line)
    # valores reales
    for j, v in enumerate(vs):
        prev = vs[:j]
        for tr, te in DIRS:
            g1 = oot(L, tr, te, [v], K)
            gp = oot(L, tr, te, prev, K)["all"] if prev else 0.0
            gs = oot(L, tr, te, prev + [v], K)["all"]
            real[(line, v, tr)] = dict(oneway=g1["all"], oneway_nb=g1["nb"], incr=gs - gp, base_prev=gp)
    for tr, te in DIRS:
        real[(line, "SEQ", tr)] = dict(oneway=oot(L, tr, te, vs, K)["all"])
    # réplicas
    for r in range(NREP):
        fakes = {v: permuta_cliente(L, v, rng) for v in vs}
        for j, v in enumerate(vs):
            prev = vs[:j]
            for tr, te in DIRS:
                g1 = oot(L, tr, te, [v], K, overrides={v: fakes[v]})
                gs = oot(L, tr, te, prev + [v], K, overrides={v: fakes[v]})["all"]
                rows.append(dict(line=line, var=v, rep=r, tr=tr, oneway=g1["all"], oneway_nb=g1["nb"],
                                 incr=gs - real[(line, v, tr)]["base_prev"]))
        for tr, te in DIRS:
            g = oot(L, tr, te, vs, K, overrides=fakes)
            rows.append(dict(line=line, var="SEQ", rep=r, tr=tr, oneway=g["all"], oneway_nb=g["nb"], incr=np.nan))
    print(line, "listo", round(time.time() - t0, 1), "s", flush=True)

nul = pd.DataFrame(rows)
nul.to_csv(f"{OUT}/I_t3_nulo.csv", index=False)


def pval(null, obs):
    return (1 + np.sum(null >= obs - 1e-15)) / (1 + len(null))


res = {}
for line, vs in VARS.items():
    for v in vs + ["SEQ"]:
        s = nul[(nul.line == line) & (nul["var"] == v)]
        a = s[s.tr == 2023].set_index("rep")
        b = s[s.tr == 2024].set_index("rep")
        o23, o24 = real[(line, v, 2023)], real[(line, v, 2024)]
        out = {}
        for stat in (["oneway", "incr"] if v != "SEQ" else ["oneway"]):
            n23, n24 = a[stat].values, b[stat].values
            nmin = np.minimum(n23, n24)
            omin = min(o23[stat], o24[stat])
            out[stat] = dict(obs_23a24=round(o23[stat], 6), obs_24a23=round(o24[stat], 6), obs_min=round(omin, 6),
                             p_23a24=round(pval(n23, o23[stat]), 4), p_24a23=round(pval(n24, o24[stat]), 4),
                             p_min=round(pval(nmin, omin), 4),
                             nulo_min_p50=round(float(np.quantile(nmin, .5)), 6),
                             nulo_min_p95=round(float(np.quantile(nmin, .95)), 6),
                             nulo_min_p99=round(float(np.quantile(nmin, .99)), 6),
                             nulo_max_min=round(float(nmin.max()), 6),
                             nulo_23a24_p95=round(float(np.quantile(n23, .95)), 6),
                             nulo_media_23a24=round(float(n23.mean()), 6))
        res[f"{line}|{v}"] = out
print(json.dumps(res, indent=1))
json.dump(dict(NREP=NREP, K=K, resultados=res), open(f"{OUT}/I_t3_nulo.json", "w"), indent=1)
