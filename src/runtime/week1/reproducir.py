"""Reconstruct the frozen S30 blend and its S41 delivery calibration.

The runner checks required artifacts against the frozen recipe. An exact final CSV
match is a separate check from equality of intermediate artifacts.

Commands:
  plan          Print dependency order and commands without running models.
  mezcla        Rebuild final blends from verified, previously saved components.
  componentes   Rebuild features, selections, production models and blends from F0.
  verificar     Check existing outputs without training or changing files.
  datos         Rebuild prepared tables, actuarial bases and F0 from 11 original files.
  todo          Run datos, then componentes on the newly generated data.

Options:
  --semana1=<directory>     Week 1 workspace containing data and historical runs.
  --trabajo=<directory>     New private workspace for outputs, logs and journal.
  --objetivo=S30,S22        Requested blend targets; both are used by default.
  --artefactos=<directory>  Additional component directories for mezcla; repeatable.
  --solo=<node>[,...]       Run only named nodes whose dependencies already exist.
  --originales=<directory>  Original Parquet directory for datos and todo.
  --decisiones=<directory>  Frozen audit-flag decision lists, where required.
  --continuar-si-difiere    Record intermediate content differences and continue.
  --relanzar-parciales      Preserve incomplete outputs as .parcial_<UTC> and retry.

Missing, unreadable or unpinned required artifacts always stop execution. The
continue option never bypasses the exact SHA-256 check on a final CSV. Completed
nodes can be reused only after their required fingerprints have been checked.
Every executed node records its command, duration, exit code and output checks in
registro.jsonl and writes its standard output to registros/<node>.log.

Exit codes:
  0  All requested artifact checks and final CSV fingerprints match.
  1  A required input, stage, artifact or final fingerprint failed.
  2  Invalid command or arguments.
  3  Final CSVs match, but recorded intermediate content differences remain.

The full model graph can take several hours on two CPU cores. Model sources use
the runtime paths supplied by the runner; original data remain read-only.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.2"
VERSION_FECHA = "2026-10-19"

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "herramientas"))
from huella import huellas  # noqa: E402

RECETA = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
NODOS = {n["id"]: n for n in RECETA["nodos"]}
ORDEN = [n["id"] for n in RECETA["nodos"]]
CSV_FINALES = {v["csv"] for v in RECETA["objetivos"].values()}


class NoConforme(SystemExit):
    """Stop because a required input or artifact violates the recipe contract (exit code 1)."""

    def __init__(self, mensaje: str):
        super().__init__(f"NO CONFORME: {mensaje}")


def opciones(argv):
    o = {}
    for a in argv:
        if a.startswith("--"):
            k, _, v = a[2:].partition("=")
            o[k] = v if v else True
    return o


def cierre(objetivos, solo=None):
    """Return the target dependency closure in the frozen recipe order."""
    if solo:
        desconocidos = sorted(set(solo) - set(ORDEN))
        if desconocidos:
            raise SystemExit(f"--solo nombra nodos que no están en la receta: {desconocidos}")
        return [i for i in ORDEN if i in solo]
    raices = [RECETA["objetivos"][o]["nodo"] for o in objetivos]
    necesarios, pila = set(), list(raices)
    while pila:
        i = pila.pop()
        if i in necesarios:
            continue
        necesarios.add(i)
        pila += NODOS[i]["requiere"]
    return [i for i in ORDEN if i in necesarios]


def orden_de(nodo):
    args = [str(REPO / a) if a.startswith("receta/") else a for a in nodo["args"]]
    # Write both final CSVs with LF line endings, matching the reference serialization.
    # Keep the required SHA unchanged; do not normalize a file after verifying it.
    if nodo["script"] in {"src/modelos/mezcla3.py", "src/linea_b/mezcla3_b.py"}:
        return [sys.executable, "-W", "ignore", str(REPO / "herramientas" / "ejecutar_csv_lf.py"), str(REPO / nodo["script"])] + args
    return [sys.executable, "-W", "ignore", str(REPO / nodo["script"])] + args


def entorno(semana1: Path, work: Path):
    env = dict(os.environ)
    env.update({"HAKATON_SEMANA1": str(semana1), "MODELOS_WORK": str(work), "MODELOS_BASE": str(REPO / "src" / "modelos"),
                "PYTHONHASHSEED": "0"})
    return env


def esperadas():
    """Load expected fingerprints; execution requires this recipe contract."""
    p = REPO / "receta" / "huellas_esperadas.json"
    if not p.is_file():
        raise NoConforme(f"falta {p.relative_to(REPO)}; sin huellas esperadas no se puede verificar nada")
    esp = json.loads(p.read_text(encoding="utf-8"))
    for clave in ("entradas", "salidas"):
        if not isinstance(esp.get(clave), dict) or not esp[clave]:
            raise NoConforme(f"receta/huellas_esperadas.json no tiene la sección «{clave}» o está vacía")
    return esp


def comparar(rel, work: Path, esp: dict, seccion: str = "salidas", clave: str | None = None):
    """Compare work/<rel> with esp[section][key]. Return diagnostics instead of raising."""
    p = work / rel
    e = esp.get(seccion, {}).get(clave or rel)
    r = {"ruta": rel, "existe": p.is_file(), "huella_esperada": isinstance(e, dict) and bool(e.get("contenido"))}
    if not p.is_file():
        return r
    try:
        h = huellas(p)
    except Exception as exc:  # A required file may be truncated, corrupt or unreadable.
        r.update({"legible": False, "error": f"{type(exc).__name__}: {exc}"})
        return r
    r.update({"legible": True, "sha256": h["sha256"], "contenido": h["contenido"]})
    if r["huella_esperada"]:
        r.update({"igual_bytes": h["sha256"] == e.get("sha256"), "igual_contenido": h["contenido"] == e["contenido"]})
    return r


def no_conformidades(filas, tolerar_diferencias=False):
    """Separate blocking failures from allowed intermediate differences. Final CSVs also require exact bytes."""
    bloqueantes, diferencias = [], []
    for f in filas:
        if not f.get("existe"):
            bloqueantes.append((f["ruta"], "falta"))
        elif not f.get("legible", True):
            bloqueantes.append((f["ruta"], f"no se puede leer: {f.get('error')}"))
        elif not f.get("huella_esperada"):
            bloqueantes.append((f["ruta"], "sin huella esperada en la receta"))
        elif f.get("igual_contenido") is not True or (f["ruta"] in CSV_FINALES and f.get("igual_bytes") is not True):
            motivo = "contenido distinto" if f.get("igual_contenido") is not True else "CSV final con SHA-256 distinto"
            (diferencias if tolerar_diferencias else bloqueantes).append((f["ruta"], motivo))
    return bloqueantes, diferencias


def exigir_artefactos(filas, contexto: str, tolerar_diferencias=False):
    """Stop on blocking artifact failures and return any explicitly tolerated differences."""
    if not filas:
        raise NoConforme(f"{contexto}: no hay artefactos requeridos que verificar")
    bloqueantes, diferencias = no_conformidades(filas, tolerar_diferencias)
    if bloqueantes:
        raise NoConforme(f"{contexto}: artefactos requeridos no conformes: {resumir(bloqueantes)}")
    return diferencias


def resumir(lista, maximo=8):
    """Summarize long lists; the JSON output and journal retain every item."""
    return str(lista) if len(lista) <= maximo else f"{lista[:maximo]} y {len(lista) - maximo} más (detalle en la salida JSON y en registro.jsonl)"


def exigir_datos(informe):
    """Require every mandatory data-stage check to be present and successful at the entry point."""
    contrato = esperadas().get("datos")
    if not contrato or not isinstance(informe, dict):
        raise NoConforme("datos: falta el contrato esperado de datos o el informe no es válido")
    fallos = []
    for nombre in contrato["capa"]:
        if informe.get("capa", {}).get(nombre) is not True:
            fallos.append("capa/" + nombre)
    for grupo in ("bases", "f0"):
        for nombre in contrato[grupo]:
            item = informe.get(grupo, {}).get(nombre)
            if not isinstance(item, dict) or item.get("igual_contenido") is not True:
                fallos.append(grupo + "/" + nombre)
    if informe.get("f0", {}).get("contrato_bloques_iguales") is not True:
        fallos.append("f0/contrato_bloques_iguales")
    if fallos:
        raise NoConforme(f"datos: controles requeridos no conformes: {fallos}")


def bloques_contrato(p: Path) -> str:
    """Fingerprint the F0 feature-block assignments consumed by comun.contract."""
    import hashlib
    cols = json.loads(p.read_text(encoding="utf-8"))["columnas"]
    return hashlib.sha256(json.dumps({l: {c: v["bloque"] for c, v in cc.items()} for l, cc in cols.items()}, sort_keys=True).encode()).hexdigest()


def comprobar_entradas(semana1: Path, esp: dict):
    malas = []
    bloques_esperados = esp.get("datos", {}).get("f0_contrato_bloques")
    for rel, e in esp["entradas"].items():
        p = semana1 / rel
        if not p.is_file():
            malas.append((rel, "no existe"))
            continue
        try:
            if rel.endswith("contrato_disponibilidad.json"):
                # Arrow column types can vary with the pandas version.
                if not bloques_esperados:
                    malas.append((rel, "la receta no tiene la huella esperada de los bloques (datos/f0_contrato_bloques)"))
                elif bloques_contrato(p) != bloques_esperados:
                    malas.append((rel, "bloques distintos"))
            elif not e.get("contenido"):
                malas.append((rel, "sin huella de contenido esperada"))
            elif huellas(p)["contenido"] != e["contenido"]:
                malas.append((rel, "contenido distinto"))
        except Exception as exc:
            malas.append((rel, f"no se puede leer: {type(exc).__name__}: {exc}"))
    return malas


def registrar(trabajo: Path, fila: dict):
    with open(trabajo / "registro.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def apartar_parciales(nodo: dict, work: Path, trabajo: Path):
    """Preserve incomplete node outputs with a .parcial_<UTC> suffix; delete nothing."""
    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    apartadas = []
    for s in nodo["salidas"]:
        p = work / s
        if p.exists() or p.is_symlink():
            destino = p.with_name(p.name + f".parcial_{marca}")
            p.rename(destino)
            apartadas.append({"de": s, "a": str(destino.relative_to(work))})
    registrar(trabajo, {"nodo": nodo["id"], "estado": "parciales_apartadas", "apartadas": apartadas, "utc": ahora()})
    print(f"[{nodo['id']}] salidas parciales apartadas: {[a['a'] for a in apartadas]}", flush=True)


def ejecutar(ids, semana1: Path, trabajo: Path, continuar=False, relanzar_parciales=False):
    """Run nodes in dependency order and return the recorded intermediate differences."""
    work = trabajo / "work"
    (trabajo / "registros").mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    esp = esperadas()
    env = entorno(semana1, work)
    toleradas = []
    for i in ids:
        n = NODOS[i]
        presentes = [s for s in n["salidas"] if (work / s).is_file()]
        if len(presentes) == len(n["salidas"]):
            comp = [comparar(s, work, esp) for s in n["verificar"]]
            dif = exigir_artefactos(comp, f"reanudar {i}", continuar)
            estado = "reanudado_con_diferencias" if dif else "reanudado_verificado"
            registrar(trabajo, {"nodo": i, "estado": estado, "verificacion": comp, "utc": ahora()})
            print(f"[{i}] ya hecho, huellas requeridas verificadas" + (f"; difieren: {[d[0] for d in dif]}" if dif else ""), flush=True)
            toleradas += [(i, *d) for d in dif]
            continue
        if presentes or any((work / s).exists() or (work / s).is_symlink() for s in n["salidas"]):
            if not relanzar_parciales:
                raise NoConforme(f"{i}: salidas parciales en work/ ({presentes or 'rutas presentes sin archivo'}); "
                                 "revisar la carpeta de trabajo o relanzar con --relanzar-parciales")
            apartar_parciales(n, work, trabajo)
        cmd = orden_de(n)
        print(f"[{i}] {' '.join(cmd[3:])}", flush=True)
        t0 = time.time()
        with open(trabajo / "registros" / f"{i}.log", "a", encoding="utf-8") as log:
            log.write(f"# {ahora()} {' '.join(cmd)}\n")
            log.flush()
            rc = subprocess.run(cmd, cwd=str(trabajo), env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # Use a private cwd because CatBoost writes catboost_info/ there.
        seg = round(time.time() - t0, 1)
        comp = [comparar(s, work, esp) for s in n["verificar"]]
        bloq, dif = no_conformidades(comp, continuar)
        estado = "error" if rc else ("no_conforme" if bloq else ("difiere" if dif else "igual"))
        fila = {"nodo": i, "orden": cmd[2:], "rc": rc, "segundos": seg, "utc_fin": ahora(), "estado": estado, "verificacion": comp}
        registrar(trabajo, fila)
        print(f"[{i}] {estado} en {seg:.0f} s" + (f"; no conformes: {bloq}" if bloq else "") + (f"; difieren: {[d[0] for d in dif]}" if dif else ""), flush=True)
        if rc:
            raise SystemExit(f"El nodo {i} terminó con código {rc}; ver registros/{i}.log")
        exigir_artefactos(comp, f"salida {i}", continuar)
        toleradas += [(i, *d) for d in dif]
    return toleradas


def enlazar_archivo(src: Path, dst: Path):
    """Use a private copy on Windows, then apply the same checks as for a symbolic link."""
    if os.name == "nt":
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(src)


def preparar_mezcla(ids, semana1: Path, trabajo: Path, extra: list[Path], esp: dict):
    """Stage saved component and exposure files in work/, verify them, and return missing or nonconforming inputs."""
    work = trabajo / "work"
    work.mkdir(parents=True, exist_ok=True)
    origenes = [semana1 / "Modelos_base", semana1 / "Modelos_line_b"] + extra
    sys.path.insert(0, str(REPO / "herramientas"))
    from inventario import localizar
    faltan, comp = [], []
    directos = sorted({r for i in ids if NODOS[i]["etapa"] == "mezcla" for r in NODOS[i]["requiere"]})
    for i in directos:
        n = NODOS[i]
        for rel in n["verificar"]:
            if not rel.endswith(".parquet"):
                continue  # Blends read only v24.parquet, prediccion_2025.parquet and sel_<name>.parquet.
            dst = work / rel
            if not dst.exists():
                src = localizar(rel, origenes)
                if src is None:
                    faltan.append(rel)
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                enlazar_archivo(src, dst)
            comp.append(comparar(rel, work, esp))
    for line in ("motor", "buildings", "contents"):
        rel = f"feat_{line}.parquet"
        dst = work / rel
        if not dst.exists():
            src = next((o / "insumos" / f"exposicion_{line}.parquet" for o in origenes if (o / "insumos" / f"exposicion_{line}.parquet").is_file()), None)
            src = src or next((o / rel for o in origenes if (o / rel).is_file()), None)
            if src is None:
                faltan.append(f"{rel} (o insumos/exposicion_{line}.parquet)")
                continue
            enlazar_archivo(src, dst)
        # Exposure may come from the full feature matrix checked under salidas,
        # or from the frozen insumos/exposicion_<line>.parquet extract checked under mezcla.
        # Accept exactly one of the two contract-approved inputs.
        # Resolving a Windows copy does not retain its original source filename.
        completo = comparar(rel, work, esp)
        extracto = comparar(rel, work, esp, "mezcla", clave=f"insumos/exposicion_{line}.parquet")
        if completo.get("igual_contenido") is True:
            completo["contrato"] = "salidas"
            comp.append(completo)
        else:
            extracto["contrato"] = "mezcla"
            comp.append(extracto)
    bloq, _ = no_conformidades(comp, tolerar_diferencias=False)
    registrar(trabajo, {"modo": "mezcla", "estado": "componentes_enlazados", "faltan": faltan, "no_conformes": bloq, "verificacion": comp, "utc": ahora()})
    return faltan, bloq


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("plan", "mezcla", "componentes", "verificar", "datos", "todo"):
        print(__doc__)
        raise SystemExit(2)
    modo, o = sys.argv[1], opciones(sys.argv[2:])
    print(f"reproducir.py versión {VERSION} ({VERSION_FECHA}), modo {modo}", flush=True)
    if o.get("parar-si-difiere"):
        print("--parar-si-difiere ya es el comportamiento por defecto desde la versión 1.1; se ignora", flush=True)
    continuar = bool(o.get("continuar-si-difiere"))
    objetivos = [x for x in str(o.get("objetivo", "S30,S22")).split(",") if x]
    desconocidos = [x for x in objetivos if x not in RECETA["objetivos"]]
    if desconocidos:
        raise SystemExit(f"Objetivos desconocidos: {desconocidos}; la receta define {sorted(RECETA['objetivos'])}")
    semana1 = Path(o.get("semana1") or os.environ.get("IAA_SEMANA1", "")).expanduser().resolve()
    trabajo = Path(o.get("trabajo", "trabajo")).expanduser().resolve()
    solo = set(str(o["solo"]).split(",")) if o.get("solo") else None
    ids = cierre(objetivos, solo)
    if modo == "plan":
        for i in ids:
            n = NODOS[i]
            print(f"{i:30s} [{n['etapa']}, {n['linea']}, ~{n['minutos_ref']} min] {' '.join(orden_de(n)[3:])}")
        print(f"{len(ids)} nodos; tiempo de referencia ~{sum(NODOS[i]['minutos_ref'] or 0 for i in ids) / 60:.1f} h con dos núcleos")
        return
    if modo == "verificar":
        esp = esperadas()
        work = trabajo / "work"
        filas = [comparar(rel, work, esp) for i in ids for rel in NODOS[i]["verificar"]]
        bloq, _ = no_conformidades(filas, tolerar_diferencias=False)
        resumen = {"version": VERSION, "comparados": len(filas), "iguales_contenido": sum(f.get("igual_contenido") is True for f in filas),
                   "iguales_bytes": sum(f.get("igual_bytes") is True for f in filas),
                   "difieren": [f["ruta"] for f in filas if f.get("existe") and f.get("legible", True) and f.get("igual_contenido") is False],
                   "faltan": [f["ruta"] for f in filas if not f.get("existe")],
                   "ilegibles": [f["ruta"] for f in filas if f.get("existe") and not f.get("legible", True)],
                   "sin_huella_esperada": [f["ruta"] for f in filas if f.get("existe") and not f.get("huella_esperada")],
                   "conforme": not bloq}
        print(json.dumps(resumen, ensure_ascii=False, indent=1))
        exigir_artefactos(filas, "verificar")
        return
    if not semana1.is_dir():
        raise SystemExit("Falta --semana1=<carpeta Hackaton/Semana 1> (o la variable IAA_SEMANA1)")
    trabajo.mkdir(parents=True, exist_ok=True)
    registrar(trabajo, {"modo": modo, "estado": "inicio", "version": VERSION, "version_fecha": VERSION_FECHA, "orden": sys.argv[1:], "utc": ahora()})
    if modo in ("datos", "todo"):
        from etapas_datos import preparar_datos
        originales = Path(o.get("originales") or (semana1 / "Datos")).expanduser()
        decisiones = Path(o.get("decisiones") or semana1).expanduser()
        semana1, informe = preparar_datos(originales, decisiones, trabajo)
        exigir_datos(informe)
        registrar(trabajo, {"modo": "datos", "semana1": str(semana1), "informe": informe, "conforme": True, "utc": ahora()})
        print(json.dumps(informe, ensure_ascii=False, indent=1))
        if modo == "datos":
            print("datos: conforme", flush=True)
            return
        ids = cierre(objetivos, solo)
    esp = esperadas()
    if modo == "mezcla":
        extra = [Path(x) for x in str(o.get("artefactos", "")).split(",") if x]
        faltan, bloq = preparar_mezcla(ids, semana1, trabajo, extra, esp)
        if faltan:
            raise NoConforme(f"no encuentro estas salidas guardadas: {faltan}")
        if bloq:
            raise NoConforme(f"componentes guardados que no coinciden con la receta: {bloq}")
        ids = [i for i in ids if NODOS[i]["etapa"] == "mezcla"]
    else:
        malas = comprobar_entradas(semana1, esp)
        if malas:
            raise NoConforme(f"las entradas no coinciden con las de la receta: {malas}")
    toleradas = ejecutar(ids, semana1, trabajo, continuar=continuar, relanzar_parciales=bool(o.get("relanzar-parciales")))
    work = trabajo / "work"
    final, no_construidos = {}, []
    for ob in objetivos:
        t = RECETA["objetivos"][ob]
        if t["nodo"] not in ids:
            no_construidos.append(ob)
            continue
        p = work / t["csv"]
        sha = huellas(p)["sha256"] if p.is_file() else None
        final[ob] = {"csv": str(p), "sha256": sha, "esperado": t["sha256"], "coincide": sha == t["sha256"]}
    csv_ok = all(v["coincide"] for v in final.values())
    estado = "igual" if csv_ok and not toleradas else ("csv_iguales_con_diferencias_intermedias" if csv_ok else "csv_distinto")
    resultado = {"modo": modo, "version": VERSION, "objetivos": final, "objetivos_no_construidos": no_construidos,
                 "diferencias_toleradas": [{"nodo": n, "ruta": r, "motivo": m} for n, r, m in toleradas], "estado": estado, "utc": ahora()}
    registrar(trabajo, resultado)
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    if not csv_ok:
        raise SystemExit("NO CONFORME: algún CSV final no coincide con el entregado")
    if toleradas:
        print(f"Reconstrucción con {len(toleradas)} diferencias de contenido toleradas (--continuar-si-difiere): no acreditada", flush=True)
        raise SystemExit(3)


if __name__ == "__main__":
    main()
