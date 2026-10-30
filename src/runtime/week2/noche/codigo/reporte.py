"""Estimate peril reporting completeness with right-truncated Lynden-Bell data.

REP-N1 assumes accepted-claim reporting delay depends on peril, not market or
year. Pool both markets and retain market contrasts as diagnostics. Normalize
F(t) at the largest observed delay (1,460 days); the unobserved tail beyond that
is not identifiable from one valuation. Inspect severity versus delay in mature
developed cohorts before equating cost and count completeness.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('__RUN_ROOT__/noche')
CUT = pd.Timestamp('2024-12-31')
B = 7  # Days per delay bin.


def load(mk):
    c = pd.read_parquet(R / f'datos/{mk}/claims.parquet')
    if mk == 's1':  # Identical payloads except claim_id: retain the 10-character identifier.
        c = c[c.claim_id.str.len() == 10]
    c = c[c.status != 'repudiated'].copy()
    c['ld'] = pd.to_datetime(c.loss_date); c['rd'] = pd.to_datetime(c.report_date)
    c['delay'] = (c.rd - c.ld).dt.days; c['window'] = (CUT - c.ld).dt.days
    c['market'] = mk
    c['net'] = c.incurred_to_date - c.recoveries
    return c


def lynden_bell(delay, window, tmax):
    """Estimate F(t) in B-day bins; delay is bounded by the observation window."""
    db = (delay // B).astype(int); wb = (window // B).astype(int)
    nb = tmax // B + 1
    d = np.bincount(db, minlength=nb)[:nb]
    # Reverse-time risk set: records satisfying db <= s <= wb.
    start = np.bincount(db, minlength=nb + 1)[:nb]
    end = np.bincount(np.minimum(wb, nb - 1) + 1, minlength=nb + 1)[:nb]
    risk = np.cumsum(start) - np.cumsum(end)  # Records with db<=s and wb>=s.
    h = np.where(risk > 0, d / np.maximum(risk, 1), 0.0)
    # F(s) = prod_{u>s} (1-h_u)
    surv = np.cumprod((1 - h)[::-1])[::-1]
    F = np.concatenate([surv[1:], [1.0]])
    return F  # F[s] = P(delay bucket <= s | delay <= tmax)


def main():
    c = pd.concat([load('s1'), load('s2')], ignore_index=True)
    tmax = int(c.window.max())
    out = {}; tabla = {}
    for p, g in c.groupby('peril'):
        F = lynden_bell(g.delay.values, g.window.values, tmax)
        Fe = lynden_bell(g[g.market == 's2'].delay.values, g[g.market == 's2'].window.values, 730) if (g.market == 's2').sum() > 30 else None
        Fd = lynden_bell(g[g.market == 's1'].delay.values, g[g.market == 's1'].window.values, tmax)
        tabla[p] = F.tolist()
        k = {lag: round(float(F[min(lag // B, len(F) - 1)]), 4) for lag in (30, 91, 182, 365, 730)}
        kd = {lag: round(float(Fd[min(lag // B, len(Fd) - 1)]), 4) for lag in (30, 91, 182, 365, 730)}
        ke = {lag: round(float(Fe[min(lag // B, len(Fe) - 1)] * Fd[min(730 // B, len(Fd) - 1)]), 4) for lag in (30, 91, 182, 365, 730)} if Fe is not None else None
        out[p] = {'n': int(len(g)), 'n_emerging': int((g.market == 's2').sum()), 'F_pooled': k, 'F_developed': kd,
                  'F_emerging_rescaled_to_dev730': ke}
    json.dump({'bucket_days': B, 'tmax_days': tmax, 'F': tabla}, open(R / 'salidas/reporte_F.json', 'w'))
    json.dump(out, open(R / 'salidas/reporte_resumen.json', 'w'), indent=1)
    # Mature developed 2021-2022 severity diagnostic: late/early mean-cost ratio.
    m = c[(c.market == 's1') & (c.ld.dt.year <= 2022)]
    sev = {}
    for p, g in m.groupby('peril'):
        q = g.delay.quantile([0.5, 0.9])
        sev[p] = {'media_hasta_p50': round(float(g[g.delay <= q[0.5]].net.mean()), 1),
                  'media_p50_p90': round(float(g[(g.delay > q[0.5]) & (g.delay <= q[0.9])].net.mean()), 1),
                  'media_sobre_p90': round(float(g[g.delay > q[0.9]].net.mean()), 1), 'n': int(len(g))}
    json.dump(sev, open(R / 'salidas/severidad_por_retraso.json', 'w'), indent=1)
    print(json.dumps(out, indent=1)); print(json.dumps(sev, indent=1))


if __name__ == '__main__':
    main()
