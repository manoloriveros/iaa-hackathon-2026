"""Nota de entrega de un candidato de la línea B para Envios/, a partir de los archivos de la batería en WORK.
Uso: python3 entrega_b.py <corrida> <nombre_envio> <clave> <spec> <forma>
Escribe /mnt/user-data/outputs/Envios/<nombre_envio>_entrega_codex.json y copia el CSV a /mnt/user-data/outputs/Envios/archivos/.
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

run, out, key, spec_path, forma = sys.argv[1:6]
W = "/home/claude/work"; O = "/mnt/user-data/outputs/Envios"
EXPO = {"motor": 199983.6, "buildings": 150243.91, "contents": 150123.77}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


c = lambda v: f"{v:+.5f}".replace(".", ",")
p3 = lambda x: str(round(x, 3)).replace(".", ",")
import os
os.makedirs(f"{O}/archivos", exist_ok=True)
src = f"{W}/{run}/{run}.csv"; dst = f"{O}/archivos/{out}.csv"
shutil.copyfile(src, dst)
sample = pd.read_parquet("/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Datos/sample_submission.parquet", columns=["row_id"])
df = pd.read_csv(dst, dtype={"row_id": str})
assert list(df.columns) == ["row_id", "prediction"] and len(df) == 626639 and (df.row_id.values == sample.row_id.values).all()
assert df.prediction.notna().all() and np.isfinite(df.prediction).all() and (df.prediction > 0).all()
rep = json.load(open(f"{W}/{run}/resumen.json"))
assert rep["file"]["sha256"] == sha(dst)
by = rep["file"]["by_line_CU"]
rob = json.load(open(f"{W}/rob_s30.json"))["candidatos"]
boot = json.load(open(f"{W}/bootstrap_codex_s30.json"))
pub = json.load(open(f"{W}/publico_simulado_s30.json"))
tab = pd.read_csv(f"{W}/tabla_rob_s30.csv")
infl = json.load(open(f"{W}/influencia_reservas_s30.json")) if os.path.exists(f"{W}/influencia_reservas_s30.json") else None
spec = json.load(open(spec_path))


def fila_rob(cand):
    r = rob[cand]
    return {("V23_seleccion" if f == "V23" else f): {k: f"{c(v['dif'])} (P>0 {p3(v['P_mejora'])})" for k, v in r[f].items()} for f in ("V23", "V24")} | {
        "sin_el_0_1_por_ciento_superior_V23_V24": {k: f"{c(r['V23'][k]['dif_sin_top01'])} / {c(r['V24'][k]['dif_sin_top01'])}" for k in r["V24"]}}


def cuerpo(cand, corte):
    g = tab[(tab.ramo == "global") & (tab.corte == corte) & (tab.cand == cand)].iloc[0]
    return {"d2_completo": round(float(g.d2), 5), "sin_0_5_renivelado": round(float(g["rt0.995"]), 5), "sin_1_renivelado": round(float(g["rt0.99"]), 5)}


nota = {
    "id": out,
    "autor": "Claude, línea B (Modelos_claude_b), 18 de octubre",
    "linaje": "Estimación propia de Claude: ningún componente, total ni factor de Codex (acuerdo del foro, COD-20261018-001 y CLA-20261018-001). Reutiliza las partes guardadas de frecuencia por peligro de Modelos_claude (CFS, FSAP) y los componentes Tweedie de la línea principal; los componentes nuevos son de esta carpeta",
    "recomendacion": "S22 con tres cambios medidos con el mismo criterio (mejorar el completo y el cuerpo en V23 y V24): severidad con tendencia por peligro en autos y edificios (el nivel de severidad de 2025 de cada peligro sale de la serie anual recortada, no de la media 2021-2024; relatividades GLM sin cambios; fuera de la referencia de nivel por la regla s17), y pesos de cuerpo en contenidos (sin la red neuronal, aditivo 0,3, severidad ampliada 0,4, LightGBM 0,3, elasticidad de exposición 0,95). Frente a S22: +0,00016 en V23 y +0,00014 en V24 en el completo, +0,00072 y +0,00020 sin el 0,1 % superior, +0,00075 y +0,00032 en el cuerpo sin el 0,5 % renivelado. Mejora pequeña, consistente en los dos cortes y en los dos criterios, no apoyada en la cola. No usa el clima del año (S31 quedó sin entregar: no mejora el total del ramo).",
    "archivo": f"Hackaton/Semana 1/Envios/archivos/{out}.csv",
    "sha256": rep["file"]["sha256"],
    "filas": 626639,
    "columnas": ["row_id", "prediction"],
    "total_CU": rep["file"]["total_CU"],
    "por_ramo_CU": by,
    "tasa_2025_por_unidad_de_exposicion": {l: round(by[l] / EXPO[l], 1) for l in by},
    "composicion": {
        "motor": "CatBoost Tweedie F01234 sin marketing_segment, cuatro semillas (0,2); CatBoost Poisson por peligro (partes CFS de Modelos_claude: V23 CFS_motor_v23, V24 CFS_motor_s23, 2025 CFS_motor y CFS_motor_s23) con severidad GLM gamma por valor y antigüedad del vehículo y nivel de severidad con tendencia por peligro (B_CFST_motor_tendencia) (0,6); LightGBM F01234 (0,1); LightGBM reducido (0,1). Forma de tasa y exposición 1,09/0,95 como S21 y S22",
        "buildings": "LightGBM F0124 con las siete F3 de D80 y min_data_in_leaf 1000 (S12h_edif_md1000) (0,4); CatBoost Poisson por peligro (CFS_buildings y CFS_buildings_s23) con severidad GLM por capital y sótano y tendencia por peligro (B_CFST_buildings_tendencia) (0,3); frecuencia aditiva por peligro (FSAP_buildings y FSAP2_buildings) con la misma severidad y tendencia (B_FSAST_buildings_tendencia) (0,3). Sin forma",
        "contents": "LightGBM con las siete F3 (S08h_hogar_F3s2) (0,3); modelo aditivo por peligro con severidad modelada (FSA_contents) (0,3); frecuencia aditiva de cuatro semillas con severidad GLM ampliada con covariables físicas (FSAXc4_contents) (0,4). Sin red neuronal. Forma de exposición 0,95 (a = 1)",
        "regla_de_nivel": "mezcla3.py --nivel=s17 extendida a las corridas B_ (nivel_b.py: fuera de la referencia de nivel si el total 2025/V24 se aparta más de un 1,5 % del ancla del ramo, calculado sin etiquetas): fuera B_CFST_motor_tendencia, B_CFST_buildings_tendencia, B_FSAST_buildings_tendencia, FSAXc4_contents; el nivel lo fijan CAT_motor_4s, S12h_edif_md1000, S08h_hogar_F3s2 y FSA_contents, y el factor de año siguiente de D70",
        "spec": spec, "forma": forma},
    "validacion": {"d2_v24_global_con_factor_v23": rep["d2_v24_global_f23"], "por_ramo": rep["lines"],
                   "frente_a_S22": fila_rob("S30"), "frente_a_S21": fila_rob("S21_ref_invertida_ver_nota") if "S21_ref_invertida_ver_nota" in rob else "en rob_s30.json, S21 frente a S22: S30 cede frente a S21 −0,00038 (V23) y −0,00019 (V24) en el completo y gana +0,00272 y +0,00097 sin el 0,1 % superior",
                   "cuerpo_global": {cand: {corte: cuerpo(cand, corte) for corte in ("V23", "V24")} for cand in ("S22", "S30", "S21")},
                   "frente_a_AG_y_H_2024": boot,
                   "reservas_de_caso": infl if infl else "pendiente: influencia_reservas_s30.json"},
    "publico_simulado": {f"{corte} {frac}": {k: v for k, v in d.items() if k.startswith("S30")} for corte, dd in pub.items() for frac, d in dd.items()},
    "criterio_fijado_antes_de_resultados": {
        "regla_de_adopcion": "Un cambio entra solo si mejora el ramo en V23 y en V24 en el D² completo y en el cuerpo (sin el 0,5 % superior, renivelado), o mejora uno sin ceder más de 0,0003 en el otro; fijado en CLB-20261018-001 antes de construir S30",
        "severidad_con_tendencia": "Regresión log-lineal de la serie anual recortada (cuantil 0,999), crecimiento acotado a ±15 %, un año adelante; control pooled reproduce CFSS/FSAS exactamente; en contenidos no entra (−0,0004 frente a la severidad ampliada)",
        "pesos_de_contenidos": "Frontera de Pareto entre la peor mejora del completo y la peor mejora del cuerpo en V23 y V24 (rejilla_cuerpo_b.py); se eligió un punto intermedio, no el extremo de cuerpo",
        "clima_del_anio": "Probado por peligro con variables fijadas de antemano; mejora el peligro en escape de agua y lunas, no el total del ramo (S31 frente a S30: +0,00002 y −0,00005); no se usa",
        "limite": "V23 y V24 entran en la elección; la peor de las dos mejoras en dos criterios limita el sobreajuste a un corte y a la cola, pero no es validación independiente"},
    "autorizacion": {"F3_hogar": "D80", "envio": "Lo coordina Codex con autorización del participante; Claude no envía"},
    "controles_claude": ["626.639 filas en el orden de sample_submission", "columnas row_id,prediction", "sin faltantes", f"mínimo {df.prediction.min():.5f} > 0", "SHA-256 recalculado tras la copia"],
    "predicciones_por_fila_v23_v24": {"archivo": f"Hackaton/Semana 1/Modelos_claude_b/experimentos/predicciones_v23_v24_{key}.parquet",
                                      "sha256": sha(f"{W}/predicciones_v23_v24_{key}.parquet") if os.path.exists(f"{W}/predicciones_v23_v24_{key}.parquet") else "pendiente",
                                      "columnas": ["row_id", "line", "corte", "y_T0", "reserva_caso", "prediction"]},
    "reproduccion": f"En el equipo: python3 reproducir_s30_b.py experimentos/spec_s30.json {forma} {out} {rep['file']['sha256']} (desde Modelos_claude_b, con Modelos_claude al lado; repite la mezcla a partir de las predicciones guardadas de cada componente)",
    "creado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(nota, open(f"{O}/{out}_entrega_codex.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: nota[k] for k in ("id", "sha256", "total_CU", "por_ramo_CU", "tasa_2025_por_unidad_de_exposicion")}, ensure_ascii=False, indent=1))
