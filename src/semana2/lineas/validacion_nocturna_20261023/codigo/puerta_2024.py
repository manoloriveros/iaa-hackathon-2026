"""Puerta de confirmación 2024 (implementación propia de los números de SEL01, política S2-SELECCION-v1-20261023).

Una sola apertura. Lee las predicciones congeladas (SHA comprobado contra la preinscripción) y las etiquetas 2024.
Primaria: D² Tweedie 1,5 global sin pesos sobre las 59.202 filas de 2024 (T0 observado; vínculo de observación e_ef
fijado con ocurrencias <= 2023). Bootstrap ordinario de componentes cliente-dirección, 10.000 réplicas, semilla 2026102301,
mismos sorteos para todos los pares; seis pares; Bonferroni alfa 0,05 bilateral -> cuantil inferior 0,0041667.
Promoción secuencial: titular R0; cada aspirante en orden reemplaza al titular solo si el límite inferior de su diferencia
frente al titular es > 0,0005 y pasan las salvaguardas (cliente nuevo, cuatro escenarios, cinco segmentos, influencia,
nivel). Uso: python puerta_2024.py preinscripcion.json
"""
import hashlib, json, math, pathlib, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); C = R / 'salidas/conf'
pre = json.load(open(sys.argv[1]))
pf = C / 'predicciones/predicciones_2024.parquet'
assert hashlib.sha256(pf.read_bytes()).hexdigest() == pre['predicciones_sha256'], 'predicciones cambiadas'
P = pd.read_parquet(pf)
MODELS = pre['orden']  # ['R0', 'A1', 'A2', 'A3']
SIM = '--simular' in sys.argv  # ensayo del evaluador con etiquetas sintéticas; no lee 2024
P = P.set_index('row_id')
if SIM:
    rs = np.random.default_rng(99); mu = P['A1'].values
    n = rs.poisson(mu / 2500.0); sev = rs.gamma(1.2, 2500.0 / 1.2, size=len(mu))
    t0 = n * sev
    L = pd.DataFrame({'t0': t0, 'paid': t0 * 0.8, 'incurred': t0, 'recov': 0.0, 'late': t0 * 0.2}, index=P.index)
else:  # etiquetas 2024 (primera y única lectura)
    lab = []
    for line in ['motor', 'buildings', 'contents']:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet')
        b = b[b.year == 2024]
        late = b.get('t0_bodily_injury', pd.Series(0.0, index=b.index)).fillna(0) + b.get('t0_subsidence', pd.Series(0.0, index=b.index)).fillna(0)
        lab.append(pd.DataFrame({'row_id': b.row_id, 't0': b.t0, 'paid': b.paid, 'incurred': b.incurred, 'recov': b.recov, 'late': late}))
    L = pd.concat(lab, ignore_index=True).set_index('row_id').loc[P.index]
assert len(P) == 59202
y = L.t0.values
seen23 = set()
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet'); seen23 |= set(b.loc[b.year == 2023, 'customer_id'])
cold = ~P.customer_id.isin(seen23).values
comp = M.components(P.customer_id.values, P.address_id.values); K = comp.max() + 1
MU = {m: P[m].values for m in MODELS}
rng = np.random.default_rng(pre['semilla']); NB = pre['replicas']


def d2_boot(yv, mus, compv, n=NB, seed=pre['semilla']):
    """Bootstrap ordinario de componentes (multinomial), mismos sorteos para todos los modelos."""
    Kc = compv.max() + 1
    agg = lambda v: np.bincount(compv, weights=v, minlength=Kc)
    Sy, Sy2, Sn = agg(yv), agg(np.power(yv, 0.5)), agg(np.ones_like(yv))
    Sd = {k: agg(M.dev(yv, m)) for k, m in mus.items()}
    r = np.random.default_rng(seed); out = {k: [] for k in mus}
    for s in range(0, n, 200):
        nb = min(200, n - s)
        W = np.stack([np.bincount(r.integers(0, Kc, Kc), minlength=Kc) for _ in range(nb)]).astype(float)
        ny, nn, ny2 = W @ Sy, W @ Sn, W @ Sy2; c = ny / nn
        null = 2 * (ny2 / ((1 - 1.5) * (2 - 1.5)) - ny * np.power(c, -0.5) / (1 - 1.5) + nn * np.power(c, 0.5) / 0.5)
        for k in mus: out[k].append(1 - (W @ Sd[k]) / null)
    return {k: np.concatenate(v) for k, v in out.items()}


t0 = time.time()
res = {'abierta_utc': pd.Timestamp.now(tz='UTC').isoformat(), 'filas': int(len(P)), 'componentes': int(K),
       'cliente_nuevo_filas': int(cold.sum())}
res['D2'] = {m: round(float(M.d2(y, MU[m])), 6) for m in MODELS}
res['D2_por_ramo'] = {m: {l: round(float(M.d2(y[P.line.values == l], MU[m][P.line.values == l])), 6) for l in ['motor', 'buildings', 'contents']} for m in MODELS}
res['AE'] = {m: {l: round(float(y[P.line.values == l].sum() / MU[m][P.line.values == l].sum()), 4) for l in ['motor', 'buildings', 'contents']} for m in MODELS}
B = d2_boot(y, MU, comp)
q = pre['cuantil_inferior']
pairs = {}
for i, a in enumerate(MODELS):
    for b_ in MODELS[i + 1:]:
        d = B[b_] - B[a]
        pairs[f'{b_}-{a}'] = {'diff': round(float(res['D2'][b_] - res['D2'][a]), 6), 'lower': round(float(np.quantile(d, q)), 6),
                              'upper': round(float(np.quantile(d, 1 - q)), 6), 'P_gt0': round(float((d > 0).mean()), 4)}
res['pares'] = pairs


def safeguards(ch, inc):
    s = {}
    # cliente nuevo
    yc = y[cold]; cc = pd.factorize(comp[cold])[0]
    Bc = d2_boot(yc, {ch: MU[ch][cold], inc: MU[inc][cold]}, cc, n=2000, seed=pre['semilla'] + 1)
    dc = Bc[ch] - Bc[inc]
    s['cliente_nuevo'] = {'diff': round(float(M.d2(yc, MU[ch][cold]) - M.d2(yc, MU[inc][cold])), 6), 'lower95': round(float(np.quantile(dc, 0.05)), 6)}
    s['cliente_nuevo']['pasa'] = s['cliente_nuevo']['diff'] >= 0 and s['cliente_nuevo']['lower95'] >= -0.001
    # escenarios
    sc = {}
    for name, yy in (('reserve075', L.paid + 0.75 * (L.incurred - L.paid) - L.recov), ('reserve125', L.paid + 1.25 * (L.incurred - L.paid) - L.recov),
                     ('late_cost05', L.t0 + 0.05 * L.late), ('late_cost10', L.t0 + 0.10 * L.late)):
        yy = yy.values
        dd = M.d2(yy, MU[ch]) - M.d2(yy, MU[inc]); sc[name] = {'diff': round(float(dd), 6), 'pasa': bool(dd >= 0)}
    s['escenarios'] = sc
    # segmentos
    seg = {}
    for name, m in (('motor', P.line.values == 'motor'), ('buildings', P.line.values == 'buildings'), ('contents', P.line.values == 'contents'),
                    ('new_customer', cold), ('renewal', ~cold)):
        dd = M.d2(y[m], MU[ch][m]) - M.d2(y[m], MU[inc][m]); seg[name] = {'diff': round(float(dd), 6), 'pasa': bool(dd >= -0.001)}
    s['segmentos'] = seg
    # influencia: retirar los grupos más favorables al aspirante
    gain = np.bincount(comp, weights=M.dev(y, MU[inc]) - M.dev(y, MU[ch]), minlength=K)
    k = min(K - 1, max(5, math.ceil(0.001 * K)))
    drop = set(np.argsort(-gain)[:k]); keep = ~np.isin(comp, list(drop))
    dd = M.d2(y[keep], MU[ch][keep]) - M.d2(y[keep], MU[inc][keep])
    s['influencia'] = {'grupos_retirados': int(k), 'diff': round(float(dd), 6), 'pasa': bool(dd >= 0)}
    s['pasa_todas'] = bool(s['cliente_nuevo']['pasa'] and all(v['pasa'] for v in sc.values()) and all(v['pasa'] for v in seg.values()) and s['influencia']['pasa'])
    return s


inc = MODELS[0]; actas = []
for ch in MODELS[1:]:
    pr = pairs.get(f'{ch}-{inc}')
    sg = safeguards(ch, inc)
    nivel = pre['nivel_2025'].get(ch, {})
    nivel_ok = nivel.get('condicion_cumplida', False)
    promueve = (pr['lower'] > pre['delta_min']) and sg['pasa_todas'] and nivel_ok
    actas.append({'aspirante': ch, 'titular': inc, 'par': pr, 'salvaguardas': sg, 'nivel_2025': nivel, 'promueve': bool(promueve)})
    if promueve: inc = ch
res['actas'] = actas; res['titular_final'] = inc; res['segundos'] = round(time.time() - t0, 1)
json.dump(res, open(C / ('puerta_2024_SIMULADA.json' if SIM else 'puerta_2024_resultado.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
