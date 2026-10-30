"""Rebuild prepared data, actuarial bases and F0 from 11 original Parquet files.

Create a minimal project tree under <work>/proyecto, including RUTAS_PROYECTO.json,
the prepared-data catalog, verification records and the expected Week 1 runtime
directories. Run the N62 preparation, bases_actuariales.py and construir_f0.py
in that isolated tree. Link the newly generated runs under the names consumed
by comun.py and verify each step against receta/huellas_esperadas.json.

The notebook adaptation reconstructs audit-only flags without copying restricted
decision ledgers. Return the generated Week 1 directory for the model stages.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "herramientas"))
from huella import huellas  # noqa: E402

PREAUDIT = "preaudit_20261016T211816Z_817285a5"
F0_NOMBRE = "f0_20261017T141732Z_65df7fca"
BASES_NOMBRE = "bases_20261017T120251Z_45443ff0"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def correr(cmd, cwd, log: Path):
    with open(log, "a", encoding="utf-8") as f:
        f.write("# " + " ".join(map(str, cmd)) + "\n")
        f.flush()
        rc = subprocess.run([str(c) for c in cmd], cwd=str(cwd), stdout=f, stderr=subprocess.STDOUT).returncode
    if rc:
        raise SystemExit(f"Falló {' '.join(map(str, cmd[1:3]))}; ver {log}")


def copiar_script(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
    if sha(dst) != sha(src):
        raise SystemExit(f"La copia de {src.name} en la raíz mínima no coincide con la del repositorio")
    return dst


def preparar_datos(originales: Path, decisiones: Path, trabajo: Path) -> tuple[Path, dict]:
    esp = json.loads((REPO / "receta" / "huellas_esperadas.json").read_text(encoding="utf-8"))["datos"]
    root = trabajo / "proyecto"
    s1 = root / "Hackaton" / "Semana 1"
    logs = trabajo / "registros"
    logs.mkdir(parents=True, exist_ok=True)
    s1.mkdir(parents=True, exist_ok=True)
    (root / "RUTAS_PROYECTO.json").write_text("{}\n", encoding="utf-8")
    informe = {}

    # Stage 00: frozen originals and the N62 prepared-data producer.
    malos = [n for n, h in esp["originales"].items() if sha(originales / (n if n.endswith(".parquet") else f"{n}.parquet")) != h]
    if malos:
        raise SystemExit(f"Los originales no tienen el SHA-256 congelado: {malos}")
    capa = s1 / "Limpieza" / "runs" / PREAUDIT
    if not (capa / "COMPLETE.json").exists():
        correr([sys.executable, REPO / "src/datos/n62/rebuild_base.py", "--raw", originales,
                "--rules", REPO / "src/datos/n62/rules.json", "--out", capa], trabajo, logs / "datos_capa.log")
    rel = f"Hackaton/Semana 1/Limpieza/runs/{PREAUDIT}"
    catalogo = {f.stem: {"workspace_relative_path": f"{rel}/data/{f.name}", "sha256": sha(f)} for f in sorted((capa / "data").glob("*.parquet"))}
    informe["capa"] = {n: catalogo.get(n, {}).get("sha256") == h for n, h in esp["capa"].items()}
    if not all(informe["capa"].values()):
        raise SystemExit(f"La capa reconstruida no coincide con preaudit: {informe['capa']}")
    (capa / "dataset_catalog.json").write_text(json.dumps(catalogo, indent=1), encoding="utf-8")
    (capa / "verification.json").write_text(json.dumps({"status": "capa reconstruida por N62 desde los once originales; SHA-256 iguales a preaudit",
                                                        "passed": len(catalogo), "failed": 0}, indent=1), encoding="utf-8")
    (s1 / "Limpieza" / "current_dataset.json").write_text(json.dumps({"workspace_relative_run": rel, "status": "rebuilt_N62_from_originals",
                                                                       "catalog_workspace_relative": f"{rel}/dataset_catalog.json", "approved_for_modeling": False}, indent=1), encoding="utf-8")
    datos = s1 / "Datos"
    if not datos.exists():
        shutil.copytree(capa / "data", datos) if sys.platform == "win32" else datos.symlink_to(capa / "data", target_is_directory=True)

    # Restricted audit ledgers are deliberately not copied into this run.

    # Stage 01: actuarial bases.
    bdir = s1 / "Bases_actuariales"
    script = copiar_script(REPO / "src/datos/bases_actuariales.py", bdir)
    corridas = sorted(p for p in (bdir / "runs").glob("bases_*") if not p.is_symlink() and (p / "manifest.json").exists()) if (bdir / "runs").exists() else []
    if not corridas:
        correr([sys.executable, script], bdir, logs / "datos_bases.log")
        corridas = sorted(p for p in (bdir / "runs").glob("bases_*") if not p.is_symlink() and (p / "manifest.json").exists())
    bases = corridas[-1]
    (bdir / "current_run.json").write_text(json.dumps({"workspace_relative_run": f"Hackaton/Semana 1/Bases_actuariales/runs/{bases.name}"}, indent=1), encoding="utf-8")
    alias = bdir / "runs" / BASES_NOMBRE
    if not alias.exists():
        shutil.copytree(bases, alias) if sys.platform == "win32" else alias.symlink_to(bases.name, target_is_directory=True)
    informe["bases"] = {}
    for relp, e in esp["bases"].items():
        h = huellas(bases / relp)
        informe["bases"][relp] = {"igual_bytes": h["sha256"] == e["sha256"], "igual_contenido": h["contenido"] == e["contenido"]}

    if not all(v["igual_contenido"] for v in informe["bases"].values()):
        raise SystemExit(f"Las bases requeridas difieren en contenido: {informe['bases']}")

    # Stage 02: partitioned F0 matrix.
    fdir = s1 / "Matriz_F0"
    script = copiar_script(REPO / "src/datos/construir_f0.py", fdir)
    corridas = sorted(p for p in (fdir / "runs").glob("f0_*") if not p.is_symlink() and (p / "manifest.json").exists()) if (fdir / "runs").exists() else []
    if not corridas:
        log = logs / "datos_f0.log"
        correr([sys.executable, script, "--ramo", "motor"], fdir, log)
        run_id = next(l.split(":", 1)[1].strip() for l in log.read_text(encoding="utf-8").splitlines() if l.startswith("Corrida creada:"))
        for parte in ("buildings", "contents"):
            correr([sys.executable, script, "--run", run_id, "--ramo", parte], fdir, log)
        correr([sys.executable, script, "--run", run_id, "--finalizar"], fdir, log)
        corridas = [fdir / "runs" / run_id]
    f0 = corridas[-1]
    alias = fdir / "runs" / F0_NOMBRE
    if not alias.exists():
        shutil.copytree(f0, alias) if sys.platform == "win32" else alias.symlink_to(f0.name, target_is_directory=True)
    informe["f0"] = {}
    for relp, e in esp["f0"].items():
        h = huellas(f0 / relp)
        informe["f0"][relp] = {"igual_bytes": h["sha256"] == e["sha256"], "igual_contenido": h["contenido"] == e["contenido"]}
    cols = json.loads((f0 / "contrato_disponibilidad.json").read_text(encoding="utf-8"))["columnas"]
    bloques = hashlib.sha256(json.dumps({l: {c: v["bloque"] for c, v in cc.items()} for l, cc in cols.items()}, sort_keys=True).encode()).hexdigest()
    informe["f0"]["contrato_bloques_iguales"] = bloques == esp["f0_contrato_bloques"]
    if not all(v["igual_contenido"] for k, v in informe["f0"].items() if k != "contrato_bloques_iguales"):
        raise SystemExit(f"Las tablas F0 requeridas difieren en contenido: {informe['f0']}")
    if not informe["f0"]["contrato_bloques_iguales"]:
        raise SystemExit("Los bloques del contrato F0 difieren")
    return s1, informe
