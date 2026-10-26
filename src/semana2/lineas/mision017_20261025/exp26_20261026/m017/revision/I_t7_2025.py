"""Tarea 7: efecto esperado en el test 2025 (filas reales de 2025: composición NB/REN, exposición y base).
Base 2025 = F2_ncb_previos_2025.csv (predicción previa a F3, leída como dato). Factores aplicados f = ajuste agrupado
2023+2024 (K = 300, secuencial, nivelado por celda × año). Verdad t por escenarios. Para cada fila, con E[y] = m·t:
  E[d(y,a)] - E[d(y,b)] = 4 m t (1/√a - 1/√b) + 4 (√a - √b)          (exacto; E√y se cancela)
  Var de la diferencia realizada = 16 (1/√a - 1/√b)² · Var(y),  Var(y) = m t · E[S²]/E[S] (Poisson compuesta)
  Desviación nula esperada: Σ 4 E[y]/√ȳ + 4 √ȳ - 8 E√y, con E√y por Poisson compuesta y severidades empíricas.
Se valida la desviación nula aproximada contra la real de 2024."""
import sys, json
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from scipy.stats import norm
from I_lib import *
from I_lib import _as_str, _occ_clean

OUT = "/home/claude/m017/revision"
K = 300
df = cargar()
rng = np.random.default_rng(2025)

# ------------------------------------------------ filas 2025
b = pd.read_parquet(f"{R}/base_etiquetas.parquet")
t25 = b[b.year == 2025].copy()
p25 = pd.read_csv(f"{R}/F2_ncb_previos_2025.csv").set_index("row_id").prediction
t25["m"] = p25.reindex(t25.row_id).values
assert t25.m.notna().all()
cu = pd.read_parquet(f"{DE}/customers.parquet").set_index("customer_id")
cc = cu.reindex(t25.customer_id.values)
for v in ["gender", "previous_insurer", "marketing_segment"]:
    t25[v] = _as_str(cc[v])
t25["occ"] = _occ_clean(cc["occupation"])
wf = pd.read_parquet(f"{DE}/test_contents.parquet", columns=["row_id", "works_from_home"]).set_index("row_id").works_from_home
t25["works_from_home"] = _as_str(wf.reindex(t25.row_id))

# ------------------------------------------------ severidades empíricas por línea
cl = pd.read_parquet(f"{DE}/claims.parquet")
cl = cl[cl.status != "repudiated"]
cl = cl.assign(neto=cl.incurred_to_date - cl.recoveries)
cl = cl[cl.neto > 0]
SEV = {l: g.neto.values for l, g in cl.groupby("line")}


def esqrt_y(lam, S, nsim=20000):
    """E√y para Poisson compuesta con media de conteo lam (vector) y severidades S (empíricas)."""
    s = rng.choice(S, size=(nsim, 4))
    e = [np.sqrt(s[:, :k].sum(1)).mean() for k in range(1, 5)]
    pk = [np.exp(-lam) * lam ** k / np.prod(range(1, k + 1)) for k in range(1, 5)]
    return sum(p * x for p, x in zip(pk, e))


def null_dev(mu, S):
    ES = S.mean()
    ybar = mu.mean()
    return np.sum(4 * mu / np.sqrt(ybar) + 4 * np.sqrt(ybar) - 8 * esqrt_y(mu / ES, S))


# validación de la desviación nula aproximada en 2024 (μ = m nivelado por celda)
val = {}
for l in ("motor", "contents", "buildings"):
    s = df[(df.line == l) & (df.year == 2024)]
    cell = s.new_business.values.astype(int)
    ml = nivel(s.y.values, s.m.values, cell, np.ones(len(s)))
    real = np.sum(dev(s.y.values, np.full(len(s), s.y.mean())))
    val[l] = dict(nula_real=float(real), nula_aprox=float(null_dev(ml, SEV[l])))
print("validación nula 2024 (aprox/real)", {k: round(v["nula_aprox"] / v["nula_real"], 3) for k, v in val.items()}, flush=True)


# ------------------------------------------------ ajuste agrupado 2023+2024
def ajuste_agrupado(d, seq, Kc, w=None):
    """Factores secuenciales sobre 2023+2024 agrupados; nivelación por celda × año. Devuelve {var: {valor: f}}."""
    y, m = d.y.values, d.m.values
    cy = (d.new_business.values.astype(int) * 2 + (d.year.values == 2024)).astype(int)
    w = np.ones(len(y)) if w is None else w
    ml = nivel(y, m, cy, w, C=4)
    out = {}
    for v in seq:
        cd, uni = pd.factorize(d[v])
        f = ajusta(y, ml, cd, len(uni), Kc, w) if Kc > 0 else _mle(y, ml, cd, len(uni), w)
        out[v] = dict(zip(uni, f))
        ml = nivel(y, ml * f[cd], cy, w, C=4)
    return out


def _mle(y, ml, cd, L, w):
    a = np.bincount(cd, w * y / np.sqrt(ml), L)
    bb = np.bincount(cd, w * np.sqrt(ml), L)
    return np.where(bb > 0, a / np.where(bb > 0, bb, 1), 1.0)


def producto(t, fac, seq, cell):
    f = np.ones(len(t))
    for v in seq:
        f *= t[v].map(fac[v]).fillna(1.0).values
    # restituye Σm por celda (la nivelación 2025 la fija el resto del modelo)
    m = t.m.values
    for c in (0, 1):
        i = cell == c
        f[i] *= m[i].sum() / (m[i] * f[i]).sum()
    return f


def esperado(t, f, g, S, nd):
    """Ganancia esperada de D² y su desviación típica de evaluación (por celda y total)."""
    m = t.m.values
    a, bnew = m, m * f
    mu = m * g
    dE = 4 * mu * (1 / np.sqrt(a) - 1 / np.sqrt(bnew)) + 4 * (np.sqrt(a) - np.sqrt(bnew))
    var = 16 * (1 / np.sqrt(a) - 1 / np.sqrt(bnew)) ** 2 * mu * (S ** 2).mean() / S.mean()
    nb = t.new_business.values
    r = {"all": (dE.sum() / nd["all"], np.sqrt(var.sum()) / nd["all"])}
    for k, i in (("nb", nb), ("ren", ~nb)):
        r[k] = (dE[i].sum() / nd[k], np.sqrt(var[i].sum()) / nd[k])
    return r


PAQ = {"motor": {"autor (gender+prev+occ)": ["gender", "previous_insurer", "occ"], "gender": ["gender"],
                 "gender+prev": ["gender", "previous_insurer"]},
       "contents": {"autor (gender+wfh+seg)": ["gender", "works_from_home", "marketing_segment"],
                    "gender+wfh": ["gender", "works_from_home"], "wfh+seg": ["works_from_home", "marketing_segment"],
                    "gender": ["gender"]}}
RUIDO = {"previous_insurer", "occ"}
NBOOT = int(sys.argv[1]) if len(sys.argv) > 1 else 400
allc = pd.Index(pd.unique(df.customer_id))
res = {"validacion_nula_2024": val}
for l, P in PAQ.items():
    d = df[df.line == l].reset_index(drop=True)
    t = t25[t25.line == l].reset_index(drop=True)
    cell = t.new_business.values.astype(int)
    S = SEV[l]
    nd = {"all": null_dev(t.m.values, S), "nb": null_dev(t.m.values[cell == 1], S), "ren": null_dev(t.m.values[cell == 0], S)}
    cmap = allc.get_indexer(pd.unique(d.customer_id))
    ccode = pd.Index(pd.unique(d.customer_id)).get_indexer(d.customer_id)
    for nm, seq in P.items():
        fac = ajuste_agrupado(d, seq, K)
        f = producto(t, fac, seq, cell)
        mle = ajuste_agrupado(d, seq, 0)
        r = {"factores_K300": {v: {k: round(float(x), 4) for k, x in fac[v].items()} for v in seq if len(fac[v]) <= 12}}
        # escenarios de verdad
        esc = {"T0_verdad=EMV_agrupado": producto(t, mle, seq, cell)}
        mle1 = {v: (mle[v] if v not in RUIDO else {k: 1.0 for k in mle[v]}) for v in seq}
        esc["T1_ruido(prev,occ)=1"] = producto(t, mle1, seq, cell)
        g2 = esc["T1_ruido(prev,occ)=1"].copy()
        g2[cell == 1] = 1.0
        esc["T2_sin_efecto_en_NB"] = g2
        esc["T3_verdad=f_aplicado"] = f
        r["escenarios"] = {}
        for en, g in esc.items():
            e = esperado(t, f, g, S, nd)
            r["escenarios"][en] = {k: dict(gan=round(float(x[0]), 6), sd_eval=round(float(x[1]), 6)) for k, x in e.items()}
        # bootstrap de la verdad: estimación creíble K=300 en remuestreo por cliente (la ganancia es lineal en t, así
        # que su media equivale a evaluar en la media posterior); variables ruido: K=300 (tal cual) o 1 (pesimista)
        for modo in ("K300_boot", "ruido=1"):
            gs, ps = [], []
            for _ in range(NBOOT):
                cnt = np.bincount(rng.integers(0, len(cmap), len(cmap)), minlength=len(cmap)).astype(float)
                w = cnt[ccode]
                mb = ajuste_agrupado(d, seq, K, w=w)
                if modo == "ruido=1":
                    mb = {v: (mb[v] if v not in RUIDO else {k: 1.0 for k in mb[v]}) for v in seq}
                g = producto(t, mb, seq, cell)
                e = esperado(t, f, g, S, nd)["all"]
                gs.append(e[0])
                ps.append(norm.cdf(-e[0] / e[1]))
            gs = np.array(gs)
            r[f"boot_verdad_{modo}"] = dict(gan_media=round(float(gs.mean()), 6), p05=round(float(np.quantile(gs, .05)), 6),
                                            p95=round(float(np.quantile(gs, .95)), 6), P_empeora=round(float(np.mean(ps)), 4))
        res[f"{l}|{nm}"] = r
        print(l, nm)
        for en, x in r["escenarios"].items():
            print(f"   {en:26s}", {k: f"{v['gan'] * 1e4:.1f}±{v['sd_eval'] * 1e4:.1f}" for k, v in x.items()})
        for modo in ("K300_boot", "ruido=1"):
            x = r[f"boot_verdad_{modo}"]
            print(f"   boot {modo:16s} media {x['gan_media'] * 1e4:.1f} [{x['p05'] * 1e4:.1f},{x['p95'] * 1e4:.1f}] P(empeora) {x['P_empeora']:.3f}", flush=True)

# conversión a D² agregado de las 3 líneas (nulo con media global)
mu_all = t25.m.values
ybar = mu_all.mean()
nd_tot = 0.0
for l in ("motor", "contents", "buildings"):
    mm = t25.m.values[t25.line.values == l]
    nd_tot += np.sum(4 * mm / np.sqrt(ybar) + 4 * np.sqrt(ybar) - 8 * esqrt_y(mm / SEV[l].mean(), SEV[l]))
conv = {}
for l in ("motor", "contents"):
    t = t25[t25.line == l]
    conv[l] = float(null_dev(t.m.values, SEV[l]) / nd_tot)
res["factor_conversion_D2_linea_a_D2_total"] = conv
print("conversión D² línea -> D² total 3 líneas", {k: round(v, 3) for k, v in conv.items()})
json.dump(res, open(f"{OUT}/I_t7_2025.json", "w"), indent=1)
