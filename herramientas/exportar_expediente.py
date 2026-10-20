"""Exporta al repositorio una copia legible del foro común y del registro de decisiones, con identificadores enmascarados.

    python herramientas/exportar_expediente.py --raiz C:/dev/Hakaton

Lee foros/FORO.md y Preparación/DECISIONES.md desde la raíz del proyecto (sin modificarlos) y escribe en docs/expediente/:

    foro/FORO.md                  copia del foro con identificadores sintéticos de pólizas, clientes, siniestros y direcciones enmascarados
    foro/indice.csv               un aporte por fila: autor, identificador, hora UTC y asunto
    decisiones/DECISIONES.md      copia del registro de decisiones con el mismo enmascarado
    decisiones/indice.csv         un encabezado por fila
    MANIFIESTO.json               SHA-256 de fuentes y salidas, regla de enmascarado y recuentos

El enmascarado sustituye cada identificador por su prefijo y seis caracteres de su SHA-256 (por ejemplo, C·3fa9c1): las menciones
del mismo caso siguen enlazadas sin mostrar el valor. Si aparece algo con forma de credencial, la exportación se detiene sin escribir.
Los datos son sintéticos; aun así, el expediente no lleva filas de datos ni conversaciones privadas.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FUENTES = {"foro": "foros/FORO.md", "decisiones": "Preparación/DECISIONES.md"}
# Claves de los datos del concurso: CL (siniestro), TP, A (dirección), B/C/M (pólizas o clientes) seguidos de 7 a 9 cifras.
ID_DATOS = re.compile(r"\b(CL|TP|[ABCM])(\d{7,9})\b")
CREDENCIAL = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
                        r"|\"key\"\s*:\s*\"[0-9a-f]{32}\"")
# Mismo criterio de encabezado que herramientas/cifras_entregables.py (bloque del foro).
APORTE = re.compile(r"(?m)^## (Codex|Claude|Participante) \| ([A-Z]{3}[^|]*?) \| ([0-9T:\-+.]+) \| (.*)$")
ENCABEZADO = re.compile(r"(?m)^(#{2,3}) (.+)$")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def enmascarar(texto: str):
    vistos = {}

    def cambio(m):
        clave = m.group(0)
        vistos[clave] = vistos.get(clave, 0) + 1
        return f"{m.group(1)}·{sha(clave.encode())[:6]}"

    return ID_DATOS.sub(cambio, texto), vistos


def indice_foro(texto: str):
    filas = [{"autor": m.group(1), "id": m.group(2).strip(), "utc": m.group(3), "asunto": m.group(4).strip()} for m in APORTE.finditer(texto)]
    return filas


def indice_decisiones(texto: str):
    filas = []
    for m in ENCABEZADO.finditer(texto):
        titulo = m.group(2).strip()
        ident = re.match(r"([A-Z]{1,4}\d{1,3}[a-z]?)\b", titulo)
        filas.append({"nivel": len(m.group(1)), "id": ident.group(1) if ident else "", "titulo": titulo})
    return filas


def a_csv(filas, campos) -> str:
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=campos, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    return b.getvalue()


def cabecera(nombre: str, ruta: str, h: str, n_ids: int, utc: str) -> str:
    return (f"<!-- Copia exportada para el expediente de la entrega. Fuente: {ruta} (SHA-256 {h}), exportada el {utc}. "
            f"Identificadores sintéticos de los datos enmascarados: {n_ids} menciones. El original sigue fuera del repositorio "
            f"y no se modificó. Regenerar con herramientas/exportar_expediente.py. -->\n\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", required=True, type=Path, help="raíz del proyecto (contiene foros/ y Preparación/)")
    ap.add_argument("--salida", type=Path, default=REPO / "docs/expediente")
    a = ap.parse_args()
    utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifiesto = {"generado_utc": utc, "script": "herramientas/exportar_expediente.py",
                  "regla_enmascarado": ID_DATOS.pattern + " → prefijo·sha256[:6]", "fuentes": {}, "salidas": {}}
    escrituras = {}
    for clave, rel in FUENTES.items():
        p = a.raiz / rel
        bruto = p.read_bytes()
        texto = bruto.decode("utf-8-sig").replace("\r\n", "\n")
        if CREDENCIAL.search(texto):
            raise SystemExit(f"{rel}: hay un texto con forma de credencial; no se exporta nada.")
        limpio, vistos = enmascarar(texto)
        resto = ID_DATOS.findall(limpio)
        if resto:
            raise SystemExit(f"{rel}: quedaron identificadores sin enmascarar: {resto[:3]}")
        h = sha(bruto)
        manifiesto["fuentes"][clave] = {"ruta": rel, "sha256": h, "bytes": len(bruto), "identificadores_distintos": len(vistos),
                                        "menciones_enmascaradas": sum(vistos.values())}
        nombre = Path(rel).name
        escrituras[f"{clave}/{nombre}"] = cabecera(nombre, rel, h, sum(vistos.values()), utc) + limpio
        if clave == "foro":
            filas = indice_foro(limpio)
            manifiesto["fuentes"][clave]["aportes"] = len(filas)
            escrituras["foro/indice.csv"] = a_csv(filas, ["autor", "id", "utc", "asunto"])
        else:
            filas = indice_decisiones(limpio)
            manifiesto["fuentes"][clave]["encabezados"] = len(filas)
            escrituras["decisiones/indice.csv"] = a_csv(filas, ["nivel", "id", "titulo"])
    for rel, contenido in escrituras.items():
        destino = a.salida / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        datos = contenido.encode("utf-8")
        destino.write_bytes(datos)
        manifiesto["salidas"][rel] = {"sha256": sha(datos), "bytes": len(datos)}
    (a.salida / "MANIFIESTO.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: {x: v[x] for x in v if x != "ruta"} for k, v in manifiesto["fuentes"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
