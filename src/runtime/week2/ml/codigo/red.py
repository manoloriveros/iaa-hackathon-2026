"""Fit an FT-Transformer with power-1.5 Tweedie loss and an exposure offset.
Pretrain on developed data and fine-tune on emerging data.
Usage: python red.py pre <phase> <line>
       python red.py fino <phase> <line> <N1|N2a|N2b|N3>
DEV/HOLD share developed 2021-2023; production uses 2021-2024.
"""
from __future__ import annotations
import sys, time, math, hashlib
import numpy as np, pandas as pd, torch, torch.nn as nn
from comun import *
from variables import *

torch.set_num_threads(2)
SEMILLA = 20261024


class Tokenizador(nn.Module):
    def __init__(self, n_num, cards, d):
        super().__init__()
        self.w = nn.Parameter(torch.randn(n_num, d) * 0.1)
        self.b = nn.Parameter(torch.zeros(n_num, d))
        self.miss = nn.Parameter(torch.randn(n_num, d) * 0.1)
        self.emb = nn.ModuleList([nn.Embedding(c + 1, d) for c in cards])  # Index 0 represents unknown or missing categories.
        for e in self.emb:
            nn.init.normal_(e.weight, std=0.1)

    def forward(self, xn, mn, xc):
        t = xn.unsqueeze(-1) * self.w + self.b
        t = torch.where(mn.unsqueeze(-1), self.miss.expand_as(t), t)
        if len(self.emb):
            tc = torch.stack([e(xc[:, j]) for j, e in enumerate(self.emb)], 1)
            t = torch.cat([t, tc], 1)
        return t


class Bloque(nn.Module):
    def __init__(self, d, h, drop):
        super().__init__()
        self.n1 = nn.LayerNorm(d); self.att = nn.MultiheadAttention(d, h, dropout=drop, batch_first=True)
        self.n2 = nn.LayerNorm(d)
        self.ff = nn.Sequential(nn.Linear(d, 2 * d * 2), nn.GLU(), nn.Dropout(drop), nn.Linear(2 * d, d))
        self.dr = nn.Dropout(drop)

    def forward(self, x):
        z = self.n1(x); x = x + self.dr(self.att(z, z, z, need_weights=False)[0])
        return x + self.dr(self.ff(self.n2(x)))


class FTT(nn.Module):
    def __init__(self, n_num, cards, d=32, h=2, L=2, drop=0.1):
        super().__init__()
        self.tok = Tokenizador(n_num, cards, d)
        self.extra = None  # Additional emerging-market tokens.
        self.cls = nn.Parameter(torch.randn(1, 1, d) * 0.1)
        self.bloques = nn.ModuleList([Bloque(d, h, drop) for _ in range(L)])
        self.nf = nn.LayerNorm(d); self.cab = nn.Linear(d, 1)
        self.sesgo = nn.Parameter(torch.zeros(1))

    def forward(self, xn, mn, xc, xe=None):
        t = self.tok(xn, mn, xc)
        if self.extra is not None and xe is not None:
            t = torch.cat([t, torch.stack([e(xe[:, j]) for j, e in enumerate(self.extra)], 1)], 1)
        x = torch.cat([self.cls.expand(len(t), -1, -1), t], 1)
        for b in self.bloques:
            x = b(x)
        return self.cab(self.nf(x[:, 0])).squeeze(-1) + self.sesgo


def perdida(eta, y, off, w):
    """Power-1.5 Tweedie deviance without constant terms, with mu=exp(eta+off)."""
    s = eta + off
    return torch.sum(w * 2 * (2 * y * torch.exp(-0.5 * s) + 2 * torch.exp(0.5 * s))) / torch.sum(w)


class Prepro:
    """Fit developed-market quantile-normal numeric transforms and categorical codes."""

    def __init__(self, df, num, cat, cats):
        self.num, self.cat, self.cats = num, cat, cats
        self.q = {}
        for c in num:
            v = pd.to_numeric(df[c], errors="coerce").astype(float).values
            v = v[~np.isnan(v)]
            qs = np.unique(np.quantile(v, np.linspace(0, 1, 201))) if len(v) else np.array([0.0, 1.0])
            self.q[c] = qs

    def __call__(self, df):
        from scipy.stats import norm
        XN = np.zeros((len(df), len(self.num)), np.float32); MN = np.zeros_like(XN, dtype=bool)
        for j, c in enumerate(self.num):
            v = pd.to_numeric(df[c], errors="coerce").astype(float).values if c in df else np.full(len(df), np.nan)
            m = np.isnan(v); qs = self.q[c]
            if len(qs) < 2:
                z = np.zeros(len(v))
            else:
                r = np.interp(v, qs, np.linspace(0, 1, len(qs)))
                z = norm.ppf(np.clip(r, 0.005, 0.995))
            XN[:, j] = np.where(m, 0, z); MN[:, j] = m
        XC = np.zeros((len(df), len(self.cat)), np.int64)
        for j, c in enumerate(self.cat):
            mapa = {v: i + 1 for i, v in enumerate(self.cats[c])}
            s = df[c].astype(object).where(df[c].notna(), None) if c in df else pd.Series([None] * len(df))
            XC[:, j] = [mapa.get(str(x) if x is not None else None, 0) for x in s.values]
        return XN, MN, XC


def entrenar(model, datos, val, lr, epocas, lote=1024, paciencia=3, wd=1e-5, l2sp=None, params=None, log=""):
    """Training/validation tensor tuples: (xn,mn,xc,xe,y,off,w)."""
    params = params if params is not None else [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=wd)
    n = len(datos[4]); g = torch.Generator().manual_seed(SEMILLA)
    mejor, estado, sin_mejora, hist = math.inf, None, 0, []
    ref = None
    if l2sp is not None:
        ref = {k: v.detach().clone() for k, v in model.named_parameters()}
    for ep in range(epocas):
        model.train(); perm = torch.randperm(n, generator=g); t0 = time.time(); tot = 0.0
        for i in range(0, n, lote):
            idx = perm[i:i + lote]
            xn, mn, xc, xe, y, off, w = (d[idx] if d is not None else None for d in datos)
            loss = perdida(model(xn, mn, xc, xe), y, off, w)
            if l2sp is not None:
                pen = sum(((p - ref[k]) ** 2).sum() for k, p in model.named_parameters() if k in ref and p.requires_grad)
                loss = loss + l2sp * pen
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
            tot += float(loss.detach()) * len(idx)
        dv = evaluar(model, val)
        hist.append((ep, tot / n, dv, round(time.time() - t0, 1)))
        print(log, "época", ep, "entren", round(tot / n, 4), "val", round(dv, 5), "s", round(time.time() - t0, 1), flush=True)
        if dv < mejor - 1e-6:
            mejor, estado, sin_mejora = dv, {k: v.detach().clone() for k, v in model.state_dict().items()}, 0
        else:
            sin_mejora += 1
            if sin_mejora >= paciencia:
                break
    model.load_state_dict(estado)
    return mejor, hist


@torch.no_grad()
def evaluar(model, val, lote=8192):
    model.eval(); tot = 0.0; ws = 0.0
    n = len(val[4])
    for i in range(0, n, lote):
        sl = slice(i, i + lote)
        xn, mn, xc, xe, y, off, w = (d[sl] if d is not None else None for d in val)
        tot += float(perdida(model(xn, mn, xc, xe), y, off, w)) * float(w.sum()); ws += float(w.sum())
    return tot / ws


@torch.no_grad()
def predecir(model, xn, mn, xc, xe=None, lote=8192):
    model.eval(); out = []
    for i in range(0, len(xn), lote):
        sl = slice(i, i + lote)
        out.append(model(xn[sl], mn[sl], xc[sl], None if xe is None else xe[sl]))
    return torch.cat(out).numpy()


def tens(XN, MN, XC, XE, y, off, w):
    return (torch.tensor(XN), torch.tensor(MN), torch.tensor(XC), None if XE is None else torch.tensor(XE),
            torch.tensor(y, dtype=torch.float32), torch.tensor(off, dtype=torch.float32), torch.tensor(w, dtype=torch.float32))


# Command-line execution.
FASES = {"dev": dict(clima="hasta2023", dev_years=[2021, 2022, 2023], em_train=[2023], em_eval=None, pre="dev"),
         "hold": dict(clima="hasta2023", dev_years=[2021, 2022, 2023], em_train=[2023], em_eval=2024, pre="dev"),
         "prod": dict(clima="hasta2024", dev_years=[2021, 2022, 2023, 2024], em_train=[2023, 2024], em_eval=2025, pre="prod"),
         "pcv": dict(clima="hasta2024", dev_years=[2021, 2022, 2023, 2024], em_train=[2023, 2024], em_eval=None, pre="prod")}
EXTRA = ["region", "gender", "self_employed"]


def columnas(linea):
    cols = comunes(linea)
    return [c for c in cols if c not in CATEGORICAS], [c for c in cols if c in CATEGORICAS]


def submuestra(df, frac=0.1, sal="nn"):
    h = np.array([int(hashlib.sha256((sal + r).encode()).hexdigest()[:8], 16) / 2 ** 32 for r in df.row_id.values])
    keep = (df.y.values > 0) | (h < frac)
    w = np.where(df.y.values > 0, 1.0, 1.0 / frac)
    return keep, w


def preentrenar(fase, linea):
    import pickle
    cf = FASES[fase]; dirm = TRABAJO / "modelos" / cf["pre"]; dirm.mkdir(parents=True, exist_ok=True)
    f = dirm / f"N_pre_{linea}.pt"
    if f.exists():
        print("ya existe", f); return
    torch.manual_seed(SEMILLA); np.random.seed(SEMILLA)
    dv = cargar("developed", linea, cf["clima"]); em = cargar("emerging", linea, cf["clima"])
    dv = dv[dv.year.isin(cf["dev_years"])].reset_index(drop=True)
    num, cat = columnas(linea)
    cats = categorias_union([dv, em], num + cat + EXTRA)
    pp = Prepro(dv, num, cat, cats)
    tope = float(np.quantile(dv.y[dv.y > 0], 0.999))
    keep, w = submuestra(dv)
    dv = dv[keep].reset_index(drop=True); w = w[keep]
    XN, MN, XC = pp(dv)
    y = np.minimum(dv.y.values, tope); off = np.log(dv.exposure.values * dv.c_fila.values)
    base = math.log(np.sum(w * y) / np.sum(w * np.exp(off)))
    va = dv.fold.values == 0
    T = tens(XN, MN, XC, None, y, off, w)
    tr = tuple(None if t is None else t[torch.tensor(~va)] for t in T)
    vl = tuple(None if t is None else t[torch.tensor(va)] for t in T)
    m = FTT(len(num), [len(cats[c]) for c in cat])
    with torch.no_grad():
        m.sesgo.fill_(base)
    print(linea, "filas", len(dv), "val", int(va.sum()), "tope", round(tope), flush=True)
    mejor, hist = entrenar(m, tr, vl, lr=1e-3, epocas=6, lote=1024, paciencia=2, log=f"pre {linea}")
    torch.save(m.state_dict(), f)
    with open(dirm / f"N_pre_{linea}.pkl", "wb") as fh:
        pickle.dump({"prepro": pp, "num": num, "cat": cat, "cats": cats, "tope": tope, "hist": hist}, fh)
    guardar_json({"val": mejor, "hist": hist, "tope": tope, "filas": int(len(dv))}, dirm / f"N_pre_{linea}.json")


def interno(cids):
    return np.array([int(hashlib.sha256(("mlind_inner|" + c).encode()).hexdigest()[:8], 16) % 5 == 0 for c in cids])


def fino(fase, linea, var):
    import pickle
    cf = FASES[fase]; dirm = TRABAJO / "modelos" / cf["pre"]
    meta = pickle.load(open(dirm / f"N_pre_{linea}.pkl", "rb"))
    pp, num, cat, cats, tope = meta["prepro"], meta["num"], meta["cat"], meta["cats"], meta["tope"]
    em = cargar("emerging", linea, cf["clima"])
    XN, MN, XC = pp(em)
    XE = np.zeros((len(em), len(EXTRA)), np.int64)
    for c in EXTRA:
        if c not in cats:
            cats[c] = sorted(set(em[c].dropna().astype(str)))
    for j, c in enumerate(EXTRA):
        mapa = {v: i + 1 for i, v in enumerate(cats[c])}
        s = em[c].astype(object).where(em[c].notna(), None)
        XE[:, j] = [mapa.get(str(x) if x is not None else None, 0) for x in s.values]
    raw2 = pd.read_parquet(TRABAJO / "pred" / fase / f"T2braw_{linea}.parquet")
    em = em.reset_index(drop=True)
    r2 = em[["row_id"]].merge(raw2, on="row_id", how="left").raw.values
    tr_mask = ((em.conjunto == "train") & em.year.isin(cf["em_train"])).values
    if cf["em_eval"] is None:
        sets = [(tr_mask & (em.fold.values != k), tr_mask & (em.fold.values == k)) for k in range(5)]
    else:
        sets = [(tr_mask, (em.year == cf["em_eval"]).values)]
    off_all = np.log(em.exposure.values * np.where(em.conjunto == "test", 1.0, em.c_fila.values))
    preds = []; info = []
    for a, b in sets:
        torch.manual_seed(SEMILLA)
        ya = em.y.values[a]
        k0 = factor_tweedie(ya, np.exp(off_all[a]))
        extra_off = np.zeros(len(em))
        if var == "N3":
            k2 = factor_tweedie(ya, np.exp(off_all[a] + r2[a]))
            extra_off = r2 + math.log(k2)
        m = FTT(len(num), [len(cats[c]) for c in cat])
        if var in ("N2a", "N2b", "N3"):
            m.load_state_dict(torch.load(dirm / f"N_pre_{linea}.pt"))
        d = m.cls.shape[-1]
        m.extra = nn.ModuleList([nn.Embedding(len(cats[c]) + 1, d) for c in EXTRA])
        for e in m.extra:
            nn.init.normal_(e.weight, std=0.02)
        with torch.no_grad():
            if var == "N3":
                m.cab.weight.zero_(); m.cab.bias.zero_(); m.sesgo.zero_()
            else:
                # Preserve transferred relativities while setting the initial emerging-market level.
                eta0 = predecir(m, *[torch.tensor(x[a]) for x in (XN, MN, XC)], torch.tensor(XE[a]))
                m.sesgo += math.log(factor_tweedie(ya, np.exp(eta0 + off_all[a])))
        params = None; l2sp = None; lr = 2e-4
        if var == "N1":
            lr = 1e-3
        elif var == "N2b":
            for p in m.parameters():
                p.requires_grad = False
            for mod in [m.cab, m.nf, m.extra]:
                for p in mod.parameters():
                    p.requires_grad = True
            m.sesgo.requires_grad = True
            lr = 1e-3
        else:  # N2a/N3: full fine-tuning with L2-SP.
            l2sp = 1e-2
        idx_a = np.where(a)[0]; v = interno(em.customer_id.values[idx_a])
        it, iv = idx_a[~v], idx_a[v]
        yc = np.minimum(em.y.values, tope)
        T = lambda ix: tens(XN[ix], MN[ix], XC[ix], XE[ix], yc[ix], off_all[ix] + extra_off[ix], np.ones(len(ix)))
        mejor, hist = entrenar(m, T(it), T(iv), lr=lr, epocas=20, lote=512, paciencia=4, l2sp=l2sp, log=f"{var} {linea}")
        # Relevel training predictions with and without the cap.
        eta_a = predecir(m, torch.tensor(XN[a]), torch.tensor(MN[a]), torch.tensor(XC[a]), torch.tensor(XE[a]))
        kin = factor_tweedie(ya, np.exp(eta_a + off_all[a] + extra_off[a]))
        eta_b = predecir(m, torch.tensor(XN[b]), torch.tensor(MN[b]), torch.tensor(XC[b]), torch.tensor(XE[b]))
        mu = kin * np.exp(eta_b + extra_off[b]) * em.exposure.values[b]
        preds.append(pd.DataFrame({"row_id": em.row_id.values[b], "mu": mu}))
        info.append({"val": mejor, "epocas": len(hist), "kin": kin})
        if cf["em_eval"] is not None:
            (TRABAJO / "modelos" / fase).mkdir(parents=True, exist_ok=True)
            torch.save(m.state_dict(), TRABAJO / "modelos" / fase / f"{var}_{linea}.pt")
    out = TRABAJO / "pred" / fase; out.mkdir(parents=True, exist_ok=True)
    pd.concat(preds).to_parquet(out / f"{var}_{linea}.parquet", index=False)
    guardar_json(info, out / f"{var}_{linea}_meta.json")


if __name__ == "__main__":
    modo, fase, linea = sys.argv[1], sys.argv[2], sys.argv[3]
    if modo == "pre":
        preentrenar(fase, linea)
    else:
        for var in sys.argv[4].split(","):
            t0 = time.time(); fino(fase, linea, var); print(var, linea, "listo", round(time.time() - t0), "s", flush=True)
