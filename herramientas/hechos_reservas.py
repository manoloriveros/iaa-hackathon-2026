"""Hechos agregados de claims.parquet para RES-01 a RES-04 (COD-20261019-113). Solo lectura y solo agregados.

Responde qué permite y qué no permite la única valoración disponible (31-12-2024): una fila por siniestro, estados,
reservas de caso de los abiertos por ramo y año de ocurrencia, y dónde aparecen las recuperaciones. Incluye una
sensibilidad descriptiva (no un ajuste): cuánto bajaría el neto de los abiertos de autos si recibieran recuperaciones en
la misma proporción que los cerrados de su peligro. No cambia el objetivo, ni T0, ni ningún modelo.
Uso: python herramientas/hechos_reservas.py <ruta claims.parquet> <salida.json>
Autor: Claude (línea principal), 19 de octubre de 2026, CLA-20261019-004.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

EPS = 1e-9


def r2(x):
    return round(float(x), 2)


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    c = pd.read_parquet(src)
    columnas = list(c.columns)
    c["loss_date"] = pd.to_datetime(c.loss_date)
    c["report_date"] = pd.to_datetime(c.report_date)
    c["anio"] = c.loss_date.dt.year
    c["reserva"] = c.incurred_to_date - c.paid_to_date
    out = {
        "autor": "Claude (línea principal)", "aporte": "CLA-20261019-004", "responde_a": ["COD-20261019-113"],
        "creado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": {"archivo": "Hackaton/Semana 1/Datos/claims.parquet", "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                   "nota": "original sin limpiar; la capa preaudit (N62) deja 162.546 registros (control K07 de D67)"},
        "entorno": {"python": platform.python_version(), "pandas": pd.__version__},
        "herramienta_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "alcance": "agregados de una sola valoración; sin datos por fila; sin cambios en objetivo, T0 o modelos",
    }
    out["estructura"] = {
        "filas": int(len(c)), "claim_id_unico": bool(c.claim_id.is_unique), "columnas": columnas,
        "fechas_disponibles": ["loss_date", "report_date"],
        "sin_columna_de": ["fecha de valoración (una sola, 31-12-2024, según el diccionario)", "fecha de cierre o liquidación",
                           "reapertura o historial de estados", "movimientos o valoraciones anteriores", "gastos de liquidación",
                           "recuperaciones esperadas en la reserva"],
        "loss_date": [str(c.loss_date.min().date()), str(c.loss_date.max().date())],
        "report_date": [str(c.report_date.min().date()), str(c.report_date.max().date())],
        "estados": {k: int(v) for k, v in c.status.value_counts().items()},
    }
    por_estado = {}
    for s, d in c.groupby("status"):
        por_estado[s] = {"n": int(len(d)), "pagado_CU": r2(d.paid_to_date.sum()), "incurrido_CU": r2(d.incurred_to_date.sum()),
                         "reserva_CU": r2(d.reserva.sum()), "con_reserva_positiva": int((d.reserva > EPS).sum()),
                         "con_reserva_negativa": int((d.reserva < -EPS).sum()), "con_recuperacion": int((d.recoveries > EPS).sum()),
                         "recuperaciones_CU": r2(d.recoveries.sum()), "con_pago_cero": int((d.paid_to_date.abs() <= EPS).sum())}
    out["por_estado"] = por_estado
    ab = c[c.status == "open"]
    out["abiertos_por_ramo_y_anio_de_ocurrencia"] = {
        f"{l}/{a}": {"n": int(len(d)), "reserva_CU": r2(d.reserva.sum()), "sin_reserva": int((d.reserva <= EPS).sum())}
        for (l, a), d in ab.groupby(["line", "anio"])}
    cl = c[c.status == "closed"]
    rec, razon = {}, {}
    for (l, p), d in cl.groupby(["line", "peril"]):
        if (d.recoveries > EPS).any():
            razon[f"{l}/{p}"] = float(d.recoveries.sum() / d.incurred_to_date.sum())
            rec[f"{l}/{p}"] = {"cerrados": int(len(d)), "con_recuperacion_pct": round(100 * float((d.recoveries > EPS).mean()), 2),
                               "recuperacion_sobre_incurrido": round(float(d.recoveries.sum() / d.incurred_to_date.sum()), 4),
                               "por_anio": {int(a): round(float(x.recoveries.sum() / x.incurred_to_date.sum()), 4) for a, x in d.groupby("anio")}}
    out["recuperaciones_en_cerrados"] = rec
    out["peligros_sin_ninguna_recuperacion"] = sorted(f"{l}/{p}" for (l, p), d in c.groupby(["line", "peril"]) if not (d.recoveries > EPS).any())
    sens = {}
    for clave, v in rec.items():
        l, p = clave.split("/")
        a = ab[(ab.line == l) & (ab.peril == p)]
        sens[clave] = {"abiertos": int(len(a)), "incurrido_abiertos_CU": r2(a.incurred_to_date.sum()),
                       "incurrido_abiertos_por_anio_CU": {int(k): r2(x) for k, x in a.groupby("anio").incurred_to_date.sum().items()},
                       "recuperacion_hipotetica_CU": r2(razon[clave] * a.incurred_to_date.sum())}
    out["sensibilidad_recuperaciones_futuras"] = {
        "hipotesis": "la reserva de caso no anticipa recuperaciones y los abiertos las recibirían al cerrar en la proporción de los cerrados de su peligro",
        "alternativa": "la reserva de caso ya es neta de recuperaciones esperadas; entonces no hay nada que corregir",
        "identificable_con_esta_valoracion": False,
        "por_peligro": sens,
        "total_hipotetico_CU": r2(sum(v["recuperacion_hipotetica_CU"] for v in sens.values())),
        "uso": "solo diagnóstico para fijar materialidad; no se aplica a T0, a S30 ni a S22",
    }
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("estructura", "por_estado")}, ensure_ascii=False, indent=1))
    print(json.dumps(out["sensibilidad_recuperaciones_futuras"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
