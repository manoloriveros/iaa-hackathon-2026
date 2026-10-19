"""Construye el expediente de entrega desde evidencia existente. No ajusta modelos.

python herramientas/actualizar_revision.py --raiz C:/dev/Hakaton
Requiere pyarrow solo para verificar los CSV contra sample_submission.
Los datos por fila y las copias de CSV se guardan exclusivamente en privado/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def leer(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def guardar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raiz", type=Path, default=REPO.parents[1])
    args = ap.parse_args()
    raiz = args.raiz.resolve()
    rutas = leer(raiz / "RUTAS_PROYECTO.json")
    semana = (raiz / rutas["week_1_data"]).parent
    now = datetime.now(timezone.utc)
    marca = now.strftime("%Y%m%dT%H%M%SZ")
    ev = REPO / "docs/evidencia"
    fuentes = []

    def fuente(nombre, p):
        p = Path(p)
        d = leer(p)
        fuentes.append({"nombre": nombre, "ruta_original": p.relative_to(raiz).as_posix(),
                        "sha256": sha(p), "bytes": p.stat().st_size,
                        "modificado_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()})
        return d

    docrun = semana / "Documentacion_datos/runs/dossier_20261017T013104Z_47591209"
    facts = fuente("Dossier de datos, corte D61 (histórico)", docrun / "facts.json")
    dictionary = fuente("Diccionario 107, corte D61", docrun / "dictionary_107.json")
    profiles = fuente("Perfiles originales D30", semana / "Analisis/runs/eda_20261016T165629Z_ab2a8365/profiles.json")
    base = fuente("Índice de capa preparada activa", semana / "Limpieza/current_dataset.json")
    bases = fuente("Bases actuariales D67", semana / "Bases_actuariales_claude/current_run.json")
    f0 = fuente("Matriz F0 D68", semana / "Matriz_F0_claude/current_run.json")
    contract = fuente("Contrato F0 por columna", raiz / f0["workspace_relative_run"] / "contrato_disponibilidad.json")
    registry = fuente("Registro histórico de candidatos y envíos", semana / "Envios/registro_envios.json")
    codex = semana / "Modelado_codex/nocturna_20261017_N01"
    receipt30 = fuente("Recibo Kaggle S30", codex / "submission_receipt_S30.json")
    receipt22 = fuente("Recibo Kaggle S22", codex / "submission_receipt_S22.json")
    delivery30 = fuente("Entrega y composición S30", semana / "Envios/S30_claude_b_entrega_codex.json")
    delivery22 = fuente("Entrega y composición S22", semana / "Envios/S22_claude_entrega_codex.json")
    n62 = fuente("Reconstrucción de base N62, histórica", codex / "base_rebuild_N62/verification.json")
    cycle = fuente("Último ciclo de validación recibido", semana / "Validacion_enjambre/ultimo_ciclo.json")
    hall = fuente("Hallazgos del ciclo recibido", raiz / cycle["findings_registry"])
    recipe = fuente("Receta de reproducción", REPO / "receta/receta.json")
    spec = fuente("Pesos S30", REPO / "receta/especificaciones/spec_s30.json")
    oficial = fuente("Reglas y metadatos consultados en vivo", REPO / "docs/fuentes/reglas_kaggle_20261019.json")

    # Copias documentales, sin reescribir las fuentes históricas.
    copiar_docs = {
        "metodologia_actuarial_historica.md": semana / "Modelado/METODOLOGIA_ACTUARIAL.md",
        "plan_pruebas_D67.md": semana / "Bases_actuariales_claude/PLAN_PRUEBAS.md",
        "experimentos_linea_principal.md": semana / "Modelos_claude/README.md",
        "experimentos_linea_b.md": semana / "Modelos_claude_b/README.md",
        "documentacion_datos_D61.md": docrun / "DOCUMENTACION_DATOS.md",
        "practicas_IAA.md": raiz / "Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md",
    }
    for nombre, p in copiar_docs.items():
        dst = ev / nombre
        dst.parent.mkdir(parents=True, exist_ok=True)
        contenido = p.read_text(encoding="utf-8-sig")
        contenido, n_ids = re.subn(r"\b[MCBPA]\d{7,12}\b", "[identificador sintético omitido]", contenido)
        dst.write_text(contenido, encoding="utf-8")
        fuentes.append({"nombre": nombre, "ruta_original": p.relative_to(raiz).as_posix(), "sha256": sha(p),
                        "copia": dst.relative_to(REPO).as_posix(), "sha256_copia": sha(dst), "identificadores_omitidos": n_ids,
                        "tipo": "documentación histórica con corte propio; copia sin identificadores individuales"})

    # Perfil por variable: se eliminan categorías individuales de identificadores y nombres.
    tabla_perfiles = []
    por_columna = {}
    for tabla in profiles:
        for c in tabla["columns"]:
            cc = {k: c[k] for k in ("name", "dtype", "missing", "missing_pct", "unique", "kind", "quantiles", "mean", "std", "nonfinite", "zeros", "negative", "histogram") if k in c}
            cc["tabla"] = tabla["name"]
            if not c["name"].endswith("_id") and c["name"] not in {"surname", "email_domain", "make_model", "campaign_code", "branch_id"}:
                cc["categorias_agregadas"] = c.get("counts", [])
            tabla_perfiles.append(cc)
            por_columna.setdefault(c["name"], []).append(cc)

    # Verificación nueva de entrega; lectura de columnas, sin producir estimaciones.
    import pyarrow.parquet as pq
    sample = pq.read_table(semana / "Datos/sample_submission.parquet", columns=["row_id"])["row_id"].to_pylist()
    test_ids = []
    rows_por_ramo = {}
    for ramo in ("motor", "buildings", "contents"):
        ids = pq.read_table(semana / f"Datos/test_{ramo}.parquet", columns=["row_id"])["row_id"].to_pylist()
        rows_por_ramo[ramo] = len(ids)
        test_ids.extend(ids)
    sample_ok = len(sample) == len(set(sample)) and set(sample) == set(test_ids) and len(test_ids) == len(set(test_ids))
    preflight = []
    for nombre, delivery, receipt in (("S30", delivery30, receipt30), ("S22", delivery22, receipt22)):
        p = raiz / delivery["archivo"]
        ids, values = [], []
        with p.open(encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            columnas = rd.fieldnames
            for x in rd:
                ids.append(x["row_id"])
                values.append(float(x["prediction"]))
        checks = {"columnas_exactas": columnas == ["row_id", "prediction"], "filas": len(ids) == len(sample),
                  "ids_unicos": len(ids) == len(set(ids)), "ids_y_orden_sample": ids == sample,
                  "cobertura_tres_test": sample_ok and set(ids) == set(test_ids),
                  "valores_finitos_no_negativos": all(math.isfinite(v) and v >= 0 for v in values),
                  "predicciones_positivas": all(v > 0 for v in values),
                  "sha_entrega": sha(p) == delivery["sha256"], "sha_recibo": sha(p) == receipt["sha256"],
                  "recibo_puntuado": receipt.get("kaggle_status") == "COMPLETE"}
        dest = REPO / "privado/predicciones" / (nombre + ".csv")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and sha(dest) != sha(p):
            raise RuntimeError(f"La copia de entrega {dest} cambió; revisar antes de sustituir")
        if not dest.exists():
            shutil.copyfile(p, dest)
        preflight.append({"candidato": nombre, "utc": now.isoformat(), "archivo_origen": p.relative_to(raiz).as_posix(),
                          "copia_local": dest.relative_to(REPO).as_posix(), "sha256": sha(p), "filas": len(ids),
                          "min": min(values), "max": max(values), "total_CU": math.fsum(values),
                          "checks": checks, "pasa": all(checks.values()), "submission_id": receipt["kaggle_submission_id"],
                          "public_score": receipt["public_score"], "recibo_consultado_utc": receipt.get("retrieved_utc"),
                          "seleccion_final_manual": "No acreditada; sigue pendiente de decisión humana"})

    integridad = []
    for t in facts["raw_tables"]:
        p = semana / "Datos" / (t["table"] + ".parquet")
        actual = sha(p)
        integridad.append({"tabla": t["table"], "filas": pq.ParquetFile(p).metadata.num_rows,
                           "columnas": t["columns"], "sha256": actual, "esperado": t["sha256"],
                           "coincide": actual == t["sha256"], "bytes": p.stat().st_size})

    hallazgos = []
    for h in hall["findings"]:
        det = h.get("detalle_original", {})
        hallazgos.append({"id": h["id"], "area": h["area"], "severidad": h.get("severidad"),
                          "estado_registro_recibido": h["estado"], "titulo": h["titulo"],
                          "detalle": det.get("finding", det.get("detalle", "Ver registro original")),
                          "impacto": det.get("impact", ""), "criterio_cierre": det.get("closure_criterion", ""),
                          "revisor_necesario": det.get("specialist", "Participante; especialista si procede"),
                          "fuente": h.get("fuente"), "revisiones_recibidas": len(h.get("revisiones_posteriores", [])),
                          "responsable_humano": None})

    suites = []
    for p in sorted((REPO / "docs/controles").glob("*/resultado.json")):
        x = leer(p)
        suites.append({"archivo": p.relative_to(REPO).as_posix(), "utc": x["utc"], "version": x["version_reproducir"],
                       "entorno": x["entorno"], "casos": x["casos"], "pasan": x["pasan"],
                       "fallan": x["fallan"], "etapas_reales_invocadas": x["etapas_reales_invocadas"],
                       "resultados": x["resultados"], "paquete": x["paquete"],
                       "procedencia": "Prueba propia de esta revisión en Windows" if "windows_v12" in str(p) else "Recibo histórico de Claude, inspeccionado"})

    candidatos = []
    for x in registry["candidates"]:
        candidatos.append({k: x[k] for k in ("id", "candidate", "hypothesis", "changes", "parameters", "validation_scheme", "local_score", "public_score", "submitted", "submitted_utc", "kaggle_submission_id", "submission_id", "note") if k in x})
    experimentos = []
    for autor, folder in (("Línea principal histórica", semana / "Modelos_claude/experimentos"), ("Línea B histórica", semana / "Modelos_claude_b/experimentos")):
        if folder.exists():
            for p in sorted(folder.glob("*.json")):
                experimentos.append({"nombre": p.stem, "autor": autor, "fuente": p.relative_to(raiz).as_posix(), "sha256": sha(p),
                                     "estado": "Archivo existente; no acredita que haya un proceso activo"})
    propios = sorted(codex.glob("C*_plan.json")) + sorted(codex.glob("A*_plan.json"))
    for p in propios:
        experimentos.append({"nombre": p.stem, "autor": "Codex histórico", "fuente": p.relative_to(raiz).as_posix(), "sha256": sha(p),
                             "estado": "Plan conservado; su existencia no prueba ejecución o mejora"})

    reglas = [
        ("ID01", "Normalizar claves de cliente de autos contra el maestro", n62["rules_changes"]["ID01"], "Cambian claves; conservar texto y verificar integridad referencial."),
        ("EXP01", "Convertir exposición registrada como días/ACT360", n62["rules_changes"]["EXP01"], "No altera siniestros; afecta denominadores y prima del periodo."),
        ("CAP01", "Dividir capitales extremos por 1000 con referencia anterior admisible", 2073, "La capa base mantiene 1.454 pendientes; F0 tiene un tratamiento posterior distinto."),
        ("CAT01", "Armonizar aliases de construcción por mayúsculas", 700210, "No confundir esta regla con la posterior armonización t/w de F0."),
        ("AGE01", "Edad cumplida al inicio del periodo", 2936, "Cambio de convención, no afirmar 2.936 errores de captura. D59 deja dos diferencias sin explicar."),
        ("DUP01", "Excluir una copia exacta de siniestros duplicados", 604, "Se conservan 162.546 siniestros; no eliminar eventos distintos coincidentes en fecha."),
        ("REN00", "Marcar continuidad de pólizas con rechazo de renovación", 12041, "Marca de auditoría; no predictor ni motivo para borrar coste."),
        ("PRE00", "Marcar siniestros anteriores al historial de pólizas", 413, "Se preservan en claims, se excluyen de la asignación T0 del historial."),
        ("D66/F0", "Tratar los 1.454 capitales restantes en la matriz de modelado", 1454, "1.305 apoyados por historia y 149 PRM01-R sin confirmación; los 11 originales y la capa base no cambian."),
    ]
    validaciones = [
        {"id": "D59", "alcance": "Ocho reglas base y rama retrospectiva hasta CAP05R", "resultado": "41/41 históricos", "limite": "No valida automáticamente CAP06R o el modelo final; segunda implementación IA.", "fuente": "docs/evidencia/documentacion_datos_D61.md"},
        {"id": "N62", "alcance": "Base desde 11 originales", "resultado": "11/11 bytes; 148.424.183 celdas comparadas históricamente sin diferencias", "limite": "Esta sesión solo coteja hashes de originales. No repite esa comparación ni entrenamiento.", "fuente": "docs/evidencia/base_N62.json"},
        {"id": "D67", "alcance": "Asignación, T0 y desarrollo", "resultado": "18/18 históricos; 160.432 aceptados asignados una vez", "limite": "Proxy de incurrido, sin último observado ni suficiencia de reservas acreditada.", "fuente": "docs/evidencia/bases_D67.json"},
        {"id": "D68", "alcance": "F0 y particiones", "resultado": "25/25 históricos", "limite": "Disponibilidad temporal F3 y clima requiere revisión adicional.", "fuente": "docs/evidencia/F0_D68.json"},
        {"id": "Integral 19oct 12:02 UTC", "alcance": "Datos y modelos S22/S30", "resultado": "99 controles datos y 429 modelos, según informe recibido", "limite": "No son pruebas nuevas de esta sesión; 49 pytest históricos tampoco se suman otra vez.", "fuente": "docs/evidencia/hallazgos.json"},
        {"id": "S30 frente a S22", "alcance": "D² completo, semestres, segmentos, reservas fijas y dependencia", "resultado": "72 ámbitos; V24 +0,000138041", "limite": "IC95 cliente y dirección incluyen cero; cortes reutilizados.", "fuente": "docs/evidencia/recibo_S30.json"},
        {"id": "Reproducción mezcla", "alcance": "CSV desde componentes guardados", "resultado": "S22/S30 exactos en recibos nube y VM", "limite": "VM: diferencias intermedias de último bit; versión 1.1 devuelve 3 en modo diagnóstico. Cadena completa pendiente.", "fuente": "docs/verificacion.md"},
        {"id": "Entrega de hoy", "alcance": "Dos CSV, IDs, orden, cobertura, finitud y SHA", "resultado": f"{sum(x['pasa'] for x in preflight)}/2 conformes", "limite": "Verificación de formato/integridad, no de verdad última o score privado.", "fuente": "docs/evidencia/preflight.json"},
    ]

    replay_path = REPO / "docs/evidencia/replay_windows.json"
    replay = leer(replay_path) if replay_path.exists() else {"estado": "pendiente"}
    datos = {"generado_utc": now.isoformat(), "generado_bogota": now.astimezone(timezone(timedelta(hours=-5))).isoformat(),
             "estado": "Preparada para revisión; cierre humano y reproducción completa pendientes", "version_paquete": "1.2",
             "deadline_utc": oficial["metadata"]["deadline"], "best": {"id": "S30", "public_score": receipt30["public_score"],
             "submission_id": receipt30["kaggle_submission_id"], "local_D2_V24": receipt30["local_validation"]["D2"],
             "gain_vs_S22": receipt30["local_validation"]["gain"], "CI95_cliente": receipt30["local_validation"]["conditional_customer_CI95"],
             "CI95_direccion": receipt30["local_validation"]["conditional_address_CI95"]},
             "tablas": integridad, "rows_por_ramo": rows_por_ramo, "diccionario": dictionary, "perfiles": tabla_perfiles,
             "reglas": [{"id": a, "descripcion": b, "filas_o_celdas": c, "limite": d} for a,b,c,d in reglas],
             "base": base, "bases": bases, "f0": f0, "contrato_f0": contract, "spec": spec,
             "modelos_por_ramo": receipt30["local_validation"].get("per_line", []),
             "calibracion_s30": delivery30.get("validacion", {}), "candidatos": candidatos,
             "preflight": preflight, "validaciones": validaciones, "hallazgos": hallazgos, "suites": suites, "replay_windows": replay,
             "experimentos": experimentos, "fuentes": fuentes,
             "procesos": "No acreditado en esta sesión: la consulta de procesos del sistema fue denegada. Los archivos y planes no prueban actividad en vivo.",
             "linaje": "Se unifica la gestión y la documentación. S30 conserva sus componentes de Claude; la base N62 y verificaciones de Codex conservan su autoría. Las mezclas históricas compartidas siguen identificadas."}
    for nombre, objeto in (("base_N62", n62), ("bases_D67", bases), ("F0_D68", f0), ("preflight", preflight), ("hallazgos", hallazgos),
                            ("recibo_S30", receipt30), ("recibo_S22", receipt22)):
        guardar(ev / (nombre + ".json"), objeto)
    guardar(REPO / "registro/fuentes.json", fuentes)
    guardar(REPO / "registro/estado_entrega.json", {"utc": now.isoformat(), "carpeta_activa": REPO.relative_to(raiz).as_posix(),
             "principal": "S30", "respaldo": "S22", "seleccion_final_manual_kaggle": "pendiente_no_realizada",
             "integridad_originales": all(x["coincide"] for x in integridad), "preflight_csv": all(x["pasa"] for x in preflight),
             "reproduccion_completa": "pendiente", "revision_humana": "pendiente", "entrega_cerrada": False,
             "replay_windows": replay,
             "pruebas_activas": datos["procesos"], "corte_validacion_recibida": cycle["run_id"],
             "github": "https://github.com/manoloriveros/iaa-hackathon-2026", "visibilidad": "private",
             "limites": ["No se acredita último observado", "V23/V24 reutilizados", "Fecha de disponibilidad de predictores", "149 capitales sin confirmación", "Elegibilidad para premio pendiente"]})
    guardar(REPO / "registro/panel_datos.json", datos)
    template = (REPO / "herramientas/panel_template.html").read_text(encoding="utf-8")
    inline = json.dumps(datos, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    requisitos = json.dumps(leer(REPO / "registro/requisitos.json"), ensure_ascii=False).replace("</", "<\\/")
    out = REPO / "docs/panel_revision.html"
    out.write_text(template.replace("__DATOS_JSON__", inline).replace("__REQUISITOS_JSON__", requisitos), encoding="utf-8")
    guardar(REPO / f"privado/revisiones/{marca}/recibo.json", {"utc": now.isoformat(), "preflight": preflight,
            "originales": integridad, "fuentes": fuentes, "panel_sha256": sha(out), "entrenamientos": 0, "envios": 0})
    ok = all(x["pasa"] for x in preflight) and all(x["coincide"] for x in integridad)
    print(json.dumps({"csv_conformes": sum(x["pasa"] for x in preflight), "originales_conformes": sum(x["coincide"] for x in integridad),
                      "variables_diccionario": len(dictionary), "experimentos_indexados": len(experimentos), "fuentes": len(fuentes),
                      "panel": str(out), "entrenamientos": 0, "entrega_cerrada": False}, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
