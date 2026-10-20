"""Acotación de reservas con una sola valoración: pruebas de consistencia y umbrales de quiebre.

El plan, los supuestos y los criterios están fijados en <corrida>/PLAN_PREREGISTRO.md antes de calcular. Nada de lo que
hace este script demuestra suficiencia: estima el sesgo de la reserva de caso bajo un supuesto escrito (S1), comprueba lo
que S1 implica en los datos y mide cuánto sesgo movería el nivel 2025 de cada ramo más allá de la materialidad (1 %) o
invertiría el orden S30 frente a S22. Tampoco cambia T0, la receta ni ninguna predicción.

Uso: python3 herramientas/reservas_consistencia.py <carpeta_corrida> [datos|a|b|resumen]
Sin etapa ejecuta todas. Cada etapa escribe en <corrida>/resultados/ y la siguiente lee de ahí (cada orden cabe en unos
minutos en la máquina virtual del participante: Python 3.10, pandas 2.3, pyarrow 25).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
S1 = REPO.parent / "Semana 1"
CLAIMS = S1 / "Limpieza" / "runs" / "preaudit_20261016T211816Z_817285a5" / "data" / "claims.parquet"
BASES = S1 / "Bases_actuariales_claude" / "runs" / "bases_20261017T120251Z_45443ff0" / "tables"
PRED = {"S30": S1 / "Modelos_claude_b" / "experimentos" / "predicciones_v23_v24_s30.parquet",
        "S22": S1 / "Modelos_claude" / "experimentos" / "predicciones_v23_v24_s22.parquet"}
RESUMEN_S30 = S1 / "Modelos_claude_b" / "runs" / "S30_claude_b" / "resumen.json"
LINES = ["motor", "buildings", "contents"]
PERILS = {"motor": ["own_damage", "third_party_prop", "bodily_injury", "theft", "glass_hail"],
          "buildings": ["storm", "flood", "escape_of_water", "subsidence", "fire", "accidental_damage"],
          "contents": ["theft", "escape_of_water", "accidental_damage", "flood"]}
LARGOS = {"motor": "bodily_injury", "buildings": "subsidence"}
VALORACION = pd.Timestamp("2024-12-31")
MATERIALIDAD = 0.01
B_REPLICAS = 400
SEMILLA = 20261019
MIN_CERRADOS = 20
P = 1.5


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def r(x, n=6):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def guardar(run: Path, nombre: str, obj):
    (run / "resultados").mkdir(parents=True, exist_ok=True)
    (run / "resultados" / nombre).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


def leer(run: Path, nombre: str):
    return json.loads((run / "resultados" / nombre).read_text(encoding="utf-8"))


def deviance(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    return 2.0 * (np.power(y, 2 - P) / ((1 - P) * (2 - P)) - y * np.power(mu, 1 - P) / (1 - P) + np.power(mu, 2 - P) / (2 - P))


def d2(y, mu):
    y = np.asarray(y, float)
    return float(1.0 - deviance(y, mu).sum() / deviance(y, np.full_like(y, y.mean())).sum())


def ftw(y, mu):
    s = np.sqrt(np.asarray(mu, float))
    return float((np.asarray(y, float) / s).sum() / s.sum())


# ------------------------------------------------------------------------------------------------ datos

def etapa_datos(run: Path):
    fuentes = {str(p.relative_to(REPO.parent)): sha(p) for p in
               [CLAIMS, BASES / "asignacion_por_siniestro.parquet", BASES / "t0_por_row_id.parquet", BASES / "ibnr_por_peligro_anio.csv",
                BASES / "ibnr_2024_por_peligro.csv", PRED["S30"], PRED["S22"], RESUMEN_S30]}
    c = pd.read_parquet(CLAIMS, columns=["claim_id", "status", "paid_to_date", "incurred_to_date", "recoveries", "audit_pre00"])
    a = pd.read_parquet(BASES / "asignacion_por_siniestro.parquet", columns=["claim_id", "line", "peril", "loss_date", "report_date", "category", "row_id"])
    m = a.merge(c, on="claim_id", how="left", validate="one_to_one")
    m["unica"] = (m.category == "unica") & (~m.audit_pre00.fillna(False).astype(bool)) & m.row_id.notna()
    t0 = pd.read_parquet(BASES / "t0_por_row_id.parquet", columns=["row_id", "line", "year", "T0", "reserve", "exposure"])
    t0["row_id"] = t0.row_id.astype(str)
    m["row_id"] = m.row_id.astype(str)
    m = m.merge(t0[["row_id", "year"]].rename(columns={"year": "anio_periodo"}), on="row_id", how="left")
    m["reserva"] = np.where(m.status == "open", m.incurred_to_date - m.paid_to_date, 0.0)
    m["neto"] = m.incurred_to_date - m.recoveries
    m["anio_ocurrencia"] = pd.to_datetime(m.loss_date).dt.year
    m["report_date"] = pd.to_datetime(m.report_date)
    m["loss_date"] = pd.to_datetime(m.loss_date)
    m.drop(columns=["audit_pre00"]).to_parquet(run / "resultados" / "siniestros.parquet", index=False)
    acc = m[m.unica & m.status.isin(["open", "closed"])]
    # controles: la reserva por fila coincide con la de T0 y la de las predicciones exportadas
    rf = acc.groupby("row_id").reserva.sum()
    t0r = t0.set_index("row_id").reserve
    comun = rf.index.intersection(t0r.index)
    ctrl = {"aceptados_unicos": int(len(acc)), "abiertos": int((acc.status == "open").sum()), "cerrados": int((acc.status == "closed").sum()),
            "reserva_total": r(acc.reserva.sum(), 2), "reserva_t0_total": r(t0.reserve.sum(), 2),
            "max_dif_reserva_por_fila_frente_a_t0": r(float(np.abs(rf.reindex(comun) - t0r.reindex(comun)).max()), 6),
            "abiertos_sin_reserva": int(((acc.status == "open") & (acc.reserva <= 0)).sum()),
            "cerrados_con_reserva": int(((acc.status == "closed") & (acc.incurred_to_date != acc.paid_to_date)).sum()),
            "rechazados_unicos": int((m.unica & (m.status == "repudiated")).sum()),
            "rechazados_con_importe": int((m.unica & (m.status == "repudiated") & ((m.incurred_to_date != 0) | (m.paid_to_date != 0))).sum())}
    # totales por ramo y año de periodo: T0, reserva por peligro; IBNR por peligro y año de ocurrencia (D67)
    t0y = t0[t0.year <= 2024].groupby(["line", "year"]).agg(T0=("T0", "sum"), reserva=("reserve", "sum"), expuestos=("exposure", "sum")).reset_index()
    rp = acc[acc.status == "open"].groupby(["line", "anio_periodo", "peril"]).reserva.sum().reset_index()
    ib = pd.read_csv(BASES / "ibnr_por_peligro_anio.csv")
    tot = {}
    for line in LINES:
        tot[line] = {}
        for y in range(2021, 2025):
            row = t0y[(t0y.line == line) & (t0y.year == y)].iloc[0]
            res_p = {p: float(rp[(rp.line == line) & (rp.anio_periodo == y) & (rp.peril == p)].reserva.sum()) for p in PERILS[line]}
            ibn_p = {p: float(ib[(ib.line == line) & (ib.year == y) & (ib.peril == p)].ibnr_coste_CU.sum()) for p in PERILS[line]}
            tot[line][str(y)] = {"T0": float(row.T0), "reserva": float(row.reserva), "reserva_por_peligro": res_p, "ibnr_por_peligro": ibn_p,
                                 "ibnr": float(sum(ibn_p.values())), "ultimo_supuesto": float(row.T0 + sum(ibn_p.values())), "expuestos": float(row.expuestos)}
    # reserva por fila y peligro para las filas de V23 selección y V24
    rfp = acc[acc.status == "open"].pivot_table(index="row_id", columns="peril", values="reserva", aggfunc="sum", fill_value=0.0)
    rfp.columns = [f"res_{p}" for p in rfp.columns]
    rfp.reset_index().to_parquet(run / "resultados" / "reserva_fila_peligro.parquet", index=False)
    guardar(run, "datos.json", {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fuentes_sha256": fuentes, "controles": ctrl, "totales": tot})
    print(json.dumps(ctrl, ensure_ascii=False))


# ------------------------------------------------------------------------------------------------ parte A

def _celdas(d: pd.DataFrame):
    d = d.copy()
    d["celda"] = d.report_date.dt.to_period("Q").astype(str)
    return d


def _prep_beta(d: pd.DataFrame):
    g = pd.factorize(d.celda.values)[0]
    return {"g": g, "ng": int(g.max()) + 1 if len(g) else 0, "ab": (d.status == "open").values,
            "inc": d.incurred_to_date.values.astype(float), "paid": d.paid_to_date.values.astype(float)}


def _beta(z: dict, w=None):
    """beta = reserva implícita bajo S1 / reserva contabilizada; b = incurrido de abiertos / incurrido implícito.
    La reserva implícita de una celda es abiertos x incurrido medio de los cerrados de la celda menos lo ya pagado
    en los abiertos; solo cuentan celdas con al menos MIN_CERRADOS cerrados."""
    w = np.ones(len(z["g"])) if w is None else w
    g, ab, ng = z["g"], z["ab"], z["ng"]
    wc = np.bincount(g[~ab], weights=w[~ab], minlength=ng)
    ic = np.bincount(g[~ab], weights=(w * z["inc"])[~ab], minlength=ng)
    wo = np.bincount(g[ab], weights=w[ab], minlength=ng)
    io = np.bincount(g[ab], weights=(w * z["inc"])[ab], minlength=ng)
    po = np.bincount(g[ab], weights=(w * z["paid"])[ab], minlength=ng)
    ok = (wc >= MIN_CERRADOS) & (wo > 0)
    implicito = float((wo[ok] * ic[ok] / wc[ok]).sum())
    inc_ab, pag_ab = float(io[ok].sum()), float(po[ok].sum())
    reserva = inc_ab - pag_ab
    beta = (implicito - pag_ab) / reserva if reserva > 0 else np.nan
    return {"beta_reserva": beta, "b_incurrido": inc_ab / implicito if implicito > 0 else np.nan, "reserva_cubierta": reserva,
            "implicito": implicito, "celdas": int(ok.sum())}


def _boot(z: dict, rng):
    vals = np.array([_beta(z, rng.poisson(1.0, size=len(z["g"])).astype(float))["beta_reserva"] for _ in range(B_REPLICAS)], float)
    vals = vals[np.isfinite(vals)]
    return [r(np.quantile(vals, 0.05), 4), r(np.quantile(vals, 0.95), 4)] if len(vals) > 20 else [None, None]


def etapa_a(run: Path, solo=None):
    m = pd.read_parquet(run / "resultados" / "siniestros.parquet")
    acc = _celdas(m[m.unica & m.status.isin(["open", "closed"])])
    rng = np.random.default_rng(SEMILLA)
    out = leer(run, "parte_a.json") if (run / "resultados" / "parte_a.json").exists() else {}
    for line in LINES:
        if solo and line not in solo:
            continue
        res_line = {"peligros": {}}
        dl = acc[acc.line == line]
        reserva_total = float(dl[dl.status == "open"].reserva.sum())
        for p in PERILS[line] + ["_ramo"]:
            d = dl if p == "_ramo" else dl[dl.peril == p]
            if p == "_ramo":
                d = d.assign(celda=d.peril + "|" + d.celda)
            if (d.status == "open").sum() == 0:
                res_line["peligros"][p] = {"abiertos": 0}
                continue
            z = _prep_beta(d)
            todos = _beta(z)
            todos["ic90_beta"] = _boot(z, rng)
            pos = d[d.incurred_to_date > 0]
            positivos = _beta(_prep_beta(pos))
            # A2: cociente abiertos/cerrados por celda frente a la fracción cerrada
            g = d.groupby(["celda", "status"]).incurred_to_date.agg(["size", "mean"]).unstack("status")
            g = g.dropna()
            g = g[(g[("size", "closed")] >= MIN_CERRADOS) & (g[("size", "open")] >= 5)]
            a2 = None
            if len(g) >= 4:
                frac = g[("size", "closed")] / (g[("size", "closed")] + g[("size", "open")])
                x = np.log(frac / (1 - frac)).values
                yv = np.log(g[("mean", "open")] / g[("mean", "closed")]).values
                w = g[("size", "open")].values.astype(float)
                X = np.column_stack([np.ones(len(x)), x])
                XtW = X.T * w
                beta_ = np.linalg.solve(XtW @ X, XtW @ yv)
                resid = yv - X @ beta_
                s2 = float((w * resid ** 2).sum() / max(len(x) - 2, 1))
                cov = s2 * np.linalg.inv(XtW @ X)
                t = beta_[1] / np.sqrt(cov[1, 1]) if cov[1, 1] > 0 else np.nan
                a2 = {"celdas": int(len(g)), "pendiente": r(beta_[1], 4), "t": r(t, 2), "contradice_S1": bool(abs(t) > 2) if np.isfinite(t) else None,
                      "cociente_por_celda": {k: {"abiertos": int(g.loc[k, ("size", "open")]), "cerrados": int(g.loc[k, ("size", "closed")]),
                                                 "fraccion_cerrada": r(frac.loc[k], 4), "cociente": r(np.exp(yv[i]), 4)} for i, k in enumerate(g.index)}}
            res_line["peligros"][p] = {"abiertos": int((d.status == "open").sum()), "reserva": r(d[d.status == "open"].reserva.sum(), 2),
                                       "peso_en_reserva_del_ramo": r(d[d.status == "open"].reserva.sum() / reserva_total, 4) if reserva_total else None,
                                       "todos": {k: (r(v, 4) if not isinstance(v, list) else v) for k, v in todos.items()},
                                       "solo_positivos": {k: r(v, 4) for k, v in positivos.items()},
                                       "cobertura_reserva": r(todos["reserva_cubierta"] / max(float(d[d.status == "open"].reserva.sum()), 1e-9), 4),
                                       "A2": a2}
            print(line, p, res_line["peligros"][p]["todos"], (a2 or {}).get("t"), flush=True)
        out[line] = res_line
        guardar(run, "parte_a.json", out)
    # A3: severidad de los avisos tardíos frente a la usada por D67 para el IBNR de 2024
    sev_d67 = pd.read_csv(BASES / "ibnr_2024_por_peligro.csv").set_index(["line", "peril"])
    pos = m[m.unica & m.status.isin(["open", "closed"]) & (m.neto > 0)].copy()
    pos["tardio"] = pos.report_date > pd.to_datetime(pos.anio_ocurrencia.astype(str) + "-12-31")
    a3 = {}
    for line in LINES:
        a3[line] = {}
        for p in PERILS[line]:
            q = pos[(pos.line == line) & (pos.peril == p)]
            usada = float(sev_d67.loc[(line, p), "severidad_usada_ibnr"])
            fila = {"severidad_usada_D67": r(usada, 2), "ibnr_coste_2024_D67": r(sev_d67.loc[(line, p), "ibnr_coste_CU"], 2)}
            for ys, et in (((2021, 2022), "2021_2022"), ((2023,), "2023_incompleto")):
                qq = q[q.anio_ocurrencia.isin(ys)]
                t = qq[qq.tardio]
                fila[et] = {"tardios": int(len(t)), "positivos": int(len(qq)), "media_tardios": r(t.neto.mean(), 2) if len(t) else None,
                            "media_todos": r(qq.neto.mean(), 2) if len(qq) else None, "pct_abiertos_tardios": r((t.status == "open").mean(), 4) if len(t) else None,
                            "k_frente_a_D67": r(t.neto.mean() / usada, 4) if len(t) and usada > 0 else None}
                if len(t) >= 30 and et == "2021_2022":
                    vv = t.neto.values
                    bs = [np.average(vv, weights=rng.poisson(1.0, len(vv)) + 1e-12) for _ in range(B_REPLICAS)]
                    fila[et]["ic90_k"] = [r(np.quantile(bs, 0.05) / usada, 4), r(np.quantile(bs, 0.95) / usada, 4)]
            a3[line][p] = fila
    out["A3"] = a3
    # A4: abiertos sin reserva y rechazados
    acc_all = _celdas(m[m.unica & m.status.isin(["open", "closed"])])
    medias = acc_all[(acc_all.status == "closed") & (acc_all.incurred_to_date > 0)].groupby(["line", "peril", "celda"]).incurred_to_date.mean()
    medias_p = acc_all[(acc_all.status == "closed") & (acc_all.incurred_to_date > 0)].groupby(["line", "peril"]).incurred_to_date.mean()
    sinres = acc_all[(acc_all.status == "open") & (acc_all.reserva <= 0)]
    coste = [float(medias.get((x.line, x.peril, x.celda), medias_p.get((x.line, x.peril), 0.0))) - float(x.paid_to_date) for x in sinres.itertuples()]
    sinres = sinres.assign(coste_adicional=np.maximum(coste, 0.0))
    rech = m[m.unica & (m.status == "repudiated")]
    rech = rech.assign(sev=[float(medias_p.get((x.line, x.peril), 0.0)) for x in rech.itertuples()])
    out["A4"] = {"abiertos_sin_reserva": {line: {str(y): r(g.coste_adicional.sum(), 2) for y, g in sinres[sinres.line == line].groupby("anio_periodo")} for line in LINES},
                 "n_abiertos_sin_reserva": int(len(sinres)),
                 "rechazados": {line: {str(int(y)): {"n": int(len(g)), "coste_si_todos_se_pagaran": r(g.sev.sum(), 2)} for y, g in rech[rech.line == line].groupby("anio_periodo") if pd.notna(y)} for line in LINES},
                 "n_rechazados": int(len(rech))}
    guardar(run, "parte_a.json", out)


# ------------------------------------------------------------------------------------------------ parte B

class Nivel:
    """Nivel 2025 de un ramo bajo un multiplicador de la reserva de caso por peligro (b) y del coste IBNR por peligro (k)."""

    def __init__(self, run: Path, cand: str, line: str):
        tot = leer(run, "datos.json")["totales"][line]
        self.tot = {int(y): v for y, v in tot.items()}
        self.line = line
        df = pd.read_parquet(PRED[cand])
        df = df[df.line == line].copy()
        df["row_id"] = df.row_id.astype(str)
        rfp = pd.read_parquet(run / "resultados" / "reserva_fila_peligro.parquet")
        rfp["row_id"] = rfp.row_id.astype(str)
        df = df.merge(rfp, on="row_id", how="left")
        for p in PERILS[line]:
            c = f"res_{p}"
            df[c] = df[c].fillna(0.0) if c in df.columns else 0.0
        self.sel = df[df.corte == "V23"].reset_index(drop=True)
        self.v24 = df[df.corte == "V24"].reset_index(drop=True)
        self.f23_0 = ftw(self.sel.y_T0, self.sel.prediction)
        self.b24 = self.v24.prediction.values / self.f23_0
        self.f24_0 = ftw(self.v24.y_T0, self.b24)
        resp = np.column_stack([self.sel[f"res_{p}"] for p in PERILS[line]]).sum(axis=1)
        self.control_reserva = r(float(np.abs(resp - self.sel.reserva_caso.values).max()), 6)

    def _y(self, d, b):
        y = d.y_T0.values.copy()
        for p, bp in b.items():
            y = y + (bp - 1.0) * d[f"res_{p}"].values
        return y

    def lam(self, y: int, b: dict, k: dict) -> float:
        t = self.tot[y]
        extra = sum((b.get(p, 1.0) - 1.0) * t["reserva_por_peligro"][p] for p in PERILS[self.line])
        extra += sum((k.get(p, 1.0) - 1.0) * t["ibnr_por_peligro"][p] for p in PERILS[self.line])
        return 1.0 + extra / t["ultimo_supuesto"]

    def L(self, anios, b, k):
        u = sum(self.tot[y]["ultimo_supuesto"] for y in anios)
        return sum(self.tot[y]["ultimo_supuesto"] * self.lam(y, b, k) for y in anios) / u

    def nivel(self, b: dict, k: dict | None = None):
        k = k or {}
        # vía 1: factores de año siguiente con etiquetas modificadas (exacto para la reserva de caso; el IBNR entra como
        # cambio de nivel del año evaluado, porque actúa por la exposición efectiva del offset)
        f23 = ftw(self._y(self.sel, b), self.sel.prediction) * (self.lam(2023, {}, k))
        f24 = ftw(self._y(self.v24, b), self.b24) * (self.lam(2024, {}, k))
        # vía 2: nivel de entrenamiento de cada corte
        l2122, l2123, l2124 = self.L([2021, 2022], b, k), self.L([2021, 2022, 2023], b, k), self.L([2021, 2022, 2023, 2024], b, k)
        solo_f = (f23 + f24) / (self.f23_0 + self.f24_0)
        total = l2124 * (f23 / l2122 + f24 / l2123) / (self.f23_0 + self.f24_0)
        return {"nivel": total, "solo_factor": solo_f, "solo_entrenamiento": l2124 * (self.f23_0 / l2122 + self.f24_0 / l2123) / (self.f23_0 + self.f24_0),
                "f23": f23, "f24": f24, "L2122": l2122, "L2123": l2123, "L2124": l2124}


def _umbral(fun, objetivo, lo, hi, n=60):
    """Busca x en [lo, hi] con fun(x) = objetivo por bisección (fun monótona); None si no cruza."""
    a, b = lo, hi
    fa, fb = fun(a) - objetivo, fun(b) - objetivo
    if fa * fb > 0:
        return None
    for _ in range(n):
        mid = (a + b) / 2
        fm = fun(mid) - objetivo
        if fa * fm <= 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
    return (a + b) / 2


def etapa_b(run: Path):
    out = {"materialidad": MATERIALIDAD, "ramos": {}}
    resumen = json.loads(RESUMEN_S30.read_text(encoding="utf-8"))
    for line in LINES:
        nv = {c: Nivel(run, c, line) for c in ("S30", "S22")}
        n = nv["S30"]
        o = {"control_reserva_por_fila": n.control_reserva, "f23": r(n.f23_0, 6), "f24": r(n.f24_0, 6), "resumen_S30": {}}
        for k_, v in (resumen.get("lines", {}).get(line, {}) or {}).items():
            if k_ in ("f23", "f24", "f"):
                o["resumen_S30"][k_] = v
        grupos = {"todos": PERILS[line]}
        if line in LARGOS:
            grupos[LARGOS[line]] = [LARGOS[line]]
            grupos["resto"] = [p for p in PERILS[line] if p != LARGOS[line]]
        # B2: umbrales del 1 % para la reserva de caso y para el coste IBNR
        umb = {}
        for gname, ps in grupos.items():
            fb = lambda x, ps=ps: n.nivel({p: x for p in ps})["nivel"]
            fk = lambda x, ps=ps: n.nivel({}, {p: x for p in ps})["nivel"]
            umb[gname] = {"reserva_b_menos_1pct": r(_umbral(fb, 1 - MATERIALIDAD, 0.05, 1.0), 4), "reserva_b_mas_1pct": r(_umbral(fb, 1 + MATERIALIDAD, 1.0, 20.0), 4),
                          "ibnr_k_menos_1pct": r(_umbral(fk, 1 - MATERIALIDAD, 0.0, 1.0), 4), "ibnr_k_mas_1pct": r(_umbral(fk, 1 + MATERIALIDAD, 1.0, 20.0), 4),
                          "nivel_b_0_75": r(n.nivel({p: 0.75 for p in ps})["nivel"] - 1, 5), "nivel_b_1_25": r(n.nivel({p: 1.25 for p in ps})["nivel"] - 1, 5),
                          "vias_b_1_25": {kk: r(vv - 1 if kk in ("nivel", "solo_factor", "solo_entrenamiento") else vv, 5) for kk, vv in n.nivel({p: 1.25 for p in ps}).items()}}
        o["umbrales"] = umb
        # B3: orden S30 frente a S22
        rejilla = [0.25, 0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 2.5]
        orden = {}
        for gname, ps in grupos.items():
            filas = []
            for x in rejilla:
                b = {p: x for p in ps}
                fila = {"b": x}
                for corte in ("V24", "V23"):
                    for modo in ("fijas", "renivel"):
                        d = {}
                        for c, nc in nv.items():
                            dd = nc.v24 if corte == "V24" else nc.sel
                            y = nc._y(dd, b)
                            pred = dd.prediction.values
                            if modo == "renivel":
                                l2122, l2123 = nc.L([2021, 2022], b, {}), nc.L([2021, 2022, 2023], b, {})
                                if corte == "V23":
                                    pred = pred * l2122
                                else:
                                    f23b = ftw(nc._y(nc.sel, b), nc.sel.prediction) / l2122
                                    pred = nc.b24 * l2123 * f23b
                            d[c] = d2(y, pred)
                        fila[f"{corte}_{modo}"] = r(d["S30"] - d["S22"], 6)
                filas.append(fila)
            cambios = {}
            for col in ("V24_fijas", "V24_renivel", "V23_fijas", "V23_renivel"):
                signo = [np.sign(f[col]) for f in filas]
                cambios[col] = [f["b"] for f, s0, s1 in zip(filas[1:], signo[:-1], signo[1:]) if s0 != s1 and s1 != 0]
            orden[gname] = {"rejilla": filas, "b_donde_cambia_el_signo": cambios}
        o["orden_S30_S22"] = orden
        # B4: coste en D² de un error de nivel del 1 %
        b4 = {}
        for corte, dd, pred in (("V24", n.v24, n.v24.prediction.values), ("V23", n.sel, n.sel.prediction.values)):
            y = dd.y_T0.values
            base = d2(y, pred)
            b4[corte] = {"d2": r(base, 6), "menos_1pct": r(d2(y, pred * 0.99) - base, 6), "mas_1pct": r(d2(y, pred * 1.01) - base, 6),
                         "menos_2pct": r(d2(y, pred * 0.98) - base, 6), "mas_2pct": r(d2(y, pred * 1.02) - base, 6)}
        o["coste_d2_error_nivel"] = b4
        out["ramos"][line] = o
        print(line, json.dumps({k: v for k, v in o.items() if k in ("f23", "f24", "resumen_S30", "control_reserva_por_fila")}), json.dumps(umb["todos"]), flush=True)
    # agregado de B4
    ys, ps = {"V24": [], "V23": []}, {"V24": [], "V23": []}
    for line in LINES:
        df = pd.read_parquet(PRED["S30"])
        df = df[df.line == line]
        for corte in ("V24", "V23"):
            dd = df[df.corte == corte]
            ys[corte].append(dd.y_T0.values); ps[corte].append(dd.prediction.values)
    agg = {}
    for corte in ("V24", "V23"):
        y = np.concatenate(ys[corte]); pr = np.concatenate(ps[corte]); base = d2(y, pr)
        agg[corte] = {"d2": r(base, 6), "menos_1pct": r(d2(y, pr * 0.99) - base, 6), "mas_1pct": r(d2(y, pr * 1.01) - base, 6)}
    out["coste_d2_error_nivel_agregado"] = agg
    # B3 en el agregado de los tres ramos (la elección S30/S22 se hace sobre el agregado), b uniforme y solo lesiones
    nvs = {line: {c: Nivel(run, c, line) for c in ("S30", "S22")} for line in LINES}
    agr = {}
    for gname in ("todos", "bodily_injury"):
        filas = []
        for x in [0.25, 0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 2.5]:
            fila = {"b": x}
            for corte in ("V24", "V23"):
                d = {}
                for c in ("S30", "S22"):
                    ys_, ps_ = [], []
                    for line in LINES:
                        nc = nvs[line][c]
                        ps = PERILS[line] if gname == "todos" else [p for p in PERILS[line] if p == gname]
                        dd = nc.v24 if corte == "V24" else nc.sel
                        ys_.append(nc._y(dd, {p: x for p in ps}))
                        ps_.append(dd.prediction.values)
                    d[c] = d2(np.concatenate(ys_), np.concatenate(ps_))
                fila[corte] = r(d["S30"] - d["S22"], 6)
            filas.append(fila)
        agr[gname] = {"rejilla": filas, "rango_con_el_signo_de_b1": {corte: _rango_signo(filas, corte) for corte in ("V24", "V23")}}
    out["orden_S30_S22_agregado"] = agr
    for line in LINES:
        for gname, v in out["ramos"][line]["orden_S30_S22"].items():
            v["rango_con_el_signo_de_b1"] = {col: _rango_signo(v["rejilla"], col) for col in ("V24_fijas", "V24_renivel", "V23_fijas", "V23_renivel")}
    guardar(run, "parte_b.json", out)


def _rango_signo(filas, col):
    """Intervalo de la rejilla, alrededor de b = 1, en el que la diferencia S30 - S22 conserva el signo que tiene en b = 1."""
    bs = [f["b"] for f in filas]
    i1 = bs.index(1.0)
    s1 = np.sign(filas[i1][col])
    lo = i1
    while lo - 1 >= 0 and np.sign(filas[lo - 1][col]) == s1:
        lo -= 1
    hi = i1
    while hi + 1 < len(filas) and np.sign(filas[hi + 1][col]) == s1:
        hi += 1
    return {"signo_en_b1": int(s1), "desde": bs[lo], "hasta": bs[hi], "limitado_por_la_rejilla": [lo == 0, hi == len(filas) - 1]}


# ------------------------------------------------------------------------------------------------ resumen

def etapa_resumen(run: Path):
    a = leer(run, "parte_a.json")
    b = leer(run, "parte_b.json")
    filas = {}
    for line in LINES:
        ram = a[line]["peligros"]["_ramo"]
        ic = ram["todos"].get("ic90_beta") or [None, None]
        u = b["ramos"][line]["umbrales"]["todos"]
        lo, hi = u["reserva_b_menos_1pct"], u["reserva_b_mas_1pct"]
        # orden del pre-registro: intervalo dentro del intervalo de quiebre -> acotado; intervalo que cruza un umbral ->
        # incertidumbre material; intervalo entero fuera -> indicio de sesgo material. La posición de la estimación
        # puntual se informa aparte.
        if None in ic or lo is None or hi is None:
            clase = "sin_datos"
        elif ic[0] >= lo and ic[1] <= hi:
            clase = "acotado_bajo_materialidad_si_S1"
        elif ic[1] < lo or ic[0] > hi:
            clase = "indicio_de_sesgo_material_si_S1"
        else:
            clase = "incertidumbre_material"
        contrad = {p: v["A2"]["contradice_S1"] for p, v in a[line]["peligros"].items() if p != "_ramo" and v.get("A2")}
        bp = ram["todos"]["beta_reserva"]
        filas[line] = {"beta_reserva": bp, "ic90": ic, "umbral_b": [lo, hi], "clase": clase, "A2_contradice_S1": contrad,
                       "estimacion_puntual": ("dentro_del_intervalo_de_quiebre" if lo is not None and hi is not None and lo <= bp <= hi else
                                              ("reserva_holgada_mas_alla_del_umbral" if lo is not None and bp < lo else "reserva_corta_mas_alla_del_umbral")),
                       "nivel_2025_con_beta_puntual": r(Nivel(run, "S30", line).nivel({p: bp for p in PERILS[line]})["nivel"] - 1, 5),
                       "peso_reserva_largos": {p: a[line]["peligros"][p].get("peso_en_reserva_del_ramo") for p in a[line]["peligros"] if p in LARGOS.values()}}
        # IBNR: k de A3 (avisos tardíos de 2021-2022 frente a la severidad de D67) contra el umbral del peligro, y efecto en el nivel
        n = Nivel(run, "S30", line)
        ib = {}
        for p in PERILS[line]:
            v = a["A3"][line][p]["2021_2022"]
            kk, ick = v.get("k_frente_a_D67"), v.get("ic90_k")
            if kk is None or not ick or None in ick:
                continue
            f = lambda x, p=p: n.nivel({}, {p: x})["nivel"]
            lo_k, hi_k = _umbral(f, 1 - MATERIALIDAD, 0.0, 1.0), _umbral(f, 1 + MATERIALIDAD, 1.0, 20.0)
            # sin cruce en la búsqueda: ningún k de ese lado mueve el nivel un 1 % (umbral inexistente, lado inmaterial)
            lo_e = lo_k if lo_k is not None else -np.inf
            hi_e = hi_k if hi_k is not None else np.inf
            if ick[0] >= lo_e and ick[1] <= hi_e:
                c_ = "acotado_bajo_materialidad_si_S3"
            elif ick[1] < lo_e or ick[0] > hi_e:
                c_ = "indicio_de_desvio_material_si_S3"
            else:
                c_ = "incertidumbre_material"
            ib[p] = {"k": kk, "ic90_k": ick, "umbral_k": [r(lo_k, 4), r(hi_k, 4)], "clase": c_, "ibnr_2024_D67": a["A3"][line][p]["ibnr_coste_2024_D67"],
                     "nivel_2025_con_k": r(f(kk) - 1, 5), "nivel_2025_con_ic90_k": [r(f(ick[0]) - 1, 5), r(f(ick[1]) - 1, 5)]}
        k_todos = {p: v["k"] for p, v in ib.items()}
        filas[line]["ibnr"] = {"por_peligro": ib, "nivel_2025_con_todos_los_k": r(n.nivel({}, k_todos)["nivel"] - 1, 5)}
    # comprobación añadida después de ver A3 (no pre-registrada): k de los peligros largos por año de ocurrencia, porque
    # en 2022 los avisos con demoras de más de dos años aún no se observan
    m = pd.read_parquet(run / "resultados" / "siniestros.parquet")
    pos = m[m.unica & m.status.isin(["open", "closed"]) & (m.neto > 0)].copy()
    pos["tardio"] = pos.report_date > pd.to_datetime(pos.anio_ocurrencia.astype(str) + "-12-31")
    sev_d67 = pd.read_csv(BASES / "ibnr_2024_por_peligro.csv").set_index(["line", "peril"])
    posterior = {}
    for line, p in LARGOS.items():
        usada = float(sev_d67.loc[(line, p), "severidad_usada_ibnr"])
        q = pos[(pos.line == line) & (pos.peril == p)]
        posterior[p] = {}
        for y in (2021, 2022, 2023):
            t = q[(q.anio_ocurrencia == y) & q.tardio]
            posterior[p][str(y)] = {"tardios": int(len(t)), "media_tardios": r(t.neto.mean(), 2) if len(t) else None, "k": r(t.neto.mean() / usada, 4) if len(t) else None,
                                    "media_cerrados_tardios": r(t[t.status == "closed"].neto.mean(), 2) if (t.status == "closed").any() else None,
                                    "pct_abiertos": r((t.status == "open").mean(), 4) if len(t) else None,
                                    "demora_mediana_dias": r(float((t.report_date - t.loss_date).dt.days.median()), 1) if len(t) else None}
        tard = q[q.tardio & q.anio_ocurrencia.isin([2021, 2022])]
        largos = tard[(tard.report_date - tard.loss_date).dt.days > 365]
        posterior[p]["2021_2022_demora_mas_365_dias"] = {"n": int(len(largos)), "media": r(largos.neto.mean(), 2) if len(largos) else None}
    for line in LINES:
        filas[line]["robustez_posterior_A3"] = posterior.get(LARGOS.get(line, ""), None)
    guardar(run, "resumen.json", {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "supuesto_S3": "los avisos posteriores al 31 de diciembre de su año de ocurrencia en 2021-2022 representan la severidad del IBNR de 2024 al 31-12-2024 (misma selección por demora, sin cambio de nivel de severidad)", "ramos": filas})
    print(json.dumps(filas, ensure_ascii=False, indent=1))


def main():
    run = Path(sys.argv[1]).resolve()
    etapa = sys.argv[2] if len(sys.argv) > 2 else "todas"
    solo = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    (run / "resultados").mkdir(parents=True, exist_ok=True)
    if etapa in ("datos", "todas"):
        etapa_datos(run)
    if etapa in ("a", "todas"):
        etapa_a(run, solo)
    if etapa in ("b", "todas"):
        etapa_b(run)
    if etapa in ("resumen", "todas"):
        etapa_resumen(run)


if __name__ == "__main__":
    main()
