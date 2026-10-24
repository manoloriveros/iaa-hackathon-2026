"""Diagnóstico de la tanda de desarrollo 2023 de Codex sin reentrenar (Claude, 23 de octubre de 2026).

Lee las predicciones fuera de muestra y el diagnóstico de ajuste guardados por Codex en
dev_20261023T173828Z_7efe46fc, más las matrices F0 de f0_ultimo_20261023T170841Z_82038766, después de
comprobar sus SHA-256 contra los manifiestos de esas corridas. No carga modelos ni llama a fit: solo reescala
predicciones ya guardadas y recalcula métricas. Escribe agregados en desarrollo2023_diagnostico.json.

Uso desde C:/dev/Hakaton:
    python "Hackaton/Semana 2/Claude/revision_apertura_20261023/diagnostico_desarrollo2023.py"
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

LINES = ['motor', 'buildings', 'contents']
FACTORES = [1.0, 1.2, 1.4, 1.6]


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest_sha(manifest: pathlib.Path, name: str) -> str:
    files = json.loads(manifest.read_text(encoding='utf-8'))['files']
    hits = [f['sha256'] for f in files if f['path'].replace('\\', '/').endswith(name)]
    if len(hits) != 1:
        raise SystemExit(f'{name}: {len(hits)} entradas en {manifest}')
    return hits[0]


def tweedie_dev(y, mu, w=None):
    """Devianza media Tweedie con potencia 1,5, la misma fórmula que sklearn.metrics.mean_tweedie_deviance."""
    y = np.asarray(y, float)
    mu = np.asarray(mu, float)
    p = 1.5
    d = 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    return float(np.sum(w * d) / np.sum(w))


def d2(y, mu, w=None):
    y = np.asarray(y, float)
    w_ = np.ones_like(y) if w is None else np.asarray(w, float)
    mu0 = np.full_like(y, np.sum(w_ * y) / np.sum(w_))
    return 1 - tweedie_dev(y, mu, w_) / tweedie_dev(y, mu0, w_)


def main(args):
    run = args.run
    oof_p, fit_p = run / 'oof_2023.parquet', run / 'diagnostics' / 'fit_vs_oof.json'
    checks = {'oof_2023.parquet': (sha256(oof_p), manifest_sha(run / 'manifest.json', 'oof_2023.parquet')),
              'diagnostics/fit_vs_oof.json': (sha256(fit_p), manifest_sha(run / 'closure_manifest.json', 'diagnostics/fit_vs_oof.json'))}
    for l in LINES:
        f0 = args.f0 / f'F0_{l}.parquet'
        checks[f'F0_{l}.parquet'] = (sha256(f0), manifest_sha(args.f0 / 'manifest.json', f'F0_{l}.parquet'))
    if not all(a == b for a, b in checks.values()):
        raise SystemExit(f'Huellas distintas del manifiesto: {checks}')
    t = pq.read_table(oof_p).to_pandas()
    t['T0'] = t['T0'].astype(float)
    t['fold'] = t['fold'].astype(int)
    nodes = json.loads(fit_p.read_text(encoding='utf-8'))['nodes']
    ae_fit = {(n['model_id'], n['line'], n['fold']): n['training_actual_over_expected'] for n in nodes}
    t['k_ajuste'] = [ae_fit[(m, l, f)] for m, l, f in zip(t.model_id, t.line, t.fold)]
    t['pred_bal'] = t.prediction * t.k_ajuste
    # pesos que llevan la cuota de exposición del nuevo negocio de cada ramo a la del test de 2025
    cuota25 = {}
    for l in LINES:
        f0 = pq.read_table(args.f0 / f'F0_{l}.parquet', columns=['year', 'is_test', 'exposure', 'x_new_business']).to_pandas()
        te = f0[f0.is_test.astype(bool)]
        cuota25[l] = float(te[te.x_new_business == 1].exposure.sum() / te.exposure.sum())
    b = t[t.model_id == 'W2-B00']
    w = {}
    for l, s in b.groupby('line'):
        e_nb, e_re = s[s.x_new_business == 1].exposure.sum(), s[s.x_new_business == 0].exposure.sum()
        sh_nb = e_nb / (e_nb + e_re)
        w[(l, 1)], w[(l, 0)] = cuota25[l] / sh_nb, (1 - cuota25[l]) / (1 - sh_nb)
    t['w25'] = [w[(l, int(x))] for l, x in zip(t.line, t.x_new_business)]
    out = {'autor': 'Claude', 'utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
           'alcance': 'Sin modelos ni fit: reescalado de predicciones guardadas y métricas recalculadas.',
           'entradas': {k: v[0] for k, v in checks.items()}, 'cuota_nb_exposicion_test_2025': cuota25,
           'pesos_mezcla_2025': {f'{l}/{"NB" if x else "REN"}': v for (l, x), v in w.items()}, 'modelos': {}}
    for m, s in t.groupby('model_id'):
        o = dict(D2=d2(s.T0, s.prediction), AE=float(s.T0.sum() / s.prediction.sum()),
                 D2_balance_ajuste=d2(s.T0, s.pred_bal), AE_balance_ajuste=float(s.T0.sum() / s.pred_bal.sum()),
                 factor_balance_min=float(s.k_ajuste.min()), factor_balance_max=float(s.k_ajuste.max()))
        aeo = s.groupby('line').apply(lambda g: g.T0.sum() / g.prediction.sum(), include_groups=False)
        o['D2_oraculo_nivel_por_ramo'] = d2(s.T0, s.prediction * s.line.map(aeo))
        o['por_ramo'] = {l: dict(D2=d2(g.T0, g.prediction), D2_balance_ajuste=d2(g.T0, g.pred_bal),
                                 AE=float(g.T0.sum() / g.prediction.sum())) for l, g in s.groupby('line')}
        o['por_negocio'] = {('NB' if x else 'REN'): dict(filas=len(g), D2=d2(g.T0, g.prediction),
                                                         AE=float(g.T0.sum() / g.prediction.sum()))
                            for x, g in s.groupby('x_new_business')}
        o['mezcla_2025'] = dict(AE=float((s.T0 * s.w25).sum() / (s.prediction * s.w25).sum()),
                                D2_por_factor={f'{f:.1f}': d2(s.T0, s.prediction * f, s.w25) for f in FACTORES})
        o['mezcla_2023'] = dict(D2_por_factor={f'{f:.1f}': d2(s.T0, s.prediction * f) for f in [0.8] + FACTORES})
        out['modelos'][m] = o
    out['diferencia_B01_menos_B00'] = dict(
        sin_balance=out['modelos']['W2-B01']['D2'] - out['modelos']['W2-B00']['D2'],
        con_balance_ajuste=out['modelos']['W2-B01']['D2_balance_ajuste'] - out['modelos']['W2-B00']['D2_balance_ajuste'])
    b00 = out['modelos']['W2-B00']['mezcla_2025']['D2_por_factor']
    out['valor_del_nivel_en_mezcla_2025_B00'] = b00['1.4'] - b00['1.0']
    f0d = {}
    for l in LINES:
        f0 = pq.read_table(args.f0 / f'F0_{l}.parquet').to_pandas()
        nb = f0[f0.x_new_business == 1]
        te = f0[f0.is_test.astype(bool)]
        f0d[l] = dict(renewal_count_igual_tenure=float((f0.x_renewal_count == f0.x_customer_tenure_years).mean()),
                      nb_inicio_enero={int(y): float((g.x_start_month == 1).mean()) for y, g in nb.groupby('year')},
                      nb_enero_filas_train=int(((nb.x_start_month == 1) & (~nb.is_test.astype(bool))).sum()),
                      cuota_test_nb_enero=float(((te.x_new_business == 1) & (te.x_start_month == 1)).mean()))
        if 'x_make_model' in f0.columns:
            f0d[l]['make_model_niveles'] = int(f0.x_make_model.nunique())
    out['F0'] = f0d
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({'D2': {m: round(o['D2'], 5) for m, o in out['modelos'].items()},
                      'D2_balance': {m: round(o['D2_balance_ajuste'], 5) for m, o in out['modelos'].items()}}))


if __name__ == '__main__':
    here = pathlib.Path(__file__).resolve()
    root = here.parents[4] if len(here.parents) > 4 else here.parent
    base = root / 'Hackaton/Repositorio_IAA2026/privado/semana2'
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=pathlib.Path, default=base / 'desarrollo2023/dev_20261023T173828Z_7efe46fc')
    ap.add_argument('--f0', type=pathlib.Path, default=base / 'ultimo/f0_ultimo_20261023T170841Z_82038766')
    ap.add_argument('--out', type=pathlib.Path, default=here.parent / 'desarrollo2023_diagnostico.json')
    main(ap.parse_args())
