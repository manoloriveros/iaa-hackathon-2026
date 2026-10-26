"""J (auditor independiente de F3): biblioteca propia. No importa ni ejecuta código del autor.
Reimplementa: desvianza Tweedie 1,5, escalar óptimo, celdas, series históricas (T2b 2023/2024, A1 2024, mezcla 2024),
factores de F2 (NCB y previos, A/E con credibilidad lineal), forma por exponente a, factores Tweedie con credibilidad en log."""
import numpy as np, pandas as pd, json, hashlib, os

R = "/home/claude/m017/"
DE = R + "datos/emerging/"
CELS = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]


def dev(y, m):
    m = np.asarray(m, float); y = np.asarray(y, float)
    return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(np.maximum(y, 0))


def kopt(y, m):
    return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


B = pd.read_parquet(R + "base_etiquetas.parquet").set_index("row_id")


def celda(t):
    return np.array([f"{l}_{int(n)}" for l, n in zip(t.line.values, t.new_business.values)], dtype=object)


def _serie(conj):
    d = pd.concat([pd.read_parquet(f"{R}oof/pred/{conj}/T2b_{l}.parquet") for l in ["motor", "buildings", "contents"]]).set_index("row_id")
    t = B.loc[d.index].copy(); t["m"] = d.mu.values * t.c_fila.values
    return t


def series():
    s = {"DEV23_T2b": _serie("dev"), "HOLD24_T2b": _serie("hold")}
    p24 = pd.read_parquet(R + "in/predicciones_2024.parquet").set_index("row_id")
    a1 = B.loc[p24.index].copy(); a1["m"] = p24.A1.values; s["HOLD24_A1"] = a1
    h = s["HOLD24_T2b"].copy(); a = a1.m.reindex(h.index)
    # mezcla: 50/50 de T2b y A1, A1 llevado al total de T2b por ramo
    fac_l = h.groupby("line").m.sum() / a.groupby(h.line).sum()
    h["m"] = 0.5 * h.m.values + 0.5 * a.values * h.line.map(fac_l).values
    s["HOLD24_mezcla"] = h
    return s


# ---------- variables ----------
_cu = pd.read_parquet(DE + "customers.parquet").set_index("customer_id")
_pol = pd.concat([pd.read_parquet(f"{DE}{k}_{l}.parquet") for k in ("policies", "test") for l in ("motor", "buildings", "contents")],
                 ignore_index=True).set_index("row_id")


def ncb_banda(t):
    v = _pol.ncb_years.reindex(t.index).fillna(0).values
    lab = np.select([v <= 0, v <= 2, v <= 5, v <= 9], ["0", "1-2", "3-5", "6-9"], "10+")
    return np.where(t.line.values == "motor", lab, "x").astype(object)


def previos(t):
    v = _cu.prior_claims_5y.reindex(t.customer_id.values).fillna(0).values
    return np.minimum(v, 2).astype(int).astype(str).astype(object)


def _txt(v):
    return np.array([str(x) for x in v], dtype=object)


def var(t, nombre):
    """texto explícito: con pandas 3 astype(str) deja NaN como NaN; aquí los faltantes son la cadena 'nan'"""
    if nombre == "occ":
        s = pd.Series(_txt(_cu.occupation.reindex(t.customer_id.values).values))
        return s.str.lower().str.replace("self-employed ", "", regex=False).str.strip().values.astype(object)
    if nombre in _cu.columns:
        return _txt(_cu[nombre].reindex(t.customer_id.values).values)
    return _txt(_pol[nombre].reindex(t.index).values)


# ---------- transformaciones ----------
def fac_ae(t, m, clave, k=300):
    """F2: por celda, A/E de suma relativo a la celda, credibilidad lineal n/(n+k) con n = siniestros > 0"""
    c = celda(t); y = t.y.values; f = {}
    for cc in np.unique(c):
        i = c == cc; base = y[i].sum() / m[i].sum()
        for v in np.unique(clave[i]):
            j = i & (clave == v); n = (y[j] > 0).sum()
            f[(cc, v)] = 1 + n / (n + k) * (y[j].sum() / m[j].sum() / base - 1)
    return f


def aplica_celda(t, m, f, clave):
    c = celda(t); out = m * np.array([f.get((a, v), 1.0) for a, v in zip(c, clave)])
    for cc in np.unique(c):
        i = c == cc; out[i] *= m[i].sum() / out[i].sum()
    return out


def forma(t, m, cel, a, c_fila=None):
    """m_i ∝ e_i·(m_i/e_i)^a dentro de la celda, Σm de la celda conservado (equivalente a e·gm·(r/gm)^a reescalado)"""
    c = celda(t); out = m.copy(); i = c == cel
    e = t.exposure.values[i] * (t.c_fila.values[i] if c_fila is None else c_fila)
    mm = e * (m[i] / e) ** a; out[i] = mm * m[i].sum() / mm.sum()
    return out


def nivel_opt_celda(t, m):
    c = celda(t); out = m.copy(); y = t.y.values
    for cc in np.unique(c):
        i = c == cc; out[i] *= kopt(y[i], m[i])
    return out


def fac_tw(t, m, clave, lineas, k=300):
    """factor Tweedie-óptimo por nivel de la variable dentro del ramo (NB y REN juntos), sobre m llevado al óptimo de su celda;
    credibilidad n/(n+k) en log"""
    mr = nivel_opt_celda(t, m); y = t.y.values; f = {}
    for l in lineas:
        il = t.line.values == l
        for v in np.unique(clave[il]):
            j = il & (clave == v); n = (y[j] > 0).sum()
            if n == 0: continue
            kv = np.sum(y[j] / np.sqrt(mr[j])) / np.sum(np.sqrt(mr[j]))
            f[(l, v)] = float(np.exp(n / (n + k) * np.log(max(kv, 1e-3))))
    return f


def aplica_ramo(t, m, f, clave):
    c = celda(t); out = m * np.array([f.get((l, v), 1.0) for l, v in zip(t.line.values, clave)])
    for cc in np.unique(c):
        i = c == cc; out[i] *= m[i].sum() / out[i].sum()
    return out


class TransfF2:
    def __init__(self, pool):
        kn = ncb_banda(pool); kp = previos(pool)
        self.f1 = fac_ae(pool, pool.m.values, kn)
        m1 = aplica_celda(pool, pool.m.values, self.f1, kn)
        self.f2 = fac_ae(pool, m1, kp)

    def __call__(self, t, m, c_fila=None):
        m = aplica_celda(t, m, self.f1, ncb_banda(t)); m = aplica_celda(t, m, self.f2, previos(t))
        return forma(t, m, "motor_0", 0.9, c_fila)


SEQ = [("gender", ["motor", "contents"]), ("previous_insurer", ["motor"]), ("occ", ["motor"]),
       ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]


class TransfF3:
    def __init__(self, pool, a_m1, seq=SEQ, k=300):
        self.f2 = TransfF2(pool); self.a = a_m1
        m = self.forma(pool, self.f2(pool, pool.m.values)); self.fac = []
        for v, lineas in seq:
            cl = var(pool, v); f = fac_tw(pool, m, cl, lineas, k); m = aplica_ramo(pool, m, f, cl); self.fac.append((v, f))

    def forma(self, t, m, c_fila=None):
        return forma(t, m, "motor_1", self.a, c_fila) if self.a != 1.0 else m

    def __call__(self, t, m, c_fila=None, con_factores=True):
        m = self.forma(t, self.f2(t, m, c_fila), c_fila)
        if con_factores:
            for v, f in self.fac: m = aplica_ramo(t, m, f, var(t, v))
        return m


def razon_local(ser, fn):
    """razón de escalar Tweedie óptimo (transformado / original) por celda, media de las series"""
    r = {}
    for k, s in ser.items():
        m2 = fn(s); c = celda(s); y = s.y.values
        r[k] = {cc: kopt(y[c == cc], m2[c == cc]) / kopt(y[c == cc], s.m.values[c == cc]) for cc in CELS}
    return {cc: float(np.mean([r[k][cc] for k in r])) for cc in CELS}, r


# ---------- tablero ----------
PRE = json.load(open(R + "in/preinscripcion.json"))
REC = {r["sha256"]: float(r["d2"]) for r in json.load(open(R + "recibos_reales_20261026.json"))}


def leer_pred(p):
    d = pd.read_csv(p, dtype={"row_id": str}); return d


def test_df(row_ids):
    t = B.loc[row_ids].copy(); t["c_fila"] = 1.0; return t
