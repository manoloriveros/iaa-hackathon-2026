"""Extra: (a) factores estimados con frecuencia (conteos) en vez de prima pura Tweedie; (b) segmento de marketing
descompuesto en edad (4 niveles) y poder adquisitivo (3 niveles). Ganancia fuera de tiempo (K=300) y nulo por
permutación entre clientes (1000 réplicas) para cada variante una a una."""
import sys, json, time
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
K = 300
OUT = "/home/claude/m017/revision"
df = cargar()
df["seg_edad"] = df.marketing_segment.str.split("_").str[0]
df["seg_poder"] = df.marketing_segment.str.split("_").str[1]
CAND = {"motor": ["gender", "previous_insurer", "occ"],
        "contents": ["gender", "works_from_home", "marketing_segment", "seg_edad", "seg_poder"]}
DIRS = ((2023, 2024), (2024, 2023))
rng = np.random.default_rng(777)
res = {}
for line, vs in CAND.items():
    L = Linea(df, line, extra_vars=[v for v in vs if v not in VARS[line]])
    for v in vs:
        for modo in ("tw", "frec"):
            obs = [oot(L, tr, te, [v], K, modo=modo)["all"] for tr, te in DIRS]
            nul = np.array([[oot(L, tr, te, [v], K, modo=modo, overrides={v: fk})["all"] for tr, te in DIRS]
                            for fk in (permuta_cliente(L, v, rng) for _ in range(NREP))])
            mn = nul.min(axis=1)
            res[f"{line}|{v}|{modo}"] = dict(obs_23a24=round(obs[0], 6), obs_24a23=round(obs[1], 6),
                                             p_min=round((1 + np.sum(mn >= min(obs))) / (1 + NREP), 4),
                                             nulo_min_p95=round(float(np.quantile(mn, .95)), 6))
            print(line, v, modo, {k: (round(x * 1e4, 1) if "obs" in k or "nulo" in k else x) for k, x in res[f"{line}|{v}|{modo}"].items()}, flush=True)

# paquetes candidatos (secuenciales), ganancia real por dirección y todo / NB / REN
PAQ = {"motor": {"A_gender_tw": ([("gender", "tw")]), "B_gender_frec": ([("gender", "frec")]),
                 "C_gender_frec+occ_frec": ([("gender", "frec"), ("occ", "frec")]),
                 "autor_gender+prev+occ_tw": ([("gender", "tw"), ("previous_insurer", "tw"), ("occ", "tw")])},
       "contents": {"A_gender+wfh_tw": ([("gender", "tw"), ("works_from_home", "tw")]),
                    "autor_gender+wfh+seg_tw": ([("gender", "tw"), ("works_from_home", "tw"), ("marketing_segment", "tw")]),
                    "C_gender+wfh+poder_tw": ([("gender", "tw"), ("works_from_home", "tw"), ("seg_poder", "tw")])}}


def oot_mixto(L, tr, te, paso, K):
    """Secuencial con modo por variable."""
    A, B = L.yr[tr], L.yr[te]
    wa, wb = np.ones(len(A["y"])), np.ones(len(B["y"]))
    m_tr = nivel(A["y"], A["m"], A["cell"], wa)
    m_te = B["m"].copy()
    from I_lib import _gains_base, _gains, ajusta_frec
    base = _gains_base(B, nivel(B["y"], B["m"], B["cell"], wb), wb)
    for v, modo in paso:
        ca, cb = L.code(v, tr), L.code(v, te)
        nl = len(L.levels[v])
        f = ajusta(A["y"], m_tr, ca, nl, K, wa) if modo == "tw" else ajusta_frec(A["nc"], m_tr, ca, nl, K, wa)
        m_tr = nivel(A["y"], m_tr * f[ca], A["cell"], wa)
        m_te = m_te * f[cb]
    return _gains(B, nivel(B["y"], m_te, B["cell"], wb), wb, base)


paq = {}
for line, P in PAQ.items():
    L = Linea(df, line, extra_vars=[v for v in CAND[line] if v not in VARS[line]])
    for nm, paso in P.items():
        for tr, te in DIRS:
            for KK in (150, 300, 600):
                g = oot_mixto(L, tr, te, paso, KK)
                paq[f"{line}|{nm}|K{KK}|{tr}->{te}"] = {k: round(g[k], 6) for k in ("all", "nb", "ren")}
pq = pd.DataFrame(paq).T * 1e4
print(pq.round(1).to_string())
json.dump(dict(NREP=NREP, K=K, una_a_una=res, paquetes=paq), open(f"{OUT}/I_t8_alternativas.json", "w"), indent=1)
