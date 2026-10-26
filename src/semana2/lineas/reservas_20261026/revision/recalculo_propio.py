"""Recálculo propio de cifras clave con código escrito aparte (no importa reservas_s2.py).

No es una revisión independiente: lo escribió la misma sesión de Claude que hizo el análisis. Sustituye a la revisión por
subagente que pedía el plan, que no se hizo. Recalcula T0 y la reserva, β de autos, k_e de lesiones corporales, los factores
de nivel por celda, la elasticidad de autos y el umbral inferior de b para autos en F3c, y los compara con resultados/.

Uso: python3 recalculo_propio.py <raíz>   (raíz con datos/, cadena/ y resultados/)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(sys.argv[1]).resolve()
DAT, CAD, RES = R / "datos", R / "cadena", R / "resultados"
L = ["motor", "buildings", "contents"]
J = {k: json.loads((RES / f"{k}.json").read_text(encoding="utf-8")) for k in ("parte_a", "parte_b", "parte_c", "parte_d")}
out = []


def comparar(nombre, mio, publicado, tol):
    ok = abs(mio - publicado) <= tol
    out.append({"cifra": nombre, "recalculo": round(float(mio), 6), "publicado": publicado, "tolerancia": tol, "coincide": bool(ok)})
    print(("OK   " if ok else "FALLO"), nombre, round(float(mio), 6), publicado)


# 1. asignación, T0 y reserva
cl = pd.read_parquet(DAT / "claims.parquet")
cl["loss_date"] = pd.to_datetime(cl.loss_date); cl["report_date"] = pd.to_datetime(cl.report_date)
asig = []
for l in L:
    p = pd.read_parquet(DAT / f"policies_{l}.parquet", columns=["row_id", "policy_id", "period_start", "period_end"])
    p["period_start"] = pd.to_datetime(p.period_start); p["period_end"] = pd.to_datetime(p.period_end)
    x = cl[cl.line == l].merge(p, on="policy_id")
    asig.append(x[(x.loss_date >= x.period_start) & (x.loss_date <= x.period_end)])
A = pd.concat(asig)
acc = A[A.status != "repudiated"].copy()
acc["neto"] = acc.incurred_to_date - acc.recoveries
acc["res"] = np.where(acc.status == "open", acc.incurred_to_date - acc.paid_to_date, 0.0)
acc["anio"] = acc.period_start.dt.year
comparar("T0 total", acc.neto.sum(), J["parte_a"]["totales"]["T0"], 0.005)
comparar("reserva total", acc.res.sum(), J["parte_a"]["totales"]["reserva"], 0.005)
comparar("abiertos", (A.status == "open").sum(), J["parte_a"]["totales"]["abiertos"], 0)
for l in L:
    for y in (2023, 2024):
        q = acc[(acc.line == l) & (acc.anio == y)]
        comparar(f"T0 {l} {y}", q.neto.sum(), J["parte_a"]["por_ramo_anio"][f"{l}_{y}"]["T0"], 0.005)
lb = acc[(acc.line == "motor") & (acc.peril == "bodily_injury")].res.sum()
comparar("peso de lesiones en la reserva total", lb / acc.res.sum(), 0.48997, 0.0001)

# 2. β de autos
m = acc[(acc.line == "motor") & acc.status.isin(["open", "closed"])].copy()
m["celda"] = m.peril + "|" + m.report_date.dt.to_period("Q").astype(str)
imp = pag = inc = 0.0
for _, g in m.groupby("celda"):
    c, o = g[g.status == "closed"], g[g.status == "open"]
    if len(c) >= 20 and len(o) >= 1:
        imp += len(o) * c.incurred_to_date.mean(); pag += o.paid_to_date.sum(); inc += o.incurred_to_date.sum()
comparar("β autos", (imp - pag) / (inc - pag), J["parte_b"]["beta"]["motor|_ramo"]["beta"], 0.00006)
comparar("cobertura de β autos", (inc - pag) / m[m.status == "open"].eval("incurred_to_date - paid_to_date").sum(),
         J["parte_b"]["beta"]["motor|_ramo"]["cobertura_reserva"], 0.00006)

# 3. k_e de lesiones corporales
d = pd.read_parquet(DAT / "claims_desarrollado.parquet")
otras = [c for c in d.columns if c != "claim_id"]
d = d[~(d.duplicated(otras, keep=False) & (d.claim_id.str.len() == 11))]
d = d[(d.line == "motor") & (d.peril == "bodily_injury") & (d.status != "repudiated")].copy()
d["loss_date"] = pd.to_datetime(d.loss_date); d["report_date"] = pd.to_datetime(d.report_date)
V, V1 = pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")
d = d[(V - d.loss_date).dt.days >= 1095]
ret = (d.report_date - d.loss_date).dt.days.values
w = (d.incurred_to_date - d.recoveries).values
k = ret <= 1095
F = np.cumsum(np.bincount(ret[k], weights=w[k], minlength=1096)) / w[k].sum()


def Fe(edad):
    edad = np.asarray(edad)
    return np.where(edad < 0, 0.0, np.where(edad > 1095, 1.0, F[np.clip(edad, 0, 1095)]))


pm = pd.read_parquet(DAT / "policies_motor.parquet", columns=["period_start", "period_end"])
pm["s"] = pd.to_datetime(pm.period_start); pm["e"] = pd.to_datetime(pm.period_end)
p23 = pm[pm.s.dt.year == 2023]
num = den = 0.0
for s_, e_ in zip(p23.s, p23.e):
    dias = pd.date_range(s_, e_)
    c = Fe((V - dias).days.values).mean(); c1 = Fe((V1 - dias).days.values).mean()
    ex = ((e_ - s_).days + 1) / 365
    num += ex * (c - c1); den += ex * c1
ratio = num / den
co = acc[(acc.line == "motor") & (acc.peril == "bodily_injury") & (acc.loss_date.dt.year == 2023) & (acc.anio == 2023)]
tarde = co.report_date > V1
comparar("k_e lesiones", co.neto[tarde].sum() / (co.neto[~tarde].sum() * ratio), J["parte_c"]["k"]["motor|bodily_injury"]["k_e"], 0.00006)

# 4. factores por celda, elasticidad y umbral de autos
pre = json.loads((CAD / "sonda_segmento_preinscripcion.json").read_text(encoding="utf-8"))
fi = json.loads((CAD / "final_info_3puntos.json").read_text(encoding="utf-8"))
sg = json.loads((CAD / "sonda_global_resultado.json").read_text(encoding="utf-8"))
C = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
bs = {s: pre["base"]["beta_B"] * pre["celdas"][s]["cuota_raiz_mu"] for s in C}
as_ = {s: fi["nivel"]["c_opt"][s] * bs[s] for s in C}
Zs = {s: pre["celdas"][s]["Z"] for s in C}; Zg = sg["Z"]


def fac(rho):
    cg = sum(as_[s] * rho[s] ** -0.5 for s in C) / sum(bs[s] * rho[s] ** 0.5 for s in C)
    g = np.clip(cg ** Zg, 0.75, 1.33)
    return {s: rho[s] * g * np.clip((fi["nivel"]["c_opt"][s] / rho[s] / cg) ** Zs[s], 0.75, 1.33) for s in C}


f1 = fac({s: 1.0 for s in C})
comparar("máx. diferencia relativa con nivel.cred", max(abs(f1[s] / fi["nivel"]["cred"][s] - 1) for s in C), 0.0, 1e-6)
h = 1e-6
fh = fac({s: (1 + h if s.startswith("motor") else 1.0) for s in C})
for s in ("motor_0", "motor_1"):
    comparar(f"elasticidad {s}", np.log(fh[s] / f1[s]) / np.log(1 + h), J["parte_d"]["elasticidad_analitica"]["motor"][s], 0.0001)

b = pd.read_parquet(RES / "base_filas.parquet", columns=["line", "y", "R", "m"])
q = b[b.line == "motor"]
s_des = q.R.sum() / q.y.sum(); s_ml = (q.R / np.sqrt(q.m)).sum() / (q.y / np.sqrt(q.m)).sum()
t = pd.read_parquet(DAT / "test_motor.parquet", columns=["row_id", "new_business"])
t["row_id"] = t.row_id.astype(str); t["celda"] = "motor_" + t.new_business.astype(bool).astype(int).astype(str)
tot = {}
for nom, f in (("des", "A1fixF1b3n_2025.csv"), ("ml", "prediccion_2025_mlind.csv"), ("F3c", "F3c_2025.csv")):
    x = pd.read_csv(CAD / f, dtype={"row_id": str}).merge(t, on="row_id")
    tot[nom] = x.groupby("celda").prediction.sum()
wd = tot["des"].sum() / (tot["des"].sum() + tot["ml"].sum())


def nivel_autos(bb):
    rr = wd * (1 + (bb - 1) * s_des) + (1 - wd) * (1 + (bb - 1) * s_ml)
    f = fac({s: (rr if s.startswith("motor") else 1.0) for s in C})
    return sum(tot["F3c"][s] * f[s] / f1[s] for s in ("motor_0", "motor_1")) / tot["F3c"].sum() - 1


lo, hi = 0.5, 1.0
for _ in range(80):
    mid = (lo + hi) / 2
    lo, hi = (lo, mid) if nivel_autos(mid) > -0.01 else (mid, hi)  # por encima de −1 %: el cruce está por debajo de mid
u = (lo + hi) / 2
comparar("umbral inferior de b en autos (F3c)", u, J["parte_d"]["escenarios"]["motor|b|ramo"]["umbral_F3c"][0], 0.00001)
ic = J["parte_b"]["beta"]["motor|_ramo"]["ic90"]
clase = "acotado" if ic[0] >= u and ic[1] <= J["parte_d"]["escenarios"]["motor|b|ramo"]["umbral_F3c"][1] else "incertidumbre_material"
out.append({"cifra": "clase de la reserva de caso de autos", "recalculo": clase, "publicado": J["parte_d"]["escenarios"]["motor|b|ramo"]["clase_F3c"],
            "coincide": clase == J["parte_d"]["escenarios"]["motor|b|ramo"]["clase_F3c"]})
print(clase)
(R / "revision" / "recalculo_propio.json").write_text(json.dumps({"nota": __doc__.strip().split("\n")[0], "cifras": out,
                                                                  "fallos": sum(not o["coincide"] for o in out)}, ensure_ascii=False, indent=1), encoding="utf-8")
