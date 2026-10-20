"""Valida un expediente temporal; no ejecuta modelos ni certifica fechas históricas.

La salida 0 significa metadatos y evidencia referenciada coherentes para el corte
indicado. La veracidad de las declaraciones y la cobertura efectiva del modelo
requieren revisión humana. Una fecha desconocida nunca se convierte en disponible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def timestamp(value):
    if not isinstance(value, str) or not value:
        raise ValueError("fecha_ausente")
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("fecha_sin_huso_o_solo_dia")
    return result


def evaluar(expediente, cotizacion, root):
    quote = timestamp(cotizacion)
    fields = expediente.get("campos", [])
    if not fields:
        return {"conforme_metadata": False, "errores": ["sin_campos"], "campos": []}
    ids = [f.get("id") for f in fields]
    if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        return {"conforme_metadata": False, "errores": ["ids_ausentes_o_duplicados"], "campos": []}
    expected = expediente.get("campos_requeridos", [])
    missing = set(expected) - set(ids)
    global_errors = ["cobertura_incompleta:" + x for x in sorted(missing)]
    dependencies_by_id = {f["id"]:f.get("depende_de", []) for f in fields}
    visited, active = set(), set()
    def cycle(node):
        if node in active:
            return True
        if node in visited or node not in dependencies_by_id:
            return False
        active.add(node)
        if any(cycle(dep) for dep in dependencies_by_id[node]):
            return True
        active.remove(node)
        visited.add(node)
        return False
    if any(cycle(node) for node in ids):
        global_errors.append("dependencias_ciclicas")
    out = []
    root = Path(root).resolve()
    for field in fields:
        errors = []
        if field.get("tipo") not in {"historia", "clima", "maestro_o_contrato", "cartera_anual"}:
            errors.append("tipo_de_campo_no_documentado")
        proof = field.get("acreditacion") or {}
        try:
            measured = timestamp(proof.get("medido_hasta"))
            available = timestamp(proof.get("disponible_desde"))
            if measured > quote:
                errors.append("medicion_posterior")
            if available > quote:
                errors.append("disponibilidad_posterior")
            if available < measured:
                errors.append("disponible_antes_de_fin_medicion")
            if field.get("tipo") == "historia":
                # Se exige anterioridad estricta; los empates necesitan resolución horaria.
                if timestamp(proof.get("ultimo_aviso")) >= quote:
                    errors.append("aviso_no_estrictamente_anterior")
            if field.get("tipo") == "clima":
                if timestamp(proof.get("periodo_cerrado_en")) > available:
                    errors.append("clima_publicado_antes_del_cierre")
        except (ValueError, TypeError) as exc:
            errors.append(str(exc))
        document = proof.get("documento")
        expected_sha = proof.get("sha256")
        try:
            if not isinstance(document, str) or not document:
                raise ValueError("sin_documento")
            path = (root / document).resolve()
            if not path.is_relative_to(root):
                raise ValueError("documento_fuera_del_expediente")
            if not isinstance(expected_sha, str) or len(expected_sha) != 64:
                raise ValueError("sin_sha256")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
                errors.append("documento_sha_distinto")
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
        if not proof.get("revisor") or not proof.get("revision_utc"):
            errors.append("sin_revision_atribuida")
        else:
            try:
                timestamp(proof["revision_utc"])
            except (ValueError, TypeError):
                errors.append("fecha_revision_invalida")
        dependencies = field.get("depende_de", [])
        if any(dep not in ids for dep in dependencies):
            errors.append("dependencia_sin_ficha")
        out.append({"id": field["id"], "errores": errors})
    invalid = {f["id"] for f in out if f["errores"]}
    # Una derivación no acredita disponibilidad si alguna dependencia falla.
    changed = True
    while changed:
        changed = False
        for field, result in zip(fields, out):
            if field["id"] not in invalid and any(dep in invalid for dep in field.get("depende_de", [])):
                result["errores"].append("dependencia_no_acreditada")
                invalid.add(field["id"])
                changed = True
    return {"conforme_metadata": not global_errors and not invalid,
            "errores": global_errors, "campos": out,
            "limite": "No acredita por sí solo veracidad, cobertura efectiva, disponibilidad por cada fila ni aprobación humana."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expediente", type=Path, required=True)
    parser.add_argument("--cotizacion", required=True, help="Instante ISO con huso explícito")
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    try:
        result = evaluar(json.loads(args.expediente.read_bytes()), args.cotizacion, args.expediente.parent)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result = {"conforme_metadata": False, "errores": [str(exc)]}
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        with args.salida.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
    print(json.dumps({"conforme_metadata": result["conforme_metadata"],
                      "campos": len(result.get("campos", [])), "errores": result.get("errores", [])}))
    return 0 if result["conforme_metadata"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
