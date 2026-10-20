"""Monta una carpeta de capturas (o una carpeta de trabajo) a partir de los paquetes por nodo de una corrida.

Cada carpeta de paquetes contiene, por nodo, <nodo>.manifiesto.json y el archivo <nodo>.tar.gz o las partes que nombra su
manifiesto. Se comprueba el SHA-256 de cada parte, el del .tar.gz reunido y el de cada miembro extraído contra el
manifiesto; cualquier diferencia detiene el montaje. Si un nodo aparece en varias carpetas, gana la última de la lista:
así una recaptura sustituye por completo, nodo a nodo, a la captura anterior, sin mezclar estimadores de las dos.
Solo se extraen archivos regulares con rutas relativas sin «..».
Uso: python herramientas/montar_paquetes.py --paquetes=<carpeta>[,<carpeta>...] --destino=<carpeta nueva> [--solo=capturas|todo]
     [--salida=<json>]
--solo=capturas (por defecto) deja en el destino una raíz de capturas: <destino>/<nodo>/<archivo>.
--solo=todo extrae también work/ y registros/ con sus rutas.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    o = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if not o.get("paquetes") or not o.get("destino"):
        print(__doc__)
        raise SystemExit(2)
    solo = o.get("solo", "capturas")
    destino = Path(o["destino"])
    if destino.exists() and any(destino.iterdir()):
        raise SystemExit(f"{destino} ya existe y no está vacía; use una carpeta nueva")
    elegidos = {}
    for carpeta in o["paquetes"].split(","):
        for man in sorted(Path(carpeta).glob("*.manifiesto.json")):
            m = json.loads(man.read_text(encoding="utf-8"))
            elegidos[m["nodo"]] = (Path(carpeta), man, m)
    informe = []
    for nodo, (carpeta, man, m) in sorted(elegidos.items()):
        if m.get("partes"):
            trozos = []
            for p in m["partes"]:
                b = (carpeta / p["archivo"]).read_bytes()
                if sha_bytes(b) != p["sha256"] or len(b) != p["bytes"]:
                    raise SystemExit(f"{nodo}: la parte {p['archivo']} no coincide con su manifiesto")
                trozos.append(b)
            datos = b"".join(trozos)
        else:
            datos = (carpeta / m["tar"]).read_bytes()
        if sha_bytes(datos) != m["tar_sha256"]:
            raise SystemExit(f"{nodo}: el paquete reunido no coincide con tar_sha256 de su manifiesto")
        esperados = {x["ruta"]: x for x in m["miembros"]}
        extraidos = 0
        with tarfile.open(fileobj=io.BytesIO(datos), mode="r:gz") as t:
            for mi in t.getmembers():
                ruta = PurePosixPath(mi.name)
                if not mi.isfile() or ruta.is_absolute() or ".." in ruta.parts:
                    raise SystemExit(f"{nodo}: miembro no admitido {mi.name}")
                if mi.name not in esperados:
                    raise SystemExit(f"{nodo}: miembro {mi.name} fuera del manifiesto")
                b = t.extractfile(mi).read()
                if sha_bytes(b) != esperados[mi.name]["sha256"]:
                    raise SystemExit(f"{nodo}: el miembro {mi.name} no coincide con su manifiesto")
                if solo == "capturas":
                    if ruta.parts[0] != "capturas":
                        continue
                    final = destino.joinpath(*ruta.parts[1:])
                else:
                    final = destino.joinpath(*ruta.parts)
                final.parent.mkdir(parents=True, exist_ok=True)
                final.write_bytes(b)
                extraidos += 1
        faltan = set(esperados) - {mi.name for mi in tarfile.open(fileobj=io.BytesIO(datos), mode="r:gz").getmembers()}
        if faltan:
            raise SystemExit(f"{nodo}: faltan en el paquete {sorted(faltan)[:3]}")
        informe.append({"nodo": nodo, "carpeta": str(carpeta), "manifiesto": man.name, "tar_sha256": m["tar_sha256"],
                        "miembros": len(esperados), "extraidos": extraidos})
    res = {"herramienta": "montar_paquetes.py", "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "solo": solo,
           "destino": str(destino), "nodos": informe, "miembros_comprobados": sum(x["miembros"] for x in informe),
           "archivos_extraidos": sum(x["extraidos"] for x in informe)}
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if o.get("salida"):
        Path(o["salida"]).write_text(texto, encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("solo", "destino", "miembros_comprobados", "archivos_extraidos")}, ensure_ascii=False),
          len(informe), "nodos")


if __name__ == "__main__":
    main()
