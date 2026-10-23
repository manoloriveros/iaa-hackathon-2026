"""Acotación de reservas con la regla de nivel de S42 (corrida repro_s42_20261022T170245Z_c9ea2fc3, parte 2 del plan).

Importa sin cambios la clase Nivel de herramientas/reservas_consistencia.py (nivel relativo de S30 en un ramo si la
reserva de caso valiera b veces lo reservado y el IBNR k veces lo estimado) y le aplica la regla de D101: el óptimo del
público en nivel absoluto no depende de nuestras etiquetas, así que el óptimo relativo del ramo pasa a c*/ρ; τ² se
reestima con los tres desvíos, Z = τ²/(τ² + σ²) y c = 1 + Z·(c* − 1). Nivel relativo de S42: ρ·c(escenario)/c(1).
Corrección registrada después de la primera ejecución (reservas_s42_v1_biseccion.py, salida parte2_biseccion_literal.json):
con τ reestimada el nivel de S42 no es monótono en b y un escenario en un ramo mueve los otros dos a través de τ, así que
la bisección de la acotación de S30 en [0,05; 1] y [1; 20] puede devolver un cruce lejano y saltarse el primero. Esta
versión recorre una rejilla desde b = 1 hacia fuera (paso 0,0025 hasta 3 y 0,05 hasta 20) y afina por bisección el primer
punto en que el nivel del ramo (umbral propio, criterio preinscrito) o el de cualquiera de los tres ramos (umbral del
sistema, añadido) se aparta un 1 %.
Uso: python3 reservas_s42.py <repo> <corrida_reservas> <registro_D100_D101> <parquet_S30> <salida.json>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO, RUN, REG, PQ, SALIDA = (Path(a) for a in sys.argv[1:6])
spec = importlib.util.spec_from_file_location("reservas_consistencia", REPO / "herramientas" / "reservas_consistencia.py")
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)
rc.PRED["S30"] = PQ  # el mismo parquet histórico que usó la acotación de S30
L = rc.LINES
MAT = rc.MATERIALIDAD


def sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


pre = json.loads((REG / "sonda_nivel_D100_preinscripcion.json").read_text(encoding="utf-8"))
res = json.loads((REG / "sonda_nivel_D100_resolucion.json").read_text(encoding="utf-8"))["resolucion"]
rev = json.loads((REG / "sonda_nivel_D101_revision.json").read_text(encoding="utf-8"))["revision"]
SIG = pre["preinscrito"]["sigma_ruido_33pct_bootstrap_2024"]
CST = {l: res["ramos"][l]["c_optimo_publico"] for l in L}
S1N = {l: res["ramos"][l]["S1_sobre_N"] for l in L}
S2N = {l: res["ramos"][l]["S2_sobre_N"] for l in L}
C42 = {l: rev["ramos"][l]["c_revisado"] for l in L}
Z42 = {l: rev["ramos"][l]["Z_revisada"] for l in L}
pa = json.loads((RUN / "resultados" / "parte_a.json").read_text(encoding="utf-8"))
pb = json.loads((RUN / "resultados" / "parte_b.json").read_text(encoding="utf-8"))
NV = {l: rc.Nivel(RUN, "S30", l) for l in L}


def regla(cst: dict, sig: dict):
    """Regla de D101 con las mismas operaciones que sonda_nivel.py revisar."""
    desvio = {r: cst[r] - 1 for r in L}
    tau2 = max(float(np.mean([desvio[r] ** 2 - sig[r] ** 2 for r in L])), 0.0)
    Z = {r: tau2 / (tau2 + sig[r] ** 2) for r in L}
    return tau2, Z, {r: 1 + Z[r] * desvio[r] for r in L}


def niveles(line, rho, sig=SIG, base=C42, z_fija=None):
    """Nivel relativo de S42 en los tres ramos dado el nivel relativo ρ de S30 en `line` bajo el escenario."""
    cst = dict(CST)
    cst[line] = CST[line] / rho
    if z_fija is not None:
        c = dict(base)
        c[line] = 1 + z_fija[line] * (cst[line] - 1)
    else:
        c = regla(cst, sig)[2]
    return {j: (rho if j == line else 1.0) * c[j] / base[j] for j in L}


def rho_de(line, tipo, ps, x):
    sc = {p: x for p in ps}
    return NV[line].nivel(sc, None)["nivel"] if tipo == "b" else NV[line].nivel({}, sc)["nivel"]


def s42(line, b=None, k=None, **kw):
    return niveles(line, NV[line].nivel(b or {}, k or {})["nivel"], **kw)


def grupos(line):
    g = {"todos": rc.PERILS[line]}
    if line in rc.LARGOS:
        g[rc.LARGOS[line]] = [rc.LARGOS[line]]
        g["resto"] = [p for p in rc.PERILS[line] if p != rc.LARGOS[line]]
    return g


ARRIBA = np.concatenate([np.arange(1.0025, 3.0, 0.0025), np.arange(3.0, 20.0001, 0.05)])
ABAJO = {"b": np.arange(0.9975, 0.0499, -0.0025), "k": np.arange(0.9975, -0.0001, -0.0025)}
_RHO = {}


def rejilla(line, tipo, ps):
    clave = (line, tipo, tuple(ps))
    if clave not in _RHO:
        _RHO[clave] = {lado: [(float(x), rho_de(line, tipo, ps, float(x))) for x in xs]
                       for lado, xs in (("arriba", ARRIBA), ("abajo", ABAJO[tipo]))}
    return _RHO[clave]


def medida(line, rho, sistema, **kw):
    n = niveles(line, rho, **kw)
    if sistema:
        j = max(L, key=lambda q: abs(n[q] - 1))
    else:
        j = line
    return abs(n[j] - 1), j, n[j] - 1


def primer_cruce(line, tipo, ps, lado, sistema, **kw):
    """Primer x desde 1 hacia `lado` con |nivel − 1| >= 1 % (en el ramo o, con sistema, en cualquiera); None si no hay."""
    previo = 1.0
    for x, rho in rejilla(line, tipo, ps)[lado]:
        m, j, d = medida(line, rho, sistema, **kw)
        if m >= MAT:
            a, b_ = previo, x
            for _ in range(50):
                mid = (a + b_) / 2
                if medida(line, rho_de(line, tipo, ps, mid), sistema, **kw)[0] >= MAT:
                    b_ = mid
                else:
                    a = mid
            m, j, d = medida(line, rho_de(line, tipo, ps, b_), sistema, **kw)
            return {"x": b_, "ramo_que_cruza": j, "movimiento": d}
        previo = x
    return None


def umbrales(line, ps, **kw):
    u = {}
    for tipo, nombre in (("b", "reserva_b"), ("k", "ibnr_k")):
        for lado, tag in (("abajo", "menos"), ("arriba", "mas")):
            for sistema, sfx in ((False, "propio"), (True, "sistema")):
                u[f"{nombre}_{tag}_{sfx}"] = primer_cruce(line, tipo, ps, lado, sistema, **kw)
    for b in (0.75, 0.9, 1.1, 1.25):
        u[f"niveles_b_{b}"] = {j: v - 1 for j, v in niveles(line, rho_de(line, "b", ps, b), **kw).items()}
    return u


def x_de(v):
    return None if v is None else v["x"]


def clase(ic, lo, hi, sufijo):
    lo_e = lo if lo is not None else -np.inf
    hi_e = hi if hi is not None else np.inf
    if ic[0] >= lo_e and ic[1] <= hi_e:
        return f"acotado_bajo_materialidad_si_{sufijo}"
    if ic[1] < lo_e or ic[0] > hi_e:
        return f"indicio_de_{'sesgo' if sufijo == 'S1' else 'desvio'}_material_si_{sufijo}"
    return "incertidumbre_material"


def r6(x):
    return None if x is None else round(float(x), 6)


def limpio(o):
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, float):
        return r6(o)
    return o


def bloque(**kw):
    """Umbrales (propio y del sistema), clasificación de β (S1) y de k (S3) y efecto de S3 con una variante de la regla."""
    out = {}
    for line in L:
        g = {gn: umbrales(line, ps, **kw) for gn, ps in grupos(line).items()}
        ram = pa[line]["peligros"]["_ramo"]["todos"]
        ic, bp = ram["ic90_beta"], ram["beta_reserva"]
        u = g["todos"]
        beta = {"beta_reserva": bp, "ic90": ic}
        for sfx in ("propio", "sistema"):
            lo, hi = x_de(u[f"reserva_b_menos_{sfx}"]), x_de(u[f"reserva_b_mas_{sfx}"])
            beta[f"umbral_b_{sfx}"] = [r6(lo), r6(hi)]
            beta[f"clase_{sfx}"] = clase(ic, lo, hi, "S1")
        beta["niveles_S42_con_beta_puntual"] = {j: v - 1 for j, v in s42(line, {p: bp for p in rc.PERILS[line]}, None, **kw).items()}
        ib = {}
        for p in rc.PERILS[line]:
            v = pa["A3"][line][p]["2021_2022"]
            kk, ick = v.get("k_frente_a_D67"), v.get("ic90_k")
            if kk is None or not ick or None in ick:
                continue
            fila = {"k": kk, "ic90_k": ick}
            for sistema, sfx in ((False, "propio"), (True, "sistema")):
                lo = primer_cruce(line, "k", [p], "abajo", sistema, **kw)
                hi = primer_cruce(line, "k", [p], "arriba", sistema, **kw)
                fila[f"umbral_k_{sfx}"] = [r6(x_de(lo)), r6(x_de(hi))]
                fila[f"clase_{sfx}"] = clase(ick, x_de(lo), x_de(hi), "S3")
            fila["niveles_S42_con_k"] = {j: v_ - 1 for j, v_ in s42(line, None, {p: kk}, **kw).items()}
            fila["niveles_S42_con_ic90_k"] = [{j: v_ - 1 for j, v_ in s42(line, None, {p: x}, **kw).items()} for x in ick]
            ib[p] = fila
        k_todos = {p: v["k"] for p, v in ib.items()}
        out[line] = limpio({"umbrales": g, "beta_S1": beta,
                            "ibnr_S3": {"por_peligro": ib, "niveles_S42_con_todos_los_k": {j: v - 1 for j, v in s42(line, None, k_todos, **kw).items()}}})
    return out


def sigma_con_etiquetas(line, b, reps=300, frac=0.33, semilla=7):
    """σ del bootstrap de sonda_nivel.py (mismas réplicas) con las etiquetas del ramo modificadas por b uniforme."""
    v = pd.read_parquet(PQ)
    v = v[v.corte == "V24"]
    y, m, lin = v.y_T0.values.copy(), v.prediction.values, v.line.values
    sel = lin == line
    y[sel] = y[sel] + (b - 1.0) * v.reserva_caso.values[sel]
    rng = np.random.default_rng(semilla)
    cs = []
    for _ in range(reps):
        idx = rng.random(len(y)) < frac
        s = idx & sel
        cs.append((y[s] / np.sqrt(m[s])).sum() / np.sqrt(m[s]).sum())
    return float(np.std(cs))


def main():
    out = {"herramienta": "reservas_s42.py", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "fuentes_sha256": {"reservas_consistencia.py": sha(REPO / "herramientas" / "reservas_consistencia.py"), "parquet_S30": sha(PQ),
                              **{n: sha(REG / n) for n in ("sonda_nivel_D100_preinscripcion.json", "sonda_nivel_D100_resolucion.json", "sonda_nivel_D101_revision.json")},
                              **{f"reservas/{n}": sha(RUN / "resultados" / n) for n in ("datos.json", "parte_a.json", "parte_b.json", "reserva_fila_peligro.parquet")}},
           "materialidad": MAT}
    # control 1: la regla con b = k = 1 recupera τ, Z y los factores de D101
    tau2, Z, c = regla(CST, SIG)
    rho1 = {l: NV[l].nivel({}, {})["nivel"] for l in L}
    out["control_regla"] = {"tau": tau2 ** 0.5, "tau_registro": rev["tau_revisada"], "Z": Z, "Z_registro": Z42, "c": c, "c_registro": C42,
                            "rho_S30_en_b1": rho1,
                            "dif_relativa_max": max([abs(tau2 ** 0.5 - rev["tau_revisada"]) / rev["tau_revisada"]] +
                                                    [abs(c[l] - C42[l]) / C42[l] for l in L] + [abs(Z[l] - Z42[l]) / Z42[l] for l in L])}
    # control 2: los umbrales de S30 recalculados con la misma clase coinciden con parte_b.json (4 decimales)
    ctrl = {}
    for line in L:
        for gn, ps in grupos(line).items():
            fb = lambda x: NV[line].nivel({p: x for p in ps})["nivel"]
            lo, hi = rc._umbral(fb, 1 - MAT, 0.05, 1.0), rc._umbral(fb, 1 + MAT, 1.0, 20.0)
            reg = pb["ramos"][line]["umbrales"][gn]
            ctrl[f"{line}/{gn}"] = {"S30_recalculado": [r6(lo), r6(hi)], "S30_registro": [reg["reserva_b_menos_1pct"], reg["reserva_b_mas_1pct"]],
                                    "coincide_a_4_decimales": [round(lo, 4), round(hi, 4)] == [reg["reserva_b_menos_1pct"], reg["reserva_b_mas_1pct"]]}
    out["control_umbrales_S30"] = ctrl
    # principal: regla de D101 con τ reestimada en cada escenario
    out["principal"] = bloque()
    # d: Z fija en los valores de D101
    out["variante_Z_fija"] = bloque(z_fija=Z42)
    out["variante_Z_fija"]["sensibilidad_primer_orden_(1-Z)/c"] = {l: r6((1 - Z42[l]) / C42[l]) for l in L}
    # e: σ ampliada a σ/√0,67 (la base de la regla también se recalcula con esa σ)
    sig_e = {l: SIG[l] / 0.67 ** 0.5 for l in L}
    tau2_e, Z_e, c_e = regla(CST, sig_e)
    out["variante_sigma_ampliada"] = {"sigma": sig_e, "tau": tau2_e ** 0.5, "Z": Z_e, "factores_que_daria_la_regla": c_e, **bloque(sig=sig_e, base=c_e)}
    # f: σ recalculada con las etiquetas del escenario en los umbrales de la variante principal
    f_ = {}
    for line in L:
        u = out["principal"][line]["umbrales"]["todos"]
        f_[line] = {"sigma_registro": SIG[line], "sigma_b1_recalculada": sigma_con_etiquetas(line, 1.0)}
        for clave in ("reserva_b_menos_propio", "reserva_b_mas_propio", "reserva_b_menos_sistema", "reserva_b_mas_sistema"):
            if u[clave] is None:
                continue
            b = u[clave]["x"]
            sb = sigma_con_etiquetas(line, b)
            sig_b = dict(SIG)
            sig_b[line] = sb
            n = s42(line, {p: b for p in rc.PERILS[line]}, None, sig=sig_b)
            nuevo = primer_cruce(line, "b", rc.PERILS[line], "abajo" if "menos" in clave else "arriba", clave.endswith("sistema"), sig=sig_b)
            f_[line][clave] = {"b": b, "sigma_con_etiquetas_del_escenario": sb, "niveles_S42_en_ese_b": {j: v - 1 for j, v in n.items()},
                               "umbral_con_esa_sigma": x_de(nuevo), "desplazamiento_del_umbral": None if nuevo is None else nuevo["x"] - b}
    out["comprobacion_sigma_con_etiquetas"] = f_
    # g: coste en el D² público de un 1 % de nivel, con la forma cerrada (cambio frente a S30)
    def dD2(l, c):
        return -4 * (S1N[l] * (c ** -0.5 - 1) + S2N[l] * (c ** 0.5 - 1))
    g = {}
    for l in L:
        g[l] = {"S42_menos_1pct": dD2(l, C42[l] * 0.99) - dD2(l, C42[l]), "S42_mas_1pct": dD2(l, C42[l] * 1.01) - dD2(l, C42[l]),
                "S30_menos_1pct": dD2(l, 0.99), "S30_mas_1pct": dD2(l, 1.01), "ganancia_S42_frente_S30": dD2(l, C42[l]),
                "ganancia_en_el_optimo_publico": dD2(l, CST[l])}
    g["agregado_tres_ramos"] = {k: sum(g[l][k] for l in L) for k in g["motor"]}
    out["coste_D2_publico"] = g
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps({"control_regla": out["control_regla"]["dif_relativa_max"], "control_umbrales_S30": all(v["coincide_a_4_decimales"] for v in ctrl.values())}))
    for v in ("principal", "variante_Z_fija", "variante_sigma_ampliada"):
        for l in L:
            p = out[v][l]
            print(v, l, p["beta_S1"]["umbral_b_propio"], p["beta_S1"]["clase_propio"], p["beta_S1"]["umbral_b_sistema"], p["beta_S1"]["clase_sistema"])


if __name__ == "__main__":
    main()
