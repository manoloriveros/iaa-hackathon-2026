"""Build comparable F0 features for both markets under the frozen availability contract.
Exclude renewal_decision, current-period service contacts, identifiers, surname,
claim amounts and same-year weather. Written premium and discounts are reserved
for separate tariff ablations. Normalize occupation text, construction codes,
household insured values and developed ages into the emerging age bands.
"""
import pathlib
import numpy as np, pandas as pd

R = pathlib.Path('__RUN_ROOT__/noche')
# CON-N1 maps emerging construction codes and developed t/w aliases to one vocabulary.
# Recorded mix: brick 70%, t+w 12.6%, non_standard 9.9%, stone 8.0%; emerging BRK 70%, WOD 12.0%, MIX 10.1%, STN 7.9%.
CONS = {'BRK': 'brick', 'STN': 'stone', 'WOD': 'timber', 'MIX': 'non_standard', 'T': 'timber', 'W': 'timber'}
CAP_THR = {'buildings': 5_000_000, 'contents': 2_000_000}  # Thresholds lie within the observed insured-value gaps (894k-60M and 283k-7.6M).
BANDS = [(17, 24, '17-24'), (25, 34, '25-34'), (35, 49, '35-49'), (50, 64, '50-64'), (65, 200, '65+')]

POL_COMMON = ['start_month', 'voluntary_excess', 'compulsory_excess', 'channel', 'payment_method', 'missed_payments_12m',
              'new_business', 'renewal_count', 'days_quote_to_inception']
# VAR-N1 excludes previous_insurer, branch_id, email_domain, marketing_consent, document_preference
# and self_employed under the recorded developed-frequency diagnostics.
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
    """Build (X,columns) from a policy-row base containing year and exposure_model."""
    d = pd.read_parquet(R / f'datos/{market}/customers.parquet')
    a = pd.read_parquet(R / f'datos/{market}/addresses.parquet')
    occ = d.occupation.astype('string').str.strip().str.lower()
    d['self_employed'] = occ.str.startswith('self-employed').fillna(False)
    d['occupation_n'] = occ.str.replace(r'^self-employed\s+', '', regex=True).str.replace(r'\s+', ' ', regex=True)
    d['has_campaign'] = d.campaign_code.notna()
    # ID01: pad developed motor customer_id to eight characters for the master-data join.
    # Corrected on 23 October: the initial version omitted padding and left
    # 98,110 training and 25,554 test motor rows without customer features.
    key = base.customer_id.astype(str) if __import__('os').environ.get('A1_PRE_ID01') else base.customer_id.astype(str).str.zfill(8)
    df = base.assign(_cid=key.values).merge(d.drop(columns=['surname'], errors='ignore').rename(columns={'customer_id': '_cid'}),
                                            on='_cid', how='left', validate='m:1').drop(columns=['_cid'])
    assert __import__('os').environ.get('A1_PRE_ID01') or df.customer_since_year.notna().all(), 'cruce de clientes incompleto'
    df = df.merge(a, on='address_id', how='left', validate='m:1')
    df['cust_tenure'] = df.year - df.customer_since_year
    df['start_month'] = pd.to_datetime(df.period_start).dt.month  # NB-N2: calendar features capture part of the new-business effect.
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
    """base adds no weather; otro uses the other training year and the 2023-2024 mean for 2025."""
    w = pd.read_parquet(R / f'datos/{market}/weather.parquet')
    w = w[w.year.isin([2023, 2024])].pivot_table(index='address_id', columns='year', values=vars_)
    out = pd.DataFrame(index=df.index)
    for v in vars_:
        a23 = df.address_id.map(w[(v, 2023)]); a24 = df.address_id.map(w[(v, 2024)])
        out[f'w_{v}'] = np.where(df.year == 2023, a24, np.where(df.year == 2024, a23, (a23 + a24) / 2))
    return out
