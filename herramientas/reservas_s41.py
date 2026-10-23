"""Acotación de reservas con la regla de nivel de S41, la entrega final (corrida repro_s41_20261023T145808Z_c8055dfc, parte 2).

S41 es la Mezcla por peligro (S30) con un factor de nivel por ramo, c = 1 + Z·(c* − 1), donde c* es el óptimo del público
que despejan las seis sondas y Z = τ²/(τ² + σ²) la credibilidad fijada antes de mirar (D100): τ es una previa y σ está
registrada, así que Z es fija y un ramo no influye en los otros. Importa sin cambios la clase Nivel de
herramientas/reservas_consistencia.py: ρ es el nivel relativo de S30 en un ramo si la reserva de caso valiera b veces lo
reservado y el IBNR k veces lo estimado. El óptimo del público en nivel absoluto no depende de nuestras etiquetas, de modo
que el relativo pasa a c*/ρ y el nivel relativo de S41 es ρ·c(escenario)/c(registrado). Umbrales por primer cruce desde
b = 1 (rejilla de paso 0,0025 hasta 3 y 0,05 hasta 20, afinada por bisección), con la materialidad del 1 %.

Uso: python3 reservas_s41.py <repo> <corrida_reservas> <registro_D100> <parquet_S30> <salida.json>
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
rc.PRED["S30"] = PQ
L = rc.LINES
MAT = rc.MATERIALIDAD


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


pre = json.loads((REG / "sonda_nivel_D100_preinscripcion.json").read_text(encoding="utf-8"))["preinscrito"]
res = json.loads((REG / "sonda_nivel_D100_resolucion.json").read_text(encoding="utf-8"))["resolucion"]
SIG = pre["sigma_ruido_33pct_bootstrap_2024"]
TAU = pre["tau_previa"]
CST = {l: res["ramos"][l]["c_optimo_publico"] for l in L}
S1N = {l: res["ramos"][l]["S1_sobre_N"] for l in L}
S2N = {l: res["ramos"][l]["S2_sobre_N"] for l in L}
Z41 = {l: res["ramos"][l]["Z"] for l in L}
C41 = {l: res["ramos"][l]["c_Z"] for l in L}
pa = json.loads((RUN / "resultados" / "parte_a.json").read_text(encoding="utf-8"))
pb = json.loads((RUN / "resultados" / "parte_b.json").read_text(encoding="utf-8"))
NV = {l: rc.Nivel(RUN, "S30", l) for l in L}


def zeta(sig: dict) -> dict:
    return {l: TAU[l] ** 2 / (TAU[l] ** 2 + sig[l] ** 2) for l in L}


def nivel41(line, rho, z=Z41, base=C41):
    """Nivel relativo de S41 en el ramo, dado el nivel relativo ρ de S30 en ese ramo bajo el escenario."""
    c = 1 + z[line] * (CST[line] / rho - 1)
    return rho * c / base[line]


def rho_de(line, tipo, ps, x):
    sc = {p: x for p in ps}
    return NV[line].nivel(sc, None)["nivel"] if tipo == "b" else NV[line].nivel({}, sc)["nivel"]


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
        _RHO[clave] = {lado: [(float(x), rho_de(line, tipo, ps, float(x))) for x in xs] for lado, xs in (("arriba", ARRIBA), ("abajo", ABAJO[tipo]))}
    return _RHO[clave]


def primer_cruce(line, tipo, ps, lado, **kw):
    previo = 1.0
    for x, rho in rejilla(line, tipo, ps)[lado]:
        if abs(nivel41(line, rho, **kw) - 1) >= MAT:
            a, b_ = previo, x
            for _ in range(50):
                mid = (a + b_) / 2
                if abs(nivel41(line, rho_de(line, tipo, ps, mid), **kw) - 1) >= MAT:
                    b_ = mid
                else:
                    a = mid
            return {"x": b_, "movimiento": nivel41(line, rho_de(line, tipo, ps, b_), **kw) - 1}
        previo = x
    return None


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
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, float):
        return r6(o)
    return o


def bloque(**kw):
    out = {}
    for line in L:
        g = {}
        for gn, ps in grupos(line).items():
            u = {}
            for tipo, nombre in (("b", "reserva_b"), ("k", "ibnr_k")):
                for lado, tag in (("abajo", "menos"), ("arriba", "mas")):
                    u[f"{nombre}_{tag}"] = primer_cruce(line, tipo, ps, lado, **kw)
            for b in (0.75, 0.9, 1.1, 1.25):
                u[f"nivel_b_{b}"] = nivel41(line, rho_de(line, "b", ps, b), **kw) - 1
            g[gn] = u
        ram = pa[line]["peligros"]["_ramo"]["todos"]
        ic, bp = ram["ic90_beta"], ram["beta_reserva"]
        u = g["todos"]
        lo, hi = x_de(u["reserva_b_menos"]), x_de(u["reserva_b_mas"])
        beta = {"beta_reserva": bp, "ic90": ic, "umbral_b": [r6(lo), r6(hi)], "clase": clase(ic, lo, hi, "S1"),
                "nivel_S41_con_beta_puntual": nivel41(line, rho_de(line, "b", rc.PERILS[line], bp), **kw) - 1}
        if line in rc.LARGOS:
            p = rc.LARGOS[line]
            vl = pa[line]["peligros"][p]["todos"]
            ul = g[p]
            beta["peligro_largo"] = {"peligro": p, "beta": vl["beta_reserva"], "ic90": vl["ic90_beta"],
                                     "umbral_b": [r6(x_de(ul["reserva_b_menos"])), r6(x_de(ul["reserva_b_mas"]))],
                                     "clase": clase(vl["ic90_beta"], x_de(ul["reserva_b_menos"]), x_de(ul["reserva_b_mas"]), "S1")}
        ib = {}
        for p in rc.PERILS[line]:
            v = pa["A3"][line][p]["2021_2022"]
            kk, ick = v.get("k_frente_a_D67"), v.get("ic90_k")
            if kk is None or not ick or None in ick:
                continue
            lo_k = primer_cruce(line, "k", [p], "abajo", **kw)
            hi_k = primer_cruce(line, "k", [p], "arriba", **kw)
            ib[p] = {"k": kk, "ic90_k": ick, "umbral_k": [r6(x_de(lo_k)), r6(x_de(hi_k))], "clase": clase(ick, x_de(lo_k), x_de(hi_k), "S3"),
                     "nivel_S41_con_k": nivel41(line, NV[line].nivel({}, {p: kk})["nivel"], **kw) - 1,
                     "nivel_S41_con_ic90_k": [nivel41(line, NV[line].nivel({}, {p: x})["nivel"], **kw) - 1 for x in ick]}
        out[line] = limpio({"umbrales": g, "beta_S1": beta, "ibnr_S3": ib})
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
    out = {"herramienta": "reservas_s41.py", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "materialidad": MAT,
           "fuentes_sha256": {"reservas_consistencia.py": sha(REPO / "herramientas" / "reservas_consistencia.py"), "parquet_S30": sha(PQ),
                              **{n: sha(REG / n) for n in ("sonda_nivel_D100_preinscripcion.json", "sonda_nivel_D100_resolucion.json")},
                              **{f"reservas/{n}": sha(RUN / "resultados" / n) for n in ("datos.json", "parte_a.json", "parte_b.json", "reserva_fila_peligro.parquet")}},
           "regla": {"c_optimo_publico": CST, "Z_D100": Z41, "tau": TAU, "sigma": SIG, "factores_S41": C41}}
    # control: sin escenario se recuperan los factores de S41 y Z de la previa y σ registradas
    rho1 = {l: NV[l].nivel({}, {})["nivel"] for l in L}
    zr = zeta(SIG)
    out["control"] = {"rho_S30_en_b1": rho1, "nivel_S41_en_b1": {l: nivel41(l, 1.0) for l in L},
                      "dif_relativa_max": max([abs(1 + Z41[l] * (CST[l] - 1) - C41[l]) / C41[l] for l in L] + [abs(zr[l] - Z41[l]) / Z41[l] for l in L]),
                      "sensibilidad_primer_orden_(1-Z)/c": {l: (1 - Z41[l]) / C41[l] for l in L}}
    # control 2: los umbrales de S30 de la misma clase coinciden con parte_b.json (4 decimales)
    ctrl = {}
    for line in L:
        for gn, ps in grupos(line).items():
            fb = lambda x: NV[line].nivel({p: x for p in ps})["nivel"]
            lo, hi = rc._umbral(fb, 1 - MAT, 0.05, 1.0), rc._umbral(fb, 1 + MAT, 1.0, 20.0)
            reg = pb["ramos"][line]["umbrales"][gn]
            ctrl[f"{line}/{gn}"] = {"S30_recalculado": [r6(lo), r6(hi)], "S30_registro": [reg["reserva_b_menos_1pct"], reg["reserva_b_mas_1pct"]],
                                    "coincide_a_4_decimales": [round(lo, 4), round(hi, 4)] == [reg["reserva_b_menos_1pct"], reg["reserva_b_mas_1pct"]]}
    out["control_umbrales_S30"] = ctrl
    # a, b, c: regla de D100 tal como se aplicó
    out["principal"] = bloque()
    # e: σ ampliada a σ/√0,67; la regla daría otros factores
    sig_e = {l: SIG[l] / 0.67 ** 0.5 for l in L}
    z_e = zeta(sig_e)
    c_e = {l: 1 + z_e[l] * (CST[l] - 1) for l in L}
    out["variante_sigma_ampliada"] = {"sigma": sig_e, "Z": z_e, "factores_que_daria_la_regla": c_e, **bloque(z=z_e, base=c_e)}
    # d: σ recalculada con las etiquetas del escenario en los umbrales de la regla aplicada
    d_ = {}
    for line in L:
        u = out["principal"][line]["umbrales"]["todos"]
        d_[line] = {"sigma_registro": SIG[line], "sigma_b1_recalculada": sigma_con_etiquetas(line, 1.0)}
        for clave in ("reserva_b_menos", "reserva_b_mas"):
            if u[clave] is None:
                continue
            b = u[clave]["x"]
            sb = sigma_con_etiquetas(line, b)
            z_b = dict(Z41)
            z_b[line] = TAU[line] ** 2 / (TAU[line] ** 2 + sb ** 2)
            nuevo = primer_cruce(line, "b", rc.PERILS[line], "abajo" if "menos" in clave else "arriba", z=z_b)
            d_[line][clave] = {"b": b, "sigma_con_etiquetas_del_escenario": sb, "Z_con_esa_sigma": z_b[line],
                               "nivel_S41_en_ese_b": nivel41(line, rho_de(line, "b", rc.PERILS[line], b), z=z_b) - 1,
                               "umbral_con_esa_sigma": x_de(nuevo), "desplazamiento_del_umbral": None if nuevo is None else nuevo["x"] - b}
    out["comprobacion_sigma_con_etiquetas"] = d_

    # f: coste en el D² público de un 1 % de nivel alrededor de S41 (cambio frente a S30, forma cerrada)
    def dD2(l, c):
        return -4 * (S1N[l] * (c ** -0.5 - 1) + S2N[l] * (c ** 0.5 - 1))
    f = {}
    for l in L:
        f[l] = {"S41_menos_1pct": dD2(l, C41[l] * 0.99) - dD2(l, C41[l]), "S41_mas_1pct": dD2(l, C41[l] * 1.01) - dD2(l, C41[l]),
                "ganancia_S41_frente_S30": dD2(l, C41[l]), "ganancia_en_el_optimo_publico": dD2(l, CST[l])}
    f["agregado_tres_ramos"] = {k: sum(f[l][k] for l in L) for k in f["motor"]}
    out["coste_D2_publico"] = f
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps({"control": out["control"]["dif_relativa_max"], "control_umbrales_S30": all(v["coincide_a_4_decimales"] for v in ctrl.values())}))
    for v in ("principal", "variante_sigma_ampliada"):
        for l in L:
            p = out[v][l]["beta_S1"]
            print(v, l, p["umbral_b"], p["clase"], p.get("peligro_largo", {}).get("umbral_b"), p.get("peligro_largo", {}).get("clase"))


if __name__ == "__main__":
    main()
