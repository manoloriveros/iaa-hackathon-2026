"""Completitud de reporte por peligro con el estimador de Lynden-Bell (datos truncados a la derecha).

Supuesto REP-N1 (fijado antes de medir): el retraso de reporte de un siniestro aceptado depende del peligro y no del
mercado ni del año; se estima con los dos mercados juntos y se contrasta mercado contra mercado. F(t) es la probabilidad
de estar reportado t días después de la ocurrencia, normalizada a 1 en el mayor retraso observable (1.460 días); la cola
más allá no es identificable con una sola valoración y se declara como límite.
Coste: se contrasta si la severidad depende del retraso (cohortes maduras del desarrollado). Si no depende, la
completitud de importes es igual a la de conteos.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
CUT = pd.Timestamp('2024-12-31')
B = 7  # días por cubeta


def load(mk):
    c = pd.read_parquet(R / f'datos/{mk}/claims.parquet')
    if mk == 's1':  # duplicados idénticos salvo claim_id: se conserva el de 10 caracteres
        c = c[c.claim_id.str.len() == 10]
    c = c[c.status != 'repudiated'].copy()
    c['ld'] = pd.to_datetime(c.loss_date); c['rd'] = pd.to_datetime(c.report_date)
    c['delay'] = (c.rd - c.ld).dt.days; c['window'] = (CUT - c.ld).dt.days
    c['market'] = mk
    c['net'] = c.incurred_to_date - c.recoveries
    return c


def lynden_bell(delay, window, tmax):
    """F(t) en cubetas de B días; delay<=window por construcción."""
    db = (delay // B).astype(int); wb = (window // B).astype(int)
    nb = tmax // B + 1
    d = np.bincount(db, minlength=nb)[:nb]
    # riesgo en tiempo inverso: casos con db <= s <= wb
    start = np.bincount(db, minlength=nb + 1)[:nb]
    end = np.bincount(np.minimum(wb, nb - 1) + 1, minlength=nb + 1)[:nb]
    risk = np.cumsum(start) - np.cumsum(end)  # casos con db<=s y wb>=s
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
    # severidad por retraso en cohortes maduras del desarrollado (2021-2022): razón media tardío / temprano
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
