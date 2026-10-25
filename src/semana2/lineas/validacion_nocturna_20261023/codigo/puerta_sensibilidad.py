"""Sensibilidad del acta de la puerta 2024 a tres diferencias de implementación señaladas por la auditoría de Codex
(COD-S2-IA-20261024T052608Z): réplicas y cuantil de la salvaguarda de cliente nuevo (2.000 y 0,05 aquí; 10.000 y 0,025
en el motor común) y decisiones tomadas con valores redondeados a seis decimales.

No cambia el acta ni vuelve a decidir: lee las mismas predicciones congeladas (SHA comprobado) y las mismas etiquetas
de 2024 ya abiertas, recalcula sin redondeo y con las variantes, y dice si alguna variante cambiaría algún veredicto.
Escribe salidas/conf/puerta_sensibilidad.json; no toca puerta_2024_resultado.json.
"""
import hashlib, json, math, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); C = R / 'salidas/conf'
pre = json.load(open(R / 'preinscripcion/preinscripcion_puerta_2024.json'))
acta = json.load(open(C / 'puerta_2024_resultado.json'))
pf = C / 'predicciones/predicciones_2024.parquet'
assert hashlib.sha256(pf.read_bytes()).hexdigest() == pre['predicciones_sha256']
P = pd.read_parquet(pf).set_index('row_id')
lab = []
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet'); b = b[b.year == 2024]
    lab.append(pd.DataFrame({'row_id': b.row_id, 't0': b.t0}))
L = pd.concat(lab, ignore_index=True).set_index('row_id').loc[P.index]
y = L.t0.values
seen23 = set()
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet'); seen23 |= set(b.loc[b.year == 2023, 'customer_id'])
cold = ~P.customer_id.isin(seen23).values
comp = M.components(P.customer_id.values, P.address_id.values); K = comp.max() + 1
MU = {m: P[m].values for m in pre['orden']}


def boot(yv, mus, compv, n, seed):
    """Igual que d2_boot de puerta_2024.py (multinomial por componente, mismos sorteos para todos)."""
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


out = {'fuente': 'COD-S2-IA-20261024T052608Z', 'acta_sha256': hashlib.sha256((C / 'puerta_2024_resultado.json').read_bytes()).hexdigest()}
# 1) par primario sin redondeo
B = boot(y, MU, comp, pre['replicas'], pre['semilla'])
q = pre['cuantil_inferior']
prim = {}
for ch in ['A1', 'A2']:
    d = B[ch] - B['R0']
    lo = float(np.quantile(d, q)); diff = float(M.d2(y, MU[ch]) - M.d2(y, MU['R0']))
    prim[ch] = {'diff': diff, 'lower': lo, 'lower_acta': acta['pares'][f'{ch}-R0']['lower'], 'pasa_primaria': lo > pre['delta_min']}
out['primaria_sin_redondeo'] = prim
# 2) cliente nuevo: variantes de réplicas, semilla y cuantil
yc = y[cold]; cc = pd.factorize(comp[cold])[0]
cn = {}
for ch in ['A1', 'A2']:
    diff = float(M.d2(yc, MU[ch][cold]) - M.d2(yc, MU['R0'][cold]))
    v = {'diff': diff}
    for n, seed, tag in ((2000, pre['semilla'] + 1, 'acta_2000'), (10000, pre['semilla'] + 1, 'n10000'), (10000, pre['semilla'] + 7, 'n10000_otra_semilla')):
        Bc = boot(yc, {ch: MU[ch][cold], 'R0': MU['R0'][cold]}, cc, n, seed); dc = Bc[ch] - Bc['R0']
        v[tag] = {'q050': float(np.quantile(dc, 0.05)), 'q025': float(np.quantile(dc, 0.025)), 'P_mayor_menos0001': float((dc >= -0.001).mean())}
    v['pasa_en_alguna_variante'] = bool(diff >= 0 and any(v[t][qq] >= -0.001 for t in ('acta_2000', 'n10000', 'n10000_otra_semilla') for qq in ('q050', 'q025')))
    v['margen_al_umbral_acta'] = v['acta_2000']['q050'] + 0.001
    cn[ch] = v
out['cliente_nuevo'] = cn
# 3) márgenes sin redondeo del resto de salvaguardas (para ver si algún redondeo pudo decidir)
marg = {}
for ch in ['A1', 'A2']:
    m = {}
    for name, msk in (('motor', P.line.values == 'motor'), ('buildings', P.line.values == 'buildings'), ('contents', P.line.values == 'contents'),
                      ('new_customer', cold), ('renewal', ~cold)):
        m[f'segmento_{name}'] = float(M.d2(y[msk], MU[ch][msk]) - M.d2(y[msk], MU['R0'][msk])) + 0.001
    gain = np.bincount(comp, weights=M.dev(y, MU['R0']) - M.dev(y, MU[ch]), minlength=K)
    k = min(K - 1, max(5, math.ceil(0.001 * K))); keep = ~np.isin(comp, np.argsort(-gain)[:k])
    m['influencia'] = float(M.d2(y[keep], MU[ch][keep]) - M.d2(y[keep], MU['R0'][keep]))
    m['minimo'] = min(m.values())
    marg[ch] = m
out['margenes_sin_redondeo'] = marg
out['redondeo_pudo_decidir'] = bool(min(min(abs(v) for v in marg[ch].values()) for ch in marg) < 5e-7)
out['veredicto_cambia'] = bool(any(cn[ch]['pasa_en_alguna_variante'] for ch in cn))
json.dump(out, open(C / 'puerta_sensibilidad.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
