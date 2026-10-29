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
    "sensibilidad_informe": "Hackaton/Repositorio_IAA2026/docs/archivo/semana1/SENSIBILIDAD_S30_S22.md",
    "sens_e04": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e04.json",
    "sens_e09": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e09.json",
    "sens_e10": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e10_reproduccion.json",
    "sens_e12": "Hackaton/Repositorio_IAA2026/privado/corridas/sens_20261019T212700Z_b9e7aa92/resultados/e12.json",
    "reproduccion_completa": "Hackaton/Repositorio_IAA2026/registro/recibo_reproduccion_completa_20261020.json",
    "reproduccion_documento": "Hackaton/Repositorio_IAA2026/docs/REPRODUCCION_COMPLETA.md",
    "decisiones_participante": "Hackaton/Repositorio_IAA2026/registro/decisiones_participante_20261020.json",
    "reservas_resumen": "Hackaton/Repositorio_IAA2026/privado/corridas/reservas_20261019T225357Z_99b45271/resultados/resumen.json",
    "reservas_umbrales": "Hackaton/Repositorio_IAA2026/privado/corridas/reservas_20261019T225357Z_99b45271/resultados/parte_b.json",
    "reservas_informe": "Hackaton/Repositorio_IAA2026/docs/archivo/semana1/RESERVAS_ACOTACION.md",
    "reservas_autorizacion": "Hackaton/Repositorio_IAA2026/registro/autorizacion_reproduccion_reservas_20261019.json",
    "decision_modelo_definitivo": "Hackaton/Repositorio_IAA2026/registro/decision_modelo_definitivo_20261020.json",
    # Calibración del nivel 2025 con el marcador público (D100, D101) y entrega final S42
    "sonda_preinscripcion": "Hackaton/Repositorio_IAA2026/registro/sonda_nivel_D100_preinscripcion.json",
    "sonda_resolucion": "Hackaton/Repositorio_IAA2026/registro/sonda_nivel_D100_resolucion.json",
    "sonda_revision": "Hackaton/Repositorio_IAA2026/registro/sonda_nivel_D101_revision.json",
    "sonda_recibos": "Hackaton/Repositorio_IAA2026/registro/sonda_nivel_D100_recibos.json",
    "envios_s41_s42": "Hackaton/Repositorio_IAA2026/registro/envios_S41_S42_20261022_recibos.json",
    "entrega_final": "Hackaton/Repositorio_IAA2026/docs/evidencia/entrega_final_S42.json",
    "concurso_final": "Hackaton/Repositorio_IAA2026/privado/envio_S43_20261022/after_final.json",
    # Calibración de la forma 2025 (D102), entrega S43 y baterías de sensibilidad posteriores (sens42 y sens43, D103)
    "forma_preinscripcion": "Hackaton/Repositorio_IAA2026/registro/sonda_forma_D102_preinscripcion.json",
    "forma_resolucion": "Hackaton/Repositorio_IAA2026/registro/sonda_forma_D102_resolucion.json",
    "forma_recibos": "Hackaton/Repositorio_IAA2026/registro/sonda_forma_D102_recibos.json",
    "envio_s43": "Hackaton/Repositorio_IAA2026/registro/envio_S43_20261022_recibo.json",
    "sens_l03": "Hackaton/Repositorio_IAA2026/privado/corridas/sens42_20261022T165934Z_6ec8f1fe/resultados/l03.json",
    "sens_l04": "Hackaton/Repositorio_IAA2026/privado/corridas/sens42_20261022T165934Z_6ec8f1fe/resultados/l04.json",
    "sens_l05": "Hackaton/Repositorio_IAA2026/privado/corridas/sens42_20261022T165934Z_6ec8f1fe/resultados/l05_l07.json",
    "sens_n01": "Hackaton/Repositorio_IAA2026/privado/corridas/sens43_20261023T035154Z_aece6462/resultados/n01_n02_n08_n09.json",
    "sens_n03": "Hackaton/Repositorio_IAA2026/privado/corridas/sens43_20261023T035154Z_aece6462/resultados/n03_n04_n06_n07.json",
    "sens_n05": "Hackaton/Repositorio_IAA2026/privado/corridas/sens43_20261023T035154Z_aece6462/resultados/n05.json",
    "sens_n06": "Hackaton/Repositorio_IAA2026/privado/corridas/sens43_20261023T035154Z_aece6462/resultados/n06_clasificacion.json",
    "sens_robustez": "Hackaton/Repositorio_IAA2026/privado/corridas/sens43_20261023T035154Z_aece6462/resultados/n05_robustez.json",
    "sensibilidad_s43_informe": "Hackaton/Repositorio_IAA2026/docs/archivo/semana1/SENSIBILIDAD_S43.md",
    "prima_escrita": "Hackaton/Repositorio_IAA2026/docs/evidencia/prima_escrita_por_anio.json",
    "reservas_s42": "Hackaton/Repositorio_IAA2026/privado/corridas/repro_s42_20261022T170245Z_c9ea2fc3/resultados/parte2_resumen.json",
    "recibo_repro_s42": "Hackaton/Repositorio_IAA2026/registro/recibo_reproduccion_s42_20261022.json",
    # Comprobaciones de S43 hechas después de enviarlo: reproducción del paso de forma y reservas con su regla
    # (repro_s43, línea principal) y controles del CSV con código propio del segundo asistente (integral de Codex).
    "recibo_repro_s43": "Hackaton/Repositorio_IAA2026/registro/recibo_reproduccion_s43_20261023.json",
    "reservas_s43": "Hackaton/Repositorio_IAA2026/privado/corridas/repro_s43_20261023T141352Z_fbf66589/resultados/parte2_resumen.json",
    "csv_s43_segundo_asistente": "foros/validacion_ia_periodica/runs/20261023T052704Z_integral/csv_checks.json",
    # Entrega final S41 (CIE-D103-20261023): el participante marcó S41 tras la alarma de D103; regeneración y diez controles
    "entrega_final_s41": "Hackaton/Repositorio_IAA2026/docs/evidencia/entrega_final_S41.json",
    "decision_marca_s41": "Hackaton/Repositorio_IAA2026/registro/decision_marca_final_S41_20261023.json",
    # Reproducción del paso de nivel y reservas con la regla de S41 (repro_s41, línea principal, CLA-20261023-005) y
    # decisión del participante de mantener para S41 la limitación de reservas (DEC-RESERVAS-S41-20261023, CLA-20261023-006)
    "recibo_repro_s41": "Hackaton/Repositorio_IAA2026/registro/recibo_reproduccion_s41_20261023.json",
    "reservas_s41": "Hackaton/Repositorio_IAA2026/privado/corridas/repro_s41_20261023T145808Z_c8055dfc/resultados/parte2_resumen.json",
    "decision_reservas_s41": "Hackaton/Repositorio_IAA2026/registro/decision_reservas_S41_20261023.json",
}
# Las cifras del foro cuentan los aportes hasta el registro de la selección final de la parte 1. El foro se escribe solo
# añadiendo al final, así que los aportes posteriores no cambian esas cifras; el verificador comprueba la huella de esa parte.
CORTE_FORO = "CLA-20261023-002"
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
    "S40_sonda_motor_x090": ("Sonda de nivel: autos × 0,90", "Level probe: motor × 0.90"),
    "S40_sonda_motor_x110": ("Sonda de nivel: autos × 1,10", "Level probe: motor × 1.10"),
    "S40_sonda_buildings_x090": ("Sonda de nivel: edificios × 0,90", "Level probe: buildings × 0.90"),
    "S40_sonda_buildings_x110": ("Sonda de nivel: edificios × 1,10", "Level probe: buildings × 1.10"),
    "S40_sonda_contents_x090": ("Sonda de nivel: contenidos × 0,90", "Level probe: contents × 0.90"),
    "S40_sonda_contents_x110": ("Sonda de nivel: contenidos × 1,10", "Level probe: contents × 1.10"),
    "S41_nivel_credibilidad": ("Nivel 2025 con la credibilidad preinscrita", "2025 level, pre-registered credibility"),
    "S42_nivel_credibilidad_revisada": ("Nivel 2025 con la credibilidad revisada", "2025 level, revised credibility"),
    "S50_sonda_forma_motor_a090": ("Sonda de forma: autos a = 0,90", "Shape probe: motor a = 0.90"),
    "S50_sonda_forma_motor_a110": ("Sonda de forma: autos a = 1,10", "Shape probe: motor a = 1.10"),
    "S50_sonda_forma_buildings_a090": ("Sonda de forma: edificios a = 0,90", "Shape probe: buildings a = 0.90"),
    "S50_sonda_forma_buildings_a110": ("Sonda de forma: edificios a = 1,10", "Shape probe: buildings a = 1.10"),
    "S50_sonda_forma_contents_a090": ("Sonda de forma: contenidos a = 0,90", "Shape probe: contents a = 0.90"),
    "S50_sonda_forma_contents_a110": ("Sonda de forma: contenidos a = 1,10", "Shape probe: contents a = 1.10"),
    "S43_forma_credibilidad": ("Nivel y forma 2025 con credibilidad", "2025 level and shape, with credibility"),
}
RAMOS = ("motor", "buildings", "contents")
# Títulos breves y neutrales de los hallazgos del enjambre de validación (traducción editorial del registro original).
TITULOS_HALLAZGOS = {
    "DATA-001": ("Disponibilidad al cotizar sin acreditar en variables condicionadas y clima anual", "Availability at quotation not proven for conditional features and annual weather"),
    "DATA-002": ("Una sola valoración y ningún último observado limitan el contraste", "A single valuation and no observed ultimate limit the backtest"),
    "DATA-003": ("La escala de capitales en la matriz conserva casos sin confirmación histórica", "Sum-insured scaling keeps cases without historical confirmation"),
    "DATA-004": ("El comparador inicial de asignación debía separar los siniestros previos", "The first assignment comparator had to separate pre-history claims"),
    "DATA-005": ("Historia y clima del año anterior incluyen información posterior al corte de cotización", "Prior-year history and weather include information after the quotation cut"),
    "DATA-006": ("La prima escrita se lee como tarifa anual sin que el diccionario lo diga", "Written premium is read as an annual rate the data dictionary does not state"),
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
        tipo = ("sonda" if x["id"].startswith("S40_") else "sonda_forma" if x["id"].startswith("S50_")
                else "calibracion" if x["id"].startswith(("S41_", "S42_", "S43_")) else "modelo")
        envios.append({"id": x["id"], "utc": x.get("submitted_utc"), "publico": x["public_score"], "tipo": tipo,
                       "seleccion_final": bool(x.get("selected_final")),
                       "v24_local": r(v24, 5) if tipo == "modelo" else None, "etiqueta_es": ETIQUETAS.get(x["id"], (x["id"], x["id"]))[0],
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
                    "La prima de 2025 es el total predicho dividido por la exposición nominal de 2025: prediccion_S30 para el modelo y prediccion_final para la entrega (S42)."}


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


def chi2_sf_3gl(x):
    """Probabilidad de cola de una ji cuadrado con 3 grados de libertad (forma cerrada, sin scipy)."""
    from math import erfc, exp, pi, sqrt
    return erfc(sqrt(x / 2)) + sqrt(2 * x / pi) * exp(-x / 2)


def bloque_calibracion(pre, res, rev, s30, sens, prima, pr_anio):
    """Calibración del nivel 2025 por ramo con el marcador público (D100 y D101): tres factores sobre S30.

    Para la desviación Tweedie 1,5, D²(c) − D²(1) = −4·[S1·(c^−½ − 1) + S2·(c^½ − 1)]/N en las filas públicas del ramo;
    dos sondas por ramo (×0,90 y ×1,10) fijan S1/N y S2/N y el óptimo c* = S1/S2. Se aplica solo la fracción creíble
    c = 1 + Z·(c* − 1), Z = τ²/(τ² + σ²): S41 con la τ preinscrita y S42 con la τ revisada tras ver el marcador."""
    R, V, P = res["resolucion"], rev["revision"], pre["preinscrito"]
    d0 = R["s30_publico"]
    ramos = {}
    for l in RAMOS:
        a, b = R["ramos"][l], V["ramos"][l]
        x, z = a["S1_sobre_N"], a["S2_sobre_N"]
        curva = []
        for k in range(49):
            c = 0.88 + k * 0.005
            curva.append([round(c, 3), r(d0 - 4 * (x * (c ** -0.5 - 1) + z * (c ** 0.5 - 1)), 6)])
        f23, f24 = P["factores_s30"][l]["f23"], P["factores_s30"][l]["f24"]
        ult24 = next(q for q in pr_anio if q["ramo"] == l and q["anio"] == 2024)["prima_T0_mas_IBNR"]
        tasa30 = s30["tasa_2025_por_anio_exposicion"][l]
        # Crecimiento frente al último de 2024 con la tasa sin redondear (total del ramo entre la exposición de 2025).
        tasa30u = s30["por_ramo_2025_CU"][l] / prima["ramos"][l]["por_anio"]["2025"]["exposicion"]
        ramos[l] = {"publico_x090": a["publico_x090"], "publico_x110": a["publico_x110"],
                    "S1_sobre_N": r(x, 6), "S2_sobre_N": r(z, 6), "c_optimo": r(a["c_optimo_publico"], 4),
                    "d2_publico_en_optimo": r(a["D2_publico_en_c_optimo"], 6), "ganancia_publico_optimo": r(a["ganancia_publico_en_c_optimo"], 6),
                    "sigma_ruido": r(P["sigma_ruido_33pct_bootstrap_2024"][l], 4), "tau_previa": P["tau_previa"][l],
                    "Z_previa": r(a["Z"], 3), "c_S41": r(a["c_Z"], 4), "ganancia_publico_S41": r(a["ganancia_publico_en_c_Z"], 6),
                    "Z_revisada": r(b["Z_revisada"], 3), "c_S42": r(b["c_revisado"], 4), "ganancia_publico_S42": r(b["ganancia_publico_esperada"], 6),
                    "privado_S42": [r(b["ganancia_privada_esperada_si_previa_D100"], 8), r(b["ganancia_privada_esperada_si_tau_revisada"], 8)],
                    "f23": f23, "f24": f24, "f_modelo": r((f23 + f24) / 2, 4), "nivel_implicito_publico": r(a["lectura"]["nivel_implicito_publico"], 3),
                    "f_final": r((f23 + f24) / 2 * b["c_revisado"], 4), "f_final_S41": r((f23 + f24) / 2 * a["c_Z"], 4),
                    "tasa_2025_S41": r(tasa30u * a["c_Z"], 1), "crecimiento_2025_S41": r(tasa30u * a["c_Z"] / ult24 - 1, 4),
                    "uno_menos_Z_previa": r(1 - a["Z"], 3),
                    "prima_escrita_2024_2025": prima["ramos"][l]["cambio_2024_2025"],
                    "tasa_2025_modelo": tasa30, "tasa_2025_final": r(tasa30u * b["c_revisado"], 1), "ultimo_2024": ult24,
                    "crecimiento_2025_modelo": r(tasa30u / ult24 - 1, 4), "crecimiento_2025_final": r(tasa30u * b["c_revisado"] / ult24 - 1, 4),
                    "curva": curva}
    bt = pre["bootstrap"]["ganancia_D2_aplicando_c_del_33pct"]
    chi2 = V["suma_desvios_estandarizados_bajo_previa_D100"]
    return {"publico_modelo": d0, "sondas": 6, "factores_sonda": [0.9, 1.1], "fraccion_publico": 0.33,
            "formula": "D²(c) − D²(1) = −4·[S1·(c^−½ − 1) + S2·(c^½ − 1)]/N; c* = S1/S2; c = 1 + Z·(c* − 1); Z = τ²/(τ² + σ²)",
            "bootstrap": {"replicas": pre["bootstrap"]["replicas"], "ganancia_33": r(bt["en_el_33pct_media"], 6),
                          "ganancia_67_media": r(bt["en_el_67pct_media"], 6), "ganancia_67_p05": r(bt["en_el_67pct_p05"], 6),
                          "sigma_min": r(min(P["sigma_ruido_33pct_bootstrap_2024"].values()), 3), "sigma_max": r(max(P["sigma_ruido_33pct_bootstrap_2024"].values()), 3)},
            "tau_previa_min": min(P["tau_previa"].values()), "tau_previa_max": max(P["tau_previa"].values()),
            "tau_revisada": r(V["tau_revisada"], 4), "chi2": r(chi2, 2), "gl": V["grados_de_libertad"], "p_valor": r(chi2_sf_3gl(chi2), 3),
            "S41": {"esperado": r(R["D2_publico_esperado_S41"], 6), "privado": [r(V["privado_esperado_S41"]["si_previa_D100"], 8), r(V["privado_esperado_S41"]["si_tau_revisada"], 8)]},
            "S42": {"esperado": r(V["D2_publico_esperado_S42"], 6), "privado": [r(V["privado_esperado_S42"]["si_previa_D100"], 8), r(V["privado_esperado_S42"]["si_tau_revisada"], 8)]},
            "evidencia_autos": {"escenario_nivel_alto": sens["nivel_autos_escenario"], "recobros": sens["nivel_autos_recobros"], "ibnr": sens["nivel_autos_ibnr"]},
            "ramos": ramos,
            "nota": "Las sondas son diagnósticas y nunca se seleccionan. S41 aplica la regla preinscrita; S42 la revisión posterior a ver el marcador (D101)."}


def rango_c_optimo_por_redondeo(d090, d100, d110, medio=0.000005):
    """Rango determinista de c* = S1/S2 si cada una de las tres puntuaciones públicas del ramo (×0,90, ×1,00 y ×1,10)
    se mueve ±medio, la mitad de la última cifra que publica Kaggle. Resuelve el sistema lineal de la forma cerrada en las
    ocho esquinas; no es un intervalo estadístico."""
    from itertools import product
    vals = []
    for e0, e1, e2 in product((-medio, medio), repeat=3):
        y1, y2 = (d090 + e0) - (d100 + e1), (d110 + e2) - (d100 + e1)
        a1, b1 = -4 * (0.9 ** -0.5 - 1), -4 * (0.9 ** 0.5 - 1)
        a2, b2 = -4 * (1.1 ** -0.5 - 1), -4 * (1.1 ** 0.5 - 1)
        det = a1 * b2 - a2 * b1
        x, z = (y1 * b2 - y2 * b1) / det, (a1 * y2 - a2 * y1) / det
        vals.append(x / z)
    return [min(vals), max(vals)]


def bloque_evidencia_nivel(cal, ent, prima, s30, sens, pre, res42, recibo42, l05):
    """Evidencia del nivel 2025 que no usa el marcador: la de L05 de la batería sens42, publicada en
    docs/archivo/semana1/SENSIBILIDAD_S43.md, con su criterio escrito antes de calcular. Señales por ramo: (a) el último año, f24/f − 1;
    (b) los efectos de etiqueta de D95 (IBNR del backtesting en los tres ramos y, en autos, las recuperaciones no
    anticipadas); (c) el ajuste que deja la siniestralidad de 2025 igual a la de 2024 (último de D67 entre prima escrita,
    por año expuesto). «Apoyado» si al menos dos señales coinciden en signo con el ajuste y su tamaño no supera la mayor
    más la τ de D100; «parcial» con una, o con dos o más y el tamaño fuera; «sin apoyo» con ninguna. Es independiente del
    marcador, no de los datos ni de los supuestos del proyecto, y no es validación profesional independiente.
    L05 suma la prima por año expuesto (Σ prima / Σ e); con la prima leída como tarifa anual (Σ prima·e / Σ e,
    docs/evidencia/prima_escrita_por_anio.json) la señal (c) se recalcula aquí para mostrar que la lectura no depende
    de esa unidad, que DATA-006 deja sin confirmar.
    Añade las reservas con la regla de S42 y la repetición del paso de nivel (CLA-20261022-005) y el rango de c* por el
    redondeo de las puntuaciones (COD-IA-20261022T172751Z lo calculó aparte)."""
    P = pre["preinscrito"]
    ev = {}
    for l in RAMOS:
        z = l05["ramos"][l]
        ind = z["indicadores"]
        g_l05, g_anual = z["crec_prima_24_25"], prima["ramos"][l]["cambio_2024_2025"]
        c_anual = (1 + ind["c_ratio_siniestralidad_2024"]) * (1 + g_anual) / (1 + g_l05) - 1
        ajuste = z["ajuste_S42"]
        alt = {"a_ultimo_anio": ind["a_ultimo_anio"], "b_etiqueta_D95": ind["b_etiqueta_D95"], "c_ratio_siniestralidad_2024": c_anual}
        acuerdan_alt = [k for k, v in alt.items() if v != 0 and (v > 0) == (ajuste > 0)]
        tope_alt = max([abs(alt[k]) for k in acuerdan_alt], default=0.0) + P["tau_previa"][l]
        clase_alt = ("apoyado" if len(acuerdan_alt) >= 2 and abs(ajuste) <= tope_alt else "parcial" if acuerdan_alt else "sin apoyo")
        clase = z["clasificacion"]
        assert clase_alt == clase, (l, clase, clase_alt)
        a41 = z["ajuste_S41"]
        def clasificar(aj, ind_):
            acuerdan = [k for k, v in ind_.items() if v != 0 and (v > 0) == (aj > 0)]
            tope = max([abs(ind_[k]) for k in acuerdan], default=0.0) + P["tau_previa"][l]
            return acuerdan, tope, ("apoyado" if len(acuerdan) >= 2 and abs(aj) <= tope else "parcial" if acuerdan else "sin_apoyo")
        ind_l05 = {"a_ultimo_anio": ind["a_ultimo_anio"], "b_etiqueta_D95": ind["b_etiqueta_D95"], "c_ratio_siniestralidad_2024": ind["c_ratio_siniestralidad_2024"]}
        ac41, tope41, clase41 = clasificar(a41, ind_l05)
        _, _, clase41_anual = clasificar(a41, alt)
        assert clase41 == clase41_anual, (l, clase41, clase41_anual)
        # comprobación: el mismo cálculo reproduce la clase publicada por L05 para S42
        assert clasificar(ajuste, ind_l05)[2] == ("sin_apoyo" if clase == "sin apoyo" else clase), (l, clase)
        ev[l] = {"ajuste_S42": r(ajuste, 4), "ajuste_S41": r(a41, 4),
                 "clase_S41": clase41, "coinciden_S41": ac41, "tope_tamano_S41": r(tope41, 4),
                 "parcial_por_tamano_S41": clase41 == "parcial" and len(ac41) >= 2,
                 "indicadores": {"ultimo_anio": r(ind["a_ultimo_anio"], 4), "etiqueta_D95": r(ind["b_etiqueta_D95"], 4),
                                 "siniestralidad_2024": r(ind["c_ratio_siniestralidad_2024"], 4)},
                 "siniestralidad_2024_prima_anual": r(c_anual, 4), "clase_con_prima_anual": clase_alt,
                 "coinciden": z["acuerdan_en_signo"], "tope_tamano": r(z["magnitud_max_que_acuerda"] + z["tau_D100"], 4),
                 "clase": "apoyado" if clase == "apoyado" else ("parcial" if clase == "parcial" else "sin_apoyo"),
                 "parcial_por_tamano": clase == "parcial" and len(z["acuerdan_en_signo"]) >= 2,
                 "crecimiento_prima_L05": r(g_l05, 4), "crecimiento_prima_anual": r(g_anual, 4),
                 "siniestralidad_por_anio": {k: r(v, 3) for k, v in z["ratio_siniestralidad"].items()},
                 "siniestralidad_2025": {k: r(v, 3) for k, v in z["ratio_siniestralidad_2025"].items()},
                 "crecimiento_coste_S30": r(z["crec_coste_implicito_24_25"]["S30"], 4),
                 "crecimiento_coste_S42": r(z["crec_coste_implicito_24_25"]["S42"], 4)}
    T = res42["tabla_reserva_caso"]
    niv42 = [abs(v) for l in RAMOS for k in ("niveles_b_075", "niveles_b_125") for v in T[l]["S42_principal"][k].values()]
    reservas = {"umbral_b_S30": {l: T[l]["S30"]["umbral_b"] for l in RAMOS},
                "umbral_b_S42": {l: [r(x, 3) for x in T[l]["S42_principal"]["umbral_b_sistema"]] for l in RAMOS},
                "clase_S42": {l: T[l]["S42_principal"]["clase_beta_sistema"] for l in RAMOS},
                "clase_S42_sigma_ampliada": {l: T[l]["S42_sigma_ampliada"]["clase_beta_sistema"] for l in RAMOS},
                "nivel_max_b_075_125_S42": r(max(niv42), 4),
                "nivel_max_b_075_125_S30": r(max(abs(v) for l in RAMOS for v in T[l]["S30"]["nivel_b_075_125"]), 4),
                "ibnr_lesiones_S3": {"S30": res42["ibnr_lesiones_S3"]["S30"]["nivel_autos"], "S42": res42["ibnr_lesiones_S3"]["principal"]["nivel_autos"],
                                     "S42_intervalo": [r(x, 5) for x in res42["ibnr_lesiones_S3"]["principal"]["ic"]],
                                     "S42_sigma_ampliada": res42["ibnr_lesiones_S3"]["variante_sigma_ampliada"]["nivel_autos"]},
                "fuente": "privado/corridas/repro_s42_20261022T170245Z_c9ea2fc3 (CLA-20261022-005); docs/archivo/semana1/RESERVAS_ACOTACION.md, «Qué cambia con S42»"}
    p1 = recibo42["parte1_paso_de_nivel"]
    reproduccion = {"raices": len(p1["corridas"]), "csv": len([k for k in p1["ocho_csv"] if k != "iguales_en_R0_R1_R2"]),
                    "iguales": p1["ocho_csv"]["iguales_en_R0_R1_R2"], "clase": sorted(set(p1["clase_preinscrita"].values())),
                    "dif_relativa_max_notas": max(v["dif_relativa_max"] for v in p1["notas"].values()),
                    "forma_cerrada": {k: {"esperado": r(v["esperado_forma_cerrada"], 8), "kaggle": v["kaggle"]} for k, v in p1["forma_cerrada_frente_a_kaggle"].items()}}
    redondeo = {}
    for l in RAMOS:
        z = cal["ramos"][l]
        lo, hi = rango_c_optimo_por_redondeo(z["publico_x090"], cal["publico_modelo"], z["publico_x110"])
        redondeo[l] = {"c_optimo_min": r(lo, 6), "c_optimo_max": r(hi, 6), "semiancho_relativo": r((hi - lo) / 2 / z["c_optimo"], 4)}
    return {"criterio": "L05 de sens42_20261022T165934Z_6ec8f1fe, publicado en docs/archivo/semana1/SENSIBILIDAD_S43.md: apoyado con dos señales del mismo signo que el ajuste y tamaño dentro de la mayor más la τ de D100; parcial con una, o con dos o más y tamaño fuera; sin apoyo con ninguna",
            "estado": "L05 publicado (D103)", "ramos": ev,
            "condicion_prima": {"hallazgo": "DATA-006", "supuesto": "la señal (c) usa la prima escrita; su unidad (tarifa anual o importe del periodo) no está confirmada por el diccionario",
                                "lectura": "la clasificación es la misma con las dos lecturas de la prima"},
            "reservas_S42": reservas, "reproduccion_S42": reproduccion, "redondeo_c_optimo": redondeo,
            "optimo_publico_autos_frente_S30": r(cal["ramos"]["motor"]["c_optimo"] - 1, 4)}


def bloque_reservas_s41(res41, recibo41, dec41, cal):
    """Reservas con la regla de S41 (corrida repro_s41, CLA-20261023-005): cada escenario b o k pasa por la regla de D100
    con Z fija, así que el nivel de S41 se mueve cerca de (1 − Z)/c veces lo que el de la mezcla y los ramos no se acoplan.
    Con la materialidad del 1 % del participante. Añade la extracción de S41 del paso de nivel repetido en las tres raíces
    de repro_s42 y la decisión del participante de mantener para S41 la limitación de reservas del 20 de octubre."""
    T, regla = res41["tabla"], res41["regla"]
    for l in RAMOS:  # la regla de la corrida es la de la entrega final
        assert abs(regla["factores_S41"][l] - cal["ramos"][l]["c_S41"]) < 5e-5, l
    umbral = {l: [r(x, 3) for x in T[l]["umbral_b_S41"]] for l in RAMOS}
    error = {l: r(min(1 - T[l]["umbral_b_S41"][0], T[l]["umbral_b_S41"][1] - 1), 4) for l in RAMOS}
    niveles = {l: [r(T[l]["nivel_S41_b075"], 4), r(T[l]["nivel_S41_b125"], 4)] for l in RAMOS}
    s3 = T["motor"]["S3"]["bodily_injury"]
    bi, sub = T["motor"]["peligro_largo"], T["buildings"]["peligro_largo"]
    p1 = recibo41["parte1_paso_de_nivel"]
    campos = [int(re.match(r"(\d+)", v).group(1)) for v in p1["notas_D100"].values()]
    total_campos = int(re.search(r"de (\d+)", next(iter(p1["notas_D100"].values()))).group(1))
    difs = [float(re.search(r"([\d,]+e-\d+)", v).group(1).replace(",", ".")) for v in p1["notas_D100"].values()]
    agg = res41["coste_D2_publico"]["agregado_tres_ramos"]
    return {"sensibilidad_1_menos_Z_sobre_c": {l: r(res41["sensibilidad_primer_orden_(1-Z)/c"][l], 3) for l in RAMOS},
            "umbral_b_S41": umbral, "umbral_b_mezcla": {l: T[l]["umbral_b_S30"] for l in RAMOS},
            "error_material_S41": error, "nivel_b_075_125_S41": niveles,
            "nivel_max_b_075_125_S41": r(max(abs(v) for x in niveles.values() for v in x), 4),
            "clase": {l: T[l]["clase"] for l in RAMOS},
            "ramos_con_incertidumbre_material": sum(T[l]["clase"] == "incertidumbre_material" for l in RAMOS),
            "ic90_beta": {l: T[l]["ic90_beta"] for l in RAMOS},
            "lesiones": {"umbral_b": [r(x, 3) for x in bi["umbral_b"]], "ic90_beta": bi["ic90"], "clase": bi["clase"]},
            "hundimiento": {"umbral_b": [r(x, 3) for x in sub["umbral_b"]], "ic90_beta": sub["ic90"], "clase": sub["clase"],
                            "umbral_b_sigma_ampliada": [r(x, 3) for x in T["buildings"]["variante_sigma_ampliada"]["peligro_largo"]["umbral_b"]],
                            "clase_sigma_ampliada": T["buildings"]["variante_sigma_ampliada"]["peligro_largo"]["clase"]},
            "S3_autos": {"nivel": r(s3["nivel_S41_con_k"], 5), "nivel_ic90": [r(x, 5) for x in s3["nivel_S41_con_ic90_k"]],
                         "umbral_k": [r(x, 3) for x in s3["umbral_k"]], "clase": s3["clase"]},
            "sigma_ampliada": {"Z": {l: r(T[l]["variante_sigma_ampliada"]["Z"], 3) for l in RAMOS},
                               "umbral_b": {l: [r(x, 3) for x in T[l]["variante_sigma_ampliada"]["umbral_b"]] for l in RAMOS},
                               "clase": {l: T[l]["variante_sigma_ampliada"]["clase"] for l in RAMOS}},
            "coste_D2_publico_1pct": {"bajando": r(agg["S41_menos_1pct"], 7), "subiendo": r(agg["S41_mas_1pct"], 7)},
            "reproduccion": {"raices": len(p1["raices"]), "csv_igual_en": p1["S41"]["igual_en"], "sha256": p1["S41"]["sha256"],
                             "campos_identicos": campos, "campos": total_campos, "dif_relativa_max": max(difs),
                             "clase": p1["clase_preinscrita"]},
            "decision": {"id": dec41["id"], "respuesta": dec41["respuesta_literal"], "utc": dec41["utc_registro"],
                         "alcance": dec41["alcance"]},
            "lectura": res41["lectura"],
            "fuente": "privado/corridas/repro_s41_20261023T145808Z_c8055dfc (CLA-20261023-005); docs/archivo/semana1/RESERVAS_ACOTACION.md, «Qué cambia con S41»; "
                      "registro/decision_reservas_S41_20261023.json (CLA-20261023-006)"}


def bloque_calibracion_forma(pre, res, recibos, envio43, n01):
    """Calibración de la forma 2025 por ramo con el marcador (D102): un exponente por ramo sobre S42.

    Con r = μ/e y g = Σμ/Σe del ramo, r' = g·(r/g)^a, renivelado al total del ramo: a < 1 comprime las diferencias de tasa
    y a > 1 las amplía, sin tocar el nivel. Cerca del óptimo el público es casi una parábola en a: con los públicos de
    a = 0,90, 1,00 (S42) y 1,10, D²(a) − D²(1) = α·(a − 1) + β·(a − 1)², vértice a* = 1 − α/(2β), curvatura K = −β.
    Regla fijada antes de puntuar las sondas: a_Z = 1 + Z·(a* − 1), Z = τ²/(τ² + σ²) con τ = 0,05."""
    P, R = pre["preinscrito"], res["resolucion"]
    d0 = R["s42_publico"]
    ramos = {}
    for l in RAMOS:
        q = R["ramos"][l]
        p90, p110 = q["publico_a090"], q["publico_a110"]
        alfa, beta = (p110 - p90) / 0.2, (p90 + p110 - 2 * d0) / 0.02
        a_opt = 1 - alfa / (2 * beta)
        assert abs(a_opt - q["a_optimo_publico"]) < 1e-9 and abs(a_opt - n01["N01"]["ramos"][l]["a_optimo"]) < 1e-9
        curva = [[round(0.86 + k * 0.005, 3), r(d0 + alfa * (0.86 + k * 0.005 - 1) + beta * (0.86 + k * 0.005 - 1) ** 2, 6)] for k in range(57)]
        ramos[l] = {"publico_a090": p90, "publico_a110": p110, "alfa": r(alfa, 6), "beta": r(beta, 6),
                    "K_publico": r(-beta, 4), "K_2024": r(P["K_2024"][l], 4), "a_optimo": r(a_opt, 3),
                    "a_optimo_2024_relativo_S30": P["a_optimo_2024_relativo_a_S30"][l],
                    "sigma_ruido": r(P["sigma_ruido_33pct_bootstrap_2024"][l], 4), "tau": P["tau_previa"][l],
                    "Z": r(q["Z"], 3), "a_Z": r(q["a_Z"], 3), "a_Z_completo": q["a_Z"],
                    "ganancia_publico": r(q["ganancia_publico_esperada_en_a_Z"], 6),
                    "privado_frente_S42": [r(q["privado_esperado_si_2025_igual_2024"], 8), r(q["privado_esperado_si_tau_previa"], 8)],
                    "curva": curva}
    sondas = []
    for x in recibos["receipts"]:
        partes = x["id"].split("_")  # S50_sonda_forma_<ramo>_a090
        sondas.append({"id": x["id"], "ramo": partes[3], "a": int(partes[4][1:]) / 100, "publico": x["public_score"],
                       "envio_kaggle": x["kaggle_submission_id"], "sha256": x["sha256"]})
    assert len(sondas) == 6
    return {"publico_S42": d0, "sondas": 6, "exponentes_sonda": [0.9, 1.1], "tau": P["tau_previa"]["motor"],
            "transformacion": "r' = g·(r/g)^a con r = μ/e y g = Σμ/Σe del ramo; renivelado al total del ramo",
            "regla": "a* = vértice de la parábola por a = 0,90, 1,00 y 1,10; a_Z = 1 + Z·(a* − 1), Z = τ²/(τ² + σ²), τ = 0,05; S43 si su público ≥ el de S42; nunca una sonda",
            "preinscripcion_utc": pre["fecha_utc"], "sondas_detalle": sondas,
            "S43": {"esperado": r(R["D2_publico_esperado_S43"], 7), "kaggle": envio43["public_score"], "envio_kaggle": envio43["kaggle_submission_id"],
                    "diferencia": r(envio43["public_score"] - R["D2_publico_esperado_S43"], 8),
                    "privado_frente_S42": [r(R["privado_esperado_S43"]["si_2025_igual_2024"], 8), r(R["privado_esperado_S43"]["si_tau_previa"], 8)],
                    "sha256_csv": R["S43"]["sha256"], "regeneracion_identica": bool(n01["N01"]["sha_coincide"])},
            "ramos": ramos,
            # N02 de sens43: rango de a_Z si cada puntuación del ramo se mueve ±0,000005 (el redondeo de Kaggle); no es un intervalo.
            "redondeo_a_Z": {l: [r(n01["N02"][l]["a_Z_min"], 4), r(n01["N02"][l]["a_Z_max"], 4)] for l in RAMOS},
            "nota": "Las sondas S50 son diagnósticas y nunca se seleccionan; la de autos a = 0,90 puntuó más que S43 y la regla la excluye."}


def bloque_sensibilidad_final(l03, l04, l05, n03, n05, n06, rob, informe_rel):
    """Baterías de sensibilidad de la entrega final (sens42 para el nivel, sens43 para la forma; D103), con planes
    fijados antes de calcular. Corrigen el ruido de los óptimos públicos (medido antes frente a todo 2024, que contiene
    la muestra; frente al 67 % no visto es 1/0,67 veces mayor) y comparan S41, S42 y S43 en esperanza en el privado
    bajo tres pares de previas, con una regla de alarma escrita en el plan."""
    pares = (("P1_F1", "reglas de D100 y D102", "rules of D100 and D102"), ("P2_F2", "Bayes empírico corregido", "corrected empirical Bayes"),
             ("P3_F3", "previas sin marcador", "priors without the leaderboard"))
    esperanzas = []
    for k, es, en in pares:
        q = n05["pares"][k]
        fila = {"par": k, "nombre_es": es, "nombre_en": en}
        for c in ("S41", "S42", "S43"):
            fila[c] = {"media": r(q["frente_a_S30"][c]["media"], 8), "sd": r(q["frente_a_S30"][c]["sd"], 8)}
        fila["S43_menos_S41"] = {"media": r(q["S43_menos_S41"]["media"], 8), "sd": r(q["S43_menos_S41"]["sd"], 8),
                                 "P_S43_mejor": r(q["S43_menos_S41"]["P_mejor"], 2)}
        fila["S43_menos_S42"] = {"media": r(q["S43_menos_S42"]["media"], 8)}
        esperanzas.append(fila)
    # Particiones por filas (las variantes por clientes cambian la dispersión menos de un 6 %, sin tocar la conclusión)
    cocientes = [v for k, c in l03["corridas"].items() if k.startswith("fila") for v in c["cociente"].values()] + \
                [v for k, c in n03["N03"]["corridas"].items() if k.startswith("fila") for v in c["cociente"].values()]
    ev_nivel = {}
    for l in RAMOS:
        z = l05["ramos"][l]
        ev_nivel[l] = {"indicadores": {k: r(v, 4) for k, v in z["indicadores"].items()}, "ajuste_S42": r(z["ajuste_S42"], 4),
                       "ajuste_S41": r(z["ajuste_S41"], 4), "clase": z["clasificacion"], "coinciden": z["acuerdan_en_signo"],
                       "tope": r(z["magnitud_max_que_acuerda"] + z["tau_D100"], 4), "crec_prima_24_25": r(z["crec_prima_24_25"], 4),
                       "parcial_por_tamano": z["clasificacion"] == "parcial" and len(z["acuerdan_en_signo"]) >= 2}
    ev_forma = {l: {"indicadores": {k: r(v, 4) for k, v in n06["N06"][l]["indicadores"].items()}, "ajuste_S43": r(n06["N06"][l]["ajuste_S43"], 4),
                    "clase": n06["N06"][l]["clasificacion"]} for l in RAMOS}
    al = l04["alarma"]
    return {"informe": informe_rel, "baterias": ["sens42_20261022T165934Z_6ec8f1fe", "sens43_20261023T035154Z_aece6462"], "decision": "D103",
            "ruido": {"cociente_min": r(min(cocientes), 4), "cociente_max": r(max(cocientes), 4), "teorico": r(1 / 0.67, 4),
                      "sigma_nivel_D100": {l: r(l04["entradas"]["sigma_D100"][l], 4) for l in RAMOS},
                      "sigma_nivel_corregida": {l: r(l03["resumen_fila"]["sigma_pub_corregida"][l], 4) for l in RAMOS},
                      "Z_nivel_D100_corregida": {l: r(l04["previas"]["P1_D100"]["Z"][l], 3) for l in RAMOS},
                      "Z_forma_D102_corregida": {l: r(n05["pares"]["P1_F1"]["Z_forma"][l], 3) for l in RAMOS},
                      "sigma_forma_corregida": {l: r(n05["entradas"]["sigma_pub_forma"][l], 4) for l in RAMOS}},
            "esperanza_privado": esperanzas,
            "alarma_S41_frente_S43": {"media": r(-n06["promedios_pares"]["S43_menos_S41"], 10), "umbral": 0.00003,
                                      "margen": r(n06["alarma_margen_sobre_umbral"], 8), "cumplida": True,
                                      "sin_corregir_ruido": r(rob["sin_corregir_ruido"]["media"], 8),
                                      "redondeo_fraccion": r(rob["redondeo"]["fraccion_con_alarma"], 4),
                                      "posterior_conjunta": r(rob["posterior_conjunta_nivel_forma"]["media"], 8)},
            "alarma_S41_frente_S42": {"media": r(al["c_media_dif_S41_menos_S42"], 10), "cumplida": bool(al["hallazgo_fuerte"])},
            "evidencia_nivel_L05": ev_nivel, "evidencia_forma_N06": ev_forma,
            "retroprueba_forma_N07": {"V23": r(n06["N07"]["V23"]["agregado"], 6), "V24": r(n06["N07"]["V24"]["agregado"], 6),
                                      "V23_autos": r(n06["N07"]["V23"]["por_ramo"]["motor"], 6), "V24_autos": r(n06["N07"]["V24"]["por_ramo"]["motor"], 6)},
            "criterio": "Planes preinscritos de sens42 y sens43: «apoyado» si al menos dos señales sin marcador coinciden en signo con el ajuste y su tamaño no supera la mayor más τ; «parcial» con una (o con dos o más y tamaño fuera); «sin apoyo» con ninguna. Alarma: un candidato enviado supera a la marca en esperanza bajo al menos dos pares de previas, con media ≥ 0,00003, y no pierde frente a S30 bajo ninguno."}


def bloque_entrega_final(reg, recibos, envio43, concurso, s30, cal, forma, ent42, expo25, ent41=None, marca41=None):
    """La entrega final de la parte 1: el candidato con selected_final en el registro de envíos (S43 desde CIE-D102).
    S41 y S42 son S30 con tres factores de nivel; S43 es S42 con el exponente de forma por ramo."""
    sel = [x for x in reg["candidates"] if x.get("selected_final")]
    assert len(sel) == 1, f"selección final ambigua: {[x['id'] for x in sel]}"
    sel = sel[0]
    codigo = sel["id"].split("_")[0]
    rec = {x["code"]: x for x in recibos["receipts"]}
    rec["S43"] = envio43
    r_ = rec[codigo]
    if codigo == "S43":
        nivel = {l: r(ent42["factores_nivel"][l], 4) for l in RAMOS}
        forma_f = {l: forma["ramos"][l]["a_Z"] for l in RAMOS}
        sha, filas, total, por_ramo = envio43["sha256"], envio43["rows"], ent42["total_CU"], ent42["por_ramo_CU"]
        decision = "D102 (CIE-D102)"
    elif codigo == "S42":
        nivel = {l: r(ent42["factores_nivel"][l], 4) for l in RAMOS}
        forma_f = {l: 1.0 for l in RAMOS}
        sha, filas, total, por_ramo = ent42["sha256"], ent42["filas"], ent42["total_CU"], ent42["por_ramo_CU"]
        decision = "D101 (CIE-D101)"
    else:
        assert ent41 and ent41["sha256"] == r_["sha256"] and ent41["pasa"], "falta el recibo de regenerar_s41.py"
        nivel = {l: r(ent41["factores_nivel"][l], 4) for l in RAMOS}
        forma_f = {l: 1.0 for l in RAMOS}
        sha, filas, total, por_ramo = ent41["sha256"], ent41["filas"], ent41["total_CU"], ent41["por_ramo_CU"]
        decision = "D100 (CIE-D103-20261023)"
    return {"id": sel["id"], "codigo": codigo, "publico": r_["public_score"], "envio_kaggle": r_["kaggle_submission_id"],
            "publico_esperado": r(r_["expected_public_score"], 7), "sha256_csv": sha, "filas": filas,
            "total_2025_CU": total, "por_ramo_2025_CU": por_ramo,
            "tasa_2025_por_anio_exposicion": {l: r(por_ramo[l] / expo25[l], 1) for l in RAMOS},
            "factores_calibracion": nivel, "factores_forma": forma_f,
            "factores_nivel_final": ({l: cal["ramos"][l]["f_final"] for l in RAMOS} if codigo in ("S42", "S43") else
                                     {l: cal["ramos"][l]["f_final_S41"] for l in RAMOS}),
            "parametros": 6 if codigo == "S43" else 3,
            "base_S30": {"sha256": s30["sha256_csv"], "publico": s30["publico"], "envio_kaggle": s30["envio_kaggle"]},
            "S41": {"publico": rec["S41"]["public_score"], "envio_kaggle": rec["S41"]["kaggle_submission_id"], "publico_esperado": r(rec["S41"]["expected_public_score"], 7)},
            "S42": {"publico": rec["S42"]["public_score"], "envio_kaggle": rec["S42"]["kaggle_submission_id"], "publico_esperado": r(rec["S42"]["expected_public_score"], 7),
                    "sha256_csv": ent42["sha256"], "controles_csv": ent42["checks"], "regeneracion_identica": ent42["regeneracion"]["igual_al_entregado"]},
            "regeneracion_identica": (forma["S43"]["regeneracion_identica"] if codigo == "S43" else
                                      ent42["regeneracion"]["igual_al_entregado"] if codigo == "S42" else ent41["regeneracion"]["igual_al_entregado"]),
            "controles_csv": (ent41["checks"] if codigo == "S41" else ent42["checks"] if codigo == "S42" else None),
            "herramienta_regeneracion": ("herramientas/regenerar_s41.py" if codigo == "S41" else "herramientas/regenerar_s42.py" if codigo == "S42"
                                         else "herramientas/sonda_forma.py"),
            "marca": ({"registro": marca41["id"], "utc": marca41["utc"], "sustituye": marca41["sustituye_a"]["id"]} if codigo == "S41" and marca41 else None),
            "seleccion_final_manual": True, "decision": decision,
            "puesto_publico": concurso["competition"]["user_rank"], "equipos": concurso["competition"]["team_count"],
            "lider_publico": float(concurso["leader_score"]), "mejor_publico_equipo": float(concurso["best"]["public_score"]),
            "mejor_publico_es_sonda": "S50" in (concurso["best"].get("description") or ""),
            "consulta_utc": concurso["checked"], "envios_totales": concurso["counts"]["lifetime"]}


def bloque_comprobaciones_s43(rec43, res43, csv2, forma):
    """Comprobaciones de S43 posteriores al envío. (1) El script registrado del paso de forma, sin cambios, sobre los
    productos del reajuste completo y de la réplica congelada (corrida repro_s43): S43 sale byte a byte en las tres
    raíces; una de las seis sondas difiere en una fila en el sexto decimal (punto medio del redondeo). (2) Reservas con
    la regla de forma de S43: un escenario es material si cambia el exponente aplicado con K_2024·Δa² ≥ 0,00003, la
    materialidad que fijó el participante antes de calcular. (3) Los controles del CSV que el segundo asistente hizo con
    código propio (formato, orden y cobertura, valores, totales por ramo y reconstrucción byte a byte desde S42)."""
    p1 = rec43["parte1_paso_de_forma"]
    sd = p1["sonda_distinta"]
    clas = res43["clasificacion"]
    c43 = [c for c in csv2["checks"] if c["candidate"] == "S43_forma_credibilidad"]
    assert len(c43) == 1 and c43[0]["sha256"] == forma["S43"]["sha256_csv"]
    c43 = c43[0]
    claves = ("hash_match", "schema_ok", "sample_IDs_same_order", "unique_IDs", "test_full_coverage", "finite", "positive",
              "rounded_total_matches_metadata", "exact_byte_reconstruction")
    lineas_ok = all(v["preserved_within_row_rounding_bound"] for v in c43["per_line"].values())
    return {"reproduccion": {"raices": len(p1["raices"]), "S43_igual_en": p1["S43"]["igual_en"], "sondas_iguales": 5, "sondas": 6,
                             "sonda_distinta": {"archivo": sd["archivo"], "filas_distintas": sd["filas_distintas"]},
                             "clase_preinscrita": p1["clase_preinscrita"], "lectura_posterior": p1["lectura_posterior_declarada"],
                             "fuente": rec43["corrida"]},
            "reservas_forma": {"materialidad_D2": 0.00003,
                               "umbral_delta_a": {l: r(res43["umbral_delta_a"][l], 3) for l in RAMOS},
                               "clase": {l: clas[l]["clase"] for l in RAMOS},
                               "mayor_coste_ic90": {l: r(clas[l]["max_coste_en_ic90"], 10) for l in RAMOS},
                               "mayor_coste_ic90_max": r(max(clas[l]["max_coste_en_ic90"] for l in RAMOS), 8),
                               "a_Z_autos_ruido_corregido": r(res43["ruido_corregido"]["motor"]["sigma_N03_sens43"]["a_Z"], 3),
                               "nivel": "el de S42; su acotación vale sin cambios"},
            "csv_segundo_asistente": {"controles": {k: bool(c43[k]) for k in claves}, "filas": c43["rows"], "totales_por_ramo": lineas_ok,
                                      "todos": all(bool(c43[k]) for k in claves) and lineas_ok and c43["rows"] == 626639,
                                      "utc": csv2["utc"]}}


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


def bloque_foro(datos: bytes, hasta: str = CORTE_FORO):
    txt = datos.decode("utf-8")
    todos = list(re.finditer(r"^## (Codex|Claude|Participante) \| ([A-Z]{3}[^|]*?) \| ([0-9T:\-+.]+) \| (.*)$", txt, re.M))
    i_corte = next(i for i, m in enumerate(todos) if m.group(2).strip() == hasta)
    fin = todos[i_corte + 1].start() if i_corte + 1 < len(todos) else len(txt)
    prefijo = (txt[:fin].rstrip("\n") + "\n").encode("utf-8")  # el foro tal como quedó tras el aporte de corte
    cab = [m.groups() for m in todos[:i_corte + 1]]
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
            "corte": {"hasta_aporte": hasta, "utc": cab[-1][2], "bytes": len(prefijo), "sha256": hashlib.sha256(prefijo).hexdigest(),
                      "aportes_posteriores_al_extraer": len(todos) - i_corte - 1,
                      "regla": "Se cuentan los aportes hasta el registro de la selección final de la parte 1; el foro solo crece por el final, "
                               "así que los posteriores no cambian estas cifras mientras la huella de esa parte se mantenga."},
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
    # El registro de hallazgos del último ciclo del enjambre: su ruta la da ultimo_ciclo.json y cambia con cada ciclo.
    rel_registro = leer(rutas["ciclo_validacion"]).get("findings_registry")
    if rel_registro:
        rutas["hallazgos_ciclo"] = raiz / rel_registro
    faltan = [k for k, p in rutas.items() if not p.is_file()]
    if faltan:
        raise SystemExit(f"Faltan fuentes: {faltan}")
    fuentes = {k: {"ruta": FUENTES.get(k, rel_registro), "sha256": sha(p), "bytes": p.stat().st_size} for k, p in rutas.items()}
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
    # Hallazgos que el último ciclo abrió después de la copia del repositorio (docs/evidencia/hallazgos.json): se añaden
    # con el estado del registro del ciclo, sin tocar los demás.
    ids_repo = {h["id"] for h in hall}
    reg_ciclo = leer(rutas["hallazgos_ciclo"]) if "hallazgos_ciclo" in rutas else {"findings": []}
    for f in reg_ciclo.get("findings", []):
        if f["id"] not in ids_repo:
            hall.append({"id": f["id"], "area": f["area"], "severidad": f["severidad"], "estado_registro_recibido": f["estado"],
                         "revisor_necesario": f.get("especialista_humano_requerido_por_designar") or f.get("revisor_necesario"),
                         "origen": f"registro del ciclo {reg_ciclo.get('run_id')}"})
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
        "foro": bloque_foro(rutas["foro"].read_bytes()),
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
    # Calibración del nivel 2025 con el marcador público (D100, D101) y entrega final S42: dependen de los bloques anteriores.
    cal = bloque_calibracion(leer(rutas["sonda_preinscripcion"]), leer(rutas["sonda_resolucion"]), leer(rutas["sonda_revision"]),
                             datos["s30"], datos["sensibilidad"], leer(rutas["prima_escrita"]), datos["ibnr"]["prima_riesgo_por_anio"])
    datos["calibracion_nivel"] = cal
    forma = bloque_calibracion_forma(leer(rutas["forma_preinscripcion"]), leer(rutas["forma_resolucion"]), leer(rutas["forma_recibos"]),
                                     leer(rutas["envio_s43"]), leer(rutas["sens_n01"]))
    datos["calibracion_forma"] = forma
    prima25 = leer(rutas["prima_escrita"])
    expo25 = {l: prima25["ramos"][l]["por_anio"]["2025"]["exposicion"] for l in RAMOS}
    datos["entrega_final"] = bloque_entrega_final(reg, leer(rutas["envios_s41_s42"]), leer(rutas["envio_s43"]), leer(rutas["concurso_final"]),
                                                  datos["s30"], cal, forma, leer(rutas["entrega_final"]), expo25,
                                                  leer(rutas["entrega_final_s41"]), leer(rutas["decision_marca_s41"]))
    forma["comprobaciones_S43"] = bloque_comprobaciones_s43(leer(rutas["recibo_repro_s43"]), leer(rutas["reservas_s43"]),
                                                            leer(rutas["csv_s43_segundo_asistente"]), forma)
    datos["sensibilidad_final"] = bloque_sensibilidad_final(leer(rutas["sens_l03"]), leer(rutas["sens_l04"]), leer(rutas["sens_l05"]),
                                                            leer(rutas["sens_n03"]), leer(rutas["sens_n05"]), leer(rutas["sens_n06"]),
                                                            leer(rutas["sens_robustez"]), FUENTES["sensibilidad_s43_informe"])
    for q in datos["ibnr"]["prima_riesgo_por_anio"]:
        if q["anio"] == 2025:
            q["prediccion_final"] = datos["entrega_final"]["tasa_2025_por_anio_exposicion"][q["ramo"]]
    cal["evidencia"] = bloque_evidencia_nivel(cal, datos["entrega_final"], leer(rutas["prima_escrita"]), datos["s30"], datos["sensibilidad"],
                                              leer(rutas["sonda_preinscripcion"]), leer(rutas["reservas_s42"]), leer(rutas["recibo_repro_s42"]),
                                              leer(rutas["sens_l05"]))
    cal["evidencia"]["reservas_S41"] = bloque_reservas_s41(leer(rutas["reservas_s41"]), leer(rutas["recibo_repro_s41"]),
                                                           leer(rutas["decision_reservas_s41"]), cal)
    # D99 conserva su registro del 20 de octubre (selección manual pendiente entonces); la selección posterior se anota aparte.
    ef = datos["entrega_final"]
    datos["modelo_definitivo"]["seleccion_final_posterior"] = {"entrega": ef["codigo"], "seleccion_final_manual": ef["seleccion_final_manual"],
                                                              "decision": ef["decision"]}
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"salida": str(a.salida), "fuentes": len(fuentes), "d2_v24": pred["d2"]["V24"]["agregado"],
                      "aportes_foro": datos["foro"]["aportes"], "envios": len(datos["envios"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
