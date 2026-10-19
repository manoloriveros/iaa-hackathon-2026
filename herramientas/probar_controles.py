"""Batería de casos de control del paquete (hallazgo GOV-007): comprueba, desde la orden de consola, que
reproducir.py termina con código 0 solo cuando todo lo pedido coincide con la receta, y con código distinto de 0 en
cada caso adverso (artefacto que falta, ilegible, sin huella esperada o distinto; entradas, originales, capa, bases,
F0 o decisiones cambiadas; nodo con error; salida parcial; CSV final con bytes distintos).

Cada caso arma un paquete de prueba aislado: una copia de reproducir.py y de herramientas/ con una receta sintética
de dos nodos (un componente y una mezcla), huellas esperadas calculadas sobre archivos de dos filas y tres scripts
guardia en el lugar de las etapas reales de datos (N62, D67 y D68) que dejan una marca y fallan si alguien los
invoca. Ningún caso lee datos del concurso, entrena un modelo ni ejecuta una etapa real: el único script que se
ejecuta como nodo es un emisor de archivos de prueba.

Uso: python herramientas/probar_controles.py [--salida=<carpeta>] [--carpeta=<carpeta temporal>] [--conservar]
  --salida    carpeta donde quedan resultado.json y los registros de cada caso (por defecto
              docs/controles/<utc>_<plataforma>/ dentro del repositorio).
  --carpeta   carpeta temporal donde se arman los paquetes de prueba (por defecto una carpeta nueva del sistema).
  --conservar no borra la carpeta temporal al terminar.
Termina con código 0 si todos los casos dan el resultado esperado y 1 en caso contrario.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
sys.path.insert(0, str(AQUI))
from huella import huellas, sha256_bytes  # noqa: E402

PREAUDIT = "preaudit_20261016T211816Z_817285a5"
BASES_NOMBRE = "bases_20261017T120251Z_45443ff0"
F0_NOMBRE = "f0_20261017T141732Z_65df7fca"
ARCHIVOS_PAQUETE = ["reproducir.py", "herramientas/huella.py", "herramientas/inventario.py", "herramientas/etapas_datos.py"]
CAPA = ["policies_motor", "policies_buildings", "policies_contents", "test_motor", "test_buildings", "test_contents",
        "customers", "addresses", "weather", "claims", "sample_submission"]
DECISIONES = ["Limpieza/runs/capendorse_20261017T010844Z_fbf8cc20/ledger/cumulative_retrospective_changes.parquet",
              "Limpieza/runs/capfix_20261016T184904Z_099a22b1/ledger/all_capital_changes.parquet",
              "Decision_criterios_capital_claude/runs/dec_20261017T024905Z_c6e024cb/tables/autorizadas.csv"]
BASES = ["tables/t0_por_row_id.parquet", "tables/asignacion_por_siniestro.parquet", "tables/factores_desarrollo_conteos.csv",
         "tables/ibnr_por_peligro_anio.csv", "tables/completitud_2024_por_mes.csv", "tables/chain_ladder_conteos.csv"]
F0 = ["tables/f0_motor.parquet", "tables/f0_buildings.parquet", "tables/f0_contents.parquet", "tables/particiones.parquet"]
ENTRADAS = ["Datos/weather.parquet", "Datos/sample_submission.parquet", f"Matriz_F0_claude/runs/{F0_NOMBRE}/tables/f0_motor.parquet",
            f"Matriz_F0_claude/runs/{F0_NOMBRE}/tables/f0_buildings.parquet", f"Matriz_F0_claude/runs/{F0_NOMBRE}/tables/f0_contents.parquet",
            f"Matriz_F0_claude/runs/{F0_NOMBRE}/tables/particiones.parquet", f"Matriz_F0_claude/runs/{F0_NOMBRE}/contrato_disponibilidad.json",
            f"Bases_actuariales_claude/runs/{BASES_NOMBRE}/tables/asignacion_por_siniestro.parquet"]

GUARDIA = """# Guardia de prueba: ocupa el lugar de una etapa real de datos. Si alguien la invoca, deja una marca y falla.
import os, sys
from pathlib import Path
Path(os.environ["PRUEBA_MARCAS"], "etapa_" + Path(__file__).stem + ".txt").write_text(" ".join(sys.argv), encoding="utf-8")
raise SystemExit(93)
"""

EMISOR = """# Emisor de archivos de prueba: hace de nodo de la receta sintética. Escribe dos filas por archivo.
import os, sys
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
que = sys.argv[1]
work = Path(os.environ["MODELOS_WORK"])
Path(os.environ["PRUEBA_MARCAS"], f"emisor_{que}.txt").write_text(" ".join(sys.argv), encoding="utf-8")
variante = os.environ.get("EMISOR_VARIANTE_" + que.upper(), "ok")
if variante == "falla":
    raise SystemExit(7)
def tabla(p, valor=1.0, compresion="snappy"):
    pq.write_table(pa.table({"row_id": ["prueba_a", "prueba_b"], "x": [valor, 2.0]}), p, compression=compresion)
if que == "comp":
    (work / "comp").mkdir(parents=True, exist_ok=True)
    tabla(work / "comp" / "v24.parquet", 9.0 if variante == "contenido_distinto" else 1.0)
    if variante != "omitir_salida":
        tabla(work / "comp" / "prediccion_2025.parquet")
elif que == "mezcla":
    (work / "final").mkdir(parents=True, exist_ok=True)
    csv = b"row_id,prediction\\nprueba_a,1\\nprueba_b,2\\n"
    if variante == "csv_bytes_distintos":
        csv = csv.replace(b"\\n", b"\\r\\n")
    if variante == "contenido_distinto":
        csv = csv.replace(b"prueba_b,2", b"prueba_b,3")
    (work / "final" / "final.csv").write_bytes(csv)
    tabla(work / "final" / "prediccion_2025.parquet", 9.0 if variante == "contenido_distinto" else 1.0)
"""


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def escribir(p: Path, contenido, binario=False):
    p.parent.mkdir(parents=True, exist_ok=True)
    if binario:
        p.write_bytes(contenido)
    else:
        p.write_text(contenido, encoding="utf-8")


def tabla(p: Path, valor=1.0, compresion="snappy"):
    import pyarrow as pa
    import pyarrow.parquet as pq
    p.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"row_id": ["prueba_a", "prueba_b"], "x": [valor, 2.0]}), p, compression=compresion)


def volcar(p: Path, obj):
    escribir(p, json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


class Caso:
    """Un paquete de prueba completo: paquete p/, carpeta de trabajo w/, originales raw/, decisiones dec/, marcas/."""

    def __init__(self, base: Path, codigo: str, referencia: Path):
        self.codigo = codigo
        self.raiz = base / codigo
        self.p = self.raiz / "p"
        self.w = self.raiz / "w"
        self.s1 = self.w / "proyecto" / "Hackaton" / "Semana 1"
        self.raw = self.raiz / "raw"
        self.dec = self.raiz / "dec"
        self.marcas = self.raiz / "marcas"
        self.marcas.mkdir(parents=True)
        self.work = self.w / "work"
        self.ref = referencia
        self.env = {}
        # paquete: orquestador, herramientas, guardias y emisor
        for rel in ARCHIVOS_PAQUETE:
            escribir(self.p / rel, (REPO / rel).read_bytes(), binario=True)
        for rel in ("src/datos/n62_codex/rebuild_base.py", "src/datos/bases_actuariales.py", "src/datos/construir_f0.py", "guardia_nodo.py"):
            escribir(self.p / rel, GUARDIA)
        escribir(self.p / "emisor.py", EMISOR)
        # etapas de datos en caché: originales, capa, decisiones, bases y F0
        capa = self.s1 / "Limpieza" / "runs" / PREAUDIT
        originales, capa_h = {}, {}
        for n in CAPA:
            tabla(self.raw / f"{n}.parquet")
            tabla(capa / "data" / f"{n}.parquet")
            originales[f"{n}.parquet"] = sha256_bytes(self.raw / f"{n}.parquet")
            capa_h[n] = sha256_bytes(capa / "data" / f"{n}.parquet")
        volcar(capa / "COMPLETE.json", {"prueba": True})
        datos = self.s1 / "Datos"
        datos.mkdir(parents=True)
        for n in CAPA:
            shutil.copyfile(capa / "data" / f"{n}.parquet", datos / f"{n}.parquet")
        decisiones = {}
        for rel in DECISIONES:
            src, dst = self.dec / rel, self.s1 / rel
            if src.suffix == ".parquet":
                tabla(src)
            else:
                escribir(src, "row_id\nprueba_a\n")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            decisiones[rel] = {"uso": "prueba", "sha256": sha256_bytes(src)}
        self.bases = self.s1 / "Bases_actuariales_claude" / "runs" / BASES_NOMBRE
        self.f0 = self.s1 / "Matriz_F0_claude" / "runs" / F0_NOMBRE
        for corrida, lista in ((self.bases, BASES), (self.f0, F0)):
            for rel in lista:
                if rel.endswith(".parquet"):
                    tabla(corrida / rel)
                else:
                    escribir(corrida / rel, "clave,valor\nprueba,1\n")
            volcar(corrida / "manifest.json", {"prueba": True})
        contrato = {"columnas": {"motor": {"x": {"bloque": "F0", "tipo": "double"}}}}
        volcar(self.f0 / "contrato_disponibilidad.json", contrato)
        bloques = hashlib.sha256(json.dumps({"motor": {"x": "F0"}}, sort_keys=True).encode()).hexdigest()
        # componentes guardados para el modo mezcla
        guardados = self.s1 / "Modelos_claude"
        for rel in ("comp/v24.parquet", "comp/prediccion_2025.parquet"):
            escribir(guardados / "runs" / rel, (self.ref / rel).read_bytes(), binario=True)
        mezcla = {}
        for line in ("motor", "buildings", "contents"):
            p = guardados / "insumos" / f"exposicion_{line}.parquet"
            tabla(p, 0.5)
            mezcla[f"insumos/exposicion_{line}.parquet"] = huellas(p)
        # receta sintética y huellas esperadas
        self.receta = {"nombre": "receta de prueba", "version": "prueba",
                       "entradas": {"archivos": ENTRADAS},
                       "objetivos": {"S30": {"nodo": "mezcla_final", "csv": "final/final.csv", "sha256": sha256_bytes(self.ref / "final/final.csv")}},
                       "nodos": [
                           {"id": "comp", "etapa": "produccion", "linea": "prueba", "script": "emisor.py", "args": ["comp"], "requiere": [],
                            "salidas": ["comp/v24.parquet", "comp/prediccion_2025.parquet"], "verificar": ["comp/v24.parquet", "comp/prediccion_2025.parquet"],
                            "minutos_ref": 0},
                           {"id": "mezcla_final", "etapa": "mezcla", "linea": "prueba", "script": "emisor.py", "args": ["mezcla"], "requiere": ["comp"],
                            "salidas": ["final/final.csv", "final/prediccion_2025.parquet"], "verificar": ["final/final.csv", "final/prediccion_2025.parquet"],
                            "minutos_ref": 0}]}
        self.esperadas = {"creado_utc": utc(), "origenes": [], "semana1": str(self.s1), "faltan": [],
                          "entradas": {rel: huellas(self.s1 / rel) for rel in ENTRADAS},
                          "salidas": {rel: huellas(self.ref / rel) for rel in ("comp/v24.parquet", "comp/prediccion_2025.parquet", "final/final.csv", "final/prediccion_2025.parquet")},
                          "mezcla": mezcla,
                          "datos": {"originales": originales, "capa": capa_h, "decisiones": decisiones,
                                    "bases": {rel: huellas(self.bases / rel) for rel in BASES},
                                    "f0": {rel: huellas(self.f0 / rel) for rel in F0}, "f0_contrato_bloques": bloques}}

    def work_completo(self):
        shutil.copytree(self.ref, self.work)

    def escribir_receta(self):
        volcar(self.p / "receta" / "receta.json", self.receta)
        volcar(self.p / "receta" / "huellas_esperadas.json", self.esperadas)

    def marcas_presentes(self):
        return sorted(p.name for p in self.marcas.iterdir())


def correr(caso: Caso, modo: str, extra=(), salida: Path = None):
    caso.escribir_receta()
    orden = [sys.executable, str(caso.p / "reproducir.py"), modo, "--objetivo=S30", f"--semana1={caso.s1}", f"--trabajo={caso.w}",
             f"--originales={caso.raw}", f"--decisiones={caso.dec}", *extra]
    env = dict(os.environ, PRUEBA_MARCAS=str(caso.marcas), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", **caso.env)
    t0 = time.time()
    r = subprocess.run(orden, cwd=str(caso.raiz), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if salida:
        escribir(salida / "registros" / f"{caso.codigo}.stdout.txt", r.stdout)
        escribir(salida / "registros" / f"{caso.codigo}.stderr.txt", r.stderr)
    return {"orden": orden[2:], "rc": r.returncode, "segundos": round(time.time() - t0, 2),
            "ultima_linea": (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or [""])[-1][:300]}


def truncar(p: Path):
    b = p.read_bytes()
    p.write_bytes(b[: len(b) // 2])


def quitar(p: Path):
    p.unlink()


CASOS = []


def caso(codigo, nombre, modo, esperado, preparar=None, extra=(), comprobar=None, work=True):
    """esperado: 0 (éxito), 3 (diferencias toleradas) o "≠0" (cualquier código distinto de cero)."""
    CASOS.append({"codigo": codigo, "nombre": nombre, "modo": modo, "esperado": esperado, "preparar": preparar, "extra": tuple(extra),
                  "comprobar": comprobar, "work": work})


def sin_emisor(c: Caso):
    return not any(m.startswith("emisor_") for m in c.marcas_presentes())


def sin_mezcla(c: Caso):
    return "emisor_mezcla.txt" not in c.marcas_presentes()


def registro(c: Caso):
    p = c.w / "registro.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


# Casos nominales: código 0
caso("N01", "datos: capa, bases y F0 en caché coinciden", "datos", 0, work=False)
caso("N02", "todo: datos en caché y los dos nodos emitidos correctamente", "todo", 0, work=False,
     comprobar=lambda c: c.marcas_presentes() == ["emisor_comp.txt", "emisor_mezcla.txt"] and registro(c)[-1]["estado"] == "igual")
caso("N03", "verificar: carpeta de trabajo completa e igual", "verificar", 0)
caso("N04", "componentes: reanudar con todas las salidas presentes y verificadas", "componentes", 0,
     comprobar=lambda c: sin_emisor(c) and [r.get("estado") for r in registro(c) if r.get("nodo")] == ["reanudado_verificado"] * 2)
caso("N05", "componentes: carpeta de trabajo vacía, los dos nodos se emiten y coinciden", "componentes", 0, work=False,
     comprobar=lambda c: c.marcas_presentes() == ["emisor_comp.txt", "emisor_mezcla.txt"])
caso("N06", "verificar: Parquet intermedio con el mismo contenido y bytes distintos", "verificar", 0,
     preparar=lambda c: tabla(c.work / "comp" / "v24.parquet", compresion="none"))
caso("N07", "mezcla: componentes guardados e insumos de exposición verificados; mezcla emitida", "mezcla", 0, work=False,
     comprobar=lambda c: c.marcas_presentes() == ["emisor_mezcla.txt"] and (c.work / "feat_motor.parquet").is_file())
caso("N08", "componentes --relanzar-parciales: una salida parcial se aparta y el nodo se repite", "componentes", 0,
     preparar=lambda c: quitar(c.work / "comp" / "prediccion_2025.parquet"), extra=("--relanzar-parciales",),
     comprobar=lambda c: any(p.name.startswith("v24.parquet.parcial_") for p in (c.work / "comp").iterdir())
     and "emisor_comp.txt" in c.marcas_presentes() and any(r.get("estado") == "parciales_apartadas" for r in registro(c)))
caso("N09", "componentes --solo=comp: solo ese nodo; el objetivo no se construye y se declara", "componentes", 0, work=False,
     extra=("--solo=comp",), comprobar=lambda c: sin_mezcla(c) and registro(c)[-1]["objetivos_no_construidos"] == ["S30"])

# Casos adversos: código distinto de 0
caso("A01", "datos: un original con SHA-256 distinto", "datos", "≠0", work=False, preparar=lambda c: tabla(c.raw / "claims.parquet", 9.0))
caso("A02", "datos: una tabla de la capa con SHA-256 distinto", "datos", "≠0", work=False,
     preparar=lambda c: tabla(c.s1 / "Limpieza" / "runs" / PREAUDIT / "data" / "claims.parquet", 9.0))
caso("A03", "datos: una base requerida con contenido distinto", "datos", "≠0", work=False,
     preparar=lambda c: tabla(c.bases / "tables" / "t0_por_row_id.parquet", 9.0))
caso("A04", "datos: una tabla F0 con contenido distinto", "datos", "≠0", work=False, preparar=lambda c: tabla(c.f0 / "tables" / "f0_motor.parquet", 9.0))
caso("A05", "datos: bloques del contrato F0 distintos", "datos", "≠0", work=False,
     preparar=lambda c: volcar(c.f0 / "contrato_disponibilidad.json", {"columnas": {"motor": {"x": {"bloque": "F3"}}}}))
caso("A06", "datos: la copia local de una decisión congelada cambió", "datos", "≠0", work=False, preparar=lambda c: tabla(c.s1 / DECISIONES[0], 9.0))
caso("A07", "datos: la fuente de una decisión congelada cambió", "datos", "≠0", work=False, preparar=lambda c: tabla(c.dec / DECISIONES[0], 9.0))
caso("A08", "datos: falta la huella esperada de los bloques del contrato", "datos", "≠0", work=False,
     preparar=lambda c: c.esperadas["datos"].pop("f0_contrato_bloques"))
caso("A09", "todo: bases distintas; se detiene antes de ejecutar ningún nodo", "todo", "≠0", work=False,
     preparar=lambda c: tabla(c.bases / "tables" / "t0_por_row_id.parquet", 9.0), comprobar=sin_emisor)
caso("A10", "verificar: falta el CSV final", "verificar", "≠0", preparar=lambda c: quitar(c.work / "final" / "final.csv"))
caso("A11", "verificar: un componente con contenido distinto", "verificar", "≠0", preparar=lambda c: tabla(c.work / "comp" / "v24.parquet", 9.0))
caso("A12", "verificar: una salida sin huella esperada en la receta", "verificar", "≠0", preparar=lambda c: c.esperadas["salidas"].pop("comp/v24.parquet"))
caso("A13", "verificar: CSV final con el mismo contenido normalizado y bytes distintos", "verificar", "≠0",
     preparar=lambda c: escribir(c.work / "final" / "final.csv", (c.work / "final" / "final.csv").read_bytes().replace(b"\n", b"\r\n"), binario=True))
caso("A14", "verificar: falta receta/huellas_esperadas.json", "verificar", "≠0",
     preparar=lambda c: setattr(c, "escribir_receta", lambda: volcar(c.p / "receta" / "receta.json", c.receta)))
caso("A15", "verificar: un Parquet truncado (ilegible)", "verificar", "≠0", preparar=lambda c: truncar(c.work / "comp" / "prediccion_2025.parquet"))
caso("A16", "verificar: la sección salidas de las huellas esperadas está vacía", "verificar", "≠0", preparar=lambda c: c.esperadas.update(salidas={}))
caso("A17", "componentes: reanudar con un componente cambiado; la mezcla no se ejecuta", "componentes", "≠0",
     preparar=lambda c: tabla(c.work / "comp" / "v24.parquet", 9.0), comprobar=sin_emisor)
caso("A18", "componentes: salida parcial sin --relanzar-parciales; el nodo no se repite", "componentes", "≠0",
     preparar=lambda c: quitar(c.work / "comp" / "prediccion_2025.parquet"), comprobar=sin_emisor)
caso("A19", "componentes: reanudar con una salida sin huella esperada", "componentes", "≠0",
     preparar=lambda c: c.esperadas["salidas"].pop("comp/prediccion_2025.parquet"), comprobar=sin_emisor)
caso("A20", "componentes: Parquet truncado al reanudar", "componentes", "≠0",
     preparar=lambda c: truncar(c.work / "comp" / "v24.parquet"), comprobar=sin_emisor)
caso("A21", "componentes: falta la huella esperada de los bloques del contrato (entradas)", "componentes", "≠0", work=False,
     preparar=lambda c: c.esperadas["datos"].pop("f0_contrato_bloques"), comprobar=sin_emisor)
caso("A22", "componentes: una entrada con contenido distinto", "componentes", "≠0", work=False,
     preparar=lambda c: tabla(c.f0 / "tables" / "f0_contents.parquet", 9.0), comprobar=sin_emisor)
caso("A23", "componentes: falta una entrada", "componentes", "≠0", work=False,
     preparar=lambda c: quitar(c.s1 / "Datos" / "weather.parquet"), comprobar=sin_emisor)
caso("A24", "componentes: el nodo termina con código de error", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_COMP="falla"), comprobar=sin_mezcla)
caso("A25", "componentes: el nodo omite una salida; la mezcla no se ejecuta", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_COMP="omitir_salida"), comprobar=sin_mezcla)
caso("A26", "componentes: el nodo produce contenido distinto; la mezcla no se ejecuta", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_COMP="contenido_distinto"), comprobar=sin_mezcla)
caso("A27", "componentes --continuar-si-difiere: contenido distinto en el componente, CSV final igual; termina con código 3", "componentes", 3,
     work=False, preparar=lambda c: c.env.update(EMISOR_VARIANTE_COMP="contenido_distinto"), extra=("--continuar-si-difiere",),
     comprobar=lambda c: "emisor_mezcla.txt" in c.marcas_presentes() and registro(c)[-1]["estado"] == "csv_iguales_con_diferencias_intermedias"
     and registro(c)[-1]["objetivos"]["S30"]["coincide"] is True and len(registro(c)[-1]["diferencias_toleradas"]) == 1)
caso("A28", "componentes --continuar-si-difiere: una salida que falta sigue deteniendo", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_COMP="omitir_salida"), extra=("--continuar-si-difiere",), comprobar=sin_mezcla)
caso("A29", "componentes: la mezcla escribe el CSV final con bytes distintos y el mismo contenido", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_MEZCLA="csv_bytes_distintos"))
caso("A30", "componentes: la mezcla escribe el CSV y el Parquet finales con contenido distinto", "componentes", "≠0", work=False,
     preparar=lambda c: c.env.update(EMISOR_VARIANTE_MEZCLA="contenido_distinto"))
caso("A31", "mezcla: un componente guardado con contenido distinto; la mezcla no se ejecuta", "mezcla", "≠0", work=False,
     preparar=lambda c: tabla(c.s1 / "Modelos_claude" / "runs" / "comp" / "v24.parquet", 9.0), comprobar=sin_emisor)
caso("A32", "mezcla: falta un componente guardado", "mezcla", "≠0", work=False,
     preparar=lambda c: quitar(c.s1 / "Modelos_claude" / "runs" / "comp" / "prediccion_2025.parquet"), comprobar=sin_emisor)
caso("A33", "mezcla: un insumo de exposición con contenido distinto", "mezcla", "≠0", work=False,
     preparar=lambda c: tabla(c.s1 / "Modelos_claude" / "insumos" / "exposicion_contents.parquet", 9.0), comprobar=sin_emisor)
caso("A34", "mezcla: el insumo de exposición no tiene huella esperada", "mezcla", "≠0", work=False,
     preparar=lambda c: c.esperadas["mezcla"].pop("insumos/exposicion_motor.parquet"), comprobar=sin_emisor)
caso("A35", "componentes --solo con un nodo que no está en la receta", "componentes", "≠0", work=False, extra=("--solo=no_existe",), comprobar=sin_emisor)
caso("A36", "componentes: carpeta --semana1 inexistente", "componentes", "≠0", work=False,
     preparar=lambda c: setattr(c, "s1", c.raiz / "no_existe"), comprobar=sin_emisor)


def referencia(base: Path) -> Path:
    """Artefactos de referencia: el emisor en su variante nominal, ejecutado una vez."""
    ref = base / "referencia"
    ref.mkdir()
    marcas = base / "marcas_referencia"
    marcas.mkdir()
    emisor = base / "emisor_referencia.py"
    escribir(emisor, EMISOR)
    for que in ("comp", "mezcla"):
        subprocess.run([sys.executable, str(emisor), que], env=dict(os.environ, MODELOS_WORK=str(ref), PRUEBA_MARCAS=str(marcas)), check=True)
    return ref


def main():
    o = {a[2:].partition("=")[0]: (a[2:].partition("=")[2] or True) for a in sys.argv[1:] if a.startswith("--")}
    inicio = datetime.now(timezone.utc)
    marca = inicio.strftime("%Y%m%dT%H%M%SZ")
    plataforma = re.sub(r"[^A-Za-z0-9]+", "_", platform.system().lower())
    salida = Path(o["salida"]).resolve() if o.get("salida") else REPO / "docs" / "controles" / f"{marca}_{plataforma}"
    base = Path(o["carpeta"]).resolve() if o.get("carpeta") else Path(tempfile.mkdtemp(prefix="controles_"))
    base.mkdir(parents=True, exist_ok=True)
    salida.mkdir(parents=True, exist_ok=True)
    texto = (REPO / "reproducir.py").read_text(encoding="utf-8")
    version = re.search(r'^VERSION = "([^"]+)"', texto, re.M).group(1)
    version_fecha = re.search(r'^VERSION_FECHA = "([^"]+)"', texto, re.M).group(1)
    ref = referencia(base)
    import numpy, pyarrow
    resultados, fallos = [], []
    for c in CASOS:
        x = Caso(base, c["codigo"], ref)
        if c["work"]:
            x.work_completo()
        if c["preparar"]:
            c["preparar"](x)
        r = correr(x, c["modo"], c["extra"], salida)
        rc_ok = (r["rc"] == 0) if c["esperado"] == 0 else ((r["rc"] == 3) if c["esperado"] == 3 else (r["rc"] != 0))
        etapas = [m for m in x.marcas_presentes() if m.startswith("etapa_")]
        comp_ok = True
        if c["comprobar"]:
            try:
                comp_ok = bool(c["comprobar"](x))
            except Exception as exc:  # una comprobación que no se puede evaluar cuenta como fallo
                comp_ok, r["comprobacion_error"] = False, f"{type(exc).__name__}: {exc}"
        ok = rc_ok and comp_ok and not etapas
        fila = {"codigo": c["codigo"], "caso": c["nombre"], "modo": c["modo"], "opciones": list(c["extra"]), "esperado": c["esperado"],
                "rc": r["rc"], "rc_conforme": rc_ok, "comprobacion_adicional": comp_ok if c["comprobar"] else None,
                "etapas_reales_invocadas": etapas, "marcas": x.marcas_presentes(), "segundos": r["segundos"], "ultima_linea": r["ultima_linea"],
                "registros": {"stdout": f"registros/{c['codigo']}.stdout.txt", "stderr": f"registros/{c['codigo']}.stderr.txt"}, "pasa": ok}
        if "comprobacion_error" in r:
            fila["comprobacion_error"] = r["comprobacion_error"]
        resultados.append(fila)
        if not ok:
            fallos.append(c["codigo"])
        print(f"[{c['codigo']}] {'pasa' if ok else 'FALLA'} rc={r['rc']} esperado={c['esperado']} {c['nombre']}", flush=True)
    resumen = {"utc": utc(), "version_reproducir": version, "version_fecha": version_fecha,
               "paquete": {rel: sha256_bytes(REPO / rel) for rel in ARCHIVOS_PAQUETE},
               "entorno": {"python": platform.python_version(), "sistema": platform.platform(), "numpy": numpy.__version__, "pyarrow": pyarrow.__version__},
               "casos": len(resultados), "nominales": sum(1 for c in CASOS if c["esperado"] == 0), "adversos": sum(1 for c in CASOS if c["esperado"] != 0),
               "pasan": len(resultados) - len(fallos), "fallan": fallos, "etapas_reales_invocadas": sum(len(f["etapas_reales_invocadas"]) for f in resultados),
               "todos_pasan": not fallos, "segundos": round((datetime.now(timezone.utc) - inicio).total_seconds(), 1), "carpeta_temporal": str(base),
               "alcance": "Paquetes de prueba aislados con receta sintética de dos nodos y archivos de dos filas; ningún dato del concurso, "
                          "ningún modelo y ninguna etapa real de datos (los scripts de N62, D67 y D68 están sustituidos por guardias que fallan si se invocan).",
               "resultados": resultados}
    volcar(salida / "resultado.json", resumen)
    print(json.dumps({k: resumen[k] for k in ("version_reproducir", "casos", "nominales", "adversos", "pasan", "fallan", "todos_pasan", "segundos")}, ensure_ascii=False))
    print(f"Evidencia en {salida}")
    if not o.get("conservar"):
        shutil.rmtree(base, ignore_errors=True)
    raise SystemExit(0 if not fallos else 1)


if __name__ == "__main__":
    main()
