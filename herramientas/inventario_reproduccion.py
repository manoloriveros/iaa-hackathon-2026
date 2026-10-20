"""Inventario de solo lectura para REP-01 a REP-04 (COD-20261019-113): qué guarda cada nodo de la receta y qué haría
falta para rehacerlo sin ajustar modelos.

No ejecuta ningún nodo, no carga modelos y no escribe fuera de --salida. Para cada nodo de receta/receta.json:
  - localiza cada salida declarada en las corridas guardadas (mismo criterio que herramientas/inventario.py, más
    Envios/archivos para los CSV) y compara su SHA-256 con receta/huellas_esperadas.json;
  - lista los archivos de parámetros y registros de la corrida (resumen.json, manifest.json, config.json, log.txt) y los
    registros históricos que cita la receta en «evidencia» (colaN.sh, log_*.txt), con SHA-256;
  - clasifica el script del nodo por lo que hace (ajuste estocástico, estimación determinista, aritmética sobre
    predicciones guardadas) y busca en su código llamadas que persistan un modelo ajustado;
  - deduce si el nodo puede rehacerse sin ajustar nada a partir de lo guardado.
Uso: python herramientas/inventario_reproduccion.py --semana1=<carpeta Semana 1> --salida=<json>
Autor: Claude (línea principal), 19 de octubre de 2026, CLA-20261019-004.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
sys.path.insert(0, str(AQUI))
from inventario import localizar  # noqa: E402

# Qué hace cada script, leído en su código (src/modelos, src/linea_b). «ajuste» = entrena con semilla o parada temprana;
# «estimacion» = IRLS determinista sin semilla; «aritmetica» = combina predicciones guardadas sin estimar nada.
TIPO = {
    "src/modelos/construir_variables.py": ("transformacion", "construcción determinista de variables desde F0 y bases"),
    "src/modelos/evaluar.py": ("ajuste", "LightGBM Tweedie con parada temprana en la mitad de calibración de 2023 (V23)"),
    "src/modelos/cat_experimento.py": ("ajuste", "CatBoost Tweedie con parada temprana (V23)"),
    "src/modelos/produccion.py": ("ajuste", "LightGBM Tweedie, rondas fijadas desde V23, V24 y 2025 con varias semillas"),
    "src/modelos/cat_produccion.py": ("ajuste", "CatBoost Tweedie, iteraciones fijadas desde V23, V24 y 2025"),
    "src/modelos/cat_frecsev.py": ("ajuste", "CatBoost Poisson por peligro por severidad media; guarda partes por peligro"),
    "src/modelos/frecsev2.py": ("ajuste", "LightGBM Poisson por peligro; guarda partes por peligro"),
    "src/modelos/mlp_tweedie.py": ("ajuste", "red Tweedie en torch con QuantileTransformer ajustado en entrenamiento"),
    "src/modelos/severidad_cfs.py": ("estimacion", "GLM gamma por peligro (IRLS) sobre partes de frecuencia guardadas"),
    "src/modelos/severidad_cfs3.py": ("estimacion", "GLM gamma con ridge por peligro (IRLS) sobre partes guardadas"),
    "src/linea_b/severidad_tendencia.py": ("estimacion", "GLM gamma por peligro (IRLS) más factor de tendencia de severidad"),
    "src/modelos/combinar_semillas.py": ("aritmetica", "media ponderada por semillas de predicciones guardadas"),
    "src/modelos/mezcla3.py": ("aritmetica", "mezcla, forma y factor de año siguiente calculados sobre predicciones guardadas"),
    "src/linea_b/mezcla3_b.py": ("aritmetica", "mezcla3 con la regla de nivel s17 extendida a las corridas B"),
}
PERSISTE_MODELO = re.compile(r"save_model|joblib|pickle|torch\.save|\.cbm|booster_\.|model_file|to_json\(\s*model")
REGISTRO = re.compile(r"[\w\-]+\.(?:sh|txt)\b")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ficha(p: Path, base: Path) -> dict:
    d = {"ruta": p.relative_to(base).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
    if p.suffix == ".npz":
        with zipfile.ZipFile(p) as z:
            d["claves_npz"] = sorted(n[:-4] for n in z.namelist())
    return d


def main():
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    s1 = Path(opts["semana1"]).resolve()
    base = s1.parent.parent  # raíz del proyecto (C:\dev\Hakaton)
    receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    esp = json.loads((REPO / "receta" / "huellas_esperadas.json").read_text(encoding="utf-8"))
    origenes = [s1 / "Modelos_claude", s1 / "Modelos_claude_b"]
    experimentos = [s1 / "Modelos_claude" / "experimentos", s1 / "Modelos_claude_b" / "experimentos"]
    codigo = {}
    for script in TIPO:
        txt = (REPO / script).read_text(encoding="utf-8")
        codigo[script] = sorted(set(PERSISTE_MODELO.findall(txt)))
    nodos = []
    for n in receta["nodos"]:
        tipo, desc = TIPO[n["script"]]
        salidas = []
        for rel in n["salidas"]:
            p = localizar(rel, origenes)
            if p is None and rel.endswith(".csv"):
                c = s1 / "Envios" / "archivos" / Path(rel).name
                p = c if c.is_file() else None
            e = esp["salidas"].get(rel)
            r = {"salida": rel, "verificada_por_receta": rel in n["verificar"], "sha256_esperado": e["sha256"] if e else None}
            if p is None:
                r["estado"] = "ausente_en_equipo"
            else:
                f = ficha(p, base)
                r.update(f, estado="coincide" if e and f["sha256"] == e["sha256"] else ("sin_huella_esperada" if not e else "difiere"))
            salidas.append(r)
        # carpeta de la corrida (si el nodo escribe en runs/<id>/) y archivos que no son salidas declaradas
        carpeta = next((o / "runs" / n["id"] for o in origenes if (o / "runs" / n["id"]).is_dir()), None)
        nombres_salida = {Path(s).name for s in n["salidas"]}
        parametros = [ficha(p, base) for p in sorted(carpeta.iterdir()) if p.is_file() and p.name not in nombres_salida] if carpeta else []
        registros = []
        for nombre in sorted(set(REGISTRO.findall(n.get("evidencia", "")))):
            hall = next((d / nombre for d in experimentos + [s1 / "Modelos_claude", s1 / "Modelos_claude_b"] if (d / nombre).is_file()), None)
            registros.append(ficha(hall, base) if hall else {"ruta": nombre, "estado": "no_encontrado"})
        presentes = sum(s["estado"] == "coincide" for s in salidas if s["verificada_por_receta"])
        verif = sum(s["verificada_por_receta"] for s in salidas)
        sin_ajuste = tipo in ("transformacion", "aritmetica")
        nodos.append({
            "id": n["id"], "etapa": n["etapa"], "script": n["script"], "args": n["args"], "requiere": n["requiere"],
            "objetivos": n.get("objetivos", []), "tipo": tipo, "que_hace": desc,
            "modelo_ajustado_persistido": False if tipo in ("ajuste", "estimacion") else None,
            "llamadas_que_persisten_modelo_en_codigo": codigo[n["script"]],
            "salidas": salidas, "verificadas_presentes_y_coinciden": f"{presentes}/{verif}",
            "parametros_y_registros_de_la_corrida": parametros, "registros_historicos_citados": registros,
            "reconstruible_sin_ajuste": sin_ajuste,
            "motivo": ("transformación determinista; ya reproducida en contenido por «reproducir.py datos»" if tipo == "transformacion" else
                       "aritmética sobre predicciones guardadas; repetida con los CSV exactos («reproducir.py mezcla»)" if tipo == "aritmetica" else
                       "IRLS determinista: rehacerlo es estimar de nuevo; los coeficientes no se guardaron a precisión completa" if tipo == "estimacion" else
                       "entrenamiento con semilla o parada temprana; ningún modelo ajustado se guardó, solo sus predicciones"),
        })
    out = {
        "autor": "Claude (línea principal)", "aporte": "CLA-20261019-004", "responde_a": ["COD-20261019-113"],
        "creado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "alcance": "solo lectura: localizar, calcular SHA-256 y leer código; cero entrenamientos, inferencias o mezclas",
        "receta_sha256": sha(REPO / "receta" / "receta.json"),
        "huellas_esperadas_sha256": sha(REPO / "receta" / "huellas_esperadas.json"),
        "herramienta_sha256": sha(Path(__file__)),
        "nodos": nodos,
    }
    tot = [s for n in nodos for s in n["salidas"]]
    out["resumen"] = {
        "nodos": len(nodos),
        "por_tipo": {t: sum(n["tipo"] == t for n in nodos) for t in ("transformacion", "ajuste", "estimacion", "aritmetica")},
        "salidas_declaradas": len(tot),
        "salidas_con_huella_esperada": sum(s["sha256_esperado"] is not None for s in tot),
        "salidas_verificadas_por_receta": sum(s["verificada_por_receta"] for s in tot),
        "presentes_y_coinciden": sum(s["estado"] == "coincide" for s in tot),
        "ausentes_en_equipo": [s["salida"] for s in tot if s["estado"] == "ausente_en_equipo"],
        "difieren": [s["salida"] for s in tot if s["estado"] == "difiere"],
        "modelos_ajustados_persistidos": 0,
        "nodos_reconstruibles_sin_ajuste": [n["id"] for n in nodos if n["reconstruible_sin_ajuste"]],
    }
    Path(opts["salida"]).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["resumen"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
