"""Variables de interacción explícitas (los árboles son poco profundos, 5-7 hojas) y codificación de make_model.

Autos: edad al obtener la licencia, proporción de bonificación sobre años de licencia, kilómetros por año de licencia,
valor por antigüedad del vehículo, conductor joven con poca experiencia; frecuencia suavizada de notificaciones por
make_model calculada solo con años anteriores al del periodo (sin fuga) y su volumen.
Hogar: capital por habitación, antigüedad del inmueble al inicio del periodo, zona de inundación por baja elevación,
cercanía al río por baja elevación, prima por mil de capital (F4).
Escribe WORK/inter_<ramo>.parquet (row_id y variables). Uso: python3 variables_interaccion.py [ramos]
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from comun import BASESDIR, LINES, WORK


def main():
    lines = sys.argv[1].split(",") if len(sys.argv) > 1 else LINES
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet", columns=["claim_id", "row_id", "line", "category"])
    for line in lines:
        df = pd.read_parquet(WORK / f"feat_{line}.parquet")
        out = pd.DataFrame({"row_id": df.row_id.astype(str).values})
        if line == "motor":
            out["edad_licencia"] = (df.driver_age - df.years_licensed).astype(float).values
            out["ncb_sobre_licencia"] = (df.ncb_years / df.years_licensed.clip(lower=1)).astype(float).values
            out["km_por_anio_licencia"] = (df.annual_mileage / df.years_licensed.clip(lower=1)).astype(float).values
            out["valor_por_antiguedad"] = (df.vehicle_value_group / (df.vehicle_age.fillna(0) + 1)).astype(float).values
            out["joven_inexperto"] = ((df.driver_age < 25) & (df.years_licensed < 3)).astype(float).values
            # make_model: notificaciones por año expuesto con años anteriores al del periodo, suavizada hacia la media
            notif = a[(a.line == "motor") & (a.category == "unica")].groupby("row_id").size()
            t = df.loc[~df.is_test, ["row_id", "make_model", "year", "exposure"]].copy()
            t["n"] = t.row_id.astype(str).map(notif).fillna(0).values
            g = t.groupby(["make_model", "year"]).agg(n=("n", "sum"), e=("exposure", "sum")).reset_index()
            rows = []
            for y in range(2022, 2026):
                p = g[g.year < y].groupby("make_model").agg(n=("n", "sum"), e=("e", "sum"))
                prior = p.n.sum() / p.e.sum()
                k = 200.0  # años expuestos de credibilidad
                p["mm_frec_suav"] = (p.n + k * prior) / (p.e + k) / prior
                p["mm_expuestos_previos"] = p.e
                p["year"] = y
                rows.append(p.reset_index()[["make_model", "year", "mm_frec_suav", "mm_expuestos_previos"]])
            mm = pd.concat(rows, ignore_index=True)
            m = df[["make_model", "year"]].merge(mm, on=["make_model", "year"], how="left")
            out["mm_frec_suav"] = m.mm_frec_suav.values
            out["mm_expuestos_previos"] = m.mm_expuestos_previos.fillna(0).values
        else:
            si = df.sum_insured.astype(float)
            out["capital_por_habitacion"] = (si / df.bedrooms.clip(lower=1)).values
            out["antiguedad_inmueble"] = (df.year - df.year_built).astype(float).values
            fz = df.flood_zone.fillna(3.5)
            out["inundacion_baja_elevacion"] = (fz * np.exp(-df.elevation_m.astype(float) / 20.0)).values
            out["rio_baja_elevacion"] = (np.exp(-df.distance_to_river_km.fillna(df.distance_to_river_km.median()).astype(float)) * np.exp(-df.elevation_m.astype(float) / 20.0)).values
            out["prima_por_mil_capital"] = (df.written_premium / df.exposure / (si / 1000.0)).values
        out.to_parquet(WORK / f"inter_{line}.parquet", index=False)
        print(line, out.shape, list(out.columns), flush=True)


if __name__ == "__main__":
    main()
