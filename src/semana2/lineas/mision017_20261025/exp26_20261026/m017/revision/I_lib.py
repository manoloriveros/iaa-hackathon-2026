"""Biblioteca propia del revisor I (factores residuales género / aseguradora previa / ocupación /
works_from_home / segmento de marketing). Código independiente: no importa ni ejecuta scripts del autor.
Datos sintéticos: todo se queda en esta máquina."""
import numpy as np, pandas as pd

R = "/home/claude/m017"
DE = f"{R}/datos/emerging"
LINES = ("motor", "contents", "buildings")
VARS = {"motor": ["gender", "previous_insurer", "occ"],
        "contents": ["gender", "works_from_home", "marketing_segment"]}
CUST_VARS = ["gender", "previous_insurer", "occ", "marketing_segment"]


# ---------------------------------------------------------------- métrica Tweedie p = 1,5
def dev(y, m):
    return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)


def d2(y, m, w):
    """D² Tweedie 1,5 ponderado; nulo = media (ponderada) constante de y."""
    ybar = np.sum(w * y) / np.sum(w)
    return 1 - np.sum(w * dev(y, m)) / np.sum(w * dev(y, np.full(len(y), ybar)))


def nivel(y, m, cell, w, C=2):
    """Lleva m al escalar Tweedie-óptimo de su celda: k = Σ w y/√m / Σ w √m."""
    a = np.bincount(cell, w * y / np.sqrt(m), C)
    b = np.bincount(cell, w * np.sqrt(m), C)
    k = np.where(b > 0, a / np.where(b > 0, b, 1), 1.0)
    return m * k[cell]


# ---------------------------------------------------------------- datos
def _occ_clean(s):
    out = np.full(len(s), "NA", dtype=object)
    ok = s.notna().values
    out[ok] = (s[ok].astype(object).map(lambda x: str(x)).str.lower().str.strip()
               .str.replace("self-employed ", "", regex=False).str.strip().values)
    return out


def _as_str(s):
    """Convierte a str con NaN explícito -> 'NA' (astype(str) deja NaN como float en esta versión)."""
    out = np.full(len(s), "NA", dtype=object)
    ok = pd.notna(s.values)
    out[ok] = [str(x) for x in s.values[ok]]
    return out


def cargar():
    """Filas de entrenamiento 2023/2024 de las tres líneas con y, c_fila, mu (T2b fuera de muestra),
    m = mu × c_fila, conteo de siniestros, severidad y variables candidatas."""
    b = pd.read_parquet(f"{R}/base_etiquetas.parquet")
    tr = b[b.conjunto == "train"].copy()
    parts = []
    for conj, yr in (("dev", 2023), ("hold", 2024)):
        for l in LINES:
            p = pd.read_parquet(f"{R}/oof/pred/{conj}/T2b_{l}.parquet")
            p["yr_pred"] = yr
            parts.append(p)
    mu = pd.concat(parts).set_index("row_id")
    tr = tr.join(mu, on="row_id")
    assert tr.mu.notna().all() and (tr.yr_pred == tr.year).all()
    tr["m"] = tr.mu * tr.c_fila
    pol = pd.concat([pd.read_parquet(f"{DE}/policies_{l}.parquet",
                                     columns=["row_id", "policy_id", "address_id", "period_start", "period_end"])
                     for l in LINES], ignore_index=True)
    wfh = pd.read_parquet(f"{DE}/policies_contents.parquet", columns=["row_id", "works_from_home"])
    tr = tr.merge(pol, on="row_id", how="left").merge(wfh, on="row_id", how="left")
    cu = pd.read_parquet(f"{DE}/customers.parquet").set_index("customer_id")
    assert cu.index.is_unique
    cc = cu.reindex(tr.customer_id.values)
    for v in ["gender", "previous_insurer", "marketing_segment"]:
        tr[v] = _as_str(cc[v])
    tr["occ"] = _occ_clean(cc["occupation"])
    tr["prior_claims_5y"] = cc["prior_claims_5y"].values
    tr["customer_since_year"] = cc["customer_since_year"].values
    tr["works_from_home"] = _as_str(tr["works_from_home"])
    # siniestros: aceptados (no repudiados), neto = incurrido - recobros, ocurridos dentro del periodo
    c = pd.read_parquet(f"{DE}/claims.parquet")
    c = c[c.status != "repudiated"].copy()
    c["neto"] = c.incurred_to_date - c.recoveries
    c["loss_date"] = pd.to_datetime(c.loss_date)
    mm = c.merge(tr[["row_id", "policy_id", "period_start", "period_end"]], on="policy_id")
    mm = mm[(mm.loss_date >= pd.to_datetime(mm.period_start)) & (mm.loss_date <= pd.to_datetime(mm.period_end))]
    g = mm.groupby("row_id")
    tr["y_chk"] = tr.row_id.map(g.neto.sum()).fillna(0.0)
    tr["nclaims"] = tr.row_id.map(mm[mm.neto > 0].groupby("row_id").size()).fillna(0).astype(int)
    assert np.allclose(tr.y_chk, tr.y, atol=1e-6), "no reproduzco y"
    return tr.reset_index(drop=True)


class Linea:
    """Arreglos numpy por línea y año para cálculos vectorizados con bincount."""

    def __init__(self, df, line, extra_vars=()):
        d = df[df.line == line].reset_index(drop=True)
        self.line = line
        self.df = d
        self.cust_codes, self.cust_uni = pd.factorize(d.customer_id)
        self.vars = list(VARS.get(line, [])) + list(extra_vars)
        self.codes, self.levels = {}, {}
        for v in set(self.vars) | set(CUST_VARS) | {"works_from_home"}:
            if v not in d:
                continue
            cd, uni = pd.factorize(d[v])
            self.codes[v], self.levels[v] = cd, np.asarray(uni)
        self.yr = {}
        for yr in (2023, 2024):
            i = (d.year == yr).values
            self.yr[yr] = dict(idx=np.where(i)[0], y=d.y.values[i], m=d.m.values[i],
                               cell=d.new_business.values[i].astype(int), cust=self.cust_codes[i],
                               expo=d.exposure.values[i], nc=d.nclaims.values[i].astype(float))

    def code(self, v, yr, override=None):
        cd = self.codes[v] if override is None else override
        return cd[self.yr[yr]["idx"]]


def ajusta(y, m_lev, code, L, K, w):
    """Factor Tweedie-óptimo por nivel relativo a la base nivelada; credibilidad log con Z = n/(n+K)."""
    a = np.bincount(code, w * y / np.sqrt(m_lev), L)
    b = np.bincount(code, w * np.sqrt(m_lev), L)
    n = np.bincount(code, w * (y > 0), L)
    k = np.where(b > 0, a / np.where(b > 0, b, 1), 1.0)
    z = n / (n + K)
    f = np.exp(z * np.log(np.maximum(k, 1e-3)))
    f[n == 0] = 1.0
    return f


def ajusta_frec(nc, m_lev, code, L, K, w):
    """Variante de frecuencia: factor = (Σ siniestros / Σ siniestros esperados) por nivel, esperados ∝ m nivelado
    (supone severidad igual entre niveles); credibilidad log con Z = n/(n+K), n = siniestros."""
    e = m_lev * np.sum(w * nc) / np.sum(w * m_lev)
    a = np.bincount(code, w * nc, L)
    b = np.bincount(code, w * e, L)
    k = np.where(b > 0, a / np.where(b > 0, b, 1), 1.0)
    z = a / (a + K)
    f = np.exp(z * np.log(np.maximum(k, 1e-3)))
    f[a == 0] = 1.0
    return f


def oot(L, tr, te, seq, K=300, w=None, overrides=None, steps=False, wx=None, modo="tw"):
    """Ganancia fuera de tiempo: factores estimados en `tr` (secuencial según `seq`), aplicados a `te`.
    w: pesos por cliente (bootstrap) o None. overrides: {var: códigos alternativos (nulo)}.
    wx: pesos extra por fila del año de prueba (p. ej. composición 2025), solo en la evaluación.
    Devuelve ganancias de D² (todo / NB / REN) frente a la base nivelada por celda."""
    A, B = L.yr[tr], L.yr[te]
    wa = np.ones(len(A["y"])) if w is None else w[A["cust"]]
    wb = np.ones(len(B["y"])) if w is None else w[B["cust"]]
    if wx is not None:
        wb = wb * wx
    m_tr = nivel(A["y"], A["m"], A["cell"], wa)
    m_te0 = nivel(B["y"], B["m"], B["cell"], wb)
    m_te = B["m"].copy()
    base = _gains_base(B, m_te0, wb)
    out = []
    for v in seq:
        ov = None if overrides is None else overrides.get(v)
        ca, cb = L.code(v, tr, ov), L.code(v, te, ov)
        nl = len(L.levels[v])
        f = ajusta(A["y"], m_tr, ca, nl, K, wa) if modo == "tw" else ajusta_frec(A["nc"], m_tr, ca, nl, K, wa)
        m_tr = nivel(A["y"], m_tr * f[ca], A["cell"], wa)
        m_te = m_te * f[cb]
        if steps or v == seq[-1]:
            mt = nivel(B["y"], m_te, B["cell"], wb)
            out.append(_gains(B, mt, wb, base))
    return out if steps else out[-1]


def _gains_base(B, m0, w):
    nb = B["cell"] == 1
    return {"all": d2(B["y"], m0, w), "nb": d2(B["y"][nb], m0[nb], w[nb]), "ren": d2(B["y"][~nb], m0[~nb], w[~nb]),
            "dev_all": np.sum(w * dev(B["y"], m0))}


def _gains(B, m1, w, base):
    nb = B["cell"] == 1
    return {"all": d2(B["y"], m1, w) - base["all"],
            "nb": d2(B["y"][nb], m1[nb], w[nb]) - base["nb"],
            "ren": d2(B["y"][~nb], m1[~nb], w[~nb]) - base["ren"],
            "ddev": base["dev_all"] - np.sum(w * dev(B["y"], m1))}


def permuta_cliente(L, v, rng):
    """Variable falsa: permuta los valores de `v` entre clientes de la línea; cada cliente conserva
    un único valor en ambos años. Mismo número de niveles y mismos tamaños (en clientes)."""
    cd = L.codes[v]
    ncu = len(L.cust_uni)
    # valor por cliente: el de su primera fila (las variables de cliente son constantes por construcción)
    first = np.full(ncu, -1)
    order = np.arange(len(cd))[::-1]
    first[L.cust_codes[order]] = cd[order]
    perm = first[rng.permutation(ncu)]
    return perm[L.cust_codes]
