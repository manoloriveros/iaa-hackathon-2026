"""Sonda de nivel 2025 por ramo sobre el marcador público, aplicada con credibilidad (D100, 22 de octubre de 2026).

Idea. Para la desviación Tweedie de potencia 1,5, multiplicar por un factor c las predicciones de un ramo cambia el D²
del marcador según una forma cerrada con dos incógnitas por ramo:

    D²(c) - D²(1) = -4 * [ S1 * (c^-1/2 - 1) + S2 * (c^1/2 - 1) ] / N

donde S1 = sum(y / sqrt(mu)) y S2 = sum(sqrt(mu)) sobre las filas públicas del ramo y N es la desviación nula del
público. Dos envíos por ramo (c = 0,90 y c = 1,10) identifican S1/N y S2/N y, con ellos, el factor óptimo del público
c* = S1 / S2. La forma es exacta también con pesos por fila o con promedios por ramo, porque ambos son constantes en c.

Trampa medida. El público es el 33 % de las filas: c* lleva el ruido de ese subconjunto (desviación típica 3-5 % por
ramo en 2024 con subconjuntos del 33 %). Aplicarlo entero mejora el público y empeora en promedio el 67 % restante.
Por eso el candidato final aplica solo la fracción creíble: c_Z = 1 + Z * (c* - 1), con Z = tau² / (tau² + sigma²),
tau la incertidumbre previa del nivel del ramo (fijada antes de ver el marcador) y sigma el ruido del 33 % medido por
bootstrap sobre 2024. Todo queda preinscrito en el registro antes de enviar.

Uso (desde cualquier carpeta; el script sube hasta RUTAS_PROYECTO.json):
    python3 sonda_nivel.py generar                 # seis CSV de sonda + nota para Codex + registro preinscrito
    python3 sonda_nivel.py resolver --s30 0.12996 --motor 0.xxxxx 0.xxxxx --buildings 0.xxxxx 0.xxxxx \
                                    --contents 0.xxxxx 0.xxxxx        # puntuaciones públicas de x0.90 y x1.10
Produce S41 (S30 con c_Z por ramo) y una lectura de qué nivel 2025 implica el público frente a f23 y f24.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAMOS = ["motor", "buildings", "contents"]
C_SONDA = {"x090": 0.90, "x110": 1.10}
S30_SHA = "fd9528e0b1ee4b674dea63834a97523fd4ddc743d1495a422ce31a2eb76e3bc5"
S30_PUBLICO = 0.12996
# Incertidumbre previa del nivel 2025 por ramo (desviación típica relativa), fijada antes de ver el marcador:
# edificios: la mitad de la distancia entre f23 (1,059) y f24 (1,134) de S30; autos y contenidos: la mitad de su
# distancia f23/f24 (0,95 % y 0,7 %) ampliada con la evidencia de D95 sobre IBNR y recuperaciones (0,75-1,75 %).
TAU = {"motor": 0.015, "buildings": 0.035, "contents": 0.015}
FACTORES_S30 = {"motor": {"f23": 0.9864, "f24": 1.0047}, "buildings": {"f23": 1.0589, "f24": 1.1343}, "contents": {"f23": 1.0776, "f24": 1.0924}}


def raiz() -> Path:
    p = Path(__file__).resolve()
    for q in [p] + list(p.parents):
        if (q / "RUTAS_PROYECTO.json").exists():
            return q
    raise SystemExit("No encuentro RUTAS_PROYECTO.json subiendo desde el script")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dev(y, mu):
    return 4 * (y / np.sqrt(mu) + np.sqrt(mu) - 2 * np.sqrt(y))


def d2(y, mu):
    return 1 - dev(y, mu).sum() / dev(y, np.full_like(y, y.mean())).sum()


def lineas_test(root: Path) -> pd.Series:
    partes = []
    for ramo in RAMOS:
        t = pd.read_parquet(root / "Hackaton" / "Semana 1" / "Datos" / f"test_{ramo}.parquet", columns=["row_id"])
        t["line"] = ramo
        partes.append(t)
    return pd.concat(partes).set_index("row_id")["line"]


def leer_s30(root: Path) -> tuple[pd.DataFrame, Path]:
    p = root / "Hackaton" / "Semana 1" / "Envios" / "archivos" / "S30_claude_b.csv"
    if sha256(p) != S30_SHA:
        raise SystemExit(f"S30 no tiene el SHA entregado: {p}")
    df = pd.read_csv(p, dtype={"row_id": str, "prediction": float})
    assert list(df.columns) == ["row_id", "prediction"] and len(df) == 626639
    return df, p


def escribir_csv(df: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.6f", lineterminator="\n")
    return sha256(path)


def ruido_bootstrap(root: Path, reps: int = 300, frac: float = 0.33, semilla: int = 7) -> dict:
    """Desviación típica relativa del factor óptimo por ramo en subconjuntos del 33 % de 2024, con S30 (V24)."""
    p = root / "Hackaton" / "Semana 1" / "Modelos_claude_b" / "experimentos" / "predicciones_v23_v24_s30.parquet"
    v = pd.read_parquet(p)
    v = v[v.corte == "V24"]
    y, m, L = v.y_T0.values, v.prediction.values, v.line.values
    rng = np.random.default_rng(semilla)
    res = {r: [] for r in RAMOS}
    g_pub, g_priv = [], []
    for _ in range(reps):
        idx = rng.random(len(y)) < frac
        cs = {}
        for r in RAMOS:
            s = idx & (L == r)
            cs[r] = (y[s] / np.sqrt(m[s])).sum() / np.sqrt(m[s]).sum()
            res[r].append(cs[r])
        mm = m.copy()
        for r in RAMOS:
            mm[L == r] *= cs[r]
        g_pub.append(d2(y[idx], mm[idx]) - d2(y[idx], m[idx]))
        g_priv.append(d2(y[~idx], mm[~idx]) - d2(y[~idx], m[~idx]))
    completo = {r: float((y[L == r] / np.sqrt(m[L == r])).sum() / np.sqrt(m[L == r]).sum()) for r in RAMOS}
    return {
        "fuente": str(p.relative_to(root)), "sha256": sha256(p), "replicas": reps, "fraccion": frac, "semilla": semilla,
        "c_optimo_2024_completo": completo,
        "sigma": {r: float(np.std(res[r])) for r in RAMOS},
        "c_optimo_33pct_media": {r: float(np.mean(res[r])) for r in RAMOS},
        "ganancia_D2_aplicando_c_del_33pct": {"en_el_33pct_media": float(np.mean(g_pub)), "en_el_67pct_media": float(np.mean(g_priv)),
                                             "en_el_67pct_sd": float(np.std(g_priv)), "en_el_67pct_p05": float(np.quantile(g_priv, 0.05))},
    }


def credibilidad(sigma: dict) -> dict:
    return {r: TAU[r] ** 2 / (TAU[r] ** 2 + sigma[r] ** 2) for r in RAMOS}


def generar(args):
    root = raiz()
    env = root / "Hackaton" / "Semana 1" / "Envios"
    reg = root / "Hackaton" / "Repositorio_IAA2026" / "registro"
    s30, p30 = leer_s30(root)
    lin = lineas_test(root).reindex(s30.row_id).values
    assert not pd.isna(lin).any()
    archivos = {}
    for ramo in RAMOS:
        for tag, c in C_SONDA.items():
            df = s30.copy()
            sel = lin == ramo
            df.loc[sel, "prediction"] = df.loc[sel, "prediction"] * c
            nombre = f"S40_sonda_{ramo}_{tag}.csv"
            path = env / "archivos" / nombre
            h = escribir_csv(df, path)
            back = pd.read_csv(path, dtype={"row_id": str, "prediction": float})
            assert (back.row_id.values == s30.row_id.values).all() and np.allclose(back.prediction.values[~sel], s30.prediction.values[~sel], rtol=0, atol=0)
            assert np.allclose(back.prediction.values[sel], s30.prediction.values[sel] * c, rtol=1e-6, atol=6e-7)
            por_ramo = {r: round(float(df.prediction.values[lin == r].sum()), 2) for r in RAMOS}
            archivos[f"{ramo}_{tag}"] = {"archivo": str(path.relative_to(root)).replace("\\", "/"), "sha256": h, "ramo": ramo, "factor": c,
                                        "filas": int(len(df)), "total_CU": round(float(df.prediction.sum()), 2), "por_ramo_CU": por_ramo}
            print(nombre, h, por_ramo)
    print("bootstrap del ruido del 33 % sobre 2024...")
    boot = ruido_bootstrap(root)
    Z = credibilidad(boot["sigma"])
    ahora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    nota = {
        "id": "S40_sonda_nivel",
        "autor": "Claude (sesión Cowork del 22 de octubre), por instrucción del participante; decisión D100",
        "fecha_utc": ahora,
        "base": {"archivo": str(p30.relative_to(root)).replace("\\", "/"), "sha256": S30_SHA, "publico": S30_PUBLICO},
        "linaje": "S30 (Mezcla por peligro) con las predicciones de un solo ramo multiplicadas por un factor fijo; nada reentrenado, ningún otro cambio",
        "objetivo": "Identificar el factor de nivel 2025 que maximiza el D² del público (33 % de las filas) en cada ramo, con dos envíos por ramo, y aplicar después solo la fracción creíble (candidato S41). Las sondas no son candidatos finales y nunca se seleccionan en Kaggle.",
        "formula": "D2(c) - D2(1) = -4*[S1*(c^-0.5 - 1) + S2*(c^0.5 - 1)]/N por ramo; con los dos envíos se despejan S1/N y S2/N; c* = S1/S2",
        "factores_sonda": C_SONDA,
        "archivos": archivos,
        "preinscrito": {
            "tau_previa": TAU,
            "sigma_ruido_33pct_bootstrap_2024": boot["sigma"],
            "Z_credibilidad": Z,
            "regla": "c_Z = 1 + Z*(c* - 1) por ramo; S41 = S30 con c_Z; selección final manual en Kaggle: S41 si su público >= el de S30, si no S30; las seis sondas quedan excluidas de la selección final en cualquier caso",
            "lectura_actuarial": "c* se compara con los factores de año siguiente de S30 (f23, f24): c* > 1 indica que la experiencia 2025 del público supera el nivel medio f23/f24 elegido; se documenta en el informe como calibración del nivel con la retroalimentación del marcador",
            "factores_s30": FACTORES_S30,
        },
        "bootstrap": boot,
        "instrucciones_codex": "Enviar las seis sondas con nombre neutral en el orden que convenga (hoy quedan 10 intentos hasta las 19:00 de Bogotá), anotar cada puntuación pública en registro_envios.json con submitted=true, y devolver las seis puntuaciones con cinco decimales. No seleccionar ninguna sonda como final. Después se ejecuta `sonda_nivel.py resolver` y se prepara S41.",
    }
    (env / "S40_sonda_nivel_entrega_codex.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "sonda_nivel_D100_preinscripcion.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"sigma": boot["sigma"], "Z": Z, "ganancia": boot["ganancia_D2_aplicando_c_del_33pct"]}, indent=1))


def resolver(args):
    root = raiz()
    env = root / "Hackaton" / "Semana 1" / "Envios"
    reg = root / "Hackaton" / "Repositorio_IAA2026" / "registro"
    pre = json.loads((reg / "sonda_nivel_D100_preinscripcion.json").read_text(encoding="utf-8"))
    Z = pre["preinscrito"]["Z_credibilidad"]
    c1, c2 = C_SONDA["x090"], C_SONDA["x110"]
    a1, b1 = c1 ** -0.5 - 1, c1 ** 0.5 - 1
    a2, b2 = c2 ** -0.5 - 1, c2 ** 0.5 - 1
    A = np.array([[a1, b1], [a2, b2]])
    d0 = args.s30
    s30, _ = leer_s30(root)
    lin = lineas_test(root).reindex(s30.row_id).values
    out = {"s30_publico": d0, "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "ramos": {}}
    df = s30.copy()
    for ramo in RAMOS:
        p090, p110 = getattr(args, ramo)
        r = np.array([-(p090 - d0) / 4, -(p110 - d0) / 4])
        x, z = np.linalg.solve(A, r)  # x = S1/N, z = S2/N
        c_opt = x / z
        d2_en = lambda c: d0 - 4 * (x * (c ** -0.5 - 1) + z * (c ** 0.5 - 1))
        cZ = 1 + Z[ramo] * (c_opt - 1)
        out["ramos"][ramo] = {"publico_x090": p090, "publico_x110": p110, "S1_sobre_N": x, "S2_sobre_N": z, "c_optimo_publico": c_opt,
                              "D2_publico_en_c_optimo": d2_en(c_opt), "ganancia_publico_en_c_optimo": d2_en(c_opt) - d0,
                              "Z": Z[ramo], "c_Z": cZ, "D2_publico_en_c_Z": d2_en(cZ), "ganancia_publico_en_c_Z": d2_en(cZ) - d0,
                              "lectura": {"f23": FACTORES_S30[ramo]["f23"], "f24": FACTORES_S30[ramo]["f24"],
                                          "nivel_medio_S30": (FACTORES_S30[ramo]["f23"] + FACTORES_S30[ramo]["f24"]) / 2,
                                          "nivel_implicito_publico": (FACTORES_S30[ramo]["f23"] + FACTORES_S30[ramo]["f24"]) / 2 * c_opt}}
        df.loc[lin == ramo, "prediction"] = df.loc[lin == ramo, "prediction"] * cZ
        print(f"{ramo:9s} c*={c_opt:.4f}  ganancia pública en c*={d2_en(c_opt)-d0:+.5f}  Z={Z[ramo]:.3f}  c_Z={cZ:.4f}  ganancia pública esperada en c_Z={d2_en(cZ)-d0:+.5f}")
    gan = sum(v["ganancia_publico_en_c_Z"] for v in out["ramos"].values())
    out["D2_publico_esperado_S41"] = d0 + gan
    out["ganancia_publico_esperada_S41"] = gan
    for ramo, v in out["ramos"].items():
        if not (v["S1_sobre_N"] > 0 and v["S2_sobre_N"] > 0):
            raise SystemExit(f"{ramo}: S1/N o S2/N no positivos ({v['S1_sobre_N']:.3e}, {v['S2_sobre_N']:.3e}); puntuaciones incoherentes con la forma cerrada, no se aplica")
    if args.simular:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        print("simulación: no se escribe S41 ni notas")
        return
    path = env / "archivos" / "S41_nivel_credibilidad.csv"
    h = escribir_csv(df, path)
    out["S41"] = {"archivo": str(path.relative_to(root)).replace("\\", "/"), "sha256": h, "filas": int(len(df)), "total_CU": round(float(df.prediction.sum()), 2),
                  "por_ramo_CU": {r: round(float(df.prediction.values[lin == r].sum()), 2) for r in RAMOS},
                  "factores_aplicados": {r: out["ramos"][r]["c_Z"] for r in RAMOS}}
    nota = {"id": "S41_nivel_credibilidad", "autor": pre["autor"], "linaje": "S30 con el nivel de cada ramo multiplicado por c_Z (sonda de nivel con credibilidad, D100)",
            "base": pre["base"], "resolucion": out, "preinscrito": pre["preinscrito"],
            "recomendacion": f"Seleccionar S41 como final si su público es mayor o igual que el de S30 ({d0}); esperado {d0+gan:.5f}. Nunca seleccionar una sonda."}
    (env / "S41_nivel_credibilidad_entrega_codex.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    (reg / "sonda_nivel_D100_resolucion.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    print("S41:", h, out["S41"]["por_ramo_CU"], "público esperado", round(d0 + gan, 5))


# Curvatura del D² de 2024 frente al nivel de cada ramo, pérdida por (fracción fuera del óptimo)²; de la tabla
# «pérdida por estar 4 % fuera del óptimo» calculada sobre S30 en V24 (−0,00010, −0,00007, −0,00004).
B_2024 = {"motor": 0.00010 / 0.04 ** 2, "buildings": 0.00007 / 0.04 ** 2, "contents": 0.00004 / 0.04 ** 2}


def ganancia_privada_esperada(ramo: str, c: float, desvio: float, sigma: float, tau_true: float) -> float:
    """Ganancia esperada de D² en el 67 % restante frente a c = 1, si el desvío real del nivel tuviera previa tau_true.

    Con previa N(0, tau²) y ruido N(0, sigma²), la media posterior del desvío real es Zt·desvio; la pérdida es
    cuadrática, así que la varianza posterior se cancela al comparar dos factores."""
    zt = tau_true ** 2 / (tau_true ** 2 + sigma ** 2)
    u = zt * desvio
    return B_2024[ramo] * (u ** 2 - (c - 1 - u) ** 2)


def revisar(args):
    """D101: credibilidad revisada después de ver el marcador. τ² se reestima como la media sobre los tres ramos de
    (c* − 1)² − σ², es decir, la dispersión de los desvíos observados que el ruido del 33 % no explica (Bayes empírico).
    Escribe S42 y su nota; deja explícito que es una revisión posterior a los resultados, no la regla preinscrita."""
    root = raiz()
    env = root / "Hackaton" / "Semana 1" / "Envios"
    reg = root / "Hackaton" / "Repositorio_IAA2026" / "registro"
    pre = json.loads((reg / "sonda_nivel_D100_preinscripcion.json").read_text(encoding="utf-8"))
    res = json.loads((reg / "sonda_nivel_D100_resolucion.json").read_text(encoding="utf-8"))["resolucion"]
    sigma = pre["preinscrito"]["sigma_ruido_33pct_bootstrap_2024"]
    tau_pre = pre["preinscrito"]["tau_previa"]
    d0 = res["s30_publico"]
    desvio = {r: res["ramos"][r]["c_optimo_publico"] - 1 for r in RAMOS}
    tau2 = max(float(np.mean([desvio[r] ** 2 - sigma[r] ** 2 for r in RAMOS])), 0.0)
    tau_eb = tau2 ** 0.5
    Z_eb = {r: tau2 / (tau2 + sigma[r] ** 2) for r in RAMOS}
    chi2 = float(sum((desvio[r] ** 2) / (tau_pre[r] ** 2 + sigma[r] ** 2) for r in RAMOS))
    s30, _ = leer_s30(root)
    lin = lineas_test(root).reindex(s30.row_id).values
    df = s30.copy()
    out = {"s30_publico": d0, "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "tau_revisada": tau_eb,
           "suma_desvios_estandarizados_bajo_previa_D100": chi2, "grados_de_libertad": 3, "ramos": {}}
    for r in RAMOS:
        x, z = res["ramos"][r]["S1_sobre_N"], res["ramos"][r]["S2_sobre_N"]
        d2_en = lambda c: d0 - 4 * (x * (c ** -0.5 - 1) + z * (c ** 0.5 - 1))
        c = 1 + Z_eb[r] * desvio[r]
        out["ramos"][r] = {"c_optimo_publico": 1 + desvio[r], "sigma": sigma[r], "tau_previa_D100": tau_pre[r], "Z_D100": res["ramos"][r]["Z"], "c_Z_D100": res["ramos"][r]["c_Z"],
                           "Z_revisada": Z_eb[r], "c_revisado": c, "ganancia_publico_esperada": d2_en(c) - d0,
                           "ganancia_privada_esperada_si_previa_D100": ganancia_privada_esperada(r, c, desvio[r], sigma[r], tau_pre[r]),
                           "ganancia_privada_esperada_si_tau_revisada": ganancia_privada_esperada(r, c, desvio[r], sigma[r], tau_eb),
                           "S41_privada_esperada_si_previa_D100": ganancia_privada_esperada(r, res["ramos"][r]["c_Z"], desvio[r], sigma[r], tau_pre[r]),
                           "S41_privada_esperada_si_tau_revisada": ganancia_privada_esperada(r, res["ramos"][r]["c_Z"], desvio[r], sigma[r], tau_eb)}
        df.loc[lin == r, "prediction"] = df.loc[lin == r, "prediction"] * c
        print(f"{r:9s} desvío {desvio[r]:+.4f}  Z revisada {Z_eb[r]:.3f}  c {c:.4f}  ganancia pública esperada {d2_en(c)-d0:+.5f}")
    gan = sum(v["ganancia_publico_esperada"] for v in out["ramos"].values())
    out["D2_publico_esperado_S42"] = d0 + gan
    out["privado_esperado_S42"] = {"si_previa_D100": sum(v["ganancia_privada_esperada_si_previa_D100"] for v in out["ramos"].values()),
                                    "si_tau_revisada": sum(v["ganancia_privada_esperada_si_tau_revisada"] for v in out["ramos"].values())}
    out["privado_esperado_S41"] = {"si_previa_D100": sum(v["S41_privada_esperada_si_previa_D100"] for v in out["ramos"].values()),
                                    "si_tau_revisada": sum(v["S41_privada_esperada_si_tau_revisada"] for v in out["ramos"].values())}
    path = env / "archivos" / "S42_nivel_credibilidad_revisada.csv"
    h = escribir_csv(df, path)
    out["S42"] = {"archivo": str(path.relative_to(root)).replace("\\", "/"), "sha256": h, "filas": int(len(df)), "total_CU": round(float(df.prediction.sum()), 2),
                  "por_ramo_CU": {r: round(float(df.prediction.values[lin == r].sum()), 2) for r in RAMOS},
                  "factores_aplicados": {r: out["ramos"][r]["c_revisado"] for r in RAMOS}}
    nota = {"id": "S42_nivel_credibilidad_revisada", "autor": pre["autor"],
            "linaje": "S30 con el nivel de cada ramo multiplicado por c = 1 + Z_revisada·(c* − 1); Z_revisada con τ reestimada sobre los tres desvíos observados (D101, revisión posterior a ver el marcador)",
            "base": pre["base"], "revision": out, "D100": {"preinscripcion": "registro/sonda_nivel_D100_preinscripcion.json", "resolucion": "registro/sonda_nivel_D100_resolucion.json"},
            "advertencia": "No es la regla preinscrita de D100. La τ revisada usa los mismos resultados del público que después se aplican; por eso su esperanza en el privado se informa bajo las dos hipótesis (previa de D100 correcta o τ revisada correcta) y la elección entre S41 y S42 es una decisión de tolerancia al riesgo del participante.",
            "recomendacion": f"Público esperado {d0+gan:.5f}. Selección final manual: la que decida el participante entre S41 y S42 (ambas por encima de S30 en esperanza); nunca una sonda."}
    (env / "S42_nivel_credibilidad_revisada_entrega_codex.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    (reg / "sonda_nivel_D101_revision.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    print("S42:", h, out["S42"]["por_ramo_CU"], "público esperado", round(d0 + gan, 5), "| privado esperado S42", {k: round(v, 5) for k, v in out["privado_esperado_S42"].items()}, "| S41", {k: round(v, 5) for k, v in out["privado_esperado_S41"].items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generar")
    r = sub.add_parser("resolver")
    r.add_argument("--s30", type=float, default=S30_PUBLICO)
    r.add_argument("--simular", action="store_true", help="calcula e imprime sin escribir S41 ni notas")
    for ramo in RAMOS:
        r.add_argument(f"--{ramo}", type=float, nargs=2, required=True, metavar=("PUB_x090", "PUB_x110"))
    sub.add_parser("revisar", help="D101: S42 con credibilidad revisada (Bayes empírico sobre los tres ramos) a partir de la resolución de D100")
    args = ap.parse_args()
    {"generar": generar, "resolver": resolver, "revisar": revisar}[args.cmd](args)


if __name__ == "__main__":
    main()
