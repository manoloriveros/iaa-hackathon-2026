"""Sonda de nivel por segmento: diseño y simulación, sin enviar nada (elección del participante, 25-10: «Final + diseñar sonda
por segmento»).

Punto de partida. La sonda global (CLA-S2-SONDA-GLOBAL-20261024) dio, respecto de la mezcla enviada μ, los coeficientes
βA = Σ_s a_s y βB = Σ_s b_s de la fórmula exacta D2(1) − D2(c) = βA (c^−½ − 1) + βB (c^½ − 1), y el archivo final
F = μ × g, con g = 1,1877. Si en una celda s solo se multiplica F por k, la fórmula se separa por celdas:
  D2(F) − D2(F con s × k) = a_s [(gk)^−½ − g^−½] + b_s [(gk)^½ − g^½].
b_s = 4 Σ_{público∩s} μ^½ / nula no necesita envío: si el público es un tercio al azar, b_s ≈ βB × T_s / T, con
T_s = Σ_{test∩s} μ^½ (conocido). Cada envío da entonces a_s exacto (salvo redondeo y esa aproximación), y la celda mayor
(la de más Σμ^½) sale de βA − Σ a_s: S celdas cuestan S − 1 envíos. El óptimo del público en la celda es c*_s = a_s / b_s.

Credibilidad jerárquica: log c_s = log g + Z_s (log c*_s − log c*_g), acotado a c_s / g ∈ [0,75; 1,33], con
Z_s = τ² / (τ² + σ_s²). τ = 0,20 (fijado aquí, antes de ver ninguna puntuación de segmento): desviación logarítmica de cada
celda frente al nivel global; en 2024, con el nivel de 2023, los ramos se desviaron +0,22, −0,36 y +0,08 del global (RMS 0,25)
y el cociente nuevo negocio / renovación osciló entre 0,79 y 1,70 por ramo y año. σ_s es la desviación típica de
log(c*_s / c*_g) en el público menos la del privado, medida por remuestreo al tamaño y la composición de 2025.

Simulación. Dos sustitutos con etiquetas: 2024 (designada A1fixF1b3n con nivel 2023) y 2023 (OOF de desarrollo).
Remuestreo por componentes cliente-dirección hasta 209.063 filas con la composición ramo × nuevo negocio de 2025 (76 % de
nuevo negocio), partición al azar 33/67, puntuaciones redondeadas a 5 decimales y la regla completa (global preinscrita y
luego segmentos). Escenarios de verdad: nulo (sin desviación por celda), como salió el año y previa (desviaciones por celda
sorteadas de N(0; τ²)). Se mide la ganancia en el privado frente al archivo final global. Tres segmentaciones: nuevo negocio
/ renovación (1 envío), ramo (2 envíos) y ramo × nuevo negocio (5 envíos).
Escribe salidas/sonda_segmento/diseno.json.
"""
import io, contextlib, json, pathlib, runpy, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda_segmento'; O.mkdir(exist_ok=True)
N25 = 209063; TAU = 0.20; ZG = 0.854; K = 1.2; REPS = 150; COTA = (0.75, 1.33)
LINES = ['motor', 'buildings', 'contents']
r5 = lambda v: round(float(v), 5)
t0 = time.time()
# composición 2025 por celda (ramo × nuevo negocio)
T = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['split', 'new_business']).query("split == 'test'").assign(line=l) for l in LINES])
TARGET = (T.line + '_' + T.new_business.astype(int).astype(str)).value_counts(normalize=True).to_dict()
# sustitutos
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P = g['P']; y24 = g['y']
B = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['row_id', 'new_business']) for l in LINES]).set_index('row_id').new_business
o = pd.read_parquet(R / 'salidas/s2/oof/A1fixF1b3_nivel.parquet')
POOLS = {'2024': dict(y=np.asarray(y24, float), mu=P['A1fixF1b3n'].values, line=P.line.values, nb=B.loc[P.index].values.astype(int),
                      cust=P.customer_id.values, addr=P.address_id.values),
         '2023': dict(y=o.y.values.astype(float), mu=o.mu.values, line=o.line.values, nb=o.new_business.values.astype(int),
                      cust=o.customer_id.values, addr=o.address_id.values)}
SEGS = {'nb': lambda line, nb: np.where(nb == 1, 'NB', 'REN'), 'ramo': lambda line, nb: line,
        'ramo_nb': lambda line, nb: np.char.add(np.char.add(line.astype(str), '_'), nb.astype(str))}


def copt(yv, m):
    return (yv / np.sqrt(m)).sum() / np.sqrt(m).sum()


def resolver_global(yp, mp):
    d0 = r5(M.d2(yp, mp)); X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c in (0.85, 1.2)])
    a, b = np.linalg.solve(X, np.array([d0 - r5(M.d2(yp, mp * c)) for c in (0.85, 1.2)]))
    return a, b


def una_replica(yy, mm, cell_all, pub, seg_labels, Z):
    """Aplica la regla completa en una réplica. Devuelve dict con ganancia privada y ruido log por celda."""
    prv = ~pub; yp, mp = yy[pub], mm[pub]
    a, b = resolver_global(yp, mp); cg = a / b; gg = float(np.clip(np.exp(ZG * np.log(cg)), 0.75, 1.33))
    dF = r5(M.d2(yp, mp * gg)); Ttot = np.sqrt(mm).sum()
    b_s = {s: b * np.sqrt(mm[seg_labels == s]).sum() / Ttot for s in set(seg_labels)}
    cells = sorted(b_s, key=lambda s: b_s[s]); out = {}; a_s = {}  # la celda mayor se deduce; se sondean las demás
    for s in cells[:-1]:
        f = np.where(seg_labels[pub] == s, K, 1.0)
        ds = r5(M.d2(yp, mp * gg * f))
        a_s[s] = (dF - ds - b_s[s] * ((gg * K) ** 0.5 - gg ** 0.5)) / ((gg * K) ** -0.5 - gg ** -0.5)
    a_s[cells[-1]] = a - sum(a_s.values())
    fac = np.full(len(yy), gg); ruido = {}
    cg_prv = copt(yy[prv], mm[prv])
    for s in cells:
        m_s = seg_labels == s
        cs = a_s[s] / b_s[s] if (a_s[s] > 0 and b_s[s] > 0) else np.nan
        rel = np.exp(Z.get(s, 0.0) * np.log(cs / cg)) if np.isfinite(cs) else 1.0
        fac[m_s] = gg * float(np.clip(rel, *COTA))
        cs_prv = copt(yy[prv & m_s], mm[prv & m_s])
        ruido[s] = (np.log(cs / cg) - np.log(cs_prv / cg_prv)) if np.isfinite(cs) else np.nan
    base_prv = M.d2(yy[prv], mm[prv] * gg)
    orac = np.full(len(yy), 1.0)
    for s in cells:
        m_s = seg_labels == s; orac[m_s] = copt(yy[prv & m_s], mm[prv & m_s])
    out['ganancia'] = M.d2(yy[prv], mm[prv] * fac[prv]) - base_prv
    out['oraculo'] = M.d2(yy[prv], mm[prv] * orac[prv]) - base_prv  # techo: óptimo privado exacto por celda
    out['ruido'] = ruido
    return out


# remuestreo al tamaño y composición de 2025 (mismas réplicas para todo)
REPL = {}
for nm, d in POOLS.items():
    comp = M.components(d['cust'], d['addr']); Kc = comp.max() + 1
    cell = np.char.add(np.char.add(d['line'].astype(str), '_'), d['nb'].astype(str))
    share = pd.Series(cell).value_counts(normalize=True)
    wrow = np.array([TARGET[c] / share[c] for c in cell])
    wk = np.bincount(comp, weights=wrow, minlength=Kc) / np.bincount(comp, minlength=Kc)
    nk = np.bincount(comp, minlength=Kc); pk = wk / wk.sum(); n_comp = int(round(N25 / (pk * nk).sum()))
    rows_by = pd.Series(np.arange(len(comp))).groupby(comp).apply(np.array).values
    rng = np.random.default_rng(2026102501 + int(nm)); reps = []
    for _ in range(REPS):
        ii = np.concatenate([rows_by[k] for k in rng.choice(Kc, size=n_comp, p=pk)]); reps.append((ii, rng.random(len(ii)) < 0.33))
    cc = pd.Series(np.concatenate([cell[ii] for ii, _ in reps[:5]])).value_counts(normalize=True).round(3).to_dict()
    REPL[nm] = dict(reps=reps, cell=cell, composicion_lograda=cc)
    print(nm, 'réplicas listas', round(time.time() - t0), cc, flush=True)


def escenario_mu(d, cell, nombre, rng):
    mu = d['mu'].copy(); y = d['y']
    if nombre in ('nulo', 'previa'):  # sin desviación por celda: cada celda a su óptimo del año, luego un desvío global común
        for c in np.unique(cell):
            m = cell == c; mu[m] *= copt(y[m], mu[m])
        mu = mu / 1.2231
    return mu


if '--solo-sigma' in sys.argv:  # revisión independiente (25-10): σ de ramo × nuevo negocio por año, repeticiones y NaN
    out = {'replicas': REPS, 'pools': {}}
    for nm, d in POOLS.items():
        cell = REPL[nm]['cell']; mu = escenario_mu(d, cell, 'nulo', None); lab = SEGS['ramo_nb'](d['line'], d['nb']); rs = {}
        for ii, pub in REPL[nm]['reps']:
            r = una_replica(d['y'][ii], mu[ii], cell[ii], pub, lab[ii], {})
            for s, v in r['ruido'].items(): rs.setdefault(s, []).append(v)
        ii0 = REPL[nm]['reps'][0][0]
        out['pools'][nm] = {'sigma': {s: round(float(np.nanstd(v)), 4) for s, v in rs.items()}, 'nan': {s: int(np.isnan(v).sum()) for s, v in rs.items()},
                            'filas_origen': {c: int((cell == c).sum()) for c in np.unique(cell)},
                            'siniestros_origen': {c: int(((cell == c) & (d['y'] > 0)).sum()) for c in np.unique(cell)},
                            'copias_medias_por_fila': {c: round(float((cell[ii0] == c).sum() / (cell == c).sum()), 1) for c in np.unique(cell)},
                            'composicion_lograda': REPL[nm]['composicion_lograda']}
        print(nm, out['pools'][nm]['sigma'], flush=True)
    out['sigma_max'] = {s: max(out['pools'][p]['sigma'][s] for p in out['pools']) for s in out['pools']['2024']['sigma']}
    json.dump(out, open(O / 'sigma_por_pool.json', 'w'), indent=1, ensure_ascii=False); sys.exit(0)
res = {'tau': TAU, 'K': K, 'replicas': REPS, 'composicion_2025': {k: round(v, 4) for k, v in TARGET.items()},
       'pools': {nm: {'composicion_lograda': REPL[nm]['composicion_lograda']} for nm in REPL}}
# fase 1: σ por celda en el escenario nulo (con Z = 0 la regla no toca los segmentos; solo se mide el ruido)
sig = {}
for seg in SEGS:
    rs = {}
    for nm, d in POOLS.items():
        cell = REPL[nm]['cell']; mu = escenario_mu(d, cell, 'nulo', None)
        lab = SEGS[seg](d['line'], d['nb'])
        for ii, pub in REPL[nm]['reps']:
            r = una_replica(d['y'][ii], mu[ii], cell[ii], pub, lab[ii], {})
            for s, v in r['ruido'].items(): rs.setdefault(s, []).append(v)
    sig[seg] = {s: float(np.nanstd(v)) for s, v in rs.items()}
    print('sigma', seg, {s: round(v, 3) for s, v in sig[seg].items()}, round(time.time() - t0), flush=True)
Zs = {seg: {s: TAU ** 2 / (TAU ** 2 + v ** 2) for s, v in sig[seg].items()} for seg in SEGS}
res['sigma'] = {seg: {s: round(v, 4) for s, v in d.items()} for seg, d in sig.items()}
res['Z'] = {seg: {s: round(v, 3) for s, v in d.items()} for seg, d in Zs.items()}
# fase 2: ganancia en el privado por escenario
res['ganancia'] = {}
for seg in SEGS:
    res['ganancia'][seg] = {}
    for nm, d in POOLS.items():
        cell = REPL[nm]['cell']; lab = SEGS[seg](d['line'], d['nb'])
        for esc in ('nulo', 'como_el_año', 'previa'):
            rng = np.random.default_rng(7); mu0 = escenario_mu(d, cell, esc, rng); gains, orac = [], []
            for ii, pub in REPL[nm]['reps']:
                mu = mu0
                if esc == 'previa':
                    dev = {c: np.exp(rng.normal(0, TAU)) for c in np.unique(cell)}
                    mu = mu0 * np.array([dev[c] for c in cell])
                r = una_replica(d['y'][ii], mu[ii], cell[ii], pub, lab[ii], Zs[seg]); gains.append(r['ganancia']); orac.append(r['oraculo'])
            gg = np.array(gains)
            res['ganancia'][seg][f'{nm}_{esc}'] = {'media': round(float(gg.mean()), 5), 'p05_p50_p95': [round(float(q), 5) for q in np.quantile(gg, [0.05, 0.5, 0.95])],
                                                   'prob_ganar': round(float((gg > 0).mean()), 3), 'techo_oraculo_media': round(float(np.mean(orac)), 5)}
            print(seg, nm, esc, res['ganancia'][seg][f'{nm}_{esc}'], round(time.time() - t0), flush=True)
res['envios'] = {'nb': 1, 'ramo': 2, 'ramo_nb': 5}
res['segundos'] = round(time.time() - t0)
json.dump(res, open(O / 'diseno.json', 'w'), indent=1, ensure_ascii=False)
