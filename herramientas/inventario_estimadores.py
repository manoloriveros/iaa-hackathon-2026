"""Inventario por nodo de los estimadores congelados de una carpeta de capturas (herramientas/captura_modelos).

Para cada nodo de la receta lista cada estimador con su tipo, formato, archivo, SHA-256 comprobado contra su ficha, bytes,
versión de la captura que lo guardó, fecha y lo que su ficha registra (mejor iteración, árboles, coeficientes, épocas). Los
duplicados de una misma clave (archivo .dupN) se listan aparte: no se cargan en la réplica. Indica además si el nodo
admite inferencia sin ajuste con lo guardado, según el tipo de script, y qué estimaciones cerradas vuelve a calcular la
réplica. No carga modelos ni modifica nada.
Uso: python herramientas/inventario_estimadores.py --capturas=<carpeta> --salida=<json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FORMATO = {"lgb": "LightGBM, modelo en texto con todas las iteraciones", "cb": "CatBoost .cbm", "glm": "coeficientes GLM gamma .npy (float64)",
           "prep": "codificadores de la red (pickle: medianas, faltantes, QuantileTransformer, categorías raras)", "mlp": "red Tweedie, state_dict .pt"}
# Estimaciones cerradas que la réplica vuelve a calcular porque no son estimadores de la capa de captura
RECALCULA = {"severidad_tendencia.py": "además de cargar sus GLM, la pendiente log-lineal de la severidad media anual (numpy.polyfit, fórmula cerrada)",
             "construir_variables.py": "variables derivadas de los datos (sin modelos)",
             "combinar_semillas.py": "promedio aritmético de semillas (sin modelos)",
             "mezcla3.py": "pesos fijos de la receta; factores de nivel f23 y f24 por fórmula cerrada, sum(y/sqrt(mu))/sum(sqrt(mu)) sobre V23 y V24",
             "mezcla3_b.py": "pesos fijos de la receta; factores de nivel por la misma fórmula cerrada de mezcla3.py"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    o = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if not o.get("capturas") or not o.get("salida"):
        print(__doc__)
        raise SystemExit(2)
    cap = Path(o["capturas"])
    receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    nodos, problemas = [], []
    for n in receta["nodos"]:
        d = cap / n["id"]
        estimadores, duplicados = [], []
        for m in sorted(d.glob("*.json")) if d.is_dir() else []:
            f = json.loads(m.read_text(encoding="utf-8"))
            if not isinstance(f, dict) or not f.get("clave"):
                continue
            ruta = d / f["archivo"]
            real = sha(ruta) if ruta.exists() else None
            fila = {"tipo": f["tipo"], "formato": FORMATO.get(f["tipo"], f["tipo"]), "archivo": f"{n['id']}/{f['archivo']}", "clave": f["clave"],
                    "sha256": f["sha256"], "sha256_coincide": real == f["sha256"], "bytes": f.get("bytes"), "captura_version": f.get("captura_version"),
                    "utc": f.get("utc")}
            for k in ("best_iteration", "current_iteration", "num_trees", "tree_count", "num_boost_round", "n_filas", "con_validacion",
                      "best_ep", "epochs", "seed", "funcion", "n_obs", "segundos_ajuste", "reaplicacion_identica"):
                if k in f:
                    fila[k] = f[k]
            if f["tipo"] == "glm":
                fila["coeficientes"] = f.get("coeficientes_decimal")
            if real != f["sha256"]:
                problemas.append(fila["archivo"])
            (duplicados if ".dup" in f["archivo"] else estimadores).append(fila)
        script = Path(n["script"]).name
        tipos = Counter(e["tipo"] for e in estimadores)
        nodos.append({"nodo": n["id"], "script": n["script"], "estimadores": estimadores, "duplicados_no_cargados": duplicados,
                      "por_tipo": dict(tipos), "versiones_captura": sorted({e["captura_version"] for e in estimadores if e["captura_version"]}),
                      "inferencia_sin_ajuste": bool(estimadores) or script in RECALCULA,
                      "recalcula_en_replica": RECALCULA.get(script)})
    tot = Counter()
    for x in nodos:
        tot.update(x["por_tipo"])
    res = {"herramienta": "inventario_estimadores.py", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "capturas": str(cap),
           "nodos": nodos, "totales": {"nodos": len(nodos), "nodos_con_estimadores": sum(1 for x in nodos if x["estimadores"]),
                                       "estimadores": sum(len(x["estimadores"]) for x in nodos), "por_tipo": dict(tot),
                                       "duplicados_no_cargados": sum(len(x["duplicados_no_cargados"]) for x in nodos),
                                       "bytes": sum(e["bytes"] or 0 for x in nodos for e in x["estimadores"])},
           "sha256_no_coincide": problemas,
           "nota_datos": "La etapa datos (reproducir.py datos) recalcula desde los originales la capa preparada, las bases actuariales y F0, "
                         "incluida la cola de los factores de desarrollo (numpy.polyfit en bases_actuariales.py), y se compara con sus huellas."}
    Path(o["salida"]).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res["totales"], ensure_ascii=False), "problemas:", len(problemas))
    raise SystemExit(1 if problemas else 0)


if __name__ == "__main__":
    main()
