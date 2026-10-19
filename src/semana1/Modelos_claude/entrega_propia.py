"""Nota de entrega y copia verificada de una estimación propia de Claude (sin componentes de Codex).
Uso: python3 entrega_propia.py <corrida> <nombre_envio> <clave> <robustez.json> <cand_en_robustez> <comparar.json> <composicion.json>"""
import hashlib, json, shutil, sys
from datetime import datetime, timezone
import numpy as np, pandas as pd
run, out, key, robf, cand, compf, compj = sys.argv[1:8]
W = "/home/claude/work"; O = "/mnt/user-data/outputs/Envios"
EXPO = {"motor": 199983.6, "buildings": 150243.91, "contents": 150123.77}
rob = json.load(open(f"{W}/{robf}"))["candidatos"][cand]
cmp_ = json.load(open(f"{W}/{compf}"))
comp = json.load(open(compj))
sample = pd.read_parquet("/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Datos/sample_submission.parquet", columns=["row_id"])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
c = lambda v: f"{v:+.5f}".replace(".", ",")
p3 = lambda x: str(round(x, 3)).replace(".", ",")
src = f"{W}/{run}/{run}.csv"; dst = f"{O}/archivos/{out}.csv"
shutil.copyfile(src, dst)
df = pd.read_csv(dst, dtype={"row_id": str})
assert list(df.columns) == ["row_id", "prediction"] and len(df) == 626639 and (df.row_id.values == sample.row_id.values).all()
assert df.prediction.notna().all() and np.isfinite(df.prediction).all() and (df.prediction > 0).all()
rep = json.load(open(f"{W}/{run}/resumen.json"))
assert rep["file"]["sha256"] == sha(dst)
by = rep["file"]["by_line_CU"]
par = {("V23_seleccion" if f == "V23" else f): {k: f"{c(v['dif'])} (P>0 {p3(v['P_mejora'])})" for k, v in rob[f].items()} for f in ("V23", "V24")}
par["sin_el_0_1_por_ciento_superior_V23_V24"] = {k: f"{c(rob['V23'][k]['dif_sin_top01'])} / {c(rob['V24'][k]['dif_sin_top01'])}" for k in rob["V24"]}
tabla = {l: {m: cmp_[l][m]["d2"] for m in ("CL", "AG", "H", "S09b")} for l in ("motor", "buildings", "contents")}
tabla["agregado"] = {m: cmp_["global"][m] for m in ("CL", "AG", "H", "S09b")}
j = {"id": out, "autor": "Claude (Modelos_claude), 18 de octubre", "linaje": "Estimación propia de Claude: ningún componente, total ni factor de Codex (acuerdo del foro, COD-20261018-001 y CLA-20261018-001)",
     "recomendacion": comp["recomendacion"], "archivo": f"Hackaton/Semana 1/Envios/archivos/{out}.csv", "sha256": rep["file"]["sha256"], "filas": 626639,
     "columnas": ["row_id", "prediction"], "total_CU": rep["file"]["total_CU"], "por_ramo_CU": by,
     "tasa_2025_por_unidad_de_exposicion": {l: round(by[l] / EXPO[l], 1) for l in by},
     "composicion": comp["composicion"],
     "validacion": {"d2_v24_global_con_factor_v23": rep["d2_v24_global_f23"], "por_ramo": rep["lines"], "pareada_frente_a_S09b": par,
                    "d2_local_2024_mismos_IDs": {"tabla": tabla, "nota": "CL es esta estimación; A_G y H ajustan su meta con validación cruzada por cliente dentro de 2024, así que su D² local es optimista frente a uno fuera de año"},
                    "limite": "V23 y V24 ya se consultaron para elegir pesos y forma; no es validación nueva"},
     "autorizacion": {"F3_hogar": "D80", "envio": "Lo coordina Codex con autorización del participante; Claude no envía"},
     "controles_claude": ["626.639 filas en el orden de sample_submission", "columnas row_id,prediction", "sin faltantes", f"mínimo {df.prediction.min():.5f} > 0", "SHA-256 recalculado tras la copia"],
     "creado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
txt = json.dumps(j, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
open(f"{O}/{key}_claude_entrega_codex.json", "w", encoding="utf-8", newline="").write(txt)
print(out, rep["file"]["sha256"], j["tasa_2025_por_unidad_de_exposicion"])
print(json.dumps(par, ensure_ascii=False))
print(json.dumps(tabla))
