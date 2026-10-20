"""Revisión cruzada de Claude sobre el dictamen de Codex (docs/REVISION_DESDE_EL_PARTICIPANTE.md), 19-10-2026.

Solo lee archivos existentes y calcula agregados: no entrena, no infiere, no mezcla y no envía nada.
Escribe registro/revision_cruzada_claude_20261019.json sin datos por fila.
Uso: python3 herramientas/revision_cruzada_claude.py   (requiere pandas, numpy y pyarrow)
"""
import hashlib, json, datetime
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
S1 = REPO.parent / "Semana 1"
F = {
    "alineadas_N48": S1 / "Modelado_codex/nocturna_20261017_N01/S30_S31_review_N48/S30/aligned_predictions.parquet",
    "t0": S1 / "Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0/tables/t0_por_row_id.parquet",
    "particiones": S1 / "Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/tables/particiones.parquet",
    "f0_buildings": S1 / "Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/tables/f0_buildings.parquet",
    "f0_contents": S1 / "Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/tables/f0_contents.parquet",
    "S30_csv": REPO / "privado/predicciones/S30.csv",
    "S22_csv": REPO / "privado/predicciones/S22.csv",
    "S30_resumen": S1 / "Modelos_claude_b/runs/S30_claude_b/resumen.json",
    "S22_resumen": S1 / "Modelos_claude/runs/S22_claude_propio/resumen.json",
}
LINES = ["motor", "buildings", "contents"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ud(y, mu):  # desviación unitaria Tweedie, potencia 1,5
    return 2 * (-4 * np.sqrt(y) + 2 * y / np.sqrt(mu) + 2 * np.sqrt(mu))


def d2(y, mu, base=None):
    base = np.full(len(y), y.mean()) if base is None else base
    return float(1 - ud(y, mu).sum() / ud(y, base).sum())


def factor_tweedie(y, mu):  # escala que minimiza la desviación (misma fórmula que ftw en mezcla3.py)
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def main():
    out = {"autor": "Claude", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "alcance": "Agregados sobre archivos existentes; cero entrenamientos, inferencias, mezclas o envíos.",
           "fuentes": {k: {"ruta": str(p.relative_to(REPO.parent.parent)).replace("\\", "/"), "sha256": sha(p)} for k, p in F.items()}}
    al = pq.read_table(F["alineadas_N48"]).to_pandas()
    t0 = pq.read_table(F["t0"], columns=["row_id", "T0"]).to_pandas().set_index("row_id").T0
    out["T0_alineado_igual_a_bases"] = bool((al.row_id.map(t0) - al.T0).abs().max() == 0)

    # 1. métricas, cociente monetario y factor Tweedie óptimo por corte y ramo
    met = []
    for cut in ["V23", "V24"]:
        for line in LINES + ["cartera"]:
            z = al[(al.corte == cut) & ((al.line == line) | (line == "cartera"))]
            y, a, b, e = z.T0.values, z.S22.values, z.candidate.values, z.exposure.values
            tasa = y.sum() / e.sum() * e
            met.append({"corte": cut, "ramo": line, "filas": len(z),
                        "D2_S22": d2(y, a), "D2_S30": d2(y, b), "ganancia": d2(y, b) - d2(y, a),
                        "D2_S30_base_tasa_constante": d2(y, b, tasa), "ganancia_base_tasa_constante": d2(y, b, tasa) - d2(y, a, tasa),
                        "observado_sobre_S30": float(y.sum() / b.sum()), "factor_tweedie_optimo_S30": factor_tweedie(y, b)})
    out["metricas"] = met

    z = al[al.corte == "V24"]
    y, a, b = z.T0.values, z.S22.values, z.candidate.values
    out["reservas_V24"] = {f"{s:+.0%}": d2(y + s * z.case_reserve.values, b) - d2(y + s * z.case_reserve.values, a) for s in (-0.25, 0.25)}

    # 2. influencia por cliente, simétrica
    c = pd.Series((ud(y, a) - ud(y, b)) / ud(y, np.full(len(y), y.mean())).sum()).groupby(z.customer_id.values).sum().sort_values()
    grandes = y > np.quantile(y[y > 0], 0.99)
    cf = (ud(y, a) - ud(y, b)) / ud(y, np.full(len(y), y.mean())).sum()
    out["influencia_V24"] = {"ganancia": float(c.sum()), "diez_mas_favorables": float(c.tail(10).sum()), "diez_mas_adversos": float(c.head(10).sum()),
                             "sin_diez_de_cada_extremo": float(c.iloc[10:-10].sum()), "clientes": int(len(c)),
                             "filas_1pct_mayores_T0_positivo": float(cf[grandes].sum()), "resto_de_filas": float(cf[~grandes].sum())}

    # 3. sensibilidad de D2 V24 al nivel (diagnóstico con etiquetas V24, no propuesta de escala)
    sens = {}
    for s in (0.95, 0.97, 1.03, 1.05):
        sens[f"cartera_x{s}"] = d2(y, b * s) - d2(y, b)
    m = (z.line == "buildings").values
    for s in (0.965, 1.035, 1.07):
        bb = b.copy(); bb[m] *= s; sens[f"edificios_x{s}"] = d2(y, bb) - d2(y, b)
    opt = b.copy()
    for line in LINES:
        mm = (z.line == line).values; opt[mm] *= factor_tweedie(y[mm], b[mm])
    sens["oraculo_factor_optimo_por_ramo"] = d2(y, opt) - d2(y, b)
    out["sensibilidad_nivel_V24"] = sens

    # 4. factores de nivel guardados por la mezcla
    out["factores_nivel"] = {k: {l: json.loads(F[k].read_text())["lines"][l] for l in LINES} for k in ("S30_resumen", "S22_resumen")}

    # 5. capitales sin confirmación
    s30 = pd.read_csv(F["S30_csv"], dtype={"row_id": str}).set_index("row_id").prediction
    s22 = pd.read_csv(F["S22_csv"], dtype={"row_id": str}).set_index("row_id").prediction
    cap, ids = {}, []
    for line in ["buildings", "contents"]:
        f = pq.read_table(F[f"f0_{line}"], columns=["row_id", "year", "audit_capital_scale_adjusted", "audit_capital_scale_confirmed"]).to_pandas()
        adj = f.audit_capital_scale_adjusted.astype(bool); unc = adj & ~f.audit_capital_scale_confirmed.astype(bool)
        t = f[unc & (f.year == 2025)]; ids += list(t.row_id)
        cap[line] = {"ajustados": int(adj.sum()), "sin_confirmar": int(unc.sum()), "sin_confirmar_en_test": int(len(t))}
    cap["S30_total_123"] = float(s30.loc[ids].sum()); cap["S30_fraccion"] = float(s30.loc[ids].sum() / s30.sum())
    out["capitales"] = cap

    # 6. parecido entre los dos CSV finales
    assert (s30.index == s22.index).all()
    r = s30 / s22; pref = s30.index.str[0]
    out["S30_frente_S22_2025"] = {n: {"total_S22": float(s22[pref == p].sum()), "total_S30": float(s30[pref == p].sum()),
                                      "correlacion_log": float(np.corrcoef(np.log(s22[pref == p]), np.log(s30[pref == p]))[0, 1]),
                                      "fraccion_filas_dif_mayor_5pct": float((abs(r[pref == p] - 1) > 0.05).mean())}
                                  for n, p in [("motor", "M"), ("buildings", "B"), ("contents", "C")]}
    out["S30_frente_S22_2025"]["cartera"] = {"total_S22": float(s22.sum()), "total_S30": float(s30.sum()),
                                             "correlacion_log": float(np.corrcoef(np.log(s22), np.log(s30))[0, 1]),
                                             "fraccion_filas_dif_mayor_5pct": float((abs(r - 1) > 0.05).mean())}
    dst = REPO / "registro/revision_cruzada_claude_20261019.json"
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("escrito", dst)


if __name__ == "__main__":
    main()
