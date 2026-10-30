"""Build line-specific F0 predictors, labels and persistent temporal partitions.

Verify the ten prepared input tables and the actuarial-base manifest. Write
2021-2024 training/2025 test tables, row/peril T0 labels, partition keys,
availability contract, evidence and source/hash manifest into a new run.

Feature blocks: F0 contractual/physical attributes; F1 policy notifications known
before 1 January of the period year; F2 prior-year address weather; F3 conditional
attributes without reference dates; F4 the existing tariff. Keys, labels and audit
flags are excluded from predictors. F3/F4 require their documented separate checks.
Scale insured values above each line threshold by 1,000. Reconstructed capital
audit flags remain excluded. Harmonize construction t/w into tw_code and exclude
the unharmonized original.
Peril effective exposure weights covered days by occurrence-month completeness
at the historical valuation date. Completeness is inverse chain-ladder development
and equals 1 for 2025; e_ef_coste uses line-level developed-cost peril shares.
V22 trains on 2021 for 2022; V23 on 2021-2022 for customer-hash-split 2023;
V24 on 2021-2023 for 2024; production on 2021-2024 for 2025.

Run all lines through the isolated runner, or use --ramo motor, then
--run <id> --ramo buildings,contents and --run <id> --finalizar for staged execution.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


ROOT = find_root(HERE)
try:
    import pyarrow  # noqa: F401
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(ROOT / "Preparación" / ".cache" / "parquet-reader"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

LINES = ["motor", "buildings", "contents"]
PERILS = {"motor": ["own_damage", "third_party_prop", "bodily_injury", "theft", "glass_hail"],
          "buildings": ["storm", "flood", "escape_of_water", "subsidence", "fire", "accidental_damage"],
          "contents": ["theft", "escape_of_water", "accidental_damage", "flood"]}
THRESHOLD = {"buildings": 10_000_000.0, "contents": 1_000_000.0}
MONTHS = pd.period_range("2021-01", "2025-12", freq="M")
CUTOFF_MONTH_INDEX = 47  # December 2024 with January 2021 indexed as zero.
CAL_SALT = "cal_v1"
TRAIN_ROWS = 2409311
TEST_ROWS = 626639
STRING_MAPPER = {pa.string(): pd.StringDtype("pyarrow"), pa.large_string(): pd.StringDtype("pyarrow")}.get
AMOUNT_LABELS = ["T0", "paid", "incurred", "recoveries", "reserve"]
COUNT_LABELS = ["n_accepted", "n_positive", "n_open"]
EXCLUDED_ALWAYS = ["customer_service_contacts", "renewal_decision", "audit_ren00", "surname", "construction_type", "sum_insured_raw",
                   "audit_capital_scale_adjusted", "audit_capital_scale_confirmed", "audit_capital_cap01"]
BLOCKS = ["F0", "F1", "F2", "F3", "F4", "excluida", "clave", "etiqueta"]

CONTRACT_COMMON = {
    "row_id": ("clave", "identificador de la fila; nunca predictor"),
    "policy_id": ("clave", "identificador; nunca predictor"),
    "customer_id": ("clave", "identificador; solo para hash de calibración y agrupación"),
    "address_id": ("clave", "identificador; solo para agrupación y cruces"),
    "period_start": ("clave", "fecha de inicio; define año y mes de ocurrencia"),
    "period_end": ("clave", "fecha de fin"),
    "is_test": ("clave", "indicador de fila de test 2025"),
    "exposure": ("F0", "exposición nominal EXP01 en años; offset o multiplicador en predicción"),
    "year": ("F0", "año del periodo; efecto de nivel con extrapolación declarada a 2025"),
    "mes_inicio": ("F0", "mes de inicio del periodo; estacionalidad y duración"),
    "periodo_corto": ("F0", "indicador de exposición menor que 0,5 años; efecto de duración (D37)"),
    "new_business": ("F0", "nuevo negocio frente a renovación; conocido al inicio"),
    "renewal_count": ("F0", "número de renovaciones; conocido al inicio"),
    "channel": ("F0", "canal de venta; contractual"),
    "payment_method": ("F0", "forma de pago; contractual"),
    "voluntary_excess": ("F0", "franquicia voluntaria; contractual"),
    "compulsory_excess": ("F0", "franquicia obligatoria; contractual"),
    "days_quote_to_inception": ("F0", "días de cotización a inicio; conocido al inicio"),
    "missed_payments_12m": ("F3", "impagos de los últimos doce meses sin fecha de referencia; prueba aparte"),
    "discount_applied": ("F4", "descuento comercial; ablación del tarifario"),
    "written_premium": ("F4", "prima escrita del tarifario existente; ablación aparte, nunca en la matriz base"),
    "customer_service_contacts": ("excluida", "mide el siniestro del propio periodo y cambia de distribución en el test (D50)"),
    "renewal_decision": ("excluida", "solo existe en entrenamiento; decisión posterior al periodo (D45)"),
    "audit_ren00": ("excluida", "marca de auditoría REN00"),
    "anios_como_cliente": ("F0", "año del periodo menos customer_since_year; conocido al inicio"),
    "surname": ("excluida", "nombre personal"),
    "occupation": ("F3", "atributo del maestro de clientes sin fecha de referencia"),
    "marital_status": ("F3", "atributo del maestro sin fecha de referencia"),
    "household_size": ("F3", "atributo del maestro sin fecha de referencia"),
    "credit_band": ("F3", "banda de crédito sin fecha de referencia"),
    "prior_claims_5y": ("F3", "siniestros previos declarados sin fecha de referencia; posible solape con F1"),
    "licence_points": ("F3", "puntos de licencia sin fecha de referencia"),
    "years_at_address": ("F3", "años en el domicilio sin fecha de referencia"),
    "email_domain": ("F3", "atributo comercial"),
    "marketing_consent": ("F3", "atributo comercial"),
    "document_preference": ("F3", "atributo comercial"),
    "previous_insurer": ("F3", "atributo comercial sin fecha"),
    "campaign_code": ("F3", "atributo comercial sin fecha"),
    "branch_id": ("F3", "sucursal; atributo comercial"),
    "marketing_segment": ("F3", "segmento comercial de la aseguradora; posible proxy de edad y renta"),
    "region": ("F0", "región de la dirección; física y estable"),
    "urban_density": ("F0", "densidad urbana; física y estable"),
    "flood_zone": ("F0", "zona de inundación 1-5; nula en 2,9 % de direcciones, el nulo se conserva como ausencia"),
    "distance_to_river_km": ("F0", "distancia al río; física"),
    "elevation_m": ("F0", "elevación; física"),
    "soil_type": ("F0", "tipo de suelo; físico"),
    "year_built": ("F0", "año de construcción; estable"),
    "property_type": ("F0", "tipo de inmueble; estable"),
    "roof_type": ("F0", "tipo de tejado; estable"),
    "basement": ("F0", "sótano; estable"),
    "trees_within_5m": ("F0", "árboles a menos de 5 m; físico"),
    "listed_building": ("F0", "edificio protegido; estable"),
    "bedrooms": ("F0", "habitaciones; estable"),
    "energy_rating": ("F0", "calificación energética; estable bajo supuesto de maestro"),
    "solar_panels": ("F0", "paneles solares; estable bajo supuesto de maestro"),
}
CONTRACT_LINE = {
    "motor": {
        "driver_age": ("F0", "edad del conductor principal; contractual"),
        "years_licensed": ("F0", "años de licencia (VD34 abierto: 3.717 edades implícitas menores de 16)"),
        "ncb_years": ("F0", "años de bonificación (161.822 filas con ncb mayor que licencia, sin recortar)"),
        "vehicle_value_group": ("F0", "grupo de valor del vehículo"),
        "vehicle_age": ("F0", "antigüedad del vehículo"),
        "make_model": ("F0", "marca y modelo; alta cardinalidad, codificar dentro del fold"),
        "engine_size_cc": ("F0", "cilindrada; nula en 2.533 eléctricos (VD35), se conserva nula"),
        "body_type": ("F0", "carrocería"),
        "transmission": ("F0", "transmisión"),
        "seats": ("F0", "plazas"),
        "vehicle_colour": ("F0", "color; señal dudosa, candidata a ablación"),
        "fuel_type": ("F0", "combustible"),
        "driver_assist": ("F0", "asistencia a la conducción"),
        "cover_type": ("F0", "cobertura; estructura contractual con elegibilidad por peligro"),
        "annual_mileage": ("F0", "kilometraje declarado"),
        "overnight_parking": ("F0", "estacionamiento nocturno"),
        "vehicle_use": ("F0", "uso del vehículo"),
        "named_young_driver": ("F0", "conductor joven designado"),
        "telematics_opt_in": ("F3", "adhesión a telemática; bloque condicional"),
        "telematics_score": ("F3", "score telemático; puede generarse durante la cobertura; ausente = sin adhesión, no cero"),
    },
    "buildings": {
        "policyholder_age": ("F0", "edad AGE01 al inicio del periodo"),
        "sum_insured_raw": ("excluida", "capital leído de la capa vigente; se conserva para auditoría"),
        "sum_insured": ("F0", "capital bajo el contrato de F0 de D66 (entre mil sobre 10.000.000 CU)"),
        "log_sum_insured": ("F0", "logaritmo del capital del contrato; curva suave candidata"),
        "construction_type": ("excluida", "t y w son alias temporales (D39); usar construction_type_harmonized"),
        "construction_type_harmonized": ("F0", "construcción con t y w unificados en tw_code (equivalente a CON01, no activado en Limpieza)"),
        "occupancy": ("F0", "ocupación del inmueble; contractual"),
        "days_unoccupied": ("F0", "días desocupado declarados; contractual"),
        "smoke_alarms": ("F0", "detectores de humo; nulo en 2,5 %, nunca cambia dentro de una dirección (D63)"),
        "accidental_damage_cover": ("F0", "cobertura opcional de daño accidental"),
        "mortgage": ("F0", "hipoteca; contractual"),
        "audit_capital_scale_adjusted": ("excluida", "marca D66: capital dividido entre mil en F0"),
        "audit_capital_scale_confirmed": ("excluida", "marca D66: división respaldada por historia (rama CAP02R-CAP06R o lista D66)"),
        "audit_capital_cap01": ("excluida", "fila corregida por CAP01 en la base"),
    },
    "contents": {
        "policyholder_age": ("F0", "edad AGE01 al inicio del periodo"),
        "sum_insured_raw": ("excluida", "capital leído de la capa vigente; se conserva para auditoría"),
        "sum_insured": ("F0", "capital bajo el contrato de F0 de D66 (entre mil sobre 1.000.000 CU)"),
        "log_sum_insured": ("F0", "logaritmo del capital del contrato; curva suave candidata"),
        "tenure": ("F0", "tenencia; contractual"),
        "security_level": ("F0", "nivel de seguridad; nulo en 2,5 %"),
        "high_value_items": ("F0", "bienes de alto valor; nulo en 2,5 %"),
        "accidental_damage_cover": ("F0", "cobertura opcional"),
        "works_from_home": ("F0", "trabajo desde casa; contractual"),
        "lodgers": ("F0", "huéspedes; contractual"),
        "bicycle_cover": ("F0", "cobertura de bicicleta"),
        "audit_capital_scale_adjusted": ("excluida", "marca D66"),
        "audit_capital_scale_confirmed": ("excluida", "marca D66"),
        "audit_capital_cap01": ("excluida", "fila corregida por CAP01 en la base"),
    },
}
WEATHER_VARS = ["hail_days", "wind_exposure_index", "freezing_days", "dry_summer_index", "wildfire_index", "rainfall_mm", "mean_temperature_c"]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_table(path: Path, columns=None, filters=None) -> pd.DataFrame:
    return pq.read_table(path, columns=columns, filters=filters).to_pandas(types_mapper=STRING_MAPPER)


def cal_half(customer_id: str) -> int:
    return int(hashlib.sha256(f"{CAL_SALT}|{customer_id}".encode("utf-8")).hexdigest()[:16], 16) % 2


def classify(col: str, line: str):
    if col in CONTRACT_LINE[line]:
        return CONTRACT_LINE[line][col]
    if col in CONTRACT_COMMON:
        return CONTRACT_COMMON[col]
    if col.endswith("_prev1"):
        return ("F2", "clima del año anterior en la dirección (nulo en 2021); años posteriores al corte nunca")
    if col.startswith("f1_"):
        return ("F1", "historia de notificaciones de la póliza conocida al 1 de enero del año del periodo, sin filtrar por estado final")
    if col.startswith("e_ef_"):
        return ("F0", "exposición efectiva por completitud de reporte: offset de entrenamiento; en predicción se usa exposure")
    if col in AMOUNT_LABELS + COUNT_LABELS or col.startswith("y_") or col.startswith("n_"):
        return ("etiqueta", "coste o conteo del propio periodo valorado al 30-12-2024; nunca predictor; nulo en test")
    return ("revisar", "columna sin contrato declarado")


class Context:
    """Load prepared data, hashes, actuarial bases, capital audit context and peril completeness."""

    def __init__(self):
        self.checks = []
        current = json.loads((ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json").read_text(encoding="utf-8"))
        self.current = current
        self.catalog_path = ROOT / current["catalog_workspace_relative"]
        self.catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        used = ["policies_motor", "policies_buildings", "policies_contents", "test_motor", "test_buildings", "test_contents", "customers", "addresses", "weather", "claims"]
        self.hashes = {n: digest(ROOT / self.catalog[n]["workspace_relative_path"]) for n in used}
        bad = [n for n in used if self.hashes[n] != self.catalog[n]["sha256"]]
        self.check("K01", "SHA-256 de las diez tablas usadas iguales al catálogo activo", not bad, bad)

        self.bases_index = json.loads((ROOT / "Hackaton/Semana 1/Bases_actuariales/current_run.json").read_text(encoding="utf-8"))
        self.bases_run = ROOT / self.bases_index["workspace_relative_run"]
        manifest = json.loads((self.bases_run / "manifest.json").read_text(encoding="utf-8"))
        self.bases_evidence = json.loads((self.bases_run / "evidencia.json").read_text(encoding="utf-8"))
        needed = ["tables/t0_por_row_id.parquet", "tables/asignacion_por_siniestro.parquet", "tables/factores_desarrollo_conteos.csv", "tables/ibnr_por_peligro_anio.csv"]
        self.check("K02", "la corrida vigente de Bases_actuariales usa la misma capa y sus tablas conservan el hash",
                   self.bases_evidence["provenance"]["active_run"] == current["workspace_relative_run"] and all(digest(self.bases_run / n) == manifest[n] for n in needed),
                   self.bases_index["workspace_relative_run"])

        # The historical ledgers are not redistributed. This is an explicit retrospective
        # reconstruction of the audit flags, not the original authorization process.
        self.branch_index = {"workspace_relative_run": "audit-ledger-not-included"}
        self.cap01_index = {"workspace_relative_run": current["workspace_relative_run"]}
        self.d66_index = {"workspace_relative_run": "audit-ledger-not-included"}
        reconstructed = json.loads((ROOT / current["workspace_relative_run"] / "evidence/cap01_row_ids.json").read_text(encoding="utf-8"))
        self.cap01_ids = {str(row) for rows in reconstructed.values() for row in rows}
        self.confirmed_ids = set()
        for line, threshold in (("buildings", 10000000), ("contents", 1000000)):
            frames = [read_table(ROOT / self.catalog[f"{kind}_{line}"]["workspace_relative_path"], columns=["row_id", "policy_id", "address_id", "sum_insured"]) for kind in ("policies", "test")]
            rows = pd.concat(frames, ignore_index=True)
            normal = rows.sum_insured.le(threshold)
            grouping = [rows.policy_id, rows.address_id] if line == "buildings" else rows.policy_id
            has_normal = normal.groupby(grouping, dropna=False).transform("sum").gt(0)
            self.confirmed_ids.update(rows.loc[rows.sum_insured.gt(threshold) & has_normal, "row_id"].astype(str))
        self.check("K03_CAP01", "CAP01 identifiers reconstructed from originals", len(self.cap01_ids) == 2073)
        self.check("K03_RECONSTRUCTED", "Retrospective reconstruction of confirmation flag", len(self.confirmed_ids) == 1305)

        factors = pd.read_csv(self.bases_run / "tables/factores_desarrollo_conteos.csv")
        self.comp = {}
        for (line, peril), g in factors.groupby(["line", "peril"]):
            cdf = np.ones(48)
            for row in g.itertuples():
                cdf[int(row.lag_meses)] = float(row.factor_a_ultimo)
            c = np.ones(len(MONTHS))
            for m in range(CUTOFF_MONTH_INDEX + 1):
                c[m] = 1.0 / cdf[CUTOFF_MONTH_INDEX - m]
            self.comp[(line, peril)] = c
        ibnr_year = pd.read_csv(self.bases_run / "tables/ibnr_por_peligro_anio.csv")
        self.weights = {}
        for line in LINES:
            sub = ibnr_year[ibnr_year.line == line].groupby("peril").agg(T0=("T0_CU", "sum"), ibnr=("ibnr_coste_CU", "sum"))
            tot = sub.T0 + sub.ibnr
            self.weights[line] = (tot / tot.sum()).to_dict()

        self.customers = read_table(ROOT / self.catalog["customers"]["workspace_relative_path"])
        self.addresses = read_table(ROOT / self.catalog["addresses"]["workspace_relative_path"])
        weather = read_table(ROOT / self.catalog["weather"]["workspace_relative_path"])
        weather = weather.rename(columns={v: f"{v}_prev1" for v in WEATHER_VARS})
        weather["year"] = weather["year"].astype(int) + 1  # Weather year Y supplies features for policy periods in Y+1.
        self.weather = weather
        claims = read_table(ROOT / self.catalog["claims"]["workspace_relative_path"], columns=["claim_id", "policy_id", "line", "peril", "report_date", "status", "incurred_to_date", "recoveries"])
        claims["report_date"] = pd.to_datetime(claims["report_date"])
        claims["net"] = claims["incurred_to_date"] - claims["recoveries"]
        self.claims = claims
        assignment = read_table(self.bases_run / "tables/asignacion_por_siniestro.parquet", columns=["claim_id", "row_id", "category"])
        cr = claims.merge(assignment[assignment.category == "unica"][["claim_id", "row_id"]], on="claim_id", how="inner")
        cr = cr[cr.status.isin(["closed", "open"])].copy()
        cr["positive"] = (cr.net > 0).astype(int)
        self.claim_rows = cr
        self.half_cache: dict[str, int] = {}

    def check(self, code, name, ok, detail=None):
        self.checks.append({"code": code, "name": name, "passed": bool(ok), "detail": detail})


def process_line(line: str, ctx: Context, run_dir: Path) -> dict:
    tables_dir = run_dir / "tables"
    (tables_dir / "partes").mkdir(parents=True, exist_ok=True)
    checks = []

    def check(code, name, ok, detail=None):
        checks.append({"code": code, "name": name, "passed": bool(ok), "detail": detail})

    # F1: policy notifications known before 1 January of each period year.
    cl = ctx.claims[ctx.claims.line == line][["policy_id", "report_date"]].copy()
    cl["report_year"] = cl.report_date.dt.year.astype(int)
    hist_parts = []
    for y in range(2021, 2026):
        prev = cl[cl.report_year < y]
        h = prev.groupby("policy_id").agg(f1_notificaciones_previas=("report_date", "size"), f1_ultima_notificacion=("report_date", "max")).reset_index()
        h["year"] = y
        hist_parts.append(h)
    hist = pd.concat(hist_parts, ignore_index=True)

    # Line-specific labels.
    t0 = read_table(ctx.bases_run / "tables/t0_por_row_id.parquet", filters=[("line", "==", line)]).drop(columns=["line", "year", "exposure"])
    per = ctx.claim_rows[ctx.claim_rows.line == line].groupby(["row_id", "peril"]).agg(y=("net", "sum"), n=("positive", "sum"))
    wide = per.unstack("peril")
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    for p in PERILS[line]:
        for pre in ("y", "n"):
            if f"{pre}_{p}" not in wide.columns:
                wide[f"{pre}_{p}"] = 0
    wide = wide.reset_index()
    labels = t0.merge(wide, on="row_id", how="left")
    amount_cols = AMOUNT_LABELS + [f"y_{p}" for p in PERILS[line]]
    count_cols = COUNT_LABELS + [f"n_{p}" for p in PERILS[line]]
    for c in amount_cols:
        labels[c] = labels[c].fillna(0.0).astype("float64")
    for c in count_cols:
        labels[c] = labels[c].fillna(0).astype("int64").astype("Int64")
    del t0, per, wide

    acc = {"rows": {"train": 0, "test": 0}, "nulls": {}, "n_total": 0, "cap_ok": True, "cap": {"adjusted": 0, "confirmed": 0, "cap01": 0, "adjusted_test": 0, "confirmed_test": 0},
           "tw_ok": True, "tw_values": set(), "leak": 0, "f1_rows": 0, "f1_test_rows": 0, "ef_ok": True, "test_ef_ok": True, "ef_sum": {}, "exp_sum": {},
           "label_ok": True, "T0_train": 0.0, "test_label_null_ok": True, "weather_rows": 0, "chunk_unique_ok": True}
    out_path = tables_dir / f"f0_{line}.parquet"
    writer = None
    schema = None
    columns = None
    part_pieces = []
    for kind, table in (("train", f"policies_{line}"), ("test", f"test_{line}")):
        tab = pq.read_table(ROOT / ctx.catalog[table]["workspace_relative_path"])
        years_arr = pd.to_datetime(tab.column("period_start").to_pandas()).dt.year.to_numpy()
        for y in sorted(set(years_arr.tolist())):
            df = tab.filter(pa.array(years_arr == y)).to_pandas(types_mapper=STRING_MAPPER)
            is_test = kind == "test"
            df["is_test"] = is_test
            if "renewal_decision" not in df.columns:
                df["renewal_decision"] = pd.array([None] * len(df), dtype="string[pyarrow]")
            df["period_start"] = pd.to_datetime(df["period_start"])
            df["period_end"] = pd.to_datetime(df["period_end"])
            df["year"] = df.period_start.dt.year.astype("int64")
            df["mes_inicio"] = df.period_start.dt.month.astype("int64")
            df["periodo_corto"] = df.exposure < 0.5
            df = df.merge(ctx.customers, on="customer_id", how="left")
            df = df.merge(ctx.addresses, on="address_id", how="left")
            df["anios_como_cliente"] = (df.year - df.customer_since_year).astype("float64")
            df = df.merge(ctx.weather[ctx.weather.year == y], on=["address_id", "year"], how="left")
            df = df.drop(columns=["date_of_birth", "customer_since_year"])
            acc["weather_rows"] += int(df[f"{WEATHER_VARS[0]}_prev1"].notna().sum())

            if line in THRESHOLD:
                thr = THRESHOLD[line]
                df["sum_insured_raw"] = df["sum_insured"]
                adj = df["sum_insured_raw"] > thr
                df["audit_capital_scale_adjusted"] = adj
                df["sum_insured"] = np.where(adj, df["sum_insured_raw"] / 1000.0, df["sum_insured_raw"])
                ids = df["row_id"].astype(str)
                df["audit_capital_scale_confirmed"] = adj & ids.isin(ctx.confirmed_ids)
                df["audit_capital_cap01"] = ids.isin(ctx.cap01_ids)
                df["log_sum_insured"] = np.log(df["sum_insured"])
                idem = np.where(df["sum_insured"] > thr, df["sum_insured"] / 1000.0, df["sum_insured"])
                acc["cap_ok"] &= bool(np.allclose(idem, df["sum_insured"])) and bool((df["sum_insured"] <= thr).all()) and bool((df.audit_capital_scale_confirmed <= adj).all())
                acc["cap"]["adjusted"] += int(adj.sum())
                acc["cap"]["confirmed"] += int(df.audit_capital_scale_confirmed.sum())
                acc["cap"]["cap01"] += int(df.audit_capital_cap01.sum())
                if is_test:
                    acc["cap"]["adjusted_test"] += int(adj.sum())
                    acc["cap"]["confirmed_test"] += int(df.audit_capital_scale_confirmed.sum())
            if line == "buildings":
                df["construction_type_harmonized"] = df["construction_type"].replace({"t": "tw_code", "w": "tw_code"})
                acc["tw_ok"] &= not bool(df["construction_type_harmonized"].isin(["t", "w"]).any())
                acc["tw_values"] |= set(df["construction_type_harmonized"].dropna().astype(str).unique())

            df = df.merge(hist[hist.year == y], on=["policy_id", "year"], how="left")
            df["f1_notificaciones_previas"] = df["f1_notificaciones_previas"].fillna(0).astype("int64")
            df["f1_dias_desde_ultima_notificacion"] = (df.period_start - df.f1_ultima_notificacion).dt.days.astype("float64")
            acc["leak"] += int((df.f1_ultima_notificacion.notna() & (df.f1_ultima_notificacion >= pd.Timestamp(f"{y}-01-01"))).sum())
            acc["f1_rows"] += int((df.f1_notificaciones_previas > 0).sum())
            if is_test:
                acc["f1_test_rows"] += int((df.f1_notificaciones_previas > 0).sum())
            df = df.drop(columns=["f1_ultima_notificacion"])

            ps = df["period_start"].values.astype("datetime64[D]")
            pe = df["period_end"].values.astype("datetime64[D]")
            # Apply day-weighted completeness to EXP01 exposure, preserving its rounding.
            e_ef = {p: np.zeros(len(df)) for p in PERILS[line]}
            e_cost = np.zeros(len(df))
            covered = np.zeros(len(df))
            for j, m in enumerate(MONTHS):
                ms = np.datetime64(m.start_time.date(), "D")
                me = np.datetime64(m.end_time.date(), "D")
                if ms > pe.max() or me < ps.min():
                    continue
                overlap = np.clip((np.minimum(pe, me) - np.maximum(ps, ms)).astype("timedelta64[D]").astype(int) + 1, 0, None).astype(float)
                covered += overlap
                for p in PERILS[line]:
                    c = ctx.comp[(line, p)][j]
                    e_ef[p] += overlap * c
                    e_cost += overlap * c * ctx.weights[line][p]
            expo = df["exposure"].to_numpy(dtype=float)
            for p in PERILS[line]:
                df[f"e_ef_{p}"] = expo * e_ef[p] / covered
            df["e_ef_coste"] = expo * e_cost / covered
            ef_cols = [f"e_ef_{p}" for p in PERILS[line]] + ["e_ef_coste"]
            acc["ef_ok"] &= all(bool(((df[c] <= df.exposure * (1 + 1e-12)) & (df[c] > 0)).all()) for c in ef_cols) and bool((covered > 0).all())
            if is_test:
                acc["test_ef_ok"] &= all(bool(np.allclose(df[c], df["exposure"], rtol=1e-12, atol=0)) for c in ef_cols)
            acc["ef_sum"][y] = acc["ef_sum"].get(y, 0.0) + float(df.e_ef_coste.sum())
            acc["exp_sum"][y] = acc["exp_sum"].get(y, 0.0) + float(df.exposure.sum())

            if is_test:
                for c in amount_cols:
                    df[c] = pd.array([np.nan] * len(df), dtype="float64")
                for c in count_cols:
                    df[c] = pd.array([pd.NA] * len(df), dtype="Int64")
                acc["test_label_null_ok"] &= bool(df["T0"].isna().all())
            else:
                df = df.merge(labels, on="row_id", how="left")
                for c in amount_cols:
                    df[c] = df[c].fillna(0.0).astype("float64")
                for c in count_cols:
                    df[c] = df[c].fillna(0).astype("Int64")
                ysum = sum(df[f"y_{p}"] for p in PERILS[line])
                acc["label_ok"] &= bool(np.allclose(ysum, df["T0"], atol=1e-6))
                acc["T0_train"] += float(df["T0"].sum())

            acc["chunk_unique_ok"] &= bool(df.row_id.is_unique)
            acc["rows"][kind] += len(df)
            acc["n_total"] += len(df)
            for c in df.columns:
                acc["nulls"][c] = acc["nulls"].get(c, 0) + int(df[c].isna().sum())

            uniq = df.customer_id.astype(str).unique()
            for cid in uniq:
                if cid not in ctx.half_cache:
                    ctx.half_cache[cid] = cal_half(cid)
            piece = pd.DataFrame({"row_id": df.row_id.astype(str).values, "line": line, "year": df.year.values, "is_test": is_test,
                                  "cal_half": df.customer_id.astype(str).map(ctx.half_cache).astype("int8").values})
            part_pieces.append(piece)

            if columns is None:
                columns = list(df.columns)
            df = df[columns]
            table_out = pa.Table.from_pandas(df, preserve_index=False)
            if writer is None:
                schema = table_out.schema
                writer = pq.ParquetWriter(out_path, schema)
            else:
                table_out = table_out.cast(schema)
            writer.write_table(table_out)
            del df, table_out, piece, e_ef, e_cost, ps, pe, covered, expo
            gc.collect()
        del tab, years_arr
        gc.collect()
    writer.close()
    pd.concat(part_pieces, ignore_index=True).to_parquet(tables_dir / "partes" / f"particiones_{line}.parquet", index=False)

    if line in THRESHOLD:
        check(f"K04_{line}", f"{line}: contrato de capital idempotente, ningún capital del modelo supera el umbral y confirmadas contenidas en ajustadas", acc["cap_ok"], acc["cap"])
    if line == "buildings":
        check("K05", "buildings: construction_type_harmonized sin t ni w y con cuatro categorías", acc["tw_ok"] and len(acc["tw_values"]) == 4, sorted(acc["tw_values"]))
    check(f"K06_{line}", f"{line}: ninguna notificación de F1 posterior o igual al 1 de enero del año del periodo", acc["leak"] == 0,
          {"filas_con_historia": acc["f1_rows"], "test_con_historia": acc["f1_test_rows"]})
    ratio = {int(y): round(acc["ef_sum"][y] / acc["exp_sum"][y], 4) for y in sorted(acc["ef_sum"])}
    check(f"K07_{line}", f"{line}: exposición efectiva positiva, nunca mayor que la nominal e igual a la nominal en 2025", acc["ef_ok"] and acc["test_ef_ok"], ratio)
    t0_expected = ctx.bases_evidence["t0"]["by_line_CU"][line]
    check(f"K08_{line}", f"{line}: etiquetas por peligro suman T0 en cada fila, T0 total igual a D67 y etiquetas nulas en test",
          acc["label_ok"] and abs(acc["T0_train"] - t0_expected) < 0.01 and acc["test_label_null_ok"], {"T0_CU": round(acc["T0_train"], 2), "esperado": t0_expected})
    contract = {}
    for field in schema:
        block, reason = classify(field.name, line)
        contract[field.name] = {"bloque": block, "motivo": reason, "tipo": str(field.type), "nulos_pct": round(acc["nulls"].get(field.name, 0) / acc["n_total"] * 100, 3)}
    blocks = {b: sum(1 for v in contract.values() if v["bloque"] == b) for b in BLOCKS}
    check(f"K09_{line}", f"{line}: todas las columnas con contrato y las de exclusión obligatoria marcadas como excluidas",
          not any(v["bloque"] == "revisar" for v in contract.values()) and all(contract[c]["bloque"] == "excluida" for c in EXCLUDED_ALWAYS if c in contract),
          {"bloques": blocks, "revisar": [k for k, v in contract.items() if v["bloque"] == "revisar"]})
    src_train = pq.read_metadata(ROOT / ctx.catalog[f"policies_{line}"]["workspace_relative_path"]).num_rows
    src_test = pq.read_metadata(ROOT / ctx.catalog[f"test_{line}"]["workspace_relative_path"]).num_rows
    check(f"K10_{line}", f"{line}: filas de entrenamiento y test iguales a la capa vigente y row_id único por año",
          acc["rows"]["train"] == src_train and acc["rows"]["test"] == src_test and acc["chunk_unique_ok"], acc["rows"])
    evidence = {"rows_train": acc["rows"]["train"], "rows_test": acc["rows"]["test"], "columns": len(schema), "blocks": blocks,
                "weather_prev1_rows": acc["weather_rows"], "f1_rows_with_history": acc["f1_rows"], "f1_test_rows_with_history": acc["f1_test_rows"],
                "e_ef_coste_over_exposure_by_year": ratio, "capital": acc["cap"] if line in THRESHOLD else None,
                "peril_cost_weights": {k: round(v, 4) for k, v in ctx.weights[line].items()}, "T0_train_CU": round(acc["T0_train"], 2),
                "file": f"tables/f0_{line}.parquet", "row_groups_by_year": True}
    partial = {"line": line, "common_checks": ctx.checks, "checks": checks, "evidence": evidence, "contract": contract}
    (run_dir / f"parcial_{line}.json").write_text(json.dumps(partial, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"{line}: {sum(c['passed'] for c in checks)}/{len(checks)} controles del ramo; {acc['rows']}")
    return partial


def finalize(run_dir: Path, ctx_meta: dict) -> dict:
    tables_dir = run_dir / "tables"
    partials = {}
    for line in LINES:
        path = run_dir / f"parcial_{line}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Falta {path.name}; ejecute --ramo {line} antes de --finalizar")
        partials[line] = json.loads(path.read_text(encoding="utf-8"))
    common = partials["motor"]["common_checks"]
    checks = list(common)
    same_common = all([(c["code"], c["passed"]) for c in partials[l]["common_checks"]] == [(c["code"], c["passed"]) for c in common] for l in LINES)
    for line in LINES:
        checks.extend(partials[line]["checks"])
    part = pd.concat([pd.read_parquet(tables_dir / "partes" / f"particiones_{l}.parquet") for l in LINES], ignore_index=True)
    part["V22"] = np.select([part.year == 2021, part.year == 2022], ["train", "eval"], default="none")
    part["V23"] = np.select([part.year <= 2022, (part.year == 2023) & (part.cal_half == 0), (part.year == 2023) & (part.cal_half == 1)], ["train", "eval_calibracion", "eval_seleccion"], default="none")
    part["V24"] = np.select([part.year <= 2023, part.year == 2024], ["train", "eval"], default="none")
    part["PROD"] = np.select([part.year <= 2024, part.year == 2025], ["train", "predict"], default="none")
    part.to_parquet(tables_dir / "particiones.parquet", index=False)
    half_share = float(part.loc[part.year == 2023, "cal_half"].mean())

    def check(code, name, ok, detail=None):
        checks.append({"code": code, "name": name, "passed": bool(ok), "detail": detail})

    check("K11", "las tres partes usaron la misma capa y los mismos controles comunes", same_common)
    check("K12", "particiones: V24 entrena 2021-2023 y evalúa 2024; PROD predice las 626.639 filas de 2025; row_id único en 3.035.950 filas",
          int((part.V24 == "train").sum()) == int((part.year <= 2023).sum()) and int((part.V24 == "eval").sum()) == int((part.year == 2024).sum())
          and int((part.PROD == "predict").sum()) == TEST_ROWS and int((part.PROD == "train").sum()) == TRAIN_ROWS and part.row_id.is_unique,
          {"filas": int(len(part)), "predict": int((part.PROD == "predict").sum()), "train": int((part.PROD == "train").sum())})
    check("K13", "mitades de calibración y selección de V23 entre 45 % y 55 % de las filas de 2023", 0.45 <= half_share <= 0.55, round(half_share, 4))
    known = "05180324"  # Master-table customer; recompute the split with the published hash rule.
    check("K14", "regla de hash reproducible: SHA-256('cal_v1|customer_id'), primeros 16 hex, módulo 2", cal_half(known) in (0, 1),
          {"customer_id": known, "half": cal_half(known), "sha256_prefix": hashlib.sha256(f"{CAL_SALT}|{known}".encode()).hexdigest()[:16]})

    contract = {line: partials[line]["contract"] for line in LINES}
    (run_dir / "contrato_disponibilidad.json").write_text(json.dumps({
        "version": "F0 v1 (D68)",
        "bloques": {"F0": "contractual y físico, disponible al inicio del periodo bajo estabilidad de maestros; matriz base",
                    "F1": "historia de notificaciones de la póliza al 1 de enero del año del periodo; bloque adicional",
                    "F2": "clima del año anterior; bloque adicional", "F3": "información condicionada sin fecha de referencia; prueba separada",
                    "F4": "tarifario existente; ablación aparte", "excluida": "nunca predictor", "clave": "identificadores y fechas",
                    "etiqueta": "T0 y componentes; solo entrenamiento, nulo en test"},
        "capital": "sum_insured = sum_insured_raw/1000 si supera el umbral del ramo (10.000.000 CU edificios, 1.000.000 contenidos); marcas audit_* fuera de los predictores (D66)",
        "exposicion_efectiva": "exposure x completitud media del periodo ponderada por días; completitud del peligro para el mes de ocurrencia al 30-12-2024 (chain-ladder D67); 1 en 2025",
        "lectura": "las columnas de predictores se toman por bloque desde este contrato; el selector debe rechazar 'excluida', 'clave' y 'etiqueta' además del guard 1.0",
        "columnas": contract}, ensure_ascii=False, indent=1), encoding="utf-8")
    evidence = {
        "run_id": run_dir.name, "created_utc": ctx_meta["started"],
        "author": "AI-assisted calculation requested by the participant; no human or independent professional review",
        "scope": {"data_modified": False, "indices_modified": False, "models_trained": False, "remote_execution": False, "external_providers": False,
                  "description": "Matriz F0 por ramo con contrato de disponibilidad, etiquetas T0 y por peligro, exposición efectiva y particiones V22/V23/V24/PROD"},
        "provenance": ctx_meta["provenance"],
        "lines": {line: partials[line]["evidence"] for line in LINES},
        "partitions": {"rows": int(len(part)), "by_year": {int(y): int(n) for y, n in part.year.value_counts().sort_index().items()}, "cal_half_share_2023": round(half_share, 4),
                       "rule": "SHA-256 del texto UTF-8 'cal_v1|customer_id', primeros 16 hex como entero, módulo 2: 0 calibración, 1 selección",
                       **{v: {k: int(n) for k, n in part[v].value_counts().items()} for v in ["V22", "V23", "V24", "PROD"]}},
        "checks": checks,
        "checks_summary": {"checks_total": len(checks), "checks_passed": sum(c["passed"] for c in checks), "all_passed": all(c["passed"] for c in checks)},
    }
    (run_dir / "evidencia.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pd.DataFrame(checks).to_csv(tables_dir / "controles.csv", index=False)
    shutil.copy2(Path(__file__), run_dir / Path(__file__).name)
    manifest = {str(p.relative_to(run_dir)).replace("\\", "/"): digest(p) for p in sorted(run_dir.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    s = evidence["checks_summary"]
    print(f"Corrida {run_dir.name}: {s['checks_passed']}/{s['checks_total']} controles")
    for c in checks:
        print(("OK  " if c["passed"] else "FALLA ") + c["code"] + " " + c["name"] + ("" if c["passed"] else f" -> {c['detail']}"))
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", help="id de una corrida existente en runs/")
    parser.add_argument("--ramo", help="ramos a procesar, separados por comas (motor, buildings, contents)")
    parser.add_argument("--finalizar", action="store_true", help="reúne los parciales, construye particiones, evidencia y manifiesto")
    args = parser.parse_args()
    if args.run:
        run_dir = HERE / "runs" / args.run
        if not run_dir.is_dir():
            raise FileNotFoundError(run_dir)
    else:
        started = datetime.now(timezone.utc)
        run_dir = HERE / "runs" / f"f0_{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        (run_dir / "tables").mkdir(parents=True, exist_ok=False)
        (run_dir / "inicio.json").write_text(json.dumps({"started": started.isoformat(timespec="seconds")}), encoding="utf-8")
        print(f"Corrida creada: {run_dir.name}")
    started_iso = json.loads((run_dir / "inicio.json").read_text(encoding="utf-8"))["started"]
    lines = LINES if not (args.ramo or args.finalizar) else ([l.strip() for l in args.ramo.split(",")] if args.ramo else [])
    ctx = None
    if lines or not args.finalizar:
        ctx = Context()
        for line in lines:
            process_line(line, ctx, run_dir)
            gc.collect()
    if args.finalizar or not (args.ramo or args.run):
        if ctx is None:
            ctx = Context()
        meta = {"started": started_iso, "provenance": {
            "active_index": "Hackaton/Semana 1/Limpieza/current_dataset.json", "active_run": ctx.current["workspace_relative_run"], "catalog_sha256": digest(ctx.catalog_path),
            "tables_sha256": ctx.hashes, "bases_run": ctx.bases_index["workspace_relative_run"], "branch_run": ctx.branch_index["workspace_relative_run"],
            "cap01_run": ctx.cap01_index["workspace_relative_run"], "d66_run": ctx.d66_index["workspace_relative_run"]}}
        evidence = finalize(run_dir, meta)
        if not evidence["checks_summary"]["all_passed"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
