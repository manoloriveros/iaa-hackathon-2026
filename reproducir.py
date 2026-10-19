"""Punto de entrada único: reconstruye S30_claude_b (candidato principal) y S22_claude_propio (respaldo).

Versión 1.1 (19 de octubre de 2026): controles de conformidad del hallazgo GOV-007. El paquete solo termina con
código 0 cuando todo lo que se le pidió coincide con la receta; reanudar, verificar y las etapas de datos fallan
ante cualquier artefacto requerido que falte, no se pueda leer, no tenga huella esperada o difiera de ella.

Modos
  plan         Muestra el orden de los nodos de la receta y la orden exacta de cada uno, sin ejecutar nada.
  mezcla       Repite las mezclas finales a partir de los componentes guardados por el equipo (minutos). Antes de
               mezclar comprueba la huella de contenido de cada componente enlazado; al terminar, el SHA-256 de cada
               CSV con el entregado a Kaggle.
  componentes  Reconstruye desde las matrices F0 y la asignación de siniestros: variables, selecciones V23,
               componentes de producción, partes por peligro, severidades, línea B y mezclas (unas diez horas con dos
               núcleos). Compara cada artefacto con su huella esperada al terminar el nodo y se detiene si no coincide.
  verificar    Compara lo que haya en --trabajo con receta/huellas_esperadas.json, sin ejecutar nada; termina con
               error si algo falta, no se puede leer, no tiene huella esperada o difiere.
  datos        Etapas 00 a 02 desde los once Parquet originales: capa preparada (productor N62 de Codex), bases
               actuariales y matriz F0, en una raíz de proyecto mínima dentro de --trabajo (minutos). Cada paso se
               compara con su huella esperada y el modo falla si alguno no coincide.
  todo         datos y después componentes sobre lo que datos acaba de producir: de los originales a los dos CSV.

Opciones
  --semana1=<carpeta>   Carpeta «Hackaton/Semana 1» con Datos/, Matriz_F0_claude/runs/<F0>/ y
                        Bases_actuariales_claude/runs/<bases>/ (las entradas de la receta). En modo mezcla también
                        Modelos_claude/ y Modelos_claude_b/ con las corridas guardadas. Por defecto, IAA_SEMANA1.
  --trabajo=<carpeta>   Carpeta nueva donde se escriben work/, registros/ y registro.jsonl (por defecto ./trabajo).
  --objetivo=S30,S22    Objetivos a construir (por defecto los dos).
  --artefactos=<c>[,c]  Solo en modo mezcla: carpetas adicionales donde buscar las corridas guardadas.
  --solo=<nodo>[,...]   Ejecuta solo esos nodos (con sus salidas ya presentes para los que requieren). El resultado
                        final solo cubre los objetivos cuyo nodo esté entre los ejecutados.
  --originales=<c>      Modos datos y todo: carpeta con los once Parquet originales (por defecto <semana1>/Datos).
  --decisiones=<c>      Modos datos y todo: carpeta «Semana 1» del proyecto de donde se leen, con su SHA-256, las tres
                        listas congeladas que alimentan las marcas audit_* de F0 (por defecto --semana1).
  --continuar-si-difiere
                        No detenerse en el primer artefacto cuyo contenido difiere de la huella esperada: la
                        reconstrucción sigue, anota cada diferencia y termina con código 3 aunque los CSV finales
                        coincidan. Nunca convierte una diferencia en éxito. Un artefacto que falta, no se puede leer o
                        no tiene huella esperada detiene la reconstrucción también con esta opción.
  --relanzar-parciales  Si un nodo tiene solo parte de sus salidas (por ejemplo, porque el proceso murió a mitad),
                        aparta las existentes con el sufijo .parcial_<utc> y vuelve a ejecutar el nodo. Sin esta
                        opción el nodo se detiene y hay que revisar la carpeta de trabajo.

Reanudación. Si todas las salidas de un nodo existen ya en work/, el nodo se salta solo después de comprobar que
cada artefacto que la receta manda verificar coincide con su huella esperada (contenido; bytes para los CSV
finales). Cada nodo deja su salida estándar en registros/<nodo>.log y una línea en registro.jsonl con la orden, el
tiempo y las huellas obtenidas. Los scripts se ejecutan sin modificar, con las variables de entorno que esperan
(HAKATON_SEMANA1, MODELOS_WORK y MODELOS_CLAUDE).

Códigos de salida
  0  todo lo pedido coincide con la receta (contenido igual en los artefactos requeridos; SHA-256 exacto en los CSV
     finales construidos).
  1  detenido por un artefacto requerido que falta, no se puede leer, no tiene huella esperada o difiere; por un
     nodo que terminó con error; por entradas, originales, capa, bases, F0 o decisiones que no coinciden; o por un
     CSV final con SHA-256 distinto del entregado.
  2  uso incorrecto de la orden.
  3  terminó con --continuar-si-difiere y hubo diferencias de contenido en artefactos intermedios, aunque los CSV
     finales coincidan: reconstrucción documentada, no acreditada.
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
    """Detención por un artefacto o una entrada que no cumple el contrato de la receta (código 1)."""

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
    """Nodos necesarios para los objetivos, en el orden de la receta."""
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
    # Los dos escritores finales se ejecutan con serialización LF, como en la nube.
    # No normalizamos una salida después de verificarla ni relajamos su SHA exigido.
    if nodo["script"] in {"src/modelos/mezcla3.py", "src/linea_b/mezcla3_b.py"}:
        return [sys.executable, "-W", "ignore", str(REPO / "herramientas" / "ejecutar_csv_lf.py"), str(REPO / nodo["script"])] + args
    return [sys.executable, "-W", "ignore", str(REPO / nodo["script"])] + args


def entorno(semana1: Path, work: Path):
    env = dict(os.environ)
    env.update({"HAKATON_SEMANA1": str(semana1), "MODELOS_WORK": str(work), "MODELOS_CLAUDE": str(REPO / "src" / "modelos"),
                "PYTHONHASHSEED": "0"})
    return env


def esperadas():
    """Huellas esperadas de la receta. Sin este archivo no hay contrato, así que el paquete no puede continuar."""
    p = REPO / "receta" / "huellas_esperadas.json"
    if not p.is_file():
        raise NoConforme(f"falta {p.relative_to(REPO)}; sin huellas esperadas no se puede verificar nada")
    esp = json.loads(p.read_text(encoding="utf-8"))
    for clave in ("entradas", "salidas"):
        if not isinstance(esp.get(clave), dict) or not esp[clave]:
            raise NoConforme(f"receta/huellas_esperadas.json no tiene la sección «{clave}» o está vacía")
    return esp


def comparar(rel, work: Path, esp: dict, seccion: str = "salidas", clave: str | None = None):
    """Compara work/<rel> con la huella esperada esp[seccion][clave] (clave = rel salvo que se indique otra).
    Nunca lanza: deja el resultado en el diccionario."""
    p = work / rel
    e = esp.get(seccion, {}).get(clave or rel)
    r = {"ruta": rel, "existe": p.is_file(), "huella_esperada": isinstance(e, dict) and bool(e.get("contenido"))}
    if not p.is_file():
        return r
    try:
        h = huellas(p)
    except Exception as exc:  # archivo truncado, corrupto o de un formato que no se puede leer
        r.update({"legible": False, "error": f"{type(exc).__name__}: {exc}"})
        return r
    r.update({"legible": True, "sha256": h["sha256"], "contenido": h["contenido"]})
    if r["huella_esperada"]:
        r.update({"igual_bytes": h["sha256"] == e.get("sha256"), "igual_contenido": h["contenido"] == e["contenido"]})
    return r


def no_conformidades(filas, tolerar_diferencias=False):
    """Devuelve (bloqueantes, diferencias). Las bloqueantes detienen siempre; las diferencias de contenido solo
    pasan a la segunda lista cuando se pidió continuar. Los CSV finales exigen además SHA-256 exacto."""
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
    """Detiene el paquete si un artefacto requerido no cumple; devuelve las diferencias toleradas (lista vacía
    cuando todo coincide)."""
    if not filas:
        raise NoConforme(f"{contexto}: no hay artefactos requeridos que verificar")
    bloqueantes, diferencias = no_conformidades(filas, tolerar_diferencias)
    if bloqueantes:
        raise NoConforme(f"{contexto}: artefactos requeridos no conformes: {resumir(bloqueantes)}")
    return diferencias


def resumir(lista, maximo=8):
    """Los primeros elementos de una lista larga; el detalle completo queda en la salida JSON y en registro.jsonl."""
    return str(lista) if len(lista) <= maximo else f"{lista[:maximo]} y {len(lista) - maximo} más (detalle en la salida JSON y en registro.jsonl)"


def exigir_datos(informe):
    """Segunda barrera, en el punto de entrada, sobre el informe de las etapas de datos: cada control requerido del
    contrato «datos» de la receta tiene que estar presente y en verde."""
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
    """Huella de la asignación de bloques del contrato de F0, lo único que leen los modelos (comun.contract)."""
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
                # el contrato también anota el tipo Arrow de cada columna, que cambia con la versión de pandas
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
    """Aparta las salidas presentes de un nodo incompleto con el sufijo .parcial_<utc>; no borra nada."""
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
    """Ejecuta los nodos en orden. Devuelve la lista de diferencias toleradas (vacía si todo coincide)."""
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
            rc = subprocess.run(cmd, cwd=str(trabajo), env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # cwd fuera del repositorio: CatBoost escribe catboost_info/ en el directorio actual
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
    """Windows usa una copia privada: no requiere privilegios ni cambia el origen.
    Las comprobaciones posteriores exigen las mismas huellas que para un enlace.
    """
    if os.name == "nt":
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(src)


def preparar_mezcla(ids, semana1: Path, trabajo: Path, extra: list[Path], esp: dict):
    """Enlaza en work/ las salidas guardadas de los nodos previos a las mezclas y las exposiciones, y comprueba la
    huella de contenido de cada archivo enlazado. Devuelve (faltan, no_conformes)."""
    work = trabajo / "work"
    work.mkdir(parents=True, exist_ok=True)
    origenes = [semana1 / "Modelos_claude", semana1 / "Modelos_claude_b"] + extra
    sys.path.insert(0, str(REPO / "herramientas"))
    from inventario import localizar
    faltan, comp = [], []
    directos = sorted({r for i in ids if NODOS[i]["etapa"] == "mezcla" for r in NODOS[i]["requiere"]})
    for i in directos:
        n = NODOS[i]
        for rel in n["verificar"]:
            if not rel.endswith(".parquet"):
                continue  # la mezcla solo lee v24.parquet, prediccion_2025.parquet y sel_<nombre>.parquet
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
        # la exposición puede venir de la matriz de variables completa (huella en «salidas») o del extracto
        # insumos/exposicion_<ramo>.parquet que guarda el equipo (huella en «mezcla»)
        # Acepta exactamente uno de los dos insumos permitidos por el contrato.
        # Una copia Windows no conserva el nombre del origen al resolver realpath.
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
