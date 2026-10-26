"""Comprueba que cada cifra de INFORME.md sale de los JSON de resultados/ y aparece tal cual en el texto.

Lee cifras_informe.json (misma carpeta). Cada entrada trae la ruta en un JSON de resultados/ (o un cálculo de CALCULOS sobre
esas rutas), el formato con el que se escribe y un fragmento literal del informe. El verificador recalcula el valor desde los
JSON, lo formatea, exige que coincida con `valor` y que `contexto` aparezca en INFORME.md y contenga `valor`. Las entradas
`literales` son cifras citadas de otros documentos: se comprueba que aparecen, con su fuente declarada. Las entradas `huella`
comparan el SHA-256 de un archivo de la carpeta. Escribe verificacion_informe.json.

Uso: python3 verificar_informe.py            (desde cualquier carpeta; usa la del script)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
FUENTES = {"datos": "datos.json", "a": "parte_a.json", "b": "parte_b.json", "c": "parte_c.json", "d": "parte_d.json", "e": "parte_e.json",
           "f": "parte_f.json", "g": "parte_g.json", "ctx": "contexto.json", "cur": "curvas.json"}
LINEAS = ["motor", "buildings", "contents"]


def cargar(base: pathlib.Path):
    return {k: json.loads((base / "resultados" / v).read_text(encoding="utf-8")) for k, v in FUENTES.items()}


def get(ev, ruta: str):
    partes = ruta.split("/")
    cur = ev[partes[0]]
    for k in partes[1:]:
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur


def arg(ev, a: str):
    a = a.strip()
    if a.startswith("'") and a.endswith("'"):
        return a[1:-1]
    try:
        return float(a)
    except ValueError:
        return get(ev, a)


def _e1(ev, campo, f):
    vals = [v[campo] for l in LINEAS for k, v in ev["e"]["E1_emergente"][l].items() if k.startswith("b_")]
    return f(vals)


def _e3(ev, ramo, campo):
    vals = [g[campo] for k, v in ev["e"]["E3_factores"].items() if ramo in ("todos", k.split("|")[0]) for g in v.values() if g[campo] is not None]
    return max(vals)


def _umbral_txt(u):
    """Intervalo de quiebre en texto: sin límite por un lado si la rejilla no cruza el 1 % por ese lado."""
    if u[0] is None and u[1] is None:
        return "cualquiera de 0 a 20"
    if u[0] is None:
        return "hasta " + fmt(u[1], "dec3")
    if u[1] is None:
        return "desde " + fmt(u[0], "dec3")
    return fmt(u[0], "dec3") + " a " + fmt(u[1], "dec3")


def _elas(ev, f):
    el = ev["d"]["elasticidad_analitica"]
    return f(el[l][c] for l in LINEAS for c in (f"{l}_0", f"{l}_1"))


CALCULOS = {
    "suma": lambda ev, *a: sum(arg(ev, x) for x in a),
    "resta": lambda ev, x, y: arg(ev, x) - arg(ev, y),
    "razon": lambda ev, x, y: arg(ev, x) / arg(ev, y),
    "producto": lambda ev, x, y: arg(ev, x) * arg(ev, y),
    "uno_menos": lambda ev, x: 1 - arg(ev, x),
    "menos_uno": lambda ev, x: arg(ev, x) - 1,
    "abs": lambda ev, x: abs(arg(ev, x)),
    "neg": lambda ev, x: -arg(ev, x),
    "max_abs": lambda ev, *a: max(abs(arg(ev, x)) for x in a),
    "min": lambda ev, *a: min(arg(ev, x) for x in a),
    "max": lambda ev, *a: max(arg(ev, x) for x in a),
    # cambio relativo de T0 del ramo si la reserva de caso de sus abiertos se multiplica por b
    "cambio_T0": lambda ev, ramo, b: (arg(ev, b) - 1) * sum(ev["a"]["por_ramo_anio"][f"{arg(ev, ramo)}_{y}"]["reserva"] for y in (2023, 2024))
    / sum(ev["a"]["por_ramo_anio"][f"{arg(ev, ramo)}_{y}"]["T0"] for y in (2023, 2024)),
    "T0_ramo": lambda ev, ramo: sum(ev["a"]["por_ramo_anio"][f"{arg(ev, ramo)}_{y}"]["T0"] for y in (2023, 2024)),
    "reserva_ramo": lambda ev, ramo: sum(ev["a"]["por_ramo_anio"][f"{arg(ev, ramo)}_{y}"]["reserva"] for y in (2023, 2024)),
    "e1_max_abs_delta_a": lambda ev: _e1(ev, "delta_a", lambda v: max(abs(x) for x in v)),
    "e1_max_coste": lambda ev: _e1(ev, "coste_D2_con_T0", max),
    "e3_max": lambda ev, ramo, campo: _e3(ev, arg(ev, ramo), arg(ev, campo)),
    "elasticidad_min": lambda ev: _elas(ev, min),
    "elasticidad_max": lambda ev: _elas(ev, max),
    "contar_abiertos_tardios": lambda ev, k: round(arg(ev, k + "/tardios") * arg(ev, k + "/pct_abiertos_tardios")),
    "hora": lambda ev, x: arg(ev, x)[11:19],
    "umbral_txt": lambda ev, x: _umbral_txt(arg(ev, x)),
    "clase": lambda ev, x: {"acotado": "acotado", "incertidumbre_material": "incertidumbre material",
                            "indicio_de_desvio_material": "indicio de desvío material", "sin_estimacion": "sin estimación"}[arg(ev, x)],
    # intervalos al 90 % de k_e (coste) y de k en número de la parte C, y cuántos excluyen el 1
    "intervalos_k": lambda ev: sum(1 for v in ev["c"]["k"].values() for c in ("ic90_k_e", "ic90_k_conteos") if v[c][0] is not None),
    "intervalos_k_fuera": lambda ev: sum(1 for v in ev["c"]["k"].values() for c in ("ic90_k_e", "ic90_k_conteos")
                                         if v[c][0] is not None and (v[c][0] > 1 or v[c][1] < 1)),
}


def calcular(ev, expr: str):
    nombre, resto = expr[1:].split("(", 1)
    args = [x for x in resto[:-1].split(", ")] if resto[:-1].strip() else []
    return CALCULOS[nombre](ev, *args)


def num(x: float, d: int) -> str:
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" + s) if (x < 0 and float(s.replace(".", "").replace(",", ".")) != 0) else s


SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def fmt(v, f: str) -> str:
    if f.startswith("u"):  # umbral: None significa que no hay cruce en la rejilla por ese lado
        return "sin cruce" if v is None else fmt(v, f[1:])
    if f.startswith("sci"):
        mant, ex = f"{v:.{int(f[3:])}e}".split("e")
        return mant.replace(".", ",").replace("-", "−") + " × 10" + str(int(ex)).translate(SUP)
    if f == "int":
        return num(round(v), 0)
    if f.startswith("sdec"):
        d = int(f[4:]); s = num(v, d)
        return s if s.startswith("−") or float(s.replace(".", "").replace(",", ".")) == 0 else "+" + s
    if f.startswith("dec"):
        return num(v, int(f[3:]))
    if f.startswith("spct"):
        d = int(f[4:]); s = num(v * 100, d)
        return s if s.startswith("−") or float(s.replace(".", "").replace(",", ".")) == 0 else "+" + s
    if f.startswith("apct"):
        return num(abs(v) * 100, int(f[4:]))
    if f.startswith("pct"):
        return num(v * 100, int(f[3:]))
    if f.startswith("mill"):
        return num(v / 1e6, int(f[4:]))
    if f == "sha":
        return f"{v[:8]}…{v[-4:]}"
    if f == "raw":
        return str(v)
    raise ValueError(f)


def valor(ev, c):
    if "calculo" in c:
        return calcular(ev, c["calculo"])
    return get(ev, c["ruta"])


def main():
    spec = json.loads((HERE / "cifras_informe.json").read_text(encoding="utf-8"))
    ev = cargar(HERE)
    texto = (HERE / spec["documento"]).read_text(encoding="utf-8")
    res, fallos = [], 0
    for c in spec["cifras"]:
        try:
            v = fmt(valor(ev, c), c["formato"])
            ok = (v == c["valor"]) and (c["contexto"] in texto) and (c["valor"] in c["contexto"])
            motivo = "" if ok else ("valor" if v != c["valor"] else ("contexto ausente" if c["contexto"] not in texto else "valor fuera del contexto"))
        except Exception as e:  # noqa: BLE001
            v, ok, motivo = None, False, f"error: {e!r}"
        fallos += not ok
        res.append({"id": c["id"], "ok": ok, "esperado": c["valor"], "calculado": v, "motivo": motivo})
    for c in spec.get("literales", []):
        ok = c["texto"] in texto
        fallos += not ok
        res.append({"id": c["id"], "ok": ok, "literal": c["texto"], "fuente": c["fuente"], "motivo": "" if ok else "literal ausente"})
    for c in spec.get("huellas", []):
        h = hashlib.sha256((HERE / c["archivo"]).read_bytes()).hexdigest()
        ok = (h == c["sha256"]) and (fmt(h, "sha") in texto)
        fallos += not ok
        res.append({"id": c["id"], "ok": ok, "archivo": c["archivo"], "sha256": h, "motivo": "" if ok else "huella distinta o ausente del texto"})
    out = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "documento": spec["documento"],
           "documento_sha256": hashlib.sha256((HERE / spec["documento"]).read_bytes()).hexdigest(),
           "comprobadas": len(res), "fallos": fallos, "detalle": res}
    (HERE / "verificacion_informe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(res)} comprobaciones, {fallos} fallos")
    for x in res:
        if not x["ok"]:
            print("FALLO", x)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
