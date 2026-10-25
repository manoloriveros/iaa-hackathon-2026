"""Figuras del informe nocturno (PNG, claro). Paleta de referencia de la skill dataviz, orden fijo."""
import json, pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = pathlib.Path('/home/claude/noche'); F = R / 'figuras'; F.mkdir(exist_ok=True)
S1, S2, S3, S4 = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
GRIS, TXT, TXT2, SURF = '#b9b8b2', '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': '#d6d5d0', 'axes.labelcolor': TXT2, 'xtick.color': TXT2,
                     'ytick.color': TXT2, 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'axes.grid': True,
                     'grid.color': '#ecebe7', 'grid.linewidth': 0.8, 'axes.spines.top': False, 'axes.spines.right': False})


from matplotlib.ticker import FuncFormatter
COMA = FuncFormatter(lambda v, p: f'{v:g}'.replace('.', ','))


def num(x, d=3):
    return f'{x:.{d}f}'.replace('.', ',')


# 1. Escalera de la semana 2 (OOF 2023)
esc = json.load(open(R / 'salidas/s2/escalera_resumen.json'))
rungs = [('L0_tasa', 'Tasa por ramo', GRIS), ('L1_glm_a10', 'GLM Tweedie emergente', GRIS), ('L3_gbm', 'GBM Tweedie emergente', GRIS),
         ('T1_glm_nivel', 'Relatividades GLM desarrollado × nivel', S1), ('T1_dev_nivel', 'Relatividades GBM desarrollado × nivel', S1),
         ('T1v2_nivel', 'A1: GBM v2 desarrollado × nivel (3 parámetros)', S1), ('T2v2_reg_a1', 'A2: A1 + región emergente', S1),
         ('A1fixb3_nivel', 'A1 corregida, tres semillas (tras abrir 2024)', S3), ('A1fixF1_nivel', 'A1 corregida + historia de la póliza (tras abrir 2024)', S3)]
fig, ax = plt.subplots(figsize=(8.6, 4.5))
ys = np.arange(len(rungs))[::-1]
for y, (k, lab, c) in zip(ys, rungs):
    v = esc[k]['D2_global']; ax.barh(y, v, color=c, height=0.62)
    ax.text(v + 0.002, y, num(v), va='center', color=TXT, fontsize=9)
ax.set_yticks(ys, [r[1] for r in rungs]); ax.set_xlim(0, 0.145); ax.set_xlabel('D² Tweedie 1,5, fuera de muestra (emergente 2023, 5 folds por cliente)')
ax.set_title('Semana 2: solo emergente (gris), transferencia (azul) y añadidos posteriores (verde)', loc='left', fontsize=10.5, color=TXT); ax.xaxis.set_major_formatter(COMA)
ax.grid(axis='y', visible=False); fig.tight_layout(); fig.savefig(F / 'fig1_escalera_s2.png', dpi=160); plt.close(fig)

# 2. Puerta 2024
pu = json.load(open(R / 'salidas/conf/puerta_2024_resultado.json'))
cats = ['Global', 'Autos', 'Edificios', 'Contenidos']
vals = {m: [pu['D2'][m]] + [pu['D2_por_ramo'][m][l] for l in ['motor', 'buildings', 'contents']] for m in ['R0', 'A1', 'A2']}
fig, ax = plt.subplots(figsize=(8.4, 3.9)); x = np.arange(4); w = 0.26
for i, (m, c, lab) in enumerate([('R0', GRIS, 'R0 tasa por ramo (titular bajo v1)'), ('A1', S1, 'A1 relatividades del desarrollado × nivel (titular bajo v2)'), ('A2', S2, 'A2 = A1 + región')]):
    ax.bar(x + (i - 1) * w, vals[m], width=w - 0.02, color=c, label=lab)
    if m == 'A1':
        for xi, v in zip(x, vals[m]): ax.text(xi, v + 0.003, num(v), ha='center', fontsize=8.5, color=TXT)
ax.axhline(0, color='#9a9994', lw=0.8); ax.set_xticks(x, cats); ax.set_ylabel('D² sobre T0 de 2024')
ax.set_title('Confirmación única 2023 → 2024: A1 − R0 = +0,049, IC 99,17 % [+0,027; +0,073]', loc='left', fontsize=10.5, color=TXT); ax.yaxis.set_major_formatter(COMA)
ax.legend(frameon=False, fontsize=8.5, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig(F / 'fig2_puerta_2024.png', dpi=160); plt.close(fig)

# 3. Escalera de la parte 1 (V24)
p1 = json.load(open(R / 'salidas/p1/p1_evaluacion.json'))['tabla']
r1 = [('P1-L0', 'Tasa por ramo'), ('P1-GLM', 'GLM Tweedie (esquema común)'), ('P1-GBMc', 'Un GBM (esquema común)'),
      ('P1-GBMf', 'Un GBM (todas las F0)'), ('P1-GBMf1', 'Un GBM (F0 + historia de la póliza)'), ('S30', 'S30, receta completa')]
fig, ax = plt.subplots(figsize=(8.4, 3.4)); ys = np.arange(len(r1))[::-1]; ref = p1['S30']['D2']
for y, (k, lab) in zip(ys, r1):
    v = p1[k]['D2']; c = S2 if k == 'S30' else (GRIS if k == 'P1-L0' else S1)
    ax.barh(y, v, color=c, height=0.62); ax.text(v + 0.002, y, f'{num(v)}  ({100 * v / ref:.0f} % de S30)'.replace('.', ','), va='center', fontsize=9, color=TXT)
ax.set_yticks(ys, [r[1] for r in r1]); ax.set_xlim(0, 0.19); ax.set_xlabel('D² Tweedie 1,5 en 2024 (ajuste 2021–2023, 626.190 filas, mismo T0 que S30)')
ax.set_title('Parte 1: cuánto del resultado logra un modelo estándar', loc='left', fontsize=10.5, color=TXT); ax.xaxis.set_major_formatter(COMA)
ax.grid(axis='y', visible=False); fig.tight_layout(); fig.savefig(F / 'fig3_escalera_p1.png', dpi=160); plt.close(fig)

# 4. Opciones de nivel 2025
pi = json.load(open(R / 'salidas/produccion/produccion_info.json'))
exp = {l: pi[l]['exposicion'] for l in ['motor', 'buildings', 'contents']}
a1t = pi['A1T']['totales_por_ramo']
opts = {'motor': {'R0': pi['motor']['total_R0'] / exp['motor'], 'A1': pi['motor']['tasa_A1'], 'A1T': a1t['M'] / exp['motor'], 'rev3': 601, 'rng': (517, 661)},
        'buildings': {'R0': pi['buildings']['total_R0'] / exp['buildings'], 'A1': pi['buildings']['tasa_A1'], 'A1T': a1t['B'] / exp['buildings'], 'rev3': 475, 'rng': (401, 555)},
        'contents': {'R0': pi['contents']['total_R0'] / exp['contents'], 'A1': pi['contents']['tasa_A1'], 'A1T': a1t['C'] / exp['contents'], 'rev3': 103, 'rng': (94, 116)}}
fig, axs = plt.subplots(1, 3, figsize=(8.6, 3.2))
for ax, (l, t) in zip(axs, [('motor', 'Autos'), ('buildings', 'Edificios'), ('contents', 'Contenidos')]):
    o = opts[l]; lo, hi = o['rng']
    ax.axhspan(lo, hi, color='#ecebe7', zorder=0)
    pts = [('R0', GRIS), ('A1', S1), ('A1T', S3), ('rev3', S2)]
    for i, (k, c) in enumerate(pts):
        ax.plot(i, o[k], 'o', ms=8, color=c, zorder=3); ax.text(i, o[k] * 1.012, f'{o[k]:.0f}', ha='center', va='bottom', fontsize=8.5, color=TXT)
    ax.set_xticks(range(4), ['R0', 'A1', 'A1 +\ntendencia', 'Revisor\nrev3'], fontsize=8.5); ax.set_title(t, fontsize=10, color=TXT, loc='left')
    ax.set_xlim(-0.5, 3.5); ax.grid(axis='x', visible=False)
axs[0].set_ylabel('CU por año-exposición')
fig.suptitle('Prima de riesgo 2025 por ramo: opciones y rango plausible del revisor (franja gris)', x=0.01, ha='left', fontsize=10.5, color=TXT)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(F / 'fig4_nivel_2025.png', dpi=160); plt.close(fig)

# 5. Incendio: frecuencia por año y mercado
rows = []
for mk, yrs in (('s1', [2021, 2022, 2023, 2024]), ('s2', [2023, 2024])):
    b = pd.read_parquet(R / f'salidas/{mk}/base_buildings.parquet'); b = b[b.split == 'train']
    for y in yrs:
        x = b[b.year == y]; n = x.n_fire.sum(); e = x.eef_fire.sum()
        rows.append((mk, y, n, 1000 * n / e, 1000 * 1.645 * np.sqrt(n) / e))
fig, ax = plt.subplots(figsize=(8.4, 3.2))
for mk, c, lab, off in (('s1', GRIS, 'Desarrollado', -0.08), ('s2', S2, 'Emergente', 0.08)):
    rr = [r for r in rows if r[0] == mk]
    ax.errorbar([r[1] + off for r in rr], [r[3] for r in rr], yerr=[r[4] for r in rr], fmt='o', ms=7, color=c, capsize=3, lw=1.5, label=lab)
    for r in rr: ax.text(r[1] + off + (0.1 if mk == 's2' else -0.1), r[3], f'{int(r[2])} incendios', fontsize=8, color=TXT2, va='center', ha='left' if mk == 's2' else 'right')
ax.set_xticks([2021, 2022, 2023, 2024]); ax.set_ylabel('Incendios por mil años-exposición')
ax.set_title('Edificios: frecuencia de incendio por año y mercado (IC90 de Poisson)', loc='left', fontsize=10.5, color=TXT); ax.yaxis.set_major_formatter(COMA)
ax.legend(frameon=False, fontsize=8.5); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig(F / 'fig5_incendio.png', dpi=160); plt.close(fig)
print('ok', sorted(p.name for p in F.glob('*.png')))
