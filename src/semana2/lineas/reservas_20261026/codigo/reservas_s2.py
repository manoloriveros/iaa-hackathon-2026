"""Acotación de reservas de la semana 2 (mercado emergente) con el modelo actual F3c.

Plan preinscrito: Hackaton/Semana 2/Claude/reservas_20261026/PREINSCRIPCION.md (SHA-256 67abc8e2…00c6), escrito en el equipo a
las 13:49:39 UTC del 26-10-2026, antes de calcular. Nada de esto demuestra suficiencia: estima el sesgo de la reserva de caso bajo
un supuesto escrito (S1), contrasta la curva de reporte del desarrollado en la cohorte 2023 del emergente y mide cuánto sesgo
movería el nivel 2025 de F3c más allá de la materialidad del 1 %, siguiendo la cadena de sondas con la que se fijó ese nivel.

Uso: python3 reservas_s2.py <raiz> [datos|a|b|c|d|e|f|g]   (sin etapa, todas; g son lecturas no preinscritas)
<raiz> contiene datos/ (Parquet emergentes y claims_desarrollado.parquet), cadena/ (CSV y JSON de la cadena de F3c),
oof/pred/pcv (predicciones cruzadas de T2b de la línea ML independiente) y semana1/ (insumos de la acotación de la semana 1).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(sys.argv[1]).resolve()
DAT, CAD, PCV, S1, RES = RAIZ / "datos", RAIZ / "cadena", RAIZ / "oof" / "pred" / "pcv", RAIZ / "semana1", RAIZ / "resultados"
RES.mkdir(exist_ok=True)
V = np.datetime64("2024-12-31")
V1 = np.datetime64("2023-12-31")
D = 1095
LINEAS = ["motor", "buildings", "contents"]
LARGOS = {"motor": "bodily_injury", "buildings": "subsidence"}
CELDAS = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
MAT = 0.01
B_REP = 400
SEMILLA = 20261026
MIN_CERR = 20
T0_CONTROL = 27997991.57


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def r(x, n=6):
    if x is None:
        return None
    x = float(x)
    return None if not np.isfinite(x) else round(x, n)


def guardar(nombre, obj):
    obj = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **obj}
    (RES / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


def leer(nombre):
    return json.loads((RES / nombre).read_text(encoding="utf-8"))


def desv(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    return 2.0 * (np.power(y, 0.5) / -0.25 - y * np.power(mu, -0.5) / -0.5 + np.power(mu, 0.5) / 0.5)


def ftw(y, m, w=None):
    """Escalar Tweedie 1,5: factor k que minimiza la desviación de k·m."""
    w = np.ones(len(m)) if w is None else w
    return float(np.sum(w * y / np.sqrt(m)) / np.sum(w * np.sqrt(m)))


# ------------------------------------------------------------------------------------------------ datos

def siniestros(p: Path, dev: bool) -> pd.DataFrame:
    c = pd.read_parquet(p)
    if dev:  # DUP01: fuera las copias de 11 caracteres de pares idénticos salvo claim_id
        cols = [x for x in c.columns if x != "claim_id"]
        c = c[~(c.duplicated(cols, keep=False) & (c.claim_id.str.len() == 11))].copy()
    c["loss_date"] = pd.to_datetime(c.loss_date)
    c["report_date"] = pd.to_datetime(c.report_date)
    c["neto"] = c.incurred_to_date - c.recoveries
    c["aceptado"] = c.status != "repudiated"
    c["reserva"] = np.where(c.status == "open", c.incurred_to_date - c.paid_to_date, 0.0)
    return c


def curvas(cd: pd.DataFrame, peso: str):
    """Curva acumulada de reporte por (ramo, peligro) en el desarrollado (cohortes con ≥ D días), integrada dos veces para
    promediar sobre los días del periodo, como etiquetas.py de la misión 0,17. peso = 'neto' (coste) o 'uno' (conteos)."""
    G = {}
    for (l, p), g in cd[cd.aceptado].groupby(["line", "peril"]):
        g = g[(V - g.loss_date.values.astype("datetime64[D]")).astype(int) >= D]
        dly = (g.report_date - g.loss_date).dt.days.values
        w = g.neto.values if peso == "neto" else np.ones(len(g))
        ok = dly <= D
        cum = np.clip(np.bincount(dly[ok], weights=w[ok], minlength=D + 1).cumsum() / w[ok].sum(), 0, 1)
        G[(l, p)] = np.concatenate([[0.0], np.cumsum(np.concatenate([cum, np.ones(4000 - len(cum))]))])
    return G


def comp(G, l, p, s, e, corte=V):
    """Completitud media sobre los días del periodo [s, e] al corte. Con corte = V y periodos que terminan antes de V es la
    fórmula de etiquetas.py; si el periodo pasa del corte, los días posteriores cuentan con completitud 0."""
    g = G[(l, p)]
    a_raw = (corte - e).astype(int)
    b_raw = (corte - s).astype(int)
    a = np.clip(a_raw, 0, None)
    b = np.clip(b_raw, -1, None)
    num = np.where(b >= a, g[np.clip(b + 1, 0, len(g) - 1)] - g[np.clip(a, 0, len(g) - 1)], 0.0)
    return num / np.maximum(b_raw - a_raw + 1, 1)


def etapa_datos():
    fuentes = {p.name: sha(p) for p in sorted(DAT.glob("*.parquet"))}
    fuentes.update({p.name: sha(p) for p in sorted(CAD.glob("*.csv"))})
    ce = siniestros(DAT / "claims.parquet", False)
    cd = siniestros(DAT / "claims_desarrollado.parquet", True)
    Gc, Gn = curvas(cd, "neto"), curvas(cd, "uno")
    cus = pd.read_parquet(DAT / "customers.parquet", columns=["customer_id", "gender", "prior_claims_5y", "marketing_segment"])
    filas, asign = [], []
    for l in LINEAS:
        df = pd.read_parquet(DAT / f"policies_{l}.parquet")
        df["line"] = l
        df["period_start"] = pd.to_datetime(df.period_start)
        df["period_end"] = pd.to_datetime(df.period_end)
        df["expo"] = ((df.period_end - df.period_start).dt.days + 1) / 365.0
        df["year"] = df.period_start.dt.year
        cl = ce[ce.line == l]
        mm = cl.merge(df[["row_id", "policy_id", "period_start", "period_end", "new_business", "year"]], on="policy_id")
        mm = mm[(mm.loss_date >= mm.period_start) & (mm.loss_date <= mm.period_end)]
        assert mm.claim_id.is_unique, "un siniestro asignado a dos periodos"
        asign.append(mm)
        acc = mm[mm.aceptado]
        df["y"] = df.row_id.map(acc.groupby("row_id").neto.sum()).fillna(0.0)
        df["R"] = df.row_id.map(acc.groupby("row_id").reserva.sum()).fillna(0.0)
        s = df.period_start.values.astype("datetime64[D]")
        e = df.period_end.values.astype("datetime64[D]")
        perils = sorted(cl.peril.unique())
        for p_ in perils:
            df[f"y_{p_}"] = df.row_id.map(acc[acc.peril == p_].groupby("row_id").neto.sum()).fillna(0.0)
            df[f"R_{p_}"] = df.row_id.map(acc[acc.peril == p_].groupby("row_id").reserva.sum()).fillna(0.0)
            df[f"c_{p_}"] = comp(Gc, l, p_, s, e)
            df[f"c1_{p_}"] = comp(Gc, l, p_, s, e, V1)
            df[f"n_{p_}"] = comp(Gn, l, p_, s, e)
            df[f"n1_{p_}"] = comp(Gn, l, p_, s, e, V1)
        ult = {p_: df[f"y_{p_}"].sum() / max(np.average(df[f"c_{p_}"], weights=df.expo), 1e-6) for p_ in perils}
        tot = sum(ult.values())
        df["c_fila"] = sum(ult[p_] / tot * df[f"c_{p_}"] for p_ in perils)
        if l == "motor":
            nb = df.ncb_years.astype(float)
            df["ncb_banda"] = np.select([nb <= 0, nb <= 2, nb <= 5, nb <= 9], ["0", "1-2", "3-5", "6-9"], "10+")
        if l == "contents":
            df["wfh"] = df.works_from_home.astype(str)
        df = df.merge(cus, on="customer_id", how="left")
        df["previos"] = np.where(df.prior_claims_5y.fillna(0) >= 2, "2+", df.prior_claims_5y.fillna(0).astype(int).astype(str))
        df["celda"] = l + "_" + df.new_business.astype(bool).astype(int).astype(str)
        mu = pd.read_parquet(PCV / f"T2b_{l}.parquet")
        df["mu"] = df.row_id.map(mu.set_index("row_id").mu)
        assert df.mu.notna().all(), f"faltan predicciones PCV en {l}"
        df["m"] = df.mu * df.c_fila
        keep = ["row_id", "line", "year", "celda", "new_business", "expo", "y", "R", "c_fila", "mu", "m", "gender", "previos",
                "marketing_segment"] + (["ncb_banda"] if l == "motor" else []) + (["wfh"] if l == "contents" else []) + \
               [c for c in df.columns if c[:2] in ("y_", "R_", "c_", "n_") or c[:3] in ("c1_", "n1_")]
        filas.append(df[[c for c in dict.fromkeys(keep) if c in df.columns]])
    b = pd.concat(filas, ignore_index=True)
    a = pd.concat(asign, ignore_index=True)
    b.to_parquet(RES / "base_filas.parquet", index=False)
    a.to_parquet(RES / "siniestros_asignados.parquet", index=False)
    cd.to_parquet(RES / "siniestros_desarrollado.parquet", index=False)
    t0 = float(b.y.sum())
    ctrl = {"T0_total": r(t0, 2), "T0_control": T0_CONTROL, "T0_coincide": abs(t0 - T0_CONTROL) < 0.005,
            "siniestros": int(len(ce)), "asignados": int(len(a)), "sin_periodo": int(len(ce) - len(a)),
            "aceptados_asignados": int(a.aceptado.sum()), "abiertos_asignados": int((a.status == "open").sum()),
            "filas_entrenamiento": int(len(b))}
    guardar("datos.json", {"fuentes_sha256": fuentes, "controles": ctrl})
    print(json.dumps(ctrl, ensure_ascii=False))
    if not ctrl["T0_coincide"]:
        sys.exit("PARADA preinscrita: T0 no coincide con el control")


# ------------------------------------------------------------------------------------------------ A: hechos

def etapa_a():
    a = pd.read_parquet(RES / "siniestros_asignados.parquet")
    b = pd.read_parquet(RES / "base_filas.parquet")
    ce = siniestros(DAT / "claims.parquet", False)
    out = {"por_ramo_anio": {}, "por_peligro": {}, "por_negocio": {}, "recobros": {}, "rechazados": {}, "sin_periodo": {}}
    for l in LINEAS:
        for y in (2023, 2024):
            q = b[(b.line == l) & (b.year == y)]
            ab = a[(a.line == l) & (a.year == y) & (a.status == "open")]
            out["por_ramo_anio"][f"{l}_{y}"] = {"T0": r(q.y.sum(), 2), "reserva": r(q.R.sum(), 2), "reserva_sobre_T0": r(q.R.sum() / q.y.sum(), 4),
                                                "abiertos": int(len(ab)), "abiertos_sin_reserva": int((ab.reserva <= 0).sum()),
                                                "completitud_media_coste": r(np.average(q.c_fila, weights=q.expo), 4),
                                                "ibnr_implicito": r((q.y.sum() / np.average(q.c_fila, weights=q.expo)) - q.y.sum(), 2) if q.y.sum() > 0 else None}
        ab = a[(a.line == l) & (a.status == "open")]
        tot_res = float(ab.reserva.sum())
        for p, g in ab.groupby("peril"):
            out["por_peligro"][f"{l}|{p}"] = {"abiertos": int(len(g)), "reserva": r(g.reserva.sum(), 2), "peso_en_reserva_ramo": r(g.reserva.sum() / tot_res, 4),
                                              "reserva_media": r(g.reserva.mean(), 2), "abiertos_2023": int((g.year == 2023).sum())}
        for nb, g in b[b.line == l].groupby("new_business"):
            out["por_negocio"][f"{l}_{int(bool(nb))}"] = {"T0": r(g.y.sum(), 2), "reserva": r(g.R.sum(), 2), "reserva_sobre_T0": r(g.R.sum() / g.y.sum(), 4) if g.y.sum() else None}
        # recobros: los cerrados recuperan, los abiertos no (si la reserva no lo anticipa, T0 sobrestima)
        acc = a[(a.line == l) & a.aceptado]
        rec = {}
        for p, g in acc.groupby("peril"):
            cerr = g[g.status == "closed"]; abie = g[g.status == "open"]
            tasa = float(cerr.recoveries.sum() / cerr.incurred_to_date.sum()) if cerr.incurred_to_date.sum() > 0 else 0.0
            rec[p] = {"tasa_recobro_cerrados": r(tasa, 4), "recobros_en_abiertos": r(abie.recoveries.sum(), 2),
                      "incurrido_abiertos": r(abie.incurred_to_date.sum(), 2), "sobrestimacion_si_no_anticipa": r(tasa * abie.incurred_to_date.sum(), 2)}
        T0_l = float(b[b.line == l].y.sum())
        sob = sum(v["sobrestimacion_si_no_anticipa"] or 0 for v in rec.values())
        out["recobros"][l] = {"por_peligro": rec, "sobrestimacion_total": r(sob, 2), "sobre_T0": r(sob / T0_l, 4)}
        rj = a[(a.line == l) & (a.status == "repudiated")]
        sev = acc[acc.status == "closed"].groupby("peril").incurred_to_date.mean()
        out["rechazados"][l] = {"n": int(len(rj)), "con_importe": int(((rj.incurred_to_date != 0) | (rj.paid_to_date != 0)).sum()),
                                "coste_si_se_pagaran_todos": r(sum(float(sev.get(p, 0.0)) for p in rj.peril), 2),
                                "sobre_T0": r(sum(float(sev.get(p, 0.0)) for p in rj.peril) / T0_l, 4)}
    sp = ce[~ce.claim_id.isin(a.claim_id)]
    out["sin_periodo"] = {"n": int(len(sp)), "abiertos": int((sp.status == "open").sum()), "neto_aceptado": r(sp[sp.aceptado].neto.sum(), 2)}
    tot = {"T0": r(b.y.sum(), 2), "reserva": r(b.R.sum(), 2), "reserva_sobre_T0": r(b.R.sum() / b.y.sum(), 4),
           "abiertos": int((a.status == "open").sum()), "abiertos_sin_reserva": int(((a.status == "open") & (a.reserva <= 0)).sum()),
           "reserva_2023": r(b[b.year == 2023].R.sum(), 2), "T0_2023": r(b[b.year == 2023].y.sum(), 2),
           "reserva_2024": r(b[b.year == 2024].R.sum(), 2), "T0_2024": r(b[b.year == 2024].y.sum(), 2)}
    out["totales"] = tot
    guardar("parte_a.json", out)
    print(json.dumps(tot, ensure_ascii=False))


# ------------------------------------------------------------------------------------------------ B: β

def _prep(d):
    g = pd.factorize(d.celda_b.values)[0]
    return {"g": g, "ng": int(g.max()) + 1 if len(g) else 0, "ab": (d.status == "open").values,
            "inc": d.incurred_to_date.values.astype(float), "paid": d.paid_to_date.values.astype(float)}


def _beta(z, w=None):
    w = np.ones(len(z["g"])) if w is None else w
    g, ab, ng = z["g"], z["ab"], z["ng"]
    wc = np.bincount(g[~ab], weights=w[~ab], minlength=ng)
    ic = np.bincount(g[~ab], weights=(w * z["inc"])[~ab], minlength=ng)
    wo = np.bincount(g[ab], weights=w[ab], minlength=ng)
    io = np.bincount(g[ab], weights=(w * z["inc"])[ab], minlength=ng)
    po = np.bincount(g[ab], weights=(w * z["paid"])[ab], minlength=ng)
    ok = (wc >= MIN_CERR) & (wo > 0)
    implicito = float((wo[ok] * ic[ok] / wc[ok]).sum())
    inc_ab, pag_ab = float(io[ok].sum()), float(po[ok].sum())
    reserva = inc_ab - pag_ab
    return {"beta": (implicito - pag_ab) / reserva if reserva > 0 else np.nan, "reserva_cubierta": reserva, "celdas": int(ok.sum())}


def _boot(z, rng):
    v = np.array([_beta(z, rng.poisson(1.0, size=len(z["g"])).astype(float))["beta"] for _ in range(B_REP)], float)
    return v


def q90(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return [r(np.quantile(v, 0.05), 4), r(np.quantile(v, 0.95), 4)] if len(v) > 20 else [None, None]


def _a2(d):
    g = d.groupby(["celda_b", "status"]).incurred_to_date.agg(["size", "mean"]).unstack("status").dropna()
    if ("size", "closed") not in g.columns or ("size", "open") not in g.columns:
        return None
    g = g[(g[("size", "closed")] >= MIN_CERR) & (g[("size", "open")] >= 5)]
    if len(g) < 4:
        return {"celdas": int(len(g)), "t": None}
    frac = g[("size", "closed")] / (g[("size", "closed")] + g[("size", "open")])
    x = np.log(frac / (1 - frac)).values
    yv = np.log(g[("mean", "open")] / g[("mean", "closed")]).values
    w = g[("size", "open")].values.astype(float)
    X = np.column_stack([np.ones(len(x)), x]); XtW = X.T * w
    be = np.linalg.solve(XtW @ X, XtW @ yv); res = yv - X @ be
    s2 = float((w * res ** 2).sum() / max(len(x) - 2, 1)); cov = s2 * np.linalg.inv(XtW @ X)
    t = be[1] / np.sqrt(cov[1, 1]) if cov[1, 1] > 0 else np.nan
    return {"celdas": int(len(g)), "pendiente": r(be[1], 4), "t": r(t, 2), "contradice_S1": bool(abs(t) > 2) if np.isfinite(t) else None}


def _grupo(d, por_peligro: bool):
    d = d[d.status.isin(["open", "closed"])].copy()
    q = d.report_date.dt.to_period("Q").astype(str)
    d["celda_b"] = (d.peril + "|" + q) if por_peligro else q
    return d


def etapa_b():
    a = pd.read_parquet(RES / "siniestros_asignados.parquet")
    cd = pd.read_parquet(RES / "siniestros_desarrollado.parquet")
    rng_e, rng_d = np.random.default_rng(SEMILLA), np.random.default_rng(SEMILLA + 1)
    s1 = json.loads((S1 / "parte_a.json").read_text(encoding="utf-8"))
    out, draws = {}, {}
    casos = []
    for l in LINEAS:
        casos.append((l, "_ramo", None))
        if l in LARGOS:
            casos.append((l, LARGOS[l], None))
            casos.append((l, "_resto", None))
        casos += [(l, "_ramo", 0), (l, "_ramo", 1)]
    for l, p, nb in casos:
        def sel(df, emergente):
            q = df[(df.line == l) & df.aceptado]
            if p == "_resto":
                q = q[q.peril != LARGOS[l]]
            elif p != "_ramo":
                q = q[q.peril == p]
            if nb is not None and emergente:
                q = q[q.new_business.astype(bool) == bool(nb)]
            return _grupo(q, p in ("_ramo", "_resto"))
        de = sel(a, True)
        clave = f"{l}|{p}" + ("" if nb is None else f"|nb{nb}")
        if (de.status == "open").sum() == 0:
            out[clave] = {"abiertos": 0}
            continue
        ze = _prep(de); be = _beta(ze); ve = _boot(ze, rng_e); ve_ok = ve[np.isfinite(ve)]
        fila = {"abiertos": int((de.status == "open").sum()), "cerrados": int((de.status == "closed").sum()),
                "reserva": r(de[de.status == "open"].reserva.sum(), 2), "beta": r(be["beta"], 4), "celdas": be["celdas"],
                "cobertura_reserva": r(be["reserva_cubierta"] / max(float(de[de.status == "open"].reserva.sum()), 1e-9), 4),
                "ic90": q90(ve), "replicas_validas": int(len(ve_ok)),
                "A2": _a2(de)}
        draws[clave] = ve
        if nb is None:
            dd = sel(cd, False)
            zd = _prep(dd); bd = _beta(zd); vd = _boot(zd, rng_d)
            ok = np.isfinite(ve) & np.isfinite(vd)
            ref = s1.get(l, {}).get("peligros", {}).get(p if p != "_resto" else "__", {}).get("todos", {})
            fila["desarrollado"] = {"beta_recalculado": r(bd["beta"], 4), "ic90": q90(vd), "celdas": bd["celdas"],
                                    "beta_semana1": ref.get("beta_reserva"), "ic90_semana1": ref.get("ic90_beta"),
                                    "nota": "recalculado sin asignación a periodo (incluye prehistoria y no asignados); la semana 1 los excluía"}
            dif = ve[ok] - vd[ok]
            qd = q90(dif)
            fila["diferencia_emergente_menos_desarrollado"] = {"puntual": r(be["beta"] - bd["beta"], 4), "ic90": qd,
                                                               "excluye_cero": None if qd[0] is None else bool(qd[0] > 0 or qd[1] < 0)}
            if fila["diferencia_emergente_menos_desarrollado"]["excluye_cero"] is False:
                dj = pd.concat([de.assign(mercado="e"), dd.assign(mercado="d")])
                dj["celda_b"] = dj.mercado + "|" + dj.celda_b  # las celdas no se mezclan entre mercados; solo se agregan las reservas
                zj = _prep(dj); bj = _beta(zj); vj = _boot(zj, rng_d)
                fila["agrupado_secundario"] = {"beta": r(bj["beta"], 4), "ic90": q90(vj)}
        out[clave] = fila
        print(clave, fila["beta"], fila["ic90"], fila.get("desarrollado", {}).get("beta_recalculado"), (fila["A2"] or {}).get("t"), flush=True)
    np.savez_compressed(RES / "beta_replicas.npz", **{k.replace("|", "__"): v for k, v in draws.items()})
    guardar("parte_b.json", {"semilla": SEMILLA, "replicas": B_REP, "min_cerrados": MIN_CERR, "beta": out})


# ------------------------------------------------------------------------------------------------ C: IBNR

def etapa_c():
    b = pd.read_parquet(RES / "base_filas.parquet")
    a = pd.read_parquet(RES / "siniestros_asignados.parquet")
    rng = np.random.default_rng(SEMILLA + 2)
    a23 = a[a.aceptado & (a.loss_date.dt.year == 2023) & (a.year == 2023)].copy()
    a23["tarde"] = a23.report_date > pd.Timestamp("2023-12-31")
    out = {}
    for l in LINEAS:
        q = b[(b.line == l) & (b.year == 2023)]
        perils = sorted(a[a.line == l].peril.unique())
        pred_ratio, pred_ratio_n = {}, {}
        for p_ in perils:
            c, c1 = q[f"c_{p_}"].values, q[f"c1_{p_}"].values
            n, n1 = q[f"n_{p_}"].values, q[f"n1_{p_}"].values
            pred_ratio[p_] = float(np.sum(q.expo * (c - c1)) / np.sum(q.expo * c1))
            pred_ratio_n[p_] = float(np.sum(q.expo * (n - n1)) / np.sum(q.expo * n1))
        grupos = [("_ramo", perils)] + ([(LARGOS[l], [LARGOS[l]]), ("_resto", [p for p in perils if p != LARGOS[l]])] if l in LARGOS else [])
        for nom, ps in grupos:
            s = a23[(a23.line == l) & a23.peril.isin(ps)]
            pid = s.peril.values; w0 = np.ones(len(s)); neto = s.neto.values; tarde = s.tarde.values
            ratio = np.array([pred_ratio[p] for p in pid]); ratio_n = np.array([pred_ratio_n[p] for p in pid])

            def k(w):
                o1 = w * neto * (~tarde); o2 = w * neto * tarde
                return float(o2.sum() / (o1 * ratio).sum()) if (o1 * ratio).sum() > 0 else np.nan

            def kn(w):
                o1 = w * (~tarde); o2 = w * tarde
                return float(o2.sum() / (o1 * ratio_n).sum()) if (o1 * ratio_n).sum() > 0 else np.nan
            bk = np.array([k(rng.poisson(1.0, len(s)).astype(float)) for _ in range(B_REP)])
            bn = np.array([kn(rng.poisson(1.0, len(s)).astype(float)) for _ in range(B_REP)])
            out[f"{l}|{nom}"] = {"siniestros_2023": int(len(s)), "tardios": int(tarde.sum()), "coste_temprano": r(neto[~tarde].sum(), 2),
                                 "coste_tardio_observado": r(neto[tarde].sum(), 2),
                                 "coste_tardio_previsto": r((neto[~tarde] * ratio[~tarde]).sum(), 2),
                                 "k_e": r(k(w0), 4), "ic90_k_e": q90(bk),
                                 "k_conteos": r(kn(w0), 4), "ic90_k_conteos": q90(bn),
                                 "cuota_tardia_observada": r(neto[tarde].sum() / neto.sum(), 4) if neto.sum() > 0 else None,
                                 "pct_abiertos_tardios": r((s[s.tarde].status == "open").mean(), 4) if tarde.sum() else None}
            print(l, nom, out[f"{l}|{nom}"]["k_e"], out[f"{l}|{nom}"]["ic90_k_e"], out[f"{l}|{nom}"]["k_conteos"], flush=True)
    guardar("parte_c.json", {"definicion": "k_e = coste de 2023 reportado en 2024 / el previsto por la curva de coste del desarrollado dado el coste reportado en 2023 (ambos valorados al 31-12-2024)",
                             "k": out})


# ------------------------------------------------------------------------------------------------ D: del dato al nivel de F3c

LO, HI = 0.75, 1.33


def cadena():
    """Parámetros de la cadena de nivel de F3c: sonda global y sonda por celda (a_s, b_s, c*_s, Z_s), pesos de la mezcla y totales."""
    fi = json.loads((CAD / "final_info_3puntos.json").read_text(encoding="utf-8"))
    pre = json.loads((CAD / "sonda_segmento_preinscripcion.json").read_text(encoding="utf-8"))
    sg = json.loads((CAD / "sonda_global_resultado.json").read_text(encoding="utf-8"))
    bB = pre["base"]["beta_B"]
    b_s = {s: bB * pre["celdas"][s]["cuota_raiz_mu"] for s in CELDAS}
    a_s = {s: fi["nivel"]["c_opt"][s] * b_s[s] for s in CELDAS}
    Z_s = {s: pre["celdas"][s]["Z"] for s in CELDAS}
    test = pd.concat([pd.read_parquet(DAT / f"test_{l}.parquet", columns=["row_id", "new_business"]).assign(line=l) for l in LINEAS])
    test["celda"] = test.line + "_" + test.new_business.astype(bool).astype(int).astype(str)
    cel = test.set_index("row_id").celda
    tot = {}
    for nom, f in (("F3c", "F3c_2025.csv"), ("F3d", "F3d_2025.csv"), ("mezcla", "mezcla50_designada_mlind_2025.csv"),
                   ("designada", "A1fixF1b3n_2025.csv"), ("mlind", "prediccion_2025_mlind.csv"), ("F", "final_sonda_global_2025.csv")):
        x = pd.read_csv(CAD / f, dtype={"row_id": str})
        x["celda"] = x.row_id.map(cel)
        assert x.celda.notna().all() and len(x) == 209063
        tot[nom] = x.groupby("celda").prediction.sum().to_dict()
    wD = {l: tot["designada"][f"{l}_0"] + tot["designada"][f"{l}_1"] for l in LINEAS}
    wM = {l: tot["mlind"][f"{l}_0"] + tot["mlind"][f"{l}_1"] for l in LINEAS}
    w_des = {l: wD[l] / (wD[l] + wM[l]) for l in LINEAS}
    return {"a_s": a_s, "b_s": b_s, "c_s": dict(fi["nivel"]["c_opt"]), "Z_s": Z_s, "Z_g": sg["Z"], "c_g_publicado": sg["c_optimo_publico_exacto"],
            "w_designada": w_des, "totales": tot}


def factor_celdas(rho: dict, P: dict, Zg=None):
    """Factor final de cada celda relativo a la mezcla con un nivel base ρ_s por celda y los óptimos públicos fijos en nivel absoluto."""
    Zg = P["Z_g"] if Zg is None else Zg
    A = sum(P["a_s"][s] * rho[s] ** -0.5 for s in CELDAS)
    B = sum(P["b_s"][s] * rho[s] ** 0.5 for s in CELDAS)
    cg = A / B
    g = float(np.clip(cg ** Zg, LO, HI))
    return {s: rho[s] * g * float(np.clip((P["c_s"][s] / rho[s] / cg) ** P["Z_s"][s], LO, HI)) for s in CELDAS}


def nivel_ramos(rho: dict, P: dict, Zg=None, modelo="F3c"):
    f1, f = factor_celdas({s: 1.0 for s in CELDAS}, P, Zg), factor_celdas(rho, P, Zg)
    T = P["totales"][modelo]
    out = {}
    for l in LINEAS:
        cs = [f"{l}_0", f"{l}_1"]
        out[l] = sum(T[c] * f[c] / f1[c] for c in cs) / sum(T[c] for c in cs) - 1.0
    out.update({c: f[c] / f1[c] - 1.0 for c in CELDAS})
    return out


class Base:
    """Nivel base de la mezcla por ramo con las etiquetas de un escenario: designada por balance, línea ML por escalar Tweedie.
    Las dos fórmulas son lineales en y, así que el escenario b es exactamente lineal en b; el escenario k se calcula fila a fila."""

    def __init__(self, P):
        b = pd.read_parquet(RES / "base_filas.parquet")
        a = pd.read_parquet(RES / "siniestros_asignados.parquet", columns=["line", "peril"])
        self.P = P
        self.perils = {l: sorted(a[a.line == l].peril.unique()) for l in LINEAS}
        self.d = {}
        for l in LINEAS:
            q = b[b.line == l]
            dd = {"y": q.y.values, "m": q.m.values, "mu": q.mu.values, "expo": q.expo.values, "y2024": (q.year.values == 2024),
                  "R": {p: q[f"R_{p}"].fillna(0).values for p in self.perils[l]}, "c": {p: q[f"c_{p}"].values for p in self.perils[l]}}
            ult = {p: q[f"y_{p}"].sum() / max(np.average(q[f"c_{p}"], weights=q.expo), 1e-6) for p in self.perils[l]}
            tot = sum(ult.values())
            dd["wp"] = {p: ult[p] / tot for p in self.perils[l]}
            self.d[l] = dd

    def pendientes(self, l, peligros=None, solo_2024=False):
        dd = self.d[l]
        ps = self.perils[l] if peligros is None else peligros
        dR = sum(dd["R"][p] for p in ps)
        if solo_2024:
            dR = dR * dd["y2024"]
        y, m = dd["y"], dd["m"]
        s_des = dR.sum() / y.sum()
        s_ml = np.sum(dR / np.sqrt(m)) / np.sum(y / np.sqrt(m))
        return s_des, s_ml

    def rho(self, l, b=1.0, k=1.0, peligros=None, solo_2024=False, peso_des=None):
        dd = self.d[l]
        w = self.P["w_designada"][l] if peso_des is None else peso_des
        ps = self.perils[l] if peligros is None else peligros
        if k == 1.0:
            s_des, s_ml = self.pendientes(l, peligros, solo_2024)
            r_des, r_ml = 1 + (b - 1) * s_des, 1 + (b - 1) * s_ml
            return w * r_des + (1 - w) * r_ml, r_des, r_ml
        cf = np.zeros(len(dd["y"]))
        for p in self.perils[l]:
            c = dd["c"][p]
            if p in ps:
                c = c / (c + k * (1 - c))
            cf = cf + dd["wp"][p] * c
        m0 = dd["m"]; m = dd["mu"] * cf; y = dd["y"]
        if b != 1.0:
            y = y + (b - 1) * sum(dd["R"][p] for p in ps)
        r_des = (y.sum() / m.sum()) / (dd["y"].sum() / m0.sum())
        r_ml = ftw(y, m) / ftw(dd["y"], m0)
        return w * r_des + (1 - w) * r_ml, r_des, r_ml


def umbral(fun, lado):
    """Primer cruce desde 1 de |fun(x)| = MAT: rejilla de paso 0,0025 hasta 3 (o 0,0025 hacia 0) y 0,05 hasta 20, afinado por bisección."""
    if lado > 0:
        grid = np.concatenate([np.arange(1.0, 3.0 + 1e-9, 0.0025), np.arange(3.05, 20.0 + 1e-9, 0.05)])
    else:
        grid = np.arange(1.0, 0.0, -0.0025)
    prev = grid[0]
    for x in grid[1:]:
        if abs(fun(x)) >= MAT:
            lo, hi = prev, x
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if abs(fun(mid)) >= MAT:
                    hi = mid
                else:
                    lo = mid
            return r(hi, 6)
        prev = x
    return None


def clase(ic, u):
    """Regla de la semana 1: acotado si el intervalo queda dentro del intervalo de quiebre, indicio si queda entero fuera,
    incertidumbre material si lo cruza. Un umbral ausente significa que no hay cruce en la rejilla (sin límite por ese lado)."""
    if ic is None or ic[0] is None or ic[1] is None:
        return "sin_estimacion"
    lo = -np.inf if u[0] is None else u[0]
    hi = np.inf if u[1] is None else u[1]
    if ic[0] >= lo and ic[1] <= hi:
        return "acotado"
    if ic[1] < lo or ic[0] > hi:
        return "indicio_de_desvio_material"
    return "incertidumbre_material"


def etapa_d():
    P = cadena()
    B = Base(P)
    pb = leer("parte_b.json")["beta"]; pc = leer("parte_c.json")["k"]
    f1 = factor_celdas({s: 1.0 for s in CELDAS}, P)
    control = {"factor_celda_reconstruido": {s: r(f1[s], 6) for s in CELDAS},
               "cred_publicado": json.loads((CAD / "final_info_3puntos.json").read_text(encoding="utf-8"))["nivel"]["cred"]}
    control["max_dif_relativa"] = r(max(abs(f1[s] / control["cred_publicado"][s] - 1) for s in CELDAS), 9)
    # elasticidades analíticas en ρ = 1
    A = sum(P["a_s"].values()); Bs = sum(P["b_s"].values())
    elas = {}
    for l in LINEAS:
        w_r = 0.5 * sum(P["a_s"][s] / A + P["b_s"][s] / Bs for s in (f"{l}_0", f"{l}_1"))
        elas[l] = {"w_r": r(w_r, 4), **{s: r((1 - P["Z_s"][s]) + (P["Z_s"][s] - P["Z_g"]) * w_r, 4) for s in (f"{l}_0", f"{l}_1")},
                   "otras_celdas": r(-(P["Z_g"] - np.mean([P["Z_s"][s] for s in CELDAS])) * w_r, 4)}
    elas["uniforme"] = r(1 - P["Z_g"], 4)
    out = {"control": control, "elasticidad_analitica": elas, "pesos_designada": {l: r(v, 4) for l, v in P["w_designada"].items()},
           "totales_F3c_celda": {s: r(v, 2) for s, v in P["totales"]["F3c"].items()}, "escenarios": {}}

    def efecto(l, rho_r, Zg=None, modelo="F3c"):
        rho = {s: (rho_r if s.startswith(l) else 1.0) for s in CELDAS}
        return nivel_ramos(rho, P, Zg, modelo)

    escenarios = []
    for l in LINEAS:
        escenarios.append((l, "b", None, "ramo"))
        if l in LARGOS:
            escenarios.append((l, "b", [LARGOS[l]], "largo"))
            escenarios.append((l, "b", [p for p in B.perils[l] if p != LARGOS[l]], "resto"))
        escenarios.append((l, "k", None, "ramo"))
        if l in LARGOS:
            escenarios.append((l, "k", [LARGOS[l]], "largo"))
    for l, tipo, ps, nom in escenarios:
        def base(x, **kw):
            return B.rho(l, b=x, peligros=ps, **kw)[0] if tipo == "b" else B.rho(l, k=x, peligros=ps, **kw)[0]

        fila = {}
        fila["umbral_F3c"] = [umbral(lambda x: efecto(l, base(x))[l], -1), umbral(lambda x: efecto(l, base(x))[l], +1)]
        fila["umbral_mezcla"] = [umbral(lambda x: base(x) - 1, -1), umbral(lambda x: base(x) - 1, +1)]
        for c_ in (f"{l}_0", f"{l}_1"):
            fila[f"umbral_celda_{c_}"] = [umbral(lambda x: efecto(l, base(x))[c_], -1), umbral(lambda x: efecto(l, base(x))[c_], +1)]
        for x in (0.75, 1.25):
            rr, rd, rm = (B.rho(l, b=x, peligros=ps) if tipo == "b" else B.rho(l, k=x, peligros=ps))
            fila[f"en_{x}"] = {"rho_mezcla": r(rr - 1, 5), "rho_designada": r(rd - 1, 5), "rho_mlind": r(rm - 1, 5),
                               "F3c_ramo": r(efecto(l, rr)[l], 5), **{f"F3c_{c_}": r(efecto(l, rr)[c_], 5) for c_ in (f"{l}_0", f"{l}_1")}}
        # variantes D5
        fila["variantes"] = {
            "Zg_0.90": [umbral(lambda x: efecto(l, base(x), 0.90)[l], -1), umbral(lambda x: efecto(l, base(x), 0.90)[l], +1)],
            "solo_designada": [umbral(lambda x: efecto(l, base(x, peso_des=1.0))[l], -1), umbral(lambda x: efecto(l, base(x, peso_des=1.0))[l], +1)],
            "solo_mlind": [umbral(lambda x: efecto(l, base(x, peso_des=0.0))[l], -1), umbral(lambda x: efecto(l, base(x, peso_des=0.0))[l], +1)]}
        if tipo == "b":
            fila["variantes"]["solo_2024"] = [umbral(lambda x: efecto(l, base(x, solo_2024=True))[l], -1), umbral(lambda x: efecto(l, base(x, solo_2024=True))[l], +1)]
        # clasificación
        if tipo == "b":
            kb = f"{l}|_ramo" if nom == "ramo" else (f"{l}|{LARGOS[l]}" if nom == "largo" else f"{l}|_resto")
            ic = pb.get(kb, {}).get("ic90")
            fila["beta"] = {"clave": kb, "puntual": pb.get(kb, {}).get("beta"), "ic90": ic}
            fila["clase_F3c"] = clase(ic, fila["umbral_F3c"])
            fila["clase_mezcla_sin_sondas"] = clase(ic, fila["umbral_mezcla"])
            if pb.get(kb, {}).get("beta") is not None:
                bp = pb[kb]["beta"]
                fila["F3c_con_beta_puntual"] = r(efecto(l, base(bp))[l], 5)
            ag = pb.get(kb, {}).get("agrupado_secundario")
            if ag:
                fila["clase_F3c_beta_agrupado_secundario"] = clase(ag["ic90"], fila["umbral_F3c"])
            for vn, u in fila["variantes"].items():
                fila["variantes"][vn] = {"umbral": u, "clase": clase(ic, u)}
        else:
            kk = f"{l}|_ramo" if nom == "ramo" else f"{l}|{LARGOS[l]}"
            ic = pc.get(kk, {}).get("ic90_k_e")
            fila["k_e"] = {"clave": kk, "puntual": pc.get(kk, {}).get("k_e"), "ic90": ic}
            fila["clase_F3c"] = clase(ic, fila["umbral_F3c"])
            fila["clase_mezcla_sin_sondas"] = clase(ic, fila["umbral_mezcla"])
            if pc.get(kk, {}).get("k_e") is not None:
                fila["F3c_con_k_e_puntual"] = r(efecto(l, base(pc[kk]["k_e"]))[l], 5)
                fila["mezcla_con_k_e_puntual"] = r(base(pc[kk]["k_e"]) - 1, 5)
            for vn, u in fila["variantes"].items():
                fila["variantes"][vn] = {"umbral": u, "clase": clase(ic, u)}
        out["escenarios"][f"{l}|{tipo}|{nom}"] = fila
        print(l, tipo, nom, fila["umbral_mezcla"], fila["umbral_F3c"], fila.get("clase_F3c"), flush=True)
    # ilustración (no preinscrita como clase): b uniforme en los tres ramos
    def uni(x):
        rho = {}
        for l in LINEAS:
            rr = B.rho(l, b=x)[0]
            rho.update({f"{l}_0": rr, f"{l}_1": rr})
        return nivel_ramos(rho, P)
    out["ilustracion_b_uniforme"] = {str(x): {k_: r(v, 5) for k_, v in uni(x).items()} for x in (0.75, 1.25)}
    # F3d: mismo análisis de nivel con sus totales (solo cambia contenidos)
    out["F3d_contenidos"] = {"umbral_b": [umbral(lambda x: nivel_ramos({s: (B.rho("contents", b=x)[0] if s.startswith("contents") else 1.0) for s in CELDAS}, P, None, "F3d")["contents"], -1),
                                          umbral(lambda x: nivel_ramos({s: (B.rho("contents", b=x)[0] if s.startswith("contents") else 1.0) for s in CELDAS}, P, None, "F3d")["contents"], +1)]}
    guardar("parte_d.json", out)


# ------------------------------------------------------------------------------------------------ E: estructura

def a_optimo(y, e, r_, grid=np.arange(0.70, 1.301, 0.0025)):
    g = np.exp(np.average(np.log(r_), weights=e))
    dev = []
    for a in grid:
        ma = e * g * (r_ / g) ** a
        ma = ma * ftw(y, ma)
        dev.append(desv(y, ma).sum())
    dev = np.array(dev); i = int(np.argmin(dev))
    if 0 < i < len(grid) - 1:  # vértice de la parábola por los tres puntos alrededor del mínimo
        x0, x1, x2 = grid[i - 1:i + 2]; d0, d1, d2 = dev[i - 1:i + 2]
        den = (d0 - 2 * d1 + d2)
        a_star = x1 + 0.5 * (x2 - x1) * (d0 - d2) / den if den > 0 else x1
    else:
        a_star = grid[i]
    return float(a_star)


def d2_forma(y, e, r_, a):
    g = np.exp(np.average(np.log(r_), weights=e))
    ma = e * g * (r_ / g) ** a
    ma = ma * ftw(y, ma)
    return 1 - desv(y, ma).sum() / desv(y, np.full_like(y, y.mean())).sum()


def etapa_e():
    b = pd.read_parquet(RES / "base_filas.parquet")
    pb = leer("parte_b.json")["beta"]
    out = {"E1_emergente": {}, "E2_desarrollado": {}, "E3_factores": {}}
    for l in LINEAS:
        q = b[b.line == l]
        e = (q.expo * q.c_fila).values; r_ = (q.mu / q.expo).values; y0 = q.y.values; R = q.R.values
        a1 = a_optimo(y0, e, r_)
        ic = pb[f"{l}|_ramo"]["ic90"]
        fila = {"a_T0": r(a1, 4), "d2_en_a_T0": r(d2_forma(y0, e, r_, a1), 6)}
        for x in sorted(set([0.75, 1.25] + [v for v in ic if v is not None])):
            y = y0 + (x - 1) * R
            ab = a_optimo(y, e, r_)
            fila[f"b_{x}"] = {"a": r(ab, 4), "delta_a": r(ab - a1, 4), "coste_D2_con_T0": r(d2_forma(y0, e, r_, a1) - d2_forma(y0, e, r_, ab), 7)}
        # cuota de reserva por decil de la tasa predicha (lectura comparable con E2)
        dec = pd.qcut(r_, 10, labels=False, duplicates="drop")
        g = pd.DataFrame({"d": dec, "y": y0, "R": R, "m": q.m.values}).groupby("d").sum()
        fila["cuota_reserva_por_decil"] = [r(v, 4) for v in (g.R / g.y).values]
        x_ = np.log(g.m.values); z = g.R.values / g.y.values
        fila["pendiente_cuota_vs_log_pred"] = r(np.polyfit(x_, z, 1)[0], 4)
        out["E1_emergente"][l] = fila
        print("E1", l, fila["a_T0"], {k_: v for k_, v in fila.items() if k_.startswith("b_")}, flush=True)
    # E2: desarrollado V24 de S30 (semana 1): sin exposición en el archivo, se mide la cuota de reserva por decil de la predicción
    s30 = pd.read_parquet(S1 / "predicciones_v23_v24_s30.parquet")
    s30 = s30[s30.corte == "V24"]
    for l in LINEAS:
        q = s30[s30.line == l]
        dec = pd.qcut(q.prediction.values, 10, labels=False, duplicates="drop")
        g = pd.DataFrame({"d": dec, "y": q.y_T0.values, "R": q.reserva_caso.values, "m": q.prediction.values}).groupby("d").sum()
        z = g.R.values / g.y.values
        fila = {"cuota_reserva_por_decil": [r(v, 4) for v in z], "cuota_total": r(q.reserva_caso.sum() / q.y_T0.sum(), 4),
                "pendiente_cuota_vs_log_pred": r(np.polyfit(np.log(g.m.values), z, 1)[0], 4)}
        for x in (0.75, 1.25):
            ae = (1 + (x - 1) * z)  # cambio del A/E de cada decil
            fila[f"b_{x}"] = {"pendiente_log_AE_vs_log_pred": r(np.polyfit(np.log(g.m.values), np.log(ae), 1)[0], 4)}
        out["E2_desarrollado"][l] = fila
        print("E2", l, fila["cuota_total"], fila["pendiente_cuota_vs_log_pred"], fila["b_0.75"], fila["b_1.25"], flush=True)
    # E3: factores de F2 y F3c: cuota de reserva de cada nivel (pesos 1/√m) frente a su grupo
    vars_ = [("motor", "ncb_banda", True, "F2"), ("motor", "previos", True, "F2"), ("buildings", "previos", True, "F2"), ("contents", "previos", True, "F2"),
             ("motor", "gender", False, "F3c"), ("contents", "gender", False, "F3c"), ("contents", "wfh", False, "F3c"), ("contents", "marketing_segment", False, "F3c")]
    K = 300.0
    for l, v, por_celda, paso in vars_:
        q = b[b.line == l].copy()
        ic = pb[f"{l}|_ramo"]["ic90"]
        grupos = q.groupby("celda") if por_celda else [(l, q)]
        res = {}
        for gname, gq in grupos:
            w = 1 / np.sqrt(gq.m.values)
            r_ref = float(np.sum(w * gq.R.values) / np.sum(w * gq.y.values))
            r_ref_bal = float(gq.R.sum() / gq.y.sum())
            niveles = {}
            for lv, h in gq.groupby(v):
                wh = 1 / np.sqrt(h.m.values)
                yv = float(np.sum(wh * h.y.values))
                if yv <= 0:
                    continue
                rv = float(np.sum(wh * h.R.values) / yv)
                rv_bal = float(h.R.sum() / h.y.sum())
                n = int((h.y.values > 0).sum()); Zv = n / (n + K)
                cambios = {str(x): r(np.log((1 + (x - 1) * rv) / (1 + (x - 1) * r_ref)), 5) for x in ic if x is not None}
                cambios_cred = {str(x): r(Zv * np.log((1 + (x - 1) * (rv_bal if paso == "F2" else rv)) / (1 + (x - 1) * (r_ref_bal if paso == "F2" else r_ref))), 5)
                                for x in ic if x is not None}
                niveles[str(lv)] = {"cuota_reserva": r(rv, 4), "cuota_reserva_balance": r(rv_bal, 4), "filas": int(len(h)), "filas_con_coste": n, "Z_credibilidad": r(Zv, 4),
                                    "cambio_log_factor_en_ic_beta": cambios, "cambio_log_factor_con_credibilidad_no_preinscrito": cambios_cred}
            mx = max((abs(c) for n_ in niveles.values() for c in n_["cambio_log_factor_en_ic_beta"].values() if c is not None), default=None)
            mxc = max((abs(c) for n_ in niveles.values() for c in n_["cambio_log_factor_con_credibilidad_no_preinscrito"].values() if c is not None), default=None)
            res[gname] = {"paso": paso, "cuota_reserva_grupo": r(r_ref, 4), "niveles": niveles, "max_abs_cambio_log_factor": r(mx, 5),
                          "max_abs_cambio_log_factor_con_credibilidad_no_preinscrito": r(mxc, 5)}
        out["E3_factores"][f"{l}|{v}"] = res
        print("E3", l, v, {k_: (vv["max_abs_cambio_log_factor"], vv["max_abs_cambio_log_factor_con_credibilidad_no_preinscrito"]) for k_, vv in res.items()}, flush=True)
    guardar("parte_e.json", out)


# ------------------------------------------------------------------------------------------------ F: coste en la métrica

def etapa_f():
    P = cadena()
    T = P["totales"]
    out = {"nota": "forma cerrada por celda con a_s y b_s de la sonda por celda, en unidades de la mezcla; el nivel de F3c en cada celda se aproxima por el cociente de totales F3c/mezcla, y su cambio de forma dentro de la celda no se modela",
           "nivel_F3c_rel_mezcla": {}, "por_ramo": {}}
    Lr = {s: T["F3c"][s] / T["mezcla"][s] for s in CELDAS}
    out["nivel_F3c_rel_mezcla"] = {s: r(v, 4) for s, v in Lr.items()}
    for l in LINEAS:
        fila = {}
        for c in (0.99, 1.01):
            d = -sum(P["a_s"][s] * Lr[s] ** -0.5 * (c ** -0.5 - 1) + P["b_s"][s] * Lr[s] ** 0.5 * (c ** 0.5 - 1) for s in (f"{l}_0", f"{l}_1"))
            fila[str(c)] = r(d, 7)
        out["por_ramo"][l] = fila
    out["tres_ramos"] = {}
    for c in (0.99, 1.01):
        d = -sum(P["a_s"][s] * Lr[s] ** -0.5 * (c ** -0.5 - 1) + P["b_s"][s] * Lr[s] ** 0.5 * (c ** 0.5 - 1) for s in CELDAS)
        out["tres_ramos"][str(c)] = r(d, 7)
    out["codex_citado"] = {"PUL2_frente_G3": {"R075_C": 0.00250519, "R125_C": 0.00264151, "R075_V": 0.00262017, "R125_V": 0.00252881, "TAIL005": 0.00259096, "TAIL010": 0.00256596,
                                              "fuente": "COD-S2-20261026-MISION017-PUL2-OBS-STRESS-RESULTADO; privado/semana2/mision017_fase2/sensibilidad_observacion_PUL2_20261026_v2/report.json"},
                           "nivel_2023_R075_R125_B14": {"nominal": [-0.02484, 0.02483], "fuente": "Repositorio_IAA2026/docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md"}}
    guardar("parte_f.json", out)
    print(json.dumps(out["por_ramo"]), out["tres_ramos"])


# ------------------------------------------------------------------------------------------------ G: lecturas no preinscritas

def etapa_g():
    """Lecturas añadidas después de ver los resultados de B a F; se declaran como no preinscritas."""
    a = pd.read_parquet(RES / "siniestros_asignados.parquet")
    b = pd.read_parquet(RES / "base_filas.parquet")
    pb = leer("parte_b.json")["beta"]; pc = leer("parte_c.json")["k"]
    P = cadena(); B = Base(P)
    out = {}
    # G1: k_e de lesiones si la reserva de los tardíos abiertos se escalara por el β emergente de lesiones
    a23 = a[a.aceptado & (a.loss_date.dt.year == 2023) & (a.year == 2023) & (a.line == "motor") & (a.peril == "bodily_injury")].copy()
    tarde = a23.report_date > pd.Timestamp("2023-12-31")
    bbi = pb["motor|bodily_injury"]["beta"]
    neto_aj = a23.neto - (1 - bbi) * a23.reserva
    o1 = a23.neto[~tarde].sum(); o2 = a23.neto[tarde].sum(); o1a = neto_aj[~tarde].sum(); o2a = neto_aj[tarde].sum()
    ratio = pc["motor|bodily_injury"]["coste_tardio_previsto"] / pc["motor|bodily_injury"]["coste_temprano"]
    out["G1_k_e_lesiones_con_reserva_por_beta"] = {"beta_lesiones": bbi, "k_e_publicado": pc["motor|bodily_injury"]["k_e"],
                                                   "k_e_ajustado": r(o2a / (o1a * ratio), 4), "coste_tardio_ajustado": r(o2a, 2), "coste_temprano_ajustado": r(o1a, 2)}
    # G2: escenario central: β puntual y k_e puntual a la vez, por ramo
    cen = {}
    for l in LINEAS:
        bp = pb[f"{l}|_ramo"]["beta"]; kp = pc[f"{l}|_ramo"]["k_e"]
        rr = B.rho(l, b=bp, k=kp)[0]
        rho = {s: (rr if s.startswith(l) else 1.0) for s in CELDAS}
        cen[l] = {"beta": bp, "k_e": kp, "nivel_mezcla": r(rr - 1, 5), "nivel_F3c": r(nivel_ramos(rho, P)[l], 5)}
    rho = {}
    for l in LINEAS:
        rr = B.rho(l, b=pb[f"{l}|_ramo"]["beta"], k=pc[f"{l}|_ramo"]["k_e"])[0]
        rho.update({f"{l}_0": rr, f"{l}_1": rr})
    conj = nivel_ramos(rho, P)
    out["G2_escenario_central"] = {"por_ramo_aislado": cen, "tres_ramos_a_la_vez": {k_: r(v, 5) for k_, v in conj.items()}}
    # G3: recobros y rechazados llevados al nivel de F3c (los mismos pasos que b)
    pa = leer("parte_a.json")
    g3 = {}
    for l in LINEAS:
        T0l = float(b[b.line == l].y.sum())
        for nom, cuota, signo in (("recobros", pa["recobros"][l]["sobre_T0"], -1), ("rechazados_pagados", pa["rechazados"][l]["sobre_T0"], +1)):
            rr = 1 + signo * (cuota or 0.0)  # aproximación de balance: el cambio relativo de T0 del ramo
            rho = {s: (rr if s.startswith(l) else 1.0) for s in CELDAS}
            g3[f"{l}|{nom}"] = {"cambio_T0": r(signo * (cuota or 0.0), 4), "nivel_F3c": r(nivel_ramos(rho, P)[l], 5)}
    out["G3_recobros_y_rechazados_en_F3c"] = g3
    guardar("parte_g.json", {"nota": "lecturas no preinscritas, añadidas después de ver B a F", **out})
    print(json.dumps(out, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    et = sys.argv[2] if len(sys.argv) > 2 else "todas"
    for nombre, f in (("datos", etapa_datos), ("a", etapa_a), ("b", etapa_b), ("c", etapa_c), ("d", etapa_d), ("e", etapa_e), ("f", etapa_f), ("g", etapa_g)):
        if et in (nombre, "todas"):
            f()
