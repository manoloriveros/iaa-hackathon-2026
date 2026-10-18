"""Variables de cartera conocidas al inicio del periodo: productos del cliente y ocupación de la dirección en el mismo año.

Para cada fila (ramo, año): si el cliente tiene en ese año pólizas de los otros ramos, cuántos ramos tiene, cuántos
clientes distintos y pólizas tiene la dirección en ese año en el mismo ramo y en total. Se calculan con las matrices
de entrenamiento y test (atributos contractuales, no etiquetas), por año, sin mirar años posteriores.
Escribe WORK/cartera_<ramo>.parquet. Uso: python3 variables_cartera.py
"""
from __future__ import annotations

import pandas as pd

from comun import LINES, WORK


def main():
    frames = {l: pd.read_parquet(WORK / f"feat_{l}.parquet", columns=["row_id", "customer_id", "address_id", "year"]).assign(line=l) for l in LINES}
    allr = pd.concat(frames.values(), ignore_index=True)
    allr["customer_id"] = allr.customer_id.astype(str); allr["address_id"] = allr.address_id.astype(str)
    held = allr.groupby(["customer_id", "year", "line"]).size().unstack(fill_value=0).clip(upper=1)
    held.columns = [f"cli_tiene_{c}" for c in held.columns]
    held["cli_n_ramos"] = held.sum(axis=1)
    held = held.reset_index()
    addr_cli = allr.groupby(["address_id", "year"]).customer_id.nunique().rename("dir_n_clientes").reset_index()
    addr_pol = allr.groupby(["address_id", "year"]).size().rename("dir_n_filas").reset_index()
    for line, f in frames.items():
        f = f.copy(); f["customer_id"] = f.customer_id.astype(str); f["address_id"] = f.address_id.astype(str)
        same = f.groupby(["address_id", "year"]).customer_id.nunique().rename("dir_n_clientes_mismo_ramo").reset_index()
        out = f.merge(held, on=["customer_id", "year"], how="left").merge(addr_cli, on=["address_id", "year"], how="left") \
               .merge(addr_pol, on=["address_id", "year"], how="left").merge(same, on=["address_id", "year"], how="left")
        cols = [c for c in out.columns if c.startswith(("cli_", "dir_")) and c != f"cli_tiene_{line}"]
        res = out[["row_id"] + cols].copy(); res["row_id"] = res.row_id.astype(str)
        res.to_parquet(WORK / f"cartera_{line}.parquet", index=False)
        print(line, res.shape, cols, res[cols].mean().round(3).to_dict(), flush=True)


if __name__ == "__main__":
    main()
