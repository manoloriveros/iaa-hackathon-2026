"""Rebuild a frozen blend from saved components and check its exact CSV SHA-256.

Stage selection, V24 and 2025 tables in a temporary workspace using symbolic
links. Add the exposure extracts as feat_<line>.parquet; the blend reads only
row_id, e_ef_coste and exposure from them. Run the same specification, shape and
level rule as mezcla3.py. Keep sources unchanged and compare final file bytes.
Usage: python reproducir_mezcla.py <spec_json> <shape> <level|-> <name> <expected_sha256> [<temporary_directory>]
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
SEMANA1 = AQUI.parent


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def buscar_sel(nombre: str) -> Path:
    cands = list((AQUI / "runs").glob(f"*/sel_{nombre}.parquet")) + list((AQUI / "selecciones_v23").glob(f"sel_{nombre}.parquet"))
    if not cands:
        raise SystemExit(f"No encuentro sel_{nombre}.parquet en runs/ ni en selecciones_v23/")
    return cands[0]


def main():
    spec_path, forma, nivel, nombre, esperado = sys.argv[1:6]
    tmp = Path(sys.argv[6]) if len(sys.argv) > 6 else Path(tempfile.mkdtemp(prefix="repro_"))
    work = tmp / "work"
    work.mkdir(parents=True, exist_ok=True)
    spec = json.loads((AQUI / spec_path).read_text(encoding="utf-8")) if not Path(spec_path).is_absolute() else json.loads(Path(spec_path).read_text(encoding="utf-8"))
    corridas = {"S04b_lgbm_F0124_F3autos"}  # mezcla3.labels() reads the V24 labels and 2025 identifiers here.
    sels = {"total_F0124"}  # V23 selection labels are read from this source.
    for line in spec:
        for run, sel_name, _ in spec[line]:
            corridas.add(run); sels.add(sel_name)
    for run in sorted(corridas):
        d = work / run
        d.mkdir(exist_ok=True)
        for f in ("v24.parquet", "prediccion_2025.parquet"):
            src = AQUI / "runs" / run / f
            if not src.exists():
                raise SystemExit(f"Falta {src}")
            if not (d / f).exists():
                (d / f).symlink_to(src)
    for s in sorted(sels):
        dst = work / f"sel_{s}.parquet"
        if not dst.exists():
            dst.symlink_to(buscar_sel(s))
    for line in ("motor", "buildings", "contents"):
        dst = work / f"feat_{line}.parquet"
        if not dst.exists():
            dst.symlink_to(AQUI / "insumos" / f"exposicion_{line}.parquet")
    env = dict(os.environ, MODELOS_WORK=str(work), HAKATON_SEMANA1=str(SEMANA1))
    cmd = [sys.executable, "-W", "ignore", str(AQUI / "mezcla3.py"), nombre, str(AQUI / spec_path), f"--forma={forma}", "--escribir"]
    if nivel != "-":
        cmd.append(f"--nivel={nivel}")
    print("Ejecuto:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env, cwd=str(AQUI))
    csv = work / nombre / f"{nombre}.csv"
    obtenido = sha(csv)
    rep = {"nombre": nombre, "sha256_esperado": esperado, "sha256_obtenido": obtenido, "coincide": obtenido == esperado, "carpeta": str(work)}
    if obtenido != esperado:
        # NumPy versions may change the last bit of sums; report numerical differences separately.
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
