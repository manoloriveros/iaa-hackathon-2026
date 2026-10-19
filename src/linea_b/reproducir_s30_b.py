"""Repite una mezcla de la línea B (S30, S31) a partir de los archivos guardados en Modelos_claude y Modelos_claude_b.

Igual que Modelos_claude/reproducir_mezcla.py: monta una carpeta de trabajo con enlaces a las corridas de las dos carpetas
(v24.parquet y prediccion_2025.parquet), a los sel_<nombre>.parquet y a las exposiciones de insumos/, aplica la regla de
nivel s17 extendida a las corridas B_ (nivel_b.py, que calcula la desviación 2025/V24 frente al ancla sin etiquetas) y
ejecuta mezcla3.py con la especificación y la forma indicadas; compara el SHA-256 del CSV con el entregado.
Uso: python3 reproducir_s30_b.py <spec_json> <forma> <nombre> <sha256_esperado> [<carpeta_temporal>]
Ejemplo: python3 reproducir_s30_b.py experimentos/spec_s30.json motor:1.09:0.95,contents:1:0.95 S30_claude_b <sha>
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MC = AQUI.parent / "Modelos_claude"
SEMANA1 = AQUI.parent


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def buscar(nombre: str, patron: str) -> Path:
    for base in (AQUI, MC):
        cands = list((base / "runs").glob(patron.format(nombre))) + list((base / "selecciones_v23").glob(patron.format(nombre)) if (base / "selecciones_v23").exists() else [])
        if cands:
            return cands[0]
    raise SystemExit(f"No encuentro {patron.format(nombre)} en runs/ ni selecciones_v23/ de las dos carpetas")


def main():
    spec_path, forma, nombre, esperado = sys.argv[1:5]
    tmp = Path(sys.argv[5]) if len(sys.argv) > 5 else Path(tempfile.mkdtemp(prefix="repro_b_"))
    work = tmp / "work"
    work.mkdir(parents=True, exist_ok=True)
    sp = Path(spec_path) if Path(spec_path).is_absolute() else AQUI / spec_path
    spec = json.loads(sp.read_text(encoding="utf-8"))
    corridas = {"S04b_lgbm_F0124_F3autos"}
    sels = {"total_F0124"}
    for line in spec:
        for run, sel_name, _ in spec[line]:
            corridas.add(run); sels.add(sel_name)
    for run in sorted(corridas):
        d = work / run
        d.mkdir(exist_ok=True)
        for f in ("v24.parquet", "prediccion_2025.parquet"):
            src = next((b / "runs" / run / f for b in (AQUI, MC) if (b / "runs" / run / f).exists()), None)
            if src is None:
                raise SystemExit(f"Falta runs/{run}/{f}")
            if not (d / f).exists():
                (d / f).symlink_to(src)
    for s in sorted(sels):
        dst = work / f"sel_{s}.parquet"
        if not dst.exists():
            dst.symlink_to(buscar(s, "*/sel_{}.parquet") if not (MC / "selecciones_v23" / f"sel_{s}.parquet").exists() else MC / "selecciones_v23" / f"sel_{s}.parquet")
    for line in ("motor", "buildings", "contents"):
        dst = work / f"feat_{line}.parquet"
        if not dst.exists():
            dst.symlink_to(MC / "insumos" / f"exposicion_{line}.parquet")
    env = dict(os.environ, MODELOS_WORK=str(work), HAKATON_SEMANA1=str(SEMANA1), MODELOS_CLAUDE=str(MC))
    # la regla de nivel: mezcla3 lee WORK/nivel_inestable_b.json a través de nivel_b; se clasifica aquí
    cmd = [sys.executable, "-W", "ignore", str(AQUI / "mezcla3_b.py"), nombre, str(sp), f"--forma={forma}", "--nivel=s17", "--escribir"]
    print("Ejecuto:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env, cwd=str(AQUI))
    csv = work / nombre / f"{nombre}.csv"
    obtenido = sha(csv)
    rep = {"nombre": nombre, "sha256_esperado": esperado, "sha256_obtenido": obtenido, "coincide": obtenido == esperado, "carpeta": str(work)}
    if obtenido != esperado:
        import numpy as np
        import pandas as pd
        ref = SEMANA1 / "Envios" / "archivos" / f"{nombre}.csv"
        a = pd.read_csv(csv, dtype={"row_id": str}); r = pd.read_csv(ref, dtype={"row_id": str})
        assert (a.row_id.values == r.row_id.values).all()
        dif = np.abs(a.prediction.values - r.prediction.values)
        rep.update({"referencia": str(ref), "filas_distintas": int((dif > 0).sum()), "dif_max": float(dif.max()),
                    "total_obtenido": round(float(a.prediction.sum()), 2), "total_entregado": round(float(r.prediction.sum()), 2)})
    print(json.dumps(rep, ensure_ascii=False, indent=1), flush=True)
    if obtenido != esperado and rep["dif_max"] > 1.01e-6:
        raise SystemExit("El CSV repetido no coincide con el entregado")


if __name__ == "__main__":
    main()
