"""Variables F0 por ramo, para los dos mercados, con el mismo esquema común.

Excluidas por contrato (decididas antes de medir): renewal_decision (solo en entrenamiento), customer_service_contacts
(mide el siniestro del propio periodo), written_premium y discount_applied (tarifa vigente, F4, solo ablación),
identificadores, surname, importes de siniestros, clima del propio año.
Normalizaciones: ocupación a minúsculas sin espacios sobrantes ni prefijo «self-employed » (marca aparte);
códigos de construcción emergentes a la nomenclatura del desarrollado; capital de hogar con la regla CAP-N1;
edad del desarrollado a las bandas emergentes (17-24, 25-34, 35-49, 50-64, 65+).
"""
import pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
# CON-N1: códigos locales emergentes y alias t/w del desarrollado a una sola nomenclatura. Evidencia: proporciones
# brick 70 %, t+w 12,6 %, non_standard 9,9 %, stone 8,0 % (desarrollado) frente a BRK 70 %, WOD 12,0 %, MIX 10,1 %, STN 7,9 %.
CONS = {'BRK': 'brick', 'STN': 'stone', 'WOD': 'timber', 'MIX': 'non_standard', 'T': 'timber', 'W': 'timber'}
CAP_THR = {'buildings': 5_000_000, 'contents': 2_000_000}  # dentro de los huecos medidos (894k-60M y 283k-7,6M)
BANDS = [(17, 24, '17-24'), (25, 34, '25-34'), (35, 49, '35-49'), (50, 64, '50-64'), (65, 200, '65+')]

POL_COMMON = ['start_month', 'voluntary_excess', 'compulsory_excess', 'channel', 'payment_method', 'missed_payments_12m',
              'new_business', 'renewal_count', 'days_quote_to_inception']
# VAR-N1: fuera previous_insurer, branch_id, email_domain, marketing_consent, document_preference y la marca
# self_employed: sin señal de frecuencia en el desarrollado (chi2/gl entre 0,15 y 2,1 con 1,9 millones de filas; ver bitácora).
CUST = ['occupation_n', 'marital_status', 'household_size', 'prior_claims_5y', 'licence_points',
        'years_at_address', 'cust_tenure', 'has_campaign', 'marketing_segment']
ADDR = ['region', 'urban_density', 'flood_zone', 'distance_to_river_km', 'elevation_m', 'soil_type', 'prop_age',
        'property_type', 'roof_type', 'basement', 'trees_within_5m', 'listed_building', 'bedrooms', 'energy_rating',
        'solar_panels']
LINE = {'motor': ['age_band', 'years_licensed', 'ncb_years', 'vehicle_value_group', 'vehicle_age', 'make_model',
                  'engine_size_cc', 'body_type', 'transmission', 'seats', 'vehicle_colour', 'fuel_type',
                  'driver_assist', 'cover_type', 'overnight_parking', 'vehicle_use', 'named_young_driver'],
        'buildings': ['age_band', 'log_si', 'construction_type', 'occupancy', 'days_unoccupied', 'smoke_alarms',
                      'accidental_damage_cover', 'mortgage'],
        'contents': ['age_band', 'log_si', 'tenure', 'security_level', 'high_value_items', 'accidental_damage_cover',
                     'works_from_home', 'lodgers', 'bicycle_cover']}
CATEG = {'channel', 'payment_method', 'occupation_n', 'marital_status', 'email_domain', 'document_preference',
         'previous_insurer', 'branch_id', 'marketing_segment', 'region', 'urban_density', 'soil_type', 'property_type',
         'roof_type', 'energy_rating', 'age_band', 'make_model', 'body_type', 'transmission', 'vehicle_colour',
         'fuel_type', 'cover_type', 'overnight_parking', 'vehicle_use', 'construction_type', 'occupancy',
         'smoke_alarms', 'tenure', 'security_level'}
WEATHER = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm',
           'mean_temperature_c']


def band(age):
    out = pd.Series(pd.NA, index=age.index, dtype='object')
    for lo, hi, lab in BANDS:
        out[(age >= lo) & (age <= hi)] = lab
    return out


def features(base, line, market):
    """base: tabla de filas (de s2_base o equivalente) con year y exposure_model. Devuelve (X, cols)."""
    d = pd.read_parquet(R / f'datos/{market}/customers.parquet')
    a = pd.read_parquet(R / f'datos/{market}/addresses.parquet')
    occ = d.occupation.astype('string').str.strip().str.lower()
    d['self_employed'] = occ.str.startswith('self-employed').fillna(False)
    d['occupation_n'] = occ.str.replace(r'^self-employed\s+', '', regex=True).str.replace(r'\s+', ' ', regex=True)
    d['has_campaign'] = d.campaign_code.notna()
    # ID01 (D32): en autos del desarrollado el customer_id perdió los ceros iniciales; se rellena a ocho posiciones solo para cruzar.
    # Error propio corregido el 23-10 a las 21:25: la primera versión de la noche no lo hacía y 98.110 + 25.554 filas de autos
    # del desarrollado quedaban sin variables de cliente.
    key = base.customer_id.astype(str).str.zfill(8)
    df = base.assign(_cid=key.values).merge(d.drop(columns=['surname'], errors='ignore').rename(columns={'customer_id': '_cid'}),
                                            on='_cid', how='left', validate='m:1').drop(columns=['_cid'])
    assert df.customer_since_year.notna().all(), 'cruce de clientes incompleto'
    df = df.merge(a, on='address_id', how='left', validate='m:1')
    df['cust_tenure'] = df.year - df.customer_since_year
    df['start_month'] = pd.to_datetime(df.period_start).dt.month  # NB-N2: el calendario separa parte del efecto del nuevo negocio
    df['prop_age'] = df.year - df.year_built
    if line == 'motor':
        df['age_band'] = df['driver_age_band'] if 'driver_age_band' in df else band(df['driver_age'])
    else:
        df['age_band'] = df['policyholder_age_band'] if 'policyholder_age_band' in df else band(df['policyholder_age'])
        si = df['sum_insured'].astype(float)
        scale = si > CAP_THR[line]
        df['cap_scaled'] = scale
        df['log_si'] = np.log(np.where(scale, si / 1000.0, si))
    if line == 'buildings':
        df['construction_type'] = df.construction_type.astype('string').str.strip()
        df['construction_type'] = df.construction_type.map(lambda v: CONS.get(v.upper(), v.lower()) if isinstance(v, str) else v)
    if 'smoke_alarms' in df:
        df['smoke_alarms'] = df.smoke_alarms.map({True: 'yes', False: 'no'}).fillna('missing')
    cols = POL_COMMON + CUST + ADDR + LINE[line]
    if market == 's1':
        cols = [c for c in cols if c != 'region']
    X = df[cols].copy()
    for c in cols:
        if c in CATEG:
            X[c] = X[c].astype('string').fillna('missing').astype('category')
        elif X[c].dtype == bool or str(X[c].dtype) == 'boolean':
            X[c] = X[c].astype(float)
        else:
            X[c] = pd.to_numeric(X[c], errors='coerce').astype(float)
    return X, cols, df


def weather_other_year(df, market, vars_, mode):
    """mode='base' nada; 'otro': clima de la dirección en el otro año de entrenamiento (2023↔2024; 2025 = media 23-24)."""
    w = pd.read_parquet(R / f'datos/{market}/weather.parquet')
    w = w[w.year.isin([2023, 2024])].pivot_table(index='address_id', columns='year', values=vars_)
    out = pd.DataFrame(index=df.index)
    for v in vars_:
        a23 = df.address_id.map(w[(v, 2023)]); a24 = df.address_id.map(w[(v, 2024)])
        out[f'w_{v}'] = np.where(df.year == 2023, a24, np.where(df.year == 2024, a23, (a23 + a24) / 2))
    return out
