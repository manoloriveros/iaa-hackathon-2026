"""Reproducción completa con estimadores guardados (modo guardar) o desde estimadores congelados (modo reproducir).

Envuelve reproducir.py sin modificarlo: activa herramientas/captura_modelos con PYTHONPATH y CAPTURA_*, coloca en la
carpeta de trabajo el cfg_total.json que frecsev2.py lee de MODELOS_WORK (reproducir.py 1.2 no lo hace; mismo archivo que
receta/especificaciones/cfg_total.json, comprobado por SHA-256) y deja un recibo JSON con el entorno efectivo, las órdenes,
los códigos de salida, los tiempos, los eventos de captura por nodo y el SHA-256 de los CSV finales.

guardar     De los once originales a S30 y S22 reentrenando los 36 nodos; cada ajuste se guarda en --capturas.
reproducir  Mismo recorrido, pero cada ajuste se sustituye por la carga del estimador de --capturas; si falta alguno,
            el nodo falla y la orden termina con error. No ajusta nada.

Uso (desde la raíz de la carpeta común):
  python herramientas/reproducir_capturado.py guardar --originales=<Semana 1/Datos> --decisiones=<Semana 1> \
      --trabajo=<carpeta nueva> --capturas=<carpeta nueva> [--continuar-si-difiere] [--solo-componentes=<Semana 1 de una etapa datos previa>]
  python herramientas/reproducir_capturado.py reproducir --originales=... --decisiones=... --trabajo=<otra carpeta nueva> \
      --capturas=<capturas de una corrida guardar> [--continuar-si-difiere]
Códigos: los de reproducir.py (0 conforme, 1 no conforme o error, 2 uso, 3 diferencias toleradas).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from identidad_captura import identidad_captura

REPO = Path(__file__).resolve().parent.parent
CFG = REPO / "receta" / "especificaciones" / "cfg_total.json"
CFG_SHA = "aca601c652ab7caed8a6db95e15349e67e35fe341c57757861329a66a2ed643d"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def entorno_efectivo():
    paquetes = {}
    for nombre in ("numpy", "pandas", "scipy", "sklearn", "lightgbm", "catboost", "pyarrow", "torch"):
        try:
            mod = __import__(nombre)
            paquetes[nombre] = getattr(mod, "__version__", "?")
        except Exception as exc:  # noqa: BLE001
            paquetes[nombre] = f"no disponible: {type(exc).__name__}"
    ref = json.loads((REPO / "entorno" / "entorno_referencia.json").read_text(encoding="utf-8"))
    ref_p = {k.replace("scikit-learn", "sklearn"): v for k, v in ref.get("paquetes", {}).items()}
    dif = {k: {"efectivo": v, "referencia": ref_p.get(k)} for k, v in paquetes.items() if ref_p.get(k) and not str(ref_p[k]).startswith(str(v))}
    return {"python": sys.version.split()[0], "plataforma": platform.platform(), "procesador": platform.processor() or platform.machine(),
            "nucleos": os.cpu_count(), "paquetes": paquetes, "diferencias_con_referencia": dif}


def opciones(argv):
    o = {}
    for a in argv:
        if a.startswith("--"):
            k, _, v = a[2:].partition("=")
            o[k] = v if v else True
    return o


def correr(cmd, env, log: Path):
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"# {ahora()} {' '.join(map(str, cmd))}\n")
        f.flush()
        rc = subprocess.run([str(c) for c in cmd], env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    return rc, round(time.time() - t0, 1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("guardar", "reproducir"):
        print(__doc__)
        raise SystemExit(2)
    modo, o = sys.argv[1], opciones(sys.argv[2:])
    for k in ("trabajo", "capturas"):
        if not o.get(k):
            raise SystemExit(f"Falta --{k}")
    trabajo = Path(o["trabajo"]).resolve()
    capturas = Path(o["capturas"]).resolve()
    trabajo.mkdir(parents=True, exist_ok=True)
    if modo == "reproducir" and not capturas.is_dir():
        raise SystemExit(f"No existe la carpeta de estimadores {capturas}")
    if sha(CFG) != CFG_SHA:
        raise SystemExit("receta/especificaciones/cfg_total.json no tiene el SHA-256 esperado")
    captura = identidad_captura(REPO)
    recibo = {"herramienta": "reproducir_capturado.py", "modo": modo, "inicio_utc": ahora(), "repo": str(REPO), "orden": sys.argv,
              "reproducir_sha256": sha(REPO / "reproducir.py"), "captura_sha256": captura["sha256"],
              "captura_version": captura["version"], "captura_identidad": captura,
              "captura_identidad_origen": "Fuentes locales al inicio; no atribuye esta versión a modelos o nodos históricos.",
              "entorno": entorno_efectivo(), "pasos": []}
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "herramientas" / "captura_modelos") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env.update({"CAPTURA_MODO": modo, "CAPTURA_DIR": str(capturas), "CAPTURA_REPO": str(REPO)})
    py = sys.executable
    log = trabajo / "reproducir_capturado.log"
    if o.get("solo-componentes"):
        semana1 = Path(o["solo-componentes"]).resolve()
    else:
        for k in ("originales", "decisiones"):
            if not o.get(k):
                raise SystemExit(f"Falta --{k}")
        cmd = [py, REPO / "reproducir.py", "datos", f"--originales={o['originales']}", f"--decisiones={o['decisiones']}",
               f"--semana1={o['decisiones']}", f"--trabajo={trabajo}"]
        rc, seg = correr(cmd, env, log)
        recibo["pasos"].append({"paso": "datos", "orden": list(map(str, cmd)), "rc": rc, "segundos": seg, "fin_utc": ahora()})
        if rc:
            (trabajo / "recibo_reproducir_capturado.json").write_text(json.dumps(recibo, ensure_ascii=False, indent=1), encoding="utf-8")
            raise SystemExit(rc)
        semana1 = trabajo / "proyecto" / "Hackaton" / "Semana 1"
    (trabajo / "work").mkdir(parents=True, exist_ok=True)
    destino = trabajo / "work" / "cfg_total.json"
    if not destino.exists():
        shutil.copy2(CFG, destino)
    if sha(destino) != CFG_SHA:
        # un cfg_total.json previo distinto del de la receta no se usa ni se sobrescribe (COD-IA-20261019T232535Z)
        recibo["pasos"].append({"paso": "cfg_total", "rc": 1, "detalle": f"work/cfg_total.json existe con SHA-256 {sha(destino)}, distinto de {CFG_SHA}"})
        (trabajo / "recibo_reproducir_capturado.json").write_text(json.dumps(recibo, ensure_ascii=False, indent=1), encoding="utf-8")
        raise SystemExit("NO CONFORME: work/cfg_total.json no coincide con receta/especificaciones/cfg_total.json")
    recibo["desviaciones"] = [{"motivo": "frecsev2.py lee cfg_total.json de MODELOS_WORK y reproducir.py 1.2 no lo coloca",
                               "accion": "copia de receta/especificaciones/cfg_total.json en work/", "sha256": sha(destino)}]
    cmd = [py, REPO / "reproducir.py", "componentes", f"--semana1={semana1}", f"--trabajo={trabajo}"]
    if o.get("continuar-si-difiere"):
        cmd.append("--continuar-si-difiere")
    rc, seg = correr(cmd, env, log)
    recibo["pasos"].append({"paso": "componentes", "orden": list(map(str, cmd)), "rc": rc, "segundos": seg, "fin_utc": ahora()})
    # resumen de eventos de captura por nodo y estado de cada nodo según reproducir.py
    eventos = {}
    for d in sorted(capturas.glob("*/eventos.jsonl")) if capturas.is_dir() else []:
        cnt = {}
        for linea in d.read_text(encoding="utf-8").splitlines():
            e = json.loads(linea)
            if e.get("modo") == modo:
                cnt[e["evento"]] = cnt.get(e["evento"], 0) + 1
        eventos[d.parent.name] = cnt
    recibo["eventos_captura"] = eventos
    estados = {}
    reg = trabajo / "registro.jsonl"
    if reg.exists():
        for linea in reg.read_text(encoding="utf-8").splitlines():
            f = json.loads(linea)
            if f.get("nodo") and f.get("estado"):
                estados[f["nodo"]] = f["estado"]
            if f.get("objetivos"):
                recibo["objetivos"] = f["objetivos"]
                recibo["estado_final"] = f.get("estado")
    recibo["estados_nodos"] = estados
    recibo["fin_utc"] = ahora()
    recibo["rc"] = rc
    (trabajo / "recibo_reproducir_capturado.json").write_text(json.dumps(recibo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: recibo.get(k) for k in ("modo", "rc", "estado_final", "objetivos")}, ensure_ascii=False, indent=1))
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
