"""Pruebas acotadas de identidad, integridad del complemento y recibos. No carga modelos ni llama a sus procesos."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from identidad_captura import identidad_captura
import kit_captura


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    if args.salida.exists():
        parser.error("Conservar el recibo existente; indicar una salida nueva")
    repo = Path(__file__).resolve().parent.parent
    fixtures = args.salida.with_name(args.salida.stem + "_fixtures")
    fixtures.mkdir(parents=True, exist_ok=False)
    cases = []
    identity = identidad_captura(repo)
    cases.append({"id": "identidad_sin_importar_modelos", "conforme": identity["version"] == kit_captura.CAPTURA_VERSION
                  and identity["sha256"] == kit_captura.CAPTURA_SHA})
    base = fixtures / "codigo_base_sintetico.tar.gz"
    base.write_bytes(b"base sintetica; no es una corrida ni datos\n")
    nominal = fixtures / "kit_nominal"
    receipt = kit_captura.crear(repo, nominal, base)
    verified = kit_captura.verificar(nominal)
    cases.append({"id": "kit_nominal_version_y_SHA", "conforme": receipt["captura_version"] == verified["captura_version"] == "1.1.1"
                  and receipt["captura_sha256"] == verified["captura_sha256"] == kit_captura.CAPTURA_SHA})
    modifications = (("ZIP_alterado_rechazado", "zip", None, None),
                     ("version_manifiesto_distinta_rechazada", "manifiesto.json", "captura_version", "1.0"),
                     ("SHA_captura_declarado_distinto_rechazado", "manifiesto.json", "captura_sha256", "0" * 64),
                     ("version_recibo_distinta_rechazada", "recibo_kit.json", "captura_version", "1.0"),
                     ("SHA_recibo_distinto_rechazado", "recibo_kit.json", "captura_sha256", "0" * 64))
    for name, target, key, value in modifications:
        kit = fixtures / name
        shutil.copytree(nominal, kit)
        if target == "zip":
            with (kit / "captura_1_1_1.zip").open("ab") as f:
                f.write(b"ALTERADO")
        else:
            path = kit / target
            data = json.loads(path.read_bytes())
            data[key] = value
            path.write_text(json.dumps(data), encoding="utf-8")
        rejected = False
        detail = ""
        try:
            kit_captura.verificar(kit)
        except ValueError as exc:
            rejected, detail = True, str(exc)
        cases.append({"id": name, "conforme": rejected, "mensaje": detail})

    spec = importlib.util.spec_from_file_location("lanzador_bajo_prueba_kit", repo / "herramientas/reproducir_capturado.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    for case, stage_error in (("recibo_lanzador_final_simulado", None),
                              ("recibo_lanzador_fallo_componentes_simulado", "componentes"),
                              ("recibo_lanzador_fallo_datos_simulado", "datos"),
                              ("recibo_lanzador_cfg_adverso_simulado", "cfg")):
        root = fixtures / case
        capture_dir = root / "repo/herramientas/captura_modelos"
        capture_dir.mkdir(parents=True)
        for name in ("captura.py", "sitecustomize.py"):
            (capture_dir / name).write_bytes((repo / "herramientas/captura_modelos" / name).read_bytes())
        fake_repo = root / "repo"
        (fake_repo / "reproducir.py").write_text("# emisor no ejecutable del ensayo\n", encoding="utf-8")
        cfg = fake_repo / "cfg.json"
        cfg.write_bytes(b"{}\n")
        captures = root / "capturas_vacias"
        captures.mkdir()
        work = root / "trabajo"
        if stage_error == "cfg":
            (work / "work").mkdir(parents=True)
            (work / "work/cfg_total.json").write_bytes(b"alterado, no usar\n")
        launcher.REPO, launcher.CFG = fake_repo, cfg
        launcher.CFG_SHA = hashlib.sha256(cfg.read_bytes()).hexdigest()
        launcher.entorno_efectivo = lambda: {"doble": True, "bibliotecas_modelos_importadas": False}
        commands = []

        def correr(cmd, env, log):
            commands.append(str(cmd[2]))
            return (1 if str(cmd[2]) == stage_error else 0), 0.0

        launcher.correr = correr
        argv = ["reproducir_capturado.py", "reproducir", f"--trabajo={work}", f"--capturas={captures}"]
        argv += ["--originales=inexistentes", "--decisiones=inexistentes"] if stage_error == "datos" else [f"--solo-componentes={root / 'semana1_ficticia'}"]
        previous = sys.argv
        sys.argv = argv
        code = None
        try:
            launcher.main()
        except SystemExit as exc:
            code = exc.code
        finally:
            sys.argv = previous
        data = json.loads((work / "recibo_reproducir_capturado.json").read_bytes())
        expected_commands = [] if stage_error == "cfg" else ["datos"] if stage_error == "datos" else ["componentes"]
        ok = data["captura_version"] == "1.1.1" and data["captura_sha256"] == kit_captura.CAPTURA_SHA
        ok = ok and commands == expected_commands and (code == 0 if stage_error is None else code != 0)
        cases.append({"id": case, "conforme": ok, "captura_version": data["captura_version"],
                      "captura_sha256": data["captura_sha256"], "etapas_simuladas": commands, "salida_simulada": code})
    assert not {"catboost", "lightgbm", "torch", "captura"}.intersection(sys.modules), "Biblioteca/capa de modelos importada"
    result = {"autor": "Codex", "utc": datetime.now(timezone.utc).isoformat(), "casos": cases,
              "conformes": sum(c["conforme"] for c in cases), "total": len(cases), "captura": identity,
              "actividad": {"procesos_modelos": 0, "modelos_importados": 0, "modelos_cargados": 0, "ajustes": 0,
                            "inferencias": 0, "replays": 0, "Kaggle": 0},
              "alcance": "Kit sintético verificado y main del lanzador con entorno/correr sustituidos; no CLI de reproducción real.",
              "fuentes_sha256": {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in kit_captura.ARCHIVOS}}
    kit_captura.escribir(args.salida, result)
    print(json.dumps({"conformes": result["conformes"], "total": result["total"]}))
    return 0 if result["conformes"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
