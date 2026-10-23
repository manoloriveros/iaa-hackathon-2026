"""Acotación de reservas con la regla de forma de S43 (corrida repro_s43_20261023T141352Z_fbf66589, parte 2 del plan).

S43 = S42 con r' = g (r/g)^a_Z por ramo, renivelado al total del ramo (D102). El nivel de cada ramo es el de S42, así
que su acotación vale sin cambios. La forma depende de las etiquetas del proyecto solo a través del ruido σ del
óptimo del 33 % (bootstrap sobre 2024 con las predicciones V24 de S30), que fija Z = τ²/(τ² + σ²) y a_Z = 1 + Z (a* − 1);
a* sale del público. Este script repite, con los mismos datos y las mismas operaciones que `sonda_forma.py`
(curvatura_y_ruido: 200 réplicas, semilla 3, 33 %, rejilla 0,80-1,20 de 0,02), el cálculo de σ y K cuando la reserva
de caso de un ramo vale b veces lo reservado (etiquetas y_T0 + (b − 1)·reserva y predicciones V24 reescaladas por
f23(b)/f23, como la clase Nivel de reservas_consistencia.py), bajo S3 (IBNR de lesiones, como cambio de nivel del año)
y con el nivel de un ramo movido un 2,5 %. Materialidad elegida por el participante: K_2024·Δa_Z² >= 0,00003.

Uso: python3 reservas_s43.py <repo_con_reservas_consistencia> <corrida_reservas> <registro_D102> <parquet_S30> <raiz_datos> <salida.json>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO, RUN, REG, PQ, DATOS, SALIDA = (Path(a) for a in sys.argv[1:7])
spec = importlib.util.spec_from_file_location("reservas_consistencia", REPO / "herramientas" / "reservas_consistencia.py")
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)
rc.PRED["S30"] = PQ
L = ["motor", "buildings", "contents"]
H = 0.10
GRID = np.round(np.arange(0.80, 1.2001, 0.02), 2)
REPS, FRAC, SEMILLA = 200, 0.33, 3
MAT_D2 = 0.00003


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dev(y, mu):  # idéntica a sonda_forma.dev
    return 4 * (y / np.sqrt(mu) + np.sqrt(mu) - 2 * np.sqrt(y))


def forma(mu, e, a):  # idéntica a sonda_forma.forma
    g = mu.sum() / e.sum()
    mp = e * g * (mu / e / g) ** a
    return mp * (mu.sum() / mp.sum())


pre = json.loads((REG / "sonda_forma_D102_preinscripcion.json").read_text(encoding="utf-8"))
res = json.loads((REG / "sonda_forma_D102_resolucion.json").read_text(encoding="utf-8"))["resolucion"]
SIG0 = pre["preinscrito"]["sigma_ruido_33pct_bootstrap_2024"]
K0 = pre["preinscrito"]["K_2024"]
Z0 = pre["preinscrito"]["Z_credibilidad"]
TAU = pre["preinscrito"]["tau_previa"]
ASTAR = {l: res["ramos"][l]["a_optimo_publico"] for l in L}
AZ0 = {l: res["ramos"][l]["a_Z"] for l in L}
UMBRAL_A = {l: (MAT_D2 / K0[l]) ** 0.5 for l in L}

# ---------------------------------------------------------------- datos, en el mismo orden que curvatura_y_ruido
v = pd.read_parquet(PQ)
v = v[v.corte == "V24"].set_index("row_id")
ex = pd.concat([pd.read_parquet(DATOS / f"policies_{l}.parquet", columns=["row_id", "exposure"]) for l in L]).set_index("row_id").exposure
v["e"] = ex.reindex(v.index).values
assert v.e.notna().all() and (v.e > 0).all()
Y0, M0, E, LIN = v.y_T0.values.copy(), v.prediction.values.copy(), v.e.values, v.line.values
N = len(Y0)
IDX = {l: np.where(LIN == l)[0] for l in L}
rfp = pd.read_parquet(RUN / "resultados" / "reserva_fila_peligro.parquet")
rfp["row_id"] = rfp.row_id.astype(str)
rfp = rfp.set_index("row_id").reindex(v.index.astype(str)).fillna(0.0)
RES = {c[4:]: rfp[c].values for c in rfp.columns if c.startswith("res_")}
NV = {l: rc.Nivel(RUN, "S30", l) for l in L}

# máscaras del bootstrap: la misma secuencia que curvatura_y_ruido (rng.random(n) < frac por réplica)
_rng = np.random.default_rng(SEMILLA)
MASK = [_rng.random(N) < FRAC for _ in range(REPS)]
K1 = int(np.where(GRID == 1.0)[0][0])


def calibrar_ramo(l, y, m):
    """σ, K, vértice y óptimo de rejilla de un ramo, con las operaciones de curvatura_y_ruido."""
    sel = IDX[l]
    yl, ml, el = y[sel], m[sel], E[sel]
    D = np.zeros((len(GRID), len(sel)))
    for k, a in enumerate(GRID):
        D[k] = dev(yl, forma(ml, el, a))
    tot = D.sum(axis=1)
    null = dev(y, np.full_like(y, y.mean())).sum()
    base = dev(yl, ml).sum()
    curva = {f"{a:.2f}": float(-(tot[k] - base) / null) for k, a in enumerate(GRID)}
    d090, d100, d110 = curva["0.90"], curva["1.00"], curva["1.10"]
    c2 = (d090 - 2 * d100 + d110) / (2 * H ** 2)
    c1 = (d110 - d090) / (2 * H) - 2 * c2
    opt = []
    for mk in MASK:
        sp = mk[sel]
        opt.append(float(GRID[int(np.argmin(D[:, sp].sum(axis=1)))]))
    return {"sigma": float(np.std(opt)), "K": float(-c2), "vertice_2024": float(-c1 / (2 * c2)) if c2 < 0 else None,
            "optimo_rejilla_2024": float(GRID[int(np.argmin(tot))])}


def efecto(l, sigma):
    Z = TAU[l] ** 2 / (TAU[l] ** 2 + sigma ** 2)
    aZ = 1 + Z * (ASTAR[l] - 1)
    da = aZ - AZ0[l]
    return {"Z": Z, "a_Z": aZ, "delta_a_Z": da, "coste_D2": K0[l] * da ** 2, "material": bool(K0[l] * da ** 2 >= MAT_D2)}


def escenario_b(l, b: dict):
    """Etiquetas V24 con la reserva del ramo ×b por peligro y predicciones V24 reescaladas por f23(b)/f23."""
    y = Y0.copy()
    sel = IDX[l]
    for p, bp in b.items():
        y[sel] = y[sel] + (bp - 1.0) * RES[p][sel]
    nv = NV[l]
    f23b = rc.ftw(nv._y(nv.sel, b), nv.sel.prediction)
    m = M0.copy()
    m[sel] = m[sel] * f23b / nv.f23_0
    return y, m, f23b / nv.f23_0


t0 = time.time()
salida = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "materialidad_D2": MAT_D2,
          "fuentes_sha256": {"parquet_S30": sha(PQ), "reserva_fila_peligro": sha(RUN / "resultados" / "reserva_fila_peligro.parquet"),
                             "datos_json": sha(RUN / "resultados" / "datos.json"), "reservas_consistencia_py": sha(REPO / "herramientas" / "reservas_consistencia.py"),
                             "preinscripcion_D102": sha(REG / "sonda_forma_D102_preinscripcion.json"), "resolucion_D102": sha(REG / "sonda_forma_D102_resolucion.json"),
                             **{f"policies_{l}": sha(DATOS / f"policies_{l}.parquet") for l in L}},
          "registrado": {"sigma": SIG0, "K_2024": K0, "Z": Z0, "a_optimo_publico": ASTAR, "a_Z": AZ0}, "umbral_delta_a": UMBRAL_A}

# a. el nivel: S43 conserva los totales por ramo de S42
s42 = res["S43"]["por_ramo_CU"]
salida["a_totales_S43_igual_S42"] = {"S43_por_ramo_CU": s42, "nota": "S42: 116978988.80 / 77439071.71 / 19777818.68 (resolución de D101 y CSV)"}

# control: sin escenario se recuperan σ y K
ctrl = {}
for l in L:
    c = calibrar_ramo(l, Y0, M0)
    ctrl[l] = {**c, "sigma_igual": c["sigma"] == SIG0[l], "K_rel": abs(c["K"] - K0[l]) / K0[l]}
salida["control_b1"] = ctrl
print("control", json.dumps({l: (ctrl[l]["sigma_igual"], f"{ctrl[l]['K_rel']:.1e}") for l in L}))

# c. cota analítica
salida["c_cota"] = {l: {"a_estrella_menos_1": ASTAR[l] - 1, "coste_maximo_si_Z_va_de_0_a_1": K0[l] * (ASTAR[l] - 1) ** 2,
                        "inmaterial_para_cualquier_Z": bool(K0[l] * (ASTAR[l] - 1) ** 2 < MAT_D2),
                        "delta_Z_que_haria_material": (UMBRAL_A[l] / abs(ASTAR[l] - 1)) if ASTAR[l] != 1 else None} for l in L}

# d. reserva de caso ×b
ic_ramo = {"motor": [0.6133, 1.106], "buildings": [0.873, 1.1089], "contents": [0.7865, 1.1563]}
ic_largo = {"motor": [0.5502, 1.1542], "buildings": [0.8289, 1.2022]}
rejilla_b = [0.50, 0.75, 0.85, 0.95, 1.05, 1.15, 1.25, 1.50, 2.00]
grupos = {l: {"todos": rc.PERILS[l]} for l in L}
for l, p in rc.LARGOS.items():
    grupos[l][p] = [p]
    grupos[l]["resto"] = [q for q in rc.PERILS[l] if q != p]
filas = []
for l in L:
    for gname, ps in grupos[l].items():
        ic = ic_largo[l] if gname == rc.LARGOS.get(l) else ic_ramo[l] if gname == "todos" else None
        bs = sorted(set(rejilla_b + (ic or [])))
        for bval in bs:
            y, m, rf = escenario_b(l, {p: bval for p in ps})
            c = calibrar_ramo(l, y, m)
            ef = efecto(l, c["sigma"])
            filas.append({"ramo": l, "grupo": gname, "b": bval, "en_ic90_beta": bool(ic is not None and ic[0] <= bval <= ic[1]),
                          "f23_relativo": rf, **c, **ef})
        print(l, gname, "listo", f"{time.time() - t0:.0f} s")
salida["d_reserva_caso"] = filas

# e. S3: IBNR de lesiones como cambio de nivel del año evaluado en autos
s3 = []
for k in (0.813, 0.867, 0.922):
    lam = NV["motor"].lam(2024, {}, {"bodily_injury": k})
    m = M0.copy()
    m[IDX["motor"]] *= lam
    c = calibrar_ramo("motor", Y0, m)
    s3.append({"k": k, "lambda_2024": lam, **c, **efecto("motor", c["sigma"])})
salida["e_S3"] = s3

# f. interacción con el nivel: predicciones V24 de un ramo ×0,975 y ×1,025
inter = []
base_c = {l: ctrl[l] for l in L}
for l in L:
    for lam in (0.975, 1.025):
        m = M0.copy()
        m[IDX[l]] *= lam
        c = calibrar_ramo(l, Y0, m)
        dv = (c["vertice_2024"] - base_c[l]["vertice_2024"]) if c["vertice_2024"] is not None and base_c[l]["vertice_2024"] is not None else None
        dz = Z0[l] * dv if dv is not None else None
        inter.append({"ramo": l, "lambda": lam, **c, "delta_vertice": dv, "delta_optimo_rejilla": c["optimo_rejilla_2024"] - base_c[l]["optimo_rejilla_2024"],
                      "efecto_en_a_Z": dz, "coste_D2": K0[l] * dz ** 2 if dz is not None else None,
                      "material": bool(dz is not None and K0[l] * dz ** 2 >= MAT_D2)})
salida["f_interaccion_nivel"] = inter

# g. variante: ruido corregido
var = {}
sens43 = {"motor": 0.0526, "buildings": 0.0621, "contents": 0.0554}  # N03 de sens43, redondeado a cuatro decimales
for l in L:
    var[l] = {"sigma_entre_raiz_067": efecto(l, SIG0[l] / 0.67 ** 0.5), "sigma_N03_sens43": efecto(l, sens43[l])}
salida["g_ruido_corregido"] = var

# clasificación preinscrita
clase = {}
for l in L:
    malos = [f for f in filas if f["ramo"] == l and f["en_ic90_beta"] and f["material"]]
    malos += [f for f in s3 if l == "motor" and f["material"]]
    malos += [f for f in inter if f["ramo"] == l and f["material"]]
    clase[l] = {"clase": "material" if malos else "inmaterial", "n_escenarios_materiales": len(malos),
                "max_coste_en_ic90": max([f["coste_D2"] for f in filas if f["ramo"] == l and f["en_ic90_beta"]] + [0.0]),
                "max_coste_rejilla_b": max(f["coste_D2"] for f in filas if f["ramo"] == l),
                "max_abs_delta_a_Z_rejilla_b": max(abs(f["delta_a_Z"]) for f in filas if f["ramo"] == l)}
salida["clasificacion"] = clase
salida["segundos"] = round(time.time() - t0, 1)
SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(clase, indent=1))
