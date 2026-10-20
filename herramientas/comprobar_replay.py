"""Comprueba una réplica desde estimadores congelados (reproducir_capturado.py reproducir) contra su carpeta de capturas.

Para cada nodo de la receta exige cinco cosas: que reproducir.py lo diera por igual a sus huellas esperadas; que en modo
reproducir solo haya eventos de carga (ningún guardado, duplicado, estimador ausente, Pool sin huella ni bloqueo del
centinela); que el conjunto de claves cargadas sea exactamente el de estimadores guardados para ese nodo, de modo que
cada estimador congelado se usó y ninguno faltó; que cada proceso con nodo de la receta tuviera activo el centinela de
ajustes; y, al final, que los CSV de S30 y S22 tengan el SHA-256 entregado. No ejecuta modelos ni modifica nada.

Con --referencia=<trabajo de la corrida que guardó los estimadores>, compara además cada salida declarada de cada nodo
(las 194 de la receta, también las que no tienen huella histórica) por su huella de contenido con la de esa corrida. En
ese caso el primer requisito cambia: un nodo cuyo estado frente a las huellas históricas difiere es conforme si todas sus
salidas son idénticas a las de la corrida de referencia y esa corrida tuvo el mismo estado. Así se separan dos preguntas:
si la réplica congelada repite exactamente el reajuste, y si el reajuste repite la historia.
Uso: python herramientas/comprobar_replay.py --trabajo=<trabajo de la réplica> --capturas=<capturas usadas> [--salida=<json>]
     [--referencia=<trabajo de la corrida guardar> [--registro-referencia=<registro.jsonl de esa corrida>]]
     (una carpeta montada con montar_paquetes.py --solo=todo no trae registro.jsonl: se indica aparte)
     [--sin-centinela]   (acepta procesos sin centinela; el resultado lo hace constar)
Códigos: 0 conforme, 1 no conforme, 2 uso.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "herramientas"))
from huella import huellas  # noqa: E402

PERMITIDOS = {"proceso", "cargado", "centinela", "centinela_aplicado"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    o = {}
    for a in sys.argv[1:]:
        if a.startswith("--"):
            k, _, v = a[2:].partition("=")
            o[k] = v if v else True
    if not o.get("trabajo") or not o.get("capturas"):
        print(__doc__)
        raise SystemExit(2)
    trabajo, capturas = Path(o["trabajo"]), Path(o["capturas"])
    receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    def leer_estados(t: Path):
        e = {}
        reg = t if t.suffix == ".jsonl" else t / "registro.jsonl"
        if not reg.is_file():
            raise SystemExit(f"No existe {reg}; con una carpeta montada desde paquetes, indique --registro-referencia")
        for linea in reg.read_text(encoding="utf-8").splitlines():
            f = json.loads(linea)
            if f.get("nodo") and f.get("estado"):
                e[f["nodo"]] = f
        return e

    estados = leer_estados(trabajo)
    referencia = Path(o["referencia"]) if o.get("referencia") else None
    estados_ref = leer_estados(Path(o["registro-referencia"]) if o.get("registro-referencia") else referencia) if referencia else {}
    nodos, fallos = [], []
    for n in receta["nodos"]:
        nid = n["id"]
        d = capturas / nid
        guardadas = {}
        for m in sorted(d.glob("*.json")) if d.is_dir() else []:
            ficha = json.loads(m.read_text(encoding="utf-8"))
            if isinstance(ficha, dict) and ficha.get("clave") and ".dup" not in ficha.get("archivo", ""):
                guardadas[ficha["clave"]] = ficha.get("tipo")
        ev = [json.loads(l) for l in (d / "eventos.jsonl").read_text(encoding="utf-8").splitlines()] if (d / "eventos.jsonl").exists() else []
        rep = [e for e in ev if e.get("modo") == "reproducir"]
        cargadas = Counter(e["clave"] for e in rep if e["evento"] == "cargado")
        anomalias = [e for e in rep if e["evento"] not in PERMITIDOS]
        procesos = {e["pid"] for e in rep if e["evento"] == "proceso"}
        con_centinela = {e["pid"] for e in rep if e["evento"] == "centinela"}
        estado = estados.get(nid, {}).get("estado")
        cotejo = None
        if referencia:
            cotejo = {"salidas": 0, "identicas_bytes": 0, "identicas_contenido": 0, "distintas": [], "faltan": [], "sin_referencia": []}
            for s in n["salidas"]:
                a, b = trabajo / "work" / s, referencia / "work" / s
                if not a.is_file():
                    cotejo["faltan"].append(s)
                    continue
                if not b.is_file():
                    # p. ej. feat_*.parquet, que los paquetes por nodo no llevan; se informa y no cuenta como diferencia
                    cotejo["sin_referencia"].append(s)
                    continue
                ha, hb = huellas(a), huellas(b)
                cotejo["salidas"] += 1
                cotejo["identicas_bytes"] += ha["sha256"] == hb["sha256"]
                if ha["contenido"] == hb["contenido"]:
                    cotejo["identicas_contenido"] += 1
                else:
                    cotejo["distintas"].append(s)
        fila = {"nodo": nid, "estado": estado, "estimadores_guardados": len(guardadas), "tipos": dict(Counter(guardadas.values())),
                "cargas": sum(cargadas.values()), "claves_cargadas": len(cargadas), "procesos": len(procesos),
                "procesos_con_centinela": len(procesos & con_centinela),
                "estado_referencia": estados_ref.get(nid, {}).get("estado") if referencia else None, "cotejo_con_referencia": cotejo,
                "claves_sin_cargar": sorted(set(guardadas) - set(cargadas)), "claves_cargadas_sin_ficha": sorted(set(cargadas) - set(guardadas)),
                "anomalias": [{k: e.get(k) for k in ("evento", "tipo", "clave", "funcion", "detalle")} for e in anomalias][:20]}
        motivos = []
        if estado not in ("igual", "reanudado_verificado"):
            clase = {"igual": "igual", "reanudado_verificado": "igual", "difiere": "difiere", "reanudado_con_diferencias": "difiere"}
            mismo = (referencia and not cotejo["distintas"] and not cotejo["faltan"]
                     and clase.get(estado, estado) == clase.get(fila["estado_referencia"], fila["estado_referencia"]))
            if not mismo:
                motivos.append(f"estado {estado}")
        if cotejo and (cotejo["distintas"] or cotejo["faltan"]):
            motivos.append(f"{len(cotejo['distintas'])} salidas distintas y {len(cotejo['faltan'])} ausentes frente a la referencia")
        if anomalias:
            motivos.append(f"{len(anomalias)} eventos distintos de carga en modo reproducir")
        if fila["claves_sin_cargar"] or fila["claves_cargadas_sin_ficha"]:
            motivos.append("las claves cargadas no son las guardadas")
        if guardadas and not procesos:
            motivos.append("tiene estimadores pero ningún proceso de la réplica")
        if procesos - con_centinela and not o.get("sin-centinela"):
            motivos.append(f"{len(procesos - con_centinela)} procesos sin centinela")
        fila["conforme"] = not motivos
        fila["motivos"] = motivos
        if motivos:
            fallos.append(nid)
        nodos.append(fila)
    finales = {}
    for ob, t in receta["objetivos"].items():
        p = trabajo / "work" / t["csv"]
        s = sha(p) if p.exists() else None
        finales[ob] = {"csv": t["csv"], "sha256": s, "esperado": t["sha256"], "coincide": s == t["sha256"]}
        if s != t["sha256"]:
            fallos.append(f"CSV {ob}")
    tipos = defaultdict(int)
    for x in nodos:
        for t, c in x["tipos"].items():
            tipos[t] += c
    res = {"herramienta": "comprobar_replay.py", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "trabajo": str(trabajo),
           "capturas": str(capturas), "nodos": nodos, "csv_finales": finales,
           "totales": {"nodos": len(nodos), "nodos_conformes": sum(x["conforme"] for x in nodos),
                       "nodos_con_estimadores": sum(1 for x in nodos if x["estimadores_guardados"]),
                       "estimadores_guardados": sum(x["estimadores_guardados"] for x in nodos), "por_tipo": dict(tipos),
                       "cargas": sum(x["cargas"] for x in nodos), "procesos": sum(x["procesos"] for x in nodos),
                       "procesos_con_centinela": sum(x["procesos_con_centinela"] for x in nodos),
                       "estados": dict(Counter(x["estado"] for x in nodos)),
                       "salidas_cotejadas": sum(x["cotejo_con_referencia"]["salidas"] for x in nodos) if referencia else None,
                       "salidas_identicas_contenido": sum(x["cotejo_con_referencia"]["identicas_contenido"] for x in nodos) if referencia else None,
                       "salidas_identicas_bytes": sum(x["cotejo_con_referencia"]["identicas_bytes"] for x in nodos) if referencia else None},
           "referencia": str(referencia) if referencia else None,
           "conforme": not fallos, "no_conformes": fallos}
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if o.get("salida"):
        Path(o["salida"]).write_text(texto, encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("totales", "csv_finales", "conforme", "no_conformes")}, ensure_ascii=False, indent=1))
    raise SystemExit(0 if res["conforme"] else 1)


if __name__ == "__main__":
    main()
