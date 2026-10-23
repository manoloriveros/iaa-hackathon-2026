"""Sonda de forma (dispersión de las relatividades) sobre el marcador público, con credibilidad (D102, 22 de octubre de 2026).

Idea. Con el nivel de cada ramo ya calibrado (S42, D100/D101), queda preguntar al público cuánto conviene confiar en las
relatividades aprendidas en 2021-2024 al pasar a 2025. Para un ramo, con tasa r = mu/e y tasa media g = sum(mu)/sum(e):

    r' = g * (r / g) ** a ;  mu' = e * r' ;  mu'' = mu' * sum(mu) / sum(mu')      (el total del ramo no cambia)

a < 1 comprime las diferencias entre pólizas, a > 1 las amplía; a = 1 deja S42 intacto. El D² del público como función
de a no tiene forma cerrada, pero cerca del óptimo es casi una parábola: con D²(0,90), D²(1,00) = S42 y D²(1,10) se
estima el vértice a* por ramo. El ruido del 33 % y la credibilidad se tratan como en D100: a_Z = 1 + Z (a* − 1), con
Z = tau² / (tau² + sigma²), tau fijada antes de ver el marcador y sigma medida por bootstrap sobre 2024.

Uso (sube hasta RUTAS_PROYECTO.json):
    python3 sonda_forma.py generar
    python3 sonda_forma.py resolver --s42 0.13033 --motor D090 D110 --buildings D090 D110 --contents D090 D110 [--simular]
    (un ramo con un solo valor usa la curvatura de 2024 como conocida: --contents D090)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAMOS = ["motor", "buildings", "contents"]
A_SONDA = {"a090": 0.90, "a110": 1.10}
H = 0.10
S42_SHA = "a2fdcccd9661abff6265b9fd6fc383ef155de87dd3b075b53327641154de62f7"
S42_PUBLICO = 0.13033
TAU_A = {"motor": 0.05, "buildings": 0.05, "contents": 0.05}  # incertidumbre previa del exponente óptimo de 2025 frente al de S42


def raiz() -> Path:
    p = Path(__file__).resolve()
    for q in [p] + list(p.parents):
        if (q / "RUTAS_PROYECTO.json").exists():
            return q
    raise SystemExit("No encuentro RUTAS_PROYECTO.json")


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


def forma(mu: np.ndarray, e: np.ndarray, a: float) -> np.ndarray:
    """Transforma un ramo entero: devuelve mu'' con el mismo total que mu."""
    g = mu.sum() / e.sum()
    mp = e * g * (mu / e / g) ** a
    return mp * (mu.sum() / mp.sum())


def test_lineas_exposicion(root: Path) -> pd.DataFrame:
    partes = []
    for ramo in RAMOS:
        t = pd.read_parquet(root / "Hackaton" / "Semana 1" / "Datos" / f"test_{ramo}.parquet", columns=["row_id", "exposure"])
        t["line"] = ramo
        partes.append(t)
    return pd.concat(partes).set_index("row_id")


def leer_s42(root: Path):
    p = root / "Hackaton" / "Semana 1" / "Envios" / "archivos" / "S42_nivel_credibilidad_revisada.csv"
    if sha256(p) != S42_SHA:
        raise SystemExit(f"S42 no tiene el SHA registrado: {p}")
    df = pd.read_csv(p, dtype={"row_id": str, "prediction": float})
    assert list(df.columns) == ["row_id", "prediction"] and len(df) == 626639
    return df, p


def escribir_csv(df: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.6f", lineterminator="\n")
    return sha256(path)


def curvatura_y_ruido(root: Path, reps: int = 200, frac: float = 0.33, semilla: int = 3) -> dict:
    """Sobre 2024 con S30 (V24): curva D²(a) por ramo, vértice de 2024, curvatura K (parábola por 0,90/1,00/1,10) y
    desviación típica del a óptimo en subconjuntos del 33 % (rejilla de 0,02)."""
    p = root / "Hackaton" / "Semana 1" / "Modelos_claude_b" / "experimentos" / "predicciones_v23_v24_s30.parquet"
    v = pd.read_parquet(p)
    v = v[v.corte == "V24"].set_index("row_id")
    ex = pd.concat([pd.read_parquet(root / "Hackaton" / "Semana 1" / "Datos" / f"policies_{l}.parquet", columns=["row_id", "exposure"]) for l in RAMOS]).set_index("row_id").exposure
    v["e"] = ex.reindex(v.index).values
    assert v.e.notna().all() and (v.e > 0).all()
    y, m, e, L = v.y_T0.values, v.prediction.values, v.e.values, v.line.values
    grid = np.round(np.arange(0.80, 1.2001, 0.02), 2)
    null = dev(y, np.full_like(y, y.mean())).sum()
    base = dev(y, m)
    D, out = {}, {}
    for l in RAMOS:
        sel = L == l
        D[l] = np.zeros((len(grid), int(sel.sum())))
        for k, a in enumerate(grid):
            D[l][k] = dev(y[sel], forma(m[sel], e[sel], a))
        tot = D[l].sum(axis=1)
        curva = {f"{a:.2f}": float(-(tot[k] - base[sel].sum()) / null) for k, a in enumerate(grid)}
        d090, d100, d110 = curva["0.90"], curva["1.00"], curva["1.10"]
        c2 = (d090 - 2 * d100 + d110) / (2 * H ** 2)
        out[l] = {"curva_D2_vs_S30_2024": curva, "a_optimo_2024": float(grid[np.argmin(tot)]), "K_2024": float(-c2)}
    rng = np.random.default_rng(semilla)
    n = len(y)
    idxs = {l: np.where(L == l)[0] for l in RAMOS}
    k1 = int(np.where(grid == 1.0)[0][0])
    res = {l: [] for l in RAMOS}
    gpub, gpriv = [], []
    for _ in range(reps):
        pub = rng.random(n) < frac
        dpub = dpriv = 0.0
        nullpub = dev(y[pub], np.full(int(pub.sum()), y[pub].mean())).sum()
        nullpriv = dev(y[~pub], np.full(int((~pub).sum()), y[~pub].mean())).sum()
        for l in RAMOS:
            sp = pub[idxs[l]]
            tot = D[l][:, sp].sum(axis=1)
            k = int(np.argmin(tot))
            res[l].append(float(grid[k]))
            dpub += tot[k] - tot[k1]
            dpriv += D[l][k, ~sp].sum() - D[l][k1, ~sp].sum()
        gpub.append(-dpub / nullpub)
        gpriv.append(-dpriv / nullpriv)
    for l in RAMOS:
        out[l]["sigma_33pct"] = float(np.std(res[l]))
        out[l]["a_33pct_media"] = float(np.mean(res[l]))
    out["_bootstrap"] = {"fuente": str(p.relative_to(root)), "sha256": sha256(p), "replicas": reps, "fraccion": frac, "semilla": semilla,
                         "aplicar_a_del_33pct_entero": {"en_el_33pct_media": float(np.mean(gpub)), "en_el_67pct_media": float(np.mean(gpriv)),
                                                        "en_el_67pct_sd": float(np.std(gpriv)), "en_el_67pct_p05": float(np.quantile(gpriv, 0.05))}}
    return out


def generar(args):
    root = raiz()
    env = root / "Hackaton" / "Semana 1" / "Envios"
    reg = root / "Hackaton" / "Repositorio_IAA2026" / "registro"
    s42, p42 = leer_s42(root)
    T = test_lineas_exposicion(root).reindex(s42.row_id)
    lin, e = T.line.values, T.exposure.values
    assert not pd.isna(lin).any() and (e > 0).all()
    tot42 = {r: float(s42.prediction.values[lin == r].sum()) for r in RAMOS}
    archivos = {}
    for ramo in RAMOS:
        sel = lin == ramo
        for tag, a in A_SONDA.items():
            df = s42.copy()
            df.loc[sel, "prediction"] = forma(s42.prediction.values[sel], e[sel], a)
            nombre = f"S50_sonda_forma_{ramo}_{tag}.csv"
            path = env / "archivos" / nombre
            h = escribir_csv(df, path)
            back = pd.read_csv(path, dtype={"row_id": str, "prediction": float})
            assert (back.row_id.values == s42.row_id.values).all()
            assert np.array_equal(back.prediction.values[~sel], s42.prediction.values[~sel])
            assert (back.prediction.values > 0).all() and np.isfinite(back.prediction.values).all()
            por_ramo = {r: round(float(back.prediction.values[lin == r].sum()), 2) for r in RAMOS}
            assert abs(por_ramo[ramo] - tot42[ramo]) < 5.0, (ramo, por_ramo[ramo], tot42[ramo])
            archivos[f"{ramo}_{tag}"] = {"archivo": str(path.relative_to(root)).replace("\\", "/"), "sha256": h, "ramo": ramo, "a": a, "filas": int(len(df)),
                                        "total_CU": round(float(back.prediction.sum()), 2), "por_ramo_CU": por_ramo,
                                        "sd_log_tasa_ramo": float(np.log(back.prediction.values[sel] / e[sel]).std())}
            print(nombre, h, por_ramo, f"sd log tasa {archivos[f'{ramo}_{tag}']['sd_log_tasa_ramo']:.4f}")
    print("curvatura y ruido sobre 2024...")
    cal = curvatura_y_ruido(root)
    Z = {r: TAU_A[r] ** 2 / (TAU_A[r] ** 2 + cal[r]["sigma_33pct"] ** 2) for r in RAMOS}
    nota = {
        "id": "S50_sonda_forma", "autor": "Claude (sesión Cowork del 22 de octubre), por instrucción del participante; decisión D102",
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "base": {"archivo": str(p42.relative_to(root)).replace("\\", "/"), "sha256": S42_SHA, "publico": S42_PUBLICO,
                 "sd_log_tasa_S42": {r: float(np.log(s42.prediction.values[lin == r] / e[lin == r]).std()) for r in RAMOS}},
        "linaje": "S42 (Mezcla por peligro con nivel calibrado) con las relatividades de un solo ramo comprimidas (a = 0,90) o ampliadas (a = 1,10) alrededor de la tasa media del ramo; total por ramo idéntico a S42; nada reentrenado",
        "transformacion": "r' = g (r/g)^a con r = mu/e y g = sum(mu)/sum(e) del ramo; mu' = e r'; renivelado al total del ramo",
        "objetivo": "Estimar por parábola (D² en a = 0,90, 1,00 y 1,10) el exponente óptimo del público por ramo y aplicar solo la fracción creíble (S43). Las sondas no son candidatos finales y nunca se seleccionan.",
        "archivos": archivos,
        "preinscrito": {"tau_previa": TAU_A, "sigma_ruido_33pct_bootstrap_2024": {r: cal[r]["sigma_33pct"] for r in RAMOS}, "Z_credibilidad": Z,
                        "K_2024": {r: cal[r]["K_2024"] for r in RAMOS}, "a_optimo_2024_relativo_a_S30": {r: cal[r]["a_optimo_2024"] for r in RAMOS},
                        "regla": "a* = vértice de la parábola por los tres puntos del ramo (si la parábola no es cóncava o a* sale de [0,80; 1,20], el ramo no se aplica); a_Z = 1 + Z (a* − 1); S43 = S42 con a_Z por ramo y totales intactos; con un solo punto en un ramo se usa K_2024 como curvatura conocida. Selección final manual: S43 si su público >= el de S42, si no S42; nunca una sonda.",
                        "esperanza_calculada_antes": "público +0,00026 aproximado; privado entre −0,00004 (si el óptimo de 2025 coincide con el de 2024) y +0,00010 (si difiere como la previa)"},
        "calibracion_2024": cal,
        "instrucciones_codex": "Hoy (22 de octubre, dos intentos hasta las 19:00 de Bogotá): enviar S50_sonda_forma_motor_a090 y S50_sonda_forma_buildings_a090. Mañana a primera hora: motor_a110, buildings_a110, contents_a090, contents_a110. Anotar cada público con cinco decimales en registro_envios.json y devolverlos. Después `sonda_forma.py resolver` escribe S43.",
    }
    (env / "S50_sonda_forma_entrega_codex.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    (reg / "sonda_forma_D102_preinscripcion.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"sigma": nota["preinscrito"]["sigma_ruido_33pct_bootstrap_2024"], "Z": Z, "K_2024": nota["preinscrito"]["K_2024"],
                      "a_opt_2024": nota["preinscrito"]["a_optimo_2024_relativo_a_S30"], "bootstrap": cal["_bootstrap"]["aplicar_a_del_33pct_entero"]}, indent=1))


def resolver(args):
    root = raiz()
    env = root / "Hackaton" / "Semana 1" / "Envios"
    reg = root / "Hackaton" / "Repositorio_IAA2026" / "registro"
    pre = json.loads((reg / "sonda_forma_D102_preinscripcion.json").read_text(encoding="utf-8"))["preinscrito"]
    Z, K24, sig, tau = pre["Z_credibilidad"], pre["K_2024"], pre["sigma_ruido_33pct_bootstrap_2024"], pre["tau_previa"]
    d100 = args.s42
    s42, _ = leer_s42(root)
    T = test_lineas_exposicion(root).reindex(s42.row_id)
    lin, e = T.line.values, T.exposure.values
    df = s42.copy()
    out = {"s42_publico": d100, "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "ramos": {}}
    for ramo in RAMOS:
        vals = getattr(args, ramo)
        if vals is None:
            out["ramos"][ramo] = {"estado": "sin sonda; a_Z = 1"}
            continue
        if len(vals) == 2:
            d090, d110 = vals
            c2 = (d090 - 2 * d100 + d110) / (2 * H ** 2)
            c1 = (d110 - d090) / (2 * H) - 2 * c2 * 1.0
            modo = "parabola_tres_puntos"
        else:
            d090, d110 = vals[0], None
            c2 = -K24[ramo]
            # D(0,90) − D(1) = c1 (0,9 − 1) + c2 (0,81 − 1)  ->  c1 = (D090 − D100 − c2·(−0,19)) / (−0,10)
            c1 = (d090 - d100 + 0.19 * c2) / (-H)
            modo = "un_punto_con_K_2024"
        aplicable = c2 < 0
        a_opt = -c1 / (2 * c2) if aplicable else 1.0
        if not (0.80 <= a_opt <= 1.20):
            aplicable = False
        gan = lambda a: c1 * (a - 1) + c2 * (a ** 2 - 1)
        aZ = 1 + Z[ramo] * (a_opt - 1) if aplicable else 1.0
        rec = {"modo": modo, "publico_a090": d090, "publico_a110": d110, "c1": c1, "c2": c2, "K_publico": -c2, "K_2024": K24[ramo], "aplicable": bool(aplicable),
               "a_optimo_publico": a_opt, "ganancia_publico_en_a_optimo": gan(a_opt) if aplicable else 0.0, "Z": Z[ramo], "a_Z": aZ,
               "ganancia_publico_esperada_en_a_Z": gan(aZ) if aplicable else 0.0}
        if aplicable:
            zt0 = 0.0
            zt1 = tau[ramo] ** 2 / (tau[ramo] ** 2 + sig[ramo] ** 2)
            u1 = zt1 * (a_opt - 1)
            Kp = -c2
            rec["privado_esperado_si_2025_igual_2024"] = Kp * (0 - (aZ - 1 - zt0 * (a_opt - 1)) ** 2)
            rec["privado_esperado_si_tau_previa"] = Kp * (u1 ** 2 - (aZ - 1 - u1) ** 2)
            sel = lin == ramo
            df.loc[sel, "prediction"] = forma(s42.prediction.values[sel], e[sel], aZ)
        out["ramos"][ramo] = rec
        print(f"{ramo:9s} {modo}: a*={a_opt:.4f} aplicable={aplicable} K_pub={-c2:.4f} (K_2024 {K24[ramo]:.4f}) Z={Z[ramo]:.3f} a_Z={aZ:.4f} ganancia pública esperada {rec['ganancia_publico_esperada_en_a_Z']:+.5f}")
    gan_tot = sum(v.get("ganancia_publico_esperada_en_a_Z", 0.0) for v in out["ramos"].values())
    out["D2_publico_esperado_S43"] = d100 + gan_tot
    out["privado_esperado_S43"] = {"si_2025_igual_2024": sum(v.get("privado_esperado_si_2025_igual_2024", 0.0) for v in out["ramos"].values()),
                                    "si_tau_previa": sum(v.get("privado_esperado_si_tau_previa", 0.0) for v in out["ramos"].values())}
    if args.simular:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        print("simulación: no se escribe S43 ni notas")
        return
    path = env / "archivos" / "S43_forma_credibilidad.csv"
    h = escribir_csv(df, path)
    back = pd.read_csv(path, dtype={"row_id": str, "prediction": float})
    out["S43"] = {"archivo": str(path.relative_to(root)).replace("\\", "/"), "sha256": h, "filas": int(len(df)), "total_CU": round(float(back.prediction.sum()), 2),
                  "por_ramo_CU": {r: round(float(back.prediction.values[lin == r].sum()), 2) for r in RAMOS},
                  "factores_a_aplicados": {r: out["ramos"][r].get("a_Z", 1.0) for r in RAMOS}}
    nota = {"id": "S43_forma_credibilidad", "autor": "Claude (sesión Cowork del 22 de octubre)", "linaje": "S42 con el exponente de forma a_Z por ramo (sonda de forma con credibilidad, D102); totales por ramo iguales a S42",
            "base": {"archivo": "Hackaton/Semana 1/Envios/archivos/S42_nivel_credibilidad_revisada.csv", "sha256": S42_SHA, "publico": d100}, "resolucion": out, "preinscrito": pre,
            "recomendacion": f"Seleccionar S43 como final si su público es mayor o igual que el de S42 ({d100}); esperado {d100+gan_tot:.5f}. Nunca seleccionar una sonda."}
    (env / "S43_forma_credibilidad_entrega_codex.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    (reg / "sonda_forma_D102_resolucion.json").write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    print("S43:", h, out["S43"]["por_ramo_CU"], "público esperado", round(d100 + gan_tot, 5), "privado esperado", {k: round(v, 5) for k, v in out["privado_esperado_S43"].items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generar")
    r = sub.add_parser("resolver")
    r.add_argument("--s42", type=float, default=S42_PUBLICO)
    r.add_argument("--simular", action="store_true")
    for ramo in RAMOS:
        r.add_argument(f"--{ramo}", type=float, nargs="+", metavar="PUB")
    args = ap.parse_args()
    {"generar": generar, "resolver": resolver}[args.cmd](args)


if __name__ == "__main__":
    main()
