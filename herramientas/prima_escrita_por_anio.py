"""Prima escrita anual media por ramo y año (2021-2025), ponderada por exposición: evidencia del nivel 2025 que no
depende del marcador de Kaggle.

La prima escrita de los datos es anual: no cambia con la duración del periodo (correlación con la exposición cercana a
cero), así que su media ponderada por la exposición del periodo da el nivel de tarifa de cada año. La exposición se
recalcula desde las fechas con la convención de EXP01 (días inclusivos / 365) para no mezclar unidades. Solo lee los
once Parquet originales y escribe agregados (ninguna fila) en docs/evidencia/prima_escrita_por_anio.json.

    python herramientas/prima_escrita_por_anio.py --raiz C:/dev/Hakaton

Necesita pandas y pyarrow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAMOS = ("motor", "buildings", "contents")
SALIDA = REPO / "docs" / "evidencia" / "prima_escrita_por_anio.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=REPO.parents[1])
    a = ap.parse_args()
    datos = a.raiz.resolve() / "Hackaton" / "Semana 1" / "Datos"
    fuentes, por_ramo = {}, {}
    for ramo in RAMOS:
        partes = []
        for t in (f"policies_{ramo}", f"test_{ramo}"):
            p = datos / f"{t}.parquet"
            fuentes[t] = sha256(p)
            d = pd.read_parquet(p, columns=["period_start", "period_end", "written_premium"])
            ini, fin = pd.to_datetime(d.period_start), pd.to_datetime(d.period_end)
            d["e"] = ((fin - ini).dt.days + 1) / 365
            d["anio"] = ini.dt.year
            partes.append(d)
        d = pd.concat(partes)
        d["wp_e"] = d.written_premium * d.e
        g = d.groupby("anio").agg(wp_e=("wp_e", "sum"), e=("e", "sum"), periodos=("e", "size"))
        g["prima_media_anual"] = g.wp_e / g.e
        corr = float(d.loc[d.anio == 2024, ["written_premium", "e"]].corr().iloc[0, 1])
        por_ramo[ramo] = {"por_anio": {int(k): {"prima_media_anual": round(float(v.prima_media_anual), 2), "exposicion": round(float(v.e), 1),
                                                 "periodos": int(v.periodos)} for k, v in g.iterrows()},
                          "cambio_2024_2025": round(float(g.loc[2025, "prima_media_anual"] / g.loc[2024, "prima_media_anual"] - 1), 4),
                          "correlacion_prima_exposicion_2024": round(corr, 3)}
    salida = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "herramienta": "herramientas/prima_escrita_por_anio.py",
              "definicion": "Media de la prima escrita anual ponderada por la exposición del periodo (días inclusivos / 365), por año de inicio del periodo; 2021-2024 de policies_*, 2025 de test_*.",
              "fuentes_sha256": fuentes, "ramos": por_ramo}
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({r: v["cambio_2024_2025"] for r, v in por_ramo.items()}))


if __name__ == "__main__":
    main()
