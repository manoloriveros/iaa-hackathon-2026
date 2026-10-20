"""Reúne en un solo JSON las cifras agregadas que usan el informe, el panel y el video de la entrega final.

No entrena, no mezcla, no envía nada y no escribe datos por fila: lee recibos, tablas agregadas y las
predicciones guardadas de S30 en 2023 y 2024 (para recalcular D², escenarios de reserva y deciles), y deja cada
cifra junto a la ruta y el SHA-256 de su fuente.

    python herramientas/cifras_entregables.py --raiz C:/dev/Hakaton
    (salida: docs/entrega/datos/cifras_entregables.json)

Requiere pandas y pyarrow solo para el bloque de predicciones guardadas.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEMANA = "Hackaton/Semana 1"
BASES = f"{SEMANA}/Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0"
FUENTES = {
    "registro_envios": f"{SEMANA}/Envios/registro_envios.json",
    "entrega_s30": f"{SEMANA}/Envios/S30_claude_b_entrega_codex.json",
    "medias_s30": f"{SEMANA}/Modelos_claude_b/experimentos/medias_por_ramo_s30.json",
    "predicciones_s30": f"{SEMANA}/Modelos_claude_b/experimentos/predicciones_v23_v24_s30.parquet",
    "publico_vs_local": f"{SEMANA}/Modelos_claude_b/experimentos/publico_vs_local_b.csv",
    "bases_evidencia": f"{BASES}/evidencia.json",
    "ibnr_peligro": f"{BASES}/tables/ibnr_2024_por_peligro.csv",
    "ibnr_ramo": f"{BASES}/tables/ibnr_2024_por_ramo.csv",
    "prima_ultima": f"{BASES}/tables/prima_riesgo_ultima_ramo_anio.csv",
    "referencias_m00": f"{BASES}/tables/referencias_M00.csv",
    "reservas_ramo_anio": f"{BASES}/tables/reservas_caso_ramo_anio.csv",
    "asignacion": f"{BASES}/tables/asignacion_siniestros.csv",
    "frecuencia": f"{BASES}/tables/frecuencia_ramo_anio_peligro.csv",
    "foro": "foros/FORO.md",
    "ciclo_validacion": f"{SEMANA}/Validacion_enjambre/ultimo_ciclo.json",
    "hallazgos": "Hackaton/Repositorio_IAA2026/docs/evidencia/hallazgos.json",
    "controles_windows": "Hackaton/Repositorio_IAA2026/docs/controles/20261019_windows_v12_lf/resultado.json",
    "controles_nube": "Hackaton/Repositorio_IAA2026/docs/controles/20261019T125425Z_nube_referencia/resultado.json",
    "controles_vm": "Hackaton/Repositorio_IAA2026/docs/controles/20261019T125907Z_vm_participante/resultado.json",
    "replay_windows": "Hackaton/Repositorio_IAA2026/docs/evidencia/replay_windows.json",
    "preflight": "Hackaton/Repositorio_IAA2026/docs/evidencia/preflight.json",
    "receta": "Hackaton/Repositorio_IAA2026/receta/receta.json",
    "spec_s30": "Hackaton/Repositorio_IAA2026/receta/especificaciones/spec_s30.json",
    "reglas_kaggle": "Hackaton/Repositorio_IAA2026/docs/fuentes/reglas_kaggle_20261019.json",
    "fuentes_investigacion_a": f"{SEMANA}/Modelado/Investigacion_tecnicas/fuentes.json",
    "fuentes_investigacion_b": f"{SEMANA}/Modelado/Investigacion_tecnicas_claude/fuentes.json",
    "papers_iaa": "Preparación/Antecedentes/IAA_IA/catalogo.json",
    "base_n62": "Hackaton/Repositorio_IAA2026/docs/evidencia/base_N62.json",
    "f0_d68": "Hackaton/Repositorio_IAA2026/docs/evidencia/F0_D68.json",
    "bases_d67": "Hackaton/Repositorio_IAA2026/docs/evidencia/bases_D67.json",
    "revision_humana": "Hackaton/Repositorio_IAA2026/registro/revision_humana.json",
    "decision_gov007": "Hackaton/Repositorio_IAA2026/registro/decision_GOV007_20261019.json",
    "recalculo_d59": f"{SEMANA}/Validacion_ajustes_claude/current_run.json",
    "capitales_149": "Hackaton/Repositorio_IAA2026/docs/evidencia/capitales_149_prediccion.json",
    "sensibilidad": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/cifras_sensibilidad.json",
    "sensibilidad_informe": "Hackaton/Repositorio_IAA2026/docs/SENSIBILIDAD_S30_S22.md",
    "sens_e04": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e04.json",
    "sens_e09": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e09.json",
    "sens_e10": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e10_reproduccion.json",
    "sens_e12": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e12.json",
    "reproduccion_completa": "Hackaton/Repositorio_IAA2026/registro/recibo_reproduccion_completa_20261020.json",
    "reproduccion_documento": "Hackaton/Repositorio_IAA2026/docs/REPRODUCCION_COMPLETA.md",
    "decisiones_participante": "Hackaton/Repositorio_IAA2026/registro/decisiones_participante_20261020.json",
    "reservas_resumen": "Hackaton/Repositorio_IAA2026/privado/corridas/reservas_20261019T225357Z_99b45271/resultados/resumen.json",
    "reservas_umbrales": "Hackaton/Repositorio_IAA2026/privado/corridas/reservas_20261019T225357Z_99b45271/resultados/parte_b.json",
    "reservas_informe": "Hackaton/Repositorio_IAA2026/docs/RESERVAS_ACOTACION.md",
    "reservas_autorizacion": "Hackaton/Repositorio_IAA2026/registro/autorizacion_reproduccion_reservas_20261019.json",
    "decision_modelo_definitivo": "Hackaton/Repositorio_IAA2026/registro/decision_modelo_definitivo_20261020.json",
}
# Etiquetas neutrales de los envíos puntuados, en orden de envío (sin autoría).
ETIQUETAS = {
    "S01": ("Tasa constante por ramo (nivel observado)", "Constant rate per line (observed level)"),
    "S02": ("Tasa constante por ramo (nivel último)", "Constant rate per line (ultimate level)"),
    "S03_lgbm_F0124": ("LightGBM Tweedie con variables de contrato", "LightGBM Tweedie, contract features"),
    "S04_lgbm_F3autos": ("+ variables condicionadas en autos", "+ conditional features in motor"),
    "S07": ("Coste total + frecuencia y severidad", "Total cost + frequency-severity"),
    "S08": ("Apilado con CatBoost", "Stack with CatBoost"),
    "S09b": ("Mezcla por ramo, variables de cliente en hogar", "Per-line blend, customer features in home"),
    "N01_A_G": ("Combinador aditivo por peligro", "Additive per-peril combiner"),
    "N01_B": ("Frecuencia por póliza completa", "Full-policy frequency"),
    "N01_G": ("Frecuencia con EBM", "EBM frequency"),
    "N01_H": ("Meta-mezcla geométrica", "Geometric meta-blend"),
    "S21": ("Severidad GLM con covariables físicas", "GLM severity with physical covariates"),
    "S22": ("Sin forma en hogar (criterio de cuerpo)", "No home shape (body criterion)"),
    "S30": ("Tendencia de severidad y pesos de cuerpo", "Severity trend and body weights"),
}
RAMOS = ("motor", "buildings", "contents")
# Títulos breves y neutrales de los hallazgos del enjambre de validación (traducción editorial del registro original).
TITULOS_HALLAZGOS = {
    "DATA-001": ("Disponibilidad al cotizar sin acreditar en variables condicionadas y clima anual", "Availability at quotation not proven for conditional features and annual weather"),
    "DATA-002": ("Una sola valoración y ningún último observado limitan el contraste", "A single valuation and no observed ultimate limit the backtest"),
    "DATA-003": ("La escala de capitales en la matriz conserva casos sin confirmación histórica", "Sum-insured scaling keeps cases without historical confirmation"),
    "DATA-004": ("El comparador inicial de asignación debía separar los siniestros previos", "The first assignment comparator had to separate pre-history claims"),
    "DATA-005": ("Historia y clima del año anterior incluyen información posterior al corte de cotización", "Prior-year history and weather include information after the quotation cut"),
    "MOD-001": ("Selección hecha sobre 2023 y 2024 reutilizados", "Selection made on reused 2023 and 2024 data"),
    "MOD-002": ("Último real y suficiencia de reservas no identificados", "True ultimate and reserve adequacy not identified"),
    "MOD-003": ("Disponibilidad temporal condicional de algunas variables", "Conditional temporal availability of some features"),
    "MOD-004": ("Mejora dependiente de la cola y heterogénea", "Improvement depends on the tail and is heterogeneous"),
    "MOD-005": ("Reproducción parcial de la cadena de predicciones", "Partial reproduction of the prediction chain"),
    "MOD-006": ("Exclusión causal excesiva de la insuficiencia de reservas", "Overstated causal exclusion of reserve inadequacy"),
    "MOD-007": ("Base porcentual ambigua al comparar exposición diaria y mensual", "Ambiguous percentage base when comparing daily and monthly exposure"),
    "MOD-008": ("Afirmación de reservas insesgadas y cambio de régimen sin identificar", "Claim of unbiased reserves and regime change not identified"),
    "GOV-001": ("Revisión humana especializada pendiente", "Specialist human review pending"),
    "GOV-002": ("Vínculo entre conversaciones reales y decisiones no acreditado", "Link between real conversations and decisions not proven"),
    "GOV-003": ("Reproducción por otra persona y en otra plataforma no acreditada", "Reproduction by another person and platform not proven"),
    "GOV-004": ("La batería cubre contratos y trazabilidad; la cobertura del modelo es parcial", "The test suite covers contracts and traceability; model coverage is partial"),
    "GOV-005": ("Integridad y puertas locales auditadas sin modificar entradas", "Integrity and local gates audited without changing inputs"),
    "GOV-006": ("Cronología interna de un aporte y su adenda pendiente de aclarar", "Internal timing of a post and its addendum to be clarified"),
    "GOV-007": ("Los controles del paquete permitían éxito con incumplimientos", "Package controls allowed success despite non-conformities"),
    "GOV-008": ("La clave de la captura de modelos omitía entradas posicionales", "The model-capture key left out positional inputs"),
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def filas(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def r(x, n=5):
    return None if x is None else round(float(x), n)


def spearman(a, b):
    def rangos(v):
        orden = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        for k, i in enumerate(orden):
            out[i] = k + 1.0
        return out
    ra, rb = rangos(a), rangos(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb)


def bloque_envios(reg):
    envios = []
    for x in reg["candidates"]:
        if not x.get("submitted") or x.get("public_score") is None:
            continue
        ls = x.get("local_score")
        v24 = None
        if isinstance(ls, dict):
            for k in ("V24", "crossfit_V24", "reported_V24_D2_global", "V24_d2_global_sobre_T0", "D2"):
                if isinstance(ls.get(k), (int, float)):
                    v24 = ls[k]
                    break
        envios.append({"id": x["id"], "utc": x.get("submitted_utc"), "publico": x["public_score"],
                       "v24_local": r(v24, 5), "etiqueta_es": ETIQUETAS.get(x["id"], (x["id"], x["id"]))[0],
                       "etiqueta_en": ETIQUETAS.get(x["id"], (x["id"], x["id"]))[1]})
    envios.sort(key=lambda e: e["utc"])
    return envios


def bloque_publico_local(rows, entrega):
    glob = [x for x in rows if x["ramo"] == "global"]
    cand = [x["cand"] for x in glob]
    pub = [float(x["publico"]) for x in glob]
    comp = [float(x["d2"]) for x in glob]
    c05 = [float(x["d2_sin_0.995_reniv"]) for x in glob]
    c1 = [float(x["d2_sin_0.99_reniv"]) for x in glob]
    cg = entrega["validacion"]["cuerpo_global"]
    posteriores = []
    for k, pubk in (("S22", 0.12988), ("S30", 0.12996)):
        posteriores.append({"cand": k, "publico": pubk, "d2_completo_v24": cg[k]["V24"]["d2_completo"],
                            "d2_cuerpo_v24": cg[k]["V24"]["sin_0_5_renivelado"]})
    return {"candidatos_antes": [{"cand": c, "publico": p, "d2_completo_v24": r(a, 5), "d2_cuerpo_v24": r(b, 5)}
                                 for c, p, a, b in zip(cand, pub, comp, c05)],
            "spearman_completo": r(spearman(comp, pub), 2), "spearman_cuerpo_05": r(spearman(c05, pub), 2),
            "spearman_cuerpo_1": r(spearman(c1, pub), 2), "posteriores": posteriores,
            "definicion_cuerpo": "D² de 2024 sin el 0,5 % de periodos con mayor coste observado, con cada candidato renivelado por ramo"}


def bloque_predicciones(p: Path):
    import numpy as np
    import pandas as pd
    df = pd.read_parquet(p)

    def dev(y, mu):
        return 2 * (-4 * np.sqrt(y) + 2 * y / np.sqrt(mu) + 2 * np.sqrt(mu))

    def d2(y, mu):
        return float(1 - dev(y, mu).sum() / dev(y, np.full_like(y, y.mean())).sum())

    out = {"d2": {}, "reservas": {}, "deciles_v24": {}, "concentracion_v24": {}, "media": {}}
    for corte in ("V23", "V24"):
        s = df[df.corte == corte]
        out["d2"][corte] = {"agregado": r(d2(s.y_T0.values, s.prediction.values))}
        out["media"][corte] = {}
        for l, g in s.groupby("line"):
            out["d2"][corte][l] = r(d2(g.y_T0.values, g.prediction.values))
            out["media"][corte][l] = {"observada": r(g.y_T0.mean(), 2), "predicha": r(g.prediction.mean(), 2),
                                      "obs_entre_pred": r(g.y_T0.sum() / g.prediction.sum(), 4), "filas": int(len(g))}
        out["reservas"][corte] = {}
        for a in (0.75, 1.0, 1.25):
            y = s.y_T0.values - (1 - a) * s.reserva_caso.values
            esc = {"agregado": r(d2(y, s.prediction.values), 6)}
            for l, g in s.groupby("line"):
                esc[l] = r(d2((g.y_T0 - (1 - a) * g.reserva_caso).values, g.prediction.values), 6)
            out["reservas"][corte][str(a)] = esc
    s = df[df.corte == "V24"]
    for l, g in s.groupby("line"):
        g = g.sort_values("prediction", kind="mergesort").reset_index(drop=True)
        dec = (np.arange(len(g)) * 10 // len(g)).astype(int)
        t = g.assign(dec=dec).groupby("dec").agg(pred=("prediction", "mean"), obs=("y_T0", "mean"), n=("row_id", "size"))
        out["deciles_v24"][l] = [{"decil": int(i) + 1, "predicha": r(x.pred, 2), "observada": r(x.obs, 2),
                                  "obs_entre_pred": r(x.obs / x.pred, 3), "filas": int(x.n)} for i, x in t.iterrows()]
        gd = g.sort_values("prediction", ascending=False, kind="mergesort").reset_index(drop=True)
        cum_y = gd.y_T0.cumsum().values / gd.y_T0.sum()
        cum_p = gd.prediction.cumsum().values / gd.prediction.sum()
        n = len(gd)
        puntos = []
        for q in [i / 20 for i in range(21)]:
            k = int(round(q * n))
            puntos.append({"fraccion_periodos": r(q, 3), "coste_observado": r(cum_y[k - 1] if k else 0.0, 4),
                           "coste_predicho": r(cum_p[k - 1] if k else 0.0, 4)})
        out["concentracion_v24"][l] = {"puntos": puntos, "decil_superior_observado": r(cum_y[n // 10 - 1], 4),
                                       "decil_superior_predicho": r(cum_p[n // 10 - 1], 4)}
    return out


def bloque_ibnr(peligros, ramos, prima, reservas, entrega):
    comp = [{"ramo": x["line"], "peligro": x["peril"], "completitud_2024": r(x["completitud_ponderada_2024"], 4),
             "ibnr_coste_CU": r(x["ibnr_coste_CU"], 2), "T0_2024_CU": r(x["T0_2024_CU"], 2),
             "factor_coste": r(x["factor_ibnr_coste"], 4)} for x in peligros]
    tasas = entrega["tasa_2025_por_unidad_de_exposicion"]
    pr = []
    for x in prima:
        pr.append({"ramo": x["line"], "anio": int(x["year"]), "prima_T0": r(x["prima_riesgo_T0_CU"], 2),
                   "prima_T0_mas_IBNR": r(x["prima_riesgo_T0_mas_IBNR_CU"], 2), "factor_ibnr": r(x["factor_ibnr_coste"], 4),
                   "T1_075": r(x["prima_T1_a075_mas_IBNR_CU"], 2), "T1_125": r(x["prima_T1_a125_mas_IBNR_CU"], 2)})
    for l in RAMOS:
        pr.append({"ramo": l, "anio": 2025, "prediccion_S30": tasas[l]})
    res = [{"ramo": x["line"], "anio": int(x["year"]), "reserva_sobre_T0_pct": r(x["reserva_sobre_T0_pct"], 2),
            "abiertos": int(x["abiertos"]), "aceptados": int(x["aceptados"])} for x in reservas]
    return {"completitud_2024_por_peligro": comp,
            "factor_coste_2024": {x["line"]: r(x["factor_ibnr_coste"], 4) for x in ramos},
            "prima_riesgo_por_anio": pr, "reserva_abiertos": res,
            "nota": "Completitud = exposición efectiva / exposición nominal de 2024 (chain-ladder de conteos por peligro). "
                    "La prima de 2025 es el total predicho por S30 dividido por la exposición nominal de 2025."}


def bloque_datos(n62, bases_ev, asig, f0, frec):
    reglas = n62["rules_changes"]
    por_cat = Counter()
    for x in asig:
        por_cat[(x["category"], x["status"])] += int(x["n"])
    total = sum(por_cat.values())
    pre = sum(v for (c, s), v in por_cat.items() if c.startswith("prehistoria"))
    rechazados = sum(v for (c, s), v in por_cat.items() if c == "unica" and s == "repudiated")
    aceptados = sum(v for (c, s), v in por_cat.items() if c == "unica" and s != "repudiated")
    ceros = {}
    for x in frec:
        if x["peril"] == "todos":
            ceros.setdefault(x["line"], {})[int(x["year"])] = r(x["pct_periodos_sin_coste"], 2)
    t0 = bases_ev["t0"]
    return {"reglas_n62": reglas,
            "capitales_f0": f0["capital_contract_D66"],
            "base_reconstruida": {"tablas_identicas_en_bytes": n62["byte_identical_tables"], "celdas_comparadas": n62["cells_compared"],
                                  "diferencias": n62["value_differences"], "filas": n62["rows"]},
            "flujo_siniestros": {"originales": total + 604, "copias_exactas_excluidas": 604, "tras_DUP01": total,
                                 "fuera_del_historial_PRE00": pre, "asignados_a_un_periodo": total - pre,
                                 "rechazados": rechazados, "aceptados_asignados": aceptados,
                                 "ambiguos": 0, "fuera_de_ventana": bases_ev["assignment"]["out_of_window"]["total"]},
            "t0": {"total_CU": t0["total_CU"], "por_ramo_CU": t0["by_line_CU"], "periodos_entrenamiento": t0["rows_train"],
                   "periodos_con_coste": t0["rows_with_positive_cost"], "reserva_abiertos_CU": t0["reserve_open_total_CU"],
                   "abiertos": t0["open_claims_assigned"]},
            "periodos_sin_coste_pct": ceros}


def bloque_recalculo(d):
    """Recálculo independiente de las ocho reglas de datos desde los originales (D59)."""
    return {"controles": f"{d['checks_passed']}/{d['checks_total']}", "pasan": d["checks_passed"], "total": d["checks_total"],
            "modelos_entrenados": d.get("models_trained"), "revision_humana": d.get("human_review")}


def bloque_capitales(d):
    """Peso en la predicción entregada de los periodos de test con capital ajustado sin confirmación histórica."""
    return {"casos": d["casos"], "en_test": d["en_test"], "prediccion_CU": d["prediccion_CU"],
            "proporcion_del_total": d["proporcion_del_total"], "por_ramo": d["por_ramo"]}


PELIGROS_BT = {"motor": ["own_damage", "third_party_prop", "bodily_injury", "theft", "glass_hail"],
               "buildings": ["storm", "flood", "escape_of_water", "subsidence", "fire", "accidental_damage"],
               "contents": ["theft", "escape_of_water", "accidental_damage", "flood"]}


def bloque_backtest(e12, v):
    """Backtesting del IBNR (E12): chain-ladder de conteos reestimado en tres cortes y comparado con lo reportado hasta 12-2024."""
    cortes = list(e12["backtest"])
    celdas = []
    for c in cortes:
        por = {(x["line"], x["peril"]): x for x in e12["backtest"][c]}
        for ramo, pels in PELIGROS_BT.items():
            for pel in pels:
                x = por[(ramo, pel)]
                celdas.append({"corte": c, "ramo": ramo, "peligro": pel, "largo": bool(x["largo"]), "proyectado": r(x["pred"], 1),
                               "reportado": r(x["real"], 1), "error": r(x["error_rel"], 4), "limite": x["limite"], "cumple": bool(x["cumple"])})
    fuera = {c: sum(not x["cumple"] for x in e12["backtest"][c]) for c in cortes}
    alto_volumen = all(x["cumple"] for c in cortes for x in e12["backtest"][c] if x["line"] == "motor" and x["peril"] in ("own_damage", "third_party_prop"))
    return {"cortes": cortes, "peligros": len(e12["backtest"][cortes[0]]), "fuera_de_criterio": fuera,
            "fuera_min": min(fuera.values()), "fuera_max": max(fuera.values()),
            "control_D67": f'{sum(x["coincide"] for x in e12["control_M48"])}/{len(e12["control_M48"])}',
            "autos_alto_volumen_dentro": alto_volumen,
            "lesiones_ibnr_cierre": [v["E12_ult_2022-12_bodily_injury"], v["E12_ult_2023-12_bodily_injury"]],
            "lesiones_junio_2024": v["E12_bt_2024-06_bodily_injury"],
            "hundimiento_ibnr_cierre": [v["E12_ult_2022-12_subsidence"], v["E12_ult_2023-12_subsidence"]],
            "celdas": celdas}


def bloque_sensibilidad(lista, e04, e09, e10, e12):
    """Batería preinscrita de sensibilidad (D95): las cifras que los entregables declaran como validación y como límites."""
    v = {x["id"]: x["valor"] for x in lista}
    recobros = abs(v["E03_nivel"])
    ibnr = sorted(abs(v[k]) for k in ("E12_nivel_motor_2023-12", "E12_nivel_motor_2022-12"))
    return {"experimentos": 12, "cifras_ligadas": len(lista),
            "clientes_que_invierten_la_ventaja_V24": v["E01_kstar_V24"], "clientes_V24": v["E01_clientes_V24"],
            "nivel_edificios_semidistancia": v["E02_semi_buildings"], "nivel_autos_semidistancia": v["E02_semi_motor"],
            "nivel_autos_recobros": recobros, "nivel_autos_ibnr": ibnr,
            "nivel_autos_escenario": [r(recobros + ibnr[0], 5), r(recobros + ibnr[1], 5)],
            "capitales_multiplicador": [min(v["E05_cf_buildings_min"], v["E05_cf_contents_min"]), max(v["E05_cf_buildings_max"], v["E05_cf_contents_max"])],
            "vecinos_de_pesos_probados": v["E04_prob"],
            # Cifras para la tabla de experimentos (informe, anexo A3, y panel)
            "no_ejecutados": 1,  # «Semilla nueva»: cubierto por la corrida de cinco semillas y la reproducción (SENSIBILIDAD_S30_S22.md)
            "clientes_que_invierten_la_ventaja_V23": v["E01_kstar_V23"],
            "nivel_contenidos_semidistancia": v["E02_semi_contents"],
            "ventaja_con_reservas_V24": [v["E03_T1_0.75_V24"], v["E03_T1_1.0_V24"], v["E03_T1_1.25_V24"]],
            "piso_semillas": v["E07_piso"],
            "pesos_vecinos_que_mejoran": len(e04["vecinos_mejoran_todo"]),
            "tendencia_ventaja_min_V24": r(min(v["E08_pooled_V24_vs_S22"], v["E08_b0_V24_vs_S22"], v["E08_half_V24_vs_S22"]), 6),
            "forma_rango_vecindad": [r(min(e09[x]["rango_en_vecindad_0.02"][k] for x in ("motor", "buildings", "contents") for k in ("V23", "V24", "V23c", "V24c")), 6),
                                     r(max(e09[x]["rango_en_vecindad_0.02"][k] for x in ("motor", "buildings", "contents") for k in ("V23", "V24", "V23c", "V24c")), 6)],
            "forma_puntos_que_mejoran": sum(len(e09[x]["puntos_que_mejoran_todo"]) for x in ("motor", "buildings", "contents")),
            "cohortes_corr_edificios": v["E06_corr_b"],
            "reproduccion": {"archivos": len(e10), "predicciones": sum(x["filas"] for x in e10.values()),
                             "distintas": sum(x["filas_distintas"] for x in e10.values()), "max_rel": max(x["max_rel"] for x in e10.values())},
            "backtest_ibnr": bloque_backtest(e12, v)}


def bloque_modelo_definitivo(dec):
    """Decisión del participante (D99): S30 queda como modelo definitivo de la parte 1, con nombre propio para los entregables.
    El nombre no cambia el modelo; S30 sigue como identificador técnico y la selección manual en Kaggle sigue pendiente."""
    d = dec["decision"]
    return {"decision": dec["decision_id"], "fecha_utc": dec["mensaje_registrado_utc"], "modelo": d["modelo"],
            "nombre_es": d["nombre"]["es"], "nombre_en": d["nombre"]["en"], "sha256_csv": d["sha256_csv"],
            "parte1_cerrada": d["parte1_cerrada"], "seleccion_final_manual_kaggle": dec["seleccion_final_manual_kaggle"]}


def bloque_reproduccion(rec):
    """Reproducción completa (D97): reajuste de los 36 nodos desde los originales y réplica sin ajustes desde estimadores guardados.
    La hizo el mismo flujo asistido por IA en su nube de referencia: no es una reproducción independiente (GOV-003, D98)."""
    rc, rp = rec["reajuste_completo"], rec["replica"]
    cmp_ = rp["comprobacion"]
    minutos = (datetime.fromisoformat(rp["fin_utc"]) - datetime.fromisoformat(rp["inicio_utc"])).total_seconds() / 60
    return {"utc": rec["utc"], "nodos": cmp_["nodos"], "csv_iguales": all(x["coincide"] for x in rc["csv_finales"].values()),
            "huellas_verificadas": rc["huellas"]["verificadas_por_nodo"], "huellas_iguales": rc["huellas"]["iguales_contenido"],
            "huellas_difieren": rc["huellas"]["difieren"], "max_dif_relativa": rc["max_diferencia_relativa"],
            "codigo_salida": rc["componentes"]["codigo_salida"],
            "replica": {"csv_iguales": all(x["coincide"] for x in rp["csv_finales"].values()), "estimadores": cmp_["estimadores_guardados"],
                        "cargas": cmp_["cargas"], "salidas": cmp_["salidas_cotejadas"], "identicas": cmp_["salidas_identicas_bytes"],
                        "minutos": round(minutos), "nodos_conformes": cmp_["nodos_conformes"]},
            "independiente": False}


def bloque_reservas(res, pb, aut):
    """Acotación de reservas con una sola valoración (CLA-20261019-008): cuánto error de reserva de caso mueve el nivel
    2025 de cada ramo más allá de la materialidad que fijó el participante antes de calcular. No acredita suficiencia."""
    por = {}
    for ramo in ("motor", "buildings", "contents"):
        u, s = pb["ramos"][ramo]["umbrales"]["todos"], res["ramos"][ramo]
        por[ramo] = {"umbral_b": [u["reserva_b_menos_1pct"], u["reserva_b_mas_1pct"]],
                     "error_material": r(min(1 - u["reserva_b_menos_1pct"], u["reserva_b_mas_1pct"] - 1), 4),
                     "nivel_b_075": u["nivel_b_0_75"], "nivel_b_125": u["nivel_b_1_25"],
                     "beta": s["beta_reserva"], "ic90": s["ic90"], "clase": s["clase"]}
    bi = res["ramos"]["motor"]["ibnr"]["por_peligro"]["bodily_injury"]
    orden = pb["orden_S30_S22_agregado"]["todos"]["rango_con_el_signo_de_b1"]
    return {"materialidad": pb["materialidad"], "materialidad_fijada": "por el participante antes de calcular",
            "autorizacion_utc": aut["registrado_utc"], "por_ramo": por,
            "nivel_max_con_b_075_125": r(max(abs(por[x][k]) for x in por for k in ("nivel_b_075", "nivel_b_125")), 5),
            "ramos_con_incertidumbre_material": sum(por[x]["clase"] == "incertidumbre_material" for x in por),
            "lesiones_S3": {"k": bi["k"], "ic90_k": bi["ic90_k"], "nivel": bi["nivel_2025_con_k"], "nivel_ic90": bi["nivel_2025_con_ic90_k"]},
            "orden_agregado_sin_cambio_b": [max(orden[c]["desde"] for c in ("V23", "V24")), min(orden[c]["hasta"] for c in ("V23", "V24"))]}


def bloque_foro(txt):
    cab = re.findall(r"^## (Codex|Claude|Participante) \| ([A-Z]{3}[^|]*?) \| ([0-9T:\-+.]+) \| (.*)$", txt, re.M)
    pre = re.compile(r"predeclarad|preinscrip|fijad|predefinid|preregistr|método previo|diseño previo|antes de (entrenar|evaluar|resultados|ver|ajust)", re.I)
    adv = re.compile(r"descartad|retenid|no mejora|no supera|sin candidato|adverso|no hay s2|sin efecto|bajo el umbral|no resiste|no cierra|falla|insuficiente|no resuelve|sin mejora|no aporta", re.I)
    val = re.compile(r"^COD-(VAL|IA|DOC)|ENJ|PLAN|CIERRE")
    tipos = Counter()
    bloques = {}
    for autor, ident, ts, titulo in cab:
        ident = ident.strip()
        if val.search(ident):
            t = "validacion"
        elif adv.search(titulo):
            t = "adverso"
        elif pre.search(titulo):
            t = "preinscripcion"
        else:
            t = "resultado_o_coordinacion"
        tipos[t] += 1
        clave = f"{ts[:10]} {int(ts[11:13]) // 6 * 6:02d}h"
        bloques.setdefault(clave, Counter())[t] += 1
    contrastes = sorted({int(m) for _, _, _, t in cab for m in re.findall(r"\bC(\d{2})\b", t)})
    anclas = sorted({int(m) for _, _, _, t in cab for m in re.findall(r"\bA(\d{2})\b", t)})
    t_ini = datetime.fromisoformat(cab[0][2])
    t_fin = datetime.fromisoformat(cab[-1][2])
    return {"aportes": len(cab), "horas": r((t_fin - t_ini).total_seconds() / 3600, 1), "primero_utc": cab[0][2], "ultimo_utc": cab[-1][2],
            "por_tipo": dict(tipos), "titulos_con_preinscripcion": sum(bool(pre.search(t)) for *_, t in cab),
            "titulos_con_resultado_adverso": sum(bool(adv.search(t)) for *_, t in cab),
            "contrastes_numerados": len(contrastes) + len(anclas),
            "por_bloque_6h": [{"bloque_utc": k, **dict(v)} for k, v in sorted(bloques.items())],
            "criterio": "Clasificación por identificador y palabras del título, sin leer cuerpos: validación (series VAL, IA, DOC, ENJ, PLAN, CIERRE), "
                        "resultado adverso o descarte, preinscripción con criterio fijado antes de resultados, y el resto."}


def bloque_validacion_ia(ciclo, hall, sev, rev_humana, dec_gov007):
    """Hallazgos del enjambre con su estado vigente: el del registro del auditor, el subestado técnico del último ciclo
    y, encima, las decisiones fechadas del participante (hoy solo GOV-007, en el alcance de la corrección técnica)."""
    decisiones = {k: v for k, v in (rev_humana.get("decisiones_especificas") or {}).items()}
    if dec_gov007.get("id") == "GOV-007":
        decisiones.setdefault("GOV-007", {}).update({"estado": dec_gov007["estado"], "alcance": dec_gov007["alcance"],
                                                     "fecha": dec_gov007["fecha_declaracion_utc"]})
    tecnicos = {c.get("id") for c in ciclo.get("technical_substate_changes", [])}
    lista = []
    for h in hall:
        estado = h["estado_registro_recibido"]
        if h["id"] in tecnicos:
            estado = "remediacion_tecnica_verificada"
        d = decisiones.get(h["id"])
        if d and d.get("estado"):
            estado = d["estado"]
        lista.append({"id": h["id"], "area": h["area"], "severidad": h["severidad"], "estado": estado,
                      "titulo_es": TITULOS_HALLAZGOS[h["id"]][0], "titulo_en": TITULOS_HALLAZGOS[h["id"]][1],
                      "revisor": h.get("revisor_necesario"),
                      "decision_humana": ({"fecha": d.get("fecha"), "alcance": d.get("alcance")} if d else None)})
    return {"ciclo": ciclo["run_id"], "cerrado_utc": ciclo["closed_at_utc"], "por_estado_ciclo": ciclo["counts_by_status"],
            "por_estado": dict(Counter(x["estado"] for x in lista)), "lista": lista, "hallazgos": len(hall),
            "abiertos": sum(1 for x in lista if x["estado"] == "abierto"),
            "limitaciones_aceptadas": sum(1 for x in lista if x["estado"].startswith("limitacion_aceptada")),
            "cerrados_o_remediados": sum(1 for x in lista if x["estado"] != "abierto" and not x["estado"].startswith("limitacion_aceptada")),
            "por_severidad": dict(sev),
            "cambios_tecnicos": ciclo.get("technical_substate_changes", []),
            "revision_especialista": ciclo["human_specialist_review"],
            "revision_humana_general": rev_humana.get("estado"), "independencia_acreditada": rev_humana.get("independencia_acreditada")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raiz", type=Path, default=REPO.parents[1])
    ap.add_argument("--salida", type=Path, default=REPO / "docs/entrega/datos/cifras_entregables.json")
    a = ap.parse_args()
    raiz = a.raiz.resolve()
    rutas = {k: raiz / v for k, v in FUENTES.items()}
    faltan = [k for k, p in rutas.items() if not p.is_file()]
    if faltan:
        raise SystemExit(f"Faltan fuentes: {faltan}")
    fuentes = {k: {"ruta": FUENTES[k], "sha256": sha(p), "bytes": p.stat().st_size} for k, p in rutas.items()}
    reg = leer(rutas["registro_envios"])
    entrega = leer(rutas["entrega_s30"])
    reglas = leer(rutas["reglas_kaggle"])
    n62, bases_ev, f0, bases67 = leer(rutas["base_n62"]), leer(rutas["bases_evidencia"]), leer(rutas["f0_d68"]), leer(rutas["bases_d67"])
    m00 = {x["split"]: x for x in filas(rutas["referencias_m00"])}
    pred = bloque_predicciones(rutas["predicciones_s30"])
    val = entrega["validacion"]
    comp = []
    for ramo, items in leer(rutas["spec_s30"]).items():
        if ramo not in RAMOS:
            continue
        for nombre, _, peso in items:
            tipo = "frecuencia_severidad" if any(t in nombre for t in ("CFST", "FSA")) else "coste_total"
            comp.append({"ramo": ramo, "componente": nombre, "peso": peso, "tipo": tipo})
    controles = []
    for k in ("controles_nube", "controles_vm", "controles_windows"):
        x = leer(rutas[k])
        controles.append({"fuente": k, "utc": x["utc"], "version": x["version_reproducir"],
                          "python": x["entorno"].get("python") if isinstance(x["entorno"], dict) else x["entorno"],
                          "casos": x["casos"], "pasan": x["pasan"], "fallan": len(x["fallan"])})
    replay = leer(rutas["replay_windows"])
    ciclo = leer(rutas["ciclo_validacion"])
    hall = leer(rutas["hallazgos"])
    sev = Counter(h["severidad"] for h in hall)
    pre = [x for x in leer(rutas["preflight"]) if x["candidato"] == "S30"][0]
    iaa = leer(rutas["papers_iaa"])["papers"]
    fa, fb = leer(rutas["fuentes_investigacion_a"])["sources"], leer(rutas["fuentes_investigacion_b"])["sources"]
    receta = leer(rutas["receta"])
    nodos_s30 = sum("S30" in n.get("objetivos", []) for n in receta["nodos"])
    minutos_s30 = sum(n.get("minutos_ref") or 0 for n in receta["nodos"] if "S30" in n.get("objetivos", []))
    datos = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "herramientas/cifras_entregables.py",
        "alcance": "Cifras agregadas para la entrega final. Sin datos por fila, sin entrenamiento, sin envíos.",
        "fuentes": fuentes,
        "concurso": {"cierre_parte1_utc": reglas["metadata"]["deadline"], "equipos": reglas["metadata"]["team_count"],
                     "puesto_publico_consultado": reglas["metadata"]["user_rank"], "consulta_utc": reglas["retrieved_utc"],
                     "metrica": "D² Tweedie, potencia 1,5", "envios_diarios": reglas["metadata"]["max_daily_submissions"]},
        "s30": {"publico": 0.12996, "envio_kaggle": 57371361, "sha256_csv": pre["sha256"], "filas": pre["filas"],
                "controles_csv": pre["checks"], "total_2025_CU": entrega["total_CU"], "por_ramo_2025_CU": entrega["por_ramo_CU"],
                "tasa_2025_por_anio_exposicion": entrega["tasa_2025_por_unidad_de_exposicion"],
                "factores_nivel": {l: {"f23": val["por_ramo"][l]["f23"], "f24": val["por_ramo"][l]["f24"], "f": val["por_ramo"][l]["f"]} for l in RAMOS},
                "forma": entrega["composicion"]["forma"], "composicion": comp,
                "cuerpo_global": val["cuerpo_global"]["S30"]},
        "validacion": {"d2_recalculado": pred["d2"], "media_por_ramo": pred["media"],
                       "d2_registrado_v24": val["d2_v24_global_con_factor_v23"],
                       "referencia_m00": {s: {"agregado": r(m00[s]["d2_tasa_ramo_balance_x_exposicion"]),
                                              "motor": r(m00[s]["d2_ramo_motor_balance"]),
                                              "buildings": r(m00[s]["d2_ramo_buildings_balance"]),
                                              "contents": r(m00[s]["d2_ramo_contents_balance"])} for s in ("V23", "V24")},
                       "referencia_publica_coste_medio": bases67["m00_reference_d2"]["public_average_cost_reference_D64"],
                       "reservas": pred["reservas"], "deciles_v24": pred["deciles_v24"], "concentracion_v24": pred["concentracion_v24"]},
        "envios": bloque_envios(reg),
        "publico_vs_local": bloque_publico_local(filas(rutas["publico_vs_local"]), entrega),
        "ibnr": bloque_ibnr(filas(rutas["ibnr_peligro"]), filas(rutas["ibnr_ramo"]), filas(rutas["prima_ultima"]),
                            filas(rutas["reservas_ramo_anio"]), entrega),
        "datos": dict(bloque_datos(n62, bases_ev, filas(rutas["asignacion"]), f0, filas(rutas["frecuencia"])),
                      recalculo_independiente=bloque_recalculo(leer(rutas["recalculo_d59"])),
                      capitales_sin_confirmar=bloque_capitales(leer(rutas["capitales_149"]))),
        "foro": bloque_foro(rutas["foro"].read_text(encoding="utf-8")),
        "validacion_ia": bloque_validacion_ia(ciclo, hall, sev, leer(rutas["revision_humana"]), leer(rutas["decision_gov007"])),
        "controles_paquete": {"baterias": controles, "replay_s30": {"sha256": replay["objetivos"]["S30"]["sha256"],
                              "coincide": replay["objetivos"]["S30"]["coincide"], "codigo_salida": replay["codigo_salida"],
                              "max_rel_parquet": [d["max_rel"] for d in replay["diferencias_intermedias"] if d["candidato"] == "S30"][0]},
                              "nodos_receta_total": len(receta["nodos"]), "nodos_s30": nodos_s30,
                              "horas_referencia_s30": r(minutos_s30 / 60, 1)},
        "metodologia": {"fuentes_investigacion": len(fa) + len(fb), "fuentes_a": len(fa), "fuentes_b": len(fb),
                        "papers_iaa": [{"titulo": p["title"], "fecha": p["cover_date"]} for p in iaa]},
        "sensibilidad": bloque_sensibilidad(leer(rutas["sensibilidad"]), leer(rutas["sens_e04"]), leer(rutas["sens_e09"]),
                                            leer(rutas["sens_e10"]), leer(rutas["sens_e12"])),
        "reproduccion_completa": bloque_reproduccion(leer(rutas["reproduccion_completa"])),
        "reservas_acotacion": bloque_reservas(leer(rutas["reservas_resumen"]), leer(rutas["reservas_umbrales"]),
                                              leer(rutas["reservas_autorizacion"])),
        "modelo_definitivo": bloque_modelo_definitivo(leer(rutas["decision_modelo_definitivo"])),
        "bases": {"controles": f"{bases67['checks_passed']}/{bases67['checks_total']}", "f0_controles": f"{f0['checks_passed']}/{f0['checks_total']}"},
    }
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"salida": str(a.salida), "fuentes": len(fuentes), "d2_v24": pred["d2"]["V24"]["agregado"],
                      "aportes_foro": datos["foro"]["aportes"], "envios": len(datos["envios"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
