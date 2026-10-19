"""Variables de cambio respecto del periodo anterior de la misma póliza (renovación o cambio a mitad de año).

Todas usan atributos conocidos al inicio de cada periodo (F0/F4 del periodo actual y del anterior), sin siniestros ni
estados del propio periodo. La prima anualizada se compara con la del periodo anterior y se le resta la mediana del
cambio en su año, para quitar el ajuste general de tarifa. Autos: cambio de NCB, de vehículo, de franquicia voluntaria
y de kilometraje. Hogar: cambio relativo del capital y de la franquicia. Las filas sin periodo anterior quedan en NaN.
Uso: python3 variables_cambio.py <ramo>  ->  WORK/cambio_<ramo>.parquet
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from comun import WORK

COLS = {"motor": ["ncb_years", "make_model", "voluntary_excess", "annual_mileage", "vehicle_age"],
        "buildings": ["sum_insured", "voluntary_excess", "accidental_damage_cover"],
        "contents": ["sum_insured", "voluntary_excess", "accidental_damage_cover", "high_value_items"]}


def main():
    line = sys.argv[1]
    cols = COLS[line]
    df = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "policy_id", "year", "period_start", "period_end", "exposure", "written_premium"] + cols)
    df = df.sort_values(["policy_id", "period_start"]).reset_index(drop=True)
    g = df.groupby("policy_id", sort=False)
    rate = np.log((df.written_premium / df.exposure).clip(lower=1e-6))
    prev_rate = g["written_premium"].shift(1) / g["exposure"].shift(1)
    d = rate - np.log(prev_rate.clip(lower=1e-6))
    prev_year = g["year"].shift(1)
    out = pd.DataFrame({"row_id": df.row_id.astype(str)})
    out["cb_tiene_previo"] = prev_year.notna().astype("float32")
    out["cb_previo_mismo_anio"] = (prev_year == df.year).astype("float32").where(prev_year.notna())
    med = d.groupby(df.year).transform("median")
    out["cb_cambio_prima"] = (d - med).astype("float32")
    if line == "motor":
        out["cb_cambio_ncb"] = (df.ncb_years - g["ncb_years"].shift(1)).astype("float32")
        pm = g["make_model"].shift(1)
        out["cb_cambio_vehiculo"] = (df.make_model.astype(str) != pm.astype(str)).astype("float32").where(pm.notna())
        out["cb_cambio_franquicia"] = (df.voluntary_excess - g["voluntary_excess"].shift(1)).astype("float32")
        out["cb_cambio_km"] = np.log((df.annual_mileage + 1) / (g["annual_mileage"].shift(1) + 1)).astype("float32")
    else:
        out["cb_cambio_capital"] = np.log(df.sum_insured / g["sum_insured"].shift(1)).astype("float32")
        out["cb_cambio_franquicia"] = (df.voluntary_excess - g["voluntary_excess"].shift(1)).astype("float32")
        prev_ad = g["accidental_damage_cover"].shift(1)
        out["cb_cambio_danio_acc"] = (df.accidental_damage_cover.astype(str) != prev_ad.astype(str)).astype("float32").where(prev_ad.notna())
    out.to_parquet(WORK / f"cambio_{line}.parquet", index=False)
    print(line, len(out), out.drop(columns="row_id").describe().T[["count", "mean", "std", "min", "max"]].round(3).to_string(), flush=True)


if __name__ == "__main__":
    main()
