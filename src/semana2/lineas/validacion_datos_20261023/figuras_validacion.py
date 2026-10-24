"""Figuras de la validación de datos de semana 2 (Claude, 23-10-2026). Lee evidencia_validacion.json y tablas/controles.csv."""
from __future__ import annotations

import json
import pathlib

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

S1, S2, S3, S4 = '#2a78d6', '#eb6834', '#1baf7a', '#8e6cc6'
GRIS, TINTA, TINTA2, REJILLA = '#9aa0a6', '#1f2328', '#57606a', '#e6e8eb'
RAMO = {'motor': 'Autos', 'buildings': 'Edificios', 'contents': 'Contenidos'}
COLOR = {'pasa': S3, 'hallazgo': S2, 'limite': S4, 'informativo': GRIS}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5, 'axes.edgecolor': '#c9ced4', 'axes.labelcolor': TINTA2,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.grid': True, 'grid.color': REJILLA,
                     'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.spines.top': False, 'axes.spines.right': False,
                     'legend.frameon': False, 'savefig.dpi': 160})


def coma(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def titulo(fig, t, s):
    fig.text(0.01, 0.985, t, ha='left', va='top', fontsize=12, color=TINTA, weight='bold')
    fig.text(0.01, 0.935, s, ha='left', va='top', fontsize=9.5, color=TINTA2)


def fig_controles(out, tabla):
    orden = ['Integridad', 'Relaciones', 'Calendario', 'Clientes', 'Direcciones', 'Clima', 'Autos', 'Edificios', 'Contenidos', 'Hogar', 'Pólizas',
             'Siniestros', 'Test', 'Entrega', 'Capas derivadas', 'Faltantes', 'Disponibilidad', 'Comercial', 'Historia', 'Objetivo', 'Métrica', 'Tendencia', 'Revisión']
    areas = [a for a in orden if a in set(tabla.area)] + sorted(set(tabla.area) - set(orden))
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    y = np.arange(len(areas))
    left = np.zeros(len(areas))
    for res in ['pasa', 'hallazgo', 'limite', 'informativo']:
        n = np.array([int(((tabla.area == a) & (tabla.resultado == res)).sum()) for a in areas])
        ax.barh(y, n, left=left, color=COLOR[res], height=0.62, label=res.capitalize(), edgecolor='white', linewidth=1)
        for yi, (l0, k) in enumerate(zip(left, n)):
            if k:
                ax.text(l0 + k / 2, yi, str(k), ha='center', va='center', fontsize=8, color='white' if res != 'informativo' else TINTA)
        left += n
    ax.set_yticks(y)
    ax.set_yticklabels(areas)
    ax.invert_yaxis()
    ax.set_xlabel('Controles')
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.legend(loc='lower right', fontsize=8.5)
    tot = tabla.resultado.value_counts()
    titulo(fig, f'{len(tabla)} controles sobre el mercado emergente: {tot.get("pasa", 0)} pasan, {tot.get("hallazgo", 0)} con hallazgo, {tot.get("limite", 0)} límites declarados y {tot.get("informativo", 0)} descriptivos',
           'Hallazgo: condiciona el modelo o la entrega. Límite: estos archivos no permiten resolverlo. Descriptivo: informa sin exigir acción.')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out / 'fig1_controles.png')
    plt.close(fig)


def fig_calendario(out, ev, E):
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4))
    ax = axs[0]
    conv = {l: ev['VE16'][f'{l}_train']['convencion'] for l in RAMO}
    x = np.arange(3)
    a360 = [conv[l].get('ACT360', 0) for l in RAMO]
    adias = [conv[l].get('DIAS', 0) for l in RAMO]
    ax.bar(x - 0.18, a360, 0.34, color=S2, label='Guardada como días / 360')
    ax.bar(x + 0.18, adias, 0.34, color=S4, label='Guardada como número de días')
    for i in range(3):
        ax.text(x[i] - 0.18, a360[i] + 3, str(a360[i]), ha='center', fontsize=8.5, color=TINTA2)
        ax.text(x[i] + 0.18, adias[i] + 3, str(adias[i]), ha='center', fontsize=8.5, color=TINTA2)
    ax.set_xticks(x)
    ax.set_xticklabels([RAMO[l] for l in RAMO])
    ax.set_ylabel('Filas de entrenamiento')
    tot = sum(a360) + sum(adias)
    ax.set_title(f'{tot} filas en otra convención (el resto y todo el test, días / 365)', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='upper right', fontsize=8)
    ax = axs[1]
    for l, col in zip(RAMO, [S1, S2, S3]):
        t = pd.concat([E.pol[l], E.test[l]])
        fin = t.period_end.dt.strftime('%m-%d')
        por = t.groupby('year').apply(lambda g: (g.period_end.dt.strftime('%m-%d') == '12-31').mean(), include_groups=False)
        ax.plot(por.index, por.values, marker='o', color=col, lw=2, ms=6, label=RAMO[l])
    ax.set_xticks([2023, 2024, 2025])
    ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel('Cuota de periodos que terminan el 31 de diciembre')
    ax.set_title('2024 termina el 30-12: nada cubre el 31-12-2024', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='center right', fontsize=8)
    titulo(fig, 'Calendario y exposición: dos rasgos del generador que la base de Codex ya trata',
           'Izquierda: las 609 filas cuya exposición no está en días / 365 (VE16). Derecha: el día que falta entre 2024 y 2025 (VE14, VE15).')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig2_calendario.png')
    plt.close(fig)


def fig_nulos(out, ev):
    seg = ev['VE72']['polizas_y_direcciones_por_segmento']
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 4.6))
    etiquetas = {'2023': '2023', '2024': '2024', '2025_renovacion': '2025 renov.', '2025_nb': '2025 nuevo'}
    for ax, l in zip(axs, RAMO):
        cols = [c for c in seg[l]['2024'] if seg[l]['2024'][c] > 0.05]
        if l == 'motor':
            ax.set_ylim(len(cols) - 0.5 + 1.6, -0.6)
        y = np.arange(len(cols))
        for dy, (k, col) in zip([-0.27, -0.09, 0.09, 0.27], [('2023', S1), ('2024', S3), ('2025_renovacion', GRIS), ('2025_nb', S2)]):
            ax.barh(y + dy, [seg[l][k][c] for c in cols], height=0.17, color=col, label=etiquetas[k])
        ax.set_yticks(y)
        ax.set_yticklabels([c.replace('_', ' ') for c in cols], fontsize=8)
        if l != 'motor':
            ax.invert_yaxis()
        ax.set_xlim(0, 0.16)
        ax.set_xticks([0, 0.05, 0.10, 0.15])
        ax.set_xticklabels(['0', '5 %', '10 %', '15 %'])
        ax.set_title(RAMO[l], loc='left', fontsize=10, color=TINTA)
    axs[0].legend(loc='lower right', fontsize=8, ncol=2)
    titulo(fig, 'Los nulos del 12 %: la misma cuota en 2023, 2024, en las renovaciones y en la cartera nueva de 2025',
           'Columnas con más del 5 % de ausencias (VE72). No se concentran en ningún segmento ni se correlacionan entre columnas.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig3_nulos.png')
    plt.close(fig)


def fig_make_model(out, E, args_dev):
    import pyarrow.parquet as pq
    p = E.pol['motor'].copy()
    acc = E.acc[E.acc.line == 'motor'].groupby('row_id').size()
    p['n'] = p.row_id.map(acc).fillna(0)
    g = p.groupby('make_model').agg(n=('n', 'sum'), e=('e365', 'sum'))
    dc = pq.read_table(args_dev / 'claims.parquet', columns=['claim_id', 'policy_id', 'line', 'loss_date', 'status']).to_pandas()
    dc = dc[(dc.line == 'motor') & (dc.status != 'repudiated') & (dc.claim_id.str.len() != 11)].copy()
    dc['loss_date'] = pd.to_datetime(dc.loss_date)
    dm = pq.read_table(args_dev / 'policies_motor.parquet', columns=['row_id', 'policy_id', 'period_start', 'period_end', 'make_model']).to_pandas()
    dm['period_start'], dm['period_end'] = pd.to_datetime(dm.period_start), pd.to_datetime(dm.period_end)
    mj = dc.merge(dm[['row_id', 'policy_id', 'period_start', 'period_end']], on='policy_id')
    mj = mj[(mj.loss_date >= mj.period_start) & (mj.loss_date <= mj.period_end)]
    dm['n'] = dm.row_id.map(mj.groupby('row_id').size()).fillna(0)
    dm['e'] = ((dm.period_end - dm.period_start).dt.days + 1) / 365
    gd = dm.groupby('make_model').agg(n=('n', 'sum'), e=('e', 'sum'))
    r = pd.DataFrame(dict(em=g.n / g.e, dev=gd.n / gd.e, n_em=g.n)).dropna()
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4))
    ax = axs[0]
    ax.scatter(r.dev, r.em, s=14, color=S1, alpha=0.7, lw=0)
    ax.axhline(r.em.mean(), color=GRIS, lw=0.8, ls='--')
    ax.axvline(r.dev.mean(), color=GRIS, lw=0.8, ls='--')
    ax.set_xlabel('Frecuencia del código en el desarrollado (siniestros por año-exposición)')
    ax.set_ylabel('Frecuencia del código en el emergente 2023–2024')
    ax.set_title(f'300 códigos: correlación entre mercados {coma(r.em.corr(r.dev))}', loc='left', fontsize=10, color=TINTA)
    ax = axs[1]
    lam = g.n.sum() / g.e.sum()
    esp = lam * g.e
    z = (g.n - esp) / np.sqrt(esp)
    ax.hist(z, bins=25, color=S2, alpha=0.85, edgecolor='white')
    xs = np.linspace(-4, 4, 200)
    ancho = (z.max() - z.min()) / 25
    ax.plot(xs, len(z) * ancho * np.exp(-xs ** 2 / 2) / np.sqrt(2 * np.pi), color=TINTA2, lw=1.2, label='Poisson sin efecto del código')
    ax.set_xlabel('Desviación estandarizada de los siniestros del código frente a su exposición')
    ax.set_ylabel('Códigos')
    ax.set_title(f'Más dispersión que Poisson (razón {coma(float((z ** 2).sum() / (len(z) - 1)), 2)})', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='upper right', fontsize=8)
    titulo(fig, 'make_model: un código de 300 niveles que no describe el vehículo y cuyo efecto no se traslada',
           'Cada código mezcla carrocerías, combustibles y plazas (VE75). Lo que un árbol aprende de él en un mercado no sirve en el otro.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig4_make_model.png')
    plt.close(fig)


def fig_test(out, ev):
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 4.6), sharex=True)
    for ax, l in zip(axs, RAMO):
        d = {c: v['psi_2024_2025'] for c, v in ev['VE48'][l].items() if not c.startswith('_')}
        top = sorted(d.items(), key=lambda x: -x[1])[:10]
        nb = ev['VE48'][l]['_nb_2023_2024_vs_nb_2025']
        y = np.arange(len(top))
        ax.barh(y + 0.18, [v for _, v in top], height=0.34, color=S2, label='Todo 2024 → todo 2025')
        ax.barh(y - 0.18, [nb.get(c, 0) for c, _ in top], height=0.34, color=S1, label='Nuevo negocio 2023–2024 → nuevo negocio 2025')
        ax.set_yticks(y)
        ax.set_yticklabels([c.replace('_', ' ') for c, _ in top], fontsize=8)
        ax.invert_yaxis()
        ax.set_xscale('symlog', linthresh=0.1)
        ax.set_xticks([0, 0.1, 0.5, 1, 2, 3])
        ax.set_xticklabels(['0', '0,1', '0,5', '1', '2', '3'])
        ax.set_title(RAMO[l], loc='left', fontsize=10, color=TINTA)
    axs[1].set_xlabel('PSI (escala comprimida)')
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=2, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    titulo(fig, 'Qué cambia en 2025: casi todo el desplazamiento es la cartera nueva',
           'Dentro del nuevo negocio solo cambian la exposición (entra en enero) y los contactos; el resto se parece al nuevo negocio orgánico (VE48).')
    fig.tight_layout(rect=(0, 0.06, 1, 0.88))
    fig.savefig(out / 'fig5_test.png')
    plt.close(fig)


def fig_siniestros(out, ev):
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4))
    ax = axs[0]
    filas = []
    for l in RAMO:
        for per, d in ev['VE44'][l]['por_peligro'].items():
            filas.append((f'{RAMO[l]}: {per.replace("_", " ")}', d['mediana'], d['p90'], d['n']))
    filas.sort(key=lambda x: -x[2])
    y = np.arange(len(filas))
    ax.scatter([f[1] for f in filas], y, color=S1, s=26, zorder=3, label='Mediana')
    ax.scatter([f[2] for f in filas], y, color=S2, s=26, zorder=3, label='Percentil 90')
    for yi, f in zip(y, filas):
        ax.plot([f[1], f[2]], [yi, yi], color=REJILLA, lw=2, zorder=1)
        ax.text(f[2] * 1.08, yi, f'n = {f[3]}', fontsize=7.5, color=TINTA2, va='center')
    ax.set_yticks(y)
    ax.set_yticklabels([f[0] for f in filas], fontsize=8)
    ax.invert_yaxis()
    ax.set_xscale('log')
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks([3, 10, 30, 100, 300])
    ax.set_xticklabels(['3', '10', '30', '100', '300'])
    ax.set_xlabel('Días entre ocurrencia y reporte')
    ax.set_title('Retraso de reporte por peligro', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='lower right', fontsize=8)
    ax = axs[1]
    x = np.arange(3)
    top1 = [ev['VE45'][l]['top1'] for l in RAMO]
    top10 = [ev['VE45'][l]['top10'] for l in RAMO]
    top1pct = [ev['VE45'][l]['top1pct'] for l in RAMO]
    ax.bar(x - 0.27, top1, 0.25, color=S3, label='Mayor siniestro')
    ax.bar(x, top10, 0.25, color=S1, label='Diez mayores')
    ax.bar(x + 0.27, top1pct, 0.25, color=S2, label='1 % superior')
    for i in range(3):
        ax.text(x[i], top10[i] + 0.008, f'{top10[i]:.0%}', ha='center', fontsize=8.5, color=TINTA2)
    ax.set_xticks(x)
    ax.set_xticklabels([RAMO[l] for l in RAMO])
    ax.set_ylabel('Cuota del coste observado 2023–2024')
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_title('Concentración del coste', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='upper left', fontsize=8)
    titulo(fig, 'Siniestros: lesiones corporales tardan en reportarse y edificios depende de pocos casos',
           'Izquierda, VE44: medianas y percentiles 90 por peligro. Derecha, VE45: peso de los mayores siniestros en el coste de cada ramo.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig6_siniestros.png')
    plt.close(fig)


def dibujar(out: pathlib.Path, E, developed: pathlib.Path):
    ev = json.loads((out / 'evidencia_validacion.json').read_text(encoding='utf-8'))['detalle']
    tabla = pd.read_csv(out / 'tablas' / 'controles.csv')
    fig_controles(out, tabla)
    fig_calendario(out, ev, E)
    fig_nulos(out, ev)
    fig_make_model(out, E, developed)
    fig_test(out, ev)
    fig_siniestros(out, ev)
