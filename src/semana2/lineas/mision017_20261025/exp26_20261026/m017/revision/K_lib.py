"""Auditor K: implementación propia (no ejecuta código del autor). Utilidades comunes para auditar F4.
Métrica Tweedie 1,5: d(y,m) = 4y/sqrt(m) + 4 sqrt(m) - 8 sqrt(y)."""
import numpy as np, pandas as pd, json, hashlib, warnings
warnings.filterwarnings("ignore")
R = "/home/claude/m017"; T = "/home/claude/ml2/trabajo"; DE = R + "/datos/emerging"; OUT = R + "/revision"
LINES = ["motor", "buildings", "contents"]
CELS = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
K_F = 300.0; K_P = 100.0


def dev(y, m):
    return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)


def kopt(y, m):
    return float(np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m)))


LAB = pd.read_parquet(R + "/base_etiquetas.parquet").set_index("row_id")
LAB["new_business"] = LAB.new_business.astype(bool)


def celda(t):
    return (t.line.astype(str) + "_" + t.new_business.astype(int).astype(str)).values


# ------------------------------------------------------------------ conjuntos base (OOF de 2023 y 2024)
def load_oof(conj, mod):
    d = pd.concat([pd.read_parquet(f"{R}/oof/pred/{conj}/{mod}_{l}.parquet") for l in LINES]).set_index("row_id")
    t = LAB.loc[d.index].copy(); t["m"] = d.mu.values * t.c_fila.values
    return t


def base_sets(extra=()):
    S = {"DEV23_T2b": load_oof("dev", "T2b"), "HOLD24_T2b": load_oof("hold", "T2b")}
    p24 = pd.read_parquet(R + "/in/predicciones_2024.parquet").set_index("row_id")
    a1 = LAB.loc[p24.index].copy(); a1["m"] = p24.A1.values; S["HOLD24_A1"] = a1
    h = S["HOLD24_T2b"].copy(); a = a1.m.reindex(h.index)
    tot = h.groupby("line").m.transform("sum") / a.groupby(h.line).transform("sum")
    h["m"] = 0.5 * h.m + 0.5 * a * tot; S["HOLD24_mezcla"] = h
    for mod in extra:
        S["DEV23_" + mod] = load_oof("dev", mod); S["HOLD24_" + mod] = load_oof("hold", mod)
    return S


# ------------------------------------------------------------------ variables de clave
_cu = pd.read_parquet(DE + "/customers.parquet").set_index("customer_id")
_pol = pd.concat([pd.concat([pd.read_parquet(f"{DE}/policies_{l}.parquet"), pd.read_parquet(f"{DE}/test_{l}.parquet")])
                  for l in LINES], ignore_index=True).set_index("row_id")


def key_ncb(t):
    v = _pol.ncb_years.reindex(t.index).fillna(0).values
    b = pd.cut(v, [-1, 0, 2, 5, 9, 99], labels=["0", "1-2", "3-5", "6-9", "10+"]).astype(str)
    return np.where(t.line.values == "motor", b, "x")


def key_prior(t):
    return np.minimum(_cu.prior_claims_5y.reindex(t.customer_id.values).fillna(0).values, 2).astype(int).astype(str)


def key_var(t, v):
    if v in _cu.columns:
        return _cu[v].reindex(t.customer_id.values).astype(str).values
    return _pol[v].reindex(t.index).astype(str).values


# ------------------------------------------------------------------ pasos de F2
def keep_cell_sum(t, m_new, m_old):
    c = celda(t); out = m_new.copy()
    for cc in np.unique(c):
        i = c == cc; out[i] *= m_old[i].sum() / out[i].sum()
    return out


def fac_ae(t, m, key, k=K_F):
    """factor A/E por celda × nivel, credibilidad aditiva 1 + z(ae-1), z = positivos/(positivos+k)"""
    c = celda(t); y = t.y.values; f = {}
    for cc in np.unique(c):
        i = c == cc; base = y[i].sum() / m[i].sum()
        for v in np.unique(key[i]):
            j = i & (key == v); n = (y[j] > 0).sum(); ae = y[j].sum() / m[j].sum() / base
            f[(cc, v)] = 1 + n / (n + k) * (ae - 1)
    return f


def apply_ae(t, m, key, f):
    c = celda(t)
    return keep_cell_sum(t, m * np.array([f.get((a, v), 1.0) for a, v in zip(c, key)]), m)


def forma(t, m, acel):
    """potencia a de la tasa relativa dentro de la celda (exposición × c_fila), Σμ fijo"""
    c = celda(t); out = m.copy()
    for cc, a in acel.items():
        i = c == cc
        if not i.any(): continue
        e = t.exposure.values[i] * t.c_fila.values[i]; r = m[i] / e; gm = m[i].sum() / e.sum()
        mm = e * gm * (r / gm) ** a; out[i] = mm * m[i].sum() / mm.sum()
    return out


def f2_fit(t):
    kn, kp = key_ncb(t), key_prior(t)
    f1 = fac_ae(t, t.m.values, kn); m1 = apply_ae(t, t.m.values, kn, f1); f2 = fac_ae(t, m1, kp)
    return f1, f2


def f2_apply(t, f1, f2, m=None):
    m = t.m.values if m is None else m
    m1 = apply_ae(t, m, key_ncb(t), f1); m2 = apply_ae(t, m1, key_prior(t), f2)
    return forma(t, m2, {"motor_0": 0.9})


# ------------------------------------------------------------------ factores residuales (Tweedie, log-credibilidad)
SEQ = [("gender", ["motor", "contents"]), ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]


def nivel_celda(t, m):
    c = celda(t); out = m.copy(); y = t.y.values
    for cc in np.unique(c):
        i = c == cc; out[i] *= kopt(y[i], m[i])
    return out


def fac_tw(t, m, key, lines, k=K_F):
    rel = nivel_celda(t, m); y = t.y.values; f = {}
    for l in lines:
        il = t.line.values == l
        for v in np.unique(key[il]):
            j = il & (key == v); n = (y[j] > 0).sum()
            if n == 0: continue
            kv = np.sum(y[j] / np.sqrt(rel[j])) / np.sum(np.sqrt(rel[j]))
            f[(l, v)] = float(np.exp(n / (n + k) * np.log(max(kv, 1e-3))))
    return f


def apply_tw(t, m, key, f):
    return keep_cell_sum(t, m * np.array([f.get((l, v), 1.0) for l, v in zip(t.line.values, key)]), m)


def fit_factors(t, m, seq=SEQ, k=K_F):
    FAC = []; mm = m.copy()
    for v, lines in seq:
        key = key_var(t, v); f = fac_tw(t, mm, key, lines, k); mm = apply_tw(t, mm, key, f); FAC.append((v, f))
    return FAC


def apply_factors(t, m, FAC):
    for v, f in FAC: m = apply_tw(t, m, key_var(t, v), f)
    return m


# ------------------------------------------------------------------ FSp: κ por peligro y predicción
def fsp_tables(suffix=""):
    out = {}
    for l in LINES:
        f = pd.read_parquet(f"{T}/pred/fsp/{l}{suffix}.parquet").set_index("row_id")
        per = [c[2:] for c in f.columns if c.startswith("f_")]
        cn = pd.read_parquet(f"{T}/conteos_emerging_{l}.parquet").set_index("row_id")
        be = pd.read_parquet(f"{T}/base_emerging_{l}.parquet", columns=["row_id", "y", "year", "conjunto", "customer_id"] + [f"y_{p}" for p in per]).set_index("row_id")
        out[l] = dict(f=f, per=per, cn=cn, be=be)
    return out


def kappa(FT, l, years, kp=K_P, idx=None, detail=False):
    D = FT[l]; f, per, cn, be = D["f"], D["per"], D["cn"], D["be"]
    tr = be[(be.conjunto == "train") & be.year.astype(int).isin(years)].index if idx is None else idx
    ef = {p: f.loc[tr, f"f_{p}"].values * f.loc[tr, f"cp_{p}"].values for p in per}
    es = {p: f.loc[tr, f"s_{p}"].values for p in per}
    kg = be.loc[tr, "y"].values.sum() / sum((ef[p] * es[p]).sum() for p in per)
    kap = {}; det = {}
    for p in per:
        n = cn.loc[tr, f"n_{p}"].values.astype(float); N = n.sum()
        kf = N / ef[p].sum(); ks = be.loc[tr, f"y_{p}"].values.sum() / max((n * es[p]).sum(), 1e-9)
        raw = kf * ks / kg; z = N / (N + kp); kap[p] = float(np.exp(z * np.log(max(raw, 1e-3))))
        det[p] = dict(N=N, kf=kf, ks=ks, raw=raw, z=z, kap=kap[p],
                      cost_direct=be.loc[tr, f"y_{p}"].values.sum() / (ef[p] * es[p]).sum() / kg)
    return (kap, det) if detail else kap


def fsp_pred(FT, idx, l, kap, ultimate=False):
    D = FT[l]; f = D["f"].loc[idx]
    return sum(kap[p] * f[f"f_{p}"].values * (1.0 if ultimate else f[f"cp_{p}"].values) * f[f"s_{p}"].values for p in D["per"])


def blend(FT, t, m, w, kap_by_line, ultimate=False, alt=None):
    """mezcla geométrica por ramo con la FSp (o con alt[l]: vector alternativo), total de ramo y luego de celda conservado"""
    out = m.copy()
    for l in LINES:
        i = (t.line == l).values
        if w[l] == 0 or not i.any(): continue
        r = alt[l](t.index[i]) if alt is not None else fsp_pred(FT, t.index[i], l, kap_by_line[l], ultimate)
        r = r * m[i].sum() / r.sum()
        out[i] = np.exp((1 - w[l]) * np.log(m[i]) + w[l] * np.log(r))
    return keep_cell_sum(t, out, m)


# ------------------------------------------------------------------ D² con nivel óptimo por celda (por sumas)
def banda(e):
    return np.where(e < 0.5, "c", np.where(e < 0.9, "m", "l"))


_te25 = LAB[LAB.conjunto == "test"]
_k25 = pd.Series(_te25.line + "_" + _te25.new_business.astype(int).astype(str) + "_" + banda(_te25.exposure.values)).value_counts(normalize=True)


def pesos25(t):
    k = pd.Series(t.line + "_" + t.new_business.astype(int).astype(str) + "_" + banda(t.exposure.values), index=t.index)
    n = k.value_counts(normalize=True)
    return k.map(_k25 / n).fillna(0).values


def d2_lev(t, m, mask=None, w=None):
    """D² con escalar Tweedie-óptimo (no ponderado) por celda; desviación (y nulo) ponderados con w si se da"""
    mask = np.ones(len(t), bool) if mask is None else mask
    y = t.y.values[mask]; mm = m[mask]; c = celda(t)[mask]; ww = np.ones(len(y)) if w is None else w[mask]
    num = 0.0
    for cc in np.unique(c):
        i = c == cc; k = kopt(y[i], mm[i]); num += np.sum(ww[i] * dev(y[i], k * mm[i]))
    mu0 = np.sum(ww * y) / np.sum(ww)
    return 1 - num / np.sum(ww * dev(y, np.full(len(y), mu0)))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def jdump(obj, p):
    json.dump(obj, open(p, "w"), indent=1, ensure_ascii=False, default=float)
